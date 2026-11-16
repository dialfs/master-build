#!/usr/bin/env bash
# Rilis v1.2.185 (master-grup) — 16 Nov 2026: Dashboard Grup tahap 1 (satu login klien grup, laporan gabungan, buka tenant tanpa login ulang).
# Paket tenant: api/index.php + dashboard index.html + app.js. Pusat: backend/index.php + backend/group-lib.php + admin/index.html + grup/index.html + dev/deploy.sh.
# Patch sudah diterapkan lokal. Skrip ini: lint, build paket, commit + push GitHub, cek md5, deploy LIVE pusat, cek live.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.185/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; V=v1.2.185; TD="$HERD/master-build/tools/patch-v1.2.185"
SESS="Claude-Session: https://claude.ai/code/session_01F3pjwcqjhpuLFgGpUzbA1J"
echo "== 0/4 Lint & build paket =="
for f in "$HERD/dei-tenant/api/index.php" "$HERD/dei-pusat/backend/index.php" "$HERD/dei-pusat/backend/group-lib.php"; do
  php -l "$f" || { echo "LINT GAGAL — tidak ada yang dikirim"; read -r -p "Enter..." _; exit 1; }
done
python3 "$TD/build_v12185.py" "$HERD" || { echo "BUILD GAGAL"; read -r -p "Enter..." _; exit 1; }
echo; echo "== 1/4 Commit, sinkron & push GitHub =="
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.185; git commit -qm "tools: patch v1.2.185 master-grup" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
$SESS" && echo "master-build commit OK")
(cd "$HERD/dei-pusat" && git add backend/index.php backend/group-lib.php admin/index.html grup/index.html dev/deploy.sh releases/v1.2.185 master/dei-master.zip master/master.json && git commit -qm "release v1.2.185 master-grup (Dashboard Grup tahap 1)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
$SESS" && echo "dei-pusat commit OK")
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || { echo "$R sinkron/push GAGAL"; read -r -p "Enter..." _; exit 1; }
done
echo; echo "== 2/4 Cocokkan paket dengan dei-tenant lokal =="
python3 - "$HERD" <<'PY'
import zipfile,hashlib,sys
H=sys.argv[1]; z=zipfile.ZipFile(H+'/dei-pusat/releases/v1.2.185/update.zip')
for f in ['api/index.php','dashboard/chatbot-ai/index.html','dashboard/chatbot-ai/app.js']:
    a=hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest(); b=hashlib.md5(open(H+'/dei-tenant/'+f,'rb').read()).hexdigest()
    print(('OK   ' if a==b else 'BEDA ')+f)
PY
echo; echo "== 3/4 Deploy LIVE (rsync) =="
cd "$HERD/dei-pusat"
./dev/preflight.sh | tail -3 || { echo "PREFLIGHT GAGAL"; read -r -p "Enter..." _; exit 1; }
source dev/config.sh
ARGS=(-az --stats --human-readable --itemize-changes --checksum)
for e in "${EXCLUDES[@]}"; do ARGS+=(--exclude "$e"); done
rsync "${ARGS[@]}" -e "ssh -p ${SSH_PORT}" "$PWD/" "${SSH_USER}@${SSH_HOST}:${REMOTE_ROOT}/" | tail -12
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ${REMOTE_ROOT} && \
  find admin backend master releases daftar bayar grup -type d -exec chmod 755 {} + && \
  find admin backend master releases daftar bayar grup -type f \( -name '*.html' -o -name '*.php' -o -name '*.css' -o -name '*.js' \
    -o -name '*.json' -o -name '*.zip' -o -name '*.svg' -o -name '*.ico' -o -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.webp' -o -name '*.gif' \) -exec chmod 644 {} + && \
  true" \
  && echo "Permission OK." || echo "(!) chmod gagal, cek manual kalau ada 403."
echo; echo "== 4/4 Cek live =="
curl -s https://chat.deintegra.com/releases/$V/manifest.json | head -6; echo
curl -s -o /dev/null -w "grup/ HTTP %{http_code}  <- harus 200\n" https://chat.deintegra.com/grup/
curl -s 'https://chat.deintegra.com/backend/index.php?action=grp_me'; echo "  <- harus 'Sesi berakhir' (action grup aktif)"
curl -s -o /dev/null -w "data/groups.json HTTP %{http_code}  <- harus 403/404\n" https://chat.deintegra.com/data/groups.json
echo; echo "Berikutnya: Admin Pusat › Daftar Tenant › Update tenant grup ke $V, lalu kartu Dashboard Grup › + Grup baru."
read -r -p "Tekan Enter untuk menutup..." _
