import json, os, shutil, subprocess, zipfile, glob
SRC = '/root/demo/w/dei-chatbot-ai/data'
OUT = '/root/demo/out'
STG = OUT + '/data'
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
shutil.copytree(SRC, STG)

def h(p): return subprocess.run(['php', '-r', 'echo password_hash($argv[1], PASSWORD_DEFAULT);', p], capture_output=True, text=True).stdout
def rj(n): return json.load(open(os.path.join(STG, n)))
def wj(n, o): json.dump(o, open(os.path.join(STG, n), 'w'), ensure_ascii=False, indent=2)

users = [u for u in rj('users.json') if u['username'] != 'seed']
for u in users:
    u['password'] = h(u['username'])          # admin/admin, sales/sales
    u.pop('pw_changed_at', None); u.pop('tour_seen', None)
    u['release_seen'] = 'v1.2.220'
wj('users.json', users)

s = rj('settings.json')
s['api']['openrouter_api_key'] = ''            # diisi skrip server dari Pengaturan Pendaftaran
s['whatsapp_api'] = {'enabled': True, 'provider': 'waha', 'waha_url': '', 'waha_api_key': '', 'waha_session': 'dei-demo',
                     'waha_webhook_key': '', 'waha_number': '6281100000001', 'keep_context': True}
s['central_server'] = {'url': '', 'tenant_id': '', 'license_key': '', 'auto_update': False, 'last_check': '', 'last_result': ''}
wj('settings.json', s)

for n in ['cap-cache.json', 'license-cache.json', 'login-log.json', 'ratelimit.json', 'lockout.json', 'vapid-keys.json',
          'version.json', 'self-url.txt', '.secret.php', 'waha-sent.json', 'push-subs.json', 'sso-used.json', 'release-notes-cache.json']:
    p = os.path.join(STG, n)
    if os.path.exists(p): os.remove(p)
for p in glob.glob(STG + '/*.lock') + glob.glob(STG + '/.locks'): (shutil.rmtree if os.path.isdir(p) else os.remove)(p)
shutil.rmtree(STG + '/wa-health', ignore_errors=True)

# periksa sisa jejak seeding
bad = subprocess.run(['grep', '-rlE', '"seed"|127\\.0\\.0\\.1|mock-key|Sementara-Demo', STG], capture_output=True, text=True).stdout
print('sisa jejak:', bad or '(tidak ada)')

z = zipfile.ZipFile(OUT + '/demo-data.zip', 'w', zipfile.ZIP_DEFLATED)
for root, dirs, files in os.walk(STG):
    for f in files:
        full = os.path.join(root, f)
        z.write(full, 'data/' + os.path.relpath(full, STG))
z.close()
print(os.path.getsize(OUT + '/demo-data.zip'), 'bytes')
print(sorted(os.listdir(STG)))
