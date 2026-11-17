/* ============================================================================
 * v1.2.195: web-balas — tim membalas chat web (widget website & Asisten Bantuan)
 * dari menu Percakapan Web.
 *   - Pengunjung bisa minta bicara dengan tim (tombol di widget; pengaturan
 *     widget.web_human, selalu aktif di tenant Support).
 *   - Percakapan "ditahan" (AI tidak menjawab) selama: dipegang tim dan tim aktif
 *     <= 60 menit terakhir, atau permintaan pengunjung belum lewat 60 menit.
 *   - Pesan tim disimpan sebagai role "agent" (by = nama, by_u = username).
 *   - Pengunjung menerima balasan lewat web_poll (widget & panel Asisten).
 * ========================================================================= */
define('WEB_HOLD_SEC', 3600);
function deiWebHumanConf($s) {
    $w = (isset($s['widget']['web_human']) && is_array($s['widget']['web_human'])) ? $s['widget']['web_human'] : [];
    $sup = function_exists('deiSupportSelf') && deiSupportSelf();
    return ['enabled' => !empty($w['enabled']) || $sup, 'label' => $sup ? 'Bicara dengan tim DEI' : 'Bicara dengan tim kami'];
}
function deiWebHold($cv) {
    $now = time();
    if (!empty($cv['agent']) && $now - (int)($cv['agent_last'] ?? 0) < WEB_HOLD_SEC) return 'agent';
    if (!empty($cv['human_req']) && $now - (int)$cv['human_req'] < WEB_HOLD_SEC) return 'req';
    return '';
}
function deiWebPub($cv) {
    $h = deiWebHold($cv);
    return ['hold' => $h, 'agent_name' => $h === 'agent' ? (string)($cv['agent_name'] ?? '') : ''];
}
function deiWebAdminStatus($cv, $u = null) {
    $h = deiWebHold($cv);
    return ['hold' => $h, 'agent' => $h === 'agent' ? (string)($cv['agent'] ?? '') : '', 'agent_name' => $h === 'agent' ? (string)($cv['agent_name'] ?? '') : '',
            'mine' => $h === 'agent' && is_array($u) && (string)($cv['agent'] ?? '') === (string)($u['username'] ?? ''),
            'req_at' => !empty($cv['human_req']) ? (int)$cv['human_req'] : 0, 'agent_last' => (int)($cv['agent_last'] ?? 0), 'now' => time(),
            'archived' => !empty($cv['migrated'])];
}
/* pesan untuk pengunjung: tanpa field internal */
function deiWebMsgOut($m) {
    $o = ['role' => (string)($m['role'] ?? ''), 'content' => (string)($m['content'] ?? ''), 'ts' => (string)($m['ts'] ?? '')];
    if (($m['role'] ?? '') === 'agent') $o['by'] = (string)($m['by'] ?? '');
    if (!empty($m['sys'])) $o['sys'] = (string)$m['sys'];
    return $o;
}
function deiWebNotify($cv, $title, $text) {
    try {
        $f = DATA_DIR . '/push-subs.json';
        if (!is_file($f)) return;
        $subs = json_decode((string)file_get_contents($f), true);
        if (!is_array($subs) || !$subs) return;
        $keys = array_keys($subs);
        $who = (deiWebHold($cv) === 'agent' && !empty($cv['agent']) && in_array($cv['agent'], $keys, true)) ? [(string)$cv['agent']] : getPushTargetsByTopic('', $keys);
        sendPushToUsers($who, $title, mb_substr(trim((string)$text), 0, 90), deiDashboardUrl(), 'dei-web');
    } catch (\Throwable $e) { error_log('deiWebNotify: ' . $e->getMessage()); }
}
/* Pesan pengunjung ke percakapan yang ditahan: simpan, beri tahu tim, tanpa AI. null = tidak ditahan. */
function deiWebHeldChat($s, $convId, $visitorId, $message) {
    $convs = webConvReadAll();
    $idx = webConvFind($convs, $convId);
    if ($idx < 0 || ($convs[$idx]['visitor_id'] ?? '') !== $visitorId) return null;
    $hold = deiWebHold($convs[$idx]);
    if ($hold === '') return null;
    $ip = clientIp();
    if (!checkRateLimit($ip, (int)($s['api']['rate_limit'] ?? 20))) return ['ok' => false, 'error' => 'Terlalu banyak permintaan. Coba lagi nanti.'];
    $message = trim((string)$message);
    if ($message === '') return ['ok' => false, 'error' => 'Pesan kosong.'];
    if (mb_strlen($message) > 2000) $message = mb_substr($message, 0, 2000);
    $now = date('Y-m-d H:i:s');
    $msgs = webConvLoadMessages($convId);
    $msgs[] = ['role' => 'user', 'content' => $message, 'ts' => $now];
    webConvSaveMessages($convId, $msgs);
    $convs[$idx]['last_ts'] = $now;
    $convs[$idx]['last_message'] = mb_substr($message, 0, 120);
    $convs[$idx]['message_count'] = count($msgs);
    webConvWrite($convs);
    try { logPrepend(['ts' => $now, 'q' => $message, 'a' => '', 'ip' => $ip, 'channel' => 'web', 'web_held' => $hold], (int)($s['api']['log_limit'] ?? 500)); } catch (\Throwable $e) {}
    deiWebNotify($convs[$idx], $hold === 'agent' ? 'Pesan web baru' : 'Pengunjung web menunggu tim', ($convs[$idx]['title'] ?? 'Pengunjung') . ': ' . $message);
    return ['ok' => true, 'answer' => '', 'held' => true, 'kb_used' => 0, 'status' => deiWebPub($convs[$idx])];
}
/* Dipakai web_claim / web_reply / web_release: cari percakapan + cek boleh dipegang. */
function deiWebAdminConv($u, $convId, $forWrite) {
    $convs = webConvReadAll();
    $idx = webConvFind($convs, $convId);
    if ($idx < 0) jsonOut(['ok' => false, 'error' => 'Percakapan tidak ditemukan.'], 404);
    if (!empty($convs[$idx]['migrated'])) jsonOut(['ok' => false, 'error' => 'Percakapan arsip tidak bisa dibalas.'], 400);
    $hold = deiWebHold($convs[$idx]);
    $owner = (string)($convs[$idx]['agent'] ?? '');
    if ($forWrite && $hold === 'agent' && $owner !== '' && $owner !== (string)$u['username'] && ($u['role'] ?? '') === 'wa_agent') {
        jsonOut(['ok' => false, 'error' => 'Percakapan sedang dipegang ' . ((string)($convs[$idx]['agent_name'] ?? '') ?: $owner) . '.'], 409);
    }
    return [$convs, $idx];
}
