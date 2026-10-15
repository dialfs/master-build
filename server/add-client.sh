#!/usr/bin/env bash
# =============================================================================
# DEI Chatbot — tambah satu klien di VPS ini.
#   sudo /opt/dei/server/add-client.sh <slug> <domain> [jumlah_worker=16] [dei-master.zip|URL]
# Contoh:
#   sudo /opt/dei/server/add-client.sh sinarjaya chat.sinarjaya.haltebus.com 16
# Hasil: user Linux sendiri, folder /var/www/<slug>, database MySQL sendiri,
# prefix Redis sendiri, pool PHP-FPM, vhost Nginx, worker supervisord, cron.
# Kode tetap SATU: dei-master.zip yang sama dengan tenant DEI.
# =============================================================================
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Jalankan sebagai root (sudo)."; exit 1; }
SLUG="${1:-}"; DOMAIN="${2:-}"; WORKERS="${3:-16}"; SRC="${4:-https://chat.deintegra.com/master/dei-master.zip}"
[[ "$SLUG" =~ ^[a-z0-9][a-z0-9-]{1,19}$ ]] || { echo "slug: huruf kecil/angka/-, 2-20 karakter"; exit 1; }
[ -n "$DOMAIN" ] || { echo "domain wajib"; exit 1; }
[[ "$WORKERS" =~ ^[0-9]+$ ]] && [ "$WORKERS" -ge 1 ] && [ "$WORKERS" -le 64 ] || { echo "worker 1-64"; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"; T="$HERE/templates"
DIR="/var/www/$SLUG"; USR="dei-$SLUG"; DB="$(echo "${SLUG}_chat" | tr '-' '_')"; CONF="/etc/dei/clients/$SLUG.conf"
[ -e "$DIR" ] && { echo "$DIR sudah ada — klien ini sudah terpasang?"; exit 1; }

echo "==> User Linux $USR"
id "$USR" >/dev/null 2>&1 || useradd --system --home-dir "$DIR" --no-create-home --shell /usr/sbin/nologin "$USR"

echo "==> Kode dari $SRC"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
if [[ "$SRC" =~ ^https?:// ]]; then curl -fsSL "$SRC" -o "$TMP/master.zip"; else cp "$SRC" "$TMP/master.zip"; fi
unzip -q "$TMP/master.zip" -d "$TMP/x"
ROOT="$(dirname "$(find "$TMP/x" -maxdepth 3 -path '*/api/index.php' | head -1)")/.."
[ -f "$ROOT/api/index.php" ] || { echo "ZIP tidak berisi api/index.php"; exit 1; }
mkdir -p "$DIR"; cp -a "$ROOT"/. "$DIR"/

echo "==> Database $DB"
PASS="$(openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 28)"
mysql -e "CREATE DATABASE IF NOT EXISTS \`$DB\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
          CREATE USER IF NOT EXISTS '$USR'@'127.0.0.1' IDENTIFIED BY '$PASS';
          ALTER USER '$USR'@'127.0.0.1' IDENTIFIED BY '$PASS';
          GRANT ALL PRIVILEGES ON \`$DB\`.* TO '$USR'@'127.0.0.1'; FLUSH PRIVILEGES;"

echo "==> data/server.php (driver mysql + redis)"
cat > "$DIR/data/server.php" <<PHP
<?php
// Dibuat add-client.sh $(date '+%Y-%m-%d %H:%M'). Tidak pernah disentuh updater.
return [
    'storage' => 'mysql',
    'queue'   => 'redis',
    'db'      => ['host' => '127.0.0.1', 'port' => 3306, 'name' => '$DB', 'user' => '$USR', 'pass' => '$PASS'],
    'redis'   => ['host' => '127.0.0.1', 'port' => 6379, 'db' => 0, 'prefix' => '$SLUG:'],
    // v1.2.72: gabung bubble beruntun (detik, 0 = mati)
    'debounce_sec'    => 2,
    // v1.2.72: model cadangan kalau AI utama gagal (provider openrouter memakai API key OpenRouter di dashboard)
    'ai_fallback'     => ['provider' => 'openrouter', 'model' => 'anthropic/claude-haiku-4.5'],
    // v1.2.72: kalau semua AI gagal -> nomor dialihkan ke agent + notifikasi Telegram
    'ai_fail_handoff' => true,
    'ai_fail_text'    => 'Terima kasih, pesan Anda sudah kami terima. Tim kami akan segera membalas.',
];
PHP
chown -R "$USR:$USR" "$DIR"
find "$DIR" -type d -exec chmod 750 {} +; find "$DIR" -type f -exec chmod 640 {} +
chmod 600 "$DIR/data/server.php"
usermod -aG "$USR" www-data   # nginx boleh membaca file statis

echo "==> Akun admin awal"
ADMIN_PASS="$(openssl rand -base64 18 | tr -dc 'A-Za-z0-9' | head -c 16)"
ADMIN_PASS="$ADMIN_PASS" php -r '$u = json_decode((string)@file_get_contents($argv[1]), true); if (!is_array($u)) $u = [];
  if (!$u) { $u[] = ["username" => "admin", "password" => password_hash(getenv("ADMIN_PASS"), PASSWORD_DEFAULT), "role" => "super_admin", "migrated_3role" => true];
  file_put_contents($argv[1], json_encode($u, JSON_PRETTY_PRINT)); echo "dibuat\n"; } else echo "sudah ada pengguna, dilewati\n";' "$DIR/data/users.json"
chown "$USR:$USR" "$DIR/data/users.json"; chmod 640 "$DIR/data/users.json"

echo "==> Tabel"
sudo -u "$USR" php "$DIR/api/index.php" action=db_init

echo "==> PHP-FPM, Nginx, worker, cron"
sed "s/__SLUG__/$SLUG/g" "$T/php-fpm-pool.conf" > "/etc/php/8.3/fpm/pool.d/dei-$SLUG.conf"
sed "s/__SLUG__/$SLUG/g; s/__DOMAIN__/$DOMAIN/g" "$T/nginx-site.conf" > "/etc/nginx/sites-available/dei-$SLUG"
ln -sf "/etc/nginx/sites-available/dei-$SLUG" "/etc/nginx/sites-enabled/dei-$SLUG"
sed "s/__SLUG__/$SLUG/g; s/__WORKERS__/$WORKERS/g" "$T/supervisor-workers.conf" > "/etc/supervisor/conf.d/dei-$SLUG.conf"
sed "s/__SLUG__/$SLUG/g" "$T/cron-client" > "/etc/cron.d/dei-$SLUG"
touch "/var/log/dei/$SLUG-php.log" "/var/log/dei/$SLUG-worker.log"; chown "$USR" /var/log/dei/"$SLUG"-*.log
php-fpm8.3 -t && systemctl reload php8.3-fpm
nginx -t && systemctl reload nginx
supervisorctl reread >/dev/null && supervisorctl update >/dev/null

cat > "$CONF" <<C
SLUG=$SLUG
DOMAIN=$DOMAIN
WORKERS=$WORKERS
DB=$DB
CREATED=$(date '+%Y-%m-%d')
C

echo "==> HTTPS (butuh DNS $DOMAIN sudah mengarah ke VPS ini)"
if certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email --redirect; then
  echo "    HTTPS aktif."
else
  echo "    Certbot gagal (DNS belum siap?). Ulangi nanti: sudo certbot --nginx -d $DOMAIN --redirect"
fi

echo
echo "SELESAI: $SLUG di https://$DOMAIN"
echo "  - Login dashboard: admin / $ADMIN_PASS  (catat sekarang, lalu ganti di dashboard)"
echo "  - Daftarkan tenant '$SLUG' di dei-pusat, isi tenant_id + license_key di Pengaturan > Server Pusat."
echo "  - Webhook Meta: https://$DOMAIN/api/index.php?action=wa_webhook"
echo "  - Cek antrean: sudo -u $USR php $DIR/api/index.php action=wa_queue_status"
echo "  - Pindah dari tenant lama? salin data/*.json lalu: sudo -u $USR php $DIR/api/index.php action=db_import"
