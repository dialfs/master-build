#!/usr/bin/env bash
# Rilis v1.2.184 (lupa-password) — 16 Nov 2026: reset password lewat email dari halaman login.
# Paket tenant: api/index.php + dashboard index.html + app.js + login.html. Pusat: backend/index.php (action mail_relay).
# Patch sudah diterapkan lokal. Skrip ini: lint, build paket, commit + push GitHub, cek md5, deploy LIVE pusat, tes kirim email.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.184/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; V=v1.2.184; TD="$HERD/master-build/tools/patch-v1.2.184"
SESS="Claude-Session: https://claude.ai/code/session_01F3pjwfBxw1JfN4z2Pv4xFL"
TES_KE="${TES_KE:-dialfs@gmail.com}"
echo "== 0/5 Lint & build paket =="
for f in "$HERD/dei-tenant/api/index.php" "$HERD/dei-pusat/backend/index.php"; do
  php -l "$f" || { echo "LINT GAGAL — tidak ada yang dikirim"; read -r -p "Enter..." _; exit 1; }
done
python3 "$TD/build_v12184.py" "$HERD" || { echo "BUILD GAGAL"; read -r -p "Enter..." _; exit 1; }
echo; echo "== 1/5 Commit, sinkron & push GitHub =="
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.184; git commit -qm "tools: patch v1.2.184 lupa-password" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
$SESS" && echo "master-build commit OK")
(cd "$HERD/dei-pusat" && git add backend/index.php releases/v1.2.184 master/dei-master.zip master/master.json && git commit -qm "release v1.2.184 lupa-password (+ mail_relay pusat)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
$SESS" && echo "dei-pusat commit OK")
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || { echo "$R sinkron/push GAGAL"; read -r -p "Enter..." _; exit 1; }
done
echo; echo "== 2/5 Cocokkan paket dengan dei-tenant lokal =="
python3 - "$HERD" <<'PY'
import zipfile,hashlib,sys
H=sys.argv[1]; z=zipfile.ZipFile(H+'/dei-pusat/releases/v1.2.184/update.zip')
for f in ['api/index.php','dashboard/chatbot-ai/index.html','dashboard/chatbot-ai/app.js','dashboard/chatbot-ai/login.html']:
    a=hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest(); b=hashlib.md5(open(H+'/dei-tenant/'+f,'rb').read()).hexdigest()
    print(('OK   ' if a==b else 'BEDA ')+f)
PY
echo; echo "== 3/5 Deploy LIVE (rsync) =="
cd "$HERD/dei-pusat"
./dev/preflight.sh | tail -3 || { echo "PREFLIGHT GAGAL"; read -r -p "Enter..." _; exit 1; }
source dev/config.sh
ARGS=(-az --stats --human-readable --itemize-changes --checksum)
for e in "${EXCLUDES[@]}"; do ARGS+=(--exclude "$e"); done
rsync "${ARGS[@]}" -e "ssh -p ${SSH_PORT}" "$PWD/" "${SSH_USER}@${SSH_HOST}:${REMOTE_ROOT}/" | tail -12
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ${REMOTE_ROOT} && \
  find admin backend master releases daftar bayar -type d -exec chmod 755 {} + && \
  find admin backend master releases daftar bayar -type f \( -name '*.html' -o -name '*.php' -o -name '*.css' -o -name '*.js' \
    -o -name '*.json' -o -name '*.zip' -o -name '*.svg' -o -name '*.ico' -o -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.webp' -o -name '*.gif' \) -exec chmod 644 {} + && \
  true" \
  && echo "Permission OK." || echo "(!) chmod gagal, cek manual kalau ada 403."
echo; echo "== 4/5 Cek live =="
curl -s https://chat.deintegra.com/releases/$V/manifest.json | head -6; echo
curl -s -X POST 'https://chat.deintegra.com/backend/index.php?action=mail_relay' -H 'Content-Type: application/json' -d '{"tenant_id":"x","license_key":"x"}'; echo "  <- harus 'Tenant tidak terdaftar' (action mail_relay sudah aktif)"
echo; echo "== 5/5 Tes kirim email LIVE ke $TES_KE =="
scp -q -P "${SSH_PORT}" "$TD/tes_email_live.php" "${SSH_USER}@${SSH_HOST}:/tmp/tes_email_live_v12184.php" && \
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "php /tmp/tes_email_live_v12184.php ${REMOTE_ROOT} '$TES_KE'; rm -f /tmp/tes_email_live_v12184.php"
echo; echo "Cek Inbox $TES_KE: subjek \"[Tes] Email reset password DEI Chatbot\" dari noreply@deintegra.com."
echo "Berikutnya: Admin Pusat › Daftar Tenant › Update semua tenant."
read -r -p "Tekan Enter untuk menutup..." _
