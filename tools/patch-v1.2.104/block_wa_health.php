/* v1.2.104: skor-risiko-wa — pemantauan kesehatan nomor WhatsApp (WAHA).
 * WhatsApp tidak memberi skor risiko untuk WhatsApp Web; skor ini HEURISTIK dari perilaku nomor:
 * chat duluan ke nomor baru, balasan atas chat duluan, volume, teks kembar, centang (message.ack),
 * gagal kirim, sesi putus/logout paksa (session.status), umur nomor.
 * Data mentah per nomor: data/wa-health/<ch>.json (ember per jam WIB, simpan 14 hari).
 * Skor: data/wa-health/score.json — dihitung cron_tick tiap 15 menit (atau saat panel dibuka).
 * Ambang & bobot = tebakan awal; setel ulang setelah ada data nomor sungguhan. */
if (!defined('WA_HEALTH_DIR')) define('WA_HEALTH_DIR', DATA_DIR . '/wa-health');
if (!defined('WA_HEALTH_CFG_V')) define('WA_HEALTH_CFG_V', 2);   // 2 = webhook berlangganan message.ack
function whOn($wa) { return (string)($wa['provider'] ?? 'meta') === 'waha'; }
function whCh($wa) { $c = preg_replace('/[^A-Za-z0-9_]/', '', (string)($wa['_ch'] ?? '')); return $c !== '' ? $c : 'utama'; }
function whFile($ch) { return WA_HEALTH_DIR . '/' . preg_replace('/[^A-Za-z0-9_]/', '', (string)$ch) . '.json'; }
function whBlank() { return ['v' => 1, 'h' => [], 'li' => [], 'init' => [], 'dup' => [], 'm' => [], 'ev' => [], 'mk' => []]; }
function whRead($ch) {
    $d = readJson(whFile($ch), null);
    if (!is_array($d)) return whBlank();
    foreach (whBlank() as $k => $v) { if (!isset($d[$k]) || !is_array($d[$k]) && is_array($v)) $d[$k] = $v; }
    return $d;
}
// $fn(&$d) mengubah data; kembalikan false untuk batal menulis.
function whUpdate($ch, $fn) {
    try {
        if (!is_dir(WA_HEALTH_DIR)) @mkdir(WA_HEALTH_DIR, 0755, true);
        deiWithLock('wa-health-' . $ch, function () use ($ch, $fn) {
            $d = whRead($ch);
            if ($fn($d) === false) return;
            whPrune($d);
            writeJson(whFile($ch), $d);
        });
    } catch (\Throwable $e) { error_log('wa-health: ' . $e->getMessage()); }
}
function whPrune(&$d) {
    $now = time();
    if ((int)($d['pr'] ?? 0) > $now - 600) return;   // rapikan maks 10 menit sekali
    $d['pr'] = $now;
    $hk = gmdate('YmdH', $now + 7 * 3600 - 14 * 86400);
    foreach (array_keys($d['h']) as $k) if ((string)$k < $hk) unset($d['h'][$k]);
    foreach ($d['li'] as $n => $t) if ((int)$t < $now - 7 * 86400) unset($d['li'][$n]);
    foreach ($d['init'] as $n => $r) if ((int)($r[0] ?? 0) < $now - 7 * 86400) unset($d['init'][$n]);
    foreach ($d['dup'] as $k => $r) if ((int)($r['t'] ?? 0) < $now - 86400) unset($d['dup'][$k]);
    foreach ($d['m'] as $k => $r) if ((int)($r[0] ?? 0) < $now - 3 * 86400) unset($d['m'][$k]);
    if (count($d['m']) > 4000) $d['m'] = array_slice($d['m'], -4000, null, true);
    if (count($d['li']) > 20000) { arsort($d['li']); $d['li'] = array_slice($d['li'], 0, 20000, true); }
    $ev = [];
    foreach ($d['ev'] as $e) if ((int)($e[0] ?? 0) >= $now - 7 * 86400) $ev[] = $e;
    $d['ev'] = array_slice($ev, -80);
}
function whInc(&$d, $f, $n = 1) {
    $k = gmdate('YmdH', time() + 7 * 3600);
    if (!isset($d['h'][$k]) || !is_array($d['h'][$k])) $d['h'][$k] = [];
    $d['h'][$k][$f] = (int)($d['h'][$k][$f] ?? 0) + $n;
}
// Id pesan WAHA beda bentuk antar engine/endpoint ("true_628..@c.us_3EB0..", {_serialized}, {id}).
// Inti id (segmen terakhir) dipakai sebagai kunci.
function whMid($id) {
    $id = (string)$id;
    if ($id === '') return '';
    $p = strrpos($id, '_');
    return substr($p === false ? $id : substr($id, $p + 1), 0, 64);
}
function whIn($wa, $num) {
    $num = waNormNum($num);
    if (!whOn($wa) || $num === '') return;
    whUpdate(whCh($wa), function (&$d) use ($num) {
        $now = time();
        whInc($d, 'in');
        $d['li'][$num] = $now;
        if (isset($d['init'][$num]) && empty($d['init'][$num][1]) && $now - (int)$d['init'][$num][0] <= 86400) $d['init'][$num][1] = 1;
    });
}
// $src: bot | agent | hp (diketik dari HP, terbaca dari echo WAHA)
function whOut($wa, $to, $src, $ok, $id = '', $text = '') {
    $to = waNormNum($to);
    if (!whOn($wa) || $to === '') return;
    whUpdate(whCh($wa), function (&$d) use ($to, $src, $ok, $id, $text) {
        $now = time();
        if (!$ok) { whInc($d, 'of'); return; }
        whInc($d, $src === 'hp' ? 'oh' : ($src === 'agent' ? 'oa' : 'ob'));
        $li = (int)($d['li'][$to] ?? 0);
        if ($src === 'bot' && $li > 0 && $now - $li <= 2) whInc($d, 'fa');
        if ($li < $now - 86400) {   // chat duluan: nomor ini tidak mengirim pesan 24 jam terakhir
            whInc($d, 'on');
            if (!isset($d['init'][$to]) || (int)$d['init'][$to][0] < $now - 86400) $d['init'][$to] = [$now, 0];
            $t = trim(preg_replace('/\s+/u', ' ', mb_strtolower((string)$text)));
            if (mb_strlen($t) >= 12) {
                $hk = 'h' . substr(md5($t), 0, 12);
                $r = is_array($d['dup'][$hk] ?? null) ? $d['dup'][$hk] : ['t' => $now, 'n' => []];
                if (!in_array($to, $r['n'], true) && count($r['n']) < 30) $r['n'][] = $to;
                $r['t'] = $now;
                $d['dup'][$hk] = $r;
            }
        }
        $mid = whMid($id);
        if ($mid !== '') $d['m']['m' . $mid] = [$now, 0];
    });
}
function whAck($wa, $p) {
    if (!whOn($wa)) return;
    $mid = whMid(wahaMsgId(is_array($p) ? $p : []));
    if ($mid === '') return;
    $ack = (int)($p['ack'] ?? 0);
    whUpdate(whCh($wa), function (&$d) use ($mid, $ack) {
        $first = empty($d['ack_on']);
        if ($first) $d['ack_on'] = time();   // langganan message.ack terbukti aktif mulai sekarang
        $k = 'm' . $mid;
        if (!isset($d['m'][$k])) return $first ? null : false;
        $cur = (int)$d['m'][$k][1];
        if ($ack < 0) $d['m'][$k][1] = -1;
        elseif ($cur >= 0 && $ack > $cur) $d['m'][$k][1] = min(4, $ack);
        else return $first ? null : false;
    });
}
// Penanda aksi dari dashboard (logout manual, pasang webhook) -> perubahan status sesuai itu bukan sinyal risiko.
function whMark($wa, $key) {
    if (!whOn($wa)) return;
    whUpdate(whCh($wa), function (&$d) use ($key) {
        $d['mk'][$key] = time();
        if ($key === 'cfg_at') $d['cfg_v'] = WA_HEALTH_CFG_V;
    });
}
function whStatus($wa, $evt) {
    if (!whOn($wa)) return;
    $st = strtoupper(trim((string)($evt['payload']['status'] ?? '')));
    if ($st === '') return;
    $meId = (string)($evt['me']['id'] ?? ($evt['payload']['me']['id'] ?? ''));
    $me = $meId !== '' ? wahaJidNum(preg_replace('/:\d+@/', '@', $meId)) : '';
    $known = waNormNum($wa['waha_number'] ?? '');
    $ch = whCh($wa);
    $flagOut = '';
    whUpdate($ch, function (&$d) use ($st, $me, $known, &$flagOut) {
        $now = time();
        $prev = (string)($d['st'] ?? '');
        $dirty = false;
        if ($st === 'SCAN_QR_CODE' && $prev !== $st) { $d['qr_at'] = $now; $dirty = true; }
        if ($st === 'WORKING' && $me !== '' && (string)($d['num'] ?? '') !== $me) {
            $last = (string)($d['num'] ?? '');
            if ($last === '' && $known !== '' && $known !== $me) $last = $known;
            // nomor berbeda dari yang terakhir terlihat -> nomor baru dipasang; umur dihitung dari sekarang
            if ($last !== '' && $last !== $me) { $d['paired_at'] = $now; $d['paired_src'] = 'scan'; $d['m'] = []; $d['init'] = []; }
            elseif ($last === '' && $known === '' && (int)($d['qr_at'] ?? 0) > $now - 3600 && empty($d['paired_at'])) { $d['paired_at'] = $now; $d['paired_src'] = 'scan'; }
            $d['num'] = $me; $dirty = true;
        }
        if ($prev === $st) return $dirty ? null : false;
        $quiet = max((int)($d['mk']['manual_at'] ?? 0), (int)($d['mk']['cfg_at'] ?? 0)) > $now - 180;
        $flag = '';
        if ($prev === 'WORKING' && !$quiet) $flag = $st === 'SCAN_QR_CODE' ? 'logout' : ($st === 'FAILED' ? 'failed' : 'drop');
        $d['ev'][] = [$now, $st, $flag];
        $d['st'] = $st; $d['st_at'] = $now;
        $flagOut = $flag;
    });
    if ($flagOut === 'logout') whAlert($wa, $ch, 'logout', null);
}

/* ---------- skor ---------- */
function whLevel($score) { return $score >= 60 ? 'bahaya' : ($score >= 30 ? 'waspada' : 'aman'); }
function whScore($ch, $d = null) {
    if ($d === null) $d = whRead($ch);
    $now = time();
    $f = [];
    $add = function ($p, $t) use (&$f) { $f[] = ['p' => (int)$p, 't' => $t]; };
    $keys = ['in', 'ob', 'oa', 'oh', 'on', 'of', 'fa'];
    $a = array_fill_keys($keys, 0); $peak = 0; $firstH = '';
    $h24 = gmdate('YmdH', $now + 7 * 3600 - 23 * 3600);
    $days = [];
    for ($i = 6; $i >= 0; $i--) $days[gmdate('Y-m-d', $now + 7 * 3600 - $i * 86400)] = ['in' => 0, 'out' => 0, 'new' => 0];
    foreach ($d['h'] as $k => $b) {
        $k = (string)$k;
        if (!is_array($b)) continue;
        if ($firstH === '' || $k < $firstH) $firstH = $k;
        $o = (int)($b['ob'] ?? 0) + (int)($b['oa'] ?? 0) + (int)($b['oh'] ?? 0);
        $dk = substr($k, 0, 4) . '-' . substr($k, 4, 2) . '-' . substr($k, 6, 2);
        if (isset($days[$dk])) { $days[$dk]['in'] += (int)($b['in'] ?? 0); $days[$dk]['out'] += $o; $days[$dk]['new'] += (int)($b['on'] ?? 0); }
        if ($k < $h24) continue;
        foreach ($keys as $x) $a[$x] += (int)($b[$x] ?? 0);
        if ($o > $peak) $peak = $o;
    }
    $out = $a['ob'] + $a['oa'] + $a['oh'];

    // 1. umur nomor
    $since = (int)($d['paired_at'] ?? 0);
    $age = $since > 0 ? (int)floor(($now - $since) / 86400) : null;
    if ($age !== null) {
        if ($age < 7) $add($out >= 50 ? 20 : 8, 'Nomor baru (' . $age . ' hari)' . ($out >= 50 ? ' sudah mengirim ' . $out . ' pesan/24 jam' : '') . ' — nomor baru paling rawan; naikkan volume bertahap.');
        elseif ($age < 30 && $out >= 50) $add(10, 'Nomor masih muda (' . $age . ' hari) dengan ' . $out . ' pesan keluar/24 jam.');
    }
    // 2. chat duluan ke nomor yang tidak mengirim pesan 24 jam terakhir
    $on = $a['on'];
    if ($on > 50) $add(25, $on . ' chat duluan ke nomor yang belum menghubungi (24 jam) — pola paling sering berujung banned.');
    elseif ($on > 20) $add(15, $on . ' chat duluan ke nomor yang belum menghubungi (24 jam).');
    elseif ($on > 5) $add(8, $on . ' chat duluan ke nomor yang belum menghubungi (24 jam).');
    // 3. balasan atas chat duluan (7 hari; yang belum 24 jam & belum dibalas tidak dihitung)
    $ni = 0; $nr = 0;
    foreach ($d['init'] as $r) {
        if (!is_array($r)) continue;
        if (!empty($r[1])) { $ni++; $nr++; }
        elseif ((int)$r[0] < $now - 86400) $ni++;
    }
    $reply = $ni > 0 ? $nr / $ni : null;
    if ($ni >= 10 && $reply < 0.2) $add(15, 'Hanya ' . round($reply * 100) . '% dari ' . $ni . ' chat duluan yang dibalas (7 hari) — penerima tidak merespons/bisa melaporkan.');
    elseif ($ni >= 10 && $reply < 0.4) $add(8, round($reply * 100) . '% dari ' . $ni . ' chat duluan yang dibalas (7 hari).');
    // 4. volume
    if ($peak > 100) $add(10, 'Puncak ' . $peak . ' pesan keluar dalam 1 jam.');
    if ($out > 800) $add(10, $out . ' pesan keluar dalam 24 jam.');
    // 5. teks kembar ke banyak nomor baru
    $dupMax = 0;
    foreach ($d['dup'] as $r) if (is_array($r) && (int)($r['t'] ?? 0) >= $now - 86400) $dupMax = max($dupMax, count((array)($r['n'] ?? [])));
    if ($dupMax >= 10) $add(15, 'Teks yang sama dikirim duluan ke ' . $dupMax . ' nomor berbeda (24 jam) — terlihat seperti broadcast.');
    // 6–7. centang (hanya pesan setelah langganan message.ack aktif, umur 6–72 jam)
    $ackOn = (int)($d['ack_on'] ?? 0);
    $na = 0; $stuck = 0; $read = 0;
    if ($ackOn > 0) {
        foreach ($d['m'] as $r) {
            if (!is_array($r)) continue;
            $t = (int)$r[0];
            if ($t < $ackOn || $t > $now - 6 * 3600) continue;
            $na++;
            if ((int)$r[1] <= 1) $stuck++;
            if ((int)$r[1] >= 3) $read++;
        }
    }
    $stuckP = $na > 0 ? $stuck / $na : null; $readP = $na > 0 ? $read / $na : null;
    if ($na >= 20 && $stuckP > 0.15) $add(15, round($stuckP * 100) . '% pesan tertahan di centang satu > 6 jam — tanda diblokir penerima atau pengiriman dibatasi.');
    elseif ($na >= 20 && $stuckP > 0.05) $add(7, round($stuckP * 100) . '% pesan tertahan di centang satu > 6 jam.');
    if ($na >= 30 && $readP < 0.3) $add(5, 'Hanya ' . round($readP * 100) . '% pesan yang dibaca (centang biru).');
    // 8. gagal kirim
    $att = $out + $a['of'];
    if ($att >= 10 && $a['of'] / $att > 0.05) $add(10, $a['of'] . ' dari ' . $att . ' kiriman gagal (24 jam).');
    // 9–10. sesi
    $lo7 = 0; $fa7 = 0; $dr24 = 0;
    foreach ($d['ev'] as $e) {
        if (!is_array($e) || (string)($e[2] ?? '') === '') continue;
        if ($e[2] === 'logout') $lo7++;
        if ($e[2] === 'failed') $fa7++;
        if ((int)$e[0] >= $now - 86400) $dr24++;
    }
    if ($lo7 > 0) $add(25, 'WhatsApp memutus sesi (logout paksa) ' . $lo7 . 'x dalam 7 hari — sinyal pembatasan paling kuat.');
    if ($fa7 > 0) $add(10, 'Sesi gagal (FAILED) ' . $fa7 . 'x dalam 7 hari.');
    if ($dr24 >= 3) $add(10, 'Sesi putus-sambung ' . $dr24 . 'x dalam 24 jam.');
    // 11. balasan instan
    if ($a['ob'] >= 20 && $a['fa'] / $a['ob'] > 0.8) $add(5, 'Hampir semua balasan bot terkirim < 2 detik — aktifkan jeda balasan.');

    usort($f, function ($x, $y) { return $y['p'] - $x['p']; });
    $score = min(100, array_sum(array_column($f, 'p')));
    $hoursData = $firstH !== '' ? (int)floor(($now + 7 * 3600 - gmmktime((int)substr($firstH, 8, 2), 0, 0, (int)substr($firstH, 4, 2), (int)substr($firstH, 6, 2), (int)substr($firstH, 0, 4))) / 3600) : 0;
    $series = [];
    foreach ($days as $dk => $v) $series[] = ['d' => $dk] + $v;
    return [
        'ch' => (string)$ch, 'score' => $score, 'level' => whLevel($score), 'factors' => $f, 'at' => $now,
        'partial' => $hoursData < 24,
        'm' => ['in' => $a['in'], 'out' => $out, 'out_bot' => $a['ob'], 'out_agent' => $a['oa'], 'out_hp' => $a['oh'],
                'out_new' => $on, 'fail' => $a['of'], 'peak_hour' => $peak, 'age_days' => $age, 'age_src' => (string)($d['paired_src'] ?? ''),
                'init_n' => $ni, 'reply_pct' => $reply === null ? null : round($reply * 100),
                'ack_on' => $ackOn > 0, 'ack_n' => $na, 'stuck_pct' => $stuckP === null ? null : round($stuckP * 100), 'read_pct' => $readP === null ? null : round($readP * 100),
                'logout_7d' => $lo7, 'failed_7d' => $fa7, 'drops_24h' => $dr24, 'status' => (string)($d['st'] ?? ''), 'number' => (string)($d['num'] ?? '')],
        'series' => $series, 'since' => $since,
        'events' => array_slice(array_reverse(array_values(array_filter($d['ev'], 'is_array'))), 0, 12),
        'cfg_ok' => (int)($d['cfg_v'] ?? 0) >= WA_HEALTH_CFG_V || $ackOn > 0,
    ];
}
// Nomor WAHA yang dipantau: [[ch, label, conf], ...]
function whChannels($s = null) {
    if ($s === null) $s = getSettings();
    $wa = waConf($s);
    if (!whOn($wa)) return [];
    $out = [];
    foreach (waChannels($s) as $c) {
        $conf = $c['id'] === 'utama' ? $wa : waChanConf($wa, $c['id'], $s);
        if ($c['id'] !== 'utama' && ($conf['_ch'] ?? '') !== $c['id']) continue;
        $out[] = [$c['id'], (string)$c['label'], $conf];
    }
    return $out;
}
if (!defined('WA_HEALTH_SCORE_FILE')) define('WA_HEALTH_SCORE_FILE', WA_HEALTH_DIR . '/score.json');
// Hitung ulang semua nomor (cron_tick tiap 15 menit, $force = sekarang). Kirim push saat masuk zona Bahaya.
function whScoreAll($s = null, $force = false) {
    if ($s === null) $s = getSettings();
    $chs = whChannels($s);
    if (!$chs) return null;
    $prev = readJson(WA_HEALTH_SCORE_FILE, []);
    if (!is_array($prev)) $prev = [];
    if (!$force && (int)($prev['at'] ?? 0) > time() - 900) return $prev;
    $res = ['at' => time(), 'nums' => [], 'alerted' => is_array($prev['alerted'] ?? null) ? $prev['alerted'] : []];
    foreach ($chs as $c) {
        list($ch, $label, $conf) = $c;
        $sc = whScore($ch);
        $row = whRow($ch, $label, $conf, $sc);
        $res['nums'][$ch] = $row;
        $was = (string)($prev['nums'][$ch]['level'] ?? 'aman');
        $lastA = (int)($res['alerted'][$ch] ?? 0);
        if ($sc['level'] === 'bahaya' && ($was !== 'bahaya' || $lastA < time() - 86400) && $lastA < time() - 12 * 3600 && empty($GLOBALS['dei_dry'])) {
            whAlert($conf, $ch, 'bahaya', $row);
            $res['alerted'][$ch] = time();
        }
    }
    deiWithLock('wa-health-score', function () use ($res) { writeJson(WA_HEALTH_SCORE_FILE, $res); });
    return $res;
}
function whRow($ch, $label, $conf, $sc) {
    return ['ch' => $ch, 'label' => $label, 'number' => $sc['m']['number'] !== '' ? $sc['m']['number'] : waNormNum($conf['waha_number'] ?? ''),
            'score' => $sc['score'], 'level' => $sc['level'], 'partial' => $sc['partial'],
            'top' => array_slice(array_map(function ($x) { return '+' . $x['p'] . ': ' . $x['t']; }, $sc['factors']), 0, 3)];
}
// Panel dibuka -> skor segar satu nomor ikut disimpan (lencana sama dengan panel). Push tetap lewat cron.
function whStoreRow($ch, $label, $conf, $sc) {
    try {
        deiWithLock('wa-health-score', function () use ($ch, $label, $conf, $sc) {
            $all = readJson(WA_HEALTH_SCORE_FILE, []);
            if (!is_array($all) || empty($all['at'])) return;
            $all['nums'][$ch] = whRow($ch, $label, $conf, $sc);
            writeJson(WA_HEALTH_SCORE_FILE, $all);
        });
    } catch (\Throwable $e) { error_log('wa-health store: ' . $e->getMessage()); }
}
function whAlert($wa, $ch, $kind, $row) {
    try {
        if (!empty($GLOBALS['dei_dry'])) return;
        $label = '';
        foreach (waChannels() as $c) if ($c['id'] === $ch) $label = (string)$c['label'];
        if ($label === '') $label = $ch === 'utama' ? 'Nomor utama' : $ch;
        if ($kind === 'logout') { $title = 'Nomor WA terputus: ' . $label; $body = 'WhatsApp memutus sesi nomor ini (logout paksa). Scan ulang di Widget & API dan kurangi chat duluan — bisa jadi tanda pembatasan.'; }
        else { $title = 'Nomor WA berisiko: ' . $label . ' (' . (int)$row['score'] . '/100)'; $body = preg_replace('/^\+\d+: /', '', (string)($row['top'][0] ?? 'Cek panel Kesehatan nomor.')); }
        $subs = array_keys(readJson(DATA_DIR . '/push-subs.json', []));
        $targets = [];
        foreach (readJson(USERS_FILE, []) as $u) {
            $un = (string)($u['username'] ?? '');
            if ($un !== '' && in_array(($u['role'] ?? ''), ['super_admin', 'admin'], true) && in_array($un, $subs, true)) $targets[] = $un;
        }
        if ($targets) sendPushToUsers($targets, $title, $body, deiDashboardUrl(), 'dei-wa-health');
        error_log('[wa-health] ' . $title . ' — ' . $body);
    } catch (\Throwable $e) { error_log('wa-health alert: ' . $e->getMessage()); }
}
// Pasang ulang konfigurasi sesi (webhook + message.ack). PUT me-restart sesi WAHA beberapa detik.
function whApplyCfg($conf) {
    $n = wahaSession($conf);
    if ((string)($conf['waha_webhook_key'] ?? '') === '') return [false, 'Kunci webhook belum ada.'];
    list($c, $d) = wahaApi($conf, 'GET', '/api/sessions/' . rawurlencode($n));
    if ($c === 404) return [false, 'Sesi WAHA belum dibuat — hubungkan nomor dulu.'];
    if ($c < 200 || $c >= 300) return [false, wahaErr($c, $d)];
    whMark($conf, 'cfg_at');
    list($c, $d) = wahaApi($conf, 'PUT', '/api/sessions/' . rawurlencode($n), ['name' => $n, 'config' => wahaSessionConfig($conf)]);
    if ($c < 200 || $c >= 300) { whUpdate(whCh($conf), function (&$d) { $d['cfg_v'] = 0; }); return [false, wahaErr($c, $d, 'Gagal memasang webhook.')]; }
    return [true, ''];
}
// cron: sesi lama (dibuat sebelum v1.2.104) dipasang ulang otomatis sekali, hanya jam 01–04 WIB.
function whEnsureCfgCron($s) {
    $done = [];
    $h = (int)wibDate('G');
    if ($h < 1 || $h > 4 || !empty($GLOBALS['dei_dry'])) return $done;
    foreach (whChannels($s) as $c) {
        list($ch, , $conf) = $c;
        $d = whRead($ch);
        if ((int)($d['cfg_v'] ?? 0) >= WA_HEALTH_CFG_V || !empty($d['ack_on'])) continue;
        if ((int)($d['mk']['cfg_try'] ?? 0) > time() - 6 * 3600) continue;
        whUpdate($ch, function (&$x) { $x['mk']['cfg_try'] = time(); });
        list($ok, $err) = whApplyCfg($conf);
        $done[$ch] = $ok ? 'ok' : $err;
    }
    return $done;
}
// Ringkas untuk statistik pusat (tanpa isi chat).
function whStatsSummary() {
    $sc = readJson(WA_HEALTH_SCORE_FILE, []);
    if (!is_array($sc) || empty($sc['nums'])) return null;
    $out = [];
    foreach ($sc['nums'] as $r) {
        $out[] = ['ch' => (string)$r['ch'], 'label' => mb_substr((string)$r['label'], 0, 40), 'number' => (string)$r['number'],
                  'score' => (int)$r['score'], 'level' => (string)$r['level'], 'partial' => !empty($r['partial']),
                  'top' => array_map(function ($t) { return mb_substr((string)$t, 0, 140); }, array_slice((array)($r['top'] ?? []), 0, 3))];
    }
    return ['at' => (int)$sc['at'], 'nums' => array_slice($out, 0, 21)];
}

