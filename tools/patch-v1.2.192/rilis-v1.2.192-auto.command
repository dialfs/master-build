#!/usr/bin/env bash
# v1.2.192 (asisten-support) — umpan KB & pengaturan tenant Support. Pusat saja (tanpa paket tenant).
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.192/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"
TRAILER="Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwcAJ8kPdQosx8u6HFb"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
python3 "$HERD/master-build/tools/patch-v1.2.192/patch_pusat_v12192.py" "$HERD/dei-pusat" || stop "PATCH GAGAL"
for f in index.php support-lib.php; do php -l "$HERD/dei-pusat/backend/$f" || stop "LINT GAGAL: $f"; done
grep -q "v1.2.192: asisten-support" "$HERD/dei-pusat/admin/index.html" || stop "admin/index.html belum dipatch v1.2.192"
(cd "$HERD/dei-pusat" && ./dev/preflight.sh) || stop "PREFLIGHT GAGAL"
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.192 \
  && git commit -qm "tools: patch v1.2.192 asisten-support" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/dei-pusat" && git add admin/index.html backend/index.php backend/support-lib.php dev/preflight.sh \
  && git commit -qm "Asisten Support: umpan KB dari rilis + pengaturan tenant Support (v1.2.192)" -m "$TRAILER" && echo "dei-pusat commit OK") || echo "(dei-pusat: tidak ada yang di-commit)"
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || stop "$R push GAGAL"
done
cd "$HERD/dei-pusat" || stop "folder dei-pusat tidak ada"
[[ -z "$(git status --porcelain)" ]] || { git status --short; stop "dei-pusat masih punya perubahan belum di-commit; deploy dibatalkan."; }
./dev/deploy.sh --go | tail -8
echo "--- cek live ---"
T=$(date +%s)
curl -s "https://chat.deintegra.com/admin/index.html?x=$T" | grep -c "v1.2.192: asisten-support" | sed 's/^/penanda v1.2.192 di admin live (harus >=1): /'
echo "support_kb_feed tanpa kunci (harus: tenant_id & license_key wajib): $(curl -s -X POST "https://chat.deintegra.com/backend/index.php?action=support_kb_feed")"
echo "partner_check (backend masih sehat): $(curl -s "https://chat.deintegra.com/backend/index.php?action=partner_check&code=TESKODE1")"
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
