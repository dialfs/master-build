#!/usr/bin/env bash
# =============================================================================
# DEI Chatbot — pasang update dari dei-pusat ke semua klien di VPS ini.
#   sudo /opt/dei/server/update-all.sh            # semua klien
#   sudo /opt/dei/server/update-all.sh sinarjaya  # satu klien
# Memakai updater bawaan aplikasi (action=update_cli) — sama dengan tombol
# "Pasang Update" di dashboard: unduh, cek md5, backup, ganti 5 berkas.
# Worker dijalankan ulang supaya memuat kode baru.
# =============================================================================
set -uo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Jalankan sebagai root (sudo)."; exit 1; }
ONLY="${1:-}"; FAIL=0
for C in /etc/dei/clients/*.conf; do
  [ -e "$C" ] || { echo "Belum ada klien."; exit 0; }
  SLUG=""; BRAND=""; . "$C"
  [ -n "$ONLY" ] && [ "$ONLY" != "$SLUG" ] && continue
  DIR="/var/www/$SLUG"; USR="dei-$SLUG"
  BEFORE="$(grep -o "define('DEI_VERSION', '[^']*')" "$DIR/api/index.php" | cut -d"'" -f4)"
  OUT="$(sudo -u "$USR" php "$DIR/api/index.php" action=update_cli 2>&1)"; RC=$?
  AFTER="$(grep -o "define('DEI_VERSION', '[^']*')" "$DIR/api/index.php" | cut -d"'" -f4)"
  if [ $RC -ne 0 ] || echo "$OUT" | grep -q '"ok":false'; then
    echo "[$SLUG] GAGAL ($BEFORE): $OUT"; FAIL=1; continue
  fi
  # v1.2.73: pastikan ikon/logo brand tetap terpasang (idempoten)
  if [ -n "${BRAND:-}" ] && [ "${BRAND}" != "none" ] && [ -d "/opt/dei/server/brand/$BRAND" ]; then
    install -o "$USR" -g "$USR" -m 640 /opt/dei/server/brand/"$BRAND"/{favicon.ico,favicon-32.png,apple-touch-icon.png,icon-192.png,icon-512.png,logo-256.png,manifest.json} "$DIR/dashboard/chatbot-ai/"
  fi
  if [ "$BEFORE" != "$AFTER" ]; then
    sudo -u "$USR" php "$DIR/api/index.php" action=db_init >/dev/null   # tabel baru (kalau ada) dibuat
    supervisorctl restart "dei-$SLUG-worker:*" >/dev/null
    echo "[$SLUG] $BEFORE -> $AFTER, worker dijalankan ulang"
  else
    echo "[$SLUG] $AFTER (tidak ada update)"
  fi
done
exit $FAIL
