#!/usr/bin/env bash
# Rilis v1.2.76: push master-build + dei-pusat ke GitHub, lalu deploy dei-pusat ke chat.deintegra.com.
# Klik dua kali di Finder. Deploy live baru jalan setelah Anda ketik "ya".
set -euo pipefail
HERD="$HOME/Herd"
echo "== 1/4 Push master-build =="
cd "$HERD/master-build" && git push origin HEAD
echo; echo "== 2/4 Push dei-pusat =="
cd "$HERD/dei-pusat" && git push origin main
echo; echo "== 3/4 Cek server vs lokal + dry-run deploy =="
./dev/pull.sh | tail -15
./dev/deploy.sh | tail -25
echo
read -r -p "Lanjut deploy LIVE ke chat.deintegra.com? ketik ya: " J
if [[ "$J" == "ya" ]]; then
  echo "== 4/4 Deploy =="
  ./dev/deploy.sh --go | tail -15
  echo; echo "Cek manifest:"; curl -s https://chat.deintegra.com/releases/v1.2.76/manifest.json | head -8
else
  echo "Deploy dibatalkan (push GitHub sudah jalan)."
fi
echo; read -r -p "Tekan Enter untuk menutup..." _
