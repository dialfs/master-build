import os, json, subprocess, datetime, urllib.parse

ROOT = os.path.expanduser('~/demo/w/dei-chatbot-ai')
API = ROOT + '/api/index.php'
DATA = ROOT + '/data'
WIB = datetime.timezone(datetime.timedelta(hours=7))
NOW = datetime.datetime.now(WIB).replace(second=0, microsecond=0)
_clock = {'t': NOW}

def at(days_ago=0, hh=10, mm=0):
    d = (NOW - datetime.timedelta(days=days_ago)).replace(hour=hh, minute=mm, second=0)
    return d

def set_time(t):
    _clock['t'] = t

def tick(minutes=1, seconds=0):
    _clock['t'] = _clock['t'] + datetime.timedelta(minutes=minutes, seconds=seconds)
    return _clock['t']

CRED = {}
def call(action, method='GET', params=None, body=None, token=None, t=None, raw=False, extra_env=None, _retry=True):
    if isinstance(token, str) and token.startswith('@'):
        nm = token[1:]
        if nm not in TOK: login(*CRED[nm])
        r = call(action, method, params, body, TOK[nm], t, raw, extra_env)
        if isinstance(r, dict) and r.get('ok') is False and 'login kembali' in str(r.get('error')):
            login(*CRED[nm]); r = call(action, method, params, body, TOK[nm], t, raw, extra_env)
        return r
    t = t or _clock['t']
    q = {'action': action}
    if params: q.update(params)
    qs = urllib.parse.urlencode(q)
    data = b''
    if body is not None:
        data = body if isinstance(body, (bytes, str)) else json.dumps(body)
        if isinstance(data, str): data = data.encode()
    env = {
        'PATH': os.environ['PATH'], 'TZ': 'UTC', 'REDIRECT_STATUS': '200',
        'REQUEST_METHOD': method, 'QUERY_STRING': qs,
        'SCRIPT_FILENAME': API, 'SCRIPT_NAME': '/demo/api/index.php',
        'REQUEST_URI': '/demo/api/index.php?' + qs, 'DOCUMENT_ROOT': os.path.dirname(ROOT),
        'HTTP_HOST': 'chatbot.deintegra.com', 'HTTPS': 'on', 'SERVER_NAME': 'chatbot.deintegra.com', 'SERVER_PORT': '443',
        'REMOTE_ADDR': '36.72.10.%d' % (hash(action) % 200 + 1), 'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh) Demo',
        'CONTENT_TYPE': 'application/json', 'CONTENT_LENGTH': str(len(data)),
        'no_proxy': '127.0.0.1,localhost', 'NO_PROXY': '127.0.0.1,localhost',
        'http_proxy': '', 'https_proxy': '', 'HTTP_PROXY': '', 'HTTPS_PROXY': '',
    }
    if token: env['HTTP_AUTHORIZATION'] = 'Bearer ' + token
    if extra_env: env.update(extra_env)
    ft = t.astimezone(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    p = subprocess.run(['faketime', ft, 'php-cgi', '-d', 'cgi.force_redirect=0', '-d', 'display_errors=stderr'],
                       input=data, env=env, capture_output=True, cwd=os.path.dirname(API))
    out = p.stdout.decode('utf-8', 'replace')
    parts = out.split('\r\n\r\n', 1)
    bodytxt = parts[1] if len(parts) > 1 else out
    if raw: return bodytxt
    try:
        j = json.loads(bodytxt)
    except Exception:
        raise RuntimeError('%s -> non-JSON: %s | %s' % (action, bodytxt[:500], p.stderr.decode()[:500]))
    if isinstance(j, dict) and j.get('ok') is False and not (token and 'login kembali' in str(j.get('error'))):
        print('  !! %s %s -> %s' % (action, json.dumps(body)[:120] if body else params, j.get('error')))
    return j

def rj(name, default=None):
    p = os.path.join(DATA, name)
    if not os.path.exists(p): return default
    with open(p) as f: return json.load(f)

def wj(name, obj):
    with open(os.path.join(DATA, name), 'w') as f: json.dump(obj, f, ensure_ascii=False, indent=2)

def ai_queue(replies):
    with open(os.path.expanduser('~/demo/seed/ai-queue.json'), 'w') as f: json.dump(replies, f, ensure_ascii=False)

import random
def wa_in(num, name, text, bot_reply=None, t=None, ad=None):
    if bot_reply is not None: ai_queue([bot_reply])
    t = t or _clock['t']
    mid = 'false_%s@c.us_3A%s' % (num, ''.join(random.choice('0123456789ABCDEF') for _ in range(16)))
    evt = {'event': 'message', 'session': 'dei-demo', 'me': {'id': '6281100000001@c.us', 'pushName': 'Nusa EV'},
           'payload': {'id': mid, 'from': num + '@c.us', 'to': '6281100000001@c.us', 'fromMe': False, 'body': text,
                       'timestamp': int(t.timestamp()), 'hasMedia': False, '_data': {'notifyName': name}}}
    if ad:
        evt['payload']['_data']['ctwaContext'] = {'sourceUrl': 'https://fb.me/demo' + ad[1], 'sourceId': ad[1], 'sourceType': 'ad', 'title': ad[0], 'description': ad[0], 'ctwaClid': 'ARdemo' + ad[1]}
    r = call('wa_webhook_waha', 'POST', params={'key': 'seedkey'}, body=evt, t=t, raw=True)
    if r.strip() != 'OK': print('  webhook ->', r[:200])
    return r

TOK = {}
def login(u, p):
    CRED[u] = (u, p)
    r = call('login', 'POST', body={'username': u, 'password': p})
    TOK[u] = r['token']; return r['token']
