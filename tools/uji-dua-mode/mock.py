import json, time, threading, sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
LOG = sys.argv[1] if len(sys.argv) > 1 else 'sends.log'
lk = threading.Lock()
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        import os
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pusat', self.path.lstrip('/').split('?')[0])
        if os.path.isfile(p):
            b = open(p, 'rb').read(); self.send_response(200); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
        else:
            self.send_response(404); self.end_headers()
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0)); body = json.loads(self.rfile.read(n) or b'{}')
        if 'chat/completions' in self.path:
            time.sleep(1.5)
            last = [m for m in body.get('messages', []) if m.get('role') == 'user'][-1]['content']
            if isinstance(last, list): last = ' '.join(x.get('text', '') for x in last)
            out = {'choices': [{'message': {'content': 'Balasan: ' + str(last)[-60:]}}],
                   'usage': {'prompt_tokens': 3000, 'completion_tokens': 50, 'cost': 0.001}}
        elif '/messages' in self.path:
            with lk:
                open(LOG, 'a').write(json.dumps({'t': time.time(), 'to': body.get('to'), 'text': body.get('text', {}).get('body')}, ensure_ascii=False) + '\n')
            out = {'messages': [{'id': 'wamid.out'}]}
        elif 'check_update' in self.path:
            import os
            mf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pusat', 'latest.json')
            out = json.load(open(mf)) if os.path.exists(mf) else {'ok': True, 'update_available': False}
        else:
            out = {'ok': True, 'result': {}}
        b = json.dumps(out).encode(); self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
S = ThreadingHTTPServer; S.request_queue_size = 512; S(('127.0.0.1', 9900), H).serve_forever()
