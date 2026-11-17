#!/usr/bin/env bash
# Rilis v1.2.196 (tombol-bantuan) — tombol headset di sebelah nama pengguna untuk membuka Asisten Bantuan.
# Paket tenant: api/index.php (versi), dashboard/chatbot-ai/app.js + index.html.
# Pusat: releases/v1.2.196, master.
# Skrip ini: patch (idempoten), lint, build, commit + push, cocokkan md5, deploy pusat, perbarui tenant Support, cek live.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.196/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; V=v1.2.196; TD="$HERD/master-build/tools/patch-v1.2.196"
TRAILER="Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwcAJ8kPdQosx8u6HFb"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
echo "== 0/5 Patch, lint & build paket =="
python3 "$TD/patch_v12196.py" "$HERD" || stop "PATCH v1.2.196 GAGAL"
for f in "$HERD/dei-tenant/api/index.php"; do php -l "$f" || stop "LINT GAGAL — tidak ada yang dikirim"; done
for j in dashboard/chatbot-ai/app.js; do node --check "$HERD/dei-tenant/$j" 2>/dev/null || echo "(node tidak ada / lewati cek $j)"; done
python3 "$TD/build_v12196.py" "$HERD" || stop "BUILD GAGAL"
echo; echo "== 1/5 Commit, sinkron & push GitHub =="
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.196 \
  && git commit -qm "tools: patch v1.2.196 tombol-bantuan" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/dei-pusat" && git add releases/v1.2.196 master/dei-master.zip master/master.json \
  && git commit -qm "release v1.2.196 tombol-bantuan (tombol headset Asisten Bantuan di sebelah nama pengguna)" -m "$TRAILER" && echo "dei-pusat commit OK") || echo "(dei-pusat: tidak ada yang di-commit)"
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || stop "$R sinkron/push GAGAL"
done
echo; echo "== 2/5 Cocokkan paket dengan dei-tenant lokal =="
python3 - "$HERD" <<'PY'
import zipfile,hashlib,sys
H=sys.argv[1]; z=zipfile.ZipFile(H+'/dei-pusat/releases/v1.2.196/update.zip')
for f in ['api/index.php','dashboard/chatbot-ai/app.js','dashboard/chatbot-ai/index.html']:
    a=hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest(); b=hashlib.md5(open(H+'/dei-tenant/'+f,'rb').read()).hexdigest()
    print(('OK   ' if a==b else 'BEDA ')+f)
PY
echo; echo "== 3/5 Deploy LIVE =="
cd "$HERD/dei-pusat" || stop "folder dei-pusat tidak ada"
[[ -z "$(git status --porcelain)" ]] || { git status --short; stop "dei-pusat masih punya perubahan belum di-commit; deploy dibatalkan."; }
./dev/deploy.sh --go | tail -6 || stop "DEPLOY GAGAL"
echo; echo "== 4/5 Tenant Support: update ke $V =="
source dev/config.sh
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ${REMOTE_ROOT} && php backend/update-push.php only=dei-support" || echo "(!) periksa pesan di atas"
echo; echo "== 5/5 Cek live =="
T=$(date +%s)
curl -s "https://chat.deintegra.com/releases/$V/manifest.json?x=$T" | head -6; echo
curl -s -o /dev/null -w "dashboard tenant Support HTTP %{http_code}  <- harus 200\n" "https://chatbot.deintegra.com/support/dashboard/chatbot-ai/index.html?x=$T"
echo; echo "Berikutnya: Admin Pusat > Update tenant lain ke $V, lalu Cmd+Shift+R di dashboard."
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
