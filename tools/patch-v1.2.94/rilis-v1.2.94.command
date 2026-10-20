#!/usr/bin/env bash
# Rilis v1.2.94: push master-build + dei-pusat ke GitHub, lalu deploy dei-pusat ke chat.deintegra.com.
# Deploy live baru jalan setelah Anda ketik "ya".
set -uo pipefail
HERD="$HOME/Herd"
echo "== 1/4 master-build: tarik remote lalu push (arsip tool; gagal tidak menghentikan rilis) =="
cd "$HERD/master-build"
if git pull --rebase --autostash origin main && git push origin HEAD; then echo "master-build OK"
else echo "(!) master-build belum ter-push — lanjut ke dei-pusat. Bereskan nanti: cd ~/Herd/master-build && git status"; git rebase --abort 2>/dev/null; fi
echo; echo "== 2/4 Push dei-pusat =="
cd "$HERD/dei-pusat"
git pull --rebase origin main || { echo "GAGAL tarik dei-pusat — berhenti."; read -r -p "Enter..." _; exit 1; }
git push origin main || { echo "GAGAL push dei-pusat — berhenti."; read -r -p "Enter..." _; exit 1; }
echo; echo "== 3/4 Cek server vs lokal + dry-run deploy =="
./dev/pull.sh | tail -15
./dev/deploy.sh | tail -25
echo
read -r -p "Lanjut deploy LIVE ke chat.deintegra.com? ketik ya: " J
if [[ "$J" == "ya" ]]; then
  echo "== 4/4 Deploy =="
  ./dev/deploy.sh --go | tail -15
  echo; echo "Cek manifest:"; curl -s https://chat.deintegra.com/releases/v1.2.94/manifest.json | head -8
else
  echo "Deploy dibatalkan (push GitHub sudah jalan)."
fi
echo
read -r -p "Nyalakan unduh media di VPS WAHA (212.85.25.180) sekarang? ketik ya: " M
if [[ "$M" == "ya" ]]; then ssh root@212.85.25.180 'cd /opt/waha && ./media.sh on && ./media.sh status'; fi
echo; read -r -p "Tekan Enter untuk menutup..." _
