#!/bin/bash
# Regresi v1.2.71 — dua mode. Asumsi: mysqld, redis, mock (9900), php -S 8101/8102/8111/8112 sudah jalan.
set -e; cd "$(dirname "$0")"; ./stopw.sh
TGZ="${DATA_UJI:?set DATA_UJI=path ke tgz berisi chatbot-log.json, wa-contacts.json, wa-sessions/ dst}"
echo "### 1. Kesetaraan endpoint dashboard (data asli, impor ke MySQL)"
for A in eqfile eqdb; do
  ./mkapp.sh $A $( [ $A = eqdb ] && echo db ) >/dev/null; tar xzf "$TGZ" -C $A/data
  echo '[{"username":"dias","password":"rahasia123","role":"super_admin","migrated_3role":true}]' > $A/data/users.json
  python3 - $A/data/settings.json <<'P'
import json,sys; p=sys.argv[1]; s=json.load(open(p)); s['auto_closing']={'enabled':True,'minutes':1}; json.dump(s,open(p,'w'))
P
done
./srv.sh eqfile 8111; ./srv.sh eqdb 8112
(cd eqdb && php api/index.php action=db_import)
python3 eq.py | tail -1
echo "### 2. Jalur tulis dashboard + echo HP (logMutate) + duplikat echo"
python3 writes.py >/dev/null; (cd eqdb && php api/index.php action=wa_worker slot=9 max_sec=3 max_jobs=5)
python3 eq.py | grep -E "BEDA|SAMA" | sed 's/ukuran=.*//' | sort | uniq -c | sort -rn | head -12
echo "### 3. Auto-closing lewat cron_tick CLI (conv-state dua mode)"
: > sends.log
for P in 8111 8112; do python3 hook.py http://127.0.0.1:$P basic >/dev/null; done
(cd eqdb && php api/index.php action=wa_worker slot=9 max_sec=6 max_jobs=3)
python3 - <<'P'
import json,subprocess,time
p='eqfile/data/conv-state.json'; a=json.load(open(p)); a['628111']['last_at']-=300; json.dump(a,open(p,'w'))
subprocess.run(['mysql','-uroot','sj_chat','-e',"update dei_conv_state set last_at=last_at-300, body=JSON_SET(body,'$.last_at',JSON_EXTRACT(body,'$.last_at')-300) where num='628111'"])
P
for A in eqfile eqdb; do (cd $A && php api/index.php action=cron_tick | python3 -c "import json,sys;d=json.load(sys.stdin);print('$A closed',d.get('closed'),'purged',d.get('sessions_purged'),'err',[k for k in d if k.startswith('err')])"); done
for A in eqfile eqdb; do (cd $A && php api/index.php action=cron_tick | python3 -c "import json,sys;d=json.load(sys.stdin);print('$A tick ke-2 closed',d.get('closed'))"); done
grep -c "" sends.log
echo "### 4. Beban: 400 nomor x 3 pesan, 16 worker (mode db)"
./mkapp.sh appdb db >/dev/null; ./srv.sh appdb 8102; : > sends.log; : > /tmp/worker.log
for i in $(seq 0 15); do (cd appdb && php api/index.php action=wa_worker slot=$i max_sec=150 >>/tmp/worker.log 2>&1 &) ; done
T0=$(date +%s); python3 hook.py http://127.0.0.1:8102 burst 400 3
while [ $(wc -l < sends.log) -lt 1200 ] && [ $(( $(date +%s) - T0 )) -lt 200 ]; do sleep 2; done
echo "selesai $(( $(date +%s) - T0 )) dtk, terkirim $(wc -l < sends.log)"
python3 -c "
import json,collections;rows=[json.loads(l) for l in open('sends.log')];c=collections.Counter((r['to'],r['text']) for r in rows);print('balasan ganda',sum(1 for v in c.values() if v>1))"
mysql -uroot sj_chat -N -e "select 'log',count(*) from dei_log; select 'kontak',count(*) from dei_contacts; select 'sesi',count(*), min(json_length(turns)), max(json_length(turns)) from dei_wa_sessions; select 'conv_state',count(*) from dei_conv_state;"
echo "error worker: $(grep -c . /tmp/worker.log)"; ./stopw.sh
echo "### 5. Worker dimatikan paksa di tengah job -> job diantre ulang"
: > sends.log
PFX=kill$(date +%s) python3 hook.py http://127.0.0.1:8102 burst 3 1 >/dev/null
(cd appdb && timeout -s KILL 0.8 php api/index.php action=wa_worker slot=3 max_sec=20) || true
echo "proc tertinggal: $(redis-cli llen sj:q:wa:proc:3), antre: $(redis-cli llen sj:q:wa)"
(cd appdb && php api/index.php action=wa_worker slot=3 max_sec=8)
echo "terkirim setelah restart: $(wc -l < sends.log) (harus 3), proc: $(redis-cli llen sj:q:wa:proc:3)"
echo "### 6. Redis mati -> webhook memproses langsung (fallback)"
: > sends.log; redis-cli shutdown nosave >/dev/null 2>&1 || true; sleep 0.5
python3 hook.py http://127.0.0.1:8102 basic; echo "terkirim: $(wc -l < sends.log)"
redis-server --port 6379 --daemonize yes >/dev/null; sleep 0.5; redis-cli ping
