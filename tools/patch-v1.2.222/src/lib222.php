/* ---------- v1.2.222: notif-wa — notifikasi tim lewat WhatsApp dari salah satu nomor bisnis tenant ---------- */
if (!defined('NTF_FILE')) define('NTF_FILE', DATA_DIR . '/notif-wa.json');
if (!defined('NTF_LOG_FILE')) define('NTF_LOG_FILE', DATA_DIR . '/notif-wa-log.json');
function ntfKinds222() {   // jenis => [label, pilihan mode, bawaan]
    return [
        'crm_remind'  => ['Pengingat jatuh tempo (task & follow-up lead)', ['email', 'wa', 'both'], 'email'],
        'crm_weekly'  => ['Laporan mingguan sales', ['email', 'wa', 'both'], 'email'],
        'task_assign' => ['Task baru ditugaskan ke saya', ['off', 'wa'], 'wa'],
        'lead_assign' => ['Lead / chat ditandai ke Sales', ['off', 'wa'], 'wa'],
        'chat_assign' => ['Chat diserahkan (transfer) ke agent', ['off', 'wa'], 'wa'],
    ];
}
function ntfConf222($reset = false) {
    static $c = null;
    if ($reset) $c = null;
    if ($c !== null) return $c;
    $d = readJson(NTF_FILE, []); if (!is_array($d)) $d = [];
    $k = [];
    foreach (ntfKinds222() as $id => $x) { $v = (string)($d['kinds'][$id] ?? $x[2]); $k[$id] = in_array($v, $x[1], true) ? $v : $x[2]; }
    return $c = ['on' => !empty($d['on']), 'ch' => (string)($d['ch'] ?? 'utama'), 'kinds' => $k, 'updated_at' => (string)($d['updated_at'] ?? ''), 'updated_by' => (string)($d['updated_by'] ?? '')];
}
function ntfNum222($n) {   // 08xx / +62 / 8xx -> 628xx
    $d = preg_replace('/\D/', '', (string)$n);
    if ($d === '') return '';
    if (strpos($d, '0') === 0) $d = '62' . substr($d, 1); elseif (strpos($d, '8') === 0) $d = '62' . $d;
    return (strlen($d) >= 10 && strlen($d) <= 15) ? $d : '';
}
function ntfUserWa222($u) { return is_array($u) ? ntfNum222($u['wa'] ?? '') : ''; }
// Daftar nomor bisnis untuk pengirim notifikasi + alasan bila tidak bisa dipakai
function ntfChannels222($s = null) {
    if ($s === null) $s = getSettings();
    $wa = waConf($s); $out = [];
    if (empty($wa['enabled'])) return [];
    foreach (waChannels($s) as $c) {
        $cf = waChanConf($wa, $c['id'], $s); $p = (string)($cf['provider'] ?? 'meta'); $why = '';
        if ($p === 'meta') $why = 'Nomor WhatsApp API resmi (Meta) hanya bisa mengirim pesan bebas ke orang yang chat dalam 24 jam terakhir. Pilih nomor WAHA.';
        elseif ($p === 'waha' && (trim((string)($cf['waha_url'] ?? '')) === '' || trim((string)($cf['waha_session'] ?? '')) === '')) $why = 'Nomor ini belum terhubung (URL/sesi WAHA kosong).';
        elseif ($p === 'fonnte' && trim((string)($cf['fonnte_token'] ?? '')) === '') $why = 'Token Fonnte kosong.';
        $out[] = ['id' => (string)$c['id'], 'label' => (string)$c['label'], 'number' => (string)$c['number'], 'prov' => $p, 'ok' => $why === '', 'why' => $why];
    }
    return $out;
}
function ntfSender222() {   // [konfigurasi kirim | null, pesan error]
    $cf = ntfConf222(); $s = getSettings();
    foreach (ntfChannels222($s) as $c) {
        if ($c['id'] !== $cf['ch']) continue;
        if (!$c['ok']) return [null, $c['why']];
        $w = waChanConf(waConf($s), $c['id'], $s); $w['_ch'] = $c['id'];
        return [$w, ''];
    }
    return [null, 'Nomor pengirim notifikasi tidak ditemukan. Pilih ulang di Widget & API > Notifikasi Tim via WhatsApp.'];
}
function ntfActive222($reset = false) {
    static $a = null;
    if ($reset) $a = null;
    if ($a !== null) return $a;
    if (!ntfConf222()['on']) return $a = false;
    [$w, ] = ntfSender222();
    return $a = (bool)$w;
}
function ntfMode222($kind) { $k = ntfConf222()['kinds']; $d = ntfKinds222()[$kind][2] ?? 'off'; return ntfActive222() ? ($k[$kind] ?? $d) : (in_array('email', ntfKinds222()[$kind][1] ?? [], true) ? 'email' : 'off'); }
function ntfWantWa222($kind) { return in_array(ntfMode222($kind), ['wa', 'both'], true); }
// Email untuk pengguna ini dilewati bila mode "WhatsApp saja" dan nomornya ada
function ntfSkipMail222($kind, $u) { return ntfMode222($kind) === 'wa' && ntfUserWa222($u) !== ''; }
function ntfTeamNums222() {
    static $m = null;
    if ($m !== null) return $m;
    $m = [];
    foreach ((array)readJson(USERS_FILE, []) as $x) { $n = ntfUserWa222($x); if ($n !== '') $m[$n] = (string)($x['username'] ?? ''); }
    return $m;
}
// Nomor tim yang chat ke nomor bisnis (mis. membalas notifikasi) tidak dijawab bot
function ntfIsTeamNum222($num) {
    if (!ntfConf222()['on']) return false;
    $n = ntfNum222($num); return $n !== '' && isset(ntfTeamNums222()[$n]);
}
function ntfLogAdd222($row) {
    if (!empty($GLOBALS['dei_dry'])) return;
    try {
        deiWithLock('notif-wa-log', function () use ($row) {
            $l = readJson(NTF_LOG_FILE, []); if (!is_array($l)) $l = [];
            array_unshift($l, $row);
            writeJson(NTF_LOG_FILE, array_slice($l, 0, 300));
        });
    } catch (\Throwable $e) { error_log('ntfLog: ' . $e->getMessage()); }
}
function ntfWaSend222($to, $text, $kind, $name = '', $force = false) {
    $to = ntfNum222($to);
    if ($to === '') return ['ok' => false, 'error' => 'Nomor WhatsApp penerima kosong / tidak valid.'];
    if (!$force && !ntfActive222()) return ['ok' => false, 'error' => 'Notifikasi WhatsApp belum aktif.'];
    [$w, $err] = ntfSender222();
    if (!$w) return ['ok' => false, 'error' => $err];
    if (!empty($GLOBALS['dei_dry'])) return ['ok' => true, 'dry' => true];
    $hour = time() - 3600; $cnt = 0;
    foreach ((array)readJson(NTF_LOG_FILE, []) as $r) { if (($r['to'] ?? '') === $to && strtotime((string)($r['at'] ?? '')) >= $hour) $cnt++; }
    if ($cnt >= 20) { $res = ['ok' => false, 'error' => 'Batas 20 notifikasi per jam ke nomor ini.']; }
    else {
        $prevSrc = $GLOBALS['dei_out_src'] ?? null; $GLOBALS['dei_out_src'] = 'notif';
        $GLOBALS['wa_last_error'] = '';
        $ok = false;
        try { $ok = (bool)waSend($w, $to, mb_substr($text, 0, 3800)); } catch (\Throwable $e) { $GLOBALS['wa_last_error'] = $e->getMessage(); }
        if ($prevSrc === null) unset($GLOBALS['dei_out_src']); else $GLOBALS['dei_out_src'] = $prevSrc;
        $e = trim((string)($GLOBALS['wa_last_error'] ?? ''));
        $res = $ok ? ['ok' => true] : ['ok' => false, 'error' => $e !== '' ? $e : 'Gagal kirim WhatsApp.'];
    }
    ntfLogAdd222(['at' => date('Y-m-d H:i:s'), 'kind' => $kind, 'to' => $to, 'name' => mb_substr((string)$name, 0, 60), 'ch' => (string)($w['_ch'] ?? ''),
                  'ok' => !empty($res['ok']), 'err' => mb_substr((string)($res['error'] ?? ''), 0, 160)]);
    return $res;
}
function ntfHead222($title) { return '*' . $title . '* — ' . deiTenantName(getSettings()); }
// Notifikasi satu pengguna untuk jenis "off/wa" (task, lead, chat). Tidak ke diri sendiri.
function ntfUserEvent222($username, $kind, $title, $body, $byUser = '') {
    try {
        if ((string)$username === '' || (string)$username === (string)$byUser) return null;
        if (!ntfWantWa222($kind)) return null;
        foreach ((array)readJson(USERS_FILE, []) as $x) {
            if (!is_array($x) || ($x['username'] ?? '') !== $username || !empty($x['internal'])) continue;
            $n = ntfUserWa222($x); if ($n === '') return null;
            $nm = trim((string)($x['name'] ?? '')) ?: $username;
            return ntfWaSend222($n, ntfHead222($title) . "\n\nHalo " . $nm . ",\n" . $body . "\n\nBuka dashboard: " . crmDashUrl215(), $kind, $nm);
        }
    } catch (\Throwable $e) { error_log('ntfUserEvent222: ' . $e->getMessage()); }
    return null;
}
function ntfTaskAssigned222($t, $prevAs, $me, $meName) {
    if ($prevAs === null || !is_array($t)) return;
    $as = (string)($t['assignee'] ?? '');
    if ($as === '' || $as === (string)$prevAs || $as === (string)$me) return;
    $d = (string)($t['due'] ?? '');
    $b = 'Anda mendapat task baru dari ' . $meName . ":\n• " . (string)$t['title'] . ($d !== '' ? "\n• Tenggat: " . implode('/', array_reverse(explode('-', $d))) : '');
    $src = is_array($t['src'] ?? null) ? $t['src'] : null; $ld = (string)($t['lead'] ?? '');
    $num = $src ? (string)($src['num'] ?? '') : $ld;
    if ($num !== '') { $nm = crmLeadName215($num); $b .= "\n• Pelanggan: " . ($nm !== '' ? $nm . ' (+' . $num . ')' : '+' . $num); }
    ntfUserEvent222($as, 'task_assign', 'Task baru', $b, $me);
}
function ntfLeadAssigned222($num, $sid, $u) {
    if ((string)$sid === '') return;
    try {
        $un = crmSalesUserFor216((string)$sid, readJson(USERS_FILE, []));
        if ($un === '') return;
        $l = leadsGetAll()[$num] ?? []; $nm = crmLeadName215($num);
        $b = 'Lead baru dipegang Anda (ditandai oleh ' . (string)($u['name'] ?? $u['username'] ?? '') . "):\n• " . ($nm !== '' ? $nm . ' (+' . $num . ')' : '+' . $num);
        if (is_array($l)) {
            $need = trim((string)($l['extracted']['kebutuhan'] ?? '')); if ($need !== '') $b .= "\n• Kebutuhan: " . mb_substr($need, 0, 200);
            if (!empty($l['value'])) $b .= "\n• Nilai: " . crmRp216((int)$l['value']);
        }
        ntfUserEvent222($un, 'lead_assign', 'Lead untuk Anda', $b, (string)($u['username'] ?? ''));
    } catch (\Throwable $e) { error_log('ntfLeadAssigned222: ' . $e->getMessage()); }
}
function ntfRemindText222($u, $it, $today, $test = false) {
    $nm = trim((string)($u['name'] ?? '')) ?: (string)$u['username'];
    $fmt = function ($d) { $p = explode('-', (string)$d); return count($p) === 3 ? $p[2] . '/' . $p[1] : (string)$d; };
    $when = function ($d) use ($today, $fmt) { return $d < $today ? 'TERLAMBAT ' . $fmt($d) : ($d === $today ? 'hari ini' : 'besok'); };
    $tasks = (array)($it['tasks'] ?? []); $fus = (array)($it['fu'] ?? []); $ty = crmTypes215();
    usort($tasks, function ($a, $b) { return strcmp((string)$a['due'], (string)$b['due']); });
    usort($fus, function ($a, $b) { return strcmp($a['next_due'] . ($a['next_time'] ?? ''), $b['next_due'] . ($b['next_time'] ?? '')); });
    $lines = []; $late = 0;
    foreach ($tasks as $t) { if ($t['due'] < $today) $late++; $lines[] = '• Task: ' . $t['title'] . ' — ' . $when($t['due']); }
    foreach ($fus as $a) {
        if ($a['next_due'] < $today) $late++;
        $ln = crmLeadName215($a['num']);
        $lines[] = '• ' . ($ln !== '' ? $ln : '+' . $a['num']) . ': ' . (trim((string)($a['next_text'] ?? '')) !== '' ? $a['next_text'] : ($ty[$a['type'] ?? ''] ?? 'follow-up'))
                 . ' — ' . $when($a['next_due']) . (!empty($a['next_time']) ? ' ' . $a['next_time'] : '');
    }
    $total = count($lines);
    if ($total > 25) { $more = $total - 25; $lines = array_slice($lines, 0, 25); $lines[] = '… dan ' . $more . ' lainnya di dashboard.'; }
    if (!$total) $lines[] = 'Tidak ada task atau follow-up yang jatuh tempo saat ini.';
    $txt = ntfHead222(($test ? '[Uji] ' : '') . 'Pengingat jatuh tempo') . "\n\nHalo " . $nm . ', ada ' . $total . ' task & follow-up' . ($late ? ' (' . $late . ' terlambat)' : '') . " untuk hari ini/besok:\n"
         . implode("\n", $lines) . "\n\nBuka dashboard: " . crmDashUrl215();
    return [$txt, $total ? ltrim($lines[0], '• ') : ''];
}
function ntfWeeklyText222($nm, $rep, $own, $test = false) {
    $d = function ($x) { $p = explode('-', (string)$x); return count($p) === 3 ? $p[2] . '/' . $p[1] : (string)$x; };
    $T = $rep['total'];
    $L = [ntfHead222(($test ? '[Uji] ' : '') . 'Laporan mingguan ' . ($own ? 'Anda' : 'sales')), '', 'Halo ' . $nm . ', ringkasan ' . $d($rep['from']) . '–' . $d($rep['to']) . ':',
          '• Lead baru: ' . $T['new'] . ' · Aktivitas: ' . $T['acts'],
          '• Close Deal: ' . $T['deal'] . ' (' . crmRp216($T['deal_v']) . ') · Lose: ' . $T['lost'] . ' · Win: ' . ($T['win'] === null ? '—' : $T['win'] . '%'),
          '• Pipeline terbuka: ' . $T['open'] . ' (' . crmRp216($T['open_v']) . ')',
          '• Follow-up selesai: ' . $T['fu_done'] . ' · terlambat saat ini: ' . $T['fu_late']];
    if (!$own && $rep['rows']) { $L[] = ''; $L[] = 'Per sales:'; foreach (array_slice($rep['rows'], 0, 12) as $R) $L[] = '- ' . $R['name'] . ': ' . $R['deal'] . ' deal ' . crmRp216($R['deal_v']) . ', ' . $R['acts'] . ' aktivitas'; }
    $L[] = ''; $L[] = 'Detail: menu Laporan Sales di ' . crmDashUrl215();
    return implode("\n", $L);
}
function crmWeeklyWaRecipients222($cf) {   // [[wa, nama, sid|null]]
    $out = []; $seen = [];
    foreach ((array)readJson(USERS_FILE, []) as $x) {
        if (!is_array($x) || empty($x['username']) || !empty($x['internal'])) continue;
        $n = ntfUserWa222($x); if ($n === '' || isset($seen[$n])) continue;
        $r = (string)($x['role'] ?? ''); $nm = trim((string)($x['name'] ?? '')) ?: (string)$x['username'];
        if (in_array($r, ['super_admin', 'admin'], true) && $cf['admins']) { $out[] = [$n, $nm, null]; $seen[$n] = 1; }
        elseif ($r === 'sales' && $cf['sales'] && (string)($x['sales_id'] ?? '') !== '') { $out[] = [$n, $nm, crmSalesVisible219($x)]; $seen[$n] = 1; }
    }
    return $out;
}
function ntfPublic222($withUsers = true) {
    $cf = ntfConf222(); $kinds = [];
    foreach (ntfKinds222() as $id => $x) $kinds[] = ['id' => $id, 'label' => $x[0], 'opts' => $x[1], 'val' => $cf['kinds'][$id]];
    [$w, $err] = ntfSender222();
    $o = ['on' => $cf['on'], 'ch' => $cf['ch'], 'kinds' => $kinds, 'channels' => ntfChannels222(), 'sender_ok' => (bool)$w, 'sender_err' => $err,
          'updated_at' => $cf['updated_at'], 'updated_by' => $cf['updated_by']];
    if ($withUsers) {
        $us = [];
        foreach ((array)readJson(USERS_FILE, []) as $x) {
            if (!is_array($x) || empty($x['username']) || !empty($x['internal'])) continue;
            $us[] = ['username' => (string)$x['username'], 'name' => (string)($x['name'] ?? $x['username']), 'role' => (string)($x['role'] ?? ''), 'wa' => ntfUserWa222($x), 'email' => deiUserEmail($x) !== ''];
        }
        $o['users'] = $us;
        $o['log'] = array_slice((array)readJson(NTF_LOG_FILE, []), 0, 30);
    }
    return $o;
}
