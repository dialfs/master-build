#!/usr/bin/env python3
r"""v1.2.131 (lanjutan) ikon-dd:
- Dropdown Lead Rating di kepala thread (.wa-rate): klik di ikon tag & panah juga membuka pilihan (select menutupi seluruh pil).
- Ikon 'star' (sebelumnya tidak ada di peta ICONS -> ikon VIP kosong) dan 'message-square-heart'.
- Menu Customer Feedback memakai ikon message-square-heart.
Pakai: python3 patch_v12131c_ikon.py [~/Herd/dei-tenant] (idempoten; butuh patch_v12131b_log_selesai)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.131: ikon-dd'
NEED = 'v1.2.131: log-selesai'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def rep(s, old, new, rel):
    n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:100]); return s.replace(old, new)
def patch(rel, fn):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    assert NEED in s, rel + ': butuh ' + NEED
    s2 = fn(s, rel); assert TAG in s2, rel
    shutil.copy2(p, p + '.bak-v12131c-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s2); print('OK', rel)
def f_js(s, rel):
    return rep(s, "  var ICONS_EXTRA = {\n",
        "  var ICONS_EXTRA = {\n"
        "    'star':              '<polygon points=\"12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2\"/>',   // " + TAG + "\n"
        "    'message-square-heart': '<path d=\"M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z\"/><path d=\"M14.8 7.5a1.84 1.84 0 0 0-2.6 0l-.2.3-.3-.3a1.84 1.84 0 1 0-2.4 2.8L12 13l2.7-2.7c.9-.9.8-2.1.1-2.8\"/>',   // " + TAG + "\n", rel)
def f_html(s, rel):
    s = rep(s, '<button data-tab="gc"       data-role="super_admin,admin,supervisor" data-icon="star">',
               '<button data-tab="gc"       data-role="super_admin,admin,supervisor" data-icon="message-square-heart">', rel)
    s = rep(s, ".wa-rate select:disabled{cursor:default}\n",
        ".wa-rate select:disabled{cursor:default}\n"
        "/* " + TAG + ": select menutupi seluruh pil -> klik ikon/panah ikut membuka */\n"
        ".wa-rate{position:relative;padding:0}\n"
        ".wa-rate > svg{position:absolute;top:50%;transform:translateY(-50%);pointer-events:none}\n"
        ".wa-rate > svg:first-child{left:8px}\n"
        ".wa-rate > svg:last-child{right:7px}\n"
        ".wa-rate select{padding:2px 24px 2px 24px;line-height:1.6}\n", rel)
    return s
patch('dashboard/chatbot-ai/app.js', f_js)
patch('dashboard/chatbot-ai/index.html', f_html)
