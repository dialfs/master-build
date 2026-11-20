#!/usr/bin/env python3
"""v1.2.212 (label-ai): kartu Penggunaan di Laporan — "Chat Terpakai" jadi "Balasan AI Terpakai", satuan "chat" jadi "balasan AI".
Butuh v1.2.211. Idempoten. Pakai: patch_v12212.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.212: label-ai'; NEED = 'v1.2.211: list-db'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s, old):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12212-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

j = open(JS, encoding='utf-8').read()
if TAG not in j:
    j = rep(j, "pctEl.textContent = res.chat_cap > 0 ? (res.chats_used||0) + ' / ' + res.chat_cap + ' chat' : (res.chats_used||0) + ' chat'; // v1.2.9: chat-based",
               "pctEl.textContent = res.chat_cap > 0 ? (res.chats_used||0) + ' / ' + res.chat_cap + ' balasan AI' : (res.chats_used||0) + ' balasan AI'; // v1.2.9: chat-based; " + TAG, what='js-pct')
    j = rep(j, "menunjukkan chat terpakai, reset,", "menunjukkan balasan AI terpakai, reset,", what='js-bantuan')
    save(JS, j, None)

h = open(HT, encoding='utf-8').read()
if TAG not in h:
    h = rep(h, 'letter-spacing:.4px">Chat Terpakai</div>', 'letter-spacing:.4px">Balasan AI Terpakai</div>', what='html-label')
    h = rep(h, '<script src="app.js?v=1.2.211"></script>', '<script src="app.js?v=1.2.212"></script><!-- ' + TAG + ' -->', what='html-ver')
    save(HT, h, None)

s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API); sys.exit(0)
assert NEED in s, 'butuh v1.2.211 dulu'
s = rep(s, "define('DEI_VERSION', 'v1.2.211');   // v1.2.211:",
        "define('DEI_VERSION', 'v1.2.212');   // " + TAG + " — label kartu Penggunaan: Balasan AI Terpakai; v1.2.211:", what='versi')
save(API, s, None)
