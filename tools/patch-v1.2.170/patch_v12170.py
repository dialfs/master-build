#!/usr/bin/env python3
"""v1.2.170 grup-wa (TENANT): chat grup WhatsApp (WAHA) masuk dashboard — opsi on/off, bot TIDAK membalas,
hanya balasan manual. Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
GRP = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grp.php')
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HTML = T + '/dashboard/chatbot-ai/index.html'
TAG = 'v1.2.170: grup-wa'; stamp = time.strftime('%Y%m%d-%H%M%S')
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    shutil.copy2(p, p + '.bak-v12170-' + stamp); wr(p, fn(s)); print('OK', p)
C = '   // ' + TAG

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.169');   // v1.2.169:",
               "define('DEI_VERSION', 'v1.2.170');   // " + TAG + " — chat grup WA (WAHA) masuk dashboard, opsi on/off, hanya balasan manual; v1.2.169:", 'versi')
    # modul grup
    a = "// Terjemahkan event WAHA (message / message.any) ke payload bentuk Meta.\n"
    s = rep(s, a, rd(GRP).rstrip() + "\n" + a, 'modul')
    # webhook WAHA: grup lewat jalur sendiri (tanpa AI)
    s = rep(s, "        $payload = wahaToMetaPayload($wa, $evt);\n        if ($payload === null) { echo 'OK'; exit; }",
        "        if (wgEvtJid($evt) !== '') {" + C + " — jalur sendiri, tidak pernah ke AI\n"
        "            $eaG = function_exists('fastcgi_finish_request') || function_exists('litespeed_finish_request');\n"
        "            if ($eaG) respondAndContinue('OK');\n"
        "            try { wgHandle($s, $wa, $evt); } catch (\\Throwable $e) { error_log('grup-wa: ' . $e->getMessage()); }\n"
        "            if (!$eaG) echo 'OK';\n"
        "            exit;\n"
        "        }\n"
        "        $payload = wahaToMetaPayload($wa, $evt);\n        if ($payload === null) { echo 'OK'; exit; }", 'webhook')
    # penjaga kirim: grup hanya dari balasan manual
    G = "\n    if (waIsGroup($to) && !wgSendOk($wa)) return false;" + C
    s = rep(s, "$wa = waChanFor($wa, $to); $GLOBALS['wa_out_ch'] = (string)($wa['_ch'] ?? '');   // v1.2.98: multi-nomor\n    // v1.2.36: pilih penyedia",
               "$wa = waChanFor($wa, $to); $GLOBALS['wa_out_ch'] = (string)($wa['_ch'] ?? '');   // v1.2.98: multi-nomor" + G + "\n    // v1.2.36: pilih penyedia", 'waSend')
    s = rep(s, "$wa = waChanFor($wa, $to); $GLOBALS['wa_out_ch'] = (string)($wa['_ch'] ?? '');   // v1.2.98: multi-nomor\n    $GLOBALS['wa_last_error'] = '';\n    if (!is_file($path)) { $GLOBALS['wa_last_error'] = 'File foto tidak ada.';",
               "$wa = waChanFor($wa, $to); $GLOBALS['wa_out_ch'] = (string)($wa['_ch'] ?? '');   // v1.2.98: multi-nomor" + G + "\n    $GLOBALS['wa_last_error'] = '';\n    if (!is_file($path)) { $GLOBALS['wa_last_error'] = 'File foto tidak ada.';", 'waSendImage')
    s = rep(s, "$wa = waChanFor($wa, $to); $GLOBALS['wa_out_ch'] = (string)($wa['_ch'] ?? '');\n    $GLOBALS['wa_last_error'] = ''; $GLOBALS['wa_last_out_id'] = '';   // v1.2.121",
               "$wa = waChanFor($wa, $to); $GLOBALS['wa_out_ch'] = (string)($wa['_ch'] ?? '');" + G + "\n    $GLOBALS['wa_last_error'] = ''; $GLOBALS['wa_last_out_id'] = '';   // v1.2.121", 'waSendFile')
    s = rep(s, "function waSendTemplate($wa, $to, $name, $lang, $vars = []) {\n",
               "function waSendTemplate($wa, $to, $name, $lang, $vars = []) {\n    if (waIsGroup($to)) return ['ok' => false, 'error' => 'Template tidak bisa dikirim ke grup.'];" + C + "\n", 'waSendTemplate')
    s = rep(s, "function waSendWaha($wa, $to, $text) {\n    $GLOBALS['wa_last_error'] = '';\n",
               "function waSendWaha($wa, $to, $text) {\n    $GLOBALS['wa_last_error'] = '';\n    if (waIsGroup($to) && !wgSendOk($wa)) return false;" + C + "\n", 'waSendWaha')
    # chatId: grup -> JID grup
    s = rep(s, "'chatId' => $to . '@c.us'", "'chatId' => waChatId($to)", 'chatId', 3)
    s = rep(s, "'chatId' => $num . '@c.us']", "'chatId' => waChatId($num)]", 'typing start')
    s = rep(s, "'chatId' => waNormNum($to) . '@c.us']", "'chatId' => waChatId($to)]", 'typing stop')
    # mode & pelacakan: grup selalu manusia, tidak ikut auto-closing / laporan agent / skor risiko
    s = rep(s, "    if (deiIsManual()) return 'human';   // v1.2.58: mode Manual = semua nomor dipegang manusia\n",
               "    if (deiIsManual()) return 'human';   // v1.2.58: mode Manual = semua nomor dipegang manusia\n    if (waIsGroup($from)) return 'human';" + C + "\n", 'waGetMode')
    s = rep(s, "function waSetMode($from, $mode, $reason = '') {   // v1.2.101: + alasan serah ke agent\n",
               "function waSetMode($from, $mode, $reason = '') {   // v1.2.101: + alasan serah ke agent\n    if (waIsGroup($from)) return;" + C + "\n", 'waSetMode')
    for f, ret in [('convReply($num, $who)', 'return;'), ("convGuestMsg($num, $text, $ch = '') {   // v1.2.101: + nomor bisnis", 'return;'), ('convTrack($num, $ev, $x = [])', 'return false;')]:
        hd = 'function ' + f + (' {' if not f.endswith('bisnis') else '') + "\n    $num = waNormNum($num);\n    if ($num === '') " + ret + "\n"
        s = rep(s, hd, hd + "    if (waIsGroup($num)) " + ret + C + "\n", f)
    s = rep(s, "function deiRecordAgentReply($num, $agent, $src = 'dashboard') {\n",
               "function deiRecordAgentReply($num, $agent, $src = 'dashboard') {\n    if (waIsGroup($num)) return;" + C + "\n", 'deiRecordAgentReply')
    s = rep(s, "    $to = waNormNum($to);\n    if (!whOn($wa) || $to === '') return;\n",
               "    $to = waNormNum($to);\n    if (!whOn($wa) || $to === '' || waIsGroup($to)) return;" + C + "\n", 'whOut')
    # klasifikasi topik (kuota AI): grup tidak ikut backfill
    s = rep(s, "        if ($n !== '' && (!isset($last[$n]) || strcmp($ts, $last[$n]) > 0)) $last[$n] = $ts;\n    }\n    if (function_exists('wiIndexAll'))",
               "        if ($n !== '' && !waIsGroup($n) && (!isset($last[$n]) || strcmp($ts, $last[$n]) > 0)) $last[$n] = $ts;" + C + "\n    }\n    if (function_exists('wiIndexAll'))", 'tpBackfill')
    # daftar percakapan lama
    s = rep(s, "        foreach ($logs as $e) {                       // logs are newest-first\n            if (($e['channel'] ?? '') !== 'whatsapp') continue;\n            $num = waNormNum($e['ip'] ?? '');\n            if ($num === '') continue;\n",
               "        foreach ($logs as $e) {                       // logs are newest-first\n            if (($e['channel'] ?? '') !== 'whatsapp') continue;\n            $num = waNormNum($e['ip'] ?? '');\n            if ($num === '') continue;\n            if (waIsGroup($num) && !wgOn()) continue;" + C + "\n", 'wa_conversations')
    s = rep(s, "        foreach ($byNum as $num => $c) {\n            $c['mode'] = waGetMode($num);\n",
               "        foreach ($byNum as $num => $c) {\n            if (waIsGroup($num)) $c['number'] = (string)$num;" + C + " — id grup 18 digit melebihi angka aman JS\n            $c['mode'] = waGetMode($num);\n", 'wa_conversations str')
    # daftar percakapan v2
    s = rep(s, "        $filter = $_GET['filter'] ?? 'all';  // all|mine|unclaimed|others|takeover_requests\n",
               "        $filter = $_GET['filter'] ?? 'all';  // all|mine|unclaimed|others|takeover_requests\n        $grpOn170 = wgOn();" + C + "\n", 'v2 on')
    s = rep(s, "            if ($num === '') continue;\n            if (!isset($numbers[$num])) {\n                $numbers[$num] = [\n                    'last_ts' => $e['ts'] ?? '',\n                    'last_q' => $e['q'] ?? '',",
               "            if ($num === '') continue;\n            if (!$grpOn170 && waIsGroup($num)) continue;" + C + "\n            if (!isset($numbers[$num])) {\n                $numbers[$num] = [\n                    'last_ts' => $e['ts'] ?? '',\n                    'last_q' => (($e['q'] ?? '') !== '' && !empty($e['g_from'])) ? $e['g_from'] . ': ' . $e['q'] : ($e['q'] ?? ''),", 'v2 loop')
    s = rep(s, "            $fl = deiChatFlag((string)$num, $meta, $convState, $agentReplied, $nowTs, $allContacts[$num] ?? null);   // v1.2.129\n",
               "            $fl = deiChatFlag((string)$num, $meta, $convState, $agentReplied, $nowTs, $allContacts[$num] ?? null);   // v1.2.129\n"
               "            $isGrp170 = waIsGroup($num);" + C + " — grup tidak masuk hitungan belum dibalas / perlu perhatian\n"
               "            if ($isGrp170) $fl = ['flag' => 'active', 'flag_note' => '', 'waiting_sec' => 0, 'last_from' => $fl['last_from'] ?? '', 'full_bot' => false];\n", 'v2 flag')
    s = rep(s, "            if (!empty($fl['marked'])) $needsAttention = false;   // v1.2.129: ditandai selesai → tidak perlu perhatian\n",
               "            if (!empty($fl['marked'])) $needsAttention = false;   // v1.2.129: ditandai selesai → tidak perlu perhatian\n            if ($isGrp170) $needsAttention = false;" + C + "\n", 'v2 attn')
    s = rep(s, "                'number' => $num,\n                'name' => waContactName($num, $allContacts),   // v1.2.19\n",
               "                'number' => $isGrp170 ? (string)$num : $num," + C + " — id grup 18 digit melebihi angka aman JS\n                'is_group' => $isGrp170,\n                'name' => waContactName($num, $allContacts),   // v1.2.19\n", 'v2 item')
    # thread
    s = rep(s, "                       'call_txt' => wcLabel($e),   // v1.2.108: tolak-telepon\n",
               "                       'call_txt' => wcLabel($e),   // v1.2.108: tolak-telepon\n                       'g_from' => (string)($e['g_from'] ?? '')," + C + "\n", 'thread msg')
    s = rep(s, "            'mode' => waGetMode($num),\n            'history' =>",
               "            'mode' => waGetMode($num),\n            'group' => wgPublic($num)," + C + "\n            'history' =>", 'thread group')
    # balasan manual: satu-satunya jalur yang boleh kirim ke grup
    s = rep(s, "        $GLOBALS['dei_out_src'] = 'agent';   // v1.2.104: skor-risiko-wa\n        $GLOBALS['wa_reply_to'] = $rq121 ? $rq121['id'] : '';   // v1.2.121\n",
               "        $GLOBALS['dei_out_src'] = 'agent';   // v1.2.104: skor-risiko-wa\n        $GLOBALS['dei_grp_ok'] = true;" + C + "\n        $GLOBALS['wa_reply_to'] = $rq121 ? $rq121['id'] : '';   // v1.2.121\n", 'manual')
    s = rep(s, "        $GLOBALS['dei_out_src'] = 'agent';\n        $rqM = ",
               "        $GLOBALS['dei_out_src'] = 'agent';\n        $GLOBALS['dei_grp_ok'] = true;" + C + "\n        $rqM = ", 'media')
    s = rep(s, "    $GLOBALS['dei_out_src'] = 'agent';\n    $GLOBALS['wa_reply_to'] = '';\n    $okS = $md ? waSendFile($wa, $num, $mp, (string)$md['type'], (string)$md['mime'], $text, (string)$md['name']) : waSend($wa, $num, $text);\n",
               "    $GLOBALS['dei_out_src'] = 'agent';\n    $GLOBALS['wa_reply_to'] = '';\n    $GLOBALS['dei_grp_ok'] = true;" + C + " — jadwal dibuat manual oleh agent\n    $okS = $md ? waSendFile($wa, $num, $mp, (string)$md['type'], (string)$md['mime'], $text, (string)$md['name']) : waSend($wa, $num, $text);\n    $GLOBALS['dei_grp_ok'] = false;\n", 'sched')
    # kontak: grup bukan kontak pelanggan
    s = rep(s, "        foreach ($all as $num => $c) {\n            if (!is_array($c)) continue;\n            $out[] = [\n                'number'      => (string)$num,\n",
               "        foreach ($all as $num => $c) {\n            if (!is_array($c)) continue;\n            if (waIsGroup($num)) continue;" + C + "\n            $out[] = [\n                'number'      => (string)$num,\n", 'contacts')
    # pengaturan
    s = rep(s, "                $incoming['whatsapp_api']['waha_session'] = preg_replace('/[^A-Za-z0-9_-]/', '', (string)$incoming['whatsapp_api']['waha_session']);\n            }\n",
               "                $incoming['whatsapp_api']['waha_session'] = preg_replace('/[^A-Za-z0-9_-]/', '', (string)$incoming['whatsapp_api']['waha_session']);\n            }\n"
               "            if (isset($incoming['whatsapp_api']['wa_groups'])) $incoming['whatsapp_api']['wa_groups'] = !empty($incoming['whatsapp_api']['wa_groups']);" + C + "\n", 'settings')
    return s

def js(s):
    s = rep(s, "qh + waMediaHtml(media) + waHl164(",
               "((rq && rq.gf) ? '<div style=\"font-size:12px;font-weight:600;color:var(--brand);margin-bottom:2px\">' + esc(rq.gf) + '</div>' : '') /* " + TAG + " */ + qh + waMediaHtml(media) + waHl164(", 'bubble')
    s = rep(s, "{ id: m.wamid, reply_to: m.reply_to, k: 'q' + m.ts + (m.wamid || '') }",
               "{ id: m.wamid, reply_to: m.reply_to, k: 'q' + m.ts + (m.wamid || ''), gf: m.g_from /* " + TAG + " */ }", 'bubble call')
    s = rep(s, "    var _nama = (_konv && _konv.name) || '';\n",
               "    var _nama = (_konv && _konv.name) || '';\n    if (res.group && !_nama) _nama = res.group.name || 'Grup WhatsApp';   // " + TAG + "\n", 'nama')
    s = rep(s, "(_nama ? '+' + esc(res.number) : '')", "(res.group ? ico('users', 12) + ' Grup WhatsApp' : (_nama ? '+' + esc(res.number) : ''))", 'sub', 2)
    s = rep(s, "    var _stageNow = (_konv && _konv.stage) || 'new';\n",
               "    if (res.group) _leadLink = '';   // " + TAG + " — grup bukan lead\n    var _stageNow = (_konv && _konv.stage) || 'new';\n", 'lead')
    s = rep(s, "var _waHtml = _wiH + _moreH163 + (res.messages",
               "var _waHtml = (res.group ? '<div style=\"text-align:center;margin:6px 0 10px\"><span class=\"tag\" style=\"background:#e0f2fe;color:#075985\">' + ico('users', 12) + ' Chat grup — bot tidak membalas di grup, hanya balasan manual</span></div>' : '') /* " + TAG + " */ + _wiH + _moreH163 + (res.messages", 'notice')
    s = rep(s, "      var judul = c.name ? esc(c.name) : ('+' + esc(c.number));\n      var subNomor = '<div class=\"wa-conv-sub\">' + (c.name ? '<span>+' + esc(c.number) + '</span>' : '')",
               "      var judul = c.name ? esc(c.name) : (c.is_group ? 'Grup WhatsApp' : ('+' + esc(c.number)));\n      var subNomor = '<div class=\"wa-conv-sub\">' + (c.is_group ? '<span>' + ico('users', 11) + ' Grup</span>' : (c.name ? '<span>+' + esc(c.number) + '</span>' : ''))   // " + TAG + "\n        ", 'list')
    s = rep(s, "      $('#wa_enabled').checked = wa.enabled === true;\n",
               "      $('#wa_enabled').checked = wa.enabled === true;\n      if ($('#wa_groups')) $('#wa_groups').checked = wa.wa_groups === true;   // " + TAG + "\n", 'load')
    s = rep(s, "      enabled: $('#wa_enabled').checked,\n      media_days:",
               "      enabled: $('#wa_enabled').checked,\n      wa_groups: $('#wa_groups') ? $('#wa_groups').checked : false,   // " + TAG + "\n      media_days:", 'save')
    return s

def html(s):
    a = '          <label class="switch"><input type="checkbox" id="wa_enabled"><span class="sl"></span></label></div>\n'
    return rep(s, a, a +
        '        <div class="toggle-row"><div><div class="tt">Tampilkan Chat Grup</div><div class="td">Pesan di grup WhatsApp ikut masuk Percakapan WA supaya bisa dipantau &amp; dibalas manual oleh agent. Bot <b>tidak pernah</b> membalas di grup. Hanya untuk nomor WAHA.</div><!-- ' + TAG + ' --></div>\n'
        '          <label class="switch"><input type="checkbox" id="wa_groups"><span class="sl"></span></label></div>\n', 'toggle')

patch(API, api); patch(JS, js); patch(HTML, html)
