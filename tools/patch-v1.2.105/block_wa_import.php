/* ============================================================================
 * v1.2.105: riwayat-wa-waha — riwayat chat sebelum nomor terhubung ke dashboard
 *
 * Seperti membuka WhatsApp Web: saat nomor di-scan (ditautkan sebagai perangkat), HP
 * mengirim riwayat chat ke WAHA (engine NOWEB dengan store aktif / GOWS / WEBJS).
 * Riwayat itu ditarik lewat API WAHA (/chats, /chats/{id}/messages) secara bertahap
 * oleh cron_tick (dan oleh panel Koneksi selagi terbuka), lalu disimpan TERPISAH dari
 * log live: data/wa-import/<nomor>.json + _index.json. Tidak terpangkas log_limit,
 * tidak masuk laporan/kuota/percakapan (conv), tidak membuka jendela 24 jam.
 * Batas waktu per nomor pelanggan = sebelum pesan live pertamanya di log (tidak dobel).
 * Job per nomor bisnis (ch): data/wa-import/_sync-<ch>.json.
 * Meta Cloud API tidak menyediakan riwayat -> hanya penyedia WAHA.
 * ========================================================================= */
if (!defined('WA_IMPORT_DIR')) define('WA_IMPORT_DIR', DATA_DIR . '/wa-import');
if (!defined('WA_IMPORT_MAX_MSGS')) define('WA_IMPORT_MAX_MSGS', 20000);   // per nomor pelanggan
if (!defined('WS_MAX_CHATS')) define('WS_MAX_CHATS', 1000);                // chat pribadi per tarikan
if (!defined('WS_MAX_PER_CHAT')) define('WS_MAX_PER_CHAT', 1000);          // pesan per chat per tarikan
if (!defined('WS_PAGE')) define('WS_PAGE', 100);

function wiFile($num) { return WA_IMPORT_DIR . '/' . preg_replace('/\D/', '', (string)$num) . '.json'; }
function wiIndexFile() { return WA_IMPORT_DIR . '/_index.json'; }
function wiIndexAll() {
    if (!is_file(wiIndexFile())) return [];
    $x = readJson(wiIndexFile(), []);
    return is_array($x) ? $x : [];
}
function wiLoad($num) {
    $f = wiFile($num);
    if (!is_file($f)) return null;
    $d = readJson($f, null);
    return (is_array($d) && is_array($d['msgs'] ?? null)) ? $d : null;
}
function wiKey($m) { return (string)($m['id'] ?? '') !== '' ? 'i:' . $m['id'] : 'h:' . md5($m['ts'] . '|' . $m['d'] . '|' . $m['t']); }
// Gabungkan pesan ke riwayat satu nomor (buang duplikat). [ditambah, total]
function wiSave($num, $msgs, $meta) {
    return deiWithLock('wa-import', function () use ($num, $msgs, $meta) {
        if (!is_dir(WA_IMPORT_DIR)) @mkdir(WA_IMPORT_DIR, 0755, true);
        $cur = wiLoad($num) ?: ['num' => $num, 'msgs' => []];
        $seen = [];
        foreach ($cur['msgs'] as $m) $seen[wiKey($m)] = true;
        $add = 0;
        foreach ($msgs as $m) {
            $k = wiKey($m);
            if (isset($seen[$k])) continue;
            $seen[$k] = true; $cur['msgs'][] = $m; $add++;
        }
        if ($add === 0 && is_file(wiFile($num))) return [0, count($cur['msgs'])];
        $i = 0; foreach ($cur['msgs'] as &$m) $m['_i'] = $i++; unset($m);
        usort($cur['msgs'], function ($a, $b) { return strcmp($a['ts'], $b['ts']) ?: ($a['_i'] <=> $b['_i']); });
        foreach ($cur['msgs'] as &$m) unset($m['_i']); unset($m);
        if (count($cur['msgs']) > WA_IMPORT_MAX_MSGS) $cur['msgs'] = array_slice($cur['msgs'], -WA_IMPORT_MAX_MSGS);
        $cur['at'] = $meta['at'] ?? date('Y-m-d H:i:s');
        $cur['ch'] = (string)($meta['ch'] ?? ($cur['ch'] ?? ''));
        writeJson(wiFile($num), $cur);
        $n = count($cur['msgs']);
        $ix = wiIndexAll();
        if ($n > 0) {
            $last = $cur['msgs'][$n - 1];
            $ix[$num] = ['count' => $n, 'first_ts' => $cur['msgs'][0]['ts'], 'last_ts' => $last['ts'],
                         'last_t' => mb_substr($last['t'], 0, 200), 'last_d' => $last['d'], 'at' => $cur['at'], 'ch' => $cur['ch']];
        }
        writeJson(wiIndexFile(), $ix);
        return [$add, $n];
    });
}
// Untuk wa_thread: riwayat terakhir (lama -> baru).
function wiThreadPublic($num, $all = false) {
    $d = wiLoad($num);
    if (!$d || !$d['msgs']) return null;
    $n = count($d['msgs']);
    $out = [];
    foreach (array_slice($d['msgs'], -($all ? 5000 : 300)) as $m) $out[] = ['ts' => $m['ts'], 'd' => $m['d'], 't' => $m['t']];
    return ['total' => $n, 'msgs' => $out, 'first_ts' => $d['msgs'][0]['ts'], 'last_ts' => $d['msgs'][$n - 1]['ts'], 'at' => (string)($d['at'] ?? '')];
}
// Untuk analisa lead bila log kosong (chat hanya ada di riwayat).
function wiTranscript($num, $max = 40) {
    $d = wiLoad($num);
    if (!$d || !$d['msgs']) return '';
    $out = '';
    foreach (array_slice($d['msgs'], -$max) as $m) $out .= ($m['d'] === 'in' ? 'Customer: ' : 'CS: ') . $m['t'] . "\n";
    return trim($out);
}

/* ---------- job tarik riwayat per nomor bisnis ---------- */
function wsFile($ch) { return WA_IMPORT_DIR . '/_sync-' . preg_replace('/[^A-Za-z0-9_]/', '', (string)$ch) . '.json'; }
function wsGet($ch) { $f = wsFile($ch); if (!is_file($f)) return null; $j = readJson($f, null); return is_array($j) ? $j : null; }
function wsPut($ch, $j) { if (!is_dir(WA_IMPORT_DIR)) @mkdir(WA_IMPORT_DIR, 0755, true); $j['upd'] = time(); writeJson(wsFile($ch), $j); }
// Jadwalkan tarikan. $reason 'scan' (baru ditautkan: 3 putaran, riwayat dari HP datang bertahap) | 'manual'.
function wsSchedule($wa, $reason, $by = '') {
    if (!whOn($wa)) return null;
    $ch = whCh($wa);
    return deiWithLock('wa-sync-' . $ch, function () use ($ch, $reason, $by) {
        $j = wsGet($ch);
        $now = time();
        if ($j && in_array(($j['st'] ?? ''), ['pending', 'running'], true) && $now - (int)($j['created'] ?? 0) < 1800) return $j;
        if ($j && $reason === 'scan' && $now - (int)($j['created'] ?? 0) < 600) return $j;   // webhook + panel = satu jadwal
        $j = ['ch' => $ch, 'st' => 'pending', 'reason' => $reason, 'by' => $by, 'created' => $now,
              'cutoff' => $now, 'due' => $now + ($reason === 'scan' ? 60 : 0),
              'pass' => 1, 'passes' => $reason === 'scan' ? 3 : 1,
              'phase' => 'chats', 'coff' => 0, 'chats' => [], 'ci' => 0, 'moff' => 0,
              'n_chats' => 0, 'n_msgs' => 0, 'n_new' => 0, 'n_nums' => 0, 'err' => '', 'tot' => ['msgs' => 0, 'new' => 0]];
        wsPut($ch, $j);
        return $j;
    });
}
// Pesan live pertama per nomor pelanggan (batas atas riwayat supaya tidak dobel dengan log).
function wsFirstLiveMap() {
    $out = [];
    if (deiStorageMysql()) {
        foreach (deiDb()->query("SELECT num, MIN(ts) AS t FROM dei_log WHERE channel = 'whatsapp' AND num <> '' GROUP BY num")->fetchAll() as $r) {
            $t = strtotime((string)$r['t']); if ($t) $out[(string)$r['num']] = $t;
        }
        return $out;
    }
    foreach (logReadAll() as $e) {
        if (($e['channel'] ?? '') !== 'whatsapp') continue;
        $n = waNormNum($e['ip'] ?? ''); $t = strtotime((string)($e['ts'] ?? ''));
        if ($n !== '' && $t && (!isset($out[$n]) || $t < $out[$n])) $out[$n] = $t;
    }
    return $out;
}
// Satu pesan WAHA -> bentuk riwayat. null = lewati (sistem, reaksi, protokol, di luar batas).
function wsMsg($m, $lte) {
    if (!is_array($m)) return null;
    $ts = (int)($m['timestamp'] ?? 0);
    if ($ts > 100000000000) $ts = (int)floor($ts / 1000);
    if ($ts <= 0 || $ts > $lte) return null;
    $body = trim((string)($m['body'] ?? ''));
    $t = $body;
    if (!empty($m['hasMedia'])) {
        $mt = strtolower((string)($m['media']['mimetype'] ?? ''));
        $lbl = strpos($mt, 'image/webp') === 0 ? '[Stiker]' : (strpos($mt, 'image/') === 0 ? '[Gambar]' : (strpos($mt, 'video/') === 0 ? '[Video]'
             : (strpos($mt, 'audio/') === 0 ? '[Pesan suara]' : ($mt !== '' ? '[Dokumen]' : '[Media]'))));
        $t = $lbl . ($body !== '' ? "\n" . $body : '');
    }
    if ($t === '') return null;
    return ['ts' => date('Y-m-d H:i:s', $ts), 'd' => !empty($m['fromMe']) ? 'out' : 'in', 't' => mb_substr($t, 0, 4000), 'id' => mb_substr(wahaMsgId($m), 0, 120)];
}
function wsPersonalChat($id) {
    $id = strtolower(trim((string)$id));
    if ($id === '' || strpos($id, '@') === false) return false;
    if (preg_match('/@(g\.us|newsletter|broadcast)$/', $id) || strpos($id, 'status@') === 0) return false;
    return (bool)preg_match('/@(c\.us|s\.whatsapp\.net|lid)$/', $id);
}
/* Kerjakan job yang jatuh tempo, sampai $budget detik. $only = satu ch saja (panel).
 * Mengembalikan ringkasan [ch => status] untuk yang dikerjakan, atau [] bila tak ada. */
function wsRun($s, $budget = 20, $only = '') {
    if (!is_dir(WA_IMPORT_DIR)) return [];
    $lk = @fopen(WA_IMPORT_DIR . '/.sync.lock', 'c');
    if (!$lk || !@flock($lk, LOCK_EX | LOCK_NB)) { if ($lk) @fclose($lk); return ['busy' => true]; }
    $t0 = microtime(true); $out = []; $live = null;
    try {
        foreach (whChannels($s) as $cx) {
            list($ch, $label, $wa) = $cx;
            if ($only !== '' && $ch !== $only) continue;
            $j = wsGet($ch);
            if (!$j) continue;
            $now = time();
            if (($j['st'] ?? '') === 'done' && (int)$j['pass'] < (int)$j['passes'] && (int)($j['due'] ?? 0) <= $now) {
                $j['pass']++; $j['st'] = 'running'; $j['phase'] = 'chats'; $j['coff'] = 0; $j['chats'] = []; $j['ci'] = 0; $j['moff'] = 0;
                $j['n_chats'] = 0; $j['n_msgs'] = 0; $j['n_new'] = 0; $j['n_nums'] = 0;
            }
            if (($j['st'] ?? '') === 'pending' && (int)($j['due'] ?? 0) <= $now) { $j['st'] = 'running'; $j['started'] = $now; }
            if (($j['st'] ?? '') !== 'running') continue;
            if ($live === null) $live = wsFirstLiveMap();
            $sp = rawurlencode(wahaSession($wa));
            $me = waNormNum($wa['waha_number'] ?? '');
            $fails = 0;
            while (microtime(true) - $t0 < $budget && $j['st'] === 'running') {
                if ($j['phase'] === 'chats') {
                    list($c, $d) = wahaApi($wa, 'GET', '/api/' . $sp . '/chats?limit=' . WS_PAGE . '&offset=' . (int)$j['coff'] . '&sortBy=conversationTimestamp&sortOrder=desc');
                    if ($c === 400 && (int)$j['coff'] === 0) list($c, $d) = wahaApi($wa, 'GET', '/api/' . $sp . '/chats?limit=' . WS_PAGE . '&offset=0');
                    if ($c < 200 || $c >= 300 || !is_array($d) || ($d && !isset($d[0]))) {
                        $j['cfail'] = (int)($j['cfail'] ?? 0) + 1;   // lintas tick: 5x gagal = berhenti
                        if ($j['cfail'] >= 5 || in_array($c, [400, 401, 404, 422, 501], true)) {
                            $j['st'] = 'error'; $j['err'] = wahaErr($c, $d, 'Daftar chat tidak bisa dibaca dari WAHA.');
                        }
                        break;
                    }
                    $j['cfail'] = 0;
                    foreach ($d as $chat) {
                        $cid = is_array($chat['id'] ?? null) ? (string)($chat['id']['_serialized'] ?? '') : (string)($chat['id'] ?? '');
                        if (!wsPersonalChat($cid) || count($j['chats']) >= WS_MAX_CHATS) continue;
                        $j['chats'][] = ['id' => $cid, 'name' => mb_substr(trim((string)($chat['name'] ?? '')), 0, 100)];
                    }
                    $j['coff'] += WS_PAGE;
                    if (count($d) < WS_PAGE || count($j['chats']) >= WS_MAX_CHATS || $j['coff'] >= WS_MAX_CHATS * 5) {
                        $j['phase'] = 'msgs'; $j['n_chats'] = count($j['chats']);
                    }
                    continue;
                }
                // phase msgs
                if ((int)$j['ci'] >= count($j['chats'])) {
                    $j['tot']['msgs'] += $j['n_msgs']; $j['tot']['new'] += $j['n_new'];
                    $j['chats'] = []; $j['finished'] = time();
                    $j['st'] = 'done';
                    if ((int)$j['pass'] < (int)$j['passes']) $j['due'] = time() + ((int)$j['pass'] === 1 ? 900 : 2700);
                    break;
                }
                $cur = &$j['chats'][$j['ci']];
                if (!isset($cur['num'])) {
                    $cur['num'] = wahaResolveNum($wa, $cur['id'], []);
                    if ($cur['num'] !== '' && $me !== '' && $cur['num'] === $me) $cur['num'] = '';
                }
                $num = (string)$cur['num'];
                if ($num === '') { unset($cur); $j['ci']++; $j['moff'] = 0; continue; }
                $lte = (int)$j['cutoff'];
                if (isset($live[$num]) && $live[$num] - 1 < $lte) $lte = $live[$num] - 1;
                list($c, $d) = wahaApi($wa, 'GET', '/api/' . $sp . '/chats/' . rawurlencode($cur['id']) . '/messages?limit=' . WS_PAGE
                    . '&offset=' . (int)$j['moff'] . '&downloadMedia=false&filter.timestamp.lte=' . $lte);
                if ($c < 200 || $c >= 300 || !is_array($d) || ($d && !isset($d[0]))) {
                    // chat ini dilewati; 3 gagal beruntun = WAHA bermasalah -> berhenti dengan pesan
                    $j['n_skip'] = (int)($j['n_skip'] ?? 0) + 1; $j['ci']++; $j['moff'] = 0; unset($cur);
                    if (++$fails >= 3) { $j['st'] = 'error'; $j['err'] = wahaErr($c, $d, 'Pesan tidak bisa dibaca dari WAHA.'); }
                    continue;
                }
                $fails = 0;
                if ((string)($cur['name'] ?? '') === '') {   // NOWEB: daftar chat tanpa nama -> pushName pesan masuk
                    foreach ($d as $m) {
                        if (!is_array($m) || !empty($m['fromMe'])) continue;
                        $pn = trim((string)($m['_data']['pushName'] ?? ($m['_data']['notifyName'] ?? ($m['_data']['Info']['PushName'] ?? ''))));
                        if ($pn !== '') { $cur['name'] = mb_substr($pn, 0, 100); break; }
                    }
                }
                $batch = [];
                foreach ($d as $m) { $x = wsMsg($m, $lte); if ($x) $batch[] = $x; }
                if ($batch) {
                    list($add) = wiSave($num, $batch, ['ch' => $ch, 'at' => date('Y-m-d H:i:s')]);
                    $j['n_msgs'] += count($batch); $j['n_new'] += $add;
                    if (empty($cur['saved'])) {
                        $cur['saved'] = 1; $j['n_nums']++;
                        $first = $batch[0]['ts']; $lastTs = $batch[0]['ts'];
                        foreach ($batch as $b) { if (strcmp($b['ts'], $first) < 0) $first = $b['ts']; if (strcmp($b['ts'], $lastTs) > 0) $lastTs = $b['ts']; }
                        $nm = $cur['name']; $multi = ($ch !== 'utama');
                        if (preg_match('/^\+?[\d\s\-().]+$/', $nm)) $nm = '';
                        waContactUpdate($num, function (&$ct, $isNew) use ($nm, $first, $lastTs, $ch, $multi) {
                            if ($nm !== '' && trim((string)($ct['name_wa'] ?? '')) === '') $ct['name_wa'] = $nm;
                            if ($isNew || strcmp($first, (string)($ct['first_seen'] ?? '9999')) < 0) $ct['first_seen'] = $first;
                            if ($isNew) $ct['last_seen'] = $lastTs;
                            if ($multi && empty($ct['wa_ch'])) $ct['wa_ch'] = $ch;
                            $ct['hist'] = 1;
                        });
                    }
                }
                if (count($d) < WS_PAGE || (int)$j['moff'] + WS_PAGE >= WS_MAX_PER_CHAT) { $j['ci']++; $j['moff'] = 0; }
                else $j['moff'] += WS_PAGE;
                unset($cur);
                wsPut($ch, $j);   // progres tersimpan tiap halaman (bisa dilanjut tick berikutnya)
            }
            wsPut($ch, $j);
            $out[$ch] = wsPublic($j);
            if ($j['st'] === 'done' && (int)$j['pass'] === 1 && $j['reason'] === 'scan') {
                try { waAuditLog('history_sync', 'system', '', ['ch' => $ch, 'msgs' => $j['tot']['new']]); } catch (\Throwable $e) {}
            }
            if (microtime(true) - $t0 >= $budget) break;
        }
    } finally {
        @flock($lk, LOCK_UN); @fclose($lk);
    }
    return $out;
}
// Status untuk dashboard (tanpa daftar chat).
function wsPublic($j) {
    if (!$j) return null;
    $tot = count($j['chats'] ?? []) ?: (int)($j['n_chats'] ?? 0);
    $pct = 0;
    if (($j['st'] ?? '') === 'running') $pct = ($j['phase'] ?? '') === 'chats' ? 2 : max(3, min(99, (int)round(100 * (int)$j['ci'] / max(1, $tot))));
    elseif (($j['st'] ?? '') === 'done') $pct = 100;
    return ['st' => (string)($j['st'] ?? ''), 'reason' => (string)($j['reason'] ?? ''), 'pass' => (int)($j['pass'] ?? 1), 'passes' => (int)($j['passes'] ?? 1),
            'phase' => (string)($j['phase'] ?? ''), 'pct' => $pct, 'chats' => $tot, 'done_chats' => (int)($j['ci'] ?? 0),
            'msgs' => (int)($j['tot']['new'] ?? 0) + (($j['st'] ?? '') === 'running' ? (int)($j['n_new'] ?? 0) : 0),
            'nums' => (int)($j['n_nums'] ?? 0), 'err' => (string)($j['err'] ?? ''),
            'created' => (int)($j['created'] ?? 0), 'finished' => (int)($j['finished'] ?? 0), 'due' => (int)($j['due'] ?? 0)];
}

