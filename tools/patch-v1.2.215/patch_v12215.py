#!/usr/bin/env python3
"""v1.2.215 (crm-aktivitas): CRM tahap 1 — Growth+.
- Leads: tombol "+ Lead manual" (nama, HP/WA, perusahaan, email, sumber, status, sales, catatan).
- Per lead: modal "Aktivitas & Task" — catat aktivitas sales (telepon, chat WA, meeting, kunjungan,
  email, presentasi, kirim penawaran, lainnya) + follow-up berikutnya (tanggal/jam/rencana, centang Selesai),
  activity record otomatis (status, catatan, tag sales, PO, Close Deal, task dibuat), info lead bisa diedit,
  tab Task: task tertaut lead (+ Task untuk lead ini).
- Kartu lead: chip follow-up (hari ini / terlambat), badge merah di menu Leads = follow-up saya yang jatuh tempo.
- Task: kartu & detail menampilkan lead tertaut.
- Pengingat jatuh tempo: cron kirim 1 email ringkasan per pengguna per hari (task + follow-up yang jatuh tempo
  hari ini, besok, atau terlambat) + notifikasi push. Admin: Pengingat (on/off, jam kirim, kirim uji).
- Pusat: mail_relay mengizinkan jenis email crm_remind & crm_weekly.
Data: data/lead_activity.json, data/crm-remind.json, data/crm-remind-conf.json.
Butuh v1.2.214. Idempoten. Pakai: patch_v12215.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H + '/dei-tenant'; P = H + '/dei-pusat'
TAG = 'v1.2.215: crm-aktivitas'; NEED = 'v1.2.214: task'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s, bakdir=None):
    if not NOBAK:
        if bakdir: os.makedirs(bakdir, exist_ok=True); shutil.copy2(p, bakdir + '/' + os.path.basename(p) + '.bak-v12215-' + stamp)
        else: shutil.copy2(p, p + '.bak-v12215-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'
PB = P + '/backend/index.php'

# ======================= pusat: mail_relay =======================
pb = open(PB, encoding='utf-8').read()
if 'crm_remind' in pb: print('SUDAH', PB)
else:
    pb = rep(pb, "if (!in_array($kind, ['pw_reset', 'pw_changed'], true))",
             "if (!in_array($kind, ['pw_reset', 'pw_changed', 'crm_remind', 'crm_weekly'], true))   // " + TAG, what='pusat-kind')
    save(PB, pb, H + '/master-build/tools/patch-v1.2.215/bak-pusat')   # cadangan JANGAN di folder pusat (ikut ter-deploy)

# ======================= api =======================
LIB = r'''/* ---------- v1.2.215: crm-aktivitas — lead manual, aktivitas sales, activity record, pengingat (Growth+) ----------
 * data/lead_activity.json = {num: [{id, type, at 'Y-m-d H:i', text, next_due 'Y-m-d', next_time 'H:i', next_text,
 *                                  next_done, next_done_at, next_done_by, next_done_by_name, by, by_name, created_at}]}
 * type 'sys' = catatan otomatis (activity record), tidak bisa dihapus. */
if (!defined('CRM_ACT_FILE')) define('CRM_ACT_FILE', DATA_DIR . '/lead_activity.json');
if (!defined('CRM_REMIND_FILE')) define('CRM_REMIND_FILE', DATA_DIR . '/crm-remind.json');
if (!defined('CRM_REMIND_CONF')) define('CRM_REMIND_CONF', DATA_DIR . '/crm-remind-conf.json');
if (!defined('CRM_ACT_MAX')) define('CRM_ACT_MAX', 500);
function crmTypes215() { return ['call' => 'Telepon', 'wa' => 'Chat WA', 'meeting' => 'Meeting', 'visit' => 'Kunjungan', 'email' => 'Email', 'presentasi' => 'Presentasi / Demo', 'penawaran' => 'Kirim penawaran', 'other' => 'Lainnya']; }
function crmSources215() { return ['manual' => 'Input manual', 'referensi' => 'Referensi', 'telepon' => 'Telepon masuk', 'walkin' => 'Walk-in / datang langsung', 'event' => 'Event / pameran', 'website' => 'Website', 'sosmed' => 'Media sosial', 'iklan' => 'Iklan', 'lainnya' => 'Lainnya']; }
function crmOk215() { return slPlanOk(); }
function crmGuard215() {
    if (!crmOk215()) jsonOut(['ok' => false, 'locked' => true, 'error' => 'Fitur CRM (lead manual, aktivitas sales & pengingat) tersedia mulai paket Growth. Hubungi ' . deiBrandVendor() . ' untuk upgrade paket.'], 403);
}
function crmNormNum215($n) {
    $n = preg_replace('/\D/', '', (string)$n);
    if ($n === '') return '';
    if ($n[0] === '0') $n = '62' . substr($n, 1);
    elseif ($n[0] === '8') $n = '62' . $n;
    return (strlen($n) >= 9 && strlen($n) <= 15) ? $n : '';
}
function crmActAll215() { $a = readJson(CRM_ACT_FILE, []); return is_array($a) ? $a : []; }
function crmActFor215($num) { $a = crmActAll215(); return array_values(array_filter((array)($a[$num] ?? []), 'is_array')); }
function crmLeadName215($num) {
    static $c = [];
    if (isset($c[$num])) return $c[$num];
    $n = '';
    try { $n = (string)waContactName($num); } catch (\Throwable $e) {}
    if ($n === '') { $l = leadsGetAll()[$num] ?? null; if (is_array($l)) $n = trim((string)($l['name'] ?? '')) ?: trim((string)($l['extracted']['nama'] ?? '')); }
    return $c[$num] = $n;
}
function crmLog215($num, $text, $u = null) {   // activity record otomatis
    $num = waNormNum($num); if ($num === '') return;
    try {
        [$me, $meName] = $u ? tkMe214($u) : ['', 'Sistem'];
        deiWithLock('lead-act', function () use ($num, $text, $me, $meName) {
            $all = crmActAll215();
            $l = array_values(array_filter((array)($all[$num] ?? []), 'is_array'));
            $now = date('Y-m-d H:i:s');
            $l[] = ['id' => 'a' . bin2hex(random_bytes(5)), 'type' => 'sys', 'at' => substr($now, 0, 16), 'text' => tkClean214($text, 500),
                    'by' => $me, 'by_name' => $meName, 'created_at' => $now];
            $all[$num] = array_slice($l, -CRM_ACT_MAX);
            writeJson(CRM_ACT_FILE, $all);
        });
    } catch (\Throwable $e) { error_log('crmLog215: ' . $e->getMessage()); }
}
function crmSummaryAll215() {   // {num: {n, last, fu:{id,due,time,text,by,by_name}|null}}
    $o = [];
    foreach (crmActAll215() as $num => $list) {
        $n = 0; $last = ''; $fu = null; $fk = '';
        foreach ((array)$list as $a) {
            if (!is_array($a)) continue;
            if (($a['type'] ?? '') !== 'sys') { $n++; if ((string)($a['at'] ?? '') > $last) $last = (string)$a['at']; }
            if (!empty($a['next_due']) && empty($a['next_done'])) {
                $k = $a['next_due'] . ' ' . ($a['next_time'] ?? '');
                if ($fu === null || $k < $fk) {
                    $fk = $k;
                    $fu = ['id' => (string)($a['id'] ?? ''), 'due' => (string)$a['next_due'], 'time' => (string)($a['next_time'] ?? ''), 'text' => (string)($a['next_text'] ?? ''),
                           'by' => (string)($a['by'] ?? ''), 'by_name' => (string)($a['by_name'] ?? '')];
                }
            }
        }
        $o[(string)$num] = ['n' => $n, 'last' => $last, 'fu' => $fu];
    }
    return $o;
}
function crmActPublic215($u, $acts) {
    $me = (string)($u['username'] ?? ''); $lead = deiIsLead($u['role'] ?? '');
    $out = [];
    foreach (array_reverse($acts) as $a) {
        $a['can_del'] = ($a['type'] ?? '') !== 'sys' && ($lead || ($a['by'] ?? '') === $me);
        $out[] = $a;
    }
    return $out;
}
function crmRemindConf215() {
    $c = readJson(CRM_REMIND_CONF, []); if (!is_array($c)) $c = [];
    return ['on' => !array_key_exists('on', $c) || !empty($c['on']), 'hour' => max(0, min(23, (int)($c['hour'] ?? 7)))];
}
function crmDashUrl215() {
    $r = deiRememberedApiUrl();
    if ($r !== '' && preg_match('#^(https?://.+?)/api/index\.php#', $r, $m)) return $m[1] . '/dashboard/chatbot-ai/';
    return deiDashboardUrl();
}
// Yang jatuh tempo s/d besok per pengguna: task (assignee) + follow-up lead (pencatat aktivitas)
function crmDueItems215($tomorrow, $onlyUser = '') {
    $out = [];
    foreach (tkAll214() as $t) {
        if (!is_array($t) || empty($t['assignee']) || empty($t['due'])) continue;
        if ($onlyUser !== '' && $t['assignee'] !== $onlyUser) continue;
        if (!in_array((string)($t['status'] ?? ''), ['new', 'progress', 'pending'], true) || (string)$t['due'] > $tomorrow) continue;
        $out[$t['assignee']]['tasks'][] = $t;
    }
    $leads = leadsGetAll();
    foreach (crmActAll215() as $num => $list) {
        $num = (string)$num; $l = $leads[$num] ?? null;
        if (!is_array($l) || in_array((string)($l['status'] ?? ''), ['closed_deal', 'closed_lost', 'closed'], true)) continue;
        foreach ((array)$list as $a) {
            if (!is_array($a) || empty($a['next_due']) || !empty($a['next_done']) || empty($a['by'])) continue;
            if ($onlyUser !== '' && $a['by'] !== $onlyUser) continue;
            if ((string)$a['next_due'] > $tomorrow) continue;
            $a['num'] = $num;
            $out[$a['by']]['fu'][] = $a;
        }
    }
    return $out;
}
function crmRemindMail215($u, $to, $it, $today, $tomorrow, $test = false) {
    $brand = deiBrandProduct(); $biz = deiTenantName(getSettings());
    $nm = trim((string)($u['name'] ?? '')) ?: (string)$u['username'];
    $fmt = function ($d) { $p = explode('-', (string)$d); return count($p) === 3 ? $p[2] . '/' . $p[1] . '/' . $p[0] : (string)$d; };
    $when = function ($d) use ($today, $fmt) { return $d < $today ? 'TERLAMBAT (' . $fmt($d) . ')' : ($d === $today ? 'hari ini' : 'besok (' . $fmt($d) . ')'); };
    $tasks = (array)($it['tasks'] ?? []); $fus = (array)($it['fu'] ?? []);
    usort($tasks, function ($a, $b) { return strcmp((string)$a['due'], (string)$b['due']); });
    usort($fus, function ($a, $b) { return strcmp($a['next_due'] . ($a['next_time'] ?? ''), $b['next_due'] . ($b['next_time'] ?? '')); });
    $lines = []; $late = 0; $ty = crmTypes215();
    foreach ($tasks as $t) { if ($t['due'] < $today) $late++; $lines[] = '• Task: ' . $t['title'] . ' — ' . $when($t['due']); }
    foreach ($fus as $a) {
        if ($a['next_due'] < $today) $late++;
        $ln = crmLeadName215($a['num']); $who = $ln !== '' ? $ln . ' (+' . $a['num'] . ')' : '+' . $a['num'];
        $lines[] = '• Follow-up ' . $who . ': ' . (trim((string)($a['next_text'] ?? '')) !== '' ? $a['next_text'] : ($ty[$a['type'] ?? ''] ?? 'tindak lanjut'))
                 . ' — ' . $when($a['next_due']) . (!empty($a['next_time']) ? ' jam ' . $a['next_time'] : '');
    }
    $total = count($lines);
    if ($total > 40) { $more = $total - 40; $lines = array_slice($lines, 0, 40); $lines[] = '… dan ' . $more . ' lainnya di dashboard.'; }
    if (!$total) $lines[] = 'Tidak ada task atau follow-up yang jatuh tempo saat ini.';
    $subject = ($test ? '[Uji] ' : '') . 'Pengingat: ' . $total . ' task & follow-up jatuh tempo' . ($late ? ' (' . $late . ' terlambat)' : '') . ' — ' . $biz;
    $p = array_merge(['Halo ' . $nm . ',',
        $test ? 'Ini email uji pengingat jatuh tempo. Isinya sama dengan email harian Anda saat ini:' : 'Berikut task dan follow-up lead Anda yang jatuh tempo hari ini, besok, atau sudah terlewat:'], $lines);
    $foot = 'Dikirim otomatis sekali sehari oleh ' . $brand . ' (' . deiWibNow() . '). Tandai task Done atau follow-up Selesai di dashboard supaya tidak muncul lagi.';
    $url = crmDashUrl215();
    $text = implode("\n\n", array_slice($p, 0, 2)) . "\n\n" . implode("\n", array_slice($p, 2)) . "\n\nBuka dashboard: " . $url . "\n\n" . $foot . "\n";
    return ['mail' => deiSendMail($to, $subject, $text, deiMailHtml('Pengingat jatuh tempo', $p, 'Buka dashboard', $url, $foot), 'crm_remind'),
            'total' => $total, 'late' => $late, 'first' => $total ? ltrim($lines[0], '• ') : ''];
}
function crmRemindSweep215($s) {
    if (!crmOk215()) return null;
    $cf = crmRemindConf215(); if (!$cf['on']) return null;
    if ((int)wibDate('G') < $cf['hour']) return null;
    $today = wibDate('Y-m-d'); $tomorrow = wibDate('Y-m-d', time() + 86400);
    $st = readJson(CRM_REMIND_FILE, []); if (!is_array($st)) $st = [];
    if (($st['_day'] ?? '') === $today && !empty($st['_done'])) return null;
    if ((int)($st['_wait'] ?? 0) > time()) return null;
    if (($st['_day'] ?? '') !== $today) $st = ['_day' => $today, 'u' => []];
    $users = [];
    foreach ((array)readJson(USERS_FILE, []) as $x) if (is_array($x) && !empty($x['username']) && empty($x['internal'])) $users[$x['username']] = $x;
    $res = ['users' => 0, 'mail' => 0, 'fail' => 0]; $left = false; $n = 0; $url = crmDashUrl215();
    foreach (crmDueItems215($tomorrow) as $un => $it) {
        $un = (string)$un;
        if (!empty($st['u'][$un])) continue;
        if (!isset($users[$un])) { $st['u'][$un] = 'x'; continue; }
        if ($n >= 15) { $left = true; break; }
        $n++;
        $to = deiUserEmail($users[$un]);
        $cnt = count((array)($it['tasks'] ?? [])) + count((array)($it['fu'] ?? []));
        if ($to !== '') {
            $r = crmRemindMail215($users[$un], $to, $it, $today, $tomorrow);
            if (empty($r['mail']['ok']) && stripos((string)($r['mail']['error'] ?? ''), 'batas') !== false) { $st['_wait'] = time() + 900; $left = true; break; }
            if (!empty($r['mail']['ok'])) $res['mail']++; else { $res['fail']++; error_log('[crm-remind] email ' . deiMaskEmail($to) . ': ' . ($r['mail']['error'] ?? '')); }
            $first = $r['first'];
        } else $first = '';
        if (empty($GLOBALS['dei_dry'])) { try { sendPushToUsers([$un], 'Pengingat: ' . $cnt . ' jatuh tempo', $first !== '' ? mb_substr($first, 0, 120) : 'Task & follow-up lead jatuh tempo — buka dashboard.', $url, 'dei-crm'); } catch (\Throwable $e) {} }
        $st['u'][$un] = 1; $res['users']++;
    }
    $st['_done'] = !$left;
    if (empty($GLOBALS['dei_dry'])) writeJson(CRM_REMIND_FILE, $st);
    return $res['users'] ? $res : null;
}
'''

CASES = r'''    /* ---------- v1.2.215: crm-aktivitas ---------- */
    case 'lead_create': {   // body: number, name, company?, email?, source?, status?, sales?, note?
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        crmGuard215();
        $in = bodyInput();
        $num = crmNormNum215($in['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'No. HP/WA tidak valid. Contoh: 0812xxxx atau 62812xxxx.'], 400);
        $name = tkClean214(preg_replace('/\s+/u', ' ', (string)($in['name'] ?? '')), 120);
        if ($name === '') jsonOut(['ok' => false, 'error' => 'Nama lead wajib diisi.'], 400);
        $em = trim((string)($in['email'] ?? ''));
        if ($em !== '' && deiValidEmail($em) === '') jsonOut(['ok' => false, 'error' => 'Format email tidak valid.'], 400);
        $srcK = (string)($in['source'] ?? 'manual'); if (!isset(crmSources215()[$srcK])) $srcK = 'manual';
        $st = (string)($in['status'] ?? 'baru'); if (!in_array($st, ['baru', 'qualified', 'follow_up'], true)) $st = 'baru';
        $sid = preg_replace('/[^a-z0-9_]/', '', (string)($in['sales'] ?? ''));
        $smap = slMap();
        if ($sid !== '' && (!isset($smap[$sid]) || empty($smap[$sid]['active']))) jsonOut(['ok' => false, 'error' => 'Sales tidak ditemukan atau nonaktif.'], 404);
        deiGuardAgentPrivate($u, $num);
        [$me, $meName] = tkMe214($u);
        $r = deiWithLock('leads', function () use ($num, $name, $em, $srcK, $st, $sid, $in, $me) {
            $all = leadsGetAll();
            if (isset($all[$num]) && is_array($all[$num])) return 'dup';
            $now = date('Y-m-d H:i:s');
            $all[$num] = ['number' => $num, 'name' => $name, 'status' => $st, 'note' => tkClean214($in['note'] ?? '', 1000), 'extracted' => [],
                          'analyzed_at' => '', 'created_at' => $now, 'updated_at' => $now, 'src' => 'manual',
                          'company' => tkClean214($in['company'] ?? '', 120), 'email' => deiValidEmail($em), 'source' => $srcK, 'created_by' => $me];
            if ($sid !== '') $all[$num]['sales'] = $sid;
            writeJson(LEADS_FILE, $all);
            return 'ok';
        });
        if ($r === 'dup') jsonOut(['ok' => false, 'exists' => true, 'number' => $num, 'error' => 'Nomor +' . $num . ' sudah ada di Leads.'], 409);
        try {
            deiWithLock('leads-hidden', function () use ($num) {
                $h = readJson(LEADS_HIDDEN_FILE, []);
                if (is_array($h) && isset($h[$num])) { unset($h[$num]); writeJson(LEADS_HIDDEN_FILE, $h ?: new \stdClass()); }
            });
            $tagged = false;
            waContactUpdate($num, function (&$c) use ($name, $sid, $me, &$tagged) {
                if (trim((string)($c['name_manual'] ?? '')) === '') $c['name_manual'] = $name;
                if ($sid !== '' && empty($c['sales']['id'])) { $c['sales'] = ['id' => $sid, 'at' => time(), 'by' => $me]; $tagged = true; }
            });
            if ($tagged) slEvent('tag', $sid, $num, ['by' => $me, 'prev' => '', 'manual' => 1]);
        } catch (\Throwable $e) { error_log('lead_create contact: ' . $e->getMessage()); }
        crmLog215($num, 'Lead diinput manual (' . (crmSources215()[$srcK] ?? $srcK) . ')' . ($sid !== '' ? ' — sales ' . (string)($smap[$sid]['name'] ?? $sid) : ''), $u);
        jsonOut(['ok' => true, 'number' => $num]);
        break;
    }
    case 'lead_info_save': {   // body: number, name?, company?, email?, source?
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        crmGuard215();
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        deiGuardAgentPrivate($u, $num);
        $em = trim((string)($in['email'] ?? ''));
        if ($em !== '' && deiValidEmail($em) === '') jsonOut(['ok' => false, 'error' => 'Format email tidak valid.'], 400);
        $name = tkClean214(preg_replace('/\s+/u', ' ', (string)($in['name'] ?? '')), 120);
        $r = deiWithLock('leads', function () use ($num, $in, $em, $name) {
            $all = leadsGetAll();
            if (!isset($all[$num]) || !is_array($all[$num])) return 'Lead tidak ditemukan.';
            if ($name !== '') $all[$num]['name'] = $name;
            $all[$num]['company'] = tkClean214($in['company'] ?? '', 120);
            $all[$num]['email'] = deiValidEmail($em);
            $sk = (string)($in['source'] ?? ''); if (isset(crmSources215()[$sk])) $all[$num]['source'] = $sk;
            $all[$num]['updated_at'] = date('Y-m-d H:i:s');
            writeJson(LEADS_FILE, $all);
            return true;
        });
        if ($r !== true) jsonOut(['ok' => false, 'error' => (string)$r], 404);
        if ($name !== '') { try { waContactUpdate($num, function (&$c) use ($name) { $c['name_manual'] = $name; }); } catch (\Throwable $e) {} }
        crmLog215($num, 'Info lead diperbarui', $u);
        jsonOut(['ok' => true]);
        break;
    }
    case 'lead_acts': {   // GET number -> lead, aktivitas (terbaru dulu), task tertaut
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        crmGuard215();
        $num = waNormNum($_GET['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        deiGuardAgentPrivate($u, $num);
        $l = leadsGetAll()[$num] ?? null;
        $tasks = [];
        foreach (tkAll214() as $t) {
            if (!is_array($t)) continue;
            if ((string)($t['lead'] ?? '') !== $num && (string)($t['src']['num'] ?? '') !== $num) continue;
            if (tkCanSee214($u, $t)) $tasks[] = tkPublic214($u, $t);
        }
        usort($tasks, function ($a, $b) { return strcmp((string)($b['updated_at'] ?? ''), (string)($a['updated_at'] ?? '')); });
        jsonOut(['ok' => true, 'number' => $num,
            'lead' => is_array($l) ? ['name' => crmLeadName215($num), 'status' => (string)($l['status'] ?? 'baru'), 'src' => (string)($l['src'] ?? ''),
                                      'company' => (string)($l['company'] ?? ''), 'email' => (string)($l['email'] ?? ''), 'source' => (string)($l['source'] ?? ''),
                                      'created_at' => (string)($l['created_at'] ?? ''), 'created_by' => (string)($l['created_by'] ?? '')] : null,
            'acts' => crmActPublic215($u, crmActFor215($num)), 'tasks' => $tasks]);
        break;
    }
    case 'lead_act_add': {   // body: number, type, at, text, next_due?, next_time?, next_text?
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        crmGuard215();
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        deiGuardAgentPrivate($u, $num);
        if (!isset(leadsGetAll()[$num])) jsonOut(['ok' => false, 'error' => 'Lead tidak ditemukan.'], 404);
        $type = (string)($in['type'] ?? ''); if (!isset(crmTypes215()[$type])) jsonOut(['ok' => false, 'error' => 'Jenis aktivitas tidak dikenal.'], 400);
        $text = tkClean214($in['text'] ?? '', 2000);
        $at = str_replace('T', ' ', (string)($in['at'] ?? ''));
        if (!preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/', $at)) $at = date('Y-m-d H:i');
        $nd = (string)($in['next_due'] ?? ''); $ntm = (string)($in['next_time'] ?? ''); $ntx = tkClean214($in['next_text'] ?? '', 200);
        if ($nd !== '' && !preg_match('/^\d{4}-\d{2}-\d{2}$/', $nd)) jsonOut(['ok' => false, 'error' => 'Tanggal follow-up tidak valid.'], 400);
        if ($ntm !== '' && !preg_match('/^\d{2}:\d{2}$/', $ntm)) $ntm = '';
        if ($text === '' && $nd === '') jsonOut(['ok' => false, 'error' => 'Isi hasil/catatan aktivitas atau jadwal follow-up.'], 400);
        [$me, $meName] = tkMe214($u);
        $acts = deiWithLock('lead-act', function () use ($num, $type, $text, $at, $nd, $ntm, $ntx, $me, $meName) {
            $all = crmActAll215();
            $l = array_values(array_filter((array)($all[$num] ?? []), 'is_array'));
            $a = ['id' => 'a' . bin2hex(random_bytes(5)), 'type' => $type, 'at' => $at, 'text' => $text, 'by' => $me, 'by_name' => $meName, 'created_at' => date('Y-m-d H:i:s')];
            if ($nd !== '') { $a['next_due'] = $nd; $a['next_time'] = $ntm; $a['next_text'] = $ntx; $a['next_done'] = false; }
            $l[] = $a;
            usort($l, function ($x, $y) { return strcmp((string)($x['at'] ?? ''), (string)($y['at'] ?? '')) ?: strcmp((string)($x['created_at'] ?? ''), (string)($y['created_at'] ?? '')); });
            $all[$num] = array_slice($l, -CRM_ACT_MAX);
            writeJson(CRM_ACT_FILE, $all);
            return $all[$num];
        });
        deiWithLock('leads', function () use ($num) {
            $all = leadsGetAll();
            if (isset($all[$num]) && is_array($all[$num])) { $all[$num]['updated_at'] = date('Y-m-d H:i:s'); writeJson(LEADS_FILE, $all); }
        });
        jsonOut(['ok' => true, 'acts' => crmActPublic215($u, (array)$acts)]);
        break;
    }
    case 'lead_act_update': {   // body: number, id, done=0|1  |  number, id, remove=1
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        crmGuard215();
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? ''); $id = preg_replace('/[^a-z0-9]/', '', (string)($in['id'] ?? ''));
        if ($num === '' || $id === '') jsonOut(['ok' => false, 'error' => 'number & id wajib'], 400);
        deiGuardAgentPrivate($u, $num);
        [$me, $meName] = tkMe214($u);
        $rm = !empty($in['remove']); $done = !empty($in['done']); $isLead = deiIsLead($u['role'] ?? '');
        $r = deiWithLock('lead-act', function () use ($num, $id, $rm, $done, $me, $meName, $isLead) {
            $all = crmActAll215();
            $l = array_values(array_filter((array)($all[$num] ?? []), 'is_array'));
            $hit = false;
            foreach ($l as $i => $a) {
                if (($a['id'] ?? '') !== $id) continue;
                $hit = true;
                if ($rm) {
                    if (($a['type'] ?? '') === 'sys') return 'Catatan sistem tidak bisa dihapus.';
                    if (($a['by'] ?? '') !== $me && !$isLead) return 'Hanya pencatat atau Admin/Supervisor yang bisa menghapus aktivitas ini.';
                    unset($l[$i]);
                } else {
                    if (empty($a['next_due'])) return 'Aktivitas ini tidak punya follow-up.';
                    $l[$i]['next_done'] = $done;
                    if ($done) { $l[$i]['next_done_at'] = date('Y-m-d H:i:s'); $l[$i]['next_done_by'] = $me; $l[$i]['next_done_by_name'] = $meName; }
                    else unset($l[$i]['next_done_at'], $l[$i]['next_done_by'], $l[$i]['next_done_by_name']);
                }
            }
            if (!$hit) return 'Aktivitas tidak ditemukan.';
            $all[$num] = array_values($l);
            writeJson(CRM_ACT_FILE, $all);
            return $all[$num];
        });
        if (!is_array($r)) jsonOut(['ok' => false, 'error' => (string)$r], 400);
        jsonOut(['ok' => true, 'acts' => crmActPublic215($u, $r)]);
        break;
    }
    case 'crm_badge': {   // follow-up saya yang jatuh tempo (hari ini / terlambat)
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        if (!crmOk215()) jsonOut(['ok' => true, 'locked' => true, 'fu_due' => 0]);
        $it = crmDueItems215(wibDate('Y-m-d'), (string)$u['username']);
        jsonOut(['ok' => true, 'fu_due' => count((array)($it[(string)$u['username']]['fu'] ?? []))]);
        break;
    }
    case 'crm_remind_get': {
        requireAuth(['super_admin', 'admin']);
        crmGuard215();
        $noMail = [];
        foreach ((array)readJson(USERS_FILE, []) as $x) {
            if (is_array($x) && !empty($x['username']) && empty($x['internal']) && deiUserEmail($x) === '') $noMail[] = (string)($x['name'] ?? $x['username']);
        }
        $st = readJson(CRM_REMIND_FILE, []);
        jsonOut(['ok' => true] + crmRemindConf215() + ['no_email' => $noMail, 'last_day' => (string)($st['_day'] ?? '')]);
        break;
    }
    case 'crm_remind_save': {   // body: on, hour
        requireAuth(['super_admin', 'admin']);
        crmGuard215();
        $in = bodyInput();
        writeJson(CRM_REMIND_CONF, ['on' => !empty($in['on']), 'hour' => max(0, min(23, (int)($in['hour'] ?? 7)))]);
        jsonOut(['ok' => true] + crmRemindConf215());
        break;
    }
    case 'crm_remind_test': {   // kirim ringkasan saya sekarang ke email akun saya
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        crmGuard215();
        $uRow = null;
        foreach ((array)readJson(USERS_FILE, []) as $x) if (is_array($x) && ($x['username'] ?? '') === $u['username']) $uRow = $x;
        $to = $uRow ? deiUserEmail($uRow) : '';
        if ($to === '') jsonOut(['ok' => false, 'error' => 'Akun Anda belum punya email. Isi email di menu Pengguna / profil dulu.'], 400);
        $today = wibDate('Y-m-d'); $tomorrow = wibDate('Y-m-d', time() + 86400);
        $it = crmDueItems215($tomorrow, (string)$u['username'])[(string)$u['username']] ?? [];
        $r = crmRemindMail215($uRow, $to, $it, $today, $tomorrow, true);
        if (empty($r['mail']['ok'])) jsonOut(['ok' => false, 'error' => 'Email gagal dikirim: ' . ($r['mail']['error'] ?? '-')], 502);
        jsonOut(['ok' => true, 'to' => deiMaskEmail($to), 'total' => $r['total']]);
        break;
    }

'''

s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API)
else:
    assert NEED in s, 'v1.2.214 belum terpasang di ' + API
    s = rep(s, "define('DEI_VERSION', 'v1.2.214');   // v1.2.214:",
            "define('DEI_VERSION', 'v1.2.215');   // " + TAG + " — lead manual, aktivitas sales + activity record, task per lead, pengingat email jatuh tempo (Growth+); v1.2.214:", what='ver')
    s = rep(s, "\nfunction deiGuardAgentPrivate($u, $num) {", "\n" + LIB + "function deiGuardAgentPrivate($u, $num) {", what='lib')
    s = rep(s, "    /* ---------- ADMIN: take over / return to bot ---------- */", CASES + "    /* ---------- ADMIN: take over / return to bot ---------- */", what='cases')
    # get_leads: ringkasan aktivitas + info manual
    s = rep(s, "        $slMap203 = slPlanOk() ? slMap() : null;   // v1.2.203: sales-tag\n",
            "        $slMap203 = slPlanOk() ? slMap() : null;   // v1.2.203: sales-tag\n        $crmSum215 = crmOk215() ? crmSummaryAll215() : [];   // " + TAG + "\n", what='gl-sum')
    s = rep(s, "            if ($nm === '') $nm = trim((string)($l['extracted']['nama'] ?? ''));",
            "            if ($nm === '' && trim((string)($l['name'] ?? '')) !== '') $nm = trim((string)$l['name']);   // " + TAG + "\n            if ($nm === '') $nm = trim((string)($l['extracted']['nama'] ?? ''));", what='gl-name')
    s = rep(s, "                'src'           => (string)($l['src'] ?? ''),   // v1.2.206: sales-lead\n",
            "                'src'           => (string)($l['src'] ?? ''),   // v1.2.206: sales-lead\n"
            "                'created_at'    => (string)($l['created_at'] ?? ''),   // " + TAG + "\n"
            "                'company'       => (string)($l['company'] ?? ''),\n"
            "                'email'         => (string)($l['email'] ?? ''),\n"
            "                'source'        => (string)($l['source'] ?? ''),\n"
            "                'fu'            => $crmSum215[(string)$num]['fu'] ?? null,\n"
            "                'act_n'         => (int)($crmSum215[(string)$num]['n'] ?? 0),\n"
            "                'last_act'      => (string)($crmSum215[(string)$num]['last'] ?? ''),\n", what='gl-fields')
    s = rep(s, "        jsonOut(['ok' => true, 'leads' => $out, 'count' => count($out)]);",
            "        jsonOut(['ok' => true, 'leads' => $out, 'count' => count($out), 'crm' => crmOk215()]);   // " + TAG, what='gl-out')
    # save_lead: activity record status & catatan
    s = rep(s, "        // v1.2.29: agent boleh mengubah status & menulis catatan\n        requireAuth(['super_admin', 'admin', 'wa_agent']);",
            "        // v1.2.29: agent boleh mengubah status & menulis catatan\n        $u215 = requireAuth(['super_admin', 'admin', 'wa_agent']);   // " + TAG, what='sl-auth')
    s = rep(s, "            slLeadStamp($all[$num], $slPrev203, $st, $num);\n",
            "            slLeadStamp($all[$num], $slPrev203, $st, $num);\n"
            "            if ($slPrev203 !== $st) crmLog215($num, 'Status: ' . slLeadStLabel208($slPrev203) . ' → ' . slLeadStLabel208($st), $u215);   // " + TAG + "\n", what='sl-st')
    s = rep(s, "            $all[$num]['note'] = mb_substr(trim((string)$in['note']), 0, 1000);\n",
            "            $nPrev215 = (string)($all[$num]['note'] ?? '');   // " + TAG + "\n"
            "            $all[$num]['note'] = mb_substr(trim((string)$in['note']), 0, 1000);\n"
            "            if ($all[$num]['note'] !== $nPrev215) crmLog215($num, $all[$num]['note'] === '' ? 'Catatan lead dikosongkan' : 'Catatan lead: ' . mb_substr($all[$num]['note'], 0, 300), $u215);\n", what='sl-note')
    # sales: tag, PO, deal -> activity record
    s = rep(s, "        try { waAuditLog('sales_tag', $by, $num, ['from' => $prevId, 'to' => $sid]); } catch (\\Throwable $e) {}\n",
            "        try { waAuditLog('sales_tag', $by, $num, ['from' => $prevId, 'to' => $sid]); } catch (\\Throwable $e) {}\n"
            "        crmLog215($num, $sid === '' ? 'Tag sales dilepas' : 'Sales: ' . (string)($map[$sid]['name'] ?? $sid), $u);   // " + TAG + "\n", what='tag-log')
    s = rep(s, "        try { waAuditLog('sales_po', $po['by'], $num, ['po' => $po['id'], 'sales' => $po['sales'], 'no' => $po['no']]); } catch (\\Throwable $e) {}\n",
            "        try { waAuditLog('sales_po', $po['by'], $num, ['po' => $po['id'], 'sales' => $po['sales'], 'no' => $po['no']]); } catch (\\Throwable $e) {}\n"
            "        crmLog215($num, 'PO dicatat' . ($po['no'] !== '' ? ' no. ' . $po['no'] : '') . ' (' . $po['date'] . ')' . ($po['note'] !== '' ? ' — ' . $po['note'] : ''), $u);   // " + TAG + "\n", what='po-log')
    s = rep(s, "        try { waAuditLog('sales_deal', $u['username'], $num, ['sales' => (string)$cur['id']]); } catch (\\Throwable $e) {}\n",
            "        try { waAuditLog('sales_deal', $u['username'], $num, ['sales' => (string)$cur['id']]); } catch (\\Throwable $e) {}\n"
            "        crmLog215($num, 'Close Deal dicatat', $u);   // " + TAG + "\n", what='deal-log')
    # task tertaut lead
    s = rep(s, "    $n = (string)($t['src']['num'] ?? '');\n    return $n === '' || deiCanSeeNum164($u, $n);",
            "    $n = (string)($t['src']['num'] ?? ($t['lead'] ?? ''));   // " + TAG + ": task tertaut lead\n    return $n === '' || deiCanSeeNum164($u, $n);", what='tk-see')
    s = rep(s, "    $t['can_del'] = tkCanDel214($u, $t);\n    return $t;",
            "    if (!empty($t['lead'])) $t['lead_name'] = crmLeadName215((string)$t['lead']);   // " + TAG + "\n    $t['can_del'] = tkCanDel214($u, $t);\n    return $t;", what='tk-pub')
    s = rep(s, "        $validUsers = tkUserNames214();\n        [$me, $meName] = tkMe214($u);\n        $r = deiWithLock('tasks', function () use ($u, $in, $id, $src, $validUsers, $me, $meName) {",
            "        $ld215 = '';   // " + TAG + ": task tertaut lead\n"
            "        if ($id === '' && !$src && ($ln215 = waNormNum($in['lead'] ?? '')) !== '') {\n"
            "            if (!isset(leadsGetAll()[$ln215])) jsonOut(['ok' => false, 'error' => 'Lead tidak ditemukan.'], 404);\n"
            "            deiGuardAgentPrivate($u, $ln215);\n"
            "            $ld215 = $ln215;\n"
            "        }\n"
            "        $validUsers = tkUserNames214();\n        [$me, $meName] = tkMe214($u);\n        $r = deiWithLock('tasks', function () use ($u, $in, $id, $src, $validUsers, $me, $meName, $ld215) {", what='tk-save')
    s = rep(s, "'due' => '', 'src' => $src, 'notes' => [], 'log' => [],",
            "'due' => '', 'src' => $src, 'lead' => $ld215, 'notes' => [], 'log' => [],", what='tk-new')
    s = rep(s, "        jsonOut(['ok' => true, 'task' => tkPublic214($u, $r['task']), 'dup' => $r['dup']]);",
            "        if ($ld215 !== '' && empty($r['dup'])) crmLog215($ld215, 'Task dibuat: ' . $r['task']['title'], $u);   // " + TAG + "\n"
            "        jsonOut(['ok' => true, 'task' => tkPublic214($u, $r['task']), 'dup' => $r['dup']]);", what='tk-log')
    # cron
    s = rep(s, "        try { $whd = whDownCron($s);",
            "        try { $crr = crmRemindSweep215($s); if ($crr) $r['crm_remind'] = $crr; } catch (\\Throwable $e) { $r['err_crm_remind'] = $e->getMessage(); }   // " + TAG + "\n"
            "        try { $whd = whDownCron($s);", what='cron')
    save(API, s)

# ======================= dashboard: app.js =======================
JSLIB = r'''
  /* ====================================================================== *
   *  v1.2.215: crm-aktivitas — lead manual, aktivitas sales & activity record,
   *  task per lead, follow-up + pengingat jatuh tempo (Growth+)
   * ====================================================================== */
  var CRM_TYPES = { call: 'Telepon', wa: 'Chat WA', meeting: 'Meeting', visit: 'Kunjungan', email: 'Email', presentasi: 'Presentasi / Demo', penawaran: 'Kirim penawaran', other: 'Lainnya' };
  var CRM_TICO = { call: 'phone', wa: 'message-circle', meeting: 'users', visit: 'target', email: 'mail', presentasi: 'monitor-smartphone', penawaran: 'file-text', other: 'activity', sys: 'clipboard-list' };
  var CRM_SRC = { manual: 'Input manual', referensi: 'Referensi', telepon: 'Telepon masuk', walkin: 'Walk-in / datang langsung', event: 'Event / pameran', website: 'Website', sosmed: 'Media sosial', iklan: 'Iklan', lainnya: 'Lainnya' };
  var leadCrm215 = false, crmSales215 = null;
  function crmFmtD215(d) { return d ? String(d).slice(0, 10).split('-').reverse().join('/') : ''; }
  function crmNow215() { var d = new Date(); return tkToday214() + 'T' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0'); }
  function crmFuChip215(l) {
    var f = l && l.fu; if (!f || !f.due) return '';
    var t = tkToday214(), late = f.due < t, today = f.due === t;
    return ' <span class="tag crm-fu' + (late ? ' late' : (today ? ' today' : '')) + '" title="Follow-up berikutnya' + (f.text ? ': ' + esc(f.text) : '') + (f.by_name ? ' (' + esc(f.by_name) + ')' : '') + '">' +
      ico('alarm-clock', 11) + ' ' + (late ? 'Terlambat ' : (today ? 'Hari ini ' : 'FU ')) + esc(crmFmtD215(f.due)) + (f.time ? ' ' + esc(f.time) : '') + '</span>';
  }
  function crmInfoLine215(l) {
    var p = [];
    if (l.company) p.push(ico('briefcase-business', 11) + ' ' + esc(l.company));
    if (l.email) p.push(ico('mail', 11) + ' ' + esc(l.email));
    if (l.src === 'manual') p.push('Sumber: ' + esc(CRM_SRC[l.source] || 'Input manual'));
    if (l.act_n) p.push(ico('activity', 11) + ' ' + l.act_n + ' aktivitas' + (l.last_act ? ', terakhir ' + esc(crmFmtD215(l.last_act)) : ''));
    return p.length ? '<div class="crm-inf">' + p.join(' &middot; ') + '</div>' : '';
  }
  function crmToolbar215() {
    var a = $('#crmNewLead'), b = $('#crmRemBtn');
    if (a) a.style.display = leadCrm215 ? '' : 'none';
    if (b) b.style.display = leadCrm215 && (user.role === 'super_admin' || user.role === 'admin') ? '' : 'none';
  }
  function crmLoadSales215(then) {
    if (crmSales215) { then(crmSales215); return; }
    api('sales_list').then(function (r) { crmSales215 = (r && r.ok && !r.locked) ? (r.items || []).filter(function (x) { return x.active; }) : []; then(crmSales215); });
  }
  function crmBadge215() {
    api('crm_badge').then(function (r) {
      var b = document.querySelector('#nav button[data-tab="leads"]'); if (!b || !r || !r.ok) return;
      var n = r.fu_due || 0, s = b.querySelector('.crm-nb');
      if (!s) { s = document.createElement('span'); s.className = 'tk-nb crm-nb'; b.appendChild(s); }
      s.textContent = n; s.style.display = n ? '' : 'none'; s.title = n + ' follow-up lead Anda jatuh tempo';
    });
  }
  setTimeout(crmBadge215, 2200);

  // ---- input lead manual ----
  function crmNewLead215() {
    crmLoadSales215(function (sales) {
      tkModal214(ico('user-plus', 17) + ' Input lead manual',
        '<div class="tk-grid">' +
          '<div class="row"><label class="fl">Nama *</label><input type="text" class="crm-nm" maxlength="120" placeholder="Nama orang / PIC"></div>' +
          '<div class="row"><label class="fl">No. HP / WA *</label><input type="tel" class="crm-num" maxlength="20" placeholder="0812xxxx"></div>' +
          '<div class="row"><label class="fl">Perusahaan</label><input type="text" class="crm-co" maxlength="120" placeholder="Opsional"></div>' +
          '<div class="row"><label class="fl">Email</label><input type="email" class="crm-em" maxlength="150" placeholder="Opsional"></div>' +
          '<div class="row"><label class="fl">Sumber lead</label><select class="crm-src">' + Object.keys(CRM_SRC).map(function (k) { return '<option value="' + k + '">' + esc(CRM_SRC[k]) + '</option>'; }).join('') + '</select></div>' +
          '<div class="row"><label class="fl">Status</label><select class="crm-st"><option value="baru">Baru</option><option value="qualified">Qualified</option><option value="follow_up">Follow-up</option></select></div>' +
          (sales.length ? '<div class="row"><label class="fl">Sales</label><select class="crm-sl"><option value="">— Tanpa sales —</option>' + sales.map(function (x) { return '<option value="' + esc(x.id) + '">' + esc(x.name) + '</option>'; }).join('') + '</select></div>' : '') +
        '</div>' +
        '<div class="row"><label class="fl">Catatan</label><textarea class="crm-nt" rows="3" maxlength="1000" placeholder="Kebutuhan, anggaran, konteks…"></textarea></div>' +
        '<div class="tk-foot"><button type="button" class="btn ghost tk-x">Batal</button><button type="button" class="btn crm-save">' + ico('user-plus', 15) + ' Simpan lead</button></div>',
        function (ov, close) {
          var nm = ov.querySelector('.crm-nm'); setTimeout(function () { nm.focus(); }, 30);
          ov.querySelector('.crm-save').onclick = function () {
            var bt = this, sl = ov.querySelector('.crm-sl');
            var body = { name: nm.value.trim(), number: ov.querySelector('.crm-num').value.trim(), company: ov.querySelector('.crm-co').value.trim(),
                         email: ov.querySelector('.crm-em').value.trim(), source: ov.querySelector('.crm-src').value, status: ov.querySelector('.crm-st').value,
                         note: ov.querySelector('.crm-nt').value.trim(), sales: sl ? sl.value : '' };
            if (!body.name) { toast('Nama wajib diisi.', true); nm.focus(); return; }
            if (!body.number) { toast('No. HP / WA wajib diisi.', true); ov.querySelector('.crm-num').focus(); return; }
            bt.disabled = true;
            api('lead_create', { method: 'POST', body: body }).then(function (r) {
              bt.disabled = false;
              if (!r || !r.ok) {
                if (r && r.exists) { if (confirm((r.error || 'Lead sudah ada.') + '\n\nBuka lead tersebut?')) { close(); crmOpen215(r.number); } return; }
                toast((r && r.error) || 'Gagal menyimpan lead.', true); return;
              }
              close(); toast('Lead ditambahkan.'); fetchLeads(); crmOpen215(r.number);
            });
          };
        });
    });
  }

  // ---- modal Aktivitas & Task per lead ----
  function crmTlHtml215(acts) {
    if (!acts.length) return '<div class="tk-empty-n">Belum ada aktivitas. Catat telepon, meeting, kunjungan, dll. lewat formulir di atas.</div>';
    var t = tkToday214();
    return acts.map(function (a) {
      var sys = a.type === 'sys', fu = '';
      if (a.next_due) {
        var late = !a.next_done && a.next_due < t;
        fu = '<div class="crm-fu-row' + (a.next_done ? ' done' : (late ? ' late' : '')) + '"><label><input type="checkbox" class="crm-fu-ck" data-aid="' + esc(a.id) + '"' + (a.next_done ? ' checked' : '') + '> ' +
          ico('alarm-clock', 12) + ' Follow-up ' + esc(crmFmtD215(a.next_due)) + (a.next_time ? ' ' + esc(a.next_time) : '') + (a.next_text ? ' — ' + esc(a.next_text) : '') + '</label>' +
          (a.next_done ? '<span>Selesai' + (a.next_done_by_name ? ' · ' + esc(a.next_done_by_name) : '') + '</span>' : (late ? '<span>Terlambat</span>' : '')) + '</div>';
      }
      return '<div class="crm-it' + (sys ? ' sys' : '') + '"><span class="crm-ic">' + ico(CRM_TICO[a.type] || 'activity', 13) + '</span><div class="crm-bd">' +
        '<div class="crm-ih"><b>' + esc(sys ? 'Catatan sistem' : (CRM_TYPES[a.type] || a.type)) + '</b><span>' + esc(String(a.at || '').slice(0, 16)) + (a.by_name ? ' · ' + esc(a.by_name) : '') + '</span>' +
        (a.can_del ? '<button type="button" class="tk-n-del crm-del" data-aid="' + esc(a.id) + '" title="Hapus aktivitas">' + ico('trash-2', 12) + '</button>' : '') + '</div>' +
        (a.text ? '<div class="crm-tx2">' + esc(a.text) + '</div>' : '') + fu + '</div></div>';
    }).join('');
  }
  function crmTasksHtml215(ts) {
    if (!ts.length) return '<div class="tk-empty-n">Belum ada task untuk lead ini.</div>';
    return ts.map(function (t) {
      var d = TK_ST[t.status] || TK_ST['new'];
      return '<div class="crm-tk" data-tk="' + esc(t.id) + '"><span class="tag" style="background:' + d.bg + ';color:' + d.fg + '">' + esc(d.label) + '</span> <b>' + esc(t.title) + '</b>' +
        '<span class="crm-tk-m">' + (t.assignee ? ico('user', 11) + ' ' + esc(tkUserName214(t.assignee)) : '') + ' ' + tkDueHtml214(t) + '</span></div>';
    }).join('');
  }
  function crmOpen215(num) {
    num = String(num);
    api('lead_acts', { query: '&number=' + encodeURIComponent(num) }).then(function (r) {
      if (!r || !r.ok) { toast((r && r.error) || 'Gagal memuat aktivitas.', true); return; }
      if (!r.lead) { toast('Lead tidak ditemukan.', true); return; }
      var l = leadAll203.filter(function (x) { return x.number === num; })[0] || {};
      var info = r.lead, acts = r.acts || [], tasks = r.tasks || [];
      var nm = info.name || l.name || ('+' + num);
      var st = LEAD_STATUS[info.status] || LEAD_STATUS.baru;
      var ov = tkModal214(ico('activity', 17) + ' ' + esc(nm),
        '<div class="crm-hd">+' + esc(num) + ' <span class="tag" style="background:' + st.bg + ';color:' + st.fg + '">' + esc(st.label) + '</span>' + slLeadBadge203(l) + crmFuChip215(l) + '</div>' +
        '<details class="crm-info"><summary>Info lead' + (info.company ? ' — ' + esc(info.company) : '') + '</summary><div class="crm-ib">' +
          '<div class="tk-grid">' +
            '<div class="row"><label class="fl">Nama</label><input type="text" class="ci-nm" maxlength="120" value="' + esc(info.name || '') + '"></div>' +
            '<div class="row"><label class="fl">Perusahaan</label><input type="text" class="ci-co" maxlength="120" value="' + esc(info.company || '') + '"></div>' +
            '<div class="row"><label class="fl">Email</label><input type="email" class="ci-em" maxlength="150" value="' + esc(info.email || '') + '"></div>' +
            '<div class="row"><label class="fl">Sumber lead</label><select class="ci-src"><option value="">' + (info.src === 'manual' ? '—' : 'Chat / otomatis') + '</option>' +
              Object.keys(CRM_SRC).map(function (k) { return '<option value="' + k + '"' + (info.source === k ? ' selected' : '') + '>' + esc(CRM_SRC[k]) + '</option>'; }).join('') + '</select></div>' +
          '</div>' +
          '<div class="crm-fbtn"><span class="crm-inf" style="margin-right:auto">' + (info.created_at ? 'Dibuat ' + esc(info.created_at.slice(0, 16)) + (info.created_by ? ' oleh ' + esc(tkUserName214(info.created_by)) : '') : '') + '</span><button type="button" class="btn ghost sm ci-save">Simpan info</button></div>' +
        '</div></details>' +
        '<div class="crm-tabs"><button type="button" class="active" data-ct="act">' + ico('activity', 14) + ' Aktivitas</button><button type="button" data-ct="task">' + ico('list-todo', 14) + ' Task <span class="crm-tn">' + tasks.length + '</span></button></div>' +
        '<div class="crm-pane" data-cp="act">' +
          '<div class="crm-form">' +
            '<div class="tk-grid">' +
              '<div class="row"><label class="fl">Jenis aktivitas</label><select class="crm-ty">' + Object.keys(CRM_TYPES).map(function (k) { return '<option value="' + k + '">' + esc(CRM_TYPES[k]) + '</option>'; }).join('') + '</select></div>' +
              '<div class="row"><label class="fl">Waktu</label><input type="datetime-local" class="crm-at" value="' + crmNow215() + '"></div>' +
            '</div>' +
            '<div class="row"><label class="fl">Hasil / catatan</label><textarea class="crm-tx" rows="2" maxlength="2000" placeholder="Mis. Sudah telepon, tertarik paket B, minta penawaran tertulis"></textarea></div>' +
            '<div class="row"><label class="fl">Follow-up berikutnya (opsional — dapat pengingat email)</label><div class="crm-next-r"><input type="date" class="crm-nd"><input type="time" class="crm-ntm"><input type="text" class="crm-nx" maxlength="200" placeholder="Rencana: telepon ulang, kirim penawaran…"></div></div>' +
            '<div class="crm-fbtn"><button type="button" class="btn sm crm-add">' + ico('plus', 14) + ' Catat aktivitas</button></div>' +
          '</div>' +
          '<div class="crm-tl">' + crmTlHtml215(acts) + '</div>' +
        '</div>' +
        '<div class="crm-pane" data-cp="task" style="display:none"><div class="crm-tasks">' + crmTasksHtml215(tasks) + '</div>' +
          '<button type="button" class="btn ghost sm crm-tnew">' + ico('plus', 14) + ' Task untuk lead ini</button></div>' +
        '<div class="tk-foot"><button type="button" class="btn ghost sm crm-chat" style="margin-right:auto">' + ico('message-circle', 14) + ' Lihat percakapan</button><button type="button" class="btn ghost tk-x">Tutup</button></div>',
        function (ov, close) {
          ov.querySelector('.tk-box').classList.add('crm-box');
          function paintTl() { ov.querySelector('.crm-tl').innerHTML = crmTlHtml215(acts); }
          function paintTasks() { ov.querySelector('.crm-tasks').innerHTML = crmTasksHtml215(tasks); ov.querySelector('.crm-tn').textContent = tasks.length; }
          function changed() { fetchLeads(); crmBadge215(); }
          Array.prototype.forEach.call(ov.querySelectorAll('[data-ct]'), function (b) {
            b.onclick = function () {
              Array.prototype.forEach.call(ov.querySelectorAll('[data-ct]'), function (x) { x.classList.toggle('active', x === b); });
              Array.prototype.forEach.call(ov.querySelectorAll('[data-cp]'), function (p) { p.style.display = p.getAttribute('data-cp') === b.getAttribute('data-ct') ? '' : 'none'; });
            };
          });
          ov.querySelector('.ci-save').onclick = function () {
            var bt = this; bt.disabled = true;
            api('lead_info_save', { method: 'POST', body: { number: num, name: ov.querySelector('.ci-nm').value.trim(), company: ov.querySelector('.ci-co').value.trim(),
              email: ov.querySelector('.ci-em').value.trim(), source: ov.querySelector('.ci-src').value } }).then(function (x) {
              bt.disabled = false;
              if (!x || !x.ok) { toast((x && x.error) || 'Gagal menyimpan info.', true); return; }
              toast('Info lead disimpan.'); fetchLeads();
            });
          };
          ov.querySelector('.crm-add').onclick = function () {
            var bt = this, tx = ov.querySelector('.crm-tx'), nd = ov.querySelector('.crm-nd');
            var body = { number: num, type: ov.querySelector('.crm-ty').value, at: ov.querySelector('.crm-at').value, text: tx.value.trim(),
                         next_due: nd.value, next_time: ov.querySelector('.crm-ntm').value, next_text: ov.querySelector('.crm-nx').value.trim() };
            if (!body.text && !body.next_due) { toast('Isi hasil aktivitas atau jadwal follow-up.', true); tx.focus(); return; }
            bt.disabled = true;
            api('lead_act_add', { method: 'POST', body: body }).then(function (x) {
              bt.disabled = false;
              if (!x || !x.ok) { toast((x && x.error) || 'Gagal mencatat aktivitas.', true); return; }
              acts = x.acts || []; paintTl();
              tx.value = ''; nd.value = ''; ov.querySelector('.crm-ntm').value = ''; ov.querySelector('.crm-nx').value = ''; ov.querySelector('.crm-at').value = crmNow215();
              toast('Aktivitas dicatat.'); changed();
            });
          };
          ov.querySelector('.crm-tl').addEventListener('click', function (e) {
            var b = e.target.closest ? e.target.closest('.crm-del') : null; if (!b) return;
            if (!confirm('Hapus aktivitas ini?')) return;
            api('lead_act_update', { method: 'POST', body: { number: num, id: b.getAttribute('data-aid'), remove: 1 } }).then(function (x) {
              if (!x || !x.ok) { toast((x && x.error) || 'Gagal menghapus.', true); return; }
              acts = x.acts || []; paintTl(); changed();
            });
          });
          ov.querySelector('.crm-tl').addEventListener('change', function (e) {
            var c = e.target; if (!c.classList || !c.classList.contains('crm-fu-ck')) return;
            api('lead_act_update', { method: 'POST', body: { number: num, id: c.getAttribute('data-aid'), done: c.checked ? 1 : 0 } }).then(function (x) {
              if (!x || !x.ok) { toast((x && x.error) || 'Gagal menyimpan.', true); c.checked = !c.checked; return; }
              acts = x.acts || []; paintTl(); changed();
              if (c.checked) toast('Follow-up ditandai selesai.');
            });
          });
          ov.querySelector('.crm-tasks').addEventListener('click', function (e) {
            var b = e.target.closest ? e.target.closest('.crm-tk') : null; if (!b) return;
            var id = b.getAttribute('data-tk');
            tasks.forEach(function (t) { if (t.id === id && !tkS.list.some(function (x) { return x.id === id; })) tkS.list.unshift(t); });
            tkOpen214(id);
          });
          ov.querySelector('.crm-tnew').onclick = function () { crmTaskNew215(num, nm, function (t) { tasks.unshift(t); paintTasks(); }); };
          ov.querySelector('.crm-chat').onclick = function () { close(); openLeadConv(num); };
        });
      return ov;
    });
  }
  function crmTaskNew215(num, nm, after) {
    tkModal214('Task untuk ' + esc(nm),
      '<div class="row"><label class="fl">Judul to-do</label><input type="text" class="tk-title" maxlength="300" placeholder="Mis. Kirim penawaran ke ' + esc(nm) + '"></div>' +
      '<div class="tk-grid">' +
        '<div class="row"><label class="fl">Status</label><select class="tk-st">' + tkStatusOpts214('new') + '</select></div>' +
        '<div class="row"><label class="fl">Ditugaskan ke</label><select class="tk-as">' + tkUserOpts214(tkS.me) + '</select></div>' +
        '<div class="row"><label class="fl">Tenggat (dapat pengingat email)</label><input type="date" class="tk-due-in"></div>' +
      '</div>' +
      '<div class="row"><label class="fl">Catatan (opsional)</label><textarea class="tk-note-in" rows="3" maxlength="2000"></textarea></div>' +
      '<div class="tk-foot"><button type="button" class="btn ghost tk-x">Batal</button><button type="button" class="btn tk-save">' + ico('list-todo', 15) + ' Simpan task</button></div>',
      function (ov, close) {
        var ti = ov.querySelector('.tk-title'); setTimeout(function () { ti.focus(); }, 30);
        var go = function () {
          var title = ti.value.trim();
          if (!title) { toast('Judul to-do wajib diisi.', true); ti.focus(); return; }
          var bt = ov.querySelector('.tk-save'); bt.disabled = true;
          api('task_save', { method: 'POST', body: { title: title, status: ov.querySelector('.tk-st').value, assignee: ov.querySelector('.tk-as').value,
            due: ov.querySelector('.tk-due-in').value, note: ov.querySelector('.tk-note-in').value, lead: num } }).then(function (r) {
            bt.disabled = false;
            if (!r || !r.ok) { toast((r && r.error) || 'Gagal menyimpan task.', true); return; }
            close(); tkUpsert214(r.task); toast('Task dibuat — juga tampil di menu Task.');
            if (after) after(r.task);
          });
        };
        ov.querySelector('.tk-save').onclick = go;
        ti.onkeydown = function (e) { if (e.key === 'Enter') { e.preventDefault(); go(); } };
      });
  }
  function crmLeadBox215(t) {
    if (!t || !t.lead) return '';
    return '<div class="crm-lead">' + ico('briefcase-business', 13) + ' Lead: <b>' + esc(t.lead_name || ('+' + t.lead)) + '</b><button type="button" class="btn ghost sm crm-golead" data-num="' + esc(t.lead) + '">Buka lead</button></div>';
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.crm-golead'); if (!b) return;
    var ov = b.closest('.tk-ov'); if (ov && ov.parentNode) ov.parentNode.removeChild(ov);
    crmOpen215(b.getAttribute('data-num'));
  });

  // ---- pengaturan pengingat (Admin) ----
  function crmRemind215() {
    api('crm_remind_get').then(function (r) {
      if (!r || !r.ok) { toast((r && r.error) || 'Gagal memuat pengaturan.', true); return; }
      var hrs = ''; for (var h = 5; h <= 20; h++) hrs += '<option value="' + h + '"' + (h === r.hour ? ' selected' : '') + '>' + String(h).padStart(2, '0') + ':00 WIB</option>';
      tkModal214(ico('bell', 17) + ' Pengingat jatuh tempo',
        '<p class="crm-p">Sekali sehari, tiap pengguna menerima <b>email</b> (dan notifikasi push bila diaktifkan) berisi task yang ditugaskan kepadanya dan follow-up lead yang ia jadwalkan — yang jatuh tempo hari ini, besok, atau sudah terlambat.</p>' +
        '<label class="crm-ck"><input type="checkbox" class="cr-on"' + (r.on ? ' checked' : '') + '> Kirim pengingat harian</label>' +
        '<div class="row" style="margin-top:10px"><label class="fl">Jam kirim</label><select class="cr-h" style="width:auto">' + hrs + '</select></div>' +
        (r.no_email && r.no_email.length ? '<p class="crm-p crm-warn">Belum punya email (tidak menerima email, hanya push): ' + r.no_email.map(esc).join(', ') + '. Isi email di menu Pengguna.</p>' : '') +
        '<div class="tk-foot"><button type="button" class="btn ghost sm cr-test" style="margin-right:auto">' + ico('send', 14) + ' Kirim uji ke email saya</button><button type="button" class="btn ghost tk-x">Batal</button><button type="button" class="btn cr-save">Simpan</button></div>',
        function (ov, close) {
          ov.querySelector('.cr-save').onclick = function () {
            api('crm_remind_save', { method: 'POST', body: { on: ov.querySelector('.cr-on').checked ? 1 : 0, hour: +ov.querySelector('.cr-h').value } }).then(function (x) {
              if (!x || !x.ok) { toast((x && x.error) || 'Gagal menyimpan.', true); return; }
              close(); toast('Pengaturan pengingat disimpan.');
            });
          };
          ov.querySelector('.cr-test').onclick = function () {
            var bt = this; bt.disabled = true;
            api('crm_remind_test', { method: 'POST', body: {} }).then(function (x) {
              bt.disabled = false;
              if (!x || !x.ok) { toast((x && x.error) || 'Gagal mengirim email uji.', true); return; }
              toast('Email uji terkirim ke ' + x.to + ' (' + x.total + ' item).');
            });
          };
        });
    });
  }

'''

ICONS_ADD = (
  "  if (!ICONS['trash-2']) ICONS['trash-2'] = '<path d=\"M3 6h18\"/><path d=\"M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6\"/><path d=\"M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2\"/>';   // " + TAG + "\n")

HELP_ADD = r'''    { id: 'crm', roles: R_ALL, t: 'Input lead manual, catat aktivitas sales & pengingat follow-up', k: 'crm lead manual input tambah lead aktivitas sales activity record telepon meeting kunjungan follow up pengingat reminder email jatuh tempo due date task lead',   // v1.2.215: crm-aktivitas
      s: ['Di menu <b>Leads</b>, klik <b>+ Lead manual</b> untuk menambah lead dari luar chat (telepon, referensi, event, dll.).', 'Klik <b>Aktivitas &amp; Task</b> di kartu lead: catat telepon, meeting, kunjungan, penawaran, dan jadwalkan <b>follow-up berikutnya</b>. Semua perubahan status, catatan, tag sales, PO dan task tercatat otomatis di riwayat.', 'Centang follow-up saat selesai. Follow-up dan task yang jatuh tempo dikirim lewat email pengingat harian; Admin mengatur jamnya lewat tombol <b>Pengingat</b>.'],
      show: [{ tab: 'leads', el: '#panel-leads .card', title: 'Leads', body: '<p><b>+ Lead manual</b> untuk input lead, <b>Pengingat</b> untuk email jatuh tempo (Admin).</p>' }] },
'''

j = open(JS, encoding='utf-8').read()
if TAG in j: print('SUDAH', JS)
else:
    assert NEED in j, 'v1.2.214 belum terpasang di app.js'
    j = rep(j, "  // Expose for inline replacement of static markup\n  window._ico = ico;",
            ICONS_ADD + "  // Expose for inline replacement of static markup\n  window._ico = ico;", what='js-icons')
    j = rep(j, "  // v1.2.147: leads-kanban — pilihan tampilan diingat per browser\n", JSLIB + "  // v1.2.147: leads-kanban — pilihan tampilan diingat per browser\n", what='js-lib')
    j = rep(j, "    { id: 'kontak', roles: R_ALL,", HELP_ADD + "    { id: 'kontak', roles: R_ALL,", what='js-help')
    j = rep(j, "    $('#btnReloadLeads').onclick = fetchLeads;\n",
            "    $('#btnReloadLeads').onclick = fetchLeads;\n"
            "    if ($('#crmNewLead')) $('#crmNewLead').onclick = crmNewLead215;   // " + TAG + "\n"
            "    if ($('#crmRemBtn')) $('#crmRemBtn').onclick = crmRemind215;\n", what='js-wire')
    j = rep(j, "      leadAll203 = res.leads || []; slLeadSel203();",
            "      leadCrm215 = !!res.crm; crmToolbar215();   // " + TAG + "\n      leadAll203 = res.leads || []; slLeadSel203();", what='js-fetch')
    j = rep(j, "(l.src === 'sales' ? 'Dibuat saat tag sales ' : 'Dibuat dari PO ')",
            "(l.src === 'manual' ? 'Input manual ' : l.src === 'sales' ? 'Dibuat saat tag sales ' : 'Dibuat dari PO ')", what='js-srcline')
    j = rep(j, "          ' ' + contactStageBadgeHtml(l.contact_stage, l.contact_vip, ';margin-left:2px') + slLeadBadge203(l) +",
            "          ' ' + contactStageBadgeHtml(l.contact_stage, l.contact_vip, ';margin-left:2px') + slLeadBadge203(l) + crmFuChip215(l) + /* " + TAG + " */", what='js-listbadge')
    j = rep(j, "        '<div class=\"lead-body\" style=\"margin-top:12px;' + (terbuka ? '' : 'display:none') + '\">' +\n",
            "        '<div class=\"lead-body\" style=\"margin-top:12px;' + (terbuka ? '' : 'display:none') + '\">' + crmInfoLine215(l) + /* " + TAG + " */\n", what='js-listinfo')
    j = rep(j, "          '<button class=\"btn ghost sm lead-open\">Lihat percakapan</button>' +",
            "          (leadCrm215 ? '<button class=\"btn sm lead-crm\">' + ico('activity', 14) + ' Aktivitas &amp; Task</button>' : '') +   // " + TAG + "\n"
            "          '<button class=\"btn ghost sm lead-open\">Lihat percakapan</button>' +", what='js-listbtn')
    j = rep(j, "      card.querySelector('.lead-open').onclick = function () { openLeadConv(num); };",
            "      card.querySelector('.lead-open').onclick = function () { openLeadConv(num); };\n"
            "      var bc215 = card.querySelector('.lead-crm'); if (bc215) bc215.onclick = function () { crmOpen215(num); };   // " + TAG, what='js-listwire')
    j = rep(j, "            (ex.ringkasan ? '<div class=\"lk-r\">' + esc(ex.ringkasan) + '</div>' : '') +",
            "            crmInfoLine215(l) + (l.fu ? '<div style=\"margin-top:5px\">' + crmFuChip215(l) + '</div>' : '') +   // " + TAG + "\n"
            "            (ex.ringkasan ? '<div class=\"lk-r\">' + esc(ex.ringkasan) + '</div>' : '') +", what='js-kbinfo')
    j = rep(j, "              '<button type=\"button\" class=\"lk-chat\" title=\"Lihat percakapan\">' + ico('message-circle', 14) + '</button>' +",
            "              (leadCrm215 ? '<button type=\"button\" class=\"lk-crm\" title=\"Aktivitas & Task\">' + ico('activity', 14) + '</button>' : '') +   // " + TAG + "\n"
            "              '<button type=\"button\" class=\"lk-chat\" title=\"Lihat percakapan\">' + ico('message-circle', 14) + '</button>' +", what='js-kbbtn')
    j = rep(j, "      c.querySelector('.lk-chat').onclick = function () { openLeadConv(num); };",
            "      c.querySelector('.lk-chat').onclick = function () { openLeadConv(num); };\n"
            "      var kc215 = c.querySelector('.lk-crm'); if (kc215) kc215.onclick = function () { crmOpen215(num); };   // " + TAG, what='js-kbwire')
    # task: tampilkan lead tertaut
    j = rep(j, "            (t.src && t.src.num ? '<div class=\"lk-s tk-from\">' + ico('message-circle', 12) + ' ' + esc(tkSrcName214(t.src)) + '</div>' : '') +",
            "            (t.src && t.src.num ? '<div class=\"lk-s tk-from\">' + ico('message-circle', 12) + ' ' + esc(tkSrcName214(t.src)) + '</div>' : '') +\n"
            "            (t.lead ? '<div class=\"lk-s tk-from\">' + ico('briefcase-business', 12) + ' Lead: ' + esc(t.lead_name || ('+' + t.lead)) + '</div>' : '') +   // " + TAG, what='js-tkcard')
    j = rep(j, "      tkSrcBox214(t.src, true) +", "      tkSrcBox214(t.src, true) + crmLeadBox215(t) + /* " + TAG + " */", what='js-tkdetail')
    j = rep(j, "    var hay = [t.title, t.src && t.src.name, t.src && t.src.num, t.src && t.src.text, tkUserName214(t.assignee)]",
            "    var hay = [t.title, t.src && t.src.name, t.src && t.src.num, t.src && t.src.text, tkUserName214(t.assignee), t.lead_name, t.lead]", what='js-tkq')
    save(JS, j)

# ======================= dashboard: index.html =======================
CSS = r'''  /* v1.2.215: crm-aktivitas */
  .tk-box.crm-box{max-width:760px}
  .tk-box input[type=email],.tk-box input[type=tel],.tk-box input[type=datetime-local]{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:9px;font-size:14px;font-family:inherit;outline:none;background:#fff}
  .tk-box input[type=email]:focus,.tk-box input[type=tel]:focus,.tk-box input[type=datetime-local]:focus{border-color:var(--brand)}
  .crm-hd{display:flex;align-items:center;gap:6px;flex-wrap:wrap;color:var(--muted);font-size:13px;margin:-4px 0 10px}
  .tag.crm-fu{background:#e0f2fe;color:#075985}
  .tag.crm-fu.today{background:#fef3c7;color:#92400e}
  .tag.crm-fu.late{background:#fee2e2;color:#991b1b}
  .crm-info{border:1px solid var(--line);border-radius:9px;padding:8px 12px;margin-bottom:10px}
  .crm-info summary{cursor:pointer;font-weight:600;font-size:13px}
  .crm-info .crm-ib{margin-top:10px}
  .crm-tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin-bottom:12px}
  .crm-tabs button{border:0;background:none;padding:8px 12px;cursor:pointer;font-weight:600;color:var(--muted);border-bottom:2px solid transparent;margin-bottom:-1px;display:inline-flex;gap:6px;align-items:center}
  .crm-tabs button.active{color:var(--brand);border-bottom-color:var(--brand)}
  .crm-tn{background:var(--brand-soft);border-radius:9px;padding:0 6px;font-size:11px}
  .crm-form{background:var(--brand-soft);border-radius:10px;padding:10px 12px;margin-bottom:12px}
  .crm-next-r{display:flex;gap:6px;flex-wrap:wrap}
  .crm-next-r input[type=date],.crm-next-r input[type=time]{width:auto}
  .crm-next-r input[type=text]{flex:1;min-width:160px}
  .crm-fbtn{display:flex;justify-content:flex-end;align-items:center;margin-top:8px}
  .crm-tl{display:flex;flex-direction:column;gap:8px;max-height:46vh;overflow:auto;padding-right:2px}
  .crm-it{display:flex;gap:10px;align-items:flex-start}
  .crm-ic{flex:none;width:26px;height:26px;border-radius:50%;background:var(--brand-soft);color:var(--brand);display:inline-flex;align-items:center;justify-content:center}
  .crm-it.sys .crm-ic{background:#f3f4f6;color:#6b7280}
  .crm-bd{flex:1;min-width:0;border-bottom:1px solid var(--line);padding-bottom:8px}
  .crm-ih{display:flex;gap:8px;align-items:center;font-size:13px}
  .crm-ih span{color:var(--muted);font-size:12px}
  .crm-ih .crm-del{margin-left:auto}
  .crm-it.sys .crm-ih b{color:var(--muted);font-weight:600}
  .crm-tx2{font-size:13.5px;white-space:pre-wrap;margin-top:3px;word-break:break-word}
  .crm-it.sys .crm-tx2{color:var(--muted);font-size:12.5px}
  .crm-fu-row{display:flex;gap:8px;align-items:center;justify-content:space-between;margin-top:6px;font-size:12.5px;background:#f0f9ff;border-radius:7px;padding:5px 8px}
  .crm-fu-row label{display:flex;gap:6px;align-items:center;cursor:pointer}
  .crm-fu-row.late{background:#fef2f2;color:#991b1b}
  .crm-fu-row.done{background:#f3f4f6;color:#6b7280}
  .crm-fu-row.done label{text-decoration:line-through}
  .crm-fu-row span{font-size:11.5px;font-weight:600;white-space:nowrap}
  .crm-tk{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:8px 10px;border:1px solid var(--line);border-radius:9px;margin-bottom:6px;cursor:pointer}
  .crm-tk:hover{border-color:var(--brand)}
  .crm-tk-m{margin-left:auto;color:var(--muted);font-size:12px;display:inline-flex;gap:6px;align-items:center}
  .crm-inf{color:var(--muted);font-size:12px;margin-top:4px;line-height:1.5}
  .lk-card .lk-crm{border:1px solid var(--line);background:#fff;border-radius:7px;padding:4px 7px;cursor:pointer;color:var(--brand);display:inline-flex}
  .crm-lead{display:flex;align-items:center;gap:8px;background:#f0f9ff;border-radius:9px;padding:8px 10px;margin:8px 0;font-size:13px}
  .crm-lead button{margin-left:auto}
  .crm-p{font-size:13px;line-height:1.55;color:var(--muted);margin:0 0 10px}
  .crm-warn{color:#92400e;background:#fef3c7;border-radius:8px;padding:8px 10px}
  .crm-ck{display:flex;gap:8px;align-items:center;font-weight:600;cursor:pointer}
'''
h = open(HT, encoding='utf-8').read()
if TAG in h: print('SUDAH', HT)
else:
    assert NEED in h, 'v1.2.214 belum terpasang di index.html'
    h = rep(h, '  .lk-empty{', CSS + '  .lk-empty{', what='html-css')
    h = rep(h, '<button class="btn ghost sm" id="btnReloadLeads">&#8635; Muat ulang</button>',
            '<button class="btn ghost sm" id="btnReloadLeads">&#8635; Muat ulang</button>'
            '<button class="btn ghost sm" id="crmRemBtn" style="display:none" title="Email pengingat task & follow-up jatuh tempo">Pengingat</button>'
            '<button class="btn sm" id="crmNewLead" style="display:none">+ Lead manual</button><!-- ' + TAG + ' -->', what='html-toolbar')
    h = rep(h, '<script src="app.js?v=1.2.214"></script>', '<script src="app.js?v=1.2.215"></script><!-- ' + TAG + ' -->', what='html-ver')
    save(HT, h)
print('SELESAI patch', TAG)
