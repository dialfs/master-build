#!/usr/bin/env bash
# DEI Chatbot — cek tiap 5 menit: antrean menumpuk, worker mati, job gagal permanen.
# Kirim Telegram kalau ada masalah (isi /etc/dei/alert.conf).
set -uo pipefail
. /etc/dei/alert.conf
send() { [ -n "${TG_BOT_TOKEN:-}" ] && [ -n "${TG_CHAT_ID:-}" ] && curl -fsS -m 10 "https://api.telegram.org/bot$TG_BOT_TOKEN/sendMessage" \
  --data-urlencode "chat_id=$TG_CHAT_ID" --data-urlencode "text=$1" >/dev/null; echo "$(date '+%F %T') $1"; }
[ "${1:-}" = "--alert" ] && { send "$2"; exit 0; }
for SVC in nginx php8.3-fpm mysql redis-server supervisor; do systemctl is-active --quiet "$SVC" || send "[$(hostname)] layanan $SVC MATI"; done
for C in /etc/dei/clients/*.conf; do
  [ -e "$C" ] || exit 0
  SLUG=""; WORKERS=0; . "$C"
  J="$(sudo -u "dei-$SLUG" php "/var/www/$SLUG/api/index.php" action=wa_queue_status 2>/dev/null)" || { send "[$SLUG] status antrean tidak bisa dibaca"; continue; }
  P="$(echo "$J" | jq -r '.pending // 0')"; D="$(echo "$J" | jq -r '.dead // 0')"; A="$(echo "$J" | jq -r '.workers_alive // 0')"
  [ "$P" -gt "${QUEUE_ALERT:-200}" ] && send "[$SLUG] antrean menumpuk: $P pesan menunggu (worker hidup $A/$WORKERS)"
  [ "$A" -eq 0 ] && send "[$SLUG] TIDAK ADA worker hidup — pesan WA tidak dibalas"
  LAST="/var/lib/dei-health-$SLUG.dead"; PREV="$(cat "$LAST" 2>/dev/null || echo 0)"
  [ "$D" -gt "$PREV" ] && send "[$SLUG] $((D-PREV)) job WA gagal permanen (lihat /var/log/dei/$SLUG-worker.log)"
  echo "$D" > "$LAST"
done
