#!/usr/bin/env python3
r"""v1.2.130 selesai-fix: tombol Selesai chat lama (v1.2.129) tidak muncul — nomor di daftar percakapan
bertipe angka (kunci array PHP), nomor thread bertipe teks -> pencocokan pakai String().
Pakai: python3 patch_v12130_selesai_fix.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.129)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd/dei-tenant')
TAG = 'v1.2.130: selesai-fix'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def rep(s, old, new, rel):
    n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:100]); return s.replace(old, new)
def patch(rel, fn, need):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    assert need in s, rel + ': butuh v1.2.129'
    s2 = fn(s, rel); assert TAG in s2, rel
    shutil.copy2(p, p + '.bak-v12130-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s2); print('OK', rel)
def f_api(s, rel):
    return rep(s, "define('DEI_VERSION', 'v1.2.129');   // v1.2.129: wa-selesai-lama",
                  "define('DEI_VERSION', 'v1.2.130');   // " + TAG, rel)
def f_js(s, rel):
    for old in ["return c.number === num; })[0];   // v1.2.129: wa-selesai-lama", "return String(c.number) === String(num); })[0];   // v1.2.129: wa-selesai-lama"]:
        if old in s:
            return rep(s, old, "return String(c.number) === String(num); })[0];   // v1.2.129: wa-selesai-lama; " + TAG, rel)
    raise AssertionError(rel + ': anchor _li129 tidak ketemu')
def f_html(s, rel):
    return rep(s, '<script src="app.js?v=1.2.129"></script><!-- v1.2.129: wa-selesai-lama -->',
                  '<script src="app.js?v=1.2.130"></script><!-- ' + TAG + ' -->', rel)
patch('api/index.php', f_api, 'v1.2.129: wa-selesai-lama')
patch('dashboard/chatbot-ai/app.js', f_js, 'v1.2.129: wa-selesai-lama')
patch('dashboard/chatbot-ai/index.html', f_html, 'v1.2.129: wa-selesai-lama')
