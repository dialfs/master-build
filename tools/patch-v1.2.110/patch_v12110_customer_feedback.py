#!/usr/bin/env python3
"""v1.2.110: customer-feedback — Guest Comment diganti nama jadi "Customer Feedback" (umum lintas industri):
teks bawaan umum, label nomor referensi bisa diatur (kamar/meja/pesanan/kode booking), preset aspek per industri,
kata kunci "survey" = "survei", bawaan lama khas hotel yang belum diubah dimigrasikan otomatis.
Mengganti blok v1.2.109 utuh (old/*) dengan blok baru. Pakai: python3 patch_v12110_customer_feedback.py ~/Herd (idempoten)"""
import sys, os, shutil, time
D = os.path.dirname(os.path.abspath(__file__))
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd'); T = H + '/dei-tenant'
TAG = 'v1.2.110: customer-feedback'
stamp = time.strftime('%Y%m%d-%H%M%S')
rd = lambda f: open(os.path.join(D, f), encoding='utf-8').read()
QR = rd('qrcode.min.js').strip()
P = {
 'api/index.php': [
  ("define('DEI_VERSION', 'v1.2.109');   // v1.2.109: guest-comment", "define('DEI_VERSION', 'v1.2.110');   // " + TAG),
  (rd('old/gc_funcs.php'), rd('gc_funcs.php')),
  (rd('old/gc_cases.php'), rd('gc_cases.php')),
 ],
 'dashboard/chatbot-ai/app.js': [
  (rd('old/gc_app.js').replace('/*@@QRLIB@@*/', QR), rd('gc_app.js').replace('/*@@QRLIB@@*/', QR)),
 ],
 'dashboard/chatbot-ai/index.html': [
  ('<span class="ic"></span> Guest Comment</button><!-- v1.2.109: guest-comment -->',
   '<span class="ic"></span> Customer Feedback</button><!-- v1.2.109: guest-comment; ' + TAG + ' -->'),
  (rd('old/gc_panel.html'), rd('gc_panel.html')),
  ('<script src="app.js?v=1.2.109"></script><!-- v1.2.109: guest-comment -->',
   '<script src="app.js?v=1.2.110"></script><!-- ' + TAG + ' -->'),
 ],
}
for f, reps in P.items():
    p = T + '/' + f; s = open(p, encoding='utf-8').read(); o = s
    for a, b in reps:
        if b in s: continue
        assert s.count(a) == 1, 'anchor tidak unik/tidak ada di ' + f + ' (' + str(s.count(a)) + '): ' + a[:70]
        s = s.replace(a, b)
    if s != o:
        shutil.copy2(p, p + '.bak-v12110-' + stamp)
        open(p, 'w', encoding='utf-8').write(s); print('patched', f)
    else: print('sudah', f)
