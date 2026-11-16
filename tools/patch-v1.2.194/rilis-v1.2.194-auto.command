#!/usr/bin/env bash
# Rilis v1.2.194 (asisten-bantuan) — Asisten Bantuan di Pusat Bantuan. Memuat juga v1.2.193 (tenant Support: umpan KB + konteks) dan isi awal KB.
# Paket tenant: api/index.php, assets/js/chat-widget.js, dashboard/chatbot-ai/app.js + index.html. Pusat: backend/cron-tick.php, releases/guide.json.
# v1.2.192 (pusat) dan v1.2.193 ikut terkirim lewat skrip ini; keduanya tidak dirilis terpisah.
# Patch sudah diterapkan lokal. Skrip ini: lint, build paket, commit + push GitHub, cek md5, deploy LIVE pusat, cek live.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.194/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; V=v1.2.194; TD="$HERD/master-build/tools/patch-v1.2.194"
TRAILER="Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwcAJ8kPdQosx8u6HFb"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
echo "== 0/4 Patch (idempoten), lint & build paket =="
python3 "$HERD/master-build/tools/patch-v1.2.192/patch_pusat_v12192.py" "$HERD/dei-pusat" || stop "PATCH v1.2.192 GAGAL"
python3 "$HERD/master-build/tools/patch-v1.2.193/patch_v12193.py" "$HERD" || stop "PATCH v1.2.193 GAGAL"
python3 "$TD/patch_v12194.py" "$HERD" || stop "PATCH v1.2.194 GAGAL"
[[ -f "$HERD/dei-pusat/releases/guide.json" ]] || stop "releases/guide.json (isi awal KB) tidak ada"
for f in "$HERD/dei-tenant/api/index.php" "$HERD/dei-pusat/backend/index.php" "$HERD/dei-pusat/backend/support-lib.php" "$HERD/dei-pusat/backend/cron-tick.php"; do
  php -l "$f" || stop "LINT GAGAL — tidak ada yang dikirim"
done
for j in assets/js/chat-widget.js dashboard/chatbot-ai/app.js; do node --check "$HERD/dei-tenant/$j" 2>/dev/null || echo "(node tidak ada / lewati cek $j)"; done
python3 "$TD/build_v12194.py" "$HERD" || stop "BUILD GAGAL"
echo; echo "== 1/4 Commit, sinkron & push GitHub =="
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.192 tools/patch-v1.2.193 tools/patch-v1.2.194 tools/kb-awal \
  && git commit -qm "tools: patch v1.2.192-194 asisten support/bantuan + isi awal KB" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/dei-pusat" && git add admin/index.html backend/index.php backend/support-lib.php backend/cron-tick.php dev/preflight.sh releases/guide.json releases/v1.2.194 master/dei-master.zip master/master.json \
  && git commit -qm "release v1.2.194 asisten-bantuan (Asisten Bantuan di Pusat Bantuan; tenant Support + umpan KB; isi awal KB)" -m "$TRAILER" && echo "dei-pusat commit OK") || echo "(dei-pusat: tidak ada yang di-commit)"
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || stop "$R sinkron/push GAGAL"
done
echo; echo "== 2/4 Cocokkan paket dengan dei-tenant lokal =="
python3 - "$HERD" <<'PY'
import zipfile,hashlib,sys
H=sys.argv[1]; z=zipfile.ZipFile(H+'/dei-pusat/releases/v1.2.194/update.zip')
for f in ['api/index.php','assets/js/chat-widget.js','dashboard/chatbot-ai/app.js','dashboard/chatbot-ai/index.html']:
    a=hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest(); b=hashlib.md5(open(H+'/dei-tenant/'+f,'rb').read()).hexdigest()
    print(('OK   ' if a==b else 'BEDA ')+f)
PY
echo; echo "== 3/4 Deploy LIVE =="
cd "$HERD/dei-pusat" || stop "folder dei-pusat tidak ada"
[[ -z "$(git status --porcelain)" ]] || { git status --short; stop "dei-pusat masih punya perubahan belum di-commit; deploy dibatalkan."; }
./dev/deploy.sh --go | tail -10 || stop "DEPLOY GAGAL"
echo; echo "== 4/4 Cek live =="
T=$(date +%s)
curl -s "https://chat.deintegra.com/releases/$V/manifest.json?x=$T" | head -6; echo
curl -s "https://chat.deintegra.com/admin/index.html?x=$T" | grep -c "v1.2.192: asisten-support" | sed 's/^/penanda v1.2.192 di admin live (harus >=1): /'
echo "support_kb_feed tanpa kunci (harus: tenant_id & license_key wajib): $(curl -s -X POST "https://chat.deintegra.com/backend/index.php?action=support_kb_feed")"
echo "partner_check (backend masih sehat): $(curl -s "https://chat.deintegra.com/backend/index.php?action=partner_check&code=TESKODE1")"
echo; echo "Berikutnya: pasang tenant dei-support (v1.2.194), isi kartu Asisten Support di Admin Pusat > Pengaturan, uji, baru nyalakan tombol Bantuan."
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
