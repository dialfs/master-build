#!/usr/bin/env python3
"""v1.2.154 hp-firm — tampilan HP tidak geser/mantul. Idempoten. Pakai: patch_v12154.py <dei-tenant>"""
import sys, shutil, time
T = sys.argv[1]; TAG = 'v1.2.154: hp-firm'
A = T + '/api/index.php'; H = T + '/dashboard/chatbot-ai/index.html'; J = T + '/dashboard/chatbot-ai/app.js'
api, ht, js = (open(p, encoding='utf-8').read() for p in (A, H, J))
if all(TAG in s for s in (api, ht, js)):
    print('sudah dipatch'); sys.exit(0)
stamp = time.strftime('%Y%m%d-%H%M%S')
for p in (A, H, J): shutil.copy2(p, p + '.bak-v12154-' + stamp)
def rep(s, old, new, cnt=1):
    n = s.count(old); assert n == cnt, f'anchor {n}x (harus {cnt}): {old[:90]!r}'
    return s.replace(old, new)

api = rep(api, "define('DEI_VERSION', 'v1.2.153');   // v1.2.153: jadwal-kirim",
               "define('DEI_VERSION', 'v1.2.154');   // " + TAG)

ht = rep(ht, '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
             '<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover"><!-- ' + TAG + ': tanpa auto-zoom saat input disentuh -->')
ht = rep(ht, '<script src="app.js?v=1.2.153"></script><!-- v1.2.153: jadwal-kirim -->',
             '<script src="app.js?v=1.2.154"></script><!-- ' + TAG + ' -->')
ht = rep(ht, '/* v1.2.153: jadwal-kirim */\n',
    '/* ' + TAG + ': layar HP tidak geser ke samping / mantul */\n'
    '.wachat-body{overflow-x:hidden;overflow-wrap:anywhere;overscroll-behavior:contain}\n'
    '.wachat-list,.wa-chips,.kb-chips,.lk-board,.tbl-wrap,.scroll{overscroll-behavior-x:contain}\n'
    '.wachat-list{overscroll-behavior-y:contain}\n'
    '@media (max-width:860px){\n'
    '  html,body{overflow-x:hidden;overflow-x:clip;overscroll-behavior:none}\n'
    '  body{touch-action:manipulation;-webkit-text-size-adjust:100%;text-size-adjust:100%}\n'
    '}\n'
    '/* v1.2.153: jadwal-kirim */\n')

js = rep(js, "    waSchedInit();   // v1.2.153: jadwal-kirim",
             "    waSchedInit();   // v1.2.153: jadwal-kirim  (" + TAG + ")")
for p, s in ((A, api), (H, ht), (J, js)): open(p, 'w', encoding='utf-8').write(s)
print('OK', TAG)
