#!/usr/bin/env python3
"""Uji skenario v1.2.101 percakapan. Pakai: scen.py <dir app uji> <port>   (app dari uji-dua-mode/mkapp.sh)
Butuh mock.py di :9900. Mode db: worker dijalankan setelah tiap webhook."""
import json, subprocess, sys, time, urllib.request, os, hmac, hashlib, glob, shutil
APP, PORT = sys.argv[1], sys.argv[2]
D = os.path.abspath(APP); DB = os.path.exists(D + '/data/server.php')
BASE = f'http://127.0.0.1:{PORT}'
FAIL = []
def ok(cond, msg):
    print(('  ok   ' if cond else '  GAGAL ') + msg)
    if not cond: FAIL.append(msg)

def php(*args):
    return subprocess.run(['php', 'api/index.php', *args], cwd=D, capture_output=True, text=True).stdout

def setup(manual=False, routing=False):
    s = json.load(open(D + '/data/settings.json'))
    s['reply'] = {'mode': 'manual' if manual else 'ai'}
    s['wa_hemat'] = {'debounce_sec': 0}
    s['routing'] = {'enabled': routing, 'online_only': False}
    s['handoff'] = {'enabled': True, 'keywords': ['admin']}
    json.dump(s, open(D + '/data/settings.json', 'w'))
    json.dump([{'username': 'dias', 'password': 'rahasia123', 'role': 'super_admin', 'migrated_3role': True},
               {'username': 'a1', 'name': 'Agen Satu', 'password': 'rahasia123', 'role': 'wa_agent', 'migrated_3role': True}],
              open(D + '/data/users.json', 'w'))
    for f in ['conv-open.json', 'wa-modes.json', 'wa-claims.json', 'conv-state.json', 'chatbot-log.json', 'wa-seen.json', 'ratelimit.json', 'lockout.json']:
        p = D + '/data/' + f
        if os.path.exists(p): os.remove(p)
    shutil.rmtree(D + '/data/convs', ignore_errors=True)
    shutil.rmtree(D + '/data/wa-sessions', ignore_errors=True); os.makedirs(D + '/data/wa-sessions', exist_ok=True)
    if DB:
        subprocess.run(['mysql', '-uroot', 'sj_chat', '-e', 'truncate dei_conversations; truncate dei_log; truncate dei_conv_state; truncate dei_wa_seen; truncate dei_wa_sessions; truncate dei_contacts'])
        subprocess.run(['redis-cli', 'flushall'], capture_output=True)

N = [0]
def wh(num, text, echo=False):
    N[0] += 1; wamid = f'wamid.T{time.time_ns()}.{N[0]}'
    v = {'metadata': {'display_phone_number': '62211', 'phone_number_id': '123'}}
    if echo: v['message_echoes'] = [{'from': '62211', 'to': num, 'id': wamid, 'type': 'text', 'text': {'body': text}}]
    else:
        v['contacts'] = [{'wa_id': num, 'profile': {'name': 'Budi'}}]
        v['messages'] = [{'from': num, 'id': wamid, 'type': 'text', 'text': {'body': text}}]
    body = json.dumps({'entry': [{'changes': [{'field': 'smb_message_echoes' if echo else 'messages', 'value': v}]}]}).encode()
    sig = 'sha256=' + hmac.new(b'sec', body, hashlib.sha256).hexdigest()
    rq = urllib.request.Request(BASE + '/api/index.php?action=wa_webhook', data=body, headers={'Content-Type': 'application/json', 'X-Hub-Signature-256': sig})
    urllib.request.urlopen(rq, timeout=60).read()
    if DB: php('action=wa_worker', 'slot=9', 'max_sec=4', 'max_jobs=1')

TOK = {}
def api(action, user='dias', body=None, q='', raw=False):
    if user not in TOK:
        r = urllib.request.urlopen(urllib.request.Request(BASE + '/api/index.php?action=login', data=json.dumps({'username': user, 'password': 'rahasia123'}).encode(), headers={'Content-Type': 'application/json'})).read()
        TOK[user] = json.loads(r)['token']
    url = BASE + '/api/index.php?action=' + action + q
    rq = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers={'Content-Type': 'application/json', 'X-Auth-Token': TOK[user]})
    try: r = urllib.request.urlopen(rq, timeout=60).read()
    except urllib.error.HTTPError as e: r = e.read()
    return r.decode('utf-8') if raw else json.loads(r)

def conv(num): return api('wa_thread', q='&number=' + num).get('conv')
TS = ['opened_at', 'last_at', 'first_reply_at', 'first_bot_at', 'handover_at', 'assigned_at', 'first_agent_at', 'wait_since', 'closing_at', 'resolved_at', 'ended_at']
def age(num, sec):
    """geser semua waktu record terakhir nomor ini ke belakang."""
    def shift(c):
        for k in TS:
            if c.get(k): c[k] -= sec
        return c
    if DB:
        r = subprocess.run(['mysql', '-uroot', 'sj_chat', '-N', '-e', f"select body from dei_conversations where num='{num}' order by opened_at desc limit 1"], capture_output=True, text=True).stdout
        c = shift(json.loads(r))
        b = json.dumps(c).replace("\\", "\\\\").replace("'", "\\'")
        subprocess.run(['mysql', '-uroot', 'sj_chat', '-e', f"update dei_conversations set opened_at={c['opened_at']}, last_at={c['last_at']}, resolved_at={c.get('resolved_at',0)}, body='{b}' where id='{c['id']}'"])
    else:
        p = D + '/data/conv-open.json'; a = json.load(open(p)); shift(a[num]); json.dump(a, open(p, 'w'))

print(f'### {APP} ({"mysql" if DB else "file"})')
setup()
print('A. bot menjawab lalu pelanggan pamit -> selesai oleh bot')
wh('6281001', 'halo, jam buka?')
c = conv('6281001'); ok(c and c['status'] == 'open' and c['bot_msgs'] == 1 and c['first_reply_at'] > 0, f"terbuka, bot 1 balasan ({c and c['status']}, bot {c and c['bot_msgs']})")
wh('6281001', 'ok makasih')
c = conv('6281001'); ok(c['status'] == 'resolved' and c['resolved_by'] == 'guest_bye', f"selesai guest_bye ({c['status']}/{c['resolved_by']})")
wh('6281001', '👍')
c = conv('6281001'); ok(c['status'] == 'resolved' and c['guest_msgs'] == 3 and c['reopen_n'] == 0, 'jempol susulan tidak membuka ulang')

print('B. kata kunci -> serah ke agent -> claim -> balas -> Selesai')
wh('6281002', 'halo')
wh('6281002', 'mau bicara dengan admin')
c = conv('6281002'); ok(c['status'] == 'handover' and c['handover_reason'] == 'keyword', f"handover keyword ({c['status']}/{c['handover_reason']})")
r = api('wa_claim', 'a1', {'number': '6281002'}); ok(r.get('ok'), 'a1 claim')
c = conv('6281002'); ok(c['status'] == 'assigned' and c['agent'] == 'a1' and c['assigned_at'] >= c['handover_at'], 'assigned ke a1')
r = api('wa_send_manual', 'a1', {'number': '6281002', 'text': 'Halo kak, saya bantu'}); ok(r.get('ok'), 'a1 balas manual')
c = conv('6281002'); ok(c['agent_msgs'] == 1 and c['first_agent_at'] > 0 and c['aresp_n'] if 'aresp_n' in c else c['agent_msgs'] == 1, 'balasan agent tercatat')
r = api('wa_resolve', 'a1', {'number': '6281002'}); ok(r.get('ok') and r['conv']['status'] == 'resolved' and r['conv']['resolver'] == 'a1', 'Selesai oleh a1')
th = api('wa_thread', q='&number=6281002'); ok(th['mode'] == 'bot', 'chat dilepas, kembali ke bot')
cl = api('wa_conversations_v2', q='&filter=done'); ok(any(str(x.get('number')) == '6281002' for x in cl.get('conversations', cl.get('items', []))), 'muncul di filter Selesai')
r = api('wa_resolve', 'a1', {'number': '6281002'}); ok(r.get('ok'), 'Selesai dua kali tetap ok (idempoten)')

print('C. buka ulang <= 30 menit, percakapan baru setelahnya')
id1 = conv('6281002')['id']
wh('6281002', 'eh satu lagi kak')
c = conv('6281002'); ok(c['id'] == id1 and c['reopen_n'] == 1 and c['status'] in ('open', 'handover', 'assigned'), f"dibuka ulang ({c['status']}, reopen {c['reopen_n']})")
api('wa_resolve', 'dias', {'number': '6281002'})
age('6281002', 31 * 60)
wh('6281002', 'halo lagi, pertanyaan baru')
c = conv('6281002'); ok(c['id'] != id1 and c['reopen_n'] == 0, 'percakapan baru setelah 31 menit')

print('D. timeout 24 jam lewat cron_tick')
wh('6281003', 'berapa harga tiket?')
t_bot = conv('6281003')['last_at']
age('6281003', 25 * 3600)
out = json.loads(php('action=cron_tick'))
ok((out.get('conv') or {}).get('timeout') == 1, f"cron menutup 1 ({out.get('conv')}, err {out.get('err_conv')})")
c = conv('6281003'); ok(c['status'] == 'resolved' and c['resolved_by'] == 'timeout' and c['resolved_at'] == t_bot - 25 * 3600, 'resolved_at = balasan terakhir')

print('E. basi saat pesan baru (cron belum menyapu)')
wh('6281004', 'halo')
id4 = conv('6281004')['id']; age('6281004', 25 * 3600)
wh('6281004', 'halo, masih buka?')
c = conv('6281004'); ok(c['id'] != id4 and c['status'] == 'open', 'percakapan lama ditutup, yang baru dibuka')

print('F. balasan agent dari HP tanpa percakapan -> outbound')
wh('6281005', 'Halo pak, info promo', echo=True)
c = conv('6281005'); ok(c and c['origin'] == 'outbound' and c['status'] == 'assigned' and c['agent'] == '(HP)', f"outbound ({c and c['origin']}/{c and c['status']})")

print('G. batas tidak ada percakapan untuk "ok" saja')
wh('6281006', 'ok')
ok(conv('6281006') is None, 'tidak membuka percakapan')

print('H. laporan')
today = time.strftime('%Y-%m-%d', time.gmtime(time.time() + 7 * 3600))
r = api('conv_report', q=f'&from={today}&to={today}')
T = r.get('totals', {})
print('   totals', {k: T.get(k) for k in ['total', 'inbound', 'outbound', 'resolved', 'assigned', 'unassigned', 'bot_handled', 'bot_resolved', 'to_agent', 'reopened']})
print('   avg', r.get('avg'))
ok(r.get('ok') and T.get('outbound') == 1 and T.get('bot_resolved') == 1, 'conv_report ok, outbound 1, bot_resolved 1')
ok(r['avg']['frt'] is not None and len(r['hourly']) == 24 and len(r['weekday']) == 7, 'FRT & pola jam/hari')
ok(any(a['agent'] == 'a1' and a['resolved'] >= 1 for a in r['agents']), 'tabel agent memuat a1')
y = time.strftime('%Y-%m-%d', time.gmtime(time.time() + 7 * 3600 - 86400))
r2 = api('conv_report', q=f'&from={y}&to={y}')
ok(r2['totals']['resolved'] >= 2, f"kemarin: percakapan yang digeser (resolved {r2['totals']['resolved']})")
l = api('conv_list', q=f'&from={y}&to={today}&kind=resolved')
ok(l.get('ok') and l['total'] == r['totals']['resolved'] + r2['totals']['resolved'], f"conv_list resolved {l.get('total')}")
csv = api('conv_export', q=f'&from={y}&to={today}', raw=True)
ok(csv.count('\n') == r['totals']['total'] + r2['totals']['total'] + 1, 'CSV baris = total + header')
bad = api('conv_report', q='&from=2026-01-01&to=2026-06-30'); ok(not bad.get('ok'), 'rentang > 93 hari ditolak')
ag = api('conv_report', 'a1', q=f'&from={today}&to={today}'); ok(not ag.get('ok'), 'WA Agent tidak bisa membuka laporan')

print('I. Mode Manual: semua chat menunggu agent; routing membagi')
setup(manual=True)
wh('6281010', 'halo admin')
c = conv('6281010'); ok(c['status'] == 'handover' and c['handover_reason'] == 'manual_mode' and c['bot_msgs'] == 0, f"manual_mode ({c['status']}/{c['handover_reason']})")
r = api('conv_report', q=f'&from={today}&to={today}'); ok(r['totals']['unassigned'] == 1, 'Unassigned 1')
setup(manual=True, routing=True)
wh('6281011', 'halo')
c = conv('6281011'); ok(c['status'] == 'assigned' and c['agent'] == 'a1', f"routing -> a1 ({c['status']}/{c['agent']})")
r = api('wa_resolve', 'a1', {'number': '6281011'}); th = api('wa_thread', q='&number=6281011')
ok(r.get('ok') and not api('wa_conversations_v2', q='&filter=mine', user='a1').get('counts', {}).get('mine'), 'Selesai melepas claim')

print('HASIL:', 'LULUS' if not FAIL else 'GAGAL ' + str(len(FAIL)))
sys.exit(1 if FAIL else 0)
