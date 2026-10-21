import json, urllib.request, sys, os
PORTS = tuple(int(x) for x in os.environ.get('PORTS', '8111,8112').split(','))
def call(port, action, tok=None, body=None, q=''):
    url = f'http://127.0.0.1:{port}/api/index.php?action={action}{q}'
    h = {'Content-Type': 'application/json'}
    if tok: h['X-Auth-Token'] = tok
    rq = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=h)
    try: return json.loads(urllib.request.urlopen(rq, timeout=30).read())
    except urllib.error.HTTPError as e: return {'HTTP': e.code, 'body': e.read().decode()[:200]}
def norm(x):
    s = json.dumps(x, sort_keys=True, ensure_ascii=False)
    for k in ('"server_time"', '"generated_at"', '"now"', '"version"', '"token"'): pass
    return s
if __name__ == "__main__":
    toks = {p: call(p, 'login', body={'username': 'dias', 'password': 'rahasia123'}).get('token') for p in PORTS}
    num = None
    tests = [('get_logs', ''), ('get_contacts', ''), ('get_leads', ''), ('wa_conversations', ''), ('wa_conversations_v2', ''), ('report', ''), ('logs_query', ''), ('kb_find_gaps', '')]
    r1 = call(PORTS[0], 'wa_conversations_v2', toks[PORTS[0]])
    convs = r1.get('conversations') or []
    if convs: num = convs[0].get('number')
    if num: tests.append(('wa_thread', f'&number={num}'))
    bad = 0
    for a, q in tests:
        A = call(PORTS[0], a, toks[PORTS[0]], q=q); B = call(PORTS[1], a, toks[PORTS[1]], q=q)
        for d in (A, B):
            if isinstance(d, dict):
                for k in ('ms', 'generated', 'now', 'ts_now', 'cached_at'): d.pop(k, None)
                if isinstance(d.get('conv'), dict):   # v1.2.101: id & waktu percakapan berbeda per jalan
                    d['conv'] = {k: (('<t>' if v else 0) if (k.endswith('_at') or k == 'id') else v) for k, v in d['conv'].items()}
        same = norm(A) == norm(B)
        if not same: bad += 1
        print(f'{a:22s} {"SAMA" if same else "BEDA"}  ok={A.get("ok") if isinstance(A,dict) else "?"} ukuran={len(norm(A))}')
        if not same:
            a_, b_ = norm(A), norm(B); i = next((i for i in range(min(len(a_), len(b_))) if a_[i] != b_[i]), 0); print('   file:', a_[max(0,i-80):i+120]); print('   db  :', b_[max(0,i-80):i+120])
    print('BEDA total', bad)
