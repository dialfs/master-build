#!/usr/bin/env python3
"""v1.2.224 (kontak-manual): tambah kontak manual dari menu Kontak.
- Tombol "+ Tambah Kontak" (Super Admin, Admin, WA Agent): nomor WA (dirapikan ke 62…), nama, Lead Rating, VIP & tanggal lahir (Active Customer).
- Nomor yang sudah ada tidak ditimpa: muncul pesan + tombol "Buka kontak". Agent yang dibatasi Lead Rating hanya boleh pakai Lead Rating miliknya.
- API: add_contact (POST). get_contacts mengembalikan 'man' (ditambah manual: waktu & oleh siapa).
Butuh v1.2.223. Idempoten. Pakai: patch_v12224.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H + '/dei-tenant'
TD = os.path.dirname(os.path.abspath(__file__))
TAG = 'v1.2.224: kontak-manual'; NEED = 'v1.2.223: laporan-pdf'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12224-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
rd = lambda f: open(os.path.join(TD, 'src', f), encoding='utf-8').read()
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'
C = '   // ' + TAG

s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API)
else:
    assert NEED in s, 'v1.2.223 belum terpasang di ' + API
    s = rep(s, "define('DEI_VERSION', 'v1.2.223');   // v1.2.223:",
            "define('DEI_VERSION', 'v1.2.224');   // " + TAG + " — tambah kontak manual dari menu Kontak; v1.2.223:", what='ver')
    s = rep(s, "    case 'save_contact': {\n", rd('case224.php') + "    case 'save_contact': {\n", what='case')
    s = rep(s, "                'imp'         => (isset($c['imp']) && is_array($c['imp'])) ? $c['imp'] : null,   // v1.2.113\n",
            "                'imp'         => (isset($c['imp']) && is_array($c['imp'])) ? $c['imp'] : null,   // v1.2.113\n"
            "                'man'         => (isset($c['man']) && is_array($c['man'])) ? $c['man'] : null," + C + "\n", what='get_contacts')
    save(API, s)

s = open(JS, encoding='utf-8').read()
if TAG in s: print('SUDAH', JS)
else:
    s = rep(s, "    $$('.contact-filter').forEach(function (b) {\n      b.onclick = function () {\n        contactFilter = b.dataset.contactStage;",
            "    var _bAdd = $('#btnAddKontak'); if (_bAdd) _bAdd.onclick = contactAddOpen;" + C + "\n"
            "    $$('.contact-filter').forEach(function (b) {\n      b.onclick = function () {\n        contactFilter = b.dataset.contactStage;", what='bind')
    s = rep(s, "                (c.imp ? ' · <span title=\"' + esc('Diimpor ' + (c.imp.at || '') + (c.imp.src ? ' dari ' + c.imp.src : '')) + '\">diimpor</span>' : '') + '</div>' +   // v1.2.113\n",
            "                (c.imp ? ' · <span title=\"' + esc('Diimpor ' + (c.imp.at || '') + (c.imp.src ? ' dari ' + c.imp.src : '')) + '\">diimpor</span>' : '') +   // v1.2.113\n"
            "                (c.man ? ' · <span title=\"' + esc('Ditambah manual ' + (c.man.at || '').slice(0, 16) + (c.man.by ? ' oleh ' + c.man.by : '')) + '\">ditambah manual</span>' : '') + '</div>' +" + C + "\n", what='badge')
    s = rep(s, "  /* ---- v1.2.113: import-kontak -- impor kontak dari XLS/XLSX/CSV ---------- */\n",
            rd('js224.js') + "  /* ---- v1.2.113: import-kontak -- impor kontak dari XLS/XLSX/CSV ---------- */\n", what='js')
    save(JS, s)

s = open(HT, encoding='utf-8').read()
if TAG in s: print('SUDAH', HT)
else:
    s = rep(s, '          <button class="btn ghost sm" id="btnImportKontak" style="margin-left:auto"',
            '          <button class="btn sm" id="btnAddKontak" style="margin-left:auto" title="Tambah satu kontak secara manual">&#43; Tambah Kontak</button><!-- ' + TAG + ' -->\n'
            '          <button class="btn ghost sm" id="btnImportKontak"', what='btn')
    s = rep(s, '      <div class="card" id="kontakImportCard" style="display:none"></div>\n',
            '      <div class="card" id="kontakAddCard" style="display:none"></div><!-- ' + TAG + ' -->\n'
            '      <div class="card" id="kontakImportCard" style="display:none"></div>\n', what='card')
    s = rep(s, 'app.js?v=1.2.223', 'app.js?v=1.2.224', what='cachebust')
    save(HT, s)
