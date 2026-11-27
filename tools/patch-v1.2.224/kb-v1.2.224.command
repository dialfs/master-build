#!/usr/bin/env bash
# v1.2.224: tambah entri KB Asisten Bantuan "tambah-kontak-manual" (guide di manifest) -> commit, push, deploy pusat.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.224/kb.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"
TRAILER="Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwcbRUtZECc2rMNcKZc"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
cd "$HERD/dei-pusat" || stop "dei-pusat tidak ada"
./dev/preflight.sh 2>&1 | tail -4
rm -f .git/*.lock "$HERD/master-build/.git/"*.lock
git add releases/v1.2.224/manifest.json && git commit -qm "release v1.2.224: panduan KB tambah-kontak-manual untuk Asisten Bantuan" -m "$TRAILER" && echo "dei-pusat commit OK"
git pull --ff-only origin main && git push -q origin main && echo "dei-pusat push OK $(git rev-parse --short HEAD)" || stop "push dei-pusat GAGAL"
(cd "$HERD/master-build" && git add tools/patch-v1.2.224/build_v12224.py tools/patch-v1.2.224/kb-v1.2.224.command && git commit -qm "tools: v1.2.224 guide KB tambah-kontak-manual" -m "$TRAILER" && git pull --ff-only origin main && git push -q origin main && echo "master-build push OK") || echo "(master-build: lewati)"
[[ -z "$(git status --porcelain)" ]] || { git status --short; stop "dei-pusat masih ada perubahan; deploy dibatalkan."; }
./dev/deploy.sh --go | tail -4 || stop "DEPLOY GAGAL"
source dev/config.sh
echo; echo "== Cek umpan KB di server =="
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ${REMOTE_ROOT} && grep -c tambah-kontak-manual releases/v1.2.224/manifest.json" | sed 's/^/guide di manifest live (harus 1): /'
echo "Tenant DEI Support menarik umpan KB maksimal 10 menit sekali; setelah itu Asisten Bantuan bisa menjawab."
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
