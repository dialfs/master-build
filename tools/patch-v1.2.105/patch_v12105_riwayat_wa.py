#!/usr/bin/env python3
"""v1.2.105: riwayat-wa-waha — riwayat chat sebelum nomor terhubung ikut tampil di Percakapan WA,
seperti membuka WhatsApp Web. Saat nomor WAHA di-scan, HP mengirim riwayat ke WAHA; tenant menariknya
bertahap (cron_tick + panel Koneksi) lewat /api/{sesi}/chats & /chats/{id}/messages, disimpan terpisah dari log
(data/wa-import/<nomor>.json). Daftar & thread Percakapan WA menampilkannya; kontak dibuat; analisa lead bisa memakainya.
Hanya tenant. Idempoten. Pakai: patch_v12105_riwayat_wa.py <Herd>   (blok dibaca dari folder skrip ini)"""
import sys, os, time, shutil
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd'); T = H + '/dei-tenant'
D = os.path.dirname(os.path.abspath(__file__))
TAG = 'v1.2.105: riwayat-wa-waha'
st = time.strftime('%Y%m%d-%H%M%S')
blk = lambda f: open(os.path.join(D, f), encoding='utf-8').read()

def patch(path, pairs):
    s = open(path, encoding='utf-8').read()
    if TAG in s: print('sudah:', path); return
    shutil.copy2(path, path + '.bak-v12105-' + st)
    for old, new in pairs:
        c = s.count(old); assert c == 1, (path, c, old[:100])
        s = s.replace(old, new)
    assert TAG in s, ('tag tidak masuk', path)
    open(path, 'w', encoding='utf-8').write(s); print('patched:', path)

# ---------------- api/index.php ----------------
patch(T + '/api/index.php', [
 ("define('DEI_VERSION', 'v1.2.104');", "define('DEI_VERSION', 'v1.2.105');"),
 ("function leadBuildTranscript($number, $logs = null, $max = 40) {",
  blk('block_wa_import.php') + "function leadBuildTranscript($number, $logs = null, $max = 40) {"),
 ("""        if ($a !== '') $out .= "CS: " . $a . "\\n";
    }
    return trim($out);
}""",
  """        if ($a !== '') $out .= "CS: " . $a . "\\n";
    }
    if (trim($out) === '') { try { return wiTranscript($number, $max); } catch (\\Throwable $e) {} }   // v1.2.105: riwayat-wa-waha
    return trim($out);
}"""),
 # pemicu: nomor baru ditautkan (QR muncul <= 1 jam lalu, lalu WORKING)
 ("    $flagOut = '';", "    $flagOut = ''; $pairedOut = false;   // v1.2.105"),
 ("    whUpdate($ch, function (&$d) use ($st, $me, $known, &$flagOut) {",
  "    whUpdate($ch, function (&$d) use ($st, $me, $known, &$flagOut, &$pairedOut) {"),
 ("        if ($prev === $st) return $dirty ? null : false;",
  "        if ($st === 'WORKING' && $prev !== 'WORKING' && (int)($d['qr_at'] ?? 0) > $now - 3600) $pairedOut = true;   // v1.2.105: baru ditautkan\n"
  "        if ($prev === $st) return $dirty ? null : false;"),
 ("    if ($flagOut === 'logout') whAlert($wa, $ch, 'logout', null);",
  "    if ($flagOut === 'logout') whAlert($wa, $ch, 'logout', null);\n"
  "    if ($pairedOut) { try { wsSchedule($wa, 'scan', 'system'); } catch (\\Throwable $e) { error_log('wsSchedule: ' . $e->getMessage()); } }   // v1.2.105: riwayat-wa-waha"),
 # cron
 ("        try { $whc = whEnsureCfgCron($s);",
  "        try { $wsr = wsRun($s, PHP_SAPI === 'cli' ? 25 : 15); if ($wsr) $r['wa_history'] = $wsr; } catch (\\Throwable $e) { $r['err_wa_history'] = $e->getMessage(); }   // v1.2.105: riwayat-wa-waha\n"
  "        try { $whc = whEnsureCfgCron($s);"),
 # panel koneksi WAHA: status / mulai / lanjutkan tarikan
 ("""        $n  = wahaSession($wa);
        $sp = rawurlencode($n);

        if ($op === 'status') {""",
  """        $n  = wahaSession($wa);
        $sp = rawurlencode($n);

        if ($op === 'history') {   // v1.2.105: riwayat-wa-waha
            $do = (string)($in['do'] ?? 'get');
            if ($do === 'start') {
                wsSchedule($wa, (($in['reason'] ?? '') === 'scan') ? 'scan' : 'manual', $u['username']);
                if (($in['reason'] ?? '') !== 'scan') { try { waAuditLog('history_pull', $u['username'], '', ['ch' => whCh($wa)]); } catch (\\Throwable $e) {} }
            }
            if ($do === 'run' || $do === 'start') { @set_time_limit(40); try { wsRun($s, 8, whCh($wa)); } catch (\\Throwable $e) { error_log('wsRun: ' . $e->getMessage()); } }
            $chk = whCh($wa); $cn = 0; $cm = 0;
            foreach (wiIndexAll() as $ir) { if ((string)($ir['ch'] ?? '') === $chk) { $cn++; $cm += (int)($ir['count'] ?? 0); } }
            jsonOut(['ok' => true, 'history' => wsPublic(wsGet($chk)), 'stored' => ['nums' => $cn, 'msgs' => $cm]]);
        }

        if ($op === 'status') {"""),
 # thread
 ("            'conv' => (function () use ($num) { try { return convPublic(convStoreGet($num));",
  "            'history' => (function () use ($num) { try { return wiThreadPublic($num, !empty($_GET['imp_all'])); } catch (\\Throwable $e) { return null; } })(),   // v1.2.105: riwayat-wa-waha\n"
  "            'conv' => (function () use ($num) { try { return convPublic(convStoreGet($num));"),
 # daftar percakapan: nomor yang hanya punya riwayat
 ("""            if (($e['dir'] ?? '') === 'manual') $numbers[$num]['has_manual'] = true;
        }
""",
  """            if (($e['dir'] ?? '') === 'manual') $numbers[$num]['has_manual'] = true;
        }
        // v1.2.105: riwayat-wa-waha — nomor yang hanya punya riwayat sebelum terhubung ikut tampil (status Selesai)
        $wiIx = []; try { $wiIx = wiIndexAll(); } catch (\\Throwable $e) {}
        foreach ($wiIx as $wiNum => $wiR) {
            $wiNum = (string)$wiNum;
            if (isset($numbers[$wiNum]) || !is_array($wiR)) continue;
            $wiIn = (($wiR['last_d'] ?? '') === 'in');
            $numbers[$wiNum] = ['last_ts' => (string)($wiR['last_ts'] ?? ''), 'last_q' => $wiIn ? (string)($wiR['last_t'] ?? '') : '',
                                'last_a' => $wiIn ? '' : (string)($wiR['last_t'] ?? ''), 'count' => (int)($wiR['count'] ?? 0),
                                'awaiting' => false, 'last_dir' => 'history', 'bot_failed' => false, 'has_manual' => true, 'history_only' => true];
        }
"""),
 ("            if ($isManual) $fl['full_bot'] = false;   // tidak ada bot di mode Manual",
  "            if ($isManual) $fl['full_bot'] = false;   // tidak ada bot di mode Manual\n"
  "            if (!empty($meta['history_only'])) $fl = ['flag' => 'done', 'flag_note' => 'Riwayat sebelum terhubung', 'waiting_sec' => 0, 'last_from' => $fl['last_from'], 'full_bot' => false];   // v1.2.105"),
 ("            $isToday = (substr((string)$meta['last_ts'], 0, 10) === $todayStr);",
  "            $isToday = (substr((string)$meta['last_ts'], 0, 10) === $todayStr) && empty($meta['history_only']);   // v1.2.105"),
 ("                'ch' => $numCh, 'ch_label' => $numCh !== '' ? $chMap[$numCh] : '',   // v1.2.98: multi-nomor",
  "                'ch' => $numCh, 'ch_label' => $numCh !== '' ? $chMap[$numCh] : '',   // v1.2.98: multi-nomor\n"
  "                'has_history' => isset($wiIx[$num]), 'history_only' => !empty($meta['history_only']),   // v1.2.105: riwayat-wa-waha"),
])

# ---------------- dashboard app.js ----------------
patch(T + '/dashboard/chatbot-ai/app.js', [
 ("  function exportWaContacts() {", blk('block_wa_import.js').replace('/* v1.2.105: riwayat-wa-waha', '/* ' + TAG, 1) + "  function exportWaContacts() {"),
 ("    api('wa_thread', { query: '&number=' + encodeURIComponent(num) })",
  "    api('wa_thread', { query: '&number=' + encodeURIComponent(num) + ((waState.wiAll && waState.wiAll[num]) ? '&imp_all=1' : '') /* v1.2.105 */ })"),
 ("    $('#waThreadBody').innerHTML = (res.messages || []).map(function (m) {",
  "    var _wiH = wiThreadHtml(res);   // v1.2.105: riwayat sebelum terhubung di atas pesan live\n"
  "    $('#waThreadBody').innerHTML = _wiH + (res.messages || []).map(function (m) {"),
 ("    $('#waReplyBar').style.display = 'block';",
  "    wiThreadBind(res);   // v1.2.105\n    $('#waReplyBar').style.display = 'block';"),
 ("      if (c.ch_label && (waState.channels || []).length > 1) stageBadge +=",
  "      if (c.has_history) stageBadge += ' <span class=\"tag\" style=\"background:#fef3c7;color:#92400e\" title=\"Ada riwayat chat dari sebelum terhubung ke dashboard\">' + ico('clock-3', 11) + ' riwayat</span>';   // v1.2.105\n"
  "      if (c.ch_label && (waState.channels || []).length > 1) stageBadge +="),
 # panel Koneksi WhatsApp
 ("    if (st.error) { p.className = 'pill off'; p.textContent = 'Status tidak diketahui'; inf.textContent = st.error; return; }",
  "    if (st.error) { p.className = 'pill off'; p.textContent = 'Status tidak diketahui'; inf.textContent = st.error; wsShow(false); return; }"),
 ("    if (st.connected) $('#fonc_numrow').classList.add('hide');",
  "    if (st.connected) $('#fonc_numrow').classList.add('hide');\n    wsShow(!!st.connected);   // v1.2.105: riwayat-wa-waha"),
 ("      if (r.connected && wasPolling) { foncStop(); toast('WhatsApp tersambung.'); }",
  "      if (r.connected && wasPolling) { foncStop(); toast('WhatsApp tersambung.'); if (_fonc.action === 'waha_conn') wsStartScan(); }   // v1.2.105"),
])

# ---------------- dashboard index.html ----------------
patch(T + '/dashboard/chatbot-ai/index.html', [
 ('        <div class="help" style="margin-top:8px">Jalur tidak resmi (WhatsApp Web)',
  '        <div id="fonc_hist" class="hide" style="border:1px solid var(--line,#e6e6ef);border-radius:10px;padding:10px 12px;margin-top:10px"></div><!-- v1.2.105: riwayat-wa-waha -->\n'
  '        <div class="help" style="margin-top:8px">Jalur tidak resmi (WhatsApp Web)'),
 ('<script src="app.js?v=1.2.104"></script><!-- v1.2.104: skor-risiko-wa -->', '<script src="app.js?v=1.2.105"></script><!-- v1.2.105: riwayat-wa-waha -->'),
])
