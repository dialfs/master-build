#!/usr/bin/env python3
r"""v1.2.131 selesai-spv: tombol/aksi Selesai hanya untuk Supervisor, Admin, Super Admin.
Agent (wa_agent) tidak lagi bisa menandai selesai — termasuk chat yang ia pegang (sebelumnya boleh sejak v1.2.101).
Pakai: python3 patch_v12131_selesai_spv.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.130)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.131: selesai-spv'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def rep(s, old, new, rel):
    n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:100]); return s.replace(old, new)
def patch(rel, fn, need):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    assert need in s, rel + ': butuh v1.2.130'
    s2 = fn(s, rel); assert TAG in s2, rel
    shutil.copy2(p, p + '.bak-v12131-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s2); print('OK', rel)
def f_api(s, rel):
    s = rep(s, "define('DEI_VERSION', 'v1.2.130');   // v1.2.130: selesai-fix",
               "define('DEI_VERSION', 'v1.2.131');   // " + TAG, rel)
    s = rep(s, "    case 'wa_resolve': {\n        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);",
               "    case 'wa_resolve': {\n        $u = requireAuth(['super_admin', 'admin', 'supervisor']);   // " + TAG + " — agent tidak boleh", rel)
    s = rep(s, "        $isAdmin = in_array($u['role'], ['super_admin', 'admin', 'supervisor'], true);\n"
               "        if (!$isAdmin && $owner !== '' && $owner !== $u['username']) {\n"
               "            jsonOut(['ok' => false, 'error' => 'Chat ini dipegang ' . $owner . '. Hanya pemegang chat atau admin yang bisa menandai selesai.'], 403);\n"
               "        }\n", "", rel)
    return s
def f_js(s, rel):
    s = rep(s, "    if ((_openConv || (_li129 && _li129.flag && _li129.flag !== 'done')) && (!claim || isMine || waState.isAdmin)) {",
               "    if ((_openConv || (_li129 && _li129.flag && _li129.flag !== 'done')) && waState.isAdmin) {   // " + TAG + " — hanya Supervisor/Admin", rel)
    s = rep(s, "    // v1.2.101: percakapan — tombol Selesai (pemegang chat, admin/supervisor, atau chat yang belum dipegang)",
               "    // v1.2.101: percakapan — tombol Selesai; v1.2.131: hanya Supervisor / Admin / Super Admin", rel)
    return s
def f_html(s, rel):
    return rep(s, '<script src="app.js?v=1.2.130"></script><!-- v1.2.130: selesai-fix -->',
                  '<script src="app.js?v=1.2.131"></script><!-- ' + TAG + ' -->', rel)
patch('api/index.php', f_api, 'v1.2.130: selesai-fix')
patch('dashboard/chatbot-ai/app.js', f_js, 'v1.2.130: selesai-fix')
patch('dashboard/chatbot-ai/index.html', f_html, 'v1.2.130: selesai-fix')
