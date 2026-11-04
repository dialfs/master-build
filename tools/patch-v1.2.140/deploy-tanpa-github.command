#!/usr/bin/env bash
# v1.2.140: deploy LANGSUNG tanpa menunggu GitHub (atas persetujuan Dias, 4 Nov 17:35 — GitHub sedang insiden).
# Sama dengan dev/deploy.sh --go tetapi TANPA cek "lokal == GitHub". Push GitHub menyusul.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.140/deploy-tanpa-github.log") 2>&1
set -uo pipefail
ROOT="$HOME/Herd/dei-pusat"; DIR="$ROOT/dev"; cd "$ROOT"
source "$DIR/config.sh"
git status -sb | head -1
[[ -z "$(git status --porcelain)" ]] || { echo "BATAL: ada perubahan belum di-commit."; read -r -p "Enter..." _; exit 1; }
"$DIR/preflight.sh" || { echo "BATAL: preflight gagal."; read -r -p "Enter..." _; exit 1; }
ARGS=(-az --stats --human-readable --itemize-changes --checksum)
for e in "${EXCLUDES[@]}"; do ARGS+=(--exclude "$e"); done
echo "MODE: UPLOAD"
rsync "${ARGS[@]}" -e "ssh -p ${SSH_PORT}" "$ROOT/" "${SSH_USER}@${SSH_HOST}:${REMOTE_ROOT}/" | tail -12
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ${REMOTE_ROOT} && \
  find admin backend master releases daftar -type d -exec chmod 755 {} + && \
  find admin backend master releases daftar -type f \( -name '*.html' -o -name '*.php' -o -name '*.css' -o -name '*.js' \
    -o -name '*.json' -o -name '*.zip' -o -name '*.svg' -o -name '*.ico' -o -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.webp' -o -name '*.gif' \) -exec chmod 644 {} +" \
  && echo "Permission OK." || echo "(!) chmod gagal, cek manual kalau ada 403."
echo; echo "Cek manifest:"; curl -s https://chat.deintegra.com/releases/v1.2.140/manifest.json | head -8
echo; read -r -p "Tekan Enter untuk menutup..." _
