import json, hmac, hashlib, sys, urllib.request, time, concurrent.futures as cf
BASE = sys.argv[1]  # http://127.0.0.1:PORT
import os; PFX = os.environ.get('PFX', '')
def post(num, text, wamid, name='Budi'):
    body = json.dumps({'entry': [{'changes': [{'value': {
        'metadata': {'display_phone_number': '62211', 'phone_number_id': '123'},
        'contacts': [{'wa_id': num, 'profile': {'name': name}}],
        'messages': [{'from': num, 'id': wamid, 'type': 'text', 'text': {'body': text}}]}}]}]}).encode()
    sig = 'sha256=' + hmac.new(b'sec', body, hashlib.sha256).hexdigest()
    rq = urllib.request.Request(BASE + '/api/index.php?action=wa_webhook', data=body, headers={'Content-Type': 'application/json', 'X-Hub-Signature-256': sig})
    t = time.time(); r = urllib.request.urlopen(rq, timeout=60).read().decode(); return r, round((time.time()-t)*1000)
if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'basic':
        print(post('628111', 'halo pertama', 'wamid.A1'))
        print(post('628111', 'halo pertama', 'wamid.A1'))          # kiriman ulang Meta
        print(post('628111', 'mau tanya harga', 'wamid.A2'))
    elif mode == 'nodup':
        print(post('628111', 'halo pertama', 'wamid.A1')); print(post('628111', 'mau tanya harga', 'wamid.A2'))
    elif mode == 'burst':   # N nomor x M pesan bersamaan
        N, M = int(sys.argv[3]), int(sys.argv[4]); jobs = []
        with cf.ThreadPoolExecutor(64) as ex:
            for m in range(M):
                for n in range(N):
                    jobs.append(ex.submit(post, f'62812{n:05d}', f'pesan {m}', f'wamid.{PFX}{n}.{m}'))
            lat = [j.result()[1] for j in jobs]
        lat.sort(); print('webhook ms p50', lat[len(lat)//2], 'p95', lat[int(len(lat)*.95)], 'max', lat[-1], 'n', len(lat))
