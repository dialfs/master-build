import json, sys, hmac, hashlib, urllib.request
from eq import call, PORTS
toks = {p: call(p, 'login', body={'username': 'dias', 'password': 'rahasia123'}).get('token') for p in PORTS}
num = call(PORTS[0], 'wa_conversations_v2', toks[PORTS[0]])['conversations'][0]['number']
print('nomor uji', num)
steps = [('save_contact', {'number': num, 'name': 'Pak Budi Koreksi'}),
         ('save_contact_stage', {'number': num, 'stage': 'active_customer', 'vip': True}),
         ('save_contact_info', {'number': num, 'cust_name': 'Budi Santoso', 'cust_dob': '1990-05-17'}),
         ('save_contact', {'number': '6289999000111', 'name': 'Kontak Baru'}),
         ('wa_set_mode', {'number': num, 'mode': 'human'}),
         ('wa_claim', {'number': num}),
         ('wa_send_manual', {'number': num, 'text': 'Halo dari agent'})]
for a, b in steps:
    r = [call(p, a, toks[p], body=b) for p in PORTS]
    print(f'{a:20s}', 'file', json.dumps(r[0])[:70], '| db', json.dumps(r[1])[:70])
# echo coexistence -> logMutate
for port in PORTS:
    body = json.dumps({'entry': [{'changes': [{'value': {'metadata': {}, 'message_echoes': [{'to': num, 'id': 'wamid.echo1', 'type': 'text', 'text': {'body': 'dibalas dari HP'}}]}}]}]}).encode()
    for _ in range(2):  # kirim 2x: duplikat harus diabaikan
        rq = urllib.request.Request(f'http://127.0.0.1:{port}/api/index.php?action=wa_webhook', data=body, headers={'Content-Type': 'application/json', 'X-Hub-Signature-256': 'sha256=' + hmac.new(b'sec', body, hashlib.sha256).hexdigest()})
        urllib.request.urlopen(rq).read()
