#!/usr/bin/env python3
"""v1.2.180 (sesi-per-tenant): token login dashboard disimpan per tenant.
Sebelumnya semua tenant di satu domain (chatbot.deintegra.com/<tenant>) memakai kunci localStorage
'dei_token' / 'dei_user' yang sama, sehingga login / refresh token di tab tenant lain menimpa sesi
tenant ini -> 401 -> ke-logout. Kini kuncinya 'dei_token@<base>' / 'dei_user@<base>'.
Migrasi: bila kunci baru kosong, token lama 'dei_token' disalin sekali (token milik tenant lain
akan ditolak server -> login ulang sekali). Kunci lama tidak dihapus (tenant versi lama masih memakainya).
Idempoten.  Pakai: patch_v12180.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
T = H + '/dei-tenant'
API = T + '/api/index.php'; APP = T + '/dashboard/chatbot-ai/app.js'
LOG = T + '/dashboard/chatbot-ai/login.html'; IDX = T + '/dashboard/chatbot-ai/index.html'
TAG = 'v1.2.180: sesi-per-tenant'; stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def keys(s, label, n_tok, n_usr):
    s = rep(s, "localStorage.getItem('dei_token')", "localStorage.getItem(TK)", label + ' get tok', s.count("localStorage.getItem('dei_token')"))
    for fn in ('setItem', 'removeItem'):
        s = s.replace("localStorage.%s('dei_token'" % fn, "localStorage.%s(TK" % fn)
        s = s.replace("localStorage.%s('dei_user'" % fn, "localStorage.%s(UK" % fn)
    s = s.replace("localStorage.getItem('dei_user')", "localStorage.getItem(UK)")
    assert "'dei_token'" not in s and "'dei_user'" not in s, label + ': sisa kunci lama'
    return s
MIG = ("  var TK = 'dei_token@' + base, UK = 'dei_user@' + base;   // " + TAG + " — kunci sesi per tenant (satu domain banyak tenant)\n"
       "  try { if (!localStorage.getItem(TK) && localStorage.getItem('dei_token')) { localStorage.setItem(TK, localStorage.getItem('dei_token')); localStorage.setItem(UK, localStorage.getItem('dei_user') || 'null'); } } catch (e) {}   // " + TAG + ": migrasi sekali dari kunci lama\n")
done = []
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    if not NOBAK: shutil.copy2(p, p + '.bak-v12180-' + stamp)
    wr(p, fn(s)); done.append(p); print('OK', p)

def app(s):
    s = keys(s, 'app', 0, 0)
    return rep(s, "  var API = SITE_BASE + '/api/index.php';\n", "  var API = SITE_BASE + '/api/index.php';\n" + MIG, 'app anchor')
def login(s):
    s = keys(s, 'login', 0, 0)
    return rep(s, "  var API = window.location.origin + base + '/api/index.php';\n", "  var API = window.location.origin + base + '/api/index.php';\n" + MIG, 'login anchor')
def idx(s):
    return rep(s, '<script src="app.js?v=1.2.173"></script>', '<script src="app.js?v=1.2.180"></script><!-- ' + TAG + ' -->', 'idx cache')
def api(s):
    return rep(s, "define('DEI_VERSION', 'v1.2.179');   //", "define('DEI_VERSION', 'v1.2.180');   // " + TAG + " — token login dashboard disimpan per tenant; v1.2.179:", 'versi')

patch(APP, app); patch(LOG, login); patch(IDX, idx); patch(API, api)
print('selesai', len(done), 'berkas')
