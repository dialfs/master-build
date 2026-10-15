#!/usr/bin/env bash
# DEI Chatbot — backup harian per klien: dump MySQL + folder data/. Dipanggil cron 02:30.
set -uo pipefail
umask 077   # isi backup = data klien
. /etc/dei/backup.conf
KEEP_DAYS="${KEEP_DAYS:-30}"; STAMP="$(date +%Y%m%d-%H%M)"; ERR=0
for C in /etc/dei/clients/*.conf; do
  [ -e "$C" ] || exit 0
  SLUG=""; DB=""; . "$C"
  OUT="/var/backups/dei/$SLUG"; mkdir -p "$OUT"
  mysqldump --single-transaction --quick --routines "$DB" | gzip > "$OUT/$STAMP-db.sql.gz" || ERR=1
  tar czf "$OUT/$STAMP-data.tgz" -C "/var/www/$SLUG" --exclude='data/.locks' --exclude='data/backup*' data || ERR=1
  find "$OUT" -type f -mtime +"$KEEP_DAYS" -delete
done
if [ -n "${RCLONE_REMOTE:-}" ] && command -v rclone >/dev/null; then
  rclone copy /var/backups/dei "$RCLONE_REMOTE" --max-age 2d || ERR=1
fi
[ $ERR -eq 0 ] && echo "$(date '+%F %T') backup OK" || { echo "$(date '+%F %T') backup ADA YANG GAGAL"; /opt/dei/server/health.sh --alert "Backup harian ada yang gagal di $(hostname)"; }
