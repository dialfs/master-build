#!/usr/bin/env python3
"""v1.2.213 (wa-arsip): chat yang diarsipkan di WhatsApp (HP) tidak tampil di daftar chat dashboard — personal & grup.
- Status arsip dibaca dari WAHA (GET /chats, medan archived) bertahap di cron_tick: 100 chat teratas tiap >=60 dtk,
  semua chat (maks 5.000) tiap >=10 menit; plus event chat.archive (engine WEBJS) bila datang.
- Daftar chat (wa_conversations_v2, juga dipakai Inbox Grup) & daftar cadangan: chat arsip tidak masuk daftar maupun hitungan.
  Chip baru "Arsip (N)" untuk melihatnya; chat yang dibuka dari arsip diberi tanda "arsip".
- Dibuka (unarchive) di HP / pesan baru membuka arsip -> tampil lagi pada sinkron berikutnya.
Butuh v1.2.212. Idempoten. Pakai: patch_v12213.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.213: wa-arsip'; NEED = 'v1.2.212: label-ai'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12213-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ---------------- dashboard ----------------
j = open(JS, encoding='utf-8').read()
if TAG not in j:
    j = rep(j, "  // Expose for inline replacement of static markup\n  window._ico = ico;",
               "  if (!ICONS.archive) ICONS.archive = '<rect width=\"20\" height=\"5\" x=\"2\" y=\"3\" rx=\"1\"/><path d=\"M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8\"/><path d=\"M10 12h4\"/>';   // " + TAG + "\n"
               "  // Expose for inline replacement of static markup\n  window._ico = ico;", what='js-ikon')
    j = rep(j, "      '<button class=\"wa-filter-btn\" data-filter=\"takeover_requests\">Take-over Requests <span class=\"wa-filter-count\" data-count=\"takeover_requests\">0</span></button>' +\n",
               "      '<button class=\"wa-filter-btn\" data-filter=\"takeover_requests\">Take-over Requests <span class=\"wa-filter-count\" data-count=\"takeover_requests\">0</span></button>' +\n"
               "      '<button class=\"wa-filter-btn\" data-filter=\"archived\" style=\"display:none\" title=\"Chat yang diarsipkan di WhatsApp — tidak tampil di daftar lain\">' + ico('archive',13) + ' Arsip <span class=\"wa-filter-count\" data-count=\"archived\">0</span></button>' +   // v1.2.213: wa-arsip\n", what='js-chip')
    j = rep(j, "    ['all', 'mine', 'unclaimed', 'others', 'takeover_requests', 'today', 'attention', 'unreplied', 'done', 'full_bot'].forEach(function (f) {",
               "    var _ab213 = $('#waFilterBar .wa-filter-btn[data-filter=\"archived\"]');   // v1.2.213: wa-arsip — chip Arsip hanya tampil bila ada\n"
               "    if (_ab213) _ab213.style.display = ((c.archived || 0) > 0 || waState.filter === 'archived') ? '' : 'none';\n"
               "    ['all', 'mine', 'unclaimed', 'others', 'takeover_requests', 'today', 'attention', 'unreplied', 'done', 'full_bot', 'archived'].forEach(function (f) {", what='js-count')
    j = rep(j, "      if (c.has_history) stageBadge += ",
               "      if (c.archived) stageBadge += ' <span class=\"tag\" style=\"background:#e5e7eb;color:#374151\" title=\"Diarsipkan di WhatsApp\">' + ico('archive', 11) + ' arsip</span>';   // v1.2.213: wa-arsip\n"
               "      if (c.has_history) stageBadge += ", what='js-tag')
    save(JS, j)
h = open(HT, encoding='utf-8').read()
if TAG not in h:
    h = rep(h, '<script src="app.js?v=1.2.212"></script>', '<script src="app.js?v=1.2.213"></script><!-- ' + TAG + ' -->', what='html-ver')
    save(HT, h)

# ---------------- api ----------------
s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API); sys.exit(0)
assert NEED in s, 'butuh v1.2.212 dulu'
s = rep(s, "define('DEI_VERSION', 'v1.2.212');   // v1.2.212:",
        "define('DEI_VERSION', 'v1.2.213');   // " + TAG + " — chat yang diarsipkan di WhatsApp tidak tampil di daftar chat (personal & grup), chip Arsip; v1.2.212:", what='versi')

LIB = r'''
/* v1.2.213: wa-arsip — chat yang diarsipkan di WhatsApp (HP) tidak tampil di daftar chat dashboard (personal & grup).
 * Status arsip dibaca dari WAHA: GET /api/{sesi}/chats (medan archived) bertahap di cron_tick, plus event
 * chat.archive (WEBJS). Berkas data/wa-archived.json:
 *   n = {kunci daftar chat (nomor / id grup): {ch, at}}   c = {ch: {off, ps, top, done, f, err, at}} */
if (!defined('WA_ARC_FILE')) define('WA_ARC_FILE', DATA_DIR . '/wa-archived.json');
if (!defined('WA_ARC_PAGE')) define('WA_ARC_PAGE', 100);
if (!defined('WA_ARC_MAX')) define('WA_ARC_MAX', 5000);   // chat per putaran penuh
function waArcAll() {
    if (!isset($GLOBALS['dei_arc213'])) {
        $a = readJson(WA_ARC_FILE, []);
        $GLOBALS['dei_arc213'] = (is_array($a) && is_array($a['n'] ?? null)) ? $a['n'] : [];
    }
    return $GLOBALS['dei_arc213'];
}
function waArcIs($num) { $k = preg_replace('/\D/', '', (string)$num); return $k !== '' && isset(waArcAll()[$k]); }
// true/false = status arsip; null = engine tidak memberi medan arsip untuk chat ini
function waArcFlag($chat) {
    if (!is_array($chat)) return null;
    $cand = [$chat['archived'] ?? null, $chat['archive'] ?? null, $chat['isArchived'] ?? null,
             is_array($chat['_chat'] ?? null) ? ($chat['_chat']['archived'] ?? null) : null,
             is_array($chat['_data'] ?? null) ? ($chat['_data']['archived'] ?? ($chat['_data']['archive'] ?? null)) : null];
    foreach ($cand as $v) {
        if ($v === null) continue;
        return $v === true || $v === 1 || $v === '1' || $v === 'true';
    }
    return null;
}
function waArcChatId($chat) {
    $id = is_array($chat) ? ($chat['id'] ?? '') : '';
    if (is_array($id)) $id = $id['_serialized'] ?? '';
    return strtolower(trim((string)$id));
}
// Kunci daftar chat dari id chat WAHA. $api=false: @lid hanya dari peta tersimpan (tanpa panggil WAHA).
function waArcKey($wa, $jid, $api) {
    $jid = strtolower(trim((string)$jid));
    if ($jid === '') return '';
    if (preg_match('/@g\.us$/', $jid)) return wgKey($jid);
    if (!wsPersonalChat($jid)) return '';
    $n = wahaJidNum($jid);
    if ($n !== '' || substr($jid, -4) !== '@lid') return $n;
    if ($api) { try { return (string)wahaResolveNum($wa, $jid, []); } catch (\Throwable $e) { return ''; } }
    if (!isset($GLOBALS['dei_arc_lids213'])) { $m = readJson(DATA_DIR . '/waha-lids.json', []); $GLOBALS['dei_arc_lids213'] = is_array($m) ? $m : []; }
    $lid = preg_replace('/\D/', '', substr($jid, 0, -4));
    return (string)($GLOBALS['dei_arc_lids213'][$lid] ?? '');
}
// Terapkan hasil baca: $upd = [kunci => true|false]. $passFrom > 0 = putaran penuh selesai -> buang entri ch ini yang tak terlihat sejak itu.
function waArcApply($ch, $upd, $cx = null, $passFrom = 0, $live = null) {
    deiWithLock('wa-arc', function () use ($ch, $upd, $cx, $passFrom, $live) {
        $a = readJson(WA_ARC_FILE, []); if (!is_array($a)) $a = [];
        $n = is_array($a['n'] ?? null) ? $a['n'] : []; $c = is_array($a['c'] ?? null) ? $a['c'] : [];
        $now = time();
        foreach ($upd as $k => $on) {
            $k = (string)$k; if ($k === '') continue;
            if ($on) $n[$k] = ['ch' => (string)$ch, 'at' => $now];
            elseif (isset($n[$k]) && (string)($n[$k]['ch'] ?? '') === (string)$ch) unset($n[$k]);
        }
        if ($passFrom > 0) foreach ($n as $k => $r) {
            if ((string)($r['ch'] ?? '') === (string)$ch && (int)($r['at'] ?? 0) < $passFrom) unset($n[$k]);
        }
        if (is_array($live)) {   // nomor WAHA yang sudah dilepas -> arsipnya ikut dibuang
            foreach ($n as $k => $r) if (!isset($live[(string)($r['ch'] ?? '')])) unset($n[$k]);
            foreach ($c as $k => $r) if (!isset($live[(string)$k])) unset($c[$k]);
        }
        if (is_array($cx)) $c[(string)$ch] = $cx;
        if (count($n) > 20000) $n = array_slice($n, -20000, null, true);
        writeJson(WA_ARC_FILE, ['n' => $n, 'c' => $c]);
        $GLOBALS['dei_arc213'] = $n;
    });
}
// cron_tick: baca status arsip dari WAHA per nomor WAHA, bertahap sampai $budget detik.
function waArcSync($s, $budget = 6) {
    if (!empty($GLOBALS['dei_dry'])) return [];
    $t0 = microtime(true); $out = []; $now = time();
    $st = readJson(WA_ARC_FILE, []); $cs = (is_array($st) && is_array($st['c'] ?? null)) ? $st['c'] : [];
    $chans = whChannels($s); $live = [];
    foreach ($chans as $cc) $live[(string)$cc[0]] = true;
    if (!$chans) { if (!empty($st['n']) || !empty($cs)) waArcApply('', [], null, 0, []); return []; }
    foreach ($chans as $cc) {
        list($ch, , $conf) = $cc;
        if (microtime(true) - $t0 > $budget) break;
        $x = is_array($cs[$ch] ?? null) ? $cs[$ch] : [];
        $doTop = $now - (int)($x['top'] ?? 0) >= 60;
        $doPass = $now - (int)($x['done'] ?? 0) >= 600;
        if (!$doTop && !$doPass) continue;
        $sp = rawurlencode(wahaSession($conf));
        $upd = []; $lidApi = 0; $err = ''; $saw = false;
        $page = function ($off) use ($conf, $sp, &$upd, &$lidApi, &$err, &$saw) {
            $q = '/api/' . $sp . '/chats?limit=' . WA_ARC_PAGE . '&offset=' . (int)$off;
            list($c, $d) = wahaApi($conf, 'GET', $q . '&sortBy=conversationTimestamp&sortOrder=desc');
            if ($c === 400) list($c, $d) = wahaApi($conf, 'GET', $q);
            if ($c < 200 || $c >= 300 || !is_array($d) || ($d && !isset($d[0]))) { $err = wahaErr($c, $d, 'Daftar chat tidak bisa dibaca dari WAHA.'); return -1; }
            foreach ($d as $chat) {
                $f = waArcFlag($chat);
                if ($f === null) continue;
                $saw = true;
                $jid = waArcChatId($chat);
                $useApi = $f && substr($jid, -4) === '@lid' && $lidApi < 20;
                if ($useApi) $lidApi++;
                $k = waArcKey($conf, $jid, $useApi);
                if ($k !== '') $upd[$k] = $f || !empty($upd[$k]);
            }
            return count($d);
        };
        $passFrom = 0;
        if ($doTop && $page(0) >= 0) $x['top'] = $now;
        if ($doPass && $err === '') {
            $off = (int)($x['off'] ?? 0);
            if ($off <= 0) { $off = 0; $x['ps'] = $now; }
            for ($i = 0; $i < 4 && microtime(true) - $t0 < $budget; $i++) {
                $cnt = $page($off);
                if ($cnt < 0) break;
                $off += WA_ARC_PAGE;
                if ($cnt < WA_ARC_PAGE || $off >= WA_ARC_MAX) { $passFrom = max(1, (int)($x['ps'] ?? $now)); $off = 0; $x['done'] = $now; break; }
            }
            $x['off'] = $off;
        }
        if ($saw) $x['f'] = 1;
        $x['err'] = mb_substr($err, 0, 200); $x['at'] = $now;
        waArcApply($ch, $upd, $x, $passFrom, $live);
        $out[$ch] = ['archived' => count(array_filter($upd)), 'read' => count($upd), 'field' => !empty($x['f'])] + ($err !== '' ? ['err' => $x['err']] : []) + ($passFrom ? ['pass_done' => true] : []);
    }
    return $out;
}
// Event WAHA chat.archive (WEBJS): {id, archived, timestamp}
function waArcEvent($wa, $p) {
    $jid = waArcChatId($p);
    $k = waArcKey($wa, $jid, true);
    if ($k === '') return;
    waArcApply(whCh($wa), [$k => !empty($p['archived'])]);
}

function whChannels($s = null) {'''
s = rep(s, "\nfunction whChannels($s = null) {", LIB, what='pustaka')

# cron_tick
s = rep(s, "        try { $wsr = wsRun($s, PHP_SAPI === 'cli' ? 25 : 15); if ($wsr) $r['wa_history'] = $wsr; } catch (\\Throwable $e) { $r['err_wa_history'] = $e->getMessage(); }   // v1.2.105: riwayat-wa-waha\n",
           "        try { $wsr = wsRun($s, PHP_SAPI === 'cli' ? 25 : 15); if ($wsr) $r['wa_history'] = $wsr; } catch (\\Throwable $e) { $r['err_wa_history'] = $e->getMessage(); }   // v1.2.105: riwayat-wa-waha\n"
           "        try { $arc = waArcSync($s, PHP_SAPI === 'cli' ? 10 : 6); if ($arc) $r['wa_archive'] = $arc; } catch (\\Throwable $e) { $r['err_wa_archive'] = $e->getMessage(); }   // " + TAG + "\n", what='cron')

# webhook WAHA: event chat.archive
s = rep(s, "        if (!in_array((string)($evt['event'] ?? ''), ['message', 'message.any'], true)) { echo 'OK'; exit; }\n\n        if (wgEvtJid($evt) !== '') {",
           "        if ((string)($evt['event'] ?? '') === 'chat.archive') { try { waArcEvent($wa, is_array($evt['payload'] ?? null) ? $evt['payload'] : []); } catch (\\Throwable $e) { error_log('wa-arsip: ' . $e->getMessage()); } echo 'OK'; exit; }   // " + TAG + "\n"
           "        if (!in_array((string)($evt['event'] ?? ''), ['message', 'message.any'], true)) { echo 'OK'; exit; }\n\n        if (wgEvtJid($evt) !== '') {", what='webhook')

# daftar cadangan (wa_conversations)
s = rep(s, "            if (waIsGroup($num) && !wgOn()) continue;   // v1.2.170: grup-wa\n            if (!isset($byNum[$num])) {",
           "            if (waIsGroup($num) && !wgOn()) continue;   // v1.2.170: grup-wa\n            if (waArcIs($num)) continue;   // " + TAG + "\n            if (!isset($byNum[$num])) {", what='legacy')

# wa_conversations_v2 — dikerjakan di dalam blok case saja
a = s.index("    case 'wa_conversations_v2': {"); b = s.index("        jsonOut([\n            'ok' => true,\n            'conversations' => $result,", a)
v = s[a:b]
v = rep(v, "        $allLeads = leadsGetAll();        // v1.2.21: tandai nomor yang sudah punya kartu lead\n",
           "        $allLeads = leadsGetAll();        // v1.2.21: tandai nomor yang sudah punya kartu lead\n"
           "        $arc213 = waArcAll(); $cntArc213 = 0; $fArc213 = ($filter === 'archived');   // " + TAG + "\n", what='v2-init')
v = rep(v, "            if ($chF !== '' && $numCh !== $chF) continue;\n            $visible[$num] = true;\n",
           "            if ($chF !== '' && $numCh !== $chF) continue;\n"
           "            $isArc213 = isset($arc213[$num]);   // v1.2.213: wa-arsip — chat arsip tidak masuk daftar & hitungan (kecuali chip Arsip)\n"
           "            if ($isArc213) { $cntArc213++; if (!$fArc213) continue; }\n"
           "            if (!$isArc213) $visible[$num] = true;\n", what='v2-skip')
v = rep(v, "            $cntFlag[$fl['flag']]++;\n            if ($fl['full_bot']) $cntFlag['full_bot']++;\n",
           "            if (!$isArc213) { $cntFlag[$fl['flag']]++; if ($fl['full_bot']) $cntFlag['full_bot']++; }   // v1.2.213\n", what='v2-flag')
v = rep(v, "            if ($isToday) $cntToday++;\n            if ($needsAttention) $cntAttention++;\n",
           "            if ($isToday && !$isArc213) $cntToday++;   // v1.2.213\n            if ($needsAttention && !$isArc213) $cntAttention++;\n", what='v2-today')
v = rep(v, "                'tp' => $tpOn ? tpPublic($allContacts[$num] ?? null) : null,   // v1.2.138: filter-topik\n            ];\n",
           "                'tp' => $tpOn ? tpPublic($allContacts[$num] ?? null) : null,   // v1.2.138: filter-topik\n                'archived' => $isArc213,   // v1.2.213: wa-arsip\n            ];\n", what='v2-item')
v = rep(v, "            if ($show) {   // v1.2.117:",
           "            if ($fArc213) $show = $isArc213;   // v1.2.213: chip Arsip = hanya chat arsip\n            if ($show) {   // v1.2.117:", what='v2-show')
v = rep(v, "'unreplied' => $cntFlag['unreplied'], 'done' => $cntFlag['done'], 'full_bot' => $cntFlag['full_bot']];  // v1.2.17 + v1.2.58",
           "'unreplied' => $cntFlag['unreplied'], 'done' => $cntFlag['done'], 'full_bot' => $cntFlag['full_bot'], 'archived' => $cntArc213];  // v1.2.17 + v1.2.58; v1.2.213: wa-arsip", what='v2-counts')
s = s[:a] + v + s[b:]
save(API, s)
