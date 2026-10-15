#!/usr/bin/env bash
# Nyalakan / matikan unduh media WAHA:  ./media.sh on | off | status
set -euo pipefail
cd "$(dirname "$0")"
[[ -f .env ]] || { echo ".env belum ada (cp .env.example .env)"; exit 1; }
case "${1:-status}" in
  on)  v=true ;;
  off) v=false ;;
  status) grep -E '^WAHA_DOWNLOAD_MEDIA=' .env || echo "WAHA_DOWNLOAD_MEDIA belum diset (bawaan: false)"; exit 0 ;;
  *) echo "pakai: ./media.sh on|off|status"; exit 2 ;;
esac
if grep -qE '^WAHA_DOWNLOAD_MEDIA=' .env; then sed -i.bak "s/^WAHA_DOWNLOAD_MEDIA=.*/WAHA_DOWNLOAD_MEDIA=$v/" .env && rm -f .env.bak
else echo "WAHA_DOWNLOAD_MEDIA=$v" >> .env; fi
docker compose up -d
echo "Media WAHA: $v"
