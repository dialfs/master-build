/* ============================================================================
 * v1.2.170: grup-wa — chat GRUP WhatsApp (WAHA) masuk dashboard, HANYA balasan manual.
 * Opsi whatsapp_api.wa_groups (bawaan mati = grup diabaikan seperti dulu).
 * Grup disimpan sebagai "nomor" semu = digit JID grup (> 15 digit, tidak bentrok dengan
 * nomor HP E.164 yang maks 15 digit); peta ke JID asli + nama grup di data/wa-groups.json.
 * Pesan grup TIDAK lewat waHandleMetaPayload (AI, handoff, debounce, survei, rate limit),
 * waGetMode grup selalu 'human', dan SEMUA kiriman ke grup ditolak kecuali dari endpoint
 * balasan manual (wa_send_manual / wa_send_media / jadwal kirim) yang menyalakan dei_grp_ok.
 * ========================================================================= */
define('WA_GROUPS_FILE', DATA_DIR . '/wa-groups.json');
function wgOn($s = null) { if ($s === null) $s = getSettings(); return !empty($s['whatsapp_api']['wa_groups']); }
function wgAll() {
    if (!isset($GLOBALS['dei_wg_cache'])) { $a = readJson(WA_GROUPS_FILE, []); $GLOBALS['dei_wg_cache'] = is_array($a) ? $a : []; }
    return $GLOBALS['dei_wg_cache'];
}
function wgKey($jid) {
    $jid = strtolower(trim((string)$jid));
    if (!preg_match('/^([0-9-]{6,48})@g\.us$/', $jid, $m)) return '';
    $k = preg_replace('/\D/', '', $m[1]);
    return strlen($k) > 15 ? $k : '';
}
function waIsGroup($num) { $k = preg_replace('/\D/', '', (string)$num); return $k !== '' && strlen($k) > 15 && isset(wgAll()[$k]); }
function wgJid($num) { $k = preg_replace('/\D/', '', (string)$num); $g = wgAll()[$k] ?? null; return is_array($g) ? (string)($g['jid'] ?? '') : ''; }
// chatId WAHA: grup -> JID grup; selain itu nomor@c.us (perilaku lama)
function waChatId($num) { $j = waIsGroup($num) ? wgJid($num) : ''; return $j !== '' ? $j : waNormNum($num) . '@c.us'; }
function wgPublic($num) {
    $g = wgAll()[preg_replace('/\D/', '', (string)$num)] ?? null;
    return is_array($g) ? ['name' => (string)($g['name'] ?? ''), 'jid' => (string)($g['jid'] ?? '')] : null;
}
function wgSave($key, $fn) {
    deiWithLock('wa-groups', function () use ($key, $fn) {
        $all = readJson(WA_GROUPS_FILE, []); if (!is_array($all)) $all = [];
        $g = is_array($all[$key] ?? null) ? $all[$key] : [];
        $fn($g);
        $all[$key] = $g;
        writeJson(WA_GROUPS_FILE, $all);
        $GLOBALS['dei_wg_cache'] = $all;
    });
}
// Boleh kirim ke grup? Hanya balasan manual (dei_grp_ok), lewat nomor WAHA, fitur menyala.
function wgSendOk($wa) {
    if (empty($GLOBALS['dei_grp_ok'])) { $GLOBALS['wa_last_error'] = 'Grup WhatsApp hanya bisa dibalas manual dari dashboard.'; error_log('grup-wa: kiriman otomatis ke grup ditolak'); return false; }
    if ((string)($wa['provider'] ?? 'meta') !== 'waha') { $GLOBALS['wa_last_error'] = 'Grup hanya bisa dibalas lewat nomor WAHA.'; return false; }
    if (!wgOn()) { $GLOBALS['wa_last_error'] = 'Fitur Chat Grup sedang dimatikan di Pengaturan.'; return false; }
    return true;
}
// JID grup dari event WAHA ('' = bukan grup)
function wgEvtJid($evt) {
    $p = is_array($evt['payload'] ?? null) ? $evt['payload'] : [];
    foreach (wahaChatCandidates($p, !empty($p['fromMe'])) as $cj) { if (preg_match('/@g\.us$/i', $cj)) return strtolower($cj); }
    return '';
}
// Nama grup dari WAHA (disimpan; diperbarui paling sering sehari sekali)
function wgName($wa, $key, $jid) {
    $g = wgAll()[$key] ?? [];
    $nm = (string)($g['name'] ?? '');
    if ($nm !== '' && (int)($g['nt'] ?? 0) > time() - 86400) return $nm;
    $new = '';
    try {
        list($c, $d) = wahaApi($wa, 'GET', '/api/' . rawurlencode(wahaSession($wa)) . '/groups/' . rawurlencode($jid));
        if ($c >= 200 && $c < 300 && is_array($d)) {
            foreach ([$d['subject'] ?? '', $d['name'] ?? '', $d['Name'] ?? '', $d['groupMetadata']['subject'] ?? '', $d['GroupName']['Name'] ?? ''] as $x) {
                if (is_string($x) && trim($x) !== '') { $new = mb_substr(trim($x), 0, 100); break; }
            }
        }
    } catch (\Throwable $e) {}
    wgSave($key, function (&$r) use ($new) { $r['nt'] = time(); if ($new !== '') $r['name'] = $new; });
    return $new !== '' ? $new : $nm;
}
function wgHandle($s, $wa, $evt) {
    $jid = wgEvtJid($evt);
    if ($jid === '' || !wgOn($s)) return;
    $key = wgKey($jid);
    if ($key === '') { error_log('grup-wa: JID grup tidak dikenali (' . mb_substr($jid, 0, 60) . ')'); return; }
    $p = is_array($evt['payload'] ?? null) ? $evt['payload'] : [];
    $dd = is_array($p['_data'] ?? null) ? $p['_data'] : [];
    $id = wahaMsgId($p);
    $fromMe = !empty($p['fromMe']);
    if ($fromMe && (($p['source'] ?? '') === 'api' || wahaSentByUs($key, $id, (string)($p['body'] ?? '')))) return;   // pantulan balasan dashboard
    // event message & message.any datang berdua -> catat sekali
    if ($id !== '' && !deiWithLock('wa-grp-seen', function () use ($id) { if (waMsgSeen('g:' . $id)) return false; waMsgMarkSeen('g:' . $id); return true; })) return;
    $ch = (string)($wa['_ch'] ?? '');
    $isNew = !isset(wgAll()[$key]);
    wgSave($key, function (&$r) use ($jid, $ch) { $r['jid'] = $jid; $r['last'] = time(); if ($ch !== '') $r['ch'] = $ch; });
    $gName = wgName($wa, $key, $jid);
    try { waSaveContact($key, $gName, $ch); } catch (\Throwable $e) { error_log('grup-wa kontak: ' . $e->getMessage()); }
    if ($isNew) error_log('grup-wa: grup baru tercatat ' . $key . ($gName !== '' ? ' (' . $gName . ')' : ''));

    // pengirim di dalam grup
    $pj = '';
    foreach ([$p['participant'] ?? '', $dd['key']['participant'] ?? '', $dd['Info']['Sender'] ?? '', $dd['author'] ?? '', $dd['id']['participant'] ?? ''] as $x) {
        if (is_string($x) && strpos($x, '@') !== false) { $pj = preg_replace('/:\d+@/', '@', trim($x)); break; }
    }
    $pNum = (!$fromMe && $pj !== '') ? wahaResolveNum($wa, $pj, $p) : '';
    $pName = '';
    if (!$fromMe) {
        foreach ([$dd['notifyName'] ?? '', $dd['pushName'] ?? '', $dd['Info']['PushName'] ?? '', $p['notifyName'] ?? ''] as $x) {
            if (is_string($x) && trim($x) !== '') { $pName = mb_substr(trim($x), 0, 60); break; }
        }
        if ($pNum !== '') { $cn = waContactName($pNum); if ($cn !== '') $pName = $cn; }   // nama kontak di dashboard menang
    }

    $body = trim((string)($p['body'] ?? ''));
    $type = 'text';
    if (!empty($p['hasMedia'])) {
        $mt = strtolower((string)($p['media']['mimetype'] ?? ''));
        $type = strpos($mt, 'image/') === 0 ? 'image' : (strpos($mt, 'video/') === 0 ? 'video'
              : (strpos($mt, 'audio/') === 0 ? 'audio' : ($mt !== '' ? 'document' : 'media')));
    } elseif ($body === '') {
        return;   // reaksi, pesan sistem grup (anggota masuk/keluar), dll.
    }
    $media = null; $text = $body;
    if ($type !== 'text') {
        list($media, $text) = deiWaMediaFromMsg($wa, $key, ['id' => $id, 'type' => $type, $type => wahaMediaObj($p, $body)]);
    }
    if (mb_strlen($text) > 4000) $text = mb_substr($text, 0, 4000);
    $row = ['ts' => date('Y-m-d H:i:s'), 'q' => $fromMe ? '' : $text, 'a' => $fromMe ? $text : '', 'ip' => $key, 'channel' => 'whatsapp',
            'grp' => 1, 'utm_source' => 'whatsapp', 'utm_medium' => 'group', 'utm_campaign' => '', 'page' => '', 'referrer' => ''];
    if ($fromMe) { $row['dir'] = 'manual'; $row['src'] = 'hp'; if ($id !== '') $row['echo_id'] = $id; }
    else {
        if ($id !== '') $row['wamid'] = mb_substr($id, 0, 120);
        $row['g_from'] = $pName !== '' ? $pName : ($pNum !== '' ? '+' . $pNum : 'Anggota');
        if ($pNum !== '') $row['g_num'] = $pNum;
    }
    if ($media) $row['media'] = $media;
    if ($ch !== '') $row['wa_ch'] = $ch;
    $rt = is_array($p['replyTo'] ?? null) ? $p['replyTo'] : null;   // kutipan: dicocokkan ulang oleh wa_thread (who kosong)
    if ($rt && !empty($rt['id'])) {
        $rid = is_array($rt['id']) ? (string)($rt['id']['_serialized'] ?? ($rt['id']['id'] ?? '')) : (string)$rt['id'];
        if ($rid !== '') $row['reply_to'] = ['id' => mb_substr($rid, 0, 120), 'who' => '', 'text' => deiQuoteSnippet(wahaQuotedBody($p, $rt))];
    }
    logPrepend($row, (int)($s['api']['log_limit'] ?? 500));
}
