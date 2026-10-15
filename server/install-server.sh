#!/usr/bin/env bash
# =============================================================================
# DEI Chatbot — siapkan VPS baru (Ubuntu 24.04 / 26.04 LTS). Jalankan SEKALI sebagai root:
#   sudo bash install-server.sh
# Memasang: Nginx, PHP-FPM bawaan OS (24.04: 8.3, 26.04: 8.5), MySQL 8, Redis, Supervisor,
# Certbot, firewall (UFW), fail2ban, update keamanan otomatis, cron backup & health.
# Aman dijalankan ulang (idempoten).
# =============================================================================
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Jalankan sebagai root (sudo)."; exit 1; }
. /etc/os-release
[ "${ID}" = "ubuntu" ] || echo "PERINGATAN: dibuat untuk Ubuntu 24.04/26.04, OS ini ${PRETTY_NAME}."
HERE="$(cd "$(dirname "$0")" && pwd)"
RAM_MB=$(awk '/MemTotal/{print int($2/1024)}' /proc/meminfo)
# Ukuran ikut RAM VPS (KVM 1 = 4 GB, KVM 2 = 8 GB, ...)
if   [ "$RAM_MB" -lt 3000 ]; then INNODB=256M; REDIS_MAX=256mb
elif [ "$RAM_MB" -lt 7000 ]; then INNODB=512M; REDIS_MAX=384mb
else INNODB=1G; REDIS_MAX=512mb; fi
echo "==> RAM ${RAM_MB} MB -> innodb ${INNODB}, redis ${REDIS_MAX}"

if [ "$(swapon --noheadings | wc -l)" -eq 0 ] && [ ! -f /swapfile ]; then
  echo "==> Swap 2 GB (cadangan saat memori penuh)"
  if fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile >/dev/null && swapon /swapfile; then
    grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
    sysctl -q vm.swappiness=10 || true; echo 'vm.swappiness=10' > /etc/sysctl.d/99-dei.conf
  else rm -f /swapfile; echo "    swap tidak bisa dibuat di VPS ini — dilewati"; fi
fi

echo "==> Paket"
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
# Paket PHP tanpa nomor versi = versi bawaan OS (Ubuntu 24.04: 8.3, 26.04: 8.5)
apt-get install -y -q nginx php-fpm php-cli php-mysql php-redis php-curl \
  php-mbstring php-xml php-zip php-gd php-intl \
  mysql-server supervisor certbot python3-certbot-nginx \
  unzip zip curl jq ufw fail2ban unattended-upgrades
apt-get install -y -q php-opcache 2>/dev/null || true   # PHP 8.5: opcache sudah bawaan
apt-get install -y -q redis-server || apt-get install -y -q valkey-server valkey-redis-compat
PHPV="$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')"
if [ -f /etc/redis/redis.conf ]; then RC=/etc/redis/redis.conf; RSVC=redis-server; else RC=/etc/valkey/valkey.conf; RSVC=valkey-server; fi
printf 'PHPV=%s\nRSVC=%s\n' "$PHPV" "$RSVC" > /etc/dei-runtime.conf
echo "    PHP $PHPV, $RSVC"

echo "==> Firewall: hanya SSH + HTTP/HTTPS"
ufw allow OpenSSH >/dev/null
ufw allow 'Nginx Full' >/dev/null
ufw --force enable >/dev/null

echo "==> Redis: hanya localhost, antrean tahan restart (AOF)"
sed -i 's/^bind .*/bind 127.0.0.1 -::1/' "$RC"
grep -q '^appendonly yes' "$RC" || sed -i 's/^appendonly no/appendonly yes/' "$RC"
sed -i '/^maxmemory /d' "$RC"; echo "maxmemory $REDIS_MAX" >> "$RC"
grep -q '^maxmemory-policy ' "$RC" || echo 'maxmemory-policy noeviction' >> "$RC"   # antrean tidak boleh dibuang diam-diam
systemctl restart "$RSVC"

echo "==> MySQL: hanya localhost"
grep -q '^bind-address' /etc/mysql/mysql.conf.d/mysqld.cnf || echo 'bind-address = 127.0.0.1' >> /etc/mysql/mysql.conf.d/mysqld.cnf
cat > /etc/mysql/mysql.conf.d/dei.cnf <<'CNF'
[mysqld]
innodb_buffer_pool_size = __INNODB__
max_connections = 300
default_time_zone = '+07:00'
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
CNF
sed -i "s/__INNODB__/$INNODB/" /etc/mysql/mysql.conf.d/dei.cnf
systemctl restart mysql

echo "==> PHP: opcache + zona waktu"
cat > /etc/php/$PHPV/mods-available/dei.ini <<'INI'
date.timezone = Asia/Jakarta
opcache.enable = 1
opcache.enable_cli = 0
opcache.memory_consumption = 128
opcache.max_accelerated_files = 10000
opcache.validate_timestamps = 1
opcache.revalidate_freq = 2
expose_php = Off
INI
phpenmod dei
systemctl restart "php$PHPV-fpm"

echo "==> Folder kerja"
mkdir -p /etc/dei/clients /var/www /var/backups/dei /var/log/dei /opt/dei
chmod 750 /etc/dei /var/backups/dei
cp -r "$HERE"/. /opt/dei/server/ 2>/dev/null || true
[ -f /etc/dei/alert.conf ] || cat > /etc/dei/alert.conf <<'CONF'
# Notifikasi health check & backup (Telegram). Kosongkan untuk mematikan.
TG_BOT_TOKEN=""
TG_CHAT_ID=""
# Ambang antrean menumpuk (job)
QUEUE_ALERT=200
CONF
[ -f /etc/dei/backup.conf ] || cat > /etc/dei/backup.conf <<'CONF'
# Simpan berapa hari di server
KEEP_DAYS=30
# Salinan off-site (WAJIB untuk produksi): nama remote rclone, mis. "b2:dei-backup".
# Kosong = hanya lokal (tidak aman kalau VPS hilang).
RCLONE_REMOTE=""
CONF
chmod 640 /etc/dei/*.conf

echo "==> Cron sistem: backup harian 02:30, health tiap 5 menit"
cat > /etc/cron.d/dei-system <<'CRON'
30 2 * * * root /opt/dei/server/backup.sh >> /var/log/dei/backup.log 2>&1
*/5 * * * * root /opt/dei/server/health.sh >> /var/log/dei/health.log 2>&1
CRON
chmod +x /opt/dei/server/*.sh

echo "==> Update keamanan otomatis"
dpkg-reconfigure -f noninteractive unattended-upgrades >/dev/null 2>&1 || true

systemctl enable --now nginx "php$PHPV-fpm" mysql "$RSVC" supervisor >/dev/null
echo
echo "SELESAI. Langkah berikutnya:"
echo "  1. (disarankan) matikan login SSH pakai password setelah kunci SSH terpasang."
echo "  2. Isi /etc/dei/alert.conf (Telegram) dan /etc/dei/backup.conf (off-site)."
echo "  3. Tambah klien: sudo /opt/dei/server/add-client.sh sinarjaya haltebus.chat/sinarjaya 8"
