#!/usr/bin/env bash
# Versi TANPA konfirmasi (dijalankan atas perintah Dias "commit deploy").
# Rilis v1.2.139 (topik-riwayat). Log: ~/Herd/master-build/tools/patch-v1.2.139/rilis.log
# dei-tenant & dei-pusat lokal sudah dipatch. Skrip ini: php -l, build, commit + push master-build & dei-pusat, dry-run, lalu deploy LIVE.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.139/rilis.log") 2>&1
set -uo pipefail
# SSH GitHub ditolak sejak 4 Nov -> git lewat HTTPS hanya untuk skrip ini (remote tidak diubah)
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0="url.https://github.com/.insteadOf" GIT_CONFIG_VALUE_0="git@github.com:"
HERD="$HOME/Herd"
TRAILER=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01F3pjwbEwuZQcRY9FTXj4ed'
echo "== 0/4 Build + Lint =="
for f in "$HERD/dei-tenant/api/index.php"; do
  php -l "$f" || { echo "LINT GAGAL — berhenti."; read -r -p "Enter..." _; exit 1; }
done
python3 "$HERD/master-build/tools/patch-v1.2.139/build_v12139.py" || { echo "BUILD GAGAL — berhenti."; read -r -p "Enter..." _; exit 1; }
echo; echo "== 1/4 master-build: commit + push (arsip tool) =="
cd "$HERD/master-build"
git add tools/patch-v1.2.139/*.py tools/patch-v1.2.139/*.command tools/patch-v1.2.138/*.command
git commit -m "tools: patch v1.2.139 topik-riwayat${TRAILER}" || true
if git pull --rebase --autostash origin main && git push origin HEAD; then echo "master-build OK"
else echo "(!) master-build belum ter-push — bereskan nanti"; git rebase --abort 2>/dev/null; fi
echo; echo "== 2/4 dei-pusat: commit + push =="
cd "$HERD/dei-pusat"
./dev/preflight.sh | tail -8
git add releases/v1.2.139 master/dei-master.zip master/master.json
git commit -m "release: v1.2.139 (Filter Topik membaca riwayat impor WAHA + scan chat lama per periode)${TRAILER}" || true
git pull --rebase origin main || { echo "GAGAL tarik dei-pusat — berhenti."; read -r -p "Enter..." _; exit 1; }
git push origin main || { echo "GAGAL push dei-pusat — berhenti."; read -r -p "Enter..." _; exit 1; }
echo; echo "== 3/4 Cek server vs lokal + dry-run deploy =="
./dev/pull.sh | tail -15
./dev/deploy.sh | tail -25
echo
J=ya; echo "Deploy LIVE otomatis (atas perintah Dias)."
if [[ "$J" == "ya" ]]; then
  echo "== 4/4 Deploy =="
  ./dev/deploy.sh --go | tail -15
  echo; echo "Cek manifest:"; curl -s https://chat.deintegra.com/releases/v1.2.139/manifest.json | head -8
  echo; echo "Cek endpoint klasifikasi (harus menolak tanpa lisensi):"; curl -s -X POST 'https://chat.deintegra.com/backend/index.php?action=classify' -H 'Content-Type: application/json' -d '{}'; echo
else
  echo "Deploy dibatalkan (GitHub sudah terisi; jalankan ulang skrip ini kapan saja)."
fi
echo; read -r -p "Tekan Enter untuk menutup..." _
