
/* ======================================================================
 * v1.2.101: percakapan — siklus hidup per percakapan WA (laporan layanan)
 *  Dibuka   : pesan pelanggan masuk & tidak ada percakapan terbuka
 *             (agent mengirim duluan -> dibuka dengan origin 'outbound').
 *  Selesai  : agent menekan Selesai | pelanggan pamit setelah dibalas |
 *             pesan terakhir dari kita & pelanggan diam >= 24 jam (resolved_at = balasan terakhir).
 *  Dibuka lagi: pesan pelanggan <= 30 menit setelah selesai.
 *  Kedaluwarsa: tanpa aktivitas 7 hari tanpa memenuhi syarat selesai (tidak dihitung selesai).
 *  Status   : open (bot) | handover (menunggu agent) | assigned | resolved | expired
 * ==================================================================== */
if (!defined('CONV_TIMEOUT_SEC')) define('CONV_TIMEOUT_SEC', 86400);
if (!defined('CONV_REOPEN_SEC')) define('CONV_REOPEN_SEC', 1800);
if (!defined('CONV_EXPIRE_SEC')) define('CONV_EXPIRE_SEC', 7 * 86400);

function convNew($num, $now, $origin, $ch) {
    return [
        'id' => 'c' . wibDate('ymdHis', $now) . '-' . $num . '-' . bin2hex(random_bytes(2)),
        'num' => $num, 'ch' => (string)$ch, 'channel' => 'whatsapp', 'origin' => $origin,
        'status' => 'open', 'opened_at' => $now, 'last_at' => $now, 'last_from' => '',
        'guest_msgs' => 0, 'bot_msgs' => 0, 'agent_msgs' => 0, 'system_msgs' => 0,
        'first_reply_at' => 0, 'first_bot_at' => 0, 'handover_at' => 0, 'handover_reason' => '',
        'assigned_at' => 0, 'agent' => '', 'agents' => [], 'assign_n' => 0, 'first_agent_at' => 0,
        'wait_since' => 0, 'resp_sum' => 0, 'resp_n' => 0, 'aresp_sum' => 0, 'aresp_n' => 0,
        'closing_at' => 0, 'resolved_at' => 0, 'resolved_by' => '', 'resolver' => '', 'ended_at' => 0, 'reopen_n' => 0,
    ];
}
// Selesaikan otomatis bila sudah waktunya. Hasil: '' | 'timeout' | 'expired'.
function convAutoEnd(&$c, $now) {
    if (!is_array($c) || convIsFinal($c)) return '';
    $last = (int)($c['last_at'] ?? 0);
    if (in_array((string)($c['last_from'] ?? ''), ['bot', 'agent'], true) && $now - $last >= CONV_TIMEOUT_SEC) {
        $c['status'] = 'resolved'; $c['resolved_at'] = $last; $c['resolved_by'] = 'timeout';
        $c['ended_at'] = $now; $c['wait_since'] = 0;
        return 'timeout';
    }
    if ($now - $last >= CONV_EXPIRE_SEC) {
        $c['status'] = 'expired'; $c['ended_at'] = $now; $c['wait_since'] = 0;
        return 'expired';
    }
    return '';
}
function convResolve(&$c, $now, $by, $who = '') {
    $c['status'] = 'resolved'; $c['resolved_at'] = $now; $c['resolved_by'] = $by; $c['resolver'] = (string)$who;
    $c['ended_at'] = $now; $c['wait_since'] = 0;
}
function convOpenStatus($c) {
    if ((int)($c['assigned_at'] ?? 0) > 0 && (string)($c['agent'] ?? '') !== '') return 'assigned';
    return ((int)($c['handover_at'] ?? 0) > 0) ? 'handover' : 'open';
}
// Inti mesin status (murni; diuji terpisah). Mengubah $c / $flush. Hasil: true bila ada perubahan berarti.
function convApply(&$c, &$flush, $num, $ev, $x, $now) {
    // percakapan terbuka yang sebenarnya sudah lewat waktunya (cron belum sempat menyapu)
    if (is_array($c) && !convIsFinal($c) && convAutoEnd($c, $now) !== '') { $flush[] = $c; $c = null; }

    if ($ev === 'guest') {
        $bye = !empty($x['bye']);
        if (is_array($c) && convIsFinal($c)) {
            $since = $now - (int)($c['ended_at'] ?? 0);
            if ($c['status'] === 'resolved' && $since <= CONV_REOPEN_SEC) {
                $c['guest_msgs']++;
                if ($bye) return true;                                   // "ok makasih" susulan: tetap selesai
                $c['status'] = 'open'; $c['status'] = convOpenStatus($c);
                $c['resolved_at'] = 0; $c['resolved_by'] = ''; $c['resolver'] = ''; $c['ended_at'] = 0;
                $c['reopen_n'] = (int)($c['reopen_n'] ?? 0) + 1;
                $c['last_from'] = 'guest'; $c['last_at'] = $now; $c['wait_since'] = $now;
                if (!empty($x['ch'])) $c['ch'] = (string)$x['ch'];
                return true;
            }
            if ($bye) { $c['guest_msgs']++; return true; }               // pamit ke percakapan yang sudah selesai
            $c = null;
        }
        if ($c === null) {
            if ($bye) return false;                                      // "ok"/stiker tanpa percakapan aktif: bukan percakapan baru
            $c = convNew($num, $now, 'inbound', (string)($x['ch'] ?? ''));
            if (!empty($x['human'])) {
                $c['handover_at'] = $now;
                $c['handover_reason'] = !empty($x['manual']) ? 'manual_mode' : 'mode_human';
                $c['status'] = 'handover';
            }
            if (!empty($x['agent'])) {                                   // nomor masih dipegang agent (claim)
                $c['handover_at'] = $now; if ($c['handover_reason'] === '') $c['handover_reason'] = 'claimed';
                $c['assigned_at'] = $now; $c['agent'] = (string)$x['agent']; $c['assign_n'] = 1; $c['status'] = 'assigned';
            }
        }
        $c['guest_msgs']++;
        if (!empty($x['ch'])) $c['ch'] = (string)$x['ch'];
        $c['last_from'] = 'guest'; $c['last_at'] = $now;
        if ($bye) {
            if (((int)$c['bot_msgs'] + (int)$c['agent_msgs']) > 0) convResolve($c, $now, 'guest_bye');
        } elseif (empty($c['wait_since'])) {
            $c['wait_since'] = $now;
        }
        return true;
    }

    if ($ev === 'bot' || $ev === 'agent' || $ev === 'system') {
        $agent = (string)($x['agent'] ?? '');
        if ($c === null) {
            if ($ev !== 'agent') return false;
            $c = convNew($num, $now, 'outbound', (string)($x['ch'] ?? ''));
            $c['handover_at'] = $now; $c['handover_reason'] = 'outbound';
        }
        $c[$ev . '_msgs'] = (int)($c[$ev . '_msgs'] ?? 0) + 1;
        if (convIsFinal($c)) return true;                                // balasan susulan setelah selesai: hanya dihitung
        if ($ev === 'system') return true;                               // pesan lisensi/kuota bukan jawaban
        if (!$c['first_reply_at']) $c['first_reply_at'] = $now;
        $ws = (int)($c['wait_since'] ?? 0);
        if ($ws > 0) {
            $c['resp_sum'] += max(0, $now - $ws); $c['resp_n']++;
            if ($ev === 'agent') { $c['aresp_sum'] += max(0, $now - $ws); $c['aresp_n']++; }
            $c['wait_since'] = 0;
        }
        if ($ev === 'bot') {
            if (!$c['first_bot_at']) $c['first_bot_at'] = $now;
        } else {
            if (!$c['first_agent_at']) $c['first_agent_at'] = $now;
            if ($agent !== '' && !in_array($agent, (array)$c['agents'], true)) $c['agents'][] = $agent;
            if (!$c['handover_at']) { $c['handover_at'] = $now; $c['handover_reason'] = 'agent_reply'; }
            if (!$c['assigned_at']) { $c['assigned_at'] = $now; $c['assign_n'] = max(1, (int)$c['assign_n']); }
            if ($agent !== '' && ($c['agent'] === '' || $c['agent'] === '(HP)')) $c['agent'] = $agent;
            elseif ($c['agent'] === '') $c['agent'] = '(HP)';
            $c['status'] = 'assigned';
        }
        $c['last_from'] = $ev; $c['last_at'] = $now;
        return true;
    }

    if (!is_array($c) || convIsFinal($c)) return false;                  // event berikut hanya untuk percakapan terbuka

    if ($ev === 'handover') {
        if ($c['handover_at']) return false;
        $c['handover_at'] = $now; $c['handover_reason'] = (string)($x['reason'] ?? 'mode_human');
        $c['status'] = convOpenStatus($c);
        return true;
    }
    if ($ev === 'assign') {
        $agent = (string)($x['agent'] ?? '');
        if ($agent === '') return false;
        if (!$c['handover_at']) { $c['handover_at'] = $now; $c['handover_reason'] = 'assign'; }
        if (!$c['assigned_at']) $c['assigned_at'] = $now;
        if ($c['agent'] !== $agent) { $c['agent'] = $agent; $c['assign_n'] = (int)$c['assign_n'] + 1; }
        $c['status'] = 'assigned';
        return true;
    }
    if ($ev === 'release') {
        if ($c['status'] !== 'assigned') return false;
        // agent terakhir tetap tercatat (atribusi); Mode Manual -> kembali ke antrean, Mode AI -> bot
        $c['status'] = !empty($x['manual']) ? 'handover' : 'open';
        return true;
    }
    if ($ev === 'closing') { $c['closing_at'] = $now; return true; }
    if ($ev === 'resolve') { convResolve($c, $now, 'agent', (string)($x['agent'] ?? '')); return true; }
    return false;
}
// Satu pintu pencatatan. Tidak pernah melempar — gagal mencatat tidak boleh mengganggu balasan.
function convTrack($num, $ev, $x = []) {
    $num = waNormNum($num);
    if ($num === '') return false;
    try {
        if ($ev === 'guest') {
            $x['human'] = (waGetMode($num) === 'human');
            $x['manual'] = deiIsManual();
            $cl = waClaimGet($num);
            if ($cl && !empty($cl['agent_username'])) $x['agent'] = (string)$cl['agent_username'];
        }
        if ($ev === 'release') $x['manual'] = deiIsManual();
        return (bool)convStoreMutate($num, function (&$c, &$flush) use ($num, $ev, $x) {
            return convApply($c, $flush, $num, $ev, $x, time());
        });
    } catch (\Throwable $e) { error_log('convTrack(' . $ev . '): ' . $e->getMessage()); return false; }
}
// cron_tick: selesaikan percakapan yang sudah waktunya + rapikan berkas terbuka.
function convSweep($now = null) {
    $now = $now ?? time();
    $out = ['timeout' => 0, 'expired' => 0, 'evicted' => 0];
    foreach (convStoreOpen() as $c0) {
        $tmp = $c0;
        if (convAutoEnd($tmp, $now) === '') continue;                    // pra-saring tanpa kunci
        convStoreMutate((string)$c0['num'], function (&$c, &$flush) use ($now, &$out, $c0) {
            if (!is_array($c) || ($c['id'] ?? '') !== $c0['id']) return;
            $r = convAutoEnd($c, $now);
            if ($r !== '') $out[$r]++;
        });
    }
    $out['evicted'] = convStoreEvict($now);
    return $out;
}

/* ---------- v1.2.101: statistik layanan dari record percakapan ---------- */
function convAvg($sum, $n) { return $n > 0 ? (int)round($sum / $n) : null; }
function convStats($recs, $fromTs, $toTs, $chLabels = []) {
    $z = function () { return ['n' => 0, 'sum' => 0]; };
    $T = ['total' => 0, 'inbound' => 0, 'outbound' => 0, 'customers' => 0,
          'open_now' => 0, 'unassigned' => 0, 'assigned' => 0, 'resolved' => 0, 'expired' => 0, 'in_progress' => 0,
          'bot_handled' => 0, 'bot_resolved' => 0, 'to_agent' => 0, 'reopened' => 0,
          'resolved_agent' => 0, 'resolved_bye' => 0, 'resolved_timeout' => 0,
          'guest_msgs' => 0, 'bot_msgs' => 0, 'agent_msgs' => 0];
    $A = ['frt' => $z(), 'frt_agent' => $z(), 'wait' => $z(), 'resp' => $z(), 'resp_agent' => $z(), 'resolution' => $z(), 'bot_resolution' => $z()];
    $nums = []; $daily = []; $hourly = array_fill(0, 24, 0); $wday = array_fill(1, 7, 0);
    $reasons = []; $agents = []; $chans = [];
    for ($d = $fromTs; $d <= $toTs; $d += 86400) $daily[wibDate('Y-m-d', $d)] = ['date' => wibDate('Y-m-d', $d), 'total' => 0, 'bot_resolved' => 0, 'to_agent' => 0, 'resolved' => 0];
    $add = function (&$a, $v) { if ($v !== null && $v >= 0) { $a['n']++; $a['sum'] += $v; } };
    foreach ($recs as $c) {
        $o = (int)$c['opened_at'];
        $in = (($c['origin'] ?? 'inbound') === 'inbound');
        $st = (string)($c['status'] ?? 'open');
        $res = ($st === 'resolved');
        $hand = (int)($c['handover_at'] ?? 0); $asg = (int)($c['assigned_at'] ?? 0);
        $bot = (int)($c['bot_msgs'] ?? 0) > 0;
        $botRes = $res && $bot && !$hand && (int)($c['agent_msgs'] ?? 0) === 0;
        $T['total']++; $T[$in ? 'inbound' : 'outbound']++;
        $nums[$c['num']] = 1;
        if ($st === 'open') $T['open_now']++;
        if ($st === 'handover') $T['unassigned']++;
        if (in_array($st, ['open', 'handover', 'assigned'], true)) $T['in_progress']++;
        if ($asg) $T['assigned']++;
        if ($res) { $T['resolved']++; $rb = (string)($c['resolved_by'] ?? ''); if ($rb === 'agent') $T['resolved_agent']++; elseif ($rb === 'guest_bye') $T['resolved_bye']++; else $T['resolved_timeout']++; }
        if ($st === 'expired') $T['expired']++;
        if ($bot) $T['bot_handled']++;
        if ($botRes) $T['bot_resolved']++;
        if ($bot && $hand) $T['to_agent']++;
        if ((int)($c['reopen_n'] ?? 0) > 0) $T['reopened']++;
        foreach (['guest_msgs', 'bot_msgs', 'agent_msgs'] as $k) $T[$k] += (int)($c[$k] ?? 0);
        if ($hand) { $r = (string)($c['handover_reason'] ?? '') ?: 'lainnya'; $reasons[$r] = ($reasons[$r] ?? 0) + 1; }

        $frt = $frtA = $wait = $resol = null;
        if ($in) {
            if ((int)$c['first_reply_at']) $frt = (int)$c['first_reply_at'] - $o;
            if ((int)$c['first_agent_at']) $frtA = (int)$c['first_agent_at'] - max($hand, $o);
            if ($asg && $hand) $wait = max(0, $asg - $hand);
            if ($res) $resol = max(0, (int)$c['resolved_at'] - $o);
            $add($A['frt'], $frt); $add($A['frt_agent'], $frtA); $add($A['wait'], $wait); $add($A['resolution'], $resol);
            if ($botRes) $add($A['bot_resolution'], $resol);
        }
        $A['resp']['n'] += (int)$c['resp_n']; $A['resp']['sum'] += (int)$c['resp_sum'];
        $A['resp_agent']['n'] += (int)$c['aresp_n']; $A['resp_agent']['sum'] += (int)$c['aresp_sum'];

        $dk = wibDate('Y-m-d', $o);
        if (isset($daily[$dk])) {
            $daily[$dk]['total']++;
            if ($botRes) $daily[$dk]['bot_resolved']++;
            if ($bot && $hand) $daily[$dk]['to_agent']++;
            if ($res) $daily[$dk]['resolved']++;
        }
        if ($in) { $hourly[(int)wibDate('G', $o)]++; $wday[(int)wibDate('N', $o)]++; }

        $ag = (string)($c['agent'] ?? '');
        if ($ag !== '' && $asg) {
            if (!isset($agents[$ag])) $agents[$ag] = ['agent' => $ag, 'assigned' => 0, 'resolved' => 0, 'in_progress' => 0, 'msgs' => 0,
                'frt' => $z(), 'resp' => $z(), 'resolution' => $z()];
            $R = &$agents[$ag];
            $R['assigned']++; if ($res) $R['resolved']++; if (!convIsFinal($c)) $R['in_progress']++;
            $R['msgs'] += (int)($c['agent_msgs'] ?? 0);
            $add($R['frt'], $frtA); $add($R['resolution'], $resol);
            $R['resp']['n'] += (int)$c['aresp_n']; $R['resp']['sum'] += (int)$c['aresp_sum'];
            unset($R);
        }
        $ch = (string)($c['ch'] ?? '') ?: 'utama';
        if (!isset($chans[$ch])) $chans[$ch] = ['ch' => $ch, 'label' => $chLabels[$ch] ?? $ch, 'total' => 0, 'bot_resolved' => 0, 'to_agent' => 0, 'resolved' => 0, 'unassigned' => 0,
            'frt' => $z(), 'frt_agent' => $z(), 'resolution' => $z()];
        $C = &$chans[$ch];
        $C['total']++; if ($botRes) $C['bot_resolved']++; if ($bot && $hand) $C['to_agent']++; if ($res) $C['resolved']++; if ($st === 'handover') $C['unassigned']++;
        $add($C['frt'], $frt); $add($C['frt_agent'], $frtA); $add($C['resolution'], $resol);
        unset($C);
    }
    $T['customers'] = count($nums);
    $avg = [];
    foreach ($A as $k => $a) $avg[$k] = convAvg($a['sum'], $a['n']);
    $avg['bot_rate'] = $T['bot_handled'] > 0 ? round($T['bot_resolved'] * 100 / $T['bot_handled'], 1) : null;
    $avg['resolved_rate'] = $T['total'] > 0 ? round($T['resolved'] * 100 / $T['total'], 1) : null;
    $avg['handover_rate'] = $T['bot_handled'] > 0 ? round($T['to_agent'] * 100 / $T['bot_handled'], 1) : null;
    $fin = function ($rows, $keys) {
        $o = [];
        foreach ($rows as $r) { foreach ($keys as $k) $r[$k] = convAvg($r[$k]['sum'], $r[$k]['n']); $o[] = $r; }
        usort($o, function ($a, $b) { return ($b['assigned'] ?? $b['total']) <=> ($a['assigned'] ?? $a['total']); });
        return $o;
    };
    // rata-rata per hari dalam seminggu = jumlah / banyaknya hari itu dalam rentang
    $wdN = array_fill(1, 7, 0);
    for ($d = $fromTs; $d <= $toTs; $d += 86400) $wdN[(int)wibDate('N', $d)]++;
    $wdOut = [];
    foreach ($wday as $k => $v) $wdOut[] = ['day' => $k, 'total' => $v, 'avg' => $wdN[$k] ? round($v / $wdN[$k], 1) : 0];
    arsort($reasons);
    return [
        'totals' => $T, 'avg' => $avg,
        'daily' => array_values($daily), 'hourly' => $hourly, 'weekday' => $wdOut,
        'handover_reasons' => $reasons,
        'agents' => $fin($agents, ['frt', 'resp', 'resolution']),
        'channels' => $fin($chans, ['frt', 'frt_agent', 'resolution']),
    ];
}
// Nama kontak untuk sekumpulan record (mode file: satu kali baca; mysql: per nomor).
function convContactNames($recs) {
    $out = [];
    try {
        $nums = array_unique(array_map(function ($c) { return (string)$c['num']; }, $recs));
        if (!deiStorageMysql()) {
            $all = waGetContacts();
            foreach ($nums as $n) if (isset($all[$n])) $out[$n] = (string)($all[$n]['name'] ?? '');
        } else {
            foreach ($nums as $n) { $ct = waContactGet($n); if ($ct) $out[$n] = (string)($ct['name'] ?? ''); }
        }
    } catch (\Throwable $e) {}
    return $out;
}
// Ringkas untuk UI (thread & daftar).
function convPublic($c) {
    if (!is_array($c)) return null;
    $k = ['id', 'num', 'ch', 'origin', 'status', 'opened_at', 'last_at', 'last_from', 'guest_msgs', 'bot_msgs', 'agent_msgs',
          'first_reply_at', 'handover_at', 'handover_reason', 'assigned_at', 'agent', 'first_agent_at', 'resolved_at', 'resolved_by', 'resolver', 'reopen_n'];
    $o = [];
    foreach ($k as $x) $o[$x] = $c[$x] ?? null;
    return $o;
}
// Sejak kapan percakapan tercatat (ts) — null bila belum ada.
function convTrackingSince() {
    try {
        if (deiStorageMysql()) {
            return convDbRun(function () { $v = deiDb()->query('SELECT MIN(opened_at) FROM dei_conversations')->fetchColumn(); return $v ? (int)$v : null; });
        }
        $min = null;
        $files = glob(CONV_DIR . '/*.jsonl') ?: [];
        sort($files);
        if ($files) { $fh = @fopen($files[0], 'r'); if ($fh) { $c = json_decode((string)fgets($fh), true); fclose($fh); if (is_array($c)) $min = (int)$c['opened_at']; } }
        $f = CONV_OPEN_FILE;
        foreach ((array)readJson($f, []) as $c) if (is_array($c) && ($min === null || (int)$c['opened_at'] < $min)) $min = (int)$c['opened_at'];
        return $min;
    } catch (\Throwable $e) { return null; }
}
