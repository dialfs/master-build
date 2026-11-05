#!/usr/bin/env bash
# Rilis v1.2.149 (kepala-chat-mobile) — disiapkan 5 Nov 2026.
# Paket SUDAH di-build & di-push ke GitHub (dei-pusat + master-build) dari sesi cloud.
# Skrip ini: tarik GitHub, patch dei-tenant lokal (supaya sinkron), cek md5, deploy LIVE.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.149/rilis.log") 2>&1
set -uo pipefail
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0="url.https://github.com/.insteadOf" GIT_CONFIG_VALUE_0="git@github.com:"
HERD="$HOME/Herd"; V=v1.2.149
echo "== 1/4 Tarik GitHub =="
cd "$HERD/master-build" && git pull --ff-only origin main || { echo "master-build pull GAGAL"; read -r -p "Enter..." _; exit 1; }
cd "$HERD/dei-pusat" && git pull --ff-only origin main || { echo "dei-pusat pull GAGAL"; read -r -p "Enter..." _; exit 1; }
echo; echo "== 2/4 Patch dei-tenant lokal + cocokkan dengan paket =="
python3 "$HERD/master-build/tools/patch-v1.2.149/patch_v12149.py" "$HERD/dei-tenant" || { echo "PATCH GAGAL"; read -r -p "Enter..." _; exit 1; }
php -l "$HERD/dei-tenant/api/index.php" || { echo "LINT GAGAL"; read -r -p "Enter..." _; exit 1; }
python3 - "$HERD" <<'PY'
import zipfile,hashlib,sys
H=sys.argv[1]; z=zipfile.ZipFile(H+'/dei-pusat/releases/v1.2.149/update.zip')
for f in ['api/index.php','dashboard/chatbot-ai/index.html']:
    a=hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest(); b=hashlib.md5(open(H+'/dei-tenant/'+f,'rb').read()).hexdigest()
    print(('OK   ' if a==b else 'BEDA ')+f)
PY
echo "(BEDA = dei-tenant lokal punya perubahan lain di luar v1.2.148; paket tetap dari salinan v1.2.148 + patch ini)"
echo; echo "== 3/4 Deploy LIVE (rsync) =="
cd "$HERD/dei-pusat"
./dev/preflight.sh | tail -3 || { echo "PREFLIGHT GAGAL"; read -r -p "Enter..." _; exit 1; }
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
