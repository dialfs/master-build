#!/usr/bin/env python3
"""v1.2.217 (laporan-crm): CRM tahap 3 — Growth+.
- Leads > tampilan "Performa": laporan performa per Sales untuk periode (minggu lalu, minggu ini, bulan ini,
  bulan lalu, 30 hari, kustom): lead baru, aktivitas (per jenis), follow-up selesai/terlambat, PO, Close Deal
  (jumlah & Rp), Close Lose, win rate, rata-rata nilai deal, rata-rata lama closing, pipeline terbuka,
  nilai tertimbang, perkiraan closing 30 hari; aktivitas per pencatat; unduh CSV. Sales melihat barisnya sendiri.
- Laporan mingguan via email: otomatis tiap minggu (hari & jam diatur Admin) untuk 7 hari terakhir —
  Admin/Super Admin + email tambahan menerima laporan lengkap, akun Sales menerima laporannya sendiri.
  Admin: tombol "Laporan mingguan" (on/off, hari, jam, penerima, kirim uji).
Data: data/crm-weekly-conf.json, data/crm-weekly.json. Email kind crm_weekly (sudah diizinkan pusat sejak v1.2.215).
Butuh v1.2.216. Idempoten. Pakai: patch_v12217.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H + '/dei-tenant'
TAG = 'v1.2.217: laporan-crm'; NEED = 'v1.2.216: pipeline-sales'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12217-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ======================= api =======================
LIB = r'''/* ---------- v1.2.217: laporan-crm — performa sales & laporan mingguan via email (Growth+) ---------- */
if (!defined('CRM_WEEKLY_CONF')) define('CRM_WEEKLY_CONF', DATA_DIR . '/crm-weekly-conf.json');
if (!defined('CRM_WEEKLY_FILE')) define('CRM_WEEKLY_FILE', DATA_DIR . '/crm-weekly.json');
function crmWeeklyConf217() {
    $c = readJson(CRM_WEEKLY_CONF, []); if (!is_array($c)) $c = [];
    $ex = [];
    foreach ((array)($c['extra'] ?? []) as $e) { $e = deiValidEmail($e); if ($e !== '' && !in_array($e, $ex, true)) $ex[] = $e; }
    return ['on' => !array_key_exists('on', $c) || !empty($c['on']), 'dow' => max(1, min(7, (int)($c['dow'] ?? 1))), 'hour' => max(0, min(23, (int)($c['hour'] ?? 8))),
            'admins' => !array_key_exists('admins', $c) || !empty($c['admins']), 'sales' => !array_key_exists('sales', $c) || !empty($c['sales']), 'extra' => array_slice($ex, 0, 10)];
}
// Performa per Sales untuk rentang tanggal (Y-m-d, inklusif). $onlySid: batasi ke satu Sales.
function crmPerf217($fromD, $toD, $onlySid = null) {
    $fromTs = wibDayStart($fromD); $toTs = wibDayStart($toD);
    if ($fromTs === null || $toTs === null || $toTs < $fromTs) return null;
    $toTs += 86399;
    $map = slMap(); $pc = crmPipeConf216(); $open = crmOpenStatuses216(); $today = wibToday(); $in30 = wibDate('Y-m-d', time() + 30 * 86400);
    $mk = function ($id) use ($map) {
        return ['id' => $id, 'name' => $id === '' ? 'Tanpa sales' : (string)($map[$id]['name'] ?? '(sales dihapus)'), 'active' => $id !== '' && !empty($map[$id]['active']),
                'new' => 0, 'acts' => 0, 'by_type' => [], 'fu_done' => 0, 'fu_late' => 0, 'po' => 0, 'deal' => 0, 'deal_v' => 0, 'lost' => 0,
                'open' => 0, 'open_v' => 0, 'weighted' => 0, 'fc_n' => 0, 'fc_v' => 0, '_cy' => 0, '_cn' => 0];
    };
    $rows = [];
    foreach ($map as $id => $x) if (!empty($x['active'])) $rows[(string)$id] = $mk((string)$id);
    $row = function ($id) use (&$rows, $mk) { $id = (string)$id; if (!isset($rows[$id])) $rows[$id] = $mk($id); return $id; };
    $contacts = waGetContacts(); $leads = leadsGetAll(); $sidOf = []; $stOf = [];
    foreach ($leads as $num => $l) {
        if (!is_array($l)) continue;
        $num = (string)$num; $st = (string)($l['status'] ?? 'baru'); $v = (int)($l['value'] ?? 0);
        $sid = slLeadSalesId($l, $num, $contacts); $sidOf[$num] = $sid; $stOf[$num] = $st;
        $ct = strtotime((string)($l['created_at'] ?? ''));
        if ($ct && $ct >= $fromTs && $ct <= $toTs) $rows[$row($sid)]['new']++;
        if (in_array($st, ['closed_deal', 'closed_lost'], true)) {
            $t = (int)($l['closed_ts'] ?? 0);
            if ($t >= $fromTs && $t <= $toTs) {
                $k = $row($sid);
                if ($st === 'closed_deal') { $rows[$k]['deal']++; $rows[$k]['deal_v'] += $v; if ($ct && $t > $ct) { $rows[$k]['_cy'] += $t - $ct; $rows[$k]['_cn']++; } }
                else $rows[$k]['lost']++;
            }
        } elseif (in_array($st, $open, true)) {
            $k = $row($sid);
            $rows[$k]['open']++; $rows[$k]['open_v'] += $v; $rows[$k]['weighted'] += $v * (int)($pc[$st]['prob'] ?? 0) / 100;
            $ce = (string)($l['close_est'] ?? '');
            if ($ce !== '' && $ce >= $today && $ce <= $in30) { $rows[$k]['fc_n']++; $rows[$k]['fc_v'] += $v; }
        }
    }
    $users = [];
    foreach (crmActAll215() as $num => $list) {
        $num = (string)$num; if (!isset($sidOf[$num])) continue;
        $sid = $sidOf[$num]; $isOpen = in_array($stOf[$num], $open, true);
        foreach ((array)$list as $a) {
            if (!is_array($a)) continue;
            $ty = (string)($a['type'] ?? '');
            if ($ty !== 'sys') {
                $at = strtotime((string)($a['at'] ?? ''));
                if ($at && $at >= $fromTs && $at <= $toTs) {
                    $k = $row($sid); $rows[$k]['acts']++; $rows[$k]['by_type'][$ty] = ($rows[$k]['by_type'][$ty] ?? 0) + 1;
                    $bn = (string)($a['by_name'] ?? $a['by'] ?? ''); if ($onlySid === null || $sid === $onlySid) $users[$bn] = ($users[$bn] ?? 0) + 1;
                }
            }
            if (!empty($a['next_due'])) {
                if (!empty($a['next_done'])) { $dt = strtotime((string)($a['next_done_at'] ?? '')); if ($dt && $dt >= $fromTs && $dt <= $toTs) $rows[$row($sid)]['fu_done']++; }
                elseif ($isOpen && (string)$a['next_due'] < $today) $rows[$row($sid)]['fu_late']++;
            }
        }
    }
    foreach (slPoAll() as $p) {
        $t = wibDayStart((string)($p['date'] ?? ''));
        if ($t === null || $t < $fromTs || $t > $toTs) continue;
        $rows[$row((string)($p['sales'] ?? ''))]['po']++;
    }
    $sum = ['new', 'acts', 'fu_done', 'fu_late', 'po', 'deal', 'deal_v', 'lost', 'open', 'open_v', 'weighted', 'fc_n', 'fc_v', '_cy', '_cn'];
    $tot = array_fill_keys($sum, 0); $tot['by_type'] = []; $out = [];
    foreach ($rows as $id => $R) {
        if ($onlySid !== null && (string)$id !== $onlySid) continue;
        $any = false; foreach ($sum as $k) if ($R[$k]) $any = true;
        if (!$any && ((string)$id === '' || !$R['active'])) continue;
        foreach ($sum as $k) $tot[$k] += $R[$k];
        foreach ($R['by_type'] as $ty => $n) $tot['by_type'][$ty] = ($tot['by_type'][$ty] ?? 0) + $n;
        $out[] = $R;
    }
    $fin = function ($R) {
        $R['weighted'] = (int)round($R['weighted']);
        $R['win'] = ($R['deal'] + $R['lost']) ? (int)round($R['deal'] * 100 / ($R['deal'] + $R['lost'])) : null;
        $R['avg_deal'] = $R['deal'] ? (int)round($R['deal_v'] / $R['deal']) : 0;
        $R['cycle'] = $R['_cn'] ? round($R['_cy'] / $R['_cn'] / 86400, 1) : null;
        unset($R['_cy'], $R['_cn']);
        return $R;
    };
    $out = array_map($fin, $out); $tot = $fin($tot);
    usort($out, function ($a, $b) { return $b['deal_v'] <=> $a['deal_v'] ?: $b['deal'] <=> $a['deal'] ?: $b['acts'] <=> $a['acts'] ?: strcmp($a['name'], $b['name']); });
    arsort($users);
    $ul = []; foreach ($users as $n => $c) $ul[] = ['name' => $n !== '' ? $n : '-', 'acts' => $c];
    return ['from' => $fromD, 'to' => $toD, 'rows' => $out, 'total' => $tot, 'by_user' => array_slice($ul, 0, 30), 'types' => crmTypes215()];
}
function crmWeeklyMail217($to, $nm, $rep, $own, $test = false) {
    $brand = deiBrandProduct(); $biz = deiTenantName(getSettings());
    $e = function ($x) { return htmlspecialchars((string)$x, ENT_QUOTES, 'UTF-8'); };
    $d = function ($x) { return implode('/', array_reverse(explode('-', (string)$x))); };
    $T = $rep['total']; $rows = $rep['rows'];
    $per = $d($rep['from']) . ' – ' . $d($rep['to']);
    $subject = ($test ? '[Uji] ' : '') . 'Laporan mingguan ' . ($own ? 'Anda' : 'sales') . ' ' . $per . ' — ' . $biz;
    $tiles = [['Lead baru', (string)$T['new']], ['Aktivitas', (string)$T['acts']], ['Close Deal', $T['deal'] . ' · ' . crmRp216($T['deal_v'])],
              ['Win rate', $T['win'] === null ? '—' : $T['win'] . '%'], ['Pipeline terbuka', $T['open'] . ' · ' . crmRp216($T['open_v'])],
              ['Closing 30 hari ke depan', $T['fc_n'] . ' · ' . crmRp216($T['fc_v'])]];
    $lines = ['Halo ' . $nm . ',', 'Ringkasan ' . ($own ? 'kinerja Anda' : 'kinerja tim sales') . ' periode ' . $per . ':'];
    foreach ($tiles as $t) $lines[] = '• ' . $t[0] . ': ' . $t[1];
    $lines[] = '• PO: ' . $T['po'] . ' · Close Lose: ' . $T['lost'] . ' · Follow-up selesai: ' . $T['fu_done'] . ' · Follow-up terlambat (saat ini): ' . $T['fu_late'];
    if (!$own && $rows) {
        $lines[] = ''; $lines[] = 'Per sales:';
        foreach (array_slice($rows, 0, 30) as $R) $lines[] = '- ' . $R['name'] . ': ' . $R['new'] . ' lead baru, ' . $R['acts'] . ' aktivitas, ' . $R['deal'] . ' deal (' . crmRp216($R['deal_v']) . '), pipeline ' . crmRp216($R['open_v']);
    }
    $url = crmDashUrl215();
    $foot = 'Dikirim otomatis oleh ' . $brand . ' (' . deiWibNow() . '). Detail & periode lain: Leads > Performa di dashboard.';
    $text = implode("\n", $lines) . "\n\nBuka dashboard: " . $url . "\n\n" . $foot . "\n";
    $h = '<!DOCTYPE html><html><body style="margin:0;padding:24px;background:#f4f5fb;font-family:Arial,Helvetica,sans-serif;color:#15152b">'
       . '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">'
       . '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:680px;background:#fff;border:1px solid #e6e6ef;border-radius:14px"><tr><td style="padding:26px 26px 10px">'
       . '<div style="font-size:18px;font-weight:bold;margin-bottom:4px">Laporan mingguan ' . ($own ? 'Anda' : 'sales') . '</div>'
       . '<div style="font-size:13px;color:#6b6b82;margin-bottom:16px">' . $e($biz) . ' · ' . $e($per) . '</div>'
       . '<p style="font-size:14px;margin:0 0 14px">Halo ' . $e($nm) . ',</p>'
       . '<table role="presentation" width="100%" cellpadding="0" cellspacing="6" style="margin:0 -6px 8px"><tr>';
    foreach ($tiles as $i => $t) {
        if ($i === 3) $h .= '</tr><tr>';
        $h .= '<td width="33%" style="background:#f4f5fb;border-radius:10px;padding:10px 12px;vertical-align:top"><div style="font-size:11px;color:#6b6b82;text-transform:uppercase">' . $e($t[0]) . '</div>'
            . '<div style="font-size:16px;font-weight:bold;color:#140383;margin-top:3px">' . $e($t[1]) . '</div></td>';
    }
    $h .= '</tr></table><p style="font-size:13px;color:#44445a;margin:6px 0 16px">PO: <b>' . $T['po'] . '</b> · Close Lose: <b>' . $T['lost'] . '</b> · Follow-up selesai: <b>' . $T['fu_done'] . '</b> · Follow-up terlambat saat ini: <b' . ($T['fu_late'] ? ' style="color:#b91c1c"' : '') . '>' . $T['fu_late'] . '</b></p>';
    if (!$own && $rows) {
        $th = 'style="text-align:left;font-size:11px;color:#6b6b82;padding:6px 8px;border-bottom:1px solid #e6e6ef"';
        $td = 'style="font-size:13px;padding:7px 8px;border-bottom:1px solid #f0f0f5"';
        $h .= '<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-bottom:16px"><tr><th ' . $th . '>Sales</th><th ' . $th . '>Lead baru</th><th ' . $th . '>Aktivitas</th><th ' . $th . '>PO</th><th ' . $th . '>Deal</th><th ' . $th . '>Nilai deal</th><th ' . $th . '>Win</th><th ' . $th . '>Pipeline</th></tr>';
        foreach (array_slice($rows, 0, 30) as $R) {
            $h .= '<tr><td ' . $td . '><b>' . $e($R['name']) . '</b></td><td ' . $td . '>' . $R['new'] . '</td><td ' . $td . '>' . $R['acts'] . '</td><td ' . $td . '>' . $R['po'] . '</td><td ' . $td . '>' . $R['deal'] . '</td><td ' . $td . '>' . $e(crmRp216($R['deal_v'])) . '</td><td ' . $td . '>' . ($R['win'] === null ? '—' : $R['win'] . '%') . '</td><td ' . $td . '>' . $e(crmRp216($R['open_v'])) . '</td></tr>';
        }
        $h .= '</table>';
    }
    $h .= '<p style="margin:18px 0 20px"><a href="' . $e($url) . '" style="display:inline-block;background:#140383;color:#fff;text-decoration:none;font-weight:bold;font-size:14px;padding:12px 20px;border-radius:9px">Buka dashboard</a></p>'
        . '<p style="font-size:12px;color:#6b6b82;line-height:1.5;margin:0 0 14px;border-top:1px solid #e6e6ef;padding-top:14px">' . $e($foot) . '</p>'
        . '</td></tr></table></td></tr></table></body></html>';
    return deiSendMail($to, $subject, $text, $h, 'crm_weekly');
}
function crmWeeklyRecipients217($cf, $onlyUser = '') {   // [[email, nama, sid|null]] — admin & tambahan: laporan lengkap; sales: miliknya
    $out = []; $seen = [];
    foreach ((array)readJson(USERS_FILE, []) as $x) {
        if (!is_array($x) || empty($x['username']) || !empty($x['internal'])) continue;
        if ($onlyUser !== '' && $x['username'] !== $onlyUser) continue;
        $r = (string)($x['role'] ?? ''); $em = deiUserEmail($x);
        if ($em === '' || isset($seen[$em])) continue;
        $nm = trim((string)($x['name'] ?? '')) ?: (string)$x['username'];
        if (in_array($r, ['super_admin', 'admin'], true) && ($cf['admins'] || $onlyUser !== '')) { $out[] = [$em, $nm, null]; $seen[$em] = 1; }
        elseif ($r === 'sales' && ($cf['sales'] || $onlyUser !== '') && (string)($x['sales_id'] ?? '') !== '') { $out[] = [$em, $nm, (string)$x['sales_id']]; $seen[$em] = 1; }
    }
    if ($onlyUser === '') foreach ($cf['extra'] as $em) if (!isset($seen[$em])) { $out[] = [$em, $em, null]; $seen[$em] = 1; }
    return $out;
}
function crmWeeklySweep217($s) {
    if (!crmOk215()) return null;
    $cf = crmWeeklyConf217(); if (!$cf['on']) return null;
    if ((int)wibDate('N') !== $cf['dow'] || (int)wibDate('G') < $cf['hour']) return null;
    $wk = wibDate('o-\WW');
    $st = readJson(CRM_WEEKLY_FILE, []); if (!is_array($st)) $st = [];
    if (($st['week'] ?? '') === $wk && !empty($st['done'])) return null;
    if ((int)($st['_wait'] ?? 0) > time()) return null;
    if (($st['week'] ?? '') !== $wk) $st = ['week' => $wk, 'sent' => []];
    $from = wibDate('Y-m-d', time() - 7 * 86400); $to = wibDate('Y-m-d', time() - 86400);
    $full = crmPerf217($from, $to); if (!$full) return null;
    $res = ['mail' => 0, 'fail' => 0]; $left = false; $n = 0;
    foreach (crmWeeklyRecipients217($cf) as [$em, $nm, $sid]) {
        $k = md5($em); if (!empty($st['sent'][$k])) continue;
        if ($n >= 15) { $left = true; break; }
        $n++;
        $rep = $sid === null ? $full : crmPerf217($from, $to, $sid);
        $r = crmWeeklyMail217($em, $nm, $rep, $sid !== null);
        if (empty($r['ok']) && stripos((string)($r['error'] ?? ''), 'batas') !== false) { $st['_wait'] = time() + 900; $left = true; break; }
        if (!empty($r['ok'])) $res['mail']++; else { $res['fail']++; error_log('[crm-weekly] ' . deiMaskEmail($em) . ': ' . ($r['error'] ?? '')); }
        $st['sent'][$k] = 1;
    }
    $st['done'] = !$left; $st['period'] = [$from, $to];
    if (empty($GLOBALS['dei_dry'])) writeJson(CRM_WEEKLY_FILE, $st);
    return ($res['mail'] || $res['fail']) ? $res : null;
}
'''

CASES = r'''    /* ---------- v1.2.217: laporan-crm ---------- */
    case 'crm_sales_perf': {   // GET from, to (Y-m-d). Sales: hanya barisnya.
        $u = requireAuth(['super_admin', 'admin', 'supervisor']);
        crmGuard215();
        $fromD = (string)($_GET['from'] ?? wibDate('Y-m-01')); $toD = (string)($_GET['to'] ?? wibToday());
        $a = wibDayStart($fromD); $b = wibDayStart($toD);
        if ($a === null || $b === null || $b < $a) jsonOut(['ok' => false, 'error' => 'Rentang tanggal tidak valid (YYYY-MM-DD).'], 400);
        if ($b - $a > 370 * 86400) jsonOut(['ok' => false, 'error' => 'Rentang maksimal 1 tahun.'], 400);
        $only = ($u['role'] ?? '') === 'sales' ? crmMySales216($u) : null;
        if ($only === '') jsonOut(['ok' => false, 'error' => 'Akun Sales Anda belum terhubung ke data Sales.'], 400);
        jsonOut(['ok' => true, 'own' => $only !== null] + crmPerf217($fromD, $toD, $only));
        break;
    }
    case 'crm_weekly_get': {
        requireAuth(['super_admin', 'admin']);
        crmGuard215();
        $cf = crmWeeklyConf217();
        $noMail = [];
        foreach ((array)readJson(USERS_FILE, []) as $x) {
            if (is_array($x) && !empty($x['username']) && empty($x['internal']) && in_array(($x['role'] ?? ''), ['super_admin', 'admin', 'sales'], true) && deiUserEmail($x) === '') $noMail[] = (string)($x['name'] ?? $x['username']);
        }
        $st = readJson(CRM_WEEKLY_FILE, []);
        jsonOut(['ok' => true] + $cf + ['recipients' => count(crmWeeklyRecipients217($cf)), 'no_email' => $noMail, 'last_week' => (string)($st['week'] ?? ''), 'last_period' => $st['period'] ?? null]);
        break;
    }
    case 'crm_weekly_save': {   // body: on, dow, hour, admins, sales, extra (string/array)
        requireAuth(['super_admin', 'admin']);
        crmGuard215();
        $in = bodyInput();
        $ex = is_array($in['extra'] ?? null) ? $in['extra'] : preg_split('/[\s,;]+/', (string)($in['extra'] ?? ''));
        $ok = [];
        foreach ($ex as $e) { $e = trim((string)$e); if ($e === '') continue; $v = deiValidEmail($e); if ($v === '') jsonOut(['ok' => false, 'error' => 'Email tidak valid: ' . $e], 400); $ok[] = $v; }
        if (count($ok) > 10) jsonOut(['ok' => false, 'error' => 'Maksimal 10 email tambahan.'], 400);
        writeJson(CRM_WEEKLY_CONF, ['on' => !empty($in['on']), 'dow' => max(1, min(7, (int)($in['dow'] ?? 1))), 'hour' => max(0, min(23, (int)($in['hour'] ?? 8))),
                                    'admins' => !empty($in['admins']), 'sales' => !empty($in['sales']), 'extra' => array_values(array_unique($ok))]);
        jsonOut(['ok' => true] + crmWeeklyConf217());
        break;
    }
    case 'crm_weekly_test': {   // kirim laporan 7 hari terakhir ke email saya
        $u = requireAuth(['super_admin', 'admin']);
        crmGuard215();
        $rc = crmWeeklyRecipients217(crmWeeklyConf217(), (string)$u['username']);
        if (!$rc) jsonOut(['ok' => false, 'error' => 'Akun Anda belum punya email. Isi email di menu Pengguna dulu.'], 400);
        [$em, $nm] = $rc[0];
        $rep = crmPerf217(wibDate('Y-m-d', time() - 7 * 86400), wibDate('Y-m-d', time() - 86400));
        $r = crmWeeklyMail217($em, $nm, $rep, false, true);
        if (empty($r['ok'])) jsonOut(['ok' => false, 'error' => 'Email gagal dikirim: ' . ($r['error'] ?? '-')], 502);
        jsonOut(['ok' => true, 'to' => deiMaskEmail($em)]);
        break;
    }

'''

s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API)
else:
    assert NEED in s, 'v1.2.216 belum terpasang di ' + API
    s = rep(s, "define('DEI_VERSION', 'v1.2.216');   // v1.2.216:",
            "define('DEI_VERSION', 'v1.2.217');   // " + TAG + " — Leads > Performa (laporan performa sales per periode, CSV) + laporan mingguan via email; v1.2.216:", what='ver')
    s = rep(s, "\nfunction deiGuardAgentPrivate($u, $num) {", "\n" + LIB + "function deiGuardAgentPrivate($u, $num) {", what='lib')
    s = rep(s, "    /* ---------- v1.2.216: pipeline-sales ---------- */\n", CASES + "    /* ---------- v1.2.216: pipeline-sales ---------- */\n", what='cases')
    s = rep(s, "'crm_badge', 'crm_remind_test', 'tasks_list',", "'crm_badge', 'crm_remind_test', 'crm_sales_perf', 'tasks_list',", what='sales-actions')
    s = rep(s, "        try { $crr = crmRemindSweep215($s);",
            "        try { $cwr = crmWeeklySweep217($s); if ($cwr) $r['crm_weekly'] = $cwr; } catch (\\Throwable $e) { $r['err_crm_weekly'] = $e->getMessage(); }   // " + TAG + "\n"
            "        try { $crr = crmRemindSweep215($s);", what='cron')
    save(API, s)

# ======================= dashboard: app.js =======================
JSLIB = r'''
  /* ====================================================================== *
   *  v1.2.217: laporan-crm — Leads > Performa + laporan mingguan via email
   * ====================================================================== */
  var crmPerfS217 = { preset: 'lastweek', from: '', to: '', data: null, busy: false };
  try { var _pp = localStorage.getItem('dei_perf_preset'); if (_pp) crmPerfS217.preset = _pp; } catch (e) {}
  function crmYmd217(d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  function crmRange217(p) {
    var t = new Date(); t.setHours(12, 0, 0, 0);
    var dow = (t.getDay() + 6) % 7;   // 0 = Senin
    var a = new Date(t), b = new Date(t);
    if (p === 'thisweek') { a.setDate(t.getDate() - dow); }
    else if (p === 'lastweek') { a.setDate(t.getDate() - dow - 7); b.setDate(t.getDate() - dow - 1); }
    else if (p === 'thismonth') { a.setDate(1); }
    else if (p === 'lastmonth') { a = new Date(t.getFullYear(), t.getMonth() - 1, 1, 12); b = new Date(t.getFullYear(), t.getMonth(), 0, 12); }
    else if (p === 'last7') { a.setDate(t.getDate() - 6); }
    else { a.setDate(t.getDate() - 29); }   // last30
    return [crmYmd217(a), crmYmd217(b)];
  }
  var CRM_PRESETS = { lastweek: 'Minggu lalu', thisweek: 'Minggu ini', last7: '7 hari terakhir', thismonth: 'Bulan ini', lastmonth: 'Bulan lalu', last30: '30 hari terakhir', custom: 'Pilih tanggal' };
  function crmPerfRender217() {
    var box = $('#leadList'); if (!box) return;
    if (!leadCrm215) { box.innerHTML = '<div class="card" style="text-align:center;color:var(--muted)">Laporan performa tersedia mulai paket Growth.</div>'; return; }
    var S = crmPerfS217;
    if (S.preset !== 'custom' || !S.from) { var r = crmRange217(S.preset); S.from = S.from && S.preset === 'custom' ? S.from : r[0]; S.to = S.preset === 'custom' && S.to ? S.to : r[1]; }
    var adm = user.role === 'super_admin' || user.role === 'admin';
    if (!box.querySelector('#crmPerfBar')) {
      box.innerHTML = '<div class="card crm-perf"><div class="crm-perf-bar" id="crmPerfBar">' +
        '<select id="crmPerfPre" style="width:auto">' + Object.keys(CRM_PRESETS).map(function (k) { return '<option value="' + k + '"' + (k === S.preset ? ' selected' : '') + '>' + CRM_PRESETS[k] + '</option>'; }).join('') + '</select>' +
        '<input type="date" id="crmPerfFrom"><span class="help">s/d</span><input type="date" id="crmPerfTo">' +
        '<button type="button" class="btn ghost sm" id="crmPerfGo">Tampilkan</button>' +
        '<button type="button" class="btn ghost sm" id="crmPerfCsv">' + ico('download', 14) + ' CSV</button>' +
        (adm ? '<button type="button" class="btn ghost sm" id="crmWeekBtn" style="margin-left:auto">' + ico('mail', 14) + ' Laporan mingguan</button>' : '') +
        '</div><div id="crmPerfBody"><div class="help">Memuat…</div></div></div>';
      var pre = $('#crmPerfPre'), f = $('#crmPerfFrom'), t = $('#crmPerfTo');
      pre.onchange = function () {
        S.preset = pre.value; try { localStorage.setItem('dei_perf_preset', S.preset); } catch (e) {}
        if (S.preset !== 'custom') { var r = crmRange217(S.preset); S.from = r[0]; S.to = r[1]; f.value = S.from; t.value = S.to; crmPerfLoad217(); }
      };
      var cust = function () { S.preset = 'custom'; pre.value = 'custom'; };
      f.onchange = cust; t.onchange = cust;
      $('#crmPerfGo').onclick = function () { S.from = f.value; S.to = t.value; crmPerfLoad217(); };
      $('#crmPerfCsv').onclick = crmPerfCsv217;
      if ($('#crmWeekBtn')) $('#crmWeekBtn').onclick = crmWeekly217;
    }
    $('#crmPerfFrom').value = S.from; $('#crmPerfTo').value = S.to;
    crmPerfLoad217();
  }
  function crmPerfLoad217() {
    var S = crmPerfS217, body = $('#crmPerfBody'); if (!body) return;
    if (!S.from || !S.to) { toast('Isi tanggal awal & akhir.', true); return; }
    body.style.opacity = '.5';
    api('crm_sales_perf', { query: '&from=' + encodeURIComponent(S.from) + '&to=' + encodeURIComponent(S.to) }).then(function (r) {
      body.style.opacity = '';
      if (!r || !r.ok) { body.innerHTML = '<div class="help">' + esc((r && r.error) || 'Gagal memuat laporan.') + '</div>'; return; }
      S.data = r; crmPerfPaint217();
    });
  }
  function crmPerfRows217() {
    var r = crmPerfS217.data; if (!r) return [];
    if (!leadSales203 || r.own) return r.rows;
    var want = leadSales203 === '_none' ? '' : leadSales203;
    return r.rows.filter(function (x) { return x.id === want; });
  }
  function crmPerfPaint217() {
    var r = crmPerfS217.data, body = $('#crmPerfBody'); if (!r || !body) return;
    var rows = crmPerfRows217(), T = (leadSales203 && !r.own) ? (rows[0] || r.total) : r.total;
    var per = crmFmtD215(r.from) + ' – ' + crmFmtD215(r.to);
    var tile = function (l, b, s, c) { return '<div class="crm-pt' + (c ? ' ' + c : '') + '"><div class="crm-pt-l">' + l + '</div><div class="crm-pt-b">' + b + '</div><div class="crm-pt-s">' + s + '</div></div>'; };
    var types = r.types || {};
    var bt = Object.keys(T.by_type || {}).sort(function (a, b) { return T.by_type[b] - T.by_type[a]; }).map(function (k) { return esc(types[k] || k) + ' ' + T.by_type[k]; }).join(' · ');
    var h = '<div class="crm-perf-per">' + (r.own ? 'Kinerja Anda' : 'Semua sales' + (leadSales203 ? ' (filter sales aktif)' : '')) + ' · ' + esc(per) + '</div>' +
      '<div class="crm-pts">' +
        tile('Lead baru', T.new, 'dibuat dalam periode') +
        tile('Aktivitas', T.acts, bt || 'belum ada') +
        tile('Close Deal', esc(crmRpShort216(T.deal_v)), T.deal + ' deal · rata-rata ' + esc(crmRpShort216(T.avg_deal)), 'good') +
        tile('Win rate', T.win === null ? '—' : T.win + '%', T.deal + ' deal · ' + T.lost + ' lose' + (T.cycle !== null ? ' · ±' + String(T.cycle).replace('.', ',') + ' hari closing' : '')) +
        tile('Pipeline terbuka (saat ini)', esc(crmRpShort216(T.open_v)), T.open + ' lead · tertimbang ' + esc(crmRpShort216(T.weighted))) +
        tile('Follow-up', T.fu_done + ' selesai', T.fu_late + ' terlambat saat ini · PO ' + T.po, T.fu_late ? 'bad' : '') +
      '</div>';
    if (!r.own) {
      h += '<div class="scroll" style="margin-top:12px"><table class="tbl crm-perf-t"><thead><tr><th>Sales</th><th>Lead baru</th><th>Aktivitas</th><th>FU selesai</th><th>FU telat</th><th>PO</th><th>Deal</th><th>Nilai deal</th><th>Lose</th><th>Win</th><th>Lama closing</th><th>Pipeline</th><th>Tertimbang</th><th>Closing 30 hr</th></tr></thead><tbody>' +
        (rows.length ? rows.map(function (x) {
          return '<tr><td><b>' + esc(x.name) + '</b>' + (x.active || !x.id ? '' : ' <span class="help">(nonaktif)</span>') + '</td><td>' + x.new + '</td><td title="' + esc(Object.keys(x.by_type || {}).map(function (k) { return (types[k] || k) + ': ' + x.by_type[k]; }).join(', ')) + '">' + x.acts + '</td>' +
            '<td>' + x.fu_done + '</td><td' + (x.fu_late ? ' style="color:#b91c1c;font-weight:600"' : '') + '>' + x.fu_late + '</td><td>' + x.po + '</td><td>' + x.deal + '</td><td>' + esc(crmRpFmt216(x.deal_v)) + '</td><td>' + x.lost + '</td>' +
            '<td>' + (x.win === null ? '—' : x.win + '%') + '</td><td>' + (x.cycle === null ? '—' : String(x.cycle).replace('.', ',') + ' hr') + '</td><td>' + esc(crmRpShort216(x.open_v)) + ' <span class="help">(' + x.open + ')</span></td><td>' + esc(crmRpShort216(x.weighted)) + '</td><td>' + esc(crmRpShort216(x.fc_v)) + ' <span class="help">(' + x.fc_n + ')</span></td></tr>';
        }).join('') : '<tr><td colspan="14" class="help">Belum ada data Sales. Tambah di Laporan &amp; Log &gt; Per Sales.</td></tr>') +
        '</tbody></table></div>';
      if ((r.by_user || []).length) h += '<div class="crm-perf-u"><b>Aktivitas per pencatat:</b> ' + r.by_user.map(function (x) { return esc(x.name) + ' ' + x.acts; }).join(' · ') + '</div>';
    }
    h += '<p class="help" style="margin-top:10px">Lead baru, aktivitas, follow-up selesai, PO dan Close Deal/Lose dihitung dalam periode. Pipeline, nilai tertimbang, follow-up terlambat dan closing 30 hari = kondisi saat ini. Aktivitas dihitung ke sales pemilik lead.</p>';
    body.innerHTML = h;
  }
  function crmPerfCsv217() {
    var r = crmPerfS217.data; if (!r) return;
    var rows = crmPerfRows217(), q = function (v) { v = String(v === null || v === undefined ? '' : v); return /[",\n;]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var L = [['Sales', 'Lead baru', 'Aktivitas', 'Follow-up selesai', 'Follow-up terlambat', 'PO', 'Close Deal', 'Nilai deal (Rp)', 'Close Lose', 'Win rate (%)', 'Rata-rata nilai deal', 'Lama closing (hari)', 'Pipeline terbuka', 'Nilai pipeline (Rp)', 'Nilai tertimbang (Rp)', 'Closing 30 hari', 'Nilai closing 30 hari (Rp)'].join(',')];
    rows.concat(rows.length > 1 ? [Object.assign({ name: 'TOTAL' }, r.total)] : []).forEach(function (x) {
      L.push([x.name, x.new, x.acts, x.fu_done, x.fu_late, x.po, x.deal, x.deal_v, x.lost, x.win, x.avg_deal, x.cycle, x.open, x.open_v, x.weighted, x.fc_n, x.fc_v].map(q).join(','));
    });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob(['﻿' + L.join('\n')], { type: 'text/csv;charset=utf-8' }));
    a.download = 'performa-sales-' + r.from + '_' + r.to + '.csv';
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }
  function crmWeekly217() {
    api('crm_weekly_get').then(function (r) {
      if (!r || !r.ok) { toast((r && r.error) || 'Gagal memuat pengaturan.', true); return; }
      var days = ['', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'], hrs = '';
      for (var h = 5; h <= 20; h++) hrs += '<option value="' + h + '"' + (h === r.hour ? ' selected' : '') + '>' + String(h).padStart(2, '0') + ':00 WIB</option>';
      tkModal214(ico('mail', 17) + ' Laporan mingguan',
        '<p class="crm-p">Setiap minggu, ringkasan <b>7 hari terakhir</b> dikirim lewat email: lead baru, aktivitas, PO, Close Deal (Rp), win rate, pipeline, dan follow-up terlambat. Admin menerima laporan seluruh sales; akun Sales menerima laporannya sendiri.</p>' +
        '<label class="crm-ck"><input type="checkbox" class="cw-on"' + (r.on ? ' checked' : '') + '> Kirim laporan mingguan</label>' +
        '<div class="tk-grid" style="margin-top:10px"><div class="row"><label class="fl">Hari kirim</label><select class="cw-dow">' + days.slice(1).map(function (d, i) { return '<option value="' + (i + 1) + '"' + (i + 1 === r.dow ? ' selected' : '') + '>' + d + '</option>'; }).join('') + '</select></div>' +
        '<div class="row"><label class="fl">Jam kirim</label><select class="cw-h">' + hrs + '</select></div></div>' +
        '<label class="crm-ck" style="font-weight:400"><input type="checkbox" class="cw-adm"' + (r.admins ? ' checked' : '') + '> Super Admin &amp; Admin (laporan lengkap)</label>' +
        '<label class="crm-ck" style="font-weight:400;margin-top:6px"><input type="checkbox" class="cw-sales"' + (r.sales ? ' checked' : '') + '> Akun Sales (laporan masing-masing)</label>' +
        '<div class="row" style="margin-top:10px"><label class="fl">Email tambahan (laporan lengkap, maks. 10, pisahkan koma)</label><input type="text" class="cw-ex" value="' + esc((r.extra || []).join(', ')) + '" placeholder="owner@perusahaan.com"></div>' +
        '<p class="crm-p">' + r.recipients + ' penerima dengan pengaturan saat ini' + (r.last_week ? ' · terakhir terkirim minggu ' + esc(r.last_week) : '') + '.</p>' +
        (r.no_email && r.no_email.length ? '<p class="crm-p crm-warn">Belum punya email (tidak menerima): ' + r.no_email.map(esc).join(', ') + '. Isi email di menu Pengguna.</p>' : '') +
        '<div class="tk-foot"><button type="button" class="btn ghost sm cw-test" style="margin-right:auto">' + ico('send', 14) + ' Kirim uji ke email saya</button><button type="button" class="btn ghost tk-x">Batal</button><button type="button" class="btn cw-save">Simpan</button></div>',
        function (ov, close) {
          ov.querySelector('.cw-save').onclick = function () {
            api('crm_weekly_save', { method: 'POST', body: { on: ov.querySelector('.cw-on').checked ? 1 : 0, dow: +ov.querySelector('.cw-dow').value, hour: +ov.querySelector('.cw-h').value,
              admins: ov.querySelector('.cw-adm').checked ? 1 : 0, sales: ov.querySelector('.cw-sales').checked ? 1 : 0, extra: ov.querySelector('.cw-ex').value } }).then(function (x) {
              if (!x || !x.ok) { toast((x && x.error) || 'Gagal menyimpan.', true); return; }
              close(); toast('Pengaturan laporan mingguan disimpan.');
            });
          };
          ov.querySelector('.cw-test').onclick = function () {
            var bt = this; bt.disabled = true;
            api('crm_weekly_test', { method: 'POST', body: {} }).then(function (x) {
              bt.disabled = false;
              if (!x || !x.ok) { toast((x && x.error) || 'Gagal mengirim email uji.', true); return; }
              toast('Laporan uji terkirim ke ' + x.to + '.');
            });
          };
        });
    });
  }

'''

HELP_ADD = r'''    { id: 'performa', roles: R_ALL, t: 'Laporan performa sales & laporan mingguan', k: 'laporan performa sales kinerja mingguan weekly report email win rate close deal pipeline aktivitas csv',   // v1.2.217: laporan-crm
      s: ['Buka <b>Leads</b>, klik tampilan <b>Performa</b>. Pilih periode (Minggu lalu, Bulan ini, dst. atau tanggal sendiri).', 'Tabel per sales: lead baru, aktivitas, follow-up, PO, Close Deal (jumlah &amp; Rp), win rate, lama closing, pipeline dan perkiraan closing. Unduh lewat <b>CSV</b>. Akun Sales hanya melihat kinerjanya sendiri.', 'Admin: tombol <b>Laporan mingguan</b> untuk mengatur email otomatis (hari, jam, penerima) dan mengirim uji.'],
      show: [{ tab: 'leads', el: '#panel-leads .card', title: 'Performa', body: '<p>Klik <b>Performa</b> di samping Daftar / Kanban.</p>' }] },
'''

j = open(JS, encoding='utf-8').read()
if TAG in j: print('SUDAH', JS)
else:
    assert NEED in j, 'v1.2.216 belum terpasang di app.js'
    j = rep(j, "  // v1.2.147: leads-kanban — pilihan tampilan diingat per browser\n", JSLIB + "  // v1.2.147: leads-kanban — pilihan tampilan diingat per browser\n", what='js-lib')
    j = rep(j, "    { id: 'kontak', roles: R_ALL,", HELP_ADD + "    { id: 'kontak', roles: R_ALL,", what='js-help')
    j = rep(j, "  try { leadView = localStorage.getItem('dei_lead_view') === 'kanban' ? 'kanban' : 'list'; } catch (e) {}",
            "  try { var _lv217 = localStorage.getItem('dei_lead_view'); leadView = (_lv217 === 'kanban' || _lv217 === 'perf') ? _lv217 : 'list'; } catch (e) {}   // " + TAG, what='js-lvinit')
    j = rep(j, "p.classList.toggle('lk-on', leadView === 'kanban');", "p.classList.toggle('lk-on', leadView !== 'list');   /* " + TAG + " */", what='js-lvapply')
    j = rep(j, "    if (leadView === 'kanban') { renderLeadsKanban(); return; }   // v1.2.147: leads-kanban",
            "    if (leadView === 'perf') { crmPerfRender217(); return; }   // " + TAG + "\n"
            "    if (leadView === 'kanban') { renderLeadsKanban(); return; }   // v1.2.147: leads-kanban", what='js-render')
    j = rep(j, "    sel.onchange = function () { leadSales203 = sel.value; leadData = slLeadFilt203(leadAll203); renderLeads(); };",
            "    sel.onchange = function () { leadSales203 = sel.value; leadData = slLeadFilt203(leadAll203); if (leadView === 'perf' && crmPerfS217.data) { crmPipeRender216(); crmPerfPaint217(); return; } renderLeads(); };   // " + TAG, what='js-salesflt')
    save(JS, j)

# ======================= dashboard: index.html =======================
CSS = r'''  /* v1.2.217: laporan-crm */
  .lk-view .btn + .btn{margin-left:-1px}
  .crm-perf{padding:14px 16px}
  .crm-perf-bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
  .crm-perf-bar input[type=date]{width:auto;padding:6px 8px}
  .crm-perf-bar select{padding:6px 8px}
  .crm-perf-per{font-size:12.5px;color:var(--muted);margin-bottom:8px}
  .crm-perf-t th,.crm-perf-t td{white-space:nowrap;font-size:13px}
  .crm-perf-t td:not(:first-child),.crm-perf-t th:not(:first-child){text-align:right}
  .crm-perf-u{margin-top:10px;font-size:12.5px;color:var(--muted)}
  .crm-perf-u b{color:var(--text,#15152b)}
'''
h = open(HT, encoding='utf-8').read()
if TAG in h: print('SUDAH', HT)
else:
    assert NEED in h, 'v1.2.216 belum terpasang di index.html'
    h = rep(h, '  .lk-empty{', CSS + '  .lk-empty{', what='html-css')
    h = rep(h, '<button type="button" class="btn ghost sm" data-lead-view="kanban">Kanban</button>',
            '<button type="button" class="btn ghost sm" data-lead-view="kanban">Kanban</button><button type="button" class="btn ghost sm" data-lead-view="perf">Performa</button><!-- ' + TAG + ' -->', what='html-view')
    h = rep(h, '<script src="app.js?v=1.2.216"></script>', '<script src="app.js?v=1.2.217"></script><!-- ' + TAG + ' -->', what='html-ver')
    save(HT, h)
print('SELESAI patch', TAG)
