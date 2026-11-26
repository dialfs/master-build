/* ---------- v1.2.221: laporan-sales — menu Laporan Sales (performa vs target, aktivitas, produktivitas, forecast, funnel & win/loss, umur lead) ---------- */
if (!defined('SALES_TARGET_FILE')) define('SALES_TARGET_FILE', DATA_DIR . '/sales-targets.json');
function srTargets221() {   // {sid: {rev, deals, acts}} per bulan
    $d = readJson(SALES_TARGET_FILE, []); if (!is_array($d)) $d = [];
    $o = [];
    foreach ($d as $sid => $t) {
        if (!is_array($t)) continue;
        $o[(string)$sid] = ['rev' => max(0, (int)($t['rev'] ?? 0)), 'deals' => max(0, (int)($t['deals'] ?? 0)), 'acts' => max(0, (int)($t['acts'] ?? 0))];
    }
    return $o;
}
function srStageKey221($label) {   // label status (dari log "Status: A → B") -> kunci tahap
    static $m = null;
    if ($m === null) {
        $m = [];
        foreach (crmStagesDef216() as $k => $d) $m[mb_strtolower($d['label'])] = $k;
        foreach (crmPipeConf216() as $k => $d) $m[mb_strtolower($d['label'])] = $k;
        $m['closed'] = 'closed_deal'; $m['follow up'] = 'follow_up'; $m['proposal'] = 'proposal';
    }
    return $m[mb_strtolower(trim((string)$label))] ?? '';
}
function srWorkdays221($fromTs, $toTs) {   // hari kerja Senin–Sabtu
    $n = 0;
    for ($t = $fromTs; $t <= $toTs; $t += 86400) { if ((int)gmdate('N', $t + 7 * 3600) !== 7) $n++; }
    return max(1, $n);
}
function srMonthFrac221($fromD, $toD) {   // pecahan bulan yang dicakup periode (untuk target pro-rata)
    $a = wibDayStart($fromD); $b = wibDayStart($toD); $f = 0.0;
    for ($t = $a; $t <= $b; $t += 86400) { $f += 1 / (int)gmdate('t', $t + 7 * 3600); }
    return $f;
}
/**
 * Laporan Sales lengkap. $only: null = semua sales; array id sales yang boleh dilihat.
 * $fSid: filter satu sales ('' = semua, '_none' = tanpa sales). $fDiv: filter divisi ('' = semua).
 */
function crmRep221($fromD, $toD, $only = null, $fSid = '', $fDiv = '') {
    $fromTs = wibDayStart($fromD); $toTs0 = wibDayStart($toD);
    if ($fromTs === null || $toTs0 === null || $toTs0 < $fromTs) return null;
    $toTs = $toTs0 + 86399;
    $now = time(); $today = wibToday();
    $map = slMap(); $pc = crmPipeConf216(); $openSt = crmOpenStatuses216();
    $order = ['baru' => 0, 'qualified' => 1, 'follow_up' => 2, 'proposal' => 3, 'negosiasi' => 4, 'closed_deal' => 5];
    $types = crmTypes215(); $srcs = crmSources215();
    $tg = srTargets221();
    $divLc = mb_strtolower(trim((string)$fDiv));
    $want = function ($sid) use ($only, $fSid, $divLc, $map) {
        $sid = (string)$sid;
        if ($only !== null && !in_array($sid, (array)$only, true)) return false;
        if ($fSid !== '') { if ($fSid === '_none' ? $sid !== '' : $sid !== $fSid) return false; }
        if ($divLc !== '' && mb_strtolower(trim((string)($map[$sid]['div'] ?? ''))) !== $divLc) return false;
        return true;
    };
    $sname = function ($sid) use ($map) { $sid = (string)$sid; return $sid === '' ? 'Tanpa sales' : (string)($map[$sid]['name'] ?? '(sales dihapus)'); };

    // ---- performa (pakai perhitungan v1.2.217) + target
    $vis = null;
    if ($only !== null || $fSid !== '' || $divLc !== '') {
        $vis = [];
        foreach (array_merge([''], array_map('strval', array_keys($map))) as $id) if ($want($id)) $vis[] = $id;
    }
    $perf = crmPerf217($fromD, $toD, $vis);
    $frac = srMonthFrac221($fromD, $toD);
    $tt = ['rev' => 0, 'deals' => 0, 'acts' => 0];
    foreach ($perf['rows'] as &$R) {
        $t = $tg[(string)$R['id']] ?? null;
        $R['target'] = $t ? ['rev' => (int)round($t['rev'] * $frac), 'deals' => (int)round($t['deals'] * $frac), 'acts' => (int)round($t['acts'] * $frac)] : null;
        if ($R['target']) foreach ($tt as $k => $v) $tt[$k] += $R['target'][$k];
        $R['att_rev'] = ($R['target'] && $R['target']['rev']) ? (int)round($R['deal_v'] * 100 / $R['target']['rev']) : null;
        $R['att_deals'] = ($R['target'] && $R['target']['deals']) ? (int)round($R['deal'] * 100 / $R['target']['deals']) : null;
        $R['att_acts'] = ($R['target'] && $R['target']['acts']) ? (int)round($R['acts'] * 100 / $R['target']['acts']) : null;
        $R['div'] = (string)($map[(string)$R['id']]['div'] ?? '');
    }
    unset($R);
    $perf['total']['target'] = ($tt['rev'] || $tt['deals'] || $tt['acts']) ? $tt : null;
    $perf['total']['att_rev'] = $tt['rev'] ? (int)round($perf['total']['deal_v'] * 100 / $tt['rev']) : null;
    $perf['total']['att_deals'] = $tt['deals'] ? (int)round($perf['total']['deal'] * 100 / $tt['deals']) : null;
    $perf['month_frac'] = round($frac, 2);

    // ---- data lead & aktivitas yang terlihat
    $contacts = waGetContacts(); $leads = []; $acts = crmActAll215();
    foreach (leadsGetAll() as $num => $l) {
        if (!is_array($l)) continue;
        $num = (string)$num; $sid = slLeadSalesId($l, $num, $contacts);
        if (!$want($sid)) continue;
        $st = (string)($l['status'] ?? 'baru'); if ($st === 'closed') $st = 'closed_deal';
        $hist = []; $last = ''; $first = ''; $nonSys = [];
        foreach ((array)($acts[$num] ?? []) as $a) {
            if (!is_array($a)) continue;
            if (($a['type'] ?? '') === 'sys') {
                if (preg_match('/^Status: (.+?) → (.+)$/u', (string)($a['text'] ?? ''), $m)) {
                    $k2 = srStageKey221($m[2]); if ($k2 !== '') $hist[] = [$k2, strtotime((string)$a['at'] . ':00') ?: 0];
                }
                continue;
            }
            $nonSys[] = $a;
            $at = (string)($a['at'] ?? '');
            if ($at > $last) $last = $at;
            if ($first === '' || $at < $first) $first = $at;
        }
        $leads[$num] = ['num' => $num, 'name' => crmLeadName215($num) ?: $num, 'sid' => $sid, 'st' => $st, 'v' => (int)($l['value'] ?? 0),
            'ct' => strtotime((string)($l['created_at'] ?? '')) ?: 0, 'closed' => (int)($l['closed_ts'] ?? 0), 'ce' => (string)($l['close_est'] ?? ''),
            'src' => (string)($l['source'] ?? '') !== '' ? (string)$l['source'] : (($l['src'] ?? '') === 'sales' ? 'tag' : 'chat'),
            'note' => trim((string)($l['note'] ?? '')), 'company' => (string)($l['company'] ?? ''),
            'hist' => $hist, 'last' => $last, 'first' => $first, 'acts' => $nonSys];
    }

    // ---- aktivitas
    $byDay = []; for ($t = $fromTs; $t <= $toTs0; $t += 86400) $byDay[wibDate('Y-m-d', $t)] = ['n' => 0, 't' => []];
    $mx = []; $list = []; $tTot = [];
    foreach ($leads as $L) {
        foreach ($L['acts'] as $a) {
            $at = strtotime((string)($a['at'] ?? '') . ':00') ?: strtotime((string)($a['at'] ?? ''));
            if (!$at || $at < $fromTs || $at > $toTs) continue;
            $ty = (string)($a['type'] ?? 'other'); $d = wibDate('Y-m-d', $at);
            if (isset($byDay[$d])) { $byDay[$d]['n']++; $byDay[$d]['t'][$ty] = ($byDay[$d]['t'][$ty] ?? 0) + 1; }
            $k = $L['sid'];
            if (!isset($mx[$k])) $mx[$k] = ['id' => $k, 'name' => $sname($k), 'n' => 0, 't' => []];
            $mx[$k]['n']++; $mx[$k]['t'][$ty] = ($mx[$k]['t'][$ty] ?? 0) + 1; $tTot[$ty] = ($tTot[$ty] ?? 0) + 1;
            $list[] = ['at' => (string)$a['at'], 'type' => $ty, 'text' => mb_substr((string)($a['text'] ?? ''), 0, 160), 'num' => $L['num'], 'lead' => $L['name'],
                       'sales' => $sname($k), 'by' => (string)($a['by_name'] ?? $a['by'] ?? ''), 'next' => (string)($a['next_due'] ?? '')];
        }
    }
    usort($list, function ($a, $b) { return strcmp($b['at'], $a['at']); });
    $mx = array_values($mx); usort($mx, function ($a, $b) { return $b['n'] <=> $a['n']; });
    $days = []; foreach ($byDay as $d => $x) $days[] = ['d' => $d, 'n' => $x['n'], 't' => $x['t']];
    arsort($tTot);
    $activity = ['days' => $days, 'by_sales' => $mx, 'by_type' => $tTot, 'total' => count($list), 'list' => array_slice($list, 0, 500), 'list_more' => max(0, count($list) - 500)];

    // ---- produktivitas
    $wd = srWorkdays221($fromTs, $toTs0); $P = [];
    $mkP = function ($k) use ($sname, $map) { return ['id' => $k, 'name' => $sname($k), 'active' => $k !== '' && !empty($map[$k]['active']), 'acts' => 0, 'days' => [], 'touched' => [],
        'fu_due' => 0, 'fu_ontime' => 0, 'fu_late_done' => 0, 'fu_missed' => 0, 'fu_open' => 0, 'resp' => [], 'resp_none' => 0, 'open' => 0, 'idle' => 0, 'new' => 0]; };
    foreach ($map as $id => $x) if (!empty($x['active']) && $want((string)$id)) $P[(string)$id] = $mkP((string)$id);
    foreach ($leads as $L) {
        $k = $L['sid']; if (!isset($P[$k])) $P[$k] = $mkP($k);
        $isOpen = in_array($L['st'], $openSt, true);
        if ($isOpen) { $P[$k]['open']++; $lt = $L['last'] !== '' ? strtotime($L['last'] . ':00') : 0; if (!$lt || (int)floor(($now - $lt) / 86400) > 7) $P[$k]['idle']++; }
        if ($L['ct'] >= $fromTs && $L['ct'] <= $toTs) {
            $P[$k]['new']++;
            if ($L['first'] !== '') { $ft = strtotime($L['first'] . ':00'); if ($ft) $P[$k]['resp'][] = max(0, $ft - $L['ct']); }
            else $P[$k]['resp_none']++;
        }
        foreach ($L['acts'] as $a) {
            $at = strtotime((string)($a['at'] ?? '') . ':00');
            if ($at && $at >= $fromTs && $at <= $toTs) { $P[$k]['acts']++; $P[$k]['days'][wibDate('Y-m-d', $at)] = 1; $P[$k]['touched'][$L['num']] = 1; }
            $due = (string)($a['next_due'] ?? '');
            if ($due === '' || $due < $fromD || $due > $toD) continue;
            $P[$k]['fu_due']++;
            if (!empty($a['next_done'])) { $dd = substr((string)($a['next_done_at'] ?? ''), 0, 10); if ($dd !== '' && $dd <= $due) $P[$k]['fu_ontime']++; else $P[$k]['fu_late_done']++; }
            elseif ($due < $today) $P[$k]['fu_missed']++;
            else $P[$k]['fu_open']++;
        }
    }
    $prod = []; $pt = $mkP('*'); $pt['name'] = 'Total';
    foreach ($P as $k => $R) {
        if (!$R['acts'] && !$R['open'] && !$R['fu_due'] && !$R['new'] && ($k === '' || !$R['active'])) continue;
        foreach (['acts', 'fu_due', 'fu_ontime', 'fu_late_done', 'fu_missed', 'fu_open', 'resp_none', 'open', 'idle', 'new'] as $f) $pt[$f] += $R[$f];
        $pt['days'] += $R['days']; $pt['touched'] += $R['touched']; $pt['resp'] = array_merge($pt['resp'], $R['resp']);
        $prod[] = $R;
    }
    $finP = function ($R) use ($wd) {
        $done = $R['fu_ontime'] + $R['fu_late_done'] + $R['fu_missed'];
        $r = $R['resp']; sort($r); $med = $r ? $r[(int)floor((count($r) - 1) / 2)] : null;
        return ['id' => $R['id'], 'name' => $R['name'], 'active' => $R['active'], 'acts' => $R['acts'], 'active_days' => count($R['days']), 'workdays' => $wd,
            'per_day' => round($R['acts'] / $wd, 1), 'touched' => count($R['touched']), 'per_lead' => count($R['touched']) ? round($R['acts'] / count($R['touched']), 1) : null,
            'fu_due' => $R['fu_due'], 'fu_ontime' => $R['fu_ontime'], 'fu_late_done' => $R['fu_late_done'], 'fu_missed' => $R['fu_missed'], 'fu_open' => $R['fu_open'],
            'compliance' => $done ? (int)round($R['fu_ontime'] * 100 / $done) : null,
            'new' => $R['new'], 'resp_med_h' => $med === null ? null : round($med / 3600, 1), 'resp_none' => $R['resp_none'], 'open' => $R['open'], 'idle' => $R['idle']];
    };
    $prod = array_map($finP, $prod); usort($prod, function ($a, $b) { return $b['acts'] <=> $a['acts'] ?: strcmp($a['name'], $b['name']); });
    $productivity = ['rows' => $prod, 'total' => $finP($pt), 'workdays' => $wd];

    // ---- forecast (kondisi saat ini)
    $m0 = substr($today, 0, 7); $months = [];
    for ($i = 0; $i < 4; $i++) $months[] = gmdate('Y-m', gmmktime(12, 0, 0, (int)substr($m0, 5, 2) + $i, 1, (int)substr($m0, 0, 4)));
    $bk = ['overdue' => 'Lewat perkiraan'];
    foreach ($months as $i => $mm) $bk[$mm] = $mm;
    $bk['later'] = 'Sesudahnya'; $bk['none'] = 'Tanpa tanggal';
    $mkB = function () { return ['n' => 0, 'pipe' => 0, 'weighted' => 0, 'commit' => 0, 'best' => 0]; };
    $buckets = []; foreach ($bk as $k => $lab) $buckets[$k] = ['key' => $k, 'label' => $lab] + $mkB();
    $fcS = []; $deals = [];
    $wonM = function ($k, $mm) use ($leads) { $v = 0; $n = 0; foreach ($leads as $L) if ($L['sid'] === $k && $L['st'] === 'closed_deal' && $L['closed'] && wibDate('Y-m', $L['closed']) === $mm) { $v += $L['v']; $n++; } return [$n, $v]; };
    foreach ($leads as $L) {
        if (!in_array($L['st'], $openSt, true)) continue;
        $prob = (int)($pc[$L['st']]['prob'] ?? 0); $w = $L['v'] * $prob / 100;
        $ce = $L['ce'];
        $b = $ce === '' ? 'none' : ($ce < $today ? 'overdue' : (in_array(substr($ce, 0, 7), $months, true) ? substr($ce, 0, 7) : 'later'));
        $B = &$buckets[$b]; $B['n']++; $B['pipe'] += $L['v']; $B['weighted'] += $w; if ($prob >= 70) $B['commit'] += $L['v']; if ($prob >= 40) $B['best'] += $L['v']; unset($B);
        $k = $L['sid'];
        if (!isset($fcS[$k])) $fcS[$k] = ['id' => $k, 'name' => $sname($k), 'm' => []];
        foreach ([$months[0], $months[1]] as $mm) {
            if (!isset($fcS[$k]['m'][$mm])) $fcS[$k]['m'][$mm] = $mkB();
            $hit = ($mm === $months[0]) ? ($b === $mm || $b === 'overdue') : ($b === $mm);
            if ($hit) { $X = &$fcS[$k]['m'][$mm]; $X['n']++; $X['pipe'] += $L['v']; $X['weighted'] += $w; if ($prob >= 70) $X['commit'] += $L['v']; if ($prob >= 40) $X['best'] += $L['v']; unset($X); }
        }
        if ($b !== 'none' && $b !== 'later') $deals[] = ['num' => $L['num'], 'lead' => $L['name'], 'company' => $L['company'], 'sales' => $sname($k), 'st' => $L['st'],
            'st_label' => (string)($pc[$L['st']]['label'] ?? $L['st']), 'prob' => $prob, 'v' => $L['v'], 'weighted' => (int)round($w), 'ce' => $ce, 'overdue' => $ce < $today,
            'last' => $L['last']];
    }
    foreach ($map as $id => $x) if (!empty($x['active']) && $want((string)$id) && !isset($fcS[(string)$id])) $fcS[(string)$id] = ['id' => (string)$id, 'name' => $sname($id), 'm' => []];
    $fcRows = [];
    foreach ($fcS as $k => $R) {
        $row = ['id' => $R['id'], 'name' => $R['name'], 'months' => []];
        foreach ([$months[0], $months[1]] as $mm) {
            $X = $R['m'][$mm] ?? $mkB(); [$wn, $wv] = $wonM((string)$k, $mm);
            $tr = (int)($tg[(string)$k]['rev'] ?? 0);
            $X['weighted'] = (int)round($X['weighted']); $X['won_n'] = $wn; $X['won'] = $wv; $X['target'] = $tr;
            $X['projected'] = $wv + $X['weighted']; $X['att'] = $tr ? (int)round(($wv + $X['weighted']) * 100 / $tr) : null;
            $row['months'][$mm] = $X;
        }
        $fcRows[] = $row;
    }
    usort($fcRows, function ($a, $b) use ($months) { return $b['months'][$months[0]]['projected'] <=> $a['months'][$months[0]]['projected']; });
    foreach ($buckets as &$B) $B['weighted'] = (int)round($B['weighted']); unset($B);
    usort($deals, function ($a, $b) { return strcmp($a['ce'], $b['ce']) ?: $b['v'] <=> $a['v']; });
    $forecast = ['today' => $today, 'months' => $months, 'buckets' => array_values($buckets), 'by_sales' => $fcRows, 'deals' => array_slice($deals, 0, 300),
                 'stages' => array_map(function ($k) use ($pc) { return ['key' => $k, 'label' => $pc[$k]['label'], 'prob' => $pc[$k]['prob']]; }, $openSt)];

    // ---- funnel (kohort lead dibuat dalam periode) & win/loss
    $stKeys = array_keys($order); $reach = array_fill_keys($stKeys, 0); $lostAt = array_fill_keys(array_merge($stKeys, ['?']), 0);
    $cohort = 0; $bySrc = []; $lostList = []; $wonN = 0; $lostN = 0; $wonV = 0; $lostV = 0; $cyc = []; $stDur = []; $curSt = [];
    foreach ($leads as $L) {
        if (in_array($L['st'], $openSt, true) || in_array($L['st'], ['closed_deal', 'closed_lost'], true)) $curSt[$L['st']] = ($curSt[$L['st']] ?? 0) + 1;
        // lama di tiap tahap (dari riwayat)
        $seq = array_merge([['baru', $L['ct']]], $L['hist']);
        for ($i = 0; $i < count($seq) - 1; $i++) { $d = $seq[$i + 1][1] - $seq[$i][1]; if ($seq[$i][1] && $d >= 0) { $stDur[$seq[$i][0]][] = $d; } }
        if ($L['ct'] >= $fromTs && $L['ct'] <= $toTs) {
            $cohort++;
            $max = 0; foreach (array_merge([$L['st']], array_column($L['hist'], 0)) as $s) if (isset($order[$s])) $max = max($max, $order[$s]);
            if ($L['st'] === 'closed_lost') { $mx2 = 0; foreach (array_column($L['hist'], 0) as $s) if (isset($order[$s]) && $s !== 'closed_deal') $mx2 = max($mx2, $order[$s]); $max = $mx2; }
            foreach ($order as $s => $o) if ($o <= $max) $reach[$s]++;
            $sk = $L['src']; if (!isset($bySrc[$sk])) $bySrc[$sk] = ['key' => $sk, 'label' => $srcs[$sk] ?? ($sk === 'chat' ? 'Chat WhatsApp (AI)' : ($sk === 'tag' ? 'Chat di-tag sales' : $sk)), 'leads' => 0, 'deal' => 0, 'lost' => 0, 'open' => 0, 'deal_v' => 0, 'pipe' => 0];
            $bySrc[$sk]['leads']++;
            if ($L['st'] === 'closed_deal') { $bySrc[$sk]['deal']++; $bySrc[$sk]['deal_v'] += $L['v']; }
            elseif ($L['st'] === 'closed_lost') $bySrc[$sk]['lost']++;
            else { $bySrc[$sk]['open']++; $bySrc[$sk]['pipe'] += $L['v']; }
        }
        if (in_array($L['st'], ['closed_deal', 'closed_lost'], true) && $L['closed'] >= $fromTs && $L['closed'] <= $toTs) {
            if ($L['st'] === 'closed_deal') { $wonN++; $wonV += $L['v']; if ($L['ct'] && $L['closed'] > $L['ct']) $cyc[] = $L['closed'] - $L['ct']; }
            else {
                $lostN++; $lostV += $L['v'];
                $prev = '?'; foreach ($L['hist'] as $h) if ($h[0] !== 'closed_lost') $prev = $h[0];
                if ($prev === '?' ) $prev = 'baru';
                $lostAt[$prev] = ($lostAt[$prev] ?? 0) + 1;
                $lostList[] = ['num' => $L['num'], 'lead' => $L['name'], 'sales' => $sname($L['sid']), 'v' => $L['v'], 'at' => wibDate('Y-m-d', $L['closed']), 'stage' => (string)($pc[$prev]['label'] ?? $prev), 'reason' => mb_substr($L['note'], 0, 200)];
            }
        }
    }
    $fun = []; $prevN = null;
    foreach ($order as $s => $o) { $n = $reach[$s]; $fun[] = ['key' => $s, 'label' => (string)($pc[$s]['label'] ?? $s), 'n' => $n, 'pct' => $cohort ? (int)round($n * 100 / $cohort) : null, 'step' => ($prevN ? (int)round($n * 100 / $prevN) : null)]; $prevN = $n; }
    $dur = []; foreach ($order as $s => $o) { if ($s === 'closed_deal') continue; $x = $stDur[$s] ?? []; $dur[] = ['key' => $s, 'label' => (string)($pc[$s]['label'] ?? $s), 'n' => count($x), 'avg_d' => $x ? round(array_sum($x) / count($x) / 86400, 1) : null]; }
    $bySrc = array_values($bySrc);
    foreach ($bySrc as &$x) { $x['win'] = ($x['deal'] + $x['lost']) ? (int)round($x['deal'] * 100 / ($x['deal'] + $x['lost'])) : null; $x['conv'] = $x['leads'] ? (int)round($x['deal'] * 100 / $x['leads']) : null; } unset($x);
    usort($bySrc, function ($a, $b) { return $b['leads'] <=> $a['leads']; });
    $la = []; foreach ($lostAt as $s => $n) if ($n) $la[] = ['key' => $s, 'label' => (string)($pc[$s]['label'] ?? $s), 'n' => $n];
    $funnel = ['cohort' => $cohort, 'stages' => $fun, 'current' => $curSt, 'by_source' => $bySrc, 'stage_days' => $dur,
               'won' => $wonN, 'won_v' => $wonV, 'lost' => $lostN, 'lost_v' => $lostV, 'win' => ($wonN + $lostN) ? (int)round($wonN * 100 / ($wonN + $lostN)) : null,
               'cycle' => $cyc ? round(array_sum($cyc) / count($cyc) / 86400, 1) : null, 'lost_at' => $la, 'lost_list' => array_slice($lostList, 0, 200)];

    // ---- umur lead terbuka
    $ab = [['k' => '0-3', 'max' => 3], ['k' => '4-7', 'max' => 7], ['k' => '8-14', 'max' => 14], ['k' => '15-30', 'max' => 30], ['k' => '>30', 'max' => PHP_INT_MAX]];
    $idleB = []; foreach ($ab as $b) $idleB[$b['k']] = ['n' => 0, 'v' => 0]; $idleB['never'] = ['n' => 0, 'v' => 0];
    $ageB = []; foreach ($ab as $b) $ageB[$b['k']] = ['n' => 0, 'v' => 0];
    $stale = []; $byStage = [];
    foreach ($leads as $L) {
        if (!in_array($L['st'], $openSt, true)) continue;
        $age = $L['ct'] ? (int)floor(($now - $L['ct']) / 86400) : null;
        $lt = $L['last'] !== '' ? strtotime($L['last'] . ':00') : 0;
        $idle = $lt ? (int)floor(($now - $lt) / 86400) : null;
        if ($idle === null) { $idleB['never']['n']++; $idleB['never']['v'] += $L['v']; }
        else foreach ($ab as $b) if ($idle <= $b['max']) { $idleB[$b['k']]['n']++; $idleB[$b['k']]['v'] += $L['v']; break; }
        if ($age !== null) foreach ($ab as $b) if ($age <= $b['max']) { $ageB[$b['k']]['n']++; $ageB[$b['k']]['v'] += $L['v']; break; }
        $s = $L['st']; if (!isset($byStage[$s])) $byStage[$s] = ['key' => $s, 'label' => (string)($pc[$s]['label'] ?? $s), 'n' => 0, 'age' => 0, 'idle' => 0, 'idle_n' => 0];
        $byStage[$s]['n']++; $byStage[$s]['age'] += (int)$age; if ($idle !== null) { $byStage[$s]['idle'] += $idle; $byStage[$s]['idle_n']++; }
        $fu = null; foreach ($L['acts'] as $a) if (!empty($a['next_due']) && empty($a['next_done']) && ($fu === null || $a['next_due'] < $fu)) $fu = (string)$a['next_due'];
        $stale[] = ['num' => $L['num'], 'lead' => $L['name'], 'sales' => $sname($L['sid']), 'st_label' => (string)($pc[$s]['label'] ?? $s), 'v' => $L['v'], 'age' => $age, 'idle' => $idle, 'last' => $L['last'], 'fu' => $fu];
    }
    $bs = []; foreach ($openSt as $s) if (isset($byStage[$s])) { $x = $byStage[$s]; $bs[] = ['key' => $s, 'label' => $x['label'], 'n' => $x['n'], 'avg_age' => round($x['age'] / $x['n'], 1), 'avg_idle' => $x['idle_n'] ? round($x['idle'] / $x['idle_n'], 1) : null]; }
    usort($stale, function ($a, $b) { $ia = $a['idle'] === null ? 99999 : $a['idle']; $ib = $b['idle'] === null ? 99999 : $b['idle']; return $ib <=> $ia ?: $b['v'] <=> $a['v']; });
    $aging = ['idle' => $idleB, 'age' => $ageB, 'by_stage' => $bs, 'list' => array_slice($stale, 0, 200), 'open' => count($stale)];

    $divs = []; foreach ($map as $id => $x) { $d = trim((string)($x['div'] ?? '')); if ($d !== '' && ($only === null || in_array((string)$id, (array)$only, true))) $divs[mb_strtolower($d)] = $d; }
    $sl = []; foreach ($map as $id => $x) if ($only === null || in_array((string)$id, (array)$only, true)) $sl[] = ['id' => (string)$id, 'name' => (string)($x['name'] ?? $id), 'active' => !empty($x['active']), 'div' => (string)($x['div'] ?? '')];
    usort($sl, function ($a, $b) { return ($b['active'] <=> $a['active']) ?: strcasecmp($a['name'], $b['name']); });
    return ['from' => $fromD, 'to' => $toD, 'generated' => wibDate('Y-m-d H:i'), 'types' => $types, 'perf' => $perf, 'activity' => $activity, 'productivity' => $productivity,
            'forecast' => $forecast, 'funnel' => $funnel, 'aging' => $aging, 'sales' => $sl, 'divs' => array_values($divs), 'targets' => $tg];
}
