#!/usr/bin/env bash
# Rilis v1.2.118 (close-deal-lose) + v1.2.119 (agent-stage). Log: ~/Herd/master-build/tools/patch-v1.2.119/rilis.log
# Paket sudah dibangun (releases/v1.2.119, master/, dei-tenant lokal sudah dipatch).
# Skrip ini: php -l, commit + push master-build & dei-pusat, dry-run deploy, lalu deploy LIVE.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.119/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"
TRAILER=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01F3pjwaXVYSm1bYBUyByUiQ'
echo "== 0/4 Lint =="
php -l "$HERD/dei-tenant/api/index.php" || { echo "LINT GAGAL — berhenti."; read -r -p "Enter..." _; exit 1; }
echo; echo "== 1/4 master-build: commit + push (arsip tool) =="
cd "$HERD/master-build"
git add tools/patch-v1.2.118/*.py tools/patch-v1.2.118/*.command tools/patch-v1.2.119/*.py tools/patch-v1.2.119/*.command
git commit -m "tools: patch v1.2.118 close-deal-lose + v1.2.119 agent-stage${TRAILER}" || true
if git pull --rebase --autostash origin main && git push origin HEAD; then echo "master-build OK"
else echo "(!) master-build belum ter-push — bereskan nanti"; git rebase --abort 2>/dev/null; fi
echo; echo "== 2/4 dei-pusat: commit + push =="
cd "$HERD/dei-pusat"
./dev/preflight.sh | tail -8
git add releases/v1.2.118 releases/v1.2.119 master/dei-master.zip master/master.json
git commit -m "release: v1.2.118 (Close Deal & Close Lose) + v1.2.119 (Batasi Agent per Lead Rating)${TRAILER}" || true
git pull --rebase origin main || { echo "GAGAL tarik dei-pusat — berhenti."; read -r -p "Enter..." _; exit 1; }
git push origin main || { echo "GAGAL push dei-pusat — berhenti."; read -r -p "Enter..." _; exit 1; }
echo; echo "== 3/4 Cek server vs lokal + dry-run deploy =="
./dev/pull.sh | tail -15
./dev/deploy.sh | tail -25
echo
J=ya; echo "Deploy LIVE (otomatis ya — diminta Dias)"
if [[ "$J" == "ya" ]]; then
  echo "== 4/4 Deploy =="
  ./dev/deploy.sh --go | tail -15
  echo; echo "Cek manifest:"; curl -s https://chat.deintegra.com/releases/v1.2.118/manifest.json | head -3; curl -s https://chat.deintegra.com/releases/v1.2.119/manifest.json | head -8
else
  echo "Deploy dibatalkan (GitHub sudah terisi; jalankan ulang skrip ini kapan saja)."
fi
echo; read -r -p "Tekan Enter untuk menutup..." _
