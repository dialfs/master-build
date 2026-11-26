#!/usr/bin/env bash
# Rilis v1.2.223 (laporan-pdf): Laporan Berkala PDF mingguan & bulanan -> email (lampiran) & WhatsApp (dokumen).
# + pusat: mail_relay menerima lampiran PDF (report_pdf) & PERBAIKAN bug v1.2.215 (semua email relay ditolak "Alamat email tidak valid").
# + pusat: /lib/dompdf-3.1.4-dei.zip (mesin PDF yang diunduh tenant sekali, sha256 dikunci di tenant).
# Butuh v1.2.222 sudah dirilis.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.223/rilis.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; V=v1.2.223; TD="$HERD/master-build/tools/patch-v1.2.223"
SHA=f19009552a5769afb3b13e718a89b9f8566a8a303819e6478282d378569e4bcd
TRAILER="Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwasRrQcqSQ2YX2E6Yg"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
echo "== 0/5 Cek v1.2.222, patch, lint & build =="
[[ -d "$HERD/dei-pusat/releases/v1.2.222" ]] || stop "v1.2.222 belum dirilis."
command -v node >/dev/null || stop "node tidak ada — perlu untuk minify (brew install node)"
[[ "$(shasum -a 256 "$TD/lib/dompdf-3.1.4-dei.zip" | cut -d' ' -f1)" == "$SHA" ]] || stop "lib/dompdf-3.1.4-dei.zip rusak (sha256 beda)."
python3 "$TD/patch_v12223.py" "$HERD" || stop "PATCH v1.2.223 GAGAL"
php -l "$HERD/dei-tenant/api/index.php" || stop "LINT tenant GAGAL — tidak ada yang dikirim"
php -l "$HERD/dei-pusat/backend/index.php" || stop "LINT pusat GAGAL — tidak ada yang dikirim"
node --check "$HERD/dei-tenant/dashboard/chatbot-ai/app.js" || stop "JS GAGAL"
python3 "$HERD/master-build/tools/cek-storage.py" "$HERD/dei-tenant/api/index.php" || echo "(i) cek-storage: lihat catatan di atas (baris lama sudah ada sebelum v1.2.223)"
python3 "$TD/build_v12223.py" "$HERD" || stop "BUILD GAGAL"
echo; echo "== 1/5 Commit, sinkron & push GitHub =="
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/patch-v1.2.223 ':!tools/patch-v1.2.223/out' ':!tools/patch-v1.2.223/rilis.log' \
  && git commit -qm "tools: patch v1.2.223 laporan-pdf" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/dei-pusat" && git add releases/v1.2.223 master/dei-master.zip master/master.json backend/index.php lib dev/deploy.sh \
  && git commit -qm "release v1.2.223 laporan-pdf (laporan berkala PDF via email & WhatsApp; mail_relay lampiran PDF + perbaikan bug v1.2.215; lib dompdf)" -m "$TRAILER" && echo "dei-pusat commit rilis OK") || echo "(dei-pusat: rilis tidak ada yang di-commit)"
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || stop "$R sinkron/push GAGAL"
done
echo; echo "== 2/5 Cocokkan paket dengan hasil build =="
python3 - "$HERD" <<'PY'
import zipfile,hashlib,sys
H=sys.argv[1]; z=zipfile.ZipFile(H+'/dei-pusat/releases/v1.2.223/update.zip'); O=H+'/master-build/tools/patch-v1.2.223/out/'
for f,p in [('api/index.php',H+'/dei-tenant/api/index.php'),('dashboard/chatbot-ai/app.js',O+'app.js'),('dashboard/chatbot-ai/index.html',H+'/dei-tenant/dashboard/chatbot-ai/index.html')]:
    a=hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest(); b=hashlib.md5(open(p,'rb').read()).hexdigest()
    print(('OK   ' if a==b else 'BEDA ')+f)
PY
echo; echo "== 3/5 Deploy LIVE (pusat: rilis + mail_relay + lib) =="
cd "$HERD/dei-pusat" || stop "folder dei-pusat tidak ada"
[[ -z "$(git status --porcelain)" ]] || { git status --short; stop "dei-pusat masih punya perubahan belum di-commit; deploy dibatalkan."; }
./dev/deploy.sh --go | tail -6 || stop "DEPLOY GAGAL"
source dev/config.sh
echo; echo "== 4/5 Tenant Support, omowaynuenco & demo: update ke $V =="
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ${REMOTE_ROOT} && php backend/update-push.php only=dei-support && php backend/update-push.php only=omowaynuenco && php backend/update-push.php only=demo" || echo "(!) periksa pesan di atas"
echo; echo "== 5/5 Cek live =="
T=$(date +%s); B=https://chatbot.deintegra.com/demo
printf "%-34s HTTP %s  <- harus 403\n" "releases/$V/manifest.json" "$(curl -s -o /dev/null -w '%{http_code}' "https://chat.deintegra.com/releases/$V/manifest.json?x=$T")"
GOT=$(curl -s "https://chat.deintegra.com/lib/dompdf-3.1.4-dei.zip?x=$T" | shasum -a 256 | cut -d' ' -f1)
[[ "$GOT" == "$SHA" ]] && echo "lib/dompdf-3.1.4-dei.zip          OK (sha256 cocok)" || echo "(!) lib/dompdf-3.1.4-dei.zip sha256 BEDA/tidak terunduh: $GOT"
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ${REMOTE_ROOT} && grep -c \"'report_pdf'], true)) jsonOut\" backend/index.php" | sed 's/^/mail_relay diperbaiki (harus 1):      /'
curl -s "$B/dashboard/chatbot-ai/index.html?x=$T" | grep -o 'app.js?v=[0-9.]*' | head -1 | sed 's/$/  <- harus app.js?v=1.2.223/'
curl -s -o /dev/null -w "rpt_get tanpa login               HTTP %{http_code}  <- harus 401\n" "$B/api/index.php?action=rpt_get&x=$T"
curl -s -o /dev/null -w "rpt_dl tanda tangan palsu         HTTP %{http_code}  <- harus 403\n" "$B/api/index.php?action=rpt_dl&f=20260101-000000000000&e=9999999999&s=x&x=$T"
TOK=$(curl -s -X POST -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin"}' "$B/api/index.php?action=login" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("token",""))')
MK=$(curl -s -m 150 -X POST -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' -d '{"kind":"monthly"}' "$B/api/index.php?action=rpt_make&x=$T")
echo "$MK" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("demo rpt_make (pasang dompdf + PDF):", "OK" if d.get("ok") else d.get("error"), "| mesin:", d.get("engine"), "| ukuran:", d.get("size"))' || echo "(!) demo rpt_make gagal dibaca: $MK"
ID=$(echo "$MK" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("id",""))' 2>/dev/null)
[[ -n "$ID" ]] && curl -s -H "Authorization: Bearer $TOK" "$B/api/index.php?action=rpt_file&id=$ID&x=$T" -o "$TD/demo-$ID.pdf" && head -c 5 "$TD/demo-$ID.pdf" | sed 's/$/  <- harus %PDF-/' && echo
curl -s -o /dev/null -w "data/report-pdf/index.json publik  HTTP %{http_code}  <- harus 403/404\n" "$B/data/report-pdf/index.json?x=$T"
curl -s -o /dev/null -w "lib/dompdf-*/autoload publik      HTTP %{http_code}  <- harus 403/404\n" "$B/lib/dompdf-3.1.4/autoload.inc.php?x=$T"
[[ -n "$ID" ]] && open "$TD/demo-$ID.pdf"
echo; echo "Berikutnya: buka dashboard (Cmd+Shift+R) > Laporan & Log > Laporan Berkala. Tenant lain: Admin Pusat > Update ke $V."
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
