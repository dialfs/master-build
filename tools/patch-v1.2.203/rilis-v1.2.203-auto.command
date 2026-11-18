#!/usr/bin/env bash
# Rilis v1.2.203 (sales-tag): tag Sales per chat, catat PO, Close Deal & laporan per Sales (Growth+).
# Butuh v1.2.202 sudah dirilis (rilis-v1.2.202-auto.command).
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.203/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; V=v1.2.203; TD="$HERD/master-build/tools/patch-v1.2.203"
TRAILER="Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwbXgyuwgcm7nm7RHeD"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
echo "== 0/5 Cek v1.2.202, patch, lint & build =="
[[ -d "$HERD/dei-pusat/releases/v1.2.202" ]] || stop "v1.2.202 belum dirilis. Jalankan dulu master-build/tools/patch-v1.2.202/rilis-v1.2.202-auto.command, lalu skrip ini."
[[ -n "$(cd "$HERD/dei-pusat" && git log --oneline -15 --grep='release v1.2.202')" ]] || stop "commit 'release v1.2.202' belum ada di dei-pusat. Selesaikan rilis v1.2.202 dulu."
command -v node >/dev/null || stop "node tidak ada — perlu untuk minify (brew install node)"
python3 "$TD/patch_v12203.py" "$HERD" || stop "PATCH v1.2.203 GAGAL"
php -l "$HERD/dei-tenant/api/index.php" || stop "LINT GAGAL — tidak ada yang dikirim"
node --check "$HERD/dei-tenant/dashboard/chatbot-ai/app.js" || stop "JS GAGAL"
python3 "$TD/build_v12203.py" "$HERD" || stop "BUILD GAGAL"
echo; echo "== 1/5 Commit, sinkron & push GitHub =="
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.203/patch_v12203.py tools/patch-v1.2.203/build_v12203.py tools/patch-v1.2.203/rilis-v1.2.203-auto.command \
  && git commit -qm "tools: patch v1.2.203 sales-tag" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/dei-pusat" && git add releases/v1.2.203 master/dei-master.zip master/master.json \
  && git commit -qm "release v1.2.203 sales-tag (tag Sales per chat, PO, Close Deal & laporan per Sales)" -m "$TRAILER" && echo "dei-pusat commit rilis OK") || echo "(dei-pusat: rilis tidak ada yang di-commit)"
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || stop "$R sinkron/push GAGAL"
done
echo; echo "== 2/5 Cocokkan paket dengan hasil build =="
python3 - "$HERD" <<'PY'
import zipfile,hashlib,sys
H=sys.argv[1]; z=zipfile.ZipFile(H+'/dei-pusat/releases/v1.2.203/update.zip'); O=H+'/master-build/tools/patch-v1.2.203/out/'
for f,p in [('api/index.php',H+'/dei-tenant/api/index.php'),('dashboard/chatbot-ai/app.js',O+'app.js'),('dashboard/chatbot-ai/index.html',H+'/dei-tenant/dashboard/chatbot-ai/index.html')]:
    a=hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest(); b=hashlib.md5(open(p,'rb').read()).hexdigest()
    print(('OK   ' if a==b else 'BEDA ')+f)
PY
echo; echo "== 3/5 Deploy LIVE =="
cd "$HERD/dei-pusat" || stop "folder dei-pusat tidak ada"
[[ -z "$(git status --porcelain)" ]] || { git status --short; stop "dei-pusat masih punya perubahan belum di-commit; deploy dibatalkan."; }
./dev/deploy.sh --go | tail -6 || stop "DEPLOY GAGAL"
source dev/config.sh
echo; echo "== 4/5 Tenant Support: update ke $V =="
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ${REMOTE_ROOT} && php backend/update-push.php only=dei-support" || echo "(!) periksa pesan di atas"
echo; echo "== 5/5 Cek live =="
T=$(date +%s); B=https://chat.deintegra.com
printf "%-30s HTTP %s  <- harus 403\n" "releases/$V/manifest.json" "$(curl -s -o /dev/null -w '%{http_code}' "$B/releases/$V/manifest.json?x=$T")"
curl -s "https://chatbot.deintegra.com/support/dashboard/chatbot-ai/index.html?x=$T" | grep -o 'app.js?v=[0-9.]*' | head -1 | sed 's/$/  <- harus app.js?v=1.2.203/'
curl -s -o /dev/null -w "qr_media tanpa login             HTTP %{http_code}  <- harus 401\n" "https://chatbot.deintegra.com/support/api/index.php?action=qr_media&id=abc&x=$T"
echo; echo "Berikutnya: Admin Pusat > Update tenant lain ke $V, lalu Cmd+Shift+R di dashboard."
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
