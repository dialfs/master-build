#!/usr/bin/env bash
# v1.2.191 (mitra-skema) — skema komisi per mitra: default / persentase tetap / tier khusus. Pusat saja (tanpa paket tenant).
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.191/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"
TRAILER="Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwdBZa45Umw6CwJiMir"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
for f in index.php partner-lib.php partner-portal-lib.php; do php -l "$HERD/dei-pusat/backend/$f" || stop "LINT GAGAL: $f"; done
grep -q "v1.2.191: mitra-skema" "$HERD/dei-pusat/admin/index.html" || stop "admin/index.html belum dipatch v1.2.191"
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.187 tools/patch-v1.2.188 tools/patch-v1.2.188b tools/patch-v1.2.189 tools/patch-v1.2.190 tools/patch-v1.2.191 \
  && git commit -qm "tools: patch v1.2.191 mitra-skema" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/dei-pusat" && git add admin/index.html mitra/index.html backend/index.php backend/partner-lib.php backend/partner-portal-lib.php \
  && git commit -qm "Program Mitra: skema komisi per mitra (default, persentase tetap, tier khusus) (v1.2.191)" -m "$TRAILER" && echo "dei-pusat commit OK") || echo "(dei-pusat: tidak ada yang di-commit)"
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || stop "$R push GAGAL"
done
cd "$HERD/dei-pusat" || stop "folder dei-pusat tidak ada"
[[ -z "$(git status --porcelain)" ]] || { git status --short; stop "dei-pusat masih punya perubahan belum di-commit; deploy dibatalkan."; }
./dev/deploy.sh --go | tail -8
echo "--- cek live ---"
T=$(date +%s)
curl -s "https://chat.deintegra.com/admin/index.html?x=$T" | grep -c "v1.2.191: mitra-skema" | sed 's/^/penanda v1.2.191 di admin live (harus >=1): /'
curl -s "https://chat.deintegra.com/mitra/?x=$T" | grep -c "v1.2.191: mitra-skema" | sed 's/^/penanda v1.2.191 di \/mitra\/ live (harus >=1): /'
echo "partner_check (backend masih sehat): $(curl -s "https://chat.deintegra.com/backend/index.php?action=partner_check&code=TESKODE1")"
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
