#!/usr/bin/env python3
"""v1.2.114 kontak-jumlah: angka total per Lead Rating di tombol filter menu Kontak.
Pakai: python3 patch_v12114_kontak_jumlah.py [~/Herd/dei-tenant]  (idempoten)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.114: kontak-jumlah'
STAMP = time.strftime('%Y%m%d-%H%M%S')
HERE = os.path.dirname(os.path.abspath(__file__))
part = lambda n: open(os.path.join(HERE, n), encoding='utf-8').read()
def patch(rel, edits):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    shutil.copy2(p, p + '.bak-v12114-' + STAMP)
    for old, new in edits:
        n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:80]); s = s.replace(old, new)
    assert TAG in s, rel; open(p, 'w', encoding='utf-8').write(s); print('OK', rel)
patch('api/index.php', [("define('DEI_VERSION', 'v1.2.113');   // v1.2.113: import-kontak",
                         "define('DEI_VERSION', 'v1.2.114');   // v1.2.114: kontak-jumlah")])
patch('dashboard/chatbot-ai/index.html', [('<script src="app.js?v=1.2.113"></script><!-- v1.2.113: import-kontak -->',
                                           '<script src="app.js?v=1.2.114"></script><!-- v1.2.114: kontak-jumlah -->')])
patch('dashboard/chatbot-ai/app.js', [
    ("  function renderContacts() {\n    var list = contactFilteredList();\n",
     part('fc_app.js') + "  function renderContacts() {\n    contactUpdateCounts();   // v1.2.114\n    var list = contactFilteredList();\n")])
print('selesai', TAG)
