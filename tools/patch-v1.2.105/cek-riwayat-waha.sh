#!/usr/bin/env bash
# v1.2.105: cek baca-saja — apakah WAHA di VPS menyimpan riwayat chat untuk satu sesi
# (engine, store NOWEB, bentuk /chats & /messages). Tidak mengubah apa pun.
# Pakai (dari Terminal Mac):  ssh root@212.85.25.180 'bash -s' -- <nama-sesi> < cek-riwayat-waha.sh
#   contoh: ssh root@212.85.25.180 'bash -s' -- pomeloteljkt < ~/Herd/master-build/tools/patch-v1.2.105/cek-riwayat-waha.sh
set -uo pipefail
S="${1:-}"; [ -z "$S" ] && { echo "Sebutkan nama sesi."; exit 1; }
cd /opt/waha || exit 1
KEY=$(grep ^WAHA_API_KEY= .env | cut -d= -f2-)
W="http://127.0.0.1:3000"
q() { curl -s -H "X-Api-Key: $KEY" "$W$1"; }
echo "== engine: $(grep ^WAHA_ENGINE .env)"
echo "== sesi:"; q "/api/sessions/$S" | python3 -c "import sys,json; d=json.load(sys.stdin); print({k: d.get(k) for k in ('name','status','engine')}); print('store:', d.get('config',{}).get('noweb'))"
echo "== 5 chat terbaru:"; q "/api/$S/chats?limit=5&offset=0&sortBy=conversationTimestamp&sortOrder=desc" > /tmp/ck-chats.json
python3 - <<'P'
import json; d=json.load(open('/tmp/ck-chats.json'))
if not isinstance(d, list): print('RESPON BUKAN LIST:', str(d)[:300]); raise SystemExit
for c in d: print(' ', c.get('id'), '| nama:', bool(c.get('name')), '| kunci:', sorted(c.keys())[:8])
P
CID=$(python3 -c "import json; d=json.load(open('/tmp/ck-chats.json')); print(next((c['id'] for c in d if isinstance(c.get('id'),str) and c['id'].endswith(('@c.us','@lid','@s.whatsapp.net'))), ''))" 2>/dev/null)
[ -z "$CID" ] && { echo "Tidak ada chat pribadi di store."; exit 0; }
echo "== 3 pesan dari $CID (isi disamarkan):"
q "/api/$S/chats/$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$CID")/messages?limit=3&offset=0&downloadMedia=false&filter.timestamp.lte=$(date +%s)" | python3 -c "
import sys,json,datetime; d=json.load(sys.stdin)
if not isinstance(d, list): print('RESPON BUKAN LIST:', str(d)[:300]); raise SystemExit
for m in d: print(' ', datetime.datetime.fromtimestamp(m.get('timestamp',0) if m.get('timestamp',0)<1e11 else m['timestamp']/1000), 'fromMe', m.get('fromMe'), 'media', m.get('hasMedia'), 'body', len(m.get('body') or ''), 'char')"
echo "== jumlah chat di store:"; q "/api/$S/chats?limit=1000&offset=0" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else d)"
rm -f /tmp/ck-chats.json
