#!/usr/bin/env bash
# Rilis v1.2.148 (selesai-tanpa-flag) — disiapkan 4 Nov 2026.
# Paket sudah di-build (releases/v1.2.148 + master). Skrip ini: php -l, commit, push GitHub (HTTPS, tidak wajib), deploy LIVE langsung.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.148/rilis.log") 2>&1
set -uo pipefail
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0="url.https://github.com/.insteadOf" GIT_CONFIG_VALUE_0="git@github.com:"
HERD="$HOME/Herd"; V=v1.2.148
TRAILER=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01F3pjwcsc4vcGfqmQNsWP2t'
echo "== 0/4 Lint =="
php -l "$HERD/dei-tenant/api/index.php" || { echo "LINT GAGAL — berhenti."; read -r -p "Enter..." _; exit 1; }
echo; echo "== 1/4 master-build: commit + push =="
cd "$HERD/master-build"
git add tools/patch-v1.2.148/*.py tools/patch-v1.2.148/*.command 2>/dev/null
git commit -qm "tools: patch $V selesai-tanpa-flag${TRAILER}" || true
git push origin HEAD:main && echo "master-build PUSH OK" || echo "(!) master-build belum ter-push — susul nanti"
echo; echo "== 2/4 dei-pusat: preflight + commit + push =="
cd "$HERD/dei-pusat"
./dev/preflight.sh | tail -6 || { echo "PREFLIGHT GAGAL — berhenti."; read -r -p "Enter..." _; exit 1; }
git add releases/$V master/dei-master.zip master/master.json
git commit -qm "release: $V (tombol Selesai tanpa flag)${TRAILER}" || true
git push origin main && echo "dei-pusat PUSH OK" || echo "(!) dei-pusat belum ter-push (GitHub) — deploy tetap jalan, push susul nanti"
git status -sb | head -1
[[ -z "$(git status --porcelain -- releases master backend admin daftar)" ]] || { echo "BATAL: ada perubahan belum di-commit."; git status --short | head; read -r -p "Enter..." _; exit 1; }
echo; echo "== 3/4 Deploy LIVE (rsync langsung) =="
source dev/config.sh
ARGS=(-az --stats --human-readable --itemize-changes --checksum)
for e in "${EXCLUDES[@]}"; do ARGS+=(--exclude "$e"); done
rsync "${ARGS[@]}" -e "ssh -p ${SSH_PORT}" "$PWD/" "${SSH_USER}@${SSH_HOST}:${REMOTE_ROOT}/" | tail -12
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ${REMOTE_ROOT} && \
  find admin backend master releases daftar -type d -exec chmod 755 {} + && \
  find admin backend master releases daftar -type f \( -name '*.html' -o -name '*.php' -o -name '*.css' -o -name '*.js' \
    -o -name '*.json' -o -name '*.zip' -o -name '*.svg' -o -name '*.ico' -o -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.webp' -o -name '*.gif' \) -exec chmod 644 {} +" \
  && echo "Permission OK." || echo "(!) chmod gagal, cek manual kalau ada 403."
echo; echo "== 4/4 Cek manifest live =="
curl -s https://chat.deintegra.com/releases/$V/manifest.json | head -8
echo; read -r -p "Tekan Enter untuk menutup..." _
