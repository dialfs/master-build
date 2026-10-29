#!/usr/bin/env bash
# Migrasi tenant omowaynuenco (chatbot.deintegra.com/omowaynuenco) ke penyimpanan MySQL
# (cara 2: tetap di hosting DEI, queue=sync). Jalankan SETELAH rilis-v1.2.107-auto.command.
# Log: ~/Herd/master-build/tools/patch-v1.2.107/migrasi-omowaynuenco.log
# Rollback: ssh ke hosting, lalu  mv <dir>/data/server.php <dir>/data/server.php.off
#   (kembali ke berkas JSON; pesan yang masuk selama mode MySQL tidak ada di berkas).
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.107/migrasi-omowaynuenco.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; SLUG=omowaynuenco; NEED=v1.2.107
source "$HERD/dei-pusat/dev/config.sh"
SSH=(ssh -p "$SSH_PORT" "$SSH_USER@$SSH_HOST")
MASTER="$HERD/dei-pusat/master/dei-master.zip"
grep -q "\"version\": \"$NEED\"" "$HERD/dei-pusat/master/master.json" || { echo "master.json bukan $NEED — jalankan rilis dulu."; read -r -p "Enter..." _; exit 1; }

echo "== 1/5 Cek tenant di hosting =="
"${SSH[@]}" "SLUG=$SLUG bash -s" <<'R'
set -u
DIR=$(ls -d ~/public_html/*/$SLUG ~/*/$SLUG ~/public_html/$SLUG 2>/dev/null | while read d; do [ -f "$d/api/index.php" ] && echo "$d"; done | head -1)
[ -n "$DIR" ] || { echo "TIDAK KETEMU folder $SLUG"; exit 1; }
echo "DIR=$DIR"
echo "versi: $(grep -o "DEI_VERSION', '[^']*" "$DIR/api/index.php" | cut -d"'" -f3)"
[ -f "$DIR/data/server.php" ] && echo "server.php SUDAH ADA:" && grep -o "'storage' *=> *'[a-z]*'" "$DIR/data/server.php"
du -sh "$DIR/data" | sed 's/^/data: /'
echo "cron:"; crontab -l 2>/dev/null | grep "$SLUG" || echo "  (tidak ada cron untuk $SLUG)"
PHP=$(crontab -l 2>/dev/null | grep "$SLUG" | grep -o '/[^ ]*php[0-9.]*[^ ]*' | grep -v index.php | head -1); PHP=${PHP:-php}
echo "php CLI: $PHP ($($PHP -r 'echo PHP_VERSION;'))"; $PHP -m | grep -qi pdo_mysql && echo "pdo_mysql: ada" || echo "pdo_mysql: TIDAK ADA"
command -v uapi >/dev/null && echo "uapi: ada" || echo "uapi: tidak ada (buat DB manual di cPanel)"
R
[ $? -eq 0 ] || { read -r -p "Gagal. Enter..." _; exit 1; }
echo; read -r -p "Lanjut backup + perbarui kode ke $NEED + pindah ke MySQL? (ketik ya) " J
[ "$J" = "ya" ] || { echo "Dibatalkan."; read -r -p "Enter..." _; exit 0; }

echo; echo "== 2/5 Unggah paket master $NEED =="
scp -P "$SSH_PORT" "$MASTER" "$SSH_USER@$SSH_HOST:~/dei-master-$NEED.zip" || { read -r -p "Gagal unggah. Enter..." _; exit 1; }

echo; echo "== 3/5 Backup + perbarui kode + buat DB + impor =="
"${SSH[@]}" "SLUG=$SLUG NEED=$NEED CPUSER=$SSH_USER bash -s" <<'R'
set -u
DIR=$(ls -d ~/public_html/*/$SLUG ~/*/$SLUG ~/public_html/$SLUG 2>/dev/null | while read d; do [ -f "$d/api/index.php" ] && echo "$d"; done | head -1)
PHP=$(crontab -l 2>/dev/null | grep "$SLUG" | grep -o '/[^ ]*php[0-9.]*[^ ]*' | grep -v index.php | head -1); PHP=${PHP:-php}
TS=$(date +%Y%m%d-%H%M%S); BK=~/backup-$SLUG-pre-mysql-$TS.tar.gz
tar -czf "$BK" -C "$(dirname "$DIR")" "$(basename "$DIR")" || { echo "BACKUP GAGAL — berhenti"; exit 1; }
echo "backup: $BK ($(du -h "$BK" | cut -f1))"

CUR=$(grep -o "DEI_VERSION', '[^']*" "$DIR/api/index.php" | cut -d"'" -f3)
if [ "$(printf '%s\n%s\n' "$CUR" "$NEED" | sort -V | head -1)" != "$NEED" ]; then
  T=~/tmp-dei-master-$TS; mkdir -p "$T" && unzip -q ~/dei-master-$NEED.zip -d "$T" || { echo "unzip gagal"; exit 1; }
  # kode saja: data/ dan .htaccess akar milik tenant tidak disentuh
  rsync -a --exclude '/data/' --exclude '/.htaccess' "$T/dei-chatbot-ai/" "$DIR/" || { echo "rsync gagal"; exit 1; }
  rm -rf "$T"
  echo "kode: $CUR -> $(grep -o "DEI_VERSION', '[^']*" "$DIR/api/index.php" | cut -d"'" -f3)"
else echo "kode: $CUR (sudah >= $NEED)"; fi
rm -f ~/dei-master-$NEED.zip

if [ -f "$DIR/data/server.php" ] && grep -q "'mysql'" "$DIR/data/server.php"; then echo "sudah mode mysql — lewati pembuatan DB"; else
  CRED=~/.dei-$SLUG-db; DB="${CPUSER}_omoway"
  if [ ! -f "$CRED" ]; then
    PW=$(openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 24)
    uapi Mysql create_database name="$DB" | grep -q 'status: 1' || { echo "create_database gagal (sudah ada?)"; exit 1; }
    uapi Mysql create_user name="$DB" password="$PW" | grep -q 'status: 1' || { echo "create_user gagal"; exit 1; }
    uapi Mysql set_privileges_on_database user="$DB" database="$DB" privileges=ALL%20PRIVILEGES | grep -q 'status: 1' || { echo "set_privileges gagal"; exit 1; }
    umask 077; printf 'DB=%s\nPW=%s\n' "$DB" "$PW" > "$CRED"; echo "DB dibuat: $DB"
  fi
  . "$CRED"
  umask 027
  cat > "$DIR/data/server.php" <<PHPEOF
<?php
// v1.2.107: tenant shared hosting memakai MySQL (cara 2). Hapus/ganti nama berkas ini = kembali ke berkas JSON.
return [
    'storage' => 'mysql',
    'queue'   => 'sync',
    'db'      => ['host' => 'localhost', 'port' => 3306, 'name' => '$DB', 'user' => '$DB', 'pass' => '$PW'],
];
PHPEOF
  cd "$DIR" && $PHP api/index.php action=db_init && $PHP api/index.php action=db_import || {
    mv "$DIR/data/server.php" "$DIR/data/server.php.gagal-$TS"; echo "IMPOR GAGAL — dikembalikan ke mode berkas"; exit 1; }
fi

echo; echo "== Verifikasi jumlah (berkas vs MySQL) =="
cd "$DIR" && $PHP -r '
$c = include "data/server.php"; $d = $c["db"];
$p = new PDO("mysql:host=".$d["host"].";dbname=".$d["name"].";charset=utf8mb4", $d["user"], $d["pass"]);
$j = function ($f) { $x = json_decode((string)@file_get_contents("data/$f"), true); return is_array($x) ? count($x) : 0; };
$ids = []; foreach ((array)glob("data/convs/*.jsonl") as $f) foreach (file($f) as $l) { $x = json_decode($l, true); if (!empty($x["id"])) $ids[$x["id"]] = 1; }
foreach ((array)json_decode((string)@file_get_contents("data/conv-open.json"), true) as $x) if (!empty($x["id"])) $ids[$x["id"]] = 1;
$rows = [["log", $j("chatbot-log.json"), "dei_log"], ["kontak", $j("wa-contacts.json"), "dei_contacts"],
         ["sesi WA", count((array)glob("data/wa-sessions/*.json")), "dei_wa_sessions"], ["conv_state", $j("conv-state.json"), "dei_conv_state"],
         ["percakapan", count($ids), "dei_conversations"]];
foreach ($rows as $r) { $n = (int)$p->query("SELECT COUNT(*) FROM ".$r[2])->fetchColumn(); printf("  %-11s berkas %6d  mysql %6d  %s\n", $r[0], $r[1], $n, $n >= $r[1] ? "OK" : "KURANG"); }'
R
RC=$?
echo; echo "== 4/5 Uji alamat publik =="
curl -s "https://chatbot.deintegra.com/$SLUG/api/index.php?action=bootstrap" | head -c 300; echo
echo; echo "== 5/5 Selesai (kode keluar $RC) =="
echo "Cek dashboard: https://chatbot.deintegra.com/$SLUG/dashboard/chatbot-ai/ (Percakapan, Kontak, Statistik)."
read -r -p "Tekan Enter untuk menutup..." _
