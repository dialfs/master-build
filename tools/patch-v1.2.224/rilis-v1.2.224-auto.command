#!/usr/bin/env bash
# Rilis v1.2.224 (kontak-manual): tombol + Tambah Kontak di menu Kontak (API add_contact). Hanya tenant, pusat tidak berubah.
# Butuh v1.2.223 sudah dirilis.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.224/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; V=v1.2.224; TD="$HERD/master-build/tools/patch-v1.2.224"
TRAILER="Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwcbRUtZECc2rMNcKZc"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
echo "== 0/5 Cek v1.2.223, patch, lint & build =="
[[ -d "$HERD/dei-pusat/releases/v1.2.223" ]] || stop "v1.2.223 belum dirilis."
command -v node >/dev/null || stop "node tidak ada — perlu untuk minify (brew install node)"
python3 "$TD/patch_v12224.py" "$HERD" || stop "PATCH v1.2.224 GAGAL"
php -l "$HERD/dei-tenant/api/index.php" || stop "LINT tenant GAGAL — tidak ada yang dikirim"
node --check "$HERD/dei-tenant/dashboard/chatbot-ai/app.js" || stop "JS GAGAL"
python3 "$HERD/master-build/tools/cek-storage.py" "$HERD/dei-tenant/api/index.php" || echo "(i) cek-storage: lihat catatan di atas (baris lama sudah ada sebelum v1.2.224)"
python3 "$TD/build_v12224.py" "$HERD" || stop "BUILD GAGAL"
node --check "$TD/out/app.js" || stop "app.js hasil minify GAGAL"
echo; echo "== 1/5 Commit, sinkron & push GitHub =="
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.224 ':!tools/patch-v1.2.224/out' ':!tools/patch-v1.2.224/rilis.log' \
  && git commit -qm "tools: patch v1.2.224 kontak-manual" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/dei-pusat" && git add releases/v1.2.224 master/dei-master.zip master/master.json \
  && git commit -qm "release v1.2.224 kontak-manual (tambah kontak manual di menu Kontak)" -m "$TRAILER" && echo "dei-pusat commit rilis OK") || echo "(dei-pusat: rilis tidak ada yang di-commit)"
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || stop "$R sinkron/push GAGAL"
done
echo; echo "== 2/5 Cocokkan paket dengan hasil build =="
python3 - "$HERD" <<'PY'
import zipfile,hashlib,sys
H=sys.argv[1]; z=zipfile.ZipFile(H+'/dei-pusat/releases/v1.2.224/update.zip'); O=H+'/master-build/tools/patch-v1.2.224/out/'
for f,p in [('api/index.php',H+'/dei-tenant/api/index.php'),('dashboard/chatbot-ai/app.js',O+'app.js'),('dashboard/chatbot-ai/index.html',H+'/dei-tenant/dashboard/chatbot-ai/index.html')]:
    a=hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest(); b=hashlib.md5(open(p,'rb').read()).hexdigest()
    print(('OK   ' if a==b else 'BEDA ')+f)
PY
echo; echo "== 3/5 Deploy LIVE (pusat: paket rilis) =="
cd "$HERD/dei-pusat" || stop "folder dei-pusat tidak ada"
[[ -z "$(git status --porcelain)" ]] || { git status --short; stop "dei-pusat masih punya perubahan belum di-commit; deploy dibatalkan."; }
./dev/deploy.sh --go | tail -6 || stop "DEPLOY GAGAL"
source dev/config.sh
echo; echo "== 4/5 Tenant Support, omowaynuenco & demo: update ke $V =="
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ${REMOTE_ROOT} && php backend/update-push.php only=dei-support && php backend/update-push.php only=omowaynuenco && php backend/update-push.php only=demo" || echo "(!) periksa pesan di atas"
echo; echo "== 5/5 Cek live =="
T=$(date +%s); B=https://chatbot.deintegra.com/demo
printf "%-34s HTTP %s  <- harus 403\n" "releases/$V/manifest.json" "$(curl -s -o /dev/null -w '%{http_code}' "https://chat.deintegra.com/releases/$V/manifest.json?x=$T")"
curl -s "$B/dashboard/chatbot-ai/index.html?x=$T" | grep -o 'app.js?v=[0-9.]*' | head -1 | sed 's/$/  <- harus app.js?v=1.2.224/'
curl -s -o /dev/null -w "add_contact tanpa login           HTTP %{http_code}  <- harus 401\n" -X POST -H 'Content-Type: application/json' -d '{"number":"081200000000","name":"x"}' "$B/api/index.php?action=add_contact&x=$T"
TOK=$(curl -s -X POST -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin"}' "$B/api/index.php?action=login" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("token",""))')
curl -s -X POST -H "X-Auth-Token: $TOK" -H 'Content-Type: application/json' -d '{"number":"12","name":"x"}' "$B/api/index.php?action=add_contact&x=$T" | sed 's/^/demo nomor salah (harus ditolak): /'; echo
echo; echo "Berikutnya: buka dashboard (Cmd+Shift+R) > Kontak > + Tambah Kontak. Tenant lain: Admin Pusat > Update ke $V."
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
