/* ---------- v1.2.223: laporan-pdf — laporan berkala PDF (mingguan & bulanan) via email & WhatsApp (Growth+) ----------
 * Mesin PDF: dompdf (PHP murni; jalan di cPanel & VPS) — dipasang otomatis sekali dari server pusat ke lib/dompdf-<ver>/
 *            (atau dari vendor/ composer bila sudah ada). Opsional: Chromium/Chrome headless bila tersedia di server (VPS)
 *            -> mode "auto" memakai Chromium, gagal/tidak ada -> dompdf.
 * data/report-pdf.json        pengaturan     data/report-pdf-state.json  status kirim per periode
 * data/report-pdf/<id>.pdf    arsip PDF      data/report-pdf/index.json  daftar arsip (maks. 150, 120 hari) */
if (!defined('RP_CONF_FILE')) define('RP_CONF_FILE', DATA_DIR . '/report-pdf.json');
if (!defined('RP_STATE_FILE')) define('RP_STATE_FILE', DATA_DIR . '/report-pdf-state.json');
if (!defined('RP_DIR')) define('RP_DIR', DATA_DIR . '/report-pdf');
if (!defined('RP_LIB_VER')) define('RP_LIB_VER', '3.1.4');
if (!defined('RP_LIB_SHA256')) define('RP_LIB_SHA256', '__RP_LIB_SHA256__');
if (!defined('RP_MAX_ATTACH')) define('RP_MAX_ATTACH', 3 * 1024 * 1024);   // > ini: email tanpa lampiran, hanya tautan unduh
if (!defined('RP_LINK_DAYS')) define('RP_LINK_DAYS', 30);
function rpOk223() { return slPlanOk(); }
function rpGuard223() {
    if (!rpOk223()) jsonOut(['ok' => false, 'locked' => true, 'error' => 'Laporan Berkala PDF tersedia mulai paket Growth. Hubungi ' . deiBrandVendor() . ' untuk upgrade paket.'], 403);
}
// key => [judul, butuh CRM, boleh untuk laporan Sales]
function rpSections223() {
    return ['chat' => ['Ringkasan Chat & Sumber Lead', false, false], 'service' => ['Kinerja Layanan', false, false], 'agent' => ['Kinerja per Agent', false, false],
            'sales' => ['Performa Sales & Target', true, true], 'pipeline' => ['Pipeline, Forecast & Umur Lead', true, true], 'task' => ['Rekap Task', false, true],
            'topic' => ['Topik Chat', false, false], 'usage' => ['Penggunaan & Kuota', false, false]];
}
function rpConf223() {
    $c = readJson(RP_CONF_FILE, []); if (!is_array($c)) $c = [];
    $all = array_keys(rpSections223());
    $sec = function ($v, $def) use ($all) { $v = is_array($v) ? array_values(array_intersect($all, array_map('strval', $v))) : $def; return $v ?: $def; };
    $w = is_array($c['weekly'] ?? null) ? $c['weekly'] : []; $m = is_array($c['monthly'] ?? null) ? $c['monthly'] : [];
    $em = []; foreach ((array)($c['extra_email'] ?? []) as $e) { $e = deiValidEmail($e); if ($e !== '' && !in_array($e, $em, true)) $em[] = $e; }
    $wa = []; foreach ((array)($c['extra_wa'] ?? []) as $n) { $n = ntfNum222($n); if ($n !== '' && !in_array($n, $wa, true)) $wa[] = $n; }
    $via = (string)($c['via'] ?? 'email'); $eng = (string)($c['engine'] ?? 'auto');
    return ['weekly' => ['on' => !empty($w['on']), 'dow' => max(1, min(7, (int)($w['dow'] ?? 1))), 'hour' => max(0, min(23, (int)($w['hour'] ?? 8))),
                         'sections' => $sec($w['sections'] ?? null, ['chat', 'service', 'sales', 'task'])],
            'monthly' => ['on' => !empty($m['on']), 'dom' => max(1, min(28, (int)($m['dom'] ?? 1))), 'hour' => max(0, min(23, (int)($m['hour'] ?? 8))),
                          'sections' => $sec($m['sections'] ?? null, $all)],
            'to_admins' => !array_key_exists('to_admins', $c) || !empty($c['to_admins']), 'to_spv' => !empty($c['to_spv']),
            'to_sales' => !array_key_exists('to_sales', $c) || !empty($c['to_sales']),
            'extra_email' => array_slice($em, 0, 10), 'extra_wa' => array_slice($wa, 0, 10),
            'via' => in_array($via, ['email', 'wa', 'both'], true) ? $via : 'email',
            'engine' => in_array($eng, ['auto', 'dompdf', 'chrome'], true) ? $eng : 'auto',
            'chrome_bin' => mb_substr(trim((string)($c['chrome_bin'] ?? '')), 0, 200),
            'updated_at' => (string)($c['updated_at'] ?? ''), 'updated_by' => (string)($c['updated_by'] ?? '')];
}
/* ---------- periode ---------- */
// $kind weekly|monthly; $ts = waktu acuan (sekarang). Hasil: [key, from, to, label]
function rpPeriod223($kind, $cf, $ts = null) {
    $ts = $ts ?? time();
    if ($kind === 'monthly') {
        $y = (int)wibDate('Y', $ts); $m = (int)wibDate('n', $ts) - 1; if ($m < 1) { $m = 12; $y--; }
        $from = sprintf('%04d-%02d-01', $y, $m); $to = wibDate('Y-m-d', wibDayStart(wibDate('Y-m-01', $ts)) - 86400);
        return [wibDate('Y-m', $ts), $from, $to, rpMonthName223($m) . ' ' . $y];
    }
    // minggu ISO berjalan: hari kirim terjadwal = Senin + (dow-1); periode = 7 hari sebelum hari kirim
    $mon = wibDayStart(wibDate('Y-m-d', $ts)) - ((int)wibDate('N', $ts) - 1) * 86400;
    $send = $mon + ($cf['weekly']['dow'] - 1) * 86400;
    $from = wibDate('Y-m-d', $send - 7 * 86400); $to = wibDate('Y-m-d', $send - 86400);
    return [wibDate('o-\WW', $ts), $from, $to, rpDateId223($from) . ' – ' . rpDateId223($to)];
}
function rpPrevRange223($from, $to, $kind) {
    if ($kind === 'monthly') {
        $a = wibDayStart($from); $pt = wibDate('Y-m-d', $a - 86400);
        return [substr($pt, 0, 8) . '01', $pt];
    }
    $a = wibDayStart($from); $b = wibDayStart($to); $n = (int)round(($b - $a) / 86400) + 1;
    return [wibDate('Y-m-d', $a - $n * 86400), wibDate('Y-m-d', $a - 86400)];
}
function rpDue223($kind, $cf, $ts = null) {
    $ts = $ts ?? time(); $p = $cf[$kind];
    if (empty($p['on'])) return false;
    $day = $kind === 'monthly' ? (int)wibDate('j', $ts) : (int)wibDate('N', $ts);
    $want = $kind === 'monthly' ? $p['dom'] : $p['dow'];
    return $day > $want || ($day === $want && (int)wibDate('G', $ts) >= $p['hour']);
}
function rpMonthName223($m) { return ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'][(int)$m] ?? ''; }
function rpDateId223($ymd) {
    $p = explode('-', (string)$ymd); if (count($p) !== 3) return (string)$ymd;
    return (int)$p[2] . ' ' . mb_substr(rpMonthName223((int)$p[1]), 0, 3) . ' ' . $p[0];
}
/* ---------- penerima ---------- */
// [[key, nama, email, wa, scope(null|array sid), username, role]]
function rpRecipients223($cf, $onlyUser = '') {
    $out = []; $seen = [];
    foreach ((array)readJson(USERS_FILE, []) as $x) {
        if (!is_array($x) || empty($x['username']) || !empty($x['internal'])) continue;
        $un = (string)$x['username']; if ($onlyUser !== '' && $un !== $onlyUser) continue;
        $r = (string)($x['role'] ?? ''); $nm = trim((string)($x['name'] ?? '')) ?: $un;
        $scope = null;
        if (in_array($r, ['super_admin', 'admin'], true)) { if (!$cf['to_admins'] && $onlyUser === '') continue; }
        elseif ($r === 'supervisor') { if (!$cf['to_spv'] && $onlyUser === '') continue; }
        elseif ($r === 'sales') {
            if ((!$cf['to_sales'] && $onlyUser === '') || !crmOk215() || (string)($x['sales_id'] ?? '') === '') continue;
            $scope = crmSalesVisible219($x); if ($scope === null) $scope = array_keys(slMap()); $scope = array_values(array_map('strval', (array)$scope)); sort($scope);
        } else continue;
        $out[] = ['u:' . $un, $nm, deiUserEmail($x), ntfUserWa222($x), $scope, $un, $r]; $seen['u:' . $un] = 1;
    }
    if ($onlyUser === '') {
        foreach ($cf['extra_email'] as $e) $out[] = ['e:' . $e, $e, $e, '', null, '', ''];
        foreach ($cf['extra_wa'] as $n) $out[] = ['w:' . $n, $n, '', $n, null, '', ''];
    }
    return $out;
}
// Saluran kirim untuk satu penerima: ['email'=>bool,'wa'=>bool]
function rpChannels223($cf, $R, $waOk) {
    $em = $R[2] !== ''; $wa = $R[3] !== '' && $waOk;
    $wantE = in_array($cf['via'], ['email', 'both'], true); $wantW = in_array($cf['via'], ['wa', 'both'], true);
    $e = $wantE && $em; $w = $wantW && $wa;
    if (!$e && !$w) { if ($em) $e = true; elseif ($wa) $w = true; }   // cadangan: kirim lewat yang tersedia
    return ['email' => $e, 'wa' => $w];
}
function rpWaReady223() {   // [bool, alasan]
    if (!ntfActive222()) return [false, 'Notifikasi Tim via WhatsApp belum aktif (Widget & API).'];
    [$w, $err] = ntfSender222();
    return $w ? [true, ''] : [false, $err];
}
/* ---------- data ---------- */
function rpChatData223($fromD, $toD) {
    $fromTs = wibDayStart($fromD); $toTs = wibDayStart($toD);
    $daily = []; for ($d = $fromTs; $d <= $toTs; $d += 86400) $daily[wibDate('Y-m-d', $d)] = ['date' => wibDate('Y-m-d', $d), 'msgs' => 0, 'cust' => [], 'leads' => 0];
    $msgs = ['total' => 0, 'wa' => 0, 'web' => 0, 'ai_errors' => 0]; $uniq = []; $waNums = [];
    $src = []; $cmp = [];
    foreach (logIter($fromD, $toD) as $l) {
        if (!is_array($l) || in_array(($l['dir'] ?? ''), ['manual', 'closing'], true)) continue;
        $d = substr((string)($l['ts'] ?? ''), 0, 10); if (!isset($daily[$d])) continue;
        $wa = ((string)($l['channel'] ?? '')) === 'whatsapp';
        $msgs['total']++; $msgs[$wa ? 'wa' : 'web']++; if (!empty($l['ai_error'])) $msgs['ai_errors']++;
        $daily[$d]['msgs']++;
        $who = (string)($l['ip'] ?? ''); if ($who === '' || !empty($l['grp'])) continue;
        $k = ($wa ? 'w:' : 's:') . $who; $uniq[$k] = 1; $daily[$d]['cust'][$k] = 1;
        if ($wa) $waNums[$who] = 1;
        $s = (string)($l['utm_source'] ?? ''); $s = $s !== '' ? $s : ($wa ? 'WhatsApp langsung' : 'Website langsung');
        $src[$s][$k] = 1;
        $c = (string)deiWaCmp($l); if ($c !== '') $cmp[$c][$k] = 1;
    }
    $cnt = function ($a) { $o = []; foreach ($a as $k => $v) $o[] = ['label' => (string)$k, 'n' => count($v)]; usort($o, function ($x, $y) { return $y['n'] <=> $x['n']; }); return array_slice($o, 0, 8); };
    $ld = ['new' => 0, 'open' => 0];
    foreach (leadsGetAll() as $L) {
        if (!is_array($L)) continue;
        if (in_array((string)($L['status'] ?? 'baru'), crmOpenStatuses216(), true)) $ld['open']++;
        $cd = substr((string)($L['created_at'] ?? ''), 0, 10);
        if (isset($daily[$cd])) { $ld['new']++; $daily[$cd]['leads']++; }
    }
    foreach ($daily as &$x) $x['cust'] = count($x['cust']); unset($x);
    return ['msgs' => $msgs, 'customers' => count($uniq), 'wa_nums' => array_keys($waNums), 'daily' => array_values($daily), 'sources' => $cnt($src), 'campaigns' => $cnt($cmp), 'leads' => $ld];
}
function rpConvData223($fromD, $toD) {
    $fromTs = wibDayStart($fromD); $toEnd = wibDayStart($toD) + 86399;
    $chL = []; foreach (waChannels(getSettings()) as $x) $chL[(string)$x['id']] = (string)$x['label'];
    $cs = convStats(convStoreRange($fromTs, $toEnd), $fromTs, $toEnd, $chL);
    $names = []; foreach ((array)readJson(USERS_FILE, []) as $u) if (is_array($u)) $names[$u['username'] ?? ''] = $u['name'] ?? ($u['username'] ?? '');
    foreach ($cs['agents'] as &$a) $a['name'] = $names[$a['agent']] ?? $a['agent']; unset($a);
    return $cs;
}
function rpTaskData223($fromD, $toD, $onlyUser = null) {
    $fromTs = wibDayStart($fromD); $toTs = wibDayStart($toD) + 86399; $today = wibToday();
    $nm = []; foreach ((array)readJson(USERS_FILE, []) as $u) if (is_array($u)) $nm[(string)($u['username'] ?? '')] = (string)($u['name'] ?? $u['username'] ?? '');
    $st = array_fill_keys(tkStatuses214(), 0); $T = ['created' => 0, 'done' => 0, 'overdue' => 0, 'open' => 0]; $per = []; $late = [];
    foreach (tkAll214() as $t) {
        if (!is_array($t)) continue;
        $as = (string)($t['assignee'] ?? '');
        if ($onlyUser !== null && $as !== $onlyUser) continue;
        $s = (string)($t['status'] ?? 'new'); if (isset($st[$s])) $st[$s]++;
        $k = $as; if (!isset($per[$k])) $per[$k] = ['name' => $as === '' ? 'Belum ditugaskan' : ($nm[$as] ?? $as), 'open' => 0, 'overdue' => 0, 'created' => 0, 'done' => 0];
        $ct = strtotime((string)($t['created_at'] ?? '')); if ($ct && $ct >= $fromTs && $ct <= $toTs) { $T['created']++; $per[$k]['created']++; }
        $dn = false; foreach ((array)($t['log'] ?? []) as $g) { if (in_array((string)($g['s'] ?? ''), ['done', 'closed'], true)) { $gt = strtotime((string)($g['at'] ?? '')); if ($gt && $gt >= $fromTs && $gt <= $toTs) $dn = true; } }
        if ($dn) { $T['done']++; $per[$k]['done']++; }
        if (!in_array($s, ['done', 'closed'], true)) {
            $T['open']++; $per[$k]['open']++;
            $due = (string)($t['due'] ?? '');
            if ($due !== '' && $due < $today) { $T['overdue']++; $per[$k]['overdue']++; $late[] = ['title' => mb_substr((string)($t['title'] ?? ''), 0, 90), 'who' => $per[$k]['name'], 'due' => $due]; }
        }
    }
    usort($late, function ($a, $b) { return strcmp($a['due'], $b['due']); });
    $per = array_values(array_filter($per, function ($r) { return $r['open'] || $r['created'] || $r['done']; }));
    usort($per, function ($a, $b) { return $b['open'] <=> $a['open'] ?: $b['done'] <=> $a['done']; });
    return ['total' => $T, 'status' => $st, 'per' => array_slice($per, 0, 25), 'late' => array_slice($late, 0, 12)];
}
function rpPipeData223($scope = null) {
    $pc = crmPipeConf216(); $open = crmOpenStatuses216(); $contacts = waGetContacts(); $rows = [];
    foreach ($open as $s) $rows[$s] = ['label' => (string)($pc[$s]['label'] ?? $s), 'prob' => (int)($pc[$s]['prob'] ?? 0), 'n' => 0, 'v' => 0, 'w' => 0];
    foreach (leadsGetAll() as $num => $l) {
        if (!is_array($l)) continue;
        $s = (string)($l['status'] ?? 'baru'); if (!isset($rows[$s])) continue;
        if ($scope !== null && !in_array((string)slLeadSalesId($l, (string)$num, $contacts), $scope, true)) continue;
        $v = (int)($l['value'] ?? 0); $rows[$s]['n']++; $rows[$s]['v'] += $v; $rows[$s]['w'] += $v * $rows[$s]['prob'] / 100;
    }
    foreach ($rows as &$r) $r['w'] = (int)round($r['w']); unset($r);
    return array_values($rows);
}
function rpTopicData223($waNums) {
    if (!tpActive()) return null;
    $map = tpTopicMap(); $cnt = []; $div = []; $none = 0; $c = waGetContacts();
    foreach ($waNums as $n) {
        $tp = $c[$n]['tp'] ?? null; $m = is_array($tp) ? (string)($tp['m'] ?? '') : '';
        if ($m === '' || !isset($map[$m])) { $none++; continue; }
        $cnt[$m] = ($cnt[$m] ?? 0) + 1; $d = (string)($map[$m]['div'] ?? ''); if ($d !== '') $div[$d] = ($div[$d] ?? 0) + 1;
    }
    arsort($cnt); arsort($div); $o = []; $od = [];
    foreach ($cnt as $k => $n) $o[] = ['label' => (string)($map[$k]['name'] ?? $k), 'div' => (string)($map[$k]['div'] ?? ''), 'n' => $n];
    foreach ($div as $k => $n) $od[] = ['label' => (string)$k, 'n' => $n];
    return ['topics' => array_slice($o, 0, 12), 'divs' => array_slice($od, 0, 8), 'none' => $none, 'total' => count($waNums)];
}
function rpUsageData223($fromD, $toD) {
    $u = readJson(DATA_DIR . '/usage.json', []); $calls = 0;
    foreach ((array)$u as $d => $x) if ($d >= $fromD && $d <= $toD && is_array($x)) $calls += (int)($x['calls'] ?? 0);
    $cap = readJson(CAP_CACHE_FILE, []); $lic = readJson(DATA_DIR . '/license-cache.json', []);
    return ['ai_calls' => $calls, 'tier' => (string)($cap['tier'] ?? ''), 'cap' => (int)($cap['cap'] ?? 0), 'used' => (int)($cap['used'] ?? 0), 'pct' => (float)($cap['pct'] ?? 0),
            'expires' => (string)($lic['expires_at'] ?? ''), 'days_left' => isset($lic['days_left']) ? (int)$lic['days_left'] : null];
}
// Kumpulkan data satu laporan. $V = ['scope' => null|array sid, 'user' => username untuk task (Sales)]
function rpData223($kind, $fromD, $toD, $sections, $V = []) {
    $scope = $V['scope'] ?? null; $sales = $scope !== null;
    $defs = rpSections223(); $crm = crmOk215(); $want = [];
    foreach ($sections as $k) { if (!isset($defs[$k]) || ($defs[$k][1] && !$crm) || ($sales && !$defs[$k][2])) continue; $want[] = $k; }
    $s = getSettings(); [$pf, $pt] = rpPrevRange223($fromD, $toD, $kind);
    $D = ['kind' => $kind, 'from' => $fromD, 'to' => $toD, 'prev' => [$pf, $pt], 'sections' => $want, 'biz' => deiTenantName($s), 'brand' => deiBrandProduct(),
          'color' => preg_match('/^#[0-9a-f]{6}$/i', (string)($s['appearance']['primary_color'] ?? '')) ? (string)$s['appearance']['primary_color'] : '#140383',
          'for' => (string)($V['for'] ?? ''), 'own' => $sales, 'generated' => deiWibNow(), 'dash' => crmDashUrl215()];
    $needChat = !$sales && array_intersect($want, ['chat', 'topic']);
    if ($needChat) { $D['chat'] = rpChatData223($fromD, $toD); $pc = rpChatData223($pf, $pt); $D['chat_prev'] = ['msgs' => $pc['msgs']['total'], 'customers' => $pc['customers'], 'leads' => $pc['leads']['new']]; }
    if (!$sales && array_intersect($want, ['service', 'agent'])) {
        $D['conv'] = rpConvData223($fromD, $toD);
        $pv = rpConvData223($pf, $pt); $D['conv_prev'] = ['total' => $pv['totals']['total'], 'resolved_rate' => $pv['avg']['resolved_rate'], 'frt' => $pv['avg']['frt']];
    }
    if (array_intersect($want, ['sales', 'pipeline'])) {
        $D['crm'] = crmRep221($fromD, $toD, $scope);
        $pr = crmPerf217($pf, $pt, $scope); $D['crm_prev'] = $pr ? $pr['total'] : null;
        if (in_array('pipeline', $want, true)) $D['pipe'] = rpPipeData223($scope);
    }
    if (in_array('task', $want, true)) $D['task'] = rpTaskData223($fromD, $toD, $sales ? (string)($V['user'] ?? '-') : null);
    if (in_array('topic', $want, true)) { $D['topic'] = rpTopicData223($D['chat']['wa_nums'] ?? []); if ($D['topic'] === null) $D['sections'] = array_values(array_diff($D['sections'], ['topic'])); }
    if (in_array('usage', $want, true)) $D['usage'] = rpUsageData223($fromD, $toD);
    return $D;
}
/* ---------- HTML (satu templat untuk dompdf & Chromium: tabel, tanpa flex/grid) ---------- */
function rpNum223($n) { return number_format((float)$n, 0, ',', '.'); }
function rpRp223($n) {
    $n = (float)$n; $a = abs($n);
    if ($a >= 1e9) return 'Rp ' . str_replace('.', ',', rtrim(rtrim(number_format($n / 1e9, 2, '.', ''), '0'), '.')) . ' M';
    if ($a >= 1e6) return 'Rp ' . str_replace('.', ',', rtrim(rtrim(number_format($n / 1e6, 1, '.', ''), '0'), '.')) . ' jt';
    return 'Rp ' . number_format($n, 0, ',', '.');
}
function rpDur223($sec) {
    if ($sec === null) return '—';
    $sec = (int)$sec; if ($sec < 60) return $sec . ' dtk';
    if ($sec < 3600) return intdiv($sec, 60) . ' mnt' . ($sec % 60 && $sec < 600 ? ' ' . ($sec % 60) . ' dtk' : '');
    if ($sec < 86400) return intdiv($sec, 3600) . ' jam' . (intdiv($sec % 3600, 60) ? ' ' . intdiv($sec % 3600, 60) . ' mnt' : '');
    return str_replace('.', ',', (string)round($sec / 86400, 1)) . ' hari';
}
function rpDelta223($cur, $prev, $lowerBetter = false) {
    if ($prev === null || $cur === null) return '';
    $cur = (float)$cur; $prev = (float)$prev;
    if ($prev == 0) return $cur > 0 ? '<span class="up">baru</span>' : '';
    $p = (int)round(($cur - $prev) * 100 / abs($prev)); if ($p === 0) return '<span class="flat">= periode lalu</span>';
    $good = $lowerBetter ? $p < 0 : $p > 0;
    return '<span class="' . ($good ? 'up' : 'down') . '">' . ($p > 0 ? '▲ ' : '▼ ') . abs($p) . '%</span>';
}
function rpHtml223($D) {
    $e = function ($x) { return htmlspecialchars((string)$x, ENT_QUOTES, 'UTF-8'); };
    $C = $D['color']; $kindL = $D['kind'] === 'monthly' ? 'Bulanan' : ($D['kind'] === 'weekly' ? 'Mingguan' : '');
    $per = rpDateId223($D['from']) . ' – ' . rpDateId223($D['to']);
    $tile = function ($label, $val, $sub = '') use ($e) { return '<td class="tile"><div class="tl">' . $e($label) . '</div><div class="tv">' . $val . '</div>' . ($sub !== '' ? '<div class="ts">' . $sub . '</div>' : '') . '</td>'; };
    $tiles = function ($arr) { $h = '<table class="tiles"><tr>'; foreach ($arr as $i => $t) { if ($i && $i % 3 === 0) $h .= '</tr><tr>'; $h .= $t; } $n = count($arr) % 3; if ($n) $h .= str_repeat('<td class="tile blank"></td>', 3 - $n); return $h . '</tr></table>'; };
    $bars = function ($rows, $lab = 'label', $val = 'n', $fmt = null) use ($e, $C) {
        if (!$rows) return '<p class="muted">Belum ada data.</p>';
        $mx = 0; foreach ($rows as $r) $mx = max($mx, (float)$r[$val]);
        $h = '<table class="bars">';
        foreach ($rows as $r) {
            $w = ($mx > 0 && (float)$r[$val] > 0) ? max(1, (int)round((float)$r[$val] * 100 / $mx)) : 0;
            $h .= '<tr><td class="bl">' . $e($r[$lab]) . '</td><td class="bb">' . ($w ? '<table class="bt"><tr><td style="width:' . $w . '%;background:' . $C . '"></td>' . ($w < 100 ? '<td></td>' : '') . '</tr></table>' : '') . '</td><td class="bv">' . ($fmt ? $fmt($r[$val]) : rpNum223($r[$val])) . '</td></tr>';
        }
        return $h . '</table>';
    };
    $tbl = function ($head, $rows, $num = []) use ($e) {
        $h = '<table class="t"><thead><tr>'; foreach ($head as $i => $x) $h .= '<th' . (in_array($i, $num, true) ? ' class="n"' : '') . '>' . $e($x) . '</th>'; $h .= '</tr></thead><tbody>';
        foreach ($rows as $r) { $h .= '<tr>'; foreach (array_values($r) as $i => $x) $h .= '<td' . (in_array($i, $num, true) ? ' class="n"' : '') . '>' . $x . '</td>'; $h .= '</tr>'; }
        return $h . '</tbody></table>';
    };
    $out = [];
    $sec = rpSections223();
    foreach ($D['sections'] as $k) {
        $h = '<div class="sec' . (in_array($k, ['agent', 'topic', 'usage'], true) ? ' keep' : '') . '"><div class="keep"><h2>' . $e($sec[$k][0]) . '</h2>';
        if ($k === 'chat' && isset($D['chat'])) {
            $c = $D['chat']; $p = $D['chat_prev'];
            $h .= $tiles([$tile('Pelanggan chat', rpNum223($c['customers']), rpDelta223($c['customers'], $p['customers'])),
                          $tile('Pesan masuk', rpNum223($c['msgs']['total']), 'WA ' . rpNum223($c['msgs']['wa']) . ' · Web ' . rpNum223($c['msgs']['web']) . ' ' . rpDelta223($c['msgs']['total'], $p['msgs'])),
                          $tile('Lead baru', rpNum223($c['leads']['new']), rpDelta223($c['leads']['new'], $p['leads']) . ' · terbuka ' . rpNum223($c['leads']['open']))]);
            // grafik harian (kolom)
            $mx = 1; foreach ($c['daily'] as $d) $mx = max($mx, $d['cust']);
            $n = count($c['daily']); $lw = $n > 16 ? 2 : 1;
            $h .= '<h3>Pelanggan chat per hari</h3><table class="cols"><tr>';
            foreach ($c['daily'] as $d) { $ht = (int)round($d['cust'] * 70 / $mx); $h .= '<td class="cv"><div class="cn">' . ($d['cust'] ?: '') . '</div><div class="cb" style="height:' . max($d['cust'] ? 2 : 0, $ht) . 'px;background:' . $C . '"></div></td>'; }
            $h .= '</tr><tr>';
            foreach ($c['daily'] as $i => $d) $h .= '<td class="cd">' . (($i % $lw === 0) ? (int)substr($d['date'], 8, 2) : '') . '</td>';
            $h .= '</tr></table>';
            $h .= '<table class="two"><tr><td><h3>Sumber pelanggan</h3>' . $bars($c['sources']) . '</td><td><h3>Campaign / iklan</h3>' . ($c['campaigns'] ? $bars($c['campaigns']) : '<p class="muted">Belum ada chat dari campaign atau iklan.</p>') . '</td></tr></table>';
        } elseif ($k === 'service' && isset($D['conv'])) {
            $T = $D['conv']['totals']; $A = $D['conv']['avg']; $M = $D['conv']['med']; $p = $D['conv_prev'];
            $h .= $tiles([$tile('Percakapan', rpNum223($T['total']), rpDelta223($T['total'], $p['total'])),
                          $tile('Diselesaikan', $A['resolved_rate'] === null ? '—' : str_replace('.', ',', (string)$A['resolved_rate']) . '%', rpNum223($T['resolved']) . ' selesai ' . rpDelta223($A['resolved_rate'], $p['resolved_rate'])),
                          $tile('Respon pertama', rpDur223($A['frt']), 'median ' . rpDur223($M['frt'] ?? null) . ' ' . rpDelta223($A['frt'], $p['frt'], true)),
                          $tile('Ditangani AI', rpNum223($T['bot_handled']), ($A['bot_rate'] === null ? '' : 'selesai oleh AI ' . str_replace('.', ',', (string)$A['bot_rate']) . '%')),
                          $tile('Diteruskan ke agent', rpNum223($T['to_agent']), $A['handover_rate'] === null ? '' : str_replace('.', ',', (string)$A['handover_rate']) . '% dari chat AI'),
                          $tile('Belum ditangani agent', rpNum223($T['unassigned']), 'sedang berjalan ' . rpNum223($T['in_progress']))]);
            $RL = ['keyword' => 'Kata kunci handoff', 'ai_limit' => 'Batas balasan AI', 'ai_fail' => 'AI gagal menjawab', 'manual_mode' => 'Mode Manual', 'mode_human' => 'Nomor mode manusia', 'takeover' => 'Diambil alih admin', 'agent_reply' => 'Agent langsung membalas', 'assign' => 'Di-assign admin/routing', 'claimed' => 'Dipegang agent', 'escalation' => 'Eskalasi darurat', 'outbound' => 'Agent memulai chat', 'lainnya' => 'Lainnya'];
            $rs = []; foreach (array_slice((array)$D['conv']['handover_reasons'], 0, 6, true) as $r => $n) $rs[] = ['label' => $RL[$r] ?? (string)$r, 'n' => $n];
            $ch = []; foreach ($D['conv']['channels'] as $x) $ch[] = [$e($x['label'] ?: $x['ch']), rpNum223($x['total']), rpNum223($x['resolved']), rpNum223($x['unassigned']), rpDur223($x['frt'])];
            $h .= '<table class="two"><tr><td><h3>Alasan diteruskan ke agent</h3>' . ($rs ? $bars($rs) : '<p class="muted">Tidak ada.</p>') . '</td><td><h3>Per nomor / channel</h3>' . ($ch ? $tbl(['Channel', 'Chat', 'Selesai', 'Belum', 'Respon'], $ch, [1, 2, 3]) : '<p class="muted">Belum ada data.</p>') . '</td></tr></table>';
        } elseif ($k === 'agent' && isset($D['conv'])) {
            $rows = []; foreach (array_slice($D['conv']['agents'], 0, 25) as $a) $rows[] = ['<b>' . $e($a['name']) . '</b>', rpNum223($a['assigned']), rpNum223($a['resolved']), rpNum223($a['in_progress']), rpDur223($a['frt']), rpDur223($a['resp']), rpDur223($a['resolution'])];
            $h .= $rows ? $tbl(['Agent', 'Ditangani', 'Selesai', 'Berjalan', 'Respon pertama', 'Respon rata-rata', 'Lama selesai'], $rows, [1, 2, 3]) : '<p class="muted">Belum ada chat yang ditangani agent di periode ini.</p>';
        } elseif ($k === 'sales' && isset($D['crm'])) {
            $P = $D['crm']['perf']; $T = $P['total']; $p = $D['crm_prev'];
            $tg = $T['target'] ?? null;
            $h .= $tiles([$tile('Close Deal', rpRp223($T['deal_v']), rpNum223($T['deal']) . ' deal ' . rpDelta223($T['deal_v'], $p['deal_v'] ?? null)),
                          $tile('Win rate', $T['win'] === null ? '—' : $T['win'] . '%', rpNum223($T['deal']) . ' deal · ' . rpNum223($T['lost']) . ' lose'),
                          $tile('Lead baru', rpNum223($T['new']), rpDelta223($T['new'], $p['new'] ?? null)),
                          $tile('Aktivitas sales', rpNum223($T['acts']), 'follow-up selesai ' . rpNum223($T['fu_done']) . ' ' . rpDelta223($T['acts'], $p['acts'] ?? null)),
                          $tile('Pipeline terbuka', rpRp223($T['open_v']), rpNum223($T['open']) . ' lead · tertimbang ' . rpRp223($T['weighted'])),
                          $tile('Target omzet', $tg && !empty($tg['rev']) ? ($T['att_rev'] ?? 0) . '%' : '—', $tg && !empty($tg['rev']) ? rpRp223($T['deal_v']) . ' dari ' . rpRp223($tg['rev']) : 'target belum diisi')]);
            $rows = [];
            foreach (array_slice($P['rows'], 0, 30) as $R) {
                $t = $R['target'] ?? null;
                $rows[] = ['<b>' . $e($R['name']) . '</b>', rpNum223($R['new']), rpNum223($R['acts']), rpNum223($R['po']), rpNum223($R['deal']), rpRp223($R['deal_v']), $R['win'] === null ? '—' : $R['win'] . '%',
                           $t && !empty($t['rev']) ? ($R['att_rev'] ?? 0) . '%' : '—', ($R['fu_late'] ? '<span class="down">' . $R['fu_late'] . '</span>' : '0'), rpRp223($R['open_v'])];
            }
            if (!$D['own'] || count($rows) > 1) $h .= $tbl(['Sales', 'Lead', 'Aktivitas', 'PO', 'Deal', 'Nilai deal', 'Win', 'Target', 'FU telat', 'Pipeline'], $rows, [1, 2, 3, 4, 5, 6, 7, 8, 9]);
            $ty = []; foreach ((array)($T['by_type'] ?? []) as $k2 => $n) $ty[] = ['label' => (string)($P['types'][$k2] ?? $k2), 'n' => $n];
            usort($ty, function ($a, $b) { return $b['n'] <=> $a['n']; });
            $fs = []; foreach (array_slice((array)($D['crm']['funnel']['by_source'] ?? []), 0, 6) as $x) $fs[] = [$e($x['label']), rpNum223($x['leads']), rpNum223($x['deal']), $x['conv'] === null ? '—' : $x['conv'] . '%'];
            $h .= '<table class="two"><tr><td><h3>Jenis aktivitas</h3>' . $bars($ty) . '</td><td><h3>Sumber lead (dibuat dalam periode)</h3>' . ($fs ? $tbl(['Sumber', 'Lead', 'Deal', 'Konversi'], $fs, [1, 2, 3]) : '<p class="muted">Belum ada lead baru.</p>') . '</td></tr></table>';
        } elseif ($k === 'pipeline' && isset($D['crm'])) {
            $pp = $D['pipe'] ?? []; $rows = []; $tn = 0; $tv = 0; $tw = 0;
            foreach ($pp as $r) { $rows[] = [$e($r['label']), $r['prob'] . '%', rpNum223($r['n']), rpRp223($r['v']), rpRp223($r['w'])]; $tn += $r['n']; $tv += $r['v']; $tw += $r['w']; }
            $rows[] = ['<b>Total</b>', '', '<b>' . rpNum223($tn) . '</b>', '<b>' . rpRp223($tv) . '</b>', '<b>' . rpRp223($tw) . '</b>'];
            $fb = []; foreach ((array)($D['crm']['forecast']['buckets'] ?? []) as $b) { if (!$b['n']) continue; $lb = preg_match('/^\d{4}-\d{2}$/', $b['label']) ? rpMonthName223((int)substr($b['label'], 5)) . ' ' . substr($b['label'], 0, 4) : $b['label']; $fb[] = [$e($lb), rpNum223($b['n']), rpRp223($b['pipe']), rpRp223($b['weighted']), rpRp223($b['commit'])]; }
            $h .= '<table class="two"><tr><td><h3>Lead terbuka per tahap (saat ini)</h3>' . $tbl(['Tahap', 'Peluang', 'Lead', 'Nilai', 'Tertimbang'], $rows, [1, 2, 3, 4]) . '</td><td><h3>Perkiraan closing</h3>' . ($fb ? $tbl(['Bulan', 'Lead', 'Nilai', 'Tertimbang', 'Commit'], $fb, [1, 2, 3, 4]) : '<p class="muted">Belum ada perkiraan tanggal closing.</p>') . '</td></tr></table>';
            $idle = (array)($D['crm']['aging']['idle'] ?? []); $ib = [];
            $lbl = ['0-3' => '0–3 hari', '4-7' => '4–7 hari', '8-14' => '8–14 hari', '15-30' => '15–30 hari', '>30' => '> 30 hari', 'never' => 'Belum pernah'];
            foreach ($lbl as $kk => $l2) if (isset($idle[$kk])) $ib[] = ['label' => $l2, 'n' => (int)$idle[$kk]['n']];
            $st = []; foreach (array_slice((array)($D['crm']['aging']['list'] ?? []), 0, 8) as $x) if (($x['idle'] ?? 0) >= 7 || $x['idle'] === null) $st[] = [$e($x['lead']), $e($x['sales']), $e($x['st_label']), rpRp223($x['v']), $x['idle'] === null ? 'belum pernah' : $x['idle'] . ' hari'];
            $h .= '<table class="two"><tr><td><h3>Lead terbuka menurut terakhir dihubungi</h3>' . $bars($ib) . '</td><td><h3>Perlu ditindaklanjuti (≥ 7 hari tanpa aktivitas)</h3>' . ($st ? $tbl(['Lead', 'Sales', 'Tahap', 'Nilai', 'Diam'], $st, [3]) : '<p class="muted">Semua lead terbuka masih aktif dihubungi.</p>') . '</td></tr></table>';
        } elseif ($k === 'task' && isset($D['task'])) {
            $T = $D['task']['total']; $S = $D['task']['status'];
            $h .= $tiles([$tile('Task baru', rpNum223($T['created']), 'dibuat dalam periode'), $tile('Selesai', rpNum223($T['done']), 'Done/Closed dalam periode'),
                          $tile('Terbuka saat ini', rpNum223($T['open']), ($T['overdue'] ? '<span class="down">' . rpNum223($T['overdue']) . ' lewat jatuh tempo</span>' : 'tidak ada yang terlambat'))]);
            $sl = ['new' => 'New', 'progress' => 'On Progress', 'pending' => 'Pending', 'done' => 'Done', 'closed' => 'Closed']; $sb = [];
            foreach ($sl as $kk => $l2) $sb[] = ['label' => $l2, 'n' => (int)($S[$kk] ?? 0)];
            $pr = []; foreach ($D['task']['per'] as $r) $pr[] = [$e($r['name']), rpNum223($r['created']), rpNum223($r['done']), rpNum223($r['open']), $r['overdue'] ? '<span class="down">' . $r['overdue'] . '</span>' : '0'];
            $h .= '<table class="two"><tr><td><h3>Status semua task</h3>' . $bars($sb) . '</td><td><h3>Per orang</h3>' . ($pr ? $tbl(['Nama', 'Baru', 'Selesai', 'Terbuka', 'Telat'], $pr, [1, 2, 3, 4]) : '<p class="muted">Belum ada task.</p>') . '</td></tr></table>';
            if ($D['task']['late']) { $lr = []; foreach ($D['task']['late'] as $x) $lr[] = [$e($x['title']), $e($x['who']), $e(rpDateId223($x['due']))]; $h .= '<h3>Lewat jatuh tempo</h3>' . $tbl(['Task', 'Ditugaskan ke', 'Jatuh tempo'], $lr); }
        } elseif ($k === 'topic' && isset($D['topic'])) {
            $tp = $D['topic'];
            $h .= '<table class="two"><tr><td><h3>Topik utama pelanggan WhatsApp</h3>' . $bars($tp['topics']) . '</td><td><h3>Per divisi</h3>' . ($tp['divs'] ? $bars($tp['divs']) : '<p class="muted">Topik belum dipetakan ke divisi.</p>') . '</td></tr></table>'
                . '<p class="muted">' . rpNum223($tp['total']) . ' pelanggan WhatsApp chat dalam periode; ' . rpNum223($tp['none']) . ' belum berlabel topik.</p>';
        } elseif ($k === 'usage' && isset($D['usage'])) {
            $U = $D['usage'];
            $h .= $tiles([$tile('Balasan AI dalam periode', rpNum223($U['ai_calls']), ''),
                          $tile('Kuota bulan ini', $U['cap'] ? rpNum223($U['used']) . ' / ' . rpNum223($U['cap']) : rpNum223($U['used']), $U['cap'] ? str_replace('.', ',', (string)round($U['pct'], 1)) . '% terpakai' : 'tanpa batas'),
                          $tile('Paket', $e($U['tier'] !== '' ? ucfirst($U['tier']) : '—'), $U['expires'] !== '' ? 'berlaku s/d ' . $e(rpDateId223(substr($U['expires'], 0, 10))) : '')]);
        } else continue;
        $out[] = preg_replace('#(<div class="keep"><h2>.*?</h2>)(<table class="tiles">.*?</table>)?#s', '$1$2</div>', $h, 1) . '</div>';
    }
    $title = 'Laporan ' . ($kindL !== '' ? $kindL . ' ' : '') . ($D['own'] ? ($D['for'] !== '' ? $D['for'] : 'Sales') : $D['biz']);
    $css = '@page{margin:16mm 13mm 16mm 13mm}*{box-sizing:border-box}body{font-family:"DejaVu Sans",Arial,Helvetica,sans-serif;font-size:9.5pt;color:#15152b;margin:0}'
         . '.hd{background:' . $C . ';color:#fff;padding:14px 16px;border-radius:8px;margin-bottom:12px}.hd h1{font-size:16pt;margin:0 0 3px}.hd .sub{font-size:9.5pt;opacity:.92}'
         . 'h2{font-size:12pt;color:' . $C . ';margin:0 0 8px;padding-bottom:4px;border-bottom:1.5px solid ' . $C . '}h3{font-size:9.5pt;margin:10px 0 5px;color:#33334d}'
         . '.sec{margin-bottom:14px;page-break-inside:auto}.keep{page-break-inside:avoid}h2,h3{page-break-after:avoid}.two,.cols,.bars tr,.t tr{page-break-inside:avoid}.tiles{page-break-inside:avoid;width:100%;border-collapse:separate;border-spacing:5px;margin:0 -5px 4px}.tile{width:33.3%;background:#f4f5fb;border-radius:6px;padding:7px 9px;vertical-align:top}.tile.blank{background:none}'
         . '.tl{font-size:7.5pt;color:#6b6b82;text-transform:uppercase}.tv{font-size:13pt;font-weight:bold;color:' . $C . ';margin-top:2px}.ts{font-size:7.5pt;color:#55556b;margin-top:2px}'
         . '.up{color:#15803d;font-weight:bold}.down{color:#b91c1c;font-weight:bold}.flat{color:#6b6b82}.muted{color:#6b6b82;font-size:8.5pt;margin:4px 0}'
         . '.t{width:100%;border-collapse:collapse;margin:2px 0 6px}.t th{text-align:left;font-size:7.5pt;color:#6b6b82;padding:4px 5px;border-bottom:1px solid #d9d9e5;text-transform:uppercase}.t td{font-size:8.5pt;padding:4px 5px;border-bottom:1px solid #eeeef4;vertical-align:top}.t .n{text-align:right;white-space:nowrap}'
         . '.two{width:100%;border-collapse:collapse}.two>tbody>tr>td,.two>tr>td{width:50%;vertical-align:top;padding-right:10px}'
         . '.bars{width:100%;border-collapse:collapse}.bars td{padding:2px 0;font-size:8.5pt;vertical-align:middle}.bl{width:38%;padding-right:6px!important}.bb{width:48%}.bv{width:14%;text-align:right;white-space:nowrap}.bt{width:100%;border-collapse:collapse;height:9px}.bt td{height:9px;padding:0!important}'
         . '.cols{width:100%;border-collapse:collapse;table-layout:fixed;margin-bottom:6px}.cv{vertical-align:bottom;text-align:center;height:84px;padding:0 1px}.cb{width:70%;margin:0 auto;border-radius:2px 2px 0 0}.cn{font-size:6pt;color:#55556b}.cd{font-size:6pt;color:#6b6b82;text-align:center;border-top:1px solid #d9d9e5;padding-top:2px}'
         . '.ft{margin-top:10px;padding-top:8px;border-top:1px solid #e6e6ef;font-size:7.5pt;color:#6b6b82}';
    return '<!DOCTYPE html><html lang="id"><head><meta charset="utf-8"><title>' . $e($title) . '</title><style>' . $css . '</style></head><body>'
        . '<div class="hd"><h1>' . $e($title) . '</h1><div class="sub">' . ($D['own'] ? $e($D['biz']) . ' · ' : '') . 'Periode ' . $e($per) . ' · dibuat ' . $e($D['generated']) . '</div></div>'
        . ($out ? implode('', $out) : '<p class="muted">Tidak ada bagian laporan yang bisa ditampilkan untuk penerima ini.</p>')
        . '<div class="ft">Perbandingan (▲/▼) terhadap periode sebelumnya ' . $e(rpDateId223($D['prev'][0]) . ' – ' . rpDateId223($D['prev'][1])) . '. Nilai "saat ini" = kondisi ketika laporan dibuat. Dibuat otomatis oleh ' . $e($D['brand']) . '. Detail lengkap: ' . $e($D['dash']) . '</div>'
        . '</body></html>';
}
/* ---------- mesin PDF ---------- */
function rpLibDir223() { return dirname(__DIR__) . '/lib/dompdf-' . RP_LIB_VER; }
function rpLibState223() {   // ['ok'=>bool,'via'=>'vendor'|'lib'|'', ...]
    if (class_exists('\\Dompdf\\Dompdf')) return ['ok' => true, 'via' => 'loaded'];
    $v = dirname(__DIR__) . '/vendor/dompdf/dompdf';
    if (is_dir($v) && is_file(dirname(__DIR__) . '/vendor/autoload.php')) return ['ok' => true, 'via' => 'vendor'];
    if (is_file(rpLibDir223() . '/autoload.inc.php')) return ['ok' => true, 'via' => 'lib'];
    return ['ok' => false, 'via' => ''];
}
function rpLibLoad223() {
    if (class_exists('\\Dompdf\\Dompdf')) return true;
    $st = rpLibState223();
    if ($st['via'] === 'vendor') { require_once dirname(__DIR__) . '/vendor/autoload.php'; }
    elseif ($st['via'] === 'lib') { require_once rpLibDir223() . '/autoload.inc.php'; }
    return class_exists('\\Dompdf\\Dompdf');
}
function rpPhpReq223() {   // ekstensi PHP yang dibutuhkan dompdf
    $miss = []; foreach (['dom', 'mbstring'] as $x) if (!extension_loaded($x)) $miss[] = $x;
    if (!extension_loaded('gd')) $miss[] = 'gd (opsional, untuk gambar)';
    return $miss;
}
// Pasang dompdf dari server pusat (sekali). [ok, pesan]
function rpLibInstall223() {
    if (rpLibLoad223()) return [true, 'sudah terpasang'];
    if (!class_exists('ZipArchive')) return [false, 'Ekstensi PHP zip tidak tersedia — pasang php-zip atau unggah folder lib/dompdf-' . RP_LIB_VER . ' manual.'];
    $cs = getSettings()['central_server'] ?? []; $base = rtrim((string)($cs['url'] ?? ''), '/');
    if ($base === '') return [false, 'Server pusat belum diatur.'];
    $root = dirname(__DIR__) . '/lib'; if (!is_dir($root) && !@mkdir($root, 0755, true)) return [false, 'Folder lib/ tidak bisa dibuat (izin tulis).'];
    if (!is_file($root . '/.htaccess')) @file_put_contents($root . '/.htaccess', "# v1.2.223: laporan-pdf — pustaka PHP, tidak untuk diakses lewat web\nOptions -Indexes\n<IfModule mod_authz_core.c>\n  Require all denied\n</IfModule>\n<IfModule !mod_authz_core.c>\n  Order deny,allow\n  Deny from all\n</IfModule>\n");
    $lk = @fopen($root . '/.install.lock', 'c'); if ($lk && !flock($lk, LOCK_EX | LOCK_NB)) return [false, 'Pemasangan sedang berjalan, coba lagi sebentar.'];
    $tmp = $root . '/.dl-' . bin2hex(random_bytes(4)) . '.zip'; $fh = @fopen($tmp, 'w');
    if (!$fh) return [false, 'Tidak bisa menulis berkas sementara di lib/.'];
    $ch = curl_init($base . '/lib/dompdf-' . RP_LIB_VER . '-dei.zip');
    curl_setopt_array($ch, [CURLOPT_FILE => $fh, CURLOPT_TIMEOUT => 90, CURLOPT_CONNECTTIMEOUT => 10, CURLOPT_FOLLOWLOCATION => true]);
    $ok = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $cerr = curl_error($ch); curl_close($ch); fclose($fh);
    $fail = function ($m) use ($tmp, $lk) { @unlink($tmp); if ($lk) { flock($lk, LOCK_UN); fclose($lk); } return [false, $m]; };
    if (!$ok || $code !== 200) return $fail('Unduh mesin PDF gagal (HTTP ' . $code . ($cerr ? ', ' . $cerr : '') . ').');
    if (!hash_equals(RP_LIB_SHA256, (string)hash_file('sha256', $tmp))) return $fail('Berkas mesin PDF tidak cocok (checksum) — pemasangan dibatalkan.');
    $z = new ZipArchive(); if ($z->open($tmp) !== true) return $fail('ZIP mesin PDF rusak.');
    $pre = 'dompdf-' . RP_LIB_VER . '/';
    for ($i = 0; $i < $z->numFiles; $i++) { $n = (string)$z->getNameIndex($i); if (strpos($n, $pre) !== 0 || strpos($n, '..') !== false) { $z->close(); return $fail('Isi ZIP mesin PDF tidak dikenali.'); } }
    $stage = $root . '/.x-' . bin2hex(random_bytes(4)); @mkdir($stage, 0755);
    $okx = $z->extractTo($stage); $z->close(); @unlink($tmp);
    if (!$okx || !is_file($stage . '/' . $pre . 'autoload.inc.php')) { deiRmTree223($stage); if ($lk) { flock($lk, LOCK_UN); fclose($lk); } return [false, 'Ekstrak mesin PDF gagal.']; }
    if (is_dir(rpLibDir223())) deiRmTree223(rpLibDir223());
    $mv = @rename($stage . '/' . rtrim($pre, '/'), rpLibDir223()); deiRmTree223($stage);
    if ($lk) { flock($lk, LOCK_UN); fclose($lk); }
    if (!$mv) return [false, 'Gagal memindahkan mesin PDF ke lib/.'];
    return rpLibLoad223() ? [true, 'terpasang'] : [false, 'Mesin PDF terpasang tetapi tidak bisa dimuat (cek ekstensi PHP dom & mbstring).'];
}
function deiRmTree223($p) {
    if (is_link($p) || is_file($p)) { @unlink($p); return; }
    if (!is_dir($p)) return;
    foreach ((array)@scandir($p) as $f) if ($f !== '.' && $f !== '..') deiRmTree223($p . '/' . $f);
    @rmdir($p);
}
function rpCanExec223() {
    if (!function_exists('proc_open')) return false;
    $dis = array_map('trim', explode(',', (string)ini_get('disable_functions')));
    return !in_array('proc_open', $dis, true);
}
function rpChromeBin223($cf = null) {
    static $memo = [];
    $cf = $cf ?? rpConf223(); $k = $cf['chrome_bin'];
    if (array_key_exists($k, $memo)) return $memo[$k];
    if (!rpCanExec223()) return $memo[$k] = '';
    $c = $k !== '' ? [$k] : [];
    $env = getenv('DEI_CHROME_BIN'); if (is_string($env) && $env !== '') $c[] = $env;
    $c = array_merge($c, ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/snap/bin/chromium', '/usr/local/bin/chromium', '/opt/google/chrome/chrome']);
    foreach ($c as $b) { if (rpChromeName223($b) && @is_file($b) && @is_executable($b)) return $memo[$k] = $b; }
    return $memo[$k] = '';
}
function rpChromeName223($b) {   // hanya biner Chromium/Chrome yang boleh dijalankan
    return is_string($b) && $b !== '' && strpos($b, "\0") === false && $b[0] === '/' && (bool)preg_match('/^(chromium|chromium-browser|chrome|google-chrome|google-chrome-stable|chrome-headless-shell|headless_shell)$/', basename($b));
}
function rpPdfChrome223($html, $bin) {
    $dir = DATA_DIR . '/report-pdf/.tmp-' . bin2hex(random_bytes(5)); @mkdir($dir, 0700, true);
    $in = $dir . '/r.html'; $out = $dir . '/r.pdf'; file_put_contents($in, $html);
    $cmd = [$bin, '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--no-first-run', '--no-default-browser-check', '--disable-extensions',
            '--user-data-dir=' . $dir . '/prof', '--no-pdf-header-footer', '--print-to-pdf=' . $out, 'file://' . $in];
    $p = @proc_open($cmd, [0 => ['pipe', 'r'], 1 => ['pipe', 'w'], 2 => ['pipe', 'w']], $pipes, $dir, ['HOME' => $dir, 'PATH' => '/usr/local/bin:/usr/bin:/bin']);
    if (!is_resource($p)) { deiRmTree223($dir); return [null, 'Chromium tidak bisa dijalankan.']; }
    fclose($pipes[0]); stream_set_blocking($pipes[1], false); stream_set_blocking($pipes[2], false);
    $t0 = time(); $err = '';
    while (true) { $s = proc_get_status($p); $err .= (string)stream_get_contents($pipes[2]); stream_get_contents($pipes[1]); if (!$s['running']) break; if (time() - $t0 > 45) { proc_terminate($p, 9); $err .= ' (timeout 45 dtk)'; break; } usleep(150000); }
    fclose($pipes[1]); fclose($pipes[2]); proc_close($p);
    $pdf = is_file($out) ? (string)file_get_contents($out) : '';
    deiRmTree223($dir);
    if (strncmp($pdf, '%PDF', 4) !== 0) return [null, 'Chromium gagal membuat PDF: ' . mb_substr(trim(preg_replace('/\s+/', ' ', $err)), -200)];
    return [$pdf, ''];
}
function rpPdfDompdf223($html) {
    if (!rpLibLoad223()) { [$ok, $m] = rpLibInstall223(); if (!$ok) return [null, $m]; }
    $miss = array_filter(rpPhpReq223(), function ($x) { return strpos($x, 'opsional') === false; });
    if ($miss) return [null, 'Ekstensi PHP belum aktif: ' . implode(', ', $miss) . '.'];
    $cache = DATA_DIR . '/report-pdf/.font-cache'; if (!is_dir($cache)) @mkdir($cache, 0755, true);
    try {
        $o = new \Dompdf\Options();
        $o->set('isRemoteEnabled', false); $o->set('isPhpEnabled', false); $o->set('isJavascriptEnabled', false);
        $o->set('defaultFont', 'DejaVu Sans'); $o->set('fontCache', $cache); $o->set('tempDir', $cache); $o->set('chroot', [DATA_DIR . '/report-pdf']);
        $o->set('defaultPaperSize', 'a4'); $o->set('dpi', 96);
        $d = new \Dompdf\Dompdf($o);
        $d->loadHtml($html, 'UTF-8'); $d->setPaper('A4', 'portrait'); $d->render();
        $cv = $d->getCanvas(); $fm = $d->getFontMetrics(); $f = $fm->getFont('DejaVu Sans');
        if ($f) $cv->page_text($cv->get_width() - 92, $cv->get_height() - 28, 'Hal. {PAGE_NUM} / {PAGE_COUNT}', $f, 7, [0.42, 0.42, 0.51]);
        $pdf = (string)$d->output();
    } catch (\Throwable $e) { return [null, 'dompdf: ' . $e->getMessage()]; }
    return strncmp($pdf, '%PDF', 4) === 0 ? [$pdf, ''] : [null, 'dompdf tidak menghasilkan PDF.'];
}
// [bytes|null, mesin, error]
function rpPdf223($html, $cf = null) {
    $cf = $cf ?? rpConf223(); $eng = $cf['engine']; $err = '';
    if ($eng !== 'dompdf') {
        $bin = rpChromeBin223($cf);
        if ($bin !== '') { [$pdf, $err] = rpPdfChrome223($html, $bin); if ($pdf !== null) return [$pdf, 'chrome', '']; error_log('[report-pdf] ' . $err); }
        elseif ($eng === 'chrome') $err = 'Chromium/Chrome tidak ditemukan di server (atau proc_open dinonaktifkan) — memakai dompdf.';
    }
    [$pdf, $e2] = rpPdfDompdf223($html);
    return $pdf !== null ? [$pdf, 'dompdf', $err] : [null, '', trim($err . ' ' . $e2)];
}
/* ---------- arsip & tautan unduh ---------- */
function rpStream223($id, $inline = false) {
    $id = (string)$id; $p = RP_DIR . '/' . $id . '.pdf'; $row = null;
    if (preg_match('/^\d{8}-[0-9a-f]{12}$/', $id)) foreach (rpIndex223() as $r) if (($r['id'] ?? '') === $id) { $row = $r; break; }
    if (!$row || !is_file($p)) jsonOut(['ok' => false, 'error' => 'Laporan tidak ditemukan (arsip disimpan 120 hari).'], 404);
    while (ob_get_level()) ob_end_clean();
    header('Content-Type: application/pdf'); header('Content-Length: ' . filesize($p)); header('X-Content-Type-Options: nosniff'); header('Cache-Control: private, no-store');
    header('Content-Disposition: ' . ($inline ? 'inline' : 'attachment') . '; filename="' . rpFileName223($row) . '"');
    readfile($p); exit;
}
function rpIndex223() { $a = readJson(RP_DIR . '/index.json', []); return is_array($a) ? $a : []; }
function rpStore223($pdf, $meta) {
    if (!is_dir(RP_DIR)) @mkdir(RP_DIR, 0755, true);
    if (!is_file(RP_DIR . '/.htaccess')) @file_put_contents(RP_DIR . '/.htaccess', "Require all denied\n");
    $id = wibDate('Ymd') . '-' . bin2hex(random_bytes(6));
    if (@file_put_contents(RP_DIR . '/' . $id . '.pdf', $pdf, LOCK_EX) === false) return '';
    $ix = rpIndex223(); array_unshift($ix, ['id' => $id, 'size' => strlen($pdf), 'at' => wibDate('Y-m-d H:i:s')] + $meta);
    $keep = []; $cut = wibDate('Y-m-d', time() - 120 * 86400);
    foreach ($ix as $i => $r) { if ($i < 150 && substr((string)($r['at'] ?? ''), 0, 10) >= $cut) $keep[] = $r; else @unlink(RP_DIR . '/' . preg_replace('/[^0-9a-f-]/', '', (string)($r['id'] ?? 'x')) . '.pdf'); }
    writeJson(RP_DIR . '/index.json', $keep);
    return $id;
}
function rpFileName223($r) {
    $b = preg_replace('/[^a-z0-9]+/', '-', strtolower(deiTenantName(getSettings()))); $b = trim($b, '-') ?: 'laporan';
    $k = ['weekly' => 'mingguan', 'monthly' => 'bulanan'][$r['kind'] ?? ''] ?? 'periode';
    $w = trim(preg_replace('/[^a-z0-9]+/', '-', strtolower((string)($r['for'] ?? ''))), '-');
    return 'laporan-' . $k . '-' . $b . ($w !== '' && !empty($r['own']) ? '-' . $w : '') . '-' . ($r['from'] ?? '') . '_' . ($r['to'] ?? '') . '.pdf';
}
function rpSig223($id, $exp) { return substr(hash_hmac('sha256', 'rpdl|' . $id . '|' . $exp, getSecret()), 0, 32); }
function rpLink223($id) {
    $exp = time() + RP_LINK_DAYS * 86400; $api = deiRememberedApiUrl();
    if ($api === '') $api = preg_replace('#/dashboard/chatbot-ai/?$#', '', crmDashUrl215()) . '/api/index.php';
    $api = preg_replace('/\?.*$/', '', $api);
    return $api . '?' . http_build_query(['action' => 'rpt_dl', 'f' => $id, 'e' => $exp, 's' => rpSig223($id, $exp)]);
}
/* ---------- kirim ---------- */
function rpMailAttach223($to, $subject, $text, $html, $att) {
    $to = deiValidEmail($to);
    if ($to === '') return ['ok' => false, 'error' => 'alamat email tidak valid'];
    if (!empty($GLOBALS['dei_dry'])) return ['ok' => true, 'via' => 'dry'];
    $fromName = deiBrandProduct(); $cs = getSettings()['central_server'] ?? [];
    $a = $att && strlen($att['data']) <= RP_MAX_ATTACH ? ['name' => $att['name'], 'mime' => 'application/pdf', 'b64' => base64_encode($att['data'])] : null;
    if (!empty($cs['url']) && !empty($cs['tenant_id']) && !empty($cs['license_key'])) {
        $ch = curl_init(rtrim($cs['url'], '/') . '/backend/index.php?action=mail_relay');
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 40, CURLOPT_CONNECTTIMEOUT => 6, CURLOPT_POST => true, CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => json_encode(['tenant_id' => $cs['tenant_id'], 'license_key' => $cs['license_key'], 'kind' => 'report_pdf', 'to' => $to, 'subject' => $subject,
                'text' => $text, 'html' => $html, 'from_name' => $fromName, 'attach' => $a])]);
        $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $cerr = curl_error($ch); curl_close($ch);
        $j = json_decode((string)$resp, true);
        if ($code === 200 && !empty($j['ok']) && !empty($j['sent'])) return ['ok' => true, 'via' => 'pusat', 'attached' => $a !== null && !empty($j['attached'])];
        error_log('[report-pdf mail] pusat HTTP ' . $code . ' ' . mb_substr((string)$resp, 0, 200) . ' ' . $cerr);
        if ($code !== 0) return ['ok' => false, 'via' => 'pusat', 'error' => (string)($j['error'] ?? ('HTTP ' . $code))];
    }
    $host = strtolower(preg_replace('/:\d+$/', '', (string)($_SERVER['HTTP_HOST'] ?? '')));
    $host = preg_replace('/^www\./', '', preg_replace('/[^a-z0-9.\-]/', '', $host)); if ($host === '' || strpos($host, '.') === false) $host = 'deintegra.com';
    $b = 'deim-' . bin2hex(random_bytes(8)); $ba = 'deia-' . bin2hex(random_bytes(8));
    $hdr = 'From: =?UTF-8?B?' . base64_encode($fromName) . '?= <noreply@' . $host . ">\r\nMIME-Version: 1.0\r\nAuto-Submitted: auto-generated\r\nContent-Type: multipart/mixed; boundary=\"$b\"";
    $alt = "--$ba\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($text))
         . "--$ba\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($html)) . "--$ba--\r\n";
    $body = "--$b\r\nContent-Type: multipart/alternative; boundary=\"$ba\"\r\n\r\n" . $alt;
    if ($a) $body .= "--$b\r\nContent-Type: application/pdf; name=\"" . $a['name'] . "\"\r\nContent-Transfer-Encoding: base64\r\nContent-Disposition: attachment; filename=\"" . $a['name'] . "\"\r\n\r\n" . chunk_split($a['b64']);
    $body .= "--$b--\r\n";
    $ok = function_exists('mail') && @mail($to, '=?UTF-8?B?' . base64_encode($subject) . '?=', $body, $hdr);
    return ['ok' => (bool)$ok, 'via' => 'mail', 'attached' => (bool)$a, 'error' => $ok ? '' : 'mail() gagal'];
}
function rpSummary223($D) {   // 3–5 baris ringkas untuk badan email / caption WA
    $L = [];
    if (isset($D['chat'])) $L[] = 'Pelanggan chat: ' . rpNum223($D['chat']['customers']) . ' · lead baru ' . rpNum223($D['chat']['leads']['new']);
    if (isset($D['conv'])) $L[] = 'Percakapan: ' . rpNum223($D['conv']['totals']['total']) . ' · respon pertama ' . rpDur223($D['conv']['avg']['frt']);
    if (isset($D['crm'])) { $T = $D['crm']['perf']['total']; $L[] = 'Close Deal: ' . rpNum223($T['deal']) . ' (' . rpRp223($T['deal_v']) . ') · pipeline ' . rpRp223($T['open_v']); }
    if (isset($D['task'])) $L[] = 'Task: ' . rpNum223($D['task']['total']['done']) . ' selesai · ' . rpNum223($D['task']['total']['open']) . ' terbuka' . ($D['task']['total']['overdue'] ? ' (' . $D['task']['total']['overdue'] . ' terlambat)' : '');
    return $L;
}
function rpSendMail223($R, $D, $pdf, $fname, $link, $test = false) {
    $e = function ($x) { return htmlspecialchars((string)$x, ENT_QUOTES, 'UTF-8'); };
    $kindL = $D['kind'] === 'monthly' ? 'bulanan' : ($D['kind'] === 'weekly' ? 'mingguan' : '');
    $per = rpDateId223($D['from']) . ' – ' . rpDateId223($D['to']);
    $subject = ($test ? '[Uji] ' : '') . 'Laporan ' . ($kindL ? $kindL . ' ' : '') . ($D['own'] ? 'Anda ' : '') . $per . ' — ' . $D['biz'];
    $sum = rpSummary223($D);
    $big = strlen($pdf) > RP_MAX_ATTACH;
    $p = array_merge(['Halo ' . $R[1] . ',', 'Laporan ' . ($kindL ?: '') . ' periode ' . $per . ' ' . ($big ? 'bisa diunduh lewat tautan di bawah (ukuran PDF terlalu besar untuk lampiran).' : 'terlampir dalam bentuk PDF.')], $sum ? ['Ringkasan: ' . implode(' · ', $sum) . '.'] : []);
    $foot = 'Dikirim otomatis oleh ' . $D['brand'] . ' (' . deiWibNow() . '). Tautan unduh berlaku ' . RP_LINK_DAYS . ' hari. Atur jadwal & penerima di Laporan & Log > Laporan Berkala.';
    $text = implode("\n\n", $p) . "\n\nUnduh PDF: " . $link . "\n\n" . $foot . "\n";
    $r = rpMailAttach223($R[2], $subject, $text, deiMailHtml('Laporan ' . ($kindL ?: '') . ' ' . $D['biz'], $p, 'Unduh PDF', $link, $foot), $big ? null : ['name' => $fname, 'data' => $pdf]);
    return $r;
}
function rpSendWa223($R, $D, $pdf, $fname, $link) {
    if (!empty($GLOBALS['dei_dry'])) return ['ok' => true, 'dry' => true];
    [$w, $err] = ntfSender222(); if (!$w) return ['ok' => false, 'error' => $err];
    $kindL = $D['kind'] === 'monthly' ? 'bulanan' : ($D['kind'] === 'weekly' ? 'mingguan' : '');
    $cap = '*Laporan ' . ($kindL ?: '') . ' ' . $D['biz'] . "*\nPeriode " . rpDateId223($D['from']) . ' – ' . rpDateId223($D['to']);
    foreach (rpSummary223($D) as $l) $cap .= "\n• " . $l;
    $to = ntfNum222($R[3]);
    $prev = $GLOBALS['dei_out_src'] ?? null; $GLOBALS['dei_out_src'] = 'notif'; $GLOBALS['wa_last_error'] = '';
    $tmp = DATA_DIR . '/report-pdf/.wa-' . bin2hex(random_bytes(4)) . '.pdf'; @file_put_contents($tmp, $pdf);
    $ok = false;
    try { $ok = strlen($pdf) <= 15 * 1024 * 1024 && (bool)waSendFile($w, $to, $tmp, 'document', 'application/pdf', $cap, $fname); } catch (\Throwable $x) { $GLOBALS['wa_last_error'] = $x->getMessage(); }
    @unlink($tmp);
    $via = 'file';
    if (!$ok) {   // penyedia tanpa kirim file (Fonnte) / gagal -> teks + tautan
        $e1 = (string)($GLOBALS['wa_last_error'] ?? '');
        try { $ok = (bool)waSend($w, $to, $cap . "\n\nUnduh PDF: " . $link); } catch (\Throwable $x) { $GLOBALS['wa_last_error'] = $x->getMessage(); }
        $via = 'link'; if (!$ok && $e1 !== '') $GLOBALS['wa_last_error'] = $e1;
    }
    if ($prev === null) unset($GLOBALS['dei_out_src']); else $GLOBALS['dei_out_src'] = $prev;
    $res = $ok ? ['ok' => true, 'via' => $via] : ['ok' => false, 'error' => trim((string)($GLOBALS['wa_last_error'] ?? '')) ?: 'Gagal kirim WhatsApp.'];
    ntfLogAdd222(['at' => date('Y-m-d H:i:s'), 'kind' => 'report_pdf', 'to' => $to, 'name' => mb_substr((string)$R[1], 0, 60), 'ch' => (string)($w['_ch'] ?? ''), 'ok' => !empty($res['ok']), 'err' => mb_substr((string)($res['error'] ?? ''), 0, 160)]);
    return $res;
}
// Buat satu PDF. Hasil: ['ok', 'id', 'pdf', 'D', 'engine', 'warn', 'error']
function rpBuild223($kind, $from, $to, $sections, $V, $meta = [], $cf = null) {
    $cf = $cf ?? rpConf223();
    $D = rpData223($kind, $from, $to, $sections, $V);
    [$pdf, $eng, $err] = rpPdf223(rpHtml223($D), $cf);
    if ($pdf === null) return ['ok' => false, 'error' => $err ?: 'Gagal membuat PDF.'];
    $m = ['kind' => $kind, 'from' => $from, 'to' => $to, 'for' => (string)($V['for'] ?? ''), 'own' => $D['own'], 'engine' => $eng, 'sections' => $D['sections']] + $meta;
    $id = rpStore223($pdf, $m);
    return ['ok' => true, 'id' => $id, 'pdf' => $pdf, 'D' => $D, 'engine' => $eng, 'warn' => $err, 'name' => rpFileName223($m)];
}
function rpVariant223($R) { return $R[4] === null ? 'full' : 's:' . implode(',', $R[4]) . '|u:' . $R[5]; }
// cron_tick: kirim laporan yang jatuh tempo (bulanan dulu, lalu mingguan). Maks 8 kiriman per tick.
function rpSweep223($s) {
    if (!rpOk223()) return null;
    $cf = rpConf223(); if (!$cf['weekly']['on'] && !$cf['monthly']['on']) return null;
    $st = readJson(RP_STATE_FILE, []); if (!is_array($st)) $st = [];
    if ((int)($st['_wait'] ?? 0) > time()) return null;
    $res = null; $budget = 8; [$waOk] = rpWaReady223();
    foreach (['monthly', 'weekly'] as $kind) {
        if (!rpDue223($kind, $cf)) continue;
        [$key, $from, $to] = rpPeriod223($kind, $cf);
        $S = is_array($st[$kind] ?? null) ? $st[$kind] : [];
        if (($S['key'] ?? '') === $key && !empty($S['done'])) continue;
        if (($S['key'] ?? '') !== $key) $S = ['key' => $key, 'from' => $from, 'to' => $to, 'files' => [], 'sent' => [], 'log' => []];
        $left = false; $R0 = $res ?? ['mail' => 0, 'wa' => 0, 'fail' => 0];
        foreach (rpRecipients223($cf) as $R) {
            $ch = rpChannels223($cf, $R, $waOk);
            foreach (['email', 'wa'] as $c) {
                if (!$ch[$c]) continue;
                $sk = $c . ':' . $R[0]; if (!empty($S['sent'][$sk])) continue;
                if ($budget <= 0) { $left = true; break 2; }
                $vk = rpVariant223($R);
                if (empty($S['files'][$vk]) || !is_file(RP_DIR . '/' . $S['files'][$vk] . '.pdf')) {
                    $b = rpBuild223($kind, $from, $to, $cf[$kind]['sections'], ['scope' => $R[4], 'user' => $R[5], 'for' => $R[4] === null ? '' : $R[1]], ['by' => 'jadwal'], $cf);
                    if (!$b['ok']) { $S['err'] = $b['error']; $S['done'] = false; $st[$kind] = $S; $st['_wait'] = time() + 1800; if (empty($GLOBALS['dei_dry'])) writeJson(RP_STATE_FILE, $st); error_log('[report-pdf] ' . $b['error']); return ['error' => $b['error']]; }
                    $S['files'][$vk] = $b['id']; $budget--;
                    $GLOBALS['rp_cache'][$b['id']] = $b;
                }
                $fid = $S['files'][$vk]; $b = $GLOBALS['rp_cache'][$fid] ?? null;
                if (!$b) { $ix = null; foreach (rpIndex223() as $r) if ($r['id'] === $fid) $ix = $r; $b = ['pdf' => (string)@file_get_contents(RP_DIR . '/' . $fid . '.pdf'), 'D' => rpData223($kind, $from, $to, $cf[$kind]['sections'], ['scope' => $R[4], 'user' => $R[5], 'for' => $R[4] === null ? '' : $R[1]]), 'name' => rpFileName223($ix ?: ['kind' => $kind, 'from' => $from, 'to' => $to])]; $GLOBALS['rp_cache'][$fid] = $b; }
                $link = rpLink223($fid);
                $r = $c === 'email' ? rpSendMail223($R, $b['D'], $b['pdf'], $b['name'], $link) : rpSendWa223($R, $b['D'], $b['pdf'], $b['name'], $link);
                $budget--;
                if ($c === 'email' && empty($r['ok']) && stripos((string)($r['error'] ?? ''), 'batas') !== false) { $st['_wait'] = time() + 900; $left = true; break 2; }
                $S['sent'][$sk] = 1;
                $S['log'][] = ['at' => wibDate('Y-m-d H:i'), 'to' => $c === 'email' ? deiMaskEmail($R[2]) : $R[3], 'name' => mb_substr($R[1], 0, 60), 'ch' => $c, 'ok' => !empty($r['ok']), 'err' => mb_substr((string)($r['error'] ?? ''), 0, 160)];
                if (!empty($r['ok'])) $R0[$c === 'email' ? 'mail' : 'wa']++; else $R0['fail']++;
            }
        }
        $S['done'] = !$left; $S['log'] = array_slice($S['log'], -60); unset($S['err']);
        if (!$left) $S['done_at'] = wibDate('Y-m-d H:i');
        $st[$kind] = $S; $res = $R0;
        if ($left) break;
    }
    if (empty($GLOBALS['dei_dry'])) writeJson(RP_STATE_FILE, $st);
    return $res;
}
function rpPublicConf223($cf) {
    $W = rpWaReady223(); $ce = rpChromeBin223($cf); $lib = rpLibState223(); $st = readJson(RP_STATE_FILE, []);
    $rc = []; foreach (rpRecipients223($cf) as $R) { $ch = rpChannels223($cf, $R, $W[0]); $rc[] = ['name' => $R[1], 'role' => $R[6], 'email' => $R[2] !== '' ? deiMaskEmail($R[2]) : '', 'wa' => $R[3], 'own' => $R[4] !== null, 'via_email' => $ch['email'], 'via_wa' => $ch['wa']]; }
    $nx = [];
    foreach (['weekly', 'monthly'] as $k) { [$key, $f, $t, $lab] = rpPeriod223($k, $cf); $S = $st[$k] ?? []; $nx[$k] = ['key' => $key, 'from' => $f, 'to' => $t, 'label' => $lab, 'done' => ($S['key'] ?? '') === $key && !empty($S['done']), 'skipped' => ($S['key'] ?? '') === $key && !empty($S['skipped']), 'done_at' => ($S['key'] ?? '') === $key ? (string)($S['done_at'] ?? '') : '', 'err' => (string)($S['err'] ?? ''), 'log' => array_slice(array_reverse((array)($S['log'] ?? [])), 0, 20)]; }
    $sec = []; foreach (rpSections223() as $k => $x) $sec[] = ['key' => $k, 'label' => $x[0], 'crm' => $x[1], 'sales' => $x[2], 'avail' => !$x[1] || crmOk215()];
    return ['conf' => $cf, 'sections' => $sec, 'recipients' => $rc, 'wa_ready' => $W[0], 'wa_why' => $W[1], 'period' => $nx,
            'engine' => ['dompdf' => $lib['ok'], 'dompdf_via' => $lib['via'], 'dompdf_ver' => RP_LIB_VER, 'chrome' => $ce !== '', 'chrome_bin' => $ce, 'exec' => rpCanExec223(), 'php_missing' => rpPhpReq223(),
                         'active' => ($cf['engine'] !== 'dompdf' && $ce !== '') ? 'chrome' : 'dompdf'],
            'archive' => array_slice(rpIndex223(), 0, 30)];
}
