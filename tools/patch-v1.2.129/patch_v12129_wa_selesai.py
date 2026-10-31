#!/usr/bin/env python3
r"""v1.2.129 wa-selesai-lama:
- Tombol Selesai juga muncul di chat lama tanpa percakapan aktif (mis. "Belum dibalas · 96 hari") -> tandai selesai tanpa membalas.
- wa_resolve tidak menolak chat lama; tanda selesai disimpan permanen di kontak (res_at/res_by), tidak ikut terpangkas 3 hari.
- Chat yang ditandai selesai keluar dari "Belum Dibalas" & "Perlu Perhatian" sampai ada pesan baru.
- Dropdown Nomor / Lead Rating: klik di ikon & panah juga membuka pilihan.
Pakai: python3 patch_v12129_wa_selesai.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.128)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.129: wa-selesai-lama'
STAMP = time.strftime('%Y%m%d-%H%M%S')
NOBAK = '--nobak' in sys.argv

def rep(s, old, new, rel):
    n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:100]); return s.replace(old, new)

def patch(rel, fn, need):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    assert need in s, rel + ': butuh v1.2.128'
    s2 = fn(s, rel); assert TAG in s2, rel
    if not NOBAK: shutil.copy2(p, p + '.bak-v12129-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s2); print('OK', rel)

def f_api(s, rel):
    s = rep(s, "define('DEI_VERSION', 'v1.2.128');   // v1.2.128: wa-campur",
               "define('DEI_VERSION', 'v1.2.129');   // " + TAG, rel)
    s = rep(s, "function deiChatFlag($num, $meta, $cs, $agentReplied, $now = null) {\n    $now = $now ?? time();",
               "function deiChatFlag($num, $meta, $cs, $agentReplied, $now = null, $ct = null) {\n    $now = $now ?? time();", rel)
    s = rep(s, "    $flag = 'active'; $note = '';\n    if ($from === 'guest' && !$bye) {",
               "    $flag = 'active'; $note = ''; $marked = false;\n    if ($from === 'guest' && !$bye) {", rel)
    s = rep(s, "        $flag = 'done'; $note = 'Ditandai selesai' . (!empty($st['res_by']) ? ' oleh ' . $st['res_by'] : '');\n    }\n",
               "        $flag = 'done'; $note = 'Ditandai selesai' . (!empty($st['res_by']) ? ' oleh ' . $st['res_by'] : ''); $marked = true;\n    }\n"
               "    // v1.2.129: tanda selesai tersimpan di kontak (tidak ikut terpangkas 3 hari) — untuk chat lama\n"
               "    if (is_array($ct) && !empty($ct['res_at']) && (int)$ct['res_at'] >= (int)$at) {\n"
               "        $flag = 'done'; $note = 'Ditandai selesai' . (!empty($ct['res_by']) ? ' oleh ' . $ct['res_by'] : ''); $marked = true;\n    }\n", rel)
    s = rep(s, "        'full_bot'    => !$hasAgent,\n    ];\n}",
               "        'full_bot'    => !$hasAgent,\n        'marked'      => $marked,\n    ];\n}", rel)
    s = rep(s, "$fl = deiChatFlag((string)$num, $meta, $convState, $agentReplied, $nowTs);",
               "$fl = deiChatFlag((string)$num, $meta, $convState, $agentReplied, $nowTs, $allContacts[$num] ?? null);   // v1.2.129", rel)
    s = rep(s, "            if ($isToday) $cntToday++;\n            if ($needsAttention) $cntAttention++;",
               "            if (!empty($fl['marked'])) $needsAttention = false;   // v1.2.129: ditandai selesai → tidak perlu perhatian\n"
               "            if ($isToday) $cntToday++;\n            if ($needsAttention) $cntAttention++;", rel)
    s = rep(s, "        $c = convStoreGet($num);\n        if (!$ok && !convIsFinal($c)) jsonOut(['ok' => false, 'error' => 'Tidak ada percakapan aktif untuk nomor ini.'], 409);",
               "        $c = convStoreGet($num);\n"
               "        // v1.2.129: chat lama tanpa percakapan aktif tetap boleh ditandai selesai (tanpa membalas)\n"
               "        try { waContactUpdate($num, function (&$r) use ($u) { $r['res_at'] = time(); $r['res_by'] = $u['username']; }); }\n"
               "        catch (\\Throwable $e) { error_log('wa_resolve contact: ' . $e->getMessage()); }", rel)
    return s

def f_js(s, rel):
    return rep(s, "    if (res.conv && ['open', 'handover', 'assigned'].indexOf(res.conv.status) > -1 && (!claim || isMine || waState.isAdmin)) {",
        "    var _li129 = (waState.convs || []).filter(function (c) { return c.number === num; })[0];   // " + TAG + " — chat lama tanpa percakapan aktif\n"
        "    var _openConv = res.conv && ['open', 'handover', 'assigned'].indexOf(res.conv.status) > -1;\n"
        "    if ((_openConv || (_li129 && _li129.flag && _li129.flag !== 'done')) && (!claim || isMine || waState.isAdmin)) {", rel)

def f_html(s, rel):
    s = rep(s, '<script src="app.js?v=1.2.128"></script><!-- v1.2.128: wa-campur -->',
               '<script src="app.js?v=1.2.129"></script><!-- ' + TAG + ' -->', rel)
    s = rep(s, '.wa-dd{position:relative;display:inline-flex;align-items:center;gap:7px;height:34px;padding:0 30px 0 11px;',
               '.wa-dd{position:relative;display:inline-flex;align-items:center;height:34px;padding:0;', rel)
    s = rep(s, '.wa-dd select{appearance:none;',
               '.wa-dd > svg{position:absolute;left:11px;top:50%;transform:translateY(-50%);pointer-events:none}\n.wa-dd select{appearance:none;', rel)
    s = rep(s, 'font-weight:600;padding:0;margin:0;width:auto;max-width:240px;',
               'font-weight:600;padding:0 30px 0 32px;margin:0;height:100%;width:auto;max-width:300px;', rel)
    s = rep(s, '  .wa-dd{flex:1 1 0;min-width:0;height:32px;padding:0 24px 0 9px}\n',
               '  .wa-dd{flex:1 1 0;min-width:0;height:32px;padding:0}\n  .wa-dd > svg{left:9px}\n', rel)
    s = rep(s, 'min-width:0;font-size:12.5px}', 'min-width:0;font-size:12.5px;padding:0 24px 0 29px}', rel)
    return s

patch('api/index.php', f_api, 'v1.2.128: wa-campur')
patch('dashboard/chatbot-ai/app.js', f_js, 'v1.2.128: wa-campur')
patch('dashboard/chatbot-ai/index.html', f_html, 'v1.2.128: wa-campur')
