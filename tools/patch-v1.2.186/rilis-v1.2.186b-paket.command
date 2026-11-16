#!/usr/bin/env bash
# v1.2.186b (grup-paket) — Dashboard Grup hanya untuk tenant paket Business ke atas. Pusat saja (tanpa paket tenant).
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.186/rilis-b.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; SESS="Claude-Session: https://claude.ai/code/session_01F3pjwcqjhpuLFgGpUzbA1J"
for f in "$HERD/dei-pusat/backend/index.php" "$HERD/dei-pusat/backend/group-lib.php"; do php -l "$f" || { echo "LINT GAGAL"; read -r -p "Enter..." _; exit 1; }; done
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.186 && git commit -qm "tools: patch v1.2.186b grup-paket" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
$SESS" && echo "master-build commit OK")
(cd "$HERD/dei-pusat" && git add backend/index.php backend/group-lib.php grup/index.html admin/index.html && git commit -qm "Dashboard Grup: hanya tenant paket Business ke atas (v1.2.186b)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
$SESS" && echo "dei-pusat commit OK")
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || { echo "$R push GAGAL"; read -r -p "Enter..." _; exit 1; }
done
cd "$HERD/dei-pusat" && ./dev/deploy.sh --go | tail -6
curl -s "https://chat.deintegra.com/admin/index.html?x=$(date +%s)" | grep -c "v1.2.186b" | sed 's/^/penanda v1.2.186b di admin live: /'
read -r -p "Tekan Enter untuk menutup..." _
