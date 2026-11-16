#!/usr/bin/env bash
# v1.2.187 (mitra) + v1.2.188 (mitra-portal) + v1.2.188b (mitra-duitku) — Program Mitra. Pusat saja (tanpa paket tenant).
# Commit master-build + dei-pusat -> push GitHub -> deploy pusat -> cek live.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.188b/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"
TRAILER="Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwdBZa45Umw6CwJiMir"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
for f in index.php signup-lib.php billing-lib.php billing-callback.php partner-lib.php partner-portal-lib.php; do
  php -l "$HERD/dei-pusat/backend/$f" || stop "LINT GAGAL: $f"
done
grep -q "v1.2.188b: mitra-duitku" "$HERD/dei-pusat/admin/index.html" || stop "admin/index.html belum dipatch v1.2.188b"
[[ -f "$HERD/dei-pusat/mitra/index.html" ]] || stop "mitra/index.html tidak ada"
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.187 tools/patch-v1.2.188 tools/patch-v1.2.188b \
  && git commit -qm "tools: patch v1.2.187 mitra, v1.2.188 mitra-portal, v1.2.188b mitra-duitku" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/dei-pusat" && git add admin/index.html daftar/index.html mitra/index.html dev/deploy.sh \
    backend/index.php backend/signup-lib.php backend/billing-lib.php backend/billing-callback.php backend/partner-lib.php backend/partner-portal-lib.php \
  && git commit -qm "Program Mitra: kode mitra di pendaftaran, kartu Mitra, Portal Mitra, komisi hanya dari Duitku (v1.2.187-188b)" -m "$TRAILER" && echo "dei-pusat commit OK") || echo "(dei-pusat: tidak ada yang di-commit)"
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || stop "$R push GAGAL"
done
cd "$HERD/dei-pusat" || stop "folder dei-pusat tidak ada"
[[ -z "$(git status --porcelain)" ]] || { git status --short; stop "dei-pusat masih punya perubahan belum di-commit; deploy dibatalkan."; }
./dev/deploy.sh --go | tail -8
echo "--- cek live ---"
T=$(date +%s)
curl -s "https://chat.deintegra.com/admin/index.html?x=$T" | grep -c "v1.2.188b: mitra-duitku" | sed 's/^/penanda v1.2.188b di admin live (harus >=1): /'
curl -s -o /dev/null -w "halaman /mitra/ HTTP %{http_code} (harus 200)\n" "https://chat.deintegra.com/mitra/?x=$T"
curl -s "https://chat.deintegra.com/daftar/?x=$T" | grep -c 'id="partner_code"' | sed 's/^/isian kode mitra di \/daftar\/ live (harus 1): /'
echo "partner_check: $(curl -s "https://chat.deintegra.com/backend/index.php?action=partner_check&code=TESKODE1")"
echo "mitra_me tanpa login: $(curl -s "https://chat.deintegra.com/backend/index.php?action=mitra_me")"
echo "signup_config: $(curl -s "https://chat.deintegra.com/backend/index.php?action=signup_config" | grep -o '"partner_field":[a-z]*')"
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
