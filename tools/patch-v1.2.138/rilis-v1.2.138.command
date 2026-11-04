#!/usr/bin/env bash
# Rilis v1.2.138 (filter-topik). Log: ~/Herd/master-build/tools/patch-v1.2.138/rilis.log
# dei-tenant & dei-pusat lokal sudah dipatch. Skrip ini: php -l, build, commit + push master-build & dei-pusat, dry-run, lalu deploy LIVE.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.138/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"
TRAILER=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01F3pjwbEwuZQcRY9FTXj4ed'
echo "== 0/4 Build + Lint =="
for f in "$HERD/dei-tenant/api/index.php" "$HERD/dei-pusat/backend/index.php" "$HERD/dei-pusat/backend/cron-tick.php" "$HERD/dei-pusat/backend/classify-lib.php"; do
  php -l "$f" || { echo "LINT GAGAL — berhenti."; read -r -p "Enter..." _; exit 1; }
done
python3 "$HERD/master-build/tools/patch-v1.2.138/build_v12138.py" || { echo "BUILD GAGAL — berhenti."; read -r -p "Enter..." _; exit 1; }
echo; echo "== 1/4 master-build: commit + push (arsip tool) =="
cd "$HERD/master-build"
git add tools/patch-v1.2.138/*.py tools/patch-v1.2.138/*.command tools/patch-v1.2.138/*.php tools/patch-v1.2.138/*.js tools/patch-v1.2.138/*.html tools/patch-v1.2.138/*.css
git commit -m "tools: patch v1.2.138 filter-topik${TRAILER}" || true
if git pull --rebase --autostash origin main && git push origin HEAD; then echo "master-build OK"
else echo "(!) master-build belum ter-push — bereskan nanti"; git rebase --abort 2>/dev/null; fi
echo; echo "== 2/4 dei-pusat: commit + push =="
cd "$HERD/dei-pusat"
./dev/preflight.sh | tail -8
git add releases/v1.2.138 master/dei-master.zip master/master.json backend/index.php backend/cron-tick.php backend/classify-lib.php admin/index.html
git commit -m "release: v1.2.138 (Filter Topik & Divisi chat WA + klasifikasi pusat; Customer Feedback mulai Growth)${TRAILER}" || true
git pull --rebase origin main || { echo "GAGAL tarik dei-pusat — berhenti."; read -r -p "Enter..." _; exit 1; }
git push origin main || { echo "GAGAL push dei-pusat — berhenti."; read -r -p "Enter..." _; exit 1; }
echo; echo "== 3/4 Cek server vs lokal + dry-run deploy =="
./dev/pull.sh | tail -15
./dev/deploy.sh | tail -25
echo
read -r -p "Deploy LIVE sekarang? ketik ya: " J
if [[ "$J" == "ya" ]]; then
  echo "== 4/4 Deploy =="
  ./dev/deploy.sh --go | tail -15
  echo; echo "Cek manifest:"; curl -s https://chat.deintegra.com/releases/v1.2.138/manifest.json | head -8
  echo; echo "Cek endpoint klasifikasi (harus menolak tanpa lisensi):"; curl -s -X POST 'https://chat.deintegra.com/backend/index.php?action=classify' -H 'Content-Type: application/json' -d '{}'; echo
else
  echo "Deploy dibatalkan (GitHub sudah terisi; jalankan ulang skrip ini kapan saja)."
fi
echo; read -r -p "Tekan Enter untuk menutup..." _
