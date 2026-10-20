#!/usr/bin/env bash
# =============================================================================
# Pasang gateway WAHA di VPS yang SAMA dengan chatbot (tanpa domain publik).
# Dari Mac:  ssh root@212.85.25.180 'bash -s' < ~/Herd/master-build/server/waha/install-waha.sh
# Hasil: WAHA di http://127.0.0.1:3000 (hanya bisa diakses dari VPS ini).
# Di dashboard tenant isi URL Server WAHA = http://127.0.0.1:3000
# Aman diulang: .env (API key) yang sudah ada tidak diganti.
# =============================================================================
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Jalankan sebagai root."; exit 1; }
export DEBIAN_FRONTEND=noninteractive

if ! command -v docker >/dev/null || ! docker compose version >/dev/null 2>&1; then
  echo "==> Docker"
  apt-get update -q
  apt-get install -y -q docker.io docker-compose-v2 || apt-get install -y -q docker.io docker-compose-plugin
  systemctl enable --now docker
fi

mkdir -p /opt/waha/sessions /opt/waha/media && cd /opt/waha
SRC=/opt/dei/server/waha
if [ -f "$SRC/docker-compose.yml" ]; then cp "$SRC/docker-compose.yml" "$SRC/media.sh" /opt/waha/ 2>/dev/null || true; fi
if [ ! -f docker-compose.yml ]; then
cat > docker-compose.yml <<'YML'
services:
  waha:
    image: devlikeapro/waha:${WAHA_TAG:-latest}
    container_name: waha
    restart: always
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      WAHA_API_KEY: ${WAHA_API_KEY}
      WHATSAPP_DEFAULT_ENGINE: ${WAHA_ENGINE:-NOWEB}
      WHATSAPP_RESTART_ALL_SESSIONS: "True"
      WAHA_DASHBOARD_USERNAME: ${WAHA_DASH_USER:-admin}
      WAHA_DASHBOARD_PASSWORD: ${WAHA_DASH_PASS}
      WHATSAPP_SWAGGER_USERNAME: ${WAHA_DASH_USER:-admin}
      WHATSAPP_SWAGGER_PASSWORD: ${WAHA_DASH_PASS}
      TZ: Asia/Jakarta
      WAHA_EVENTS_DOWNLOAD_MEDIA: ${WAHA_DOWNLOAD_MEDIA:-true}
      WAHA_API_DOWNLOAD_MEDIA: ${WAHA_DOWNLOAD_MEDIA:-true}
      WHATSAPP_FILES_LIFETIME: ${WAHA_FILES_LIFETIME:-180}
      WHATSAPP_FILES_FOLDER: /app/.media
    volumes:
      - ./sessions:/app/.sessions
      - ./media:/app/.media
    logging:
      driver: json-file
      options: { max-size: "10m", max-file: "3" }
YML
fi

if [ ! -f .env ]; then
  echo "==> .env (API key acak)"
  cat > .env <<ENV
WAHA_API_KEY=$(openssl rand -hex 24)
WAHA_DASH_USER=admin
WAHA_DASH_PASS=$(openssl rand -hex 12)
WAHA_ENGINE=NOWEB
WAHA_TAG=latest
WAHA_DOWNLOAD_MEDIA=true
WAHA_FILES_LIFETIME=180
ENV
  chmod 600 .env
fi

echo "==> Jalankan WAHA"
docker compose pull -q
docker compose up -d
KEY="$(grep '^WAHA_API_KEY=' .env | cut -d= -f2-)"
for i in $(seq 1 40); do
  if curl -fsS -m 3 -H "X-Api-Key: $KEY" http://127.0.0.1:3000/api/sessions >/dev/null 2>&1; then OK=1; break; fi
  sleep 3
done
[ "${OK:-0}" = 1 ] || { echo "WAHA belum menjawab. Cek: cd /opt/waha && docker compose logs --tail 50"; exit 1; }
VER="$(curl -fsS -m 3 -H "X-Api-Key: $KEY" http://127.0.0.1:3000/api/version 2>/dev/null || true)"

# Backup sesi WA ikut backup harian
grep -q '/opt/waha/sessions' /opt/dei/server/backup.sh 2>/dev/null || \
  echo '30 3 * * * root tar -czf /var/backups/dei/waha-sessions-$(date +\%F).tgz -C /opt/waha sessions && find /var/backups/dei -name "waha-sessions-*" -mtime +14 -delete' > /etc/cron.d/dei-waha

echo
echo "SELESAI. WAHA jalan: $VER"
echo "Isi di dashboard tenant (Widget & API > WhatsApp Bot, penyedia WAHA):"
echo "  URL Server WAHA : http://127.0.0.1:3000"
echo "  API Key WAHA    : $KEY"
echo "  Nama Sesi       : <slug tenant, mis. sinarjaya>"
