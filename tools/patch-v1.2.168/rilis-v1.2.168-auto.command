#!/usr/bin/env bash
# Rilis v1.2.168 (kuota-unit) — 11 Nov 2026: kuota Unit Bisnis per paket (pusat + tenant) + LP deintegra.com/chat-widget-ai.
# Lint dulu, lalu build paket dari dei-tenant lokal. Skrip ini commit dulu (dei-pusat + master-build).
# Skrip ini: push GitHub, cek md5 paket vs dei-tenant, preflight, deploy LIVE.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.168/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; V=v1.2.168
echo "== 0/5 Lint & build paket =="
php -l "$HERD/dei-tenant/api/index.php" || { echo "LINT GAGAL — tidak ada yang dikirim"; read -r -p "Enter..." _; exit 1; }
python3 "$HERD/master-build/tools/patch-v1.2.168/build_v12168.py" "$HERD" || { echo "BUILD GAGAL"; read -r -p "Enter..." _; exit 1; }
echo; echo "== 1/5 Commit, sinkron & push GitHub =="
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.168; git commit -qm "tools: patch v1.2.168 kuota-unit" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwcdXV7H3BPQN1fBHg9" && echo "master-build commit OK")
(cd "$HERD/dei-pusat" && git add backend/classify-lib.php backend/index.php backend/cron-tick.php admin/index.html releases/v1.2.168 master/dei-master.zip master/master.json && git commit -qm "release v1.2.168 kuota-unit" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwcdXV7H3BPQN1fBHg9" && echo "dei-pusat commit OK")
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || { echo "$R sinkron/push GAGAL"; read -r -p "Enter..." _; exit 1; }
done
echo; echo "== 2/5 Cocokkan paket dengan dei-tenant lokal =="
php -l "$HERD/dei-tenant/api/index.php" || { echo "LINT GAGAL"; read -r -p "Enter..." _; exit 1; }
python3 - "$HERD" <<'PY'
import zipfile,hashlib,sys
H=sys.argv[1]; z=zipfile.ZipFile(H+'/dei-pusat/releases/v1.2.168/update.zip')
for f in ['api/index.php','dashboard/chatbot-ai/index.html','dashboard/chatbot-ai/app.js']:
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
  find admin backend master releases daftar -type d -exec chmod 755 {} + && \
  find admin backend master releases daftar -type f \( -name '*.html' -o -name '*.php' -o -name '*.css' -o -name '*.js' \
    -o -name '*.json' -o -name '*.zip' -o -name '*.svg' -o -name '*.ico' -o -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.webp' -o -name '*.gif' \) -exec chmod 644 {} +" \
  && echo "Permission OK." || echo "(!) chmod gagal, cek manual kalau ada 403."
echo; echo "== 4/5 LP deintegra.com/chat-widget-ai =="
cd "$HERD/web-deintegra" && rm -f .git/*.lock && git add chat-widget-ai.html en/chat-widget-ai.html \
  && git commit -qm "chat-widget-ai: tambah kuota unit bisnis per paket (Growth 3, Business 5, Pro 10, Enterprise custom)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwcdXV7H3BPQN1fBHg9" && echo "LP commit OK"
cd "$HERD/web-deintegra" && git pull --ff-only origin main && ./dev/run-deploy.command | tail -15
curl -s https://deintegra.com/chat-widget-ai | grep -o "Hingga [0-9]* unit bisnis[^<]*\|Jumlah unit bisnis[^<]*" | sort -u
echo; echo "== 5/5 Cek manifest live =="
curl -s https://chat.deintegra.com/releases/$V/manifest.json | head -8
echo; read -r -p "Tekan Enter untuk menutup..." _
