#!/usr/bin/env bash
# Rilis v1.2.197 (kode-terlindung) + pusat: paket-terkunci & anti-trial-ulang.
# Pusat: master/ & releases/ ditolak .htaccess, unduh rilis lewat action=pkg (tautan bertanda tangan); anti trial berulang.
# Tenant: api/index.php (blok .htaccess otomatis), app.js & chat-widget.js minified.
# Skrip ini: patch (idempoten), lint, build, commit + push, cocokkan md5, deploy pusat, perbarui tenant Support, cek live.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.197/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; V=v1.2.197; TD="$HERD/master-build/tools/patch-v1.2.197"
TRAILER="Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwd5yx9S3azht3STa98"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
echo "== 0/5 Patch, lint & build paket =="
command -v node >/dev/null || stop "node tidak ada — perlu untuk minify (brew install node)"
python3 "$TD/patch_v12197.py" "$HERD" || stop "PATCH v1.2.197 GAGAL"
for f in "$HERD/dei-tenant/api/index.php" "$HERD/dei-pusat/backend/index.php" "$HERD/dei-pusat/backend/signup-lib.php"; do php -l "$f" || stop "LINT GAGAL — tidak ada yang dikirim"; done
python3 "$TD/build_v12197.py" "$HERD" || stop "BUILD GAGAL"
echo; echo "== 1/5 Commit, sinkron & push GitHub =="
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add .gitignore tools/minify/minify.py tools/patch-v1.2.197 \
  && git commit -qm "tools: patch v1.2.197 kode-terlindung + minify" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/dei-pusat" && git add master/.htaccess releases/.htaccess backend/index.php backend/signup-lib.php admin/index.html DEPLOY-FLOW.md \
  && git commit -qm "security: paket-terkunci (master/ & releases/ tidak bisa diunduh publik, unduh rilis bertanda tangan) + anti-trial-ulang" -m "$TRAILER" && echo "dei-pusat commit keamanan OK") || echo "(dei-pusat: keamanan tidak ada yang di-commit)"
(cd "$HERD/dei-pusat" && git add releases/v1.2.197 master/dei-master.zip master/master.json \
  && git commit -qm "release v1.2.197 kode-terlindung (blok .htaccess tenant, JS minified)" -m "$TRAILER" && echo "dei-pusat commit rilis OK") || echo "(dei-pusat: rilis tidak ada yang di-commit)"
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || stop "$R sinkron/push GAGAL"
done
echo; echo "== 2/5 Cocokkan paket dengan hasil build =="
python3 - "$HERD" <<'PY'
import zipfile,hashlib,sys
H=sys.argv[1]; z=zipfile.ZipFile(H+'/dei-pusat/releases/v1.2.197/update.zip'); O=H+'/master-build/tools/patch-v1.2.197/out/'
for f,p in [('api/index.php',H+'/dei-tenant/api/index.php'),('dashboard/chatbot-ai/app.js',O+'app.js'),('assets/js/chat-widget.js',O+'chat-widget.js')]:
    a=hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest(); b=hashlib.md5(open(p,'rb').read()).hexdigest()
    print(('OK   ' if a==b else 'BEDA ')+f)
PY
echo; echo "== 3/5 Deploy LIVE =="
cd "$HERD/dei-pusat" || stop "folder dei-pusat tidak ada"
[[ -z "$(git status --porcelain)" ]] || { git status --short; stop "dei-pusat masih punya perubahan belum di-commit; deploy dibatalkan."; }
./dev/deploy.sh --go | tail -6 || stop "DEPLOY GAGAL"
echo; echo "== 4/5 Tenant Support: update ke $V (uji alur unduh bertanda tangan) =="
source dev/config.sh
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ${REMOTE_ROOT} && php backend/update-push.php only=dei-support" || echo "(!) periksa pesan di atas"
echo; echo "== 5/5 Cek live =="
T=$(date +%s); B=https://chat.deintegra.com
for u in "master/dei-master.zip" "master/master.json" "releases/$V/update.zip" "releases/$V/manifest.json" "releases/v1.2.196/update.zip"; do
  printf "%-34s HTTP %s  <- harus 403\n" "$u" "$(curl -s -o /dev/null -w '%{http_code}' "$B/$u?x=$T")"
done
printf "%-34s zip_url='%s'  <- harus kosong\n" "check_update tanpa tenant" "$(curl -s "$B/backend/index.php?action=check_update" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("zip_url",""))')"
curl -s -o /dev/null -w "dashboard tenant Support HTTP %{http_code}  <- harus 200\n" "https://chatbot.deintegra.com/support/dashboard/chatbot-ai/index.html?x=$T"
curl -s -o /dev/null -w ".git tenant Support      HTTP %{http_code}  <- harus 403 (blok .htaccess v1.2.197)\n" "https://chatbot.deintegra.com/support/.git/config?x=$T"
curl -s "https://chatbot.deintegra.com/support/dashboard/chatbot-ai/app.js?x=$T" | head -c 120; echo "  <- harus diawali komentar hak cipta v1.2.197 (minified)"
echo; echo "Berikutnya: Admin Pusat > Update tenant lain ke $V, lalu Cmd+Shift+R di dashboard."
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
