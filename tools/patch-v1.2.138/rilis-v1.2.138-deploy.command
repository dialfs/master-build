#!/usr/bin/env bash
# v1.2.138: deploy saja (build & push GitHub sudah selesai lewat HTTPS 4 Nov). Log: deploy.log
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.138/deploy.log") 2>&1
set -uo pipefail
# SSH GitHub sedang ditolak (4 Nov) -> git lewat HTTPS hanya untuk skrip ini (remote tidak diubah)
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0="url.https://github.com/.insteadOf" GIT_CONFIG_VALUE_0="git@github.com:"
cd "$HOME/Herd/dei-pusat"
git status -sb | head -1
echo "== Cek server vs lokal + dry-run =="
git fetch -q origin && git status -sb | head -1
echo "== Deploy LIVE (atas perintah Dias) =="
./dev/deploy.sh --go | tail -15
echo; echo "Cek manifest:"; curl -s https://chat.deintegra.com/releases/v1.2.138/manifest.json | head -8
echo; echo "Cek endpoint klasifikasi (harus menolak tanpa lisensi):"; curl -s -X POST 'https://chat.deintegra.com/backend/index.php?action=classify' -H 'Content-Type: application/json' -d '{}'; echo
echo; read -r -p "Tekan Enter untuk menutup..." _
