#!/usr/bin/env python3
r"""v1.2.127 respon-kata: kalimat kartu Respon Pertama Bot/Agent dibuat sederhana.
 "4 dtk / umumnya · paling lama 2 hari 10 jam"; rata-rata pindah ke tooltip.
Pakai: python3 patch_v12127_respon_kata.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.126)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.127: respon-kata'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def rep(s, old, new, rel):
    n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:90]); return s.replace(old, new)
def patch(rel, fn):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    assert 'v1.2.126: respon-median' in s, rel + ': butuh v1.2.126'
    s2 = fn(s, rel); assert TAG in s2, rel
    shutil.copy2(p, p + '.bak-v12127-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s2); print('OK', rel)
def f_api(s, rel):
    return rep(s, "define('DEI_VERSION', 'v1.2.126');   // v1.2.126: respon-median",
                  "define('DEI_VERSION', 'v1.2.127');   // v1.2.127: respon-kata", rel)
def f_js(s, rel):
    s = rep(s, "    var subm = function (pre, k) { return pre + 'rata-rata ' + svDur(A[k]) + (X[k] != null && X[k] > (M[k] || 0) ? ' · terlama ' + svDur(X[k]) : ''); };\n",
               "    // v1.2.127: respon-kata — kalimat sederhana; rata-rata di tooltip\n"
               "    var subm = function (pre, k) { return pre + (X[k] != null && X[k] > (M[k] || 0) ? ' · paling lama ' + svDur(X[k]) : ''); };\n"
               "    var tipm = function (who, k) { return 'Separuh chat dibalas ' + who + ' dalam ' + svDur(M[k]) + ' atau lebih cepat (median).' + (A[k] != null ? ' Rata-rata ' + svDur(A[k]) + (A[k] > (M[k] || 0) * 3 ? ' — terseret beberapa chat yang sangat lama.' : '.') : ''); };\n", rel)
    s = rep(s, "subm('median · ', 'frt_bot'), dtm('frt_bot'), 'Median jeda dari pesan pertama pelanggan sampai balasan pertama bot. Median = nilai tengah, tidak terseret satu-dua chat yang sangat lama; rata-rata dan terlama di bawahnya.')",
               "subm('umumnya', 'frt_bot'), dtm('frt_bot'), tipm('bot', 'frt_bot') + ' Dihitung dari pesan pertama pelanggan.')", rel)
    s = rep(s, "subm('median sejak diserahkan · ', 'frt_agent'), dtm('frt_agent'), 'Median jeda dari diserahkan ke manusia sampai balasan pertama agent (agent membalas tanpa serah terima: dari pesan pertama pelanggan).')",
               "subm('umumnya, sejak diserahkan', 'frt_agent'), dtm('frt_agent'), tipm('agent', 'frt_agent') + ' Dihitung sejak chat diserahkan ke agent.')", rel)
    return s
patch('api/index.php', f_api)
patch('dashboard/chatbot-ai/app.js', f_js)
print('selesai')
