#!/usr/bin/env python3
"""v1.2.96 (tambahan) — status "sedang mengetik…" di WhatsApp selama AI berpikir + jeda balasan.
Meta Cloud API: status=read + typing_indicator (pesan pelanggan ikut centang biru; hilang saat
balasan terkirim atau maks 25 detik). WAHA: /api/startTyping lalu /api/stopTyping sebelum kirim.
Pemakaian: python3 patch_v1296b_mengetik.py <root dei-tenant>   (idempoten; backup *.bak-v1296b-*)
Butuh patch_v1296_jeda_balasan.py sudah terpasang."""
import sys, os, time, shutil
TEN = sys.argv[1]
STAMP = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.96: mengetik'

def patch(root, rel, pairs):
    p = os.path.join(root, rel)
    s = open(p, encoding='utf-8').read()
    if MARK in s: print('sudah dipatch:', rel); return
    if 'v1.2.96: jeda-balasan' not in s: sys.exit('GAGAL: patch v1.2.96 jeda-balasan belum terpasang di ' + rel)
    for old, new in pairs:
        n = s.count(old)
        if n != 1: sys.exit(f'GAGAL {rel}: anchor {n}x:\n{old[:200]}')
        s = s.replace(old, new)
    shutil.copy2(p, p + '.bak-v1296b-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

PHP_FUNCS = r'''/* v1.2.96: mengetik — tampilkan "sedang mengetik…" ke pelanggan selama AI berpikir + jeda.
 * Meta: wajib menyertakan id pesan masuk (dipasang waHandleMetaMessage di $GLOBALS['dei_in_wamid']);
 * panggilan ini sekaligus menandai pesan dibaca (centang biru). WAHA: startTyping/stopTyping. */
function deiTypingStart($s, $wa, $to) {
    $GLOBALS['dei_typing_on'] = false;
    try {
        if (!deiReplyDelayConf($s)['typing']) return false;
        $prov = (string)($wa['provider'] ?? 'meta');
        if ($prov === 'waha') {
            $num = waNormNum($to);
            if ($num === '') return false;
            list($c) = wahaApi($wa, 'POST', '/api/startTyping', ['session' => wahaSession($wa), 'chatId' => $num . '@c.us']);
            $GLOBALS['dei_typing_on'] = ($c >= 200 && $c < 300);
            return $GLOBALS['dei_typing_on'];
        }
        if ($prov !== 'meta') return false;
        $wamid = (string)($GLOBALS['dei_in_wamid'] ?? '');
        $token = (string)($wa['access_token'] ?? ''); $pnid = (string)($wa['phone_number_id'] ?? '');
        if ($wamid === '' || $token === '' || $pnid === '') return false;
        $ch = curl_init('https://graph.facebook.com/v21.0/' . rawurlencode($pnid) . '/messages');
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true, CURLOPT_POST => true, CURLOPT_TIMEOUT => 5, CURLOPT_CONNECTTIMEOUT => 3,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'Authorization: Bearer ' . $token],
            CURLOPT_POSTFIELDS => json_encode(['messaging_product' => 'whatsapp', 'status' => 'read',
                'message_id' => $wamid, 'typing_indicator' => ['type' => 'text']]),
        ]);
        $resp = curl_exec($ch); $code = curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
        if ($code < 200 || $code >= 300) { error_log('typing Meta HTTP ' . $code . ': ' . mb_substr((string)$resp, 0, 200)); return false; }
        $GLOBALS['dei_typing_on'] = true;
        return true;
    } catch (\Throwable $e) { error_log('typing: ' . $e->getMessage()); return false; }
}
// Meta menghapus indikator sendiri saat balasan masuk; WAHA perlu dihentikan.
function deiTypingStop($wa, $to) {
    if (empty($GLOBALS['dei_typing_on'])) return;
    $GLOBALS['dei_typing_on'] = false;
    try {
        if ((string)($wa['provider'] ?? 'meta') === 'waha') {
            wahaApi($wa, 'POST', '/api/stopTyping', ['session' => wahaSession($wa), 'chatId' => waNormNum($to) . '@c.us']);
        }
    } catch (\Throwable $e) { error_log('typing stop: ' . $e->getMessage()); }
}
'''

patch(TEN, 'api/index.php', [
    ("        'over_sec' => max(0, min(DEI_REPLY_DELAY_MAX, (int)($r['over_sec'] ?? 8))),\n    ];\n}\n",
     "        'over_sec' => max(0, min(DEI_REPLY_DELAY_MAX, (int)($r['over_sec'] ?? 8))),\n"
     "        'typing'   => !empty($r['typing']),   // v1.2.96: mengetik\n    ];\n}\n"),
    ("// Pesan sistem ke satu nomor maks sekali per $ttl detik.",
     PHP_FUNCS + "// Pesan sistem ke satu nomor maks sekali per $ttl detik."),
    ("    $deiT0 = microtime(true);   // v1.2.96: jeda-balasan\n",
     "    $deiT0 = microtime(true);   // v1.2.96: jeda-balasan\n"
     "    deiTypingStart($s, $wa, $from);   // v1.2.96: mengetik\n"),
    ("    if (!$deiAiError) deiReplyDelayWait($s, $text, $answer, $deiT0);   // v1.2.96: jeda-balasan\n",
     "    if (!$deiAiError) deiReplyDelayWait($s, $text, $answer, $deiT0);   // v1.2.96: jeda-balasan\n"
     "    deiTypingStop($wa, $from);   // v1.2.96: mengetik\n"),
    ("    $wamid = (string)($msg['id'] ?? '');\n    if ($wamid !== '' && waMsgSeen($wamid)) return;\n    try {\n",
     "    $wamid = (string)($msg['id'] ?? '');\n    if ($wamid !== '' && waMsgSeen($wamid)) return;\n"
     "    $GLOBALS['dei_in_wamid'] = $wamid;   // v1.2.96: mengetik\n    try {\n"),
])

patch(TEN, 'dashboard/chatbot-ai/index.html', [
    ('        <div class="row"><label class="fl">Hitung dari</label><select id="rd_basis">',
     '        <div class="toggle-row"><div><div class="tt">Tampilkan "sedang mengetik…"</div><div class="help">Pelanggan melihat status mengetik selama AI berpikir dan selama jeda. Bisa dipakai walau jeda mati. Di Meta Cloud API pesan pelanggan sekaligus ditandai dibaca (centang biru).</div></div><label class="switch"><input type="checkbox" id="rd_typing"><span class="sl"></span></label></div><!-- v1.2.96: mengetik -->\n'
     '        <div class="row"><label class="fl">Hitung dari</label><select id="rd_basis">'),
])

patch(TEN, 'dashboard/chatbot-ai/app.js', [
    ("    $('#rd_enabled').checked = rd.enabled === true;\n",
     "    $('#rd_enabled').checked = rd.enabled === true;\n    $('#rd_typing').checked = rd.typing === true;   // v1.2.96: mengetik\n"),
    ("    return { enabled: $('#rd_enabled').checked, basis: $('#rd_basis').value, rules: rules,\n",
     "    return { enabled: $('#rd_enabled').checked, typing: $('#rd_typing').checked, basis: $('#rd_basis').value, rules: rules,\n"),
])
print('selesai')
