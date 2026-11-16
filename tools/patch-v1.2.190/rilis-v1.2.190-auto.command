#!/usr/bin/env bash
# v1.2.190 (admin-tampilan) — tampilan baru Admin Pusat (sidebar, top bar, halaman per menu) + favicon. Pusat saja, hanya tampilan.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.190/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"
TRAILER="Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwdBZa45Umw6CwJiMir"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
grep -q "v1.2.190: admin-tampilan" "$HERD/dei-pusat/admin/index.html" || stop "admin/index.html belum dipatch v1.2.190"
[[ -f "$HERD/dei-pusat/admin/favicon.svg" ]] || stop "admin/favicon.svg tidak ada"
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.189 tools/patch-v1.2.190 \
  && git commit -qm "tools: patch v1.2.190 admin-tampilan" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/dei-pusat" && git add admin/index.html admin/login.html admin/favicon.svg \
  && git commit -qm "Admin Pusat: tampilan baru dengan sidebar + favicon (v1.2.190)" -m "$TRAILER" && echo "dei-pusat commit OK") || echo "(dei-pusat: tidak ada yang di-commit)"
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || stop "$R push GAGAL"
done
cd "$HERD/dei-pusat" || stop "folder dei-pusat tidak ada"
[[ -z "$(git status --porcelain)" ]] || { git status --short; stop "dei-pusat masih punya perubahan belum di-commit; deploy dibatalkan."; }
./dev/deploy.sh --go | tail -8
echo "--- cek live ---"
T=$(date +%s)
curl -s "https://chat.deintegra.com/admin/index.html?x=$T" | grep -c "v1.2.190: admin-tampilan" | sed 's/^/penanda v1.2.190 di admin live (harus >=1): /'
curl -s -o /dev/null -w "favicon HTTP %{http_code} %{content_type} (harus 200 image/svg+xml)\n" "https://chat.deintegra.com/admin/favicon.svg?x=$T"
curl -s "https://chat.deintegra.com/admin/login.html?x=$T" | grep -c 'rel="icon"' | sed 's/^/favicon di halaman login live (harus 1): /'
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
