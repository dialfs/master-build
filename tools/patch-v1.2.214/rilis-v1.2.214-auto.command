#!/usr/bin/env bash
# Rilis v1.2.214 (task): tiap bubble chat WA bisa dijadikan to-do + menu Task (kanban New/On Progress/Pending/Done/Closed) + catatan.
# Butuh v1.2.213 sudah dirilis.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.214/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; V=v1.2.214; TD="$HERD/master-build/tools/patch-v1.2.214"
TRAILER="Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwd4HGe8hP1ron38DZU"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
echo "== 0/5 Cek v1.2.213, patch, lint & build =="
[[ -d "$HERD/dei-pusat/releases/v1.2.213" ]] || stop "v1.2.213 belum dirilis."
command -v node >/dev/null || stop "node tidak ada — perlu untuk minify (brew install node)"
python3 "$TD/patch_v12214.py" "$HERD" || stop "PATCH v1.2.214 GAGAL"
php -l "$HERD/dei-tenant/api/index.php" || stop "LINT GAGAL — tidak ada yang dikirim"
node --check "$HERD/dei-tenant/dashboard/chatbot-ai/app.js" || stop "JS GAGAL"
python3 "$HERD/master-build/tools/cek-storage.py" "$HERD/dei-tenant/api/index.php" || echo "(i) cek-storage: lihat catatan di atas (baris lama sudah ada sebelum v1.2.214)"
python3 "$TD/build_v12214.py" "$HERD" || stop "BUILD GAGAL"
echo; echo "== 1/5 Commit, sinkron & push GitHub =="
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.214/patch_v12214.py tools/patch-v1.2.214/build_v12214.py tools/patch-v1.2.214/rilis-v1.2.214-auto.command \
  && git commit -qm "tools: patch v1.2.214 task" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/dei-pusat" && git add releases/v1.2.214 master/dei-master.zip master/master.json \
  && git commit -qm "release v1.2.214 task (bubble chat jadi to-do, menu Task kanban + catatan)" -m "$TRAILER" && echo "dei-pusat commit rilis OK") || echo "(dei-pusat: rilis tidak ada yang di-commit)"
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || stop "$R sinkron/push GAGAL"
done
echo; echo "== 2/5 Cocokkan paket dengan hasil build =="
python3 - "$HERD" <<'PY'
import zipfile,hashlib,sys
H=sys.argv[1]; z=zipfile.ZipFile(H+'/dei-pusat/releases/v1.2.214/update.zip'); O=H+'/master-build/tools/patch-v1.2.214/out/'
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
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ${REMOTE_ROOT} && php backend/update-push.php only=dei-support && php backend/update-push.php only=omowaynuenco" || echo "(!) periksa pesan di atas"
echo; echo "== 5/5 Cek live =="
T=$(date +%s); B=https://chat.deintegra.com
printf "%-30s HTTP %s  <- harus 403\n" "releases/$V/manifest.json" "$(curl -s -o /dev/null -w '%{http_code}' "$B/releases/$V/manifest.json?x=$T")"
curl -s "https://chatbot.deintegra.com/support/dashboard/chatbot-ai/index.html?x=$T" | grep -o 'app.js?v=[0-9.]*' | head -1 | sed 's/$/  <- harus app.js?v=1.2.214/'
curl -s -o /dev/null -w "tasks_list tanpa login           HTTP %{http_code}  <- harus 401\n" "https://chatbot.deintegra.com/support/api/index.php?action=tasks_list&x=$T"
curl -s -o /dev/null -w "data/tasks.json publik            HTTP %{http_code}  <- harus 403/404\n" "https://chatbot.deintegra.com/support/data/tasks.json?x=$T"
echo; echo "Berikutnya: buka dashboard (Cmd+Shift+R) — menu Task di sidebar, tautan To-do di bawah bubble Percakapan WA. Tenant lain: Admin Pusat > Update ke $V."
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
