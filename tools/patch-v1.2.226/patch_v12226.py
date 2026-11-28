#!/usr/bin/env python3
"""v1.2.226 (buat-template): buat message template WhatsApp dari dashboard (menu Blast WA).
- Kartu "Template WhatsApp": form nama, kategori (Utility/Marketing), bahasa, header, isi ({{n}} + contoh), footer -> kirim ke Meta.
- Daftar semua template + status (APPROVED/PENDING/REJECTED).
- API: wa_template_create (POST, Super Admin & Admin) -> POST /{waba}/message_templates.
Butuh v1.2.225. Idempoten. Pakai: patch_v12226.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H + '/dei-tenant'
TD = os.path.dirname(os.path.abspath(__file__))
TAG = 'v1.2.226: buat-template'; NEED = 'v1.2.225: es-coex'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12226-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
rd = lambda f: open(os.path.join(TD, 'src', f), encoding='utf-8').read()
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API)
else:
    assert NEED in s, 'v1.2.225 belum terpasang di ' + API
    s = rep(s, "define('DEI_VERSION', 'v1.2.225');   // v1.2.225:",
            "define('DEI_VERSION', 'v1.2.226');   // " + TAG + " — buat message template WhatsApp dari menu Blast WA; v1.2.225:", what='ver')
    s = rep(s, "    case 'wa_blast_start': {\n", rd('case226.php') + "\n    case 'wa_blast_start': {\n", what='case')
    save(API, s)

s = open(JS, encoding='utf-8').read()
if TAG in s: print('SUDAH', JS)
else:
    s = rep(s, "    if (!blastState.templates.length) fetchBlastTemplates();\n",
            "    if (!blastState.templates.length) fetchBlastTemplates();\n    tplInit();   // " + TAG + "\n", what='init')
    s = rep(s, "  function fetchBlastTemplates() {\n", rd('js226.js') + "\n  function fetchBlastTemplates() {\n", what='fn')
    save(JS, s)

s = open(HT, encoding='utf-8').read()
if TAG in s: print('SUDAH', HT)
else:
    a = '<div id="blastHistory"><div style="color:var(--muted);font-size:13px">Belum ada blast.</div></div>\n        </div>\n      </div>\n'
    s = rep(s, a, a + rd('html226.html'), what='card')
    s = rep(s, 'app.js?v=1.2.225', 'app.js?v=1.2.226', what='cachebust')
    save(HT, s)
