#!/usr/bin/env python3
"""v1.2.216 (pipeline-sales): CRM tahap 2 — Growth+.
- Pipeline Leads: tahap baru Penawaran & Negosiasi (bisa dimatikan), label & peluang (%) per tahap bisa diatur Admin
  (tombol "Tahap pipeline"); nilai deal (Rp) + perkiraan closing per lead (form lead manual & modal lead);
  ringkasan pipeline di atas Leads (terbuka, tertimbang, perkiraan closing bulan ini, Close Deal bulan ini,
  win rate, lewat perkiraan) + jumlah & total Rp per kolom kanban; pindah ke Close Deal tanpa nilai -> diminta nilai.
- Role baru "Sales": login, terhubung ke satu data Sales; hanya melihat menu Leads & Task, hanya lead miliknya
  (tag sales chat / lead manual miliknya) dan task miliknya; lead manual otomatis atas namanya; tanpa akses chat WA.
  Dikelola Super Admin & Admin di Pengguna. Tidak memakai kursi agent; satu akun per data Sales.
Data: data/crm-pipeline.json; lead: value, close_est; user: sales_id.
Butuh v1.2.215. Idempoten. Pakai: patch_v12216.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H + '/dei-tenant'
TAG = 'v1.2.216: pipeline-sales'; NEED = 'v1.2.215: crm-aktivitas'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12216-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ======================= api =======================
LIB = r'''/* ---------- v1.2.216: pipeline-sales — tahap pipeline, nilai deal, perkiraan closing, role Sales ---------- */
if (!defined('CRM_PIPE_CONF')) define('CRM_PIPE_CONF', DATA_DIR . '/crm-pipeline.json');
function crmStagesDef216() {
    return ['baru' => ['label' => 'Baru', 'prob' => 10], 'qualified' => ['label' => 'Qualified', 'prob' => 25], 'follow_up' => ['label' => 'Follow-up', 'prob' => 40],
            'proposal' => ['label' => 'Penawaran', 'prob' => 60, 'opt' => 1], 'negosiasi' => ['label' => 'Negosiasi', 'prob' => 80, 'opt' => 1],
            'closed_deal' => ['label' => 'Close Deal', 'prob' => 100, 'fix' => 1], 'closed_lost' => ['label' => 'Close Lose', 'prob' => 0, 'fix' => 1]];
}
function crmPipeConf216() {
    static $out = null;
    if ($out !== null) return $out;
    $c = readJson(CRM_PIPE_CONF, []); if (!is_array($c)) $c = [];
    $out = [];
    foreach (crmStagesDef216() as $k => $d) {
        $x = is_array($c[$k] ?? null) ? $c[$k] : [];
        $lab = tkClean214($x['label'] ?? '', 30);
        $out[$k] = ['label' => $lab !== '' ? $lab : $d['label'],
                    'prob' => (!empty($d['fix']) || !isset($x['prob'])) ? $d['prob'] : max(0, min(100, (int)$x['prob'])),
                    'on' => empty($d['opt']) ? true : (!array_key_exists('on', $x) || !empty($x['on'])),
                    'opt' => !empty($d['opt']), 'fix' => !empty($d['fix'])];
    }
    return $out;
}
function crmOpenStatuses216() { return ['baru', 'qualified', 'follow_up', 'proposal', 'negosiasi']; }
function crmMoney216($v) { $d = preg_replace('/\D/', '', (string)$v); return $d === '' ? 0 : (int)min(9999999999999, (float)substr($d, 0, 14)); }
function crmDate216($v) { $v = (string)$v; return preg_match('/^\d{4}-\d{2}-\d{2}$/', $v) ? $v : ''; }
function crmRp216($n) { return 'Rp ' . number_format((float)$n, 0, ',', '.'); }
// Role Sales: hanya aksi berikut, dan hanya lead miliknya
function crmSalesActions216() {
    return ['auth_check', 'me', 'my_login_log', 'tour_seen', 'update_own_email', 'change_own_password', 'release_notes',
            'get_leads', 'save_lead', 'lead_create', 'lead_info_save', 'lead_acts', 'lead_act_add', 'lead_act_update', 'lead_deal_save',
            'crm_badge', 'crm_remind_test', 'tasks_list', 'task_save', 'task_note', 'task_delete', 'sales_list'];
}
function crmMySales216($u) { return (string)($u['sales_id'] ?? ''); }
function crmSalesOwns216($u, $num) {
    $sid = crmMySales216($u); $num = waNormNum($num);
    if ($sid === '' || $num === '') return false;
    static $all = null; if ($all === null) $all = leadsGetAll();
    $l = $all[$num] ?? null;
    if (!is_array($l)) return false;
    return slLeadSalesId($l, $num, [$num => waContactGet($num)]) === $sid;
}
function crmSalesUserFor216($sid, $users) {
    foreach ((array)$users as $x) if (is_array($x) && ($x['role'] ?? '') === 'sales' && (string)($x['sales_id'] ?? '') === $sid) return (string)($x['username'] ?? '');
    return '';
}
'''

CASES = r'''    /* ---------- v1.2.216: pipeline-sales ---------- */
    case 'lead_deal_save': {   // body: number, value (Rp, '' = 0), close_est (Y-m-d | '')
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        crmGuard215();
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        deiGuardAgentPrivate($u, $num);
        $val = crmMoney216($in['value'] ?? '');
        $ce = (string)($in['close_est'] ?? '');
        if ($ce !== '' && crmDate216($ce) === '') jsonOut(['ok' => false, 'error' => 'Tanggal perkiraan closing tidak valid.'], 400);
        $r = deiWithLock('leads', function () use ($num, $val, $ce) {
            $all = leadsGetAll();
            if (!isset($all[$num]) || !is_array($all[$num])) return 'Lead tidak ditemukan.';
            $old = [(int)($all[$num]['value'] ?? 0), (string)($all[$num]['close_est'] ?? '')];
            $all[$num]['value'] = $val; $all[$num]['close_est'] = $ce;
            $all[$num]['updated_at'] = date('Y-m-d H:i:s');
            writeJson(LEADS_FILE, $all);
            return $old;
        });
        if (!is_array($r)) jsonOut(['ok' => false, 'error' => (string)$r], 404);
        $msg = [];
        if ($r[0] !== $val) $msg[] = 'Nilai deal: ' . ($val ? crmRp216($val) : '(kosong)') . ($r[0] ? ' (sebelumnya ' . crmRp216($r[0]) . ')' : '');
        if ($r[1] !== $ce) $msg[] = 'Perkiraan closing: ' . ($ce !== '' ? implode('/', array_reverse(explode('-', $ce))) : '(kosong)');
        if ($msg) crmLog215($num, implode(' · ', $msg), $u);
        jsonOut(['ok' => true, 'value' => $val, 'close_est' => $ce, 'acts' => crmActPublic215($u, crmActFor215($num))]);
        break;
    }
    case 'crm_pipeline_get': {
        requireAuth(['super_admin', 'admin']);
        crmGuard215();
        $cnt = []; foreach (leadsGetAll() as $l) if (is_array($l)) { $s = (string)($l['status'] ?? 'baru'); $cnt[$s] = ($cnt[$s] ?? 0) + 1; }
        jsonOut(['ok' => true, 'stages' => crmPipeConf216(), 'counts' => $cnt]);
        break;
    }
    case 'crm_pipeline_save': {   // body: stages {key: {label, prob, on}}
        requireAuth(['super_admin', 'admin']);
        crmGuard215();
        $in = bodyInput(); $st = is_array($in['stages'] ?? null) ? $in['stages'] : [];
        $out = [];
        foreach (crmStagesDef216() as $k => $d) {
            $x = is_array($st[$k] ?? null) ? $st[$k] : [];
            $o = ['label' => tkClean214($x['label'] ?? '', 30)];
            if (empty($d['fix'])) $o['prob'] = max(0, min(100, (int)($x['prob'] ?? $d['prob'])));
            if (!empty($d['opt'])) $o['on'] = !empty($x['on']);
            $out[$k] = $o;
        }
        writeJson(CRM_PIPE_CONF, $out);
        jsonOut(['ok' => true]);
        break;
    }

'''

s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API)
else:
    assert NEED in s, 'v1.2.215 belum terpasang di ' + API
    s = rep(s, "define('DEI_VERSION', 'v1.2.215');   // v1.2.215:",
            "define('DEI_VERSION', 'v1.2.216');   // " + TAG + " — tahap pipeline (Penawaran/Negosiasi, label & peluang), nilai deal & perkiraan closing, ringkasan pipeline, role Sales (lead & task miliknya); v1.2.215:", what='ver')
    s = rep(s, "\nfunction deiGuardAgentPrivate($u, $num) {",
            "\n" + LIB + "function deiGuardAgentPrivate($u, $num) {\n"
            "    if (($u['role'] ?? '') === 'sales') { if (!crmSalesOwns216($u, $num)) jsonOut(['ok' => false, 'error' => 'Lead ini bukan milik Anda.'], 403); return; }   // " + TAG, what='lib+guard')
    s = rep(s, "    /* ---------- v1.2.215: crm-aktivitas ---------- */\n", CASES + "    /* ---------- v1.2.215: crm-aktivitas ---------- */\n", what='cases')
    # status & label
    s = rep(s, "    return in_array($s, ['baru', 'qualified', 'follow_up', 'closed_deal', 'closed_lost', 'closed'], true);",
            "    return in_array($s, ['baru', 'qualified', 'follow_up', 'proposal', 'negosiasi', 'closed_deal', 'closed_lost', 'closed'], true);   // " + TAG, what='st-valid')
    s = rep(s, "function slLeadStLabel208($st) {",
            "function slLeadStLabel208($st) {\n    if (function_exists('crmPipeConf216')) { $pc216 = crmPipeConf216(); if (isset($pc216[$st])) return $pc216[$st]['label']; }   // " + TAG, what='st-label')
    s = rep(s, "if (!in_array($st, ['baru', 'qualified', 'follow_up'], true)) $st = 'baru';",
            "if (!in_array($st, crmOpenStatuses216(), true)) $st = 'baru';", what='create-st')
    s = rep(s, "            if (in_array($st, ['baru', 'qualified', 'follow_up'], true)) $ld['open']++;",
            "            if (in_array($st, crmOpenStatuses216(), true)) $ld['open']++;   // " + TAG, what='report-open')
    # lead_create: nilai, perkiraan closing, Sales memakai data Sales-nya
    s = rep(s, "'source' => $srcK, 'created_by' => $me];",
            "'source' => $srcK, 'created_by' => $me, 'value' => crmMoney216($in['value'] ?? ''), 'close_est' => crmDate216($in['close_est'] ?? '')];", what='create-val')
    s = rep(s, "        deiGuardAgentPrivate($u, $num);\n        [$me, $meName] = tkMe214($u);\n        $r = deiWithLock('leads', function () use ($num, $name, $em, $srcK, $st, $sid, $in, $me) {",
            "        if (($u['role'] ?? '') === 'sales') {   // " + TAG + "\n"
            "            $sid = crmMySales216($u);\n"
            "            if ($sid === '' || empty($smap[$sid]['active'])) jsonOut(['ok' => false, 'error' => 'Akun Sales Anda belum terhubung ke data Sales yang aktif. Hubungi Admin.'], 400);\n"
            "        } else deiGuardAgentPrivate($u, $num);\n"
            "        [$me, $meName] = tkMe214($u);\n        $r = deiWithLock('leads', function () use ($num, $name, $em, $srcK, $st, $sid, $in, $me) {", what='create-sales')
    # get_leads: field baru, konfigurasi pipeline, filter Sales
    s = rep(s, "        // v1.2.29: agent boleh melihat — merekalah yang menindaklanjuti\n        requireAuth(['super_admin', 'admin', 'wa_agent']);",
            "        // v1.2.29: agent boleh melihat — merekalah yang menindaklanjuti\n        $u216 = requireAuth(['super_admin', 'admin', 'wa_agent']);   // " + TAG, what='gl-auth')
    s = rep(s, "                'created_at'    => (string)($l['created_at'] ?? ''),   // v1.2.215: crm-aktivitas\n",
            "                'created_at'    => (string)($l['created_at'] ?? ''),   // v1.2.215: crm-aktivitas\n"
            "                'value'         => (int)($l['value'] ?? 0),   // " + TAG + "\n"
            "                'close_est'     => (string)($l['close_est'] ?? ''),\n"
            "                'closed_at'     => !empty($l['closed_ts']) ? wibDate('Y-m-d', (int)$l['closed_ts']) : '',\n", what='gl-fields')
    s = rep(s, "        usort($out, function ($a, $b) { return strcmp($b['updated_at'], $a['updated_at']); });\n        jsonOut(['ok' => true, 'leads' => $out, 'count' => count($out), 'crm' => crmOk215()]);",
            "        if (($u216['role'] ?? '') === 'sales') { $my216 = crmMySales216($u216); $out = array_values(array_filter($out, function ($x) use ($my216) { return $my216 !== '' && $x['sales_id'] === $my216; })); }   // " + TAG + "\n"
            "        usort($out, function ($a, $b) { return strcmp($b['updated_at'], $a['updated_at']); });\n"
            "        jsonOut(['ok' => true, 'leads' => $out, 'count' => count($out), 'crm' => crmOk215(), 'pipeline' => crmOk215() ? crmPipeConf216() : null]);", what='gl-out')
    # lead_acts: nilai & perkiraan closing
    s = rep(s, "'created_at' => (string)($l['created_at'] ?? ''), 'created_by' => (string)($l['created_by'] ?? '')] : null,",
            "'created_at' => (string)($l['created_at'] ?? ''), 'created_by' => (string)($l['created_by'] ?? ''),\n"
            "                                      'value' => (int)($l['value'] ?? 0), 'close_est' => (string)($l['close_est'] ?? '')] : null,   // " + TAG, what='acts-lead')
    # save_lead: Sales hanya lead miliknya
    s = rep(s, "        $u215 = requireAuth(['super_admin', 'admin', 'wa_agent']);   // v1.2.215: crm-aktivitas\n        $in  = bodyInput();\n        $num = preg_replace('/\\D/', '', (string)($in['number'] ?? ''));\n        if ($num === '') jsonOut(['ok' => false, 'error' => 'Nomor tidak valid.'], 400);\n",
            "        $u215 = requireAuth(['super_admin', 'admin', 'wa_agent']);   // v1.2.215: crm-aktivitas\n        $in  = bodyInput();\n        $num = preg_replace('/\\D/', '', (string)($in['number'] ?? ''));\n        if ($num === '') jsonOut(['ok' => false, 'error' => 'Nomor tidak valid.'], 400);\n"
            "        if (($u215['role'] ?? '') === 'sales') deiGuardAgentPrivate($u215, $num);   // " + TAG + "\n", what='save-lead')
    # visibilitas task & nomor untuk Sales
    s = rep(s, "function deiCanSeeNum164($u, $num) {   // aturan sama dengan deiGuardAgentPrivate/deiGuardSpvScope, tapi mengembalikan bool\n",
            "function deiCanSeeNum164($u, $num) {   // aturan sama dengan deiGuardAgentPrivate/deiGuardSpvScope, tapi mengembalikan bool\n"
            "    if (($u['role'] ?? '') === 'sales') return crmSalesOwns216($u, $num);   // " + TAG + "\n", what='cansee')
    s = rep(s, "    return $n === '' || deiCanSeeNum164($u, $n);",
            "    return $n === '' ? (($u['role'] ?? '') !== 'sales') : deiCanSeeNum164($u, $n);   // " + TAG, what='tk-see')
    s = rep(s, "        $users = array_map(function ($x) { return ['username' => $x['username'], 'name' => $x['name'], 'role' => $x['role']]; }, deiAssignableUsers(null));",
            "        $users = array_map(function ($x) { return ['username' => $x['username'], 'name' => $x['name'], 'role' => $x['role']]; }, deiAssignableUsers(null));\n"
            "        foreach ((array)readJson(USERS_FILE, []) as $x216) if (is_array($x216) && ($x216['role'] ?? '') === 'sales') $users[] = ['username' => (string)$x216['username'], 'name' => (string)($x216['name'] ?? $x216['username']), 'role' => 'sales'];   // " + TAG, what='tk-users')
    # requireAuth: role Sales
    s = rep(s, "            if ($roles !== null) {\n",
            "            if ($role === 'sales') {   // " + TAG + ": hanya aksi CRM, paket Growth\n"
            "                if (!in_array((string)($GLOBALS['action'] ?? ''), crmSalesActions216(), true)) jsonOut(['ok' => false, 'error' => 'Akses ditolak untuk peran Anda.'], 403);\n"
            "                if (!crmOk215()) jsonOut(['ok' => false, 'error' => 'Akun Sales hanya bisa dipakai di paket Growth ke atas.'], 403);\n"
            "                if ($roles !== null) $roles = array_merge((array)$roles, ['sales']);\n"
            "            }\n"
            "            if ($roles !== null) {\n", what='auth')
    # Pengguna: role sales
    s = rep(s, "$role     = in_array($roleIn, ['super_admin', 'admin', 'supervisor', 'wa_agent'], true) ? $roleIn : 'admin';   // v1.2.58",
            "$role     = in_array($roleIn, ['super_admin', 'admin', 'supervisor', 'wa_agent', 'sales'], true) ? $roleIn : 'admin';   // v1.2.58; " + TAG, what='u-role')
    s = rep(s, "$bolehPeran = ($me['role'] === 'admin') ? ['wa_agent', 'supervisor'] : ['wa_agent'];",
            "$bolehPeran = ($me['role'] === 'admin') ? ['wa_agent', 'supervisor', 'sales'] : ['wa_agent'];", what='u-boleh')
    s = rep(s, "$bolehHapus = ($me['role'] === 'admin') ? ['wa_agent', 'supervisor'] : ['wa_agent'];",
            "$bolehHapus = ($me['role'] === 'admin') ? ['wa_agent', 'supervisor', 'sales'] : ['wa_agent'];", what='u-hapus')
    s = rep(s, "        $users = readJson(USERS_FILE, []);\n        // v1.2.59: supervisor atasan",
            "        $users = readJson(USERS_FILE, []);\n"
            "        $sid216 = '';   // " + TAG + ": akun Sales terhubung ke satu data Sales\n"
            "        if ($role === 'sales') {\n"
            "            if (!crmOk215()) jsonOut(['ok' => false, 'error' => 'Akun Sales tersedia mulai paket Growth.'], 403);\n"
            "            $sid216 = preg_replace('/[^a-z0-9_]/', '', (string)($in['sales_id'] ?? ''));\n"
            "            $sm216 = slMap();\n"
            "            if ($sid216 === '' || !isset($sm216[$sid216])) jsonOut(['ok' => false, 'error' => 'Pilih data Sales untuk akun ini (tambah dulu di Laporan & Log > Per Sales bila belum ada).'], 400);\n"
            "            $own216 = crmSalesUserFor216($sid216, $users);\n"
            "            if ($own216 !== '' && $own216 !== $username) jsonOut(['ok' => false, 'error' => 'Sales \"' . (string)($sm216[$sid216]['name'] ?? $sid216) . '\" sudah terhubung ke akun ' . $own216 . '.'], 400);\n"
            "        }\n"
            "        // v1.2.59: supervisor atasan", what='u-sid')
    s = rep(s, "                elseif ($spvSet !== null) $users[$i]['supervisor'] = $spvSet;",
            "                elseif ($spvSet !== null) $users[$i]['supervisor'] = $spvSet;\n"
            "                if ($role === 'sales') $users[$i]['sales_id'] = $sid216; else unset($users[$i]['sales_id']);   // " + TAG, what='u-upd')
    s = rep(s, "            if ($role === 'wa_agent' && $spvSet !== null && $spvSet !== '') $users[count($users) - 1]['supervisor'] = $spvSet;   // v1.2.59",
            "            if ($role === 'wa_agent' && $spvSet !== null && $spvSet !== '') $users[count($users) - 1]['supervisor'] = $spvSet;   // v1.2.59\n"
            "            if ($role === 'sales') $users[count($users) - 1]['sales_id'] = $sid216;   // " + TAG, what='u-new')
    s = rep(s, "                'categories' => $u['categories'] ?? [],  // v1.2.12 Fase 2: categories",
            "                'categories' => $u['categories'] ?? [],  // v1.2.12 Fase 2: categories\n"
            "                'sales_id'   => (string)($u['sales_id'] ?? ''),   // " + TAG, what='u-get')
    save(API, s)

# ======================= dashboard: app.js =======================
JSLIB = r'''
  /* ====================================================================== *
   *  v1.2.216: pipeline-sales — tahap pipeline, nilai deal, perkiraan closing,
   *  ringkasan pipeline, role Sales
   * ====================================================================== */
  var crmPipe216 = null;
  function crmRpFmt216(n) { n = Math.round(+n || 0); return 'Rp ' + String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); }
  function crmRpShort216(n) {
    n = +n || 0;
    if (n >= 1e9) return 'Rp ' + (n / 1e9).toFixed(n >= 1e10 ? 0 : 1).replace('.', ',') + ' M';
    if (n >= 1e6) return 'Rp ' + (n / 1e6).toFixed(n >= 1e7 ? 0 : 1).replace('.', ',') + ' jt';
    if (n >= 1e3) return 'Rp ' + Math.round(n / 1e3) + ' rb';
    return 'Rp ' + n;
  }
  function crmNumIn216(el) {   // input Rupiah: titik ribuan saat mengetik
    if (!el) return;
    el.addEventListener('input', function () {
      var d = el.value.replace(/\D/g, '').replace(/^0+(?=\d)/, '');
      el.value = d ? d.replace(/\B(?=(\d{3})+(?!\d))/g, '.') : '';
    });
  }
  function crmOpenKeys216() { return ['baru', 'qualified', 'follow_up', 'proposal', 'negosiasi']; }
  function crmPipeApply216(pc) {
    crmPipe216 = pc;
    Object.keys(pc).forEach(function (k) {
      var d = LEAD_STATUS[k]; if (!d) return;
      d.label = pc[k].label; d.off = !pc[k].on; d.prob = pc[k].prob;
      $$('.lead-filter[data-lead-status="' + k + '"]').forEach(function (b) { b.textContent = pc[k].label; b.style.display = (d.off && !leadAll203.some(function (l) { return l.status === k; })) ? 'none' : ''; });
    });
  }
  function crmProb216(st) { var d = LEAD_STATUS[st]; return d && typeof d.prob === 'number' ? d.prob : 0; }
  function crmDealChip216(l) {
    var h = '';
    if (l.value) h += ' <span class="tag crm-val" title="Nilai deal">' + esc(crmRpShort216(l.value)) + '</span>';
    if (l.close_est && crmOpenKeys216().indexOf(l.status || 'baru') !== -1) {
      var late = l.close_est < tkToday214();
      h += ' <span class="tag crm-ce' + (late ? ' late' : '') + '" title="Perkiraan closing' + (late ? ' — sudah lewat' : '') + '">' + ico('calendar', 11) + ' ' + esc(crmFmtD215(l.close_est)) + '</span>';
    }
    return h;
  }
  function crmColSum216(list) {
    var t = 0; list.forEach(function (l) { t += +l.value || 0; });
    return t ? '<span class="crm-colsum" title="Total nilai deal">' + esc(crmRpShort216(t)) + '</span>' : '';
  }
  function crmPipeRender216() {
    var box = $('#crmPipe'); if (!box) return;
    if (!leadCrm215 || !leadData.length) { box.innerHTML = ''; return; }
    var today = tkToday214(), ym = today.slice(0, 7), open = crmOpenKeys216();
    var o = { n: 0, v: 0, w: 0, mN: 0, mV: 0, wonN: 0, wonV: 0, lost: 0, late: 0, noVal: 0 }, by = {};
    open.forEach(function (k) { by[k] = { n: 0, v: 0 }; });
    leadData.forEach(function (l) {
      var st = l.status || 'baru', v = +l.value || 0;
      if (open.indexOf(st) !== -1) {
        o.n++; o.v += v; o.w += v * crmProb216(st) / 100; by[st].n++; by[st].v += v;
        if (!v) o.noVal++;
        if (l.close_est && l.close_est.slice(0, 7) === ym) { o.mN++; o.mV += v; }
        if (l.close_est && l.close_est < today) o.late++;
      } else if ((l.closed_at || '').slice(0, 7) === ym) {
        if (st === 'closed_deal') { o.wonN++; o.wonV += v; } else if (st === 'closed_lost') o.lost++;
      }
    });
    var wr = (o.wonN + o.lost) ? Math.round(o.wonN * 100 / (o.wonN + o.lost)) + '%' : '—';
    var tile = function (lbl, big, sub, cls) { return '<div class="crm-pt' + (cls ? ' ' + cls : '') + '"><div class="crm-pt-l">' + lbl + '</div><div class="crm-pt-b">' + big + '</div><div class="crm-pt-s">' + sub + '</div></div>'; };
    var max = 0; open.forEach(function (k) { if (by[k].v > max) max = by[k].v; });
    box.innerHTML = '<div class="card crm-pipe"><div class="crm-pipe-h"><b>' + ico('bar-chart-3', 15) + ' Pipeline</b><span>' + (leadSales203 ? 'filter sales aktif · ' : '') + 'bulan ini = ' + esc(ym.split('-').reverse().join('/')) + '</span></div>' +
      '<div class="crm-pts">' +
        tile('Pipeline terbuka', esc(crmRpShort216(o.v)), o.n + ' lead' + (o.noVal ? ' · ' + o.noVal + ' belum ada nilai' : '')) +
        tile('Nilai tertimbang', esc(crmRpShort216(o.w)), 'nilai × peluang tahap') +
        tile('Perkiraan closing bulan ini', esc(crmRpShort216(o.mV)), o.mN + ' lead') +
        tile('Close Deal bulan ini', esc(crmRpShort216(o.wonV)), o.wonN + ' deal · ' + o.lost + ' lose', 'good') +
        tile('Win rate bulan ini', wr, 'deal ÷ (deal + lose)') +
        tile('Lewat perkiraan closing', String(o.late), 'lead terbuka', o.late ? 'bad' : '') +
      '</div>' +
      '<div class="crm-stg">' + open.filter(function (k) { return !(LEAD_STATUS[k] || {}).off || by[k].n; }).map(function (k) {
        var d = LEAD_STATUS[k];
        return '<div class="crm-stg-r"><span class="crm-stg-l">' + esc(d.label) + ' <i>' + crmProb216(k) + '%</i></span><span class="crm-stg-bar"><span style="width:' + (max ? Math.max(2, Math.round(by[k].v * 100 / max)) : 0) + '%;background:' + d.fg + '"></span></span><span class="crm-stg-n">' + by[k].n + ' · ' + esc(crmRpShort216(by[k].v)) + '</span></div>';
      }).join('') + '</div></div>';
  }
  function crmDealForm216(info) {
    return '<div class="crm-deal"><div class="row"><label class="fl">Nilai deal (Rp)</label><input type="text" inputmode="numeric" class="cd-val" placeholder="0" value="' + (info.value ? esc(String(info.value).replace(/\B(?=(\d{3})+(?!\d))/g, '.')) : '') + '"></div>' +
      '<div class="row"><label class="fl">Perkiraan closing</label><input type="date" class="cd-ce" value="' + esc(info.close_est || '') + '"></div>' +
      '<button type="button" class="btn ghost sm cd-save">Simpan</button></div>';
  }
  function crmDealWire216(ov, num, done) {
    var v = ov.querySelector('.cd-val'); if (!v) return;
    crmNumIn216(v);
    ov.querySelector('.cd-save').onclick = function () {
      var bt = this; bt.disabled = true;
      api('lead_deal_save', { method: 'POST', body: { number: num, value: v.value, close_est: ov.querySelector('.cd-ce').value } }).then(function (x) {
        bt.disabled = false;
        if (!x || !x.ok) { toast((x && x.error) || 'Gagal menyimpan nilai deal.', true); return; }
        toast('Nilai deal disimpan.'); if (done) done(x);
      });
    };
  }
  // Pindah ke Close Deal tanpa nilai -> minta nilai deal
  function crmAskValue216(num, then) {
    var l = leadAll203.filter(function (x) { return x.number === num; })[0];
    if (!leadCrm215 || !l || +l.value) { then(); return; }
    var v = prompt('Close Deal — berapa nilai deal-nya (Rp)?\nKosongkan bila belum tahu.', '');
    var d = String(v || '').replace(/\D/g, '');
    if (!d) { then(); return; }
    api('lead_deal_save', { method: 'POST', body: { number: num, value: d, close_est: l.close_est || '' } }).then(function () { then(); });
  }
  // Pengaturan tahap pipeline (Admin)
  function crmPipeEdit216() {
    api('crm_pipeline_get').then(function (r) {
      if (!r || !r.ok) { toast((r && r.error) || 'Gagal memuat tahap.', true); return; }
      var st = r.stages, cnt = r.counts || {};
      tkModal214(ico('layers', 17) + ' Tahap pipeline',
        '<p class="crm-p">Ubah nama tahap dan peluang menang (%) yang dipakai untuk <b>nilai tertimbang</b>. Tahap Penawaran &amp; Negosiasi bisa dimatikan; lead yang sudah ada di tahap itu tetap tampil.</p>' +
        '<table class="tbl crm-pe"><thead><tr><th>Tahap</th><th>Nama tampilan</th><th>Peluang</th><th>Aktif</th></tr></thead><tbody>' +
        Object.keys(st).map(function (k) {
          var x = st[k];
          return '<tr data-k="' + k + '"><td class="mono" style="font-size:12px">' + esc(k) + (cnt[k] ? ' <span class="help">(' + cnt[k] + ')</span>' : '') + '</td>' +
            '<td><input type="text" class="pe-l" maxlength="30" value="' + esc(x.label) + '"></td>' +
            '<td>' + (x.fix ? x.prob + '%' : '<input type="number" class="pe-p" min="0" max="100" value="' + x.prob + '" style="width:76px"> %') + '</td>' +
            '<td>' + (x.opt ? '<input type="checkbox" class="pe-o"' + (x.on ? ' checked' : '') + '>' : '<span class="help">selalu</span>') + '</td></tr>';
        }).join('') + '</tbody></table>' +
        '<div class="tk-foot"><button type="button" class="btn ghost tk-x">Batal</button><button type="button" class="btn pe-save">Simpan</button></div>',
        function (ov, close) {
          ov.querySelector('.tk-box').classList.add('crm-box');
          ov.querySelector('.pe-save').onclick = function () {
            var out = {};
            Array.prototype.forEach.call(ov.querySelectorAll('tr[data-k]'), function (tr) {
              var p = tr.querySelector('.pe-p'), o = tr.querySelector('.pe-o');
              out[tr.dataset.k] = { label: tr.querySelector('.pe-l').value.trim(), prob: p ? +p.value : undefined, on: o ? o.checked : undefined };
            });
            api('crm_pipeline_save', { method: 'POST', body: { stages: out } }).then(function (x) {
              if (!x || !x.ok) { toast((x && x.error) || 'Gagal menyimpan.', true); return; }
              close(); toast('Tahap pipeline disimpan.'); fetchLeads();
            });
          };
        });
    });
  }
  // Pengguna: akun Sales terhubung ke data Sales
  var uSales216 = [];
  function uSalesLoad216() {
    api('sales_list').then(function (r) {
      uSales216 = (r && r.ok && !r.locked) ? (r.items || []) : [];
      var sel = document.getElementById('u_sales_id'); if (!sel) return;
      var cur = sel.value;
      sel.innerHTML = uSales216.length ? '<option value="">— Pilih data Sales —</option>' + uSales216.map(function (x) { return '<option value="' + esc(x.id) + '">' + esc(x.name) + (x.active ? '' : ' (nonaktif)') + '</option>'; }).join('')
        : '<option value="">' + (r && r.locked ? 'Butuh paket Growth' : 'Belum ada data Sales — tambah di Laporan & Log > Per Sales') + '</option>';
      sel.value = cur;
    });
  }
  function uSalesName216(id) { var x = uSales216.filter(function (s) { return s.id === id; })[0]; return x ? x.name : id; }

'''

HELP_ADD = r'''    { id: 'pipeline', roles: R_ALL, t: 'Pipeline, nilai deal & akun Sales', k: 'pipeline nilai deal rupiah perkiraan closing forecast tertimbang win rate penawaran negosiasi tahap peluang sales login akun sales role',   // v1.2.216: pipeline-sales
      s: ['Isi <b>Nilai deal</b> dan <b>Perkiraan closing</b> di modal Aktivitas &amp; Task lead (atau saat + Lead manual). Kartu lead & kolom kanban menampilkan nilainya.', 'Kartu <b>Pipeline</b> di atas Leads: total terbuka, nilai tertimbang (nilai × peluang tahap), perkiraan closing bulan ini, Close Deal bulan ini, win rate, dan lead yang lewat perkiraan closing. Filter per sales ikut berlaku.', 'Admin: <b>Tahap pipeline</b> untuk ganti nama tahap, peluang (%), dan menyalakan/mematikan Penawaran &amp; Negosiasi. Akun <b>Sales</b> dibuat di Pengguna (pilih data Sales) — hanya melihat lead &amp; task miliknya.'],
      show: [{ tab: 'leads', el: '#crmPipe', title: 'Pipeline', body: '<p>Ringkasan nilai pipeline dan perkiraan closing. Ikut filter sales.</p>' }] },
'''

j = open(JS, encoding='utf-8').read()
if TAG in j: print('SUDAH', JS)
else:
    assert NEED in j, 'v1.2.215 belum terpasang di app.js'
    j = rep(j, "  // v1.2.147: leads-kanban — pilihan tampilan diingat per browser\n", JSLIB + "  // v1.2.147: leads-kanban — pilihan tampilan diingat per browser\n", what='js-lib')
    j = rep(j, "    { id: 'kontak', roles: R_ALL,", HELP_ADD + "    { id: 'kontak', roles: R_ALL,", what='js-help')
    # role Sales
    j = rep(j, "  var ROLE_LABEL = { super_admin: 'Super Admin', admin: 'Admin', supervisor: 'Supervisor', wa_agent: 'WA Agent' };",
            "  var ROLE_LABEL = { super_admin: 'Super Admin', admin: 'Admin', supervisor: 'Supervisor', wa_agent: 'WA Agent', sales: 'Sales' };   // " + TAG, what='js-rl')
    j = rep(j, "    var roleMap = {'super_admin':'Super Admin', 'admin':'Admin', 'supervisor':'Supervisor', 'wa_agent':'WA Agent'};",
            "    var roleMap = {'super_admin':'Super Admin', 'admin':'Admin', 'supervisor':'Supervisor', 'wa_agent':'WA Agent', 'sales':'Sales'};", what='js-rm')
    j = rep(j, "  window.ROLE_LABELS_V126 = { super_admin: 'Super Admin', admin: 'Admin', supervisor: 'Supervisor', wa_agent: 'WA Agent' };",
            "  window.ROLE_LABELS_V126 = { super_admin: 'Super Admin', admin: 'Admin', supervisor: 'Supervisor', wa_agent: 'WA Agent', sales: 'Sales' };", what='js-rl126')
    j = rep(j, "  $('#whoRole').textContent = ROLE_LABEL[role] || role;",
            "  $('#whoRole').textContent = ROLE_LABEL[role] || role;\n  document.body.classList.add('role-' + role);   // " + TAG, what='js-bodyrole')
    j = rep(j, "  var firstTab = role === 'wa_agent' ? 'wachat'", "  var firstTab = role === 'sales' ? 'leads'   // " + TAG + "\n               : role === 'wa_agent' ? 'wachat'", what='js-first')
    # Pengguna
    j = rep(j, "    var row = document.getElementById('u_spv_row');",
            "    var sr216 = document.getElementById('u_sales_row'); if (sr216) { var isS216 = $('#u_role') && $('#u_role').value === 'sales'; sr216.style.display = isS216 ? '' : 'none'; if (isS216 && !uSales216.length) uSalesLoad216(); }   // " + TAG + "\n"
            "    var row = document.getElementById('u_spv_row');", what='js-urow')
    j = rep(j, "        '<option value=\"supervisor\">Supervisor (SPV) — lihat chat timnya, assign ke agent, laporan tim, kelola agent</option>';",
            "        '<option value=\"supervisor\">Supervisor (SPV) — lihat chat timnya, assign ke agent, laporan tim, kelola agent</option>' +\n"
            "        '<option value=\"sales\">Sales — hanya lead &amp; task miliknya (paket Growth)</option>';   // " + TAG, what='js-uadm')
    j = rep(j, "      sel.value = (cur === 'supervisor') ? 'supervisor' : 'wa_agent';",
            "      sel.value = (cur === 'supervisor' || cur === 'sales') ? cur : 'wa_agent';", what='js-uadmsel')
    j = rep(j, "    if (body.role === 'wa_agent') body.reply_stages",
            "    if (body.role === 'sales') { body.sales_id = ($('#u_sales_id') || {}).value || ''; if (!body.sales_id) { toast('Pilih data Sales untuk akun Sales.', true); return; } }   // " + TAG + "\n"
            "    if (body.role === 'wa_agent') body.reply_stages", what='js-usave')
    j = rep(j, "data-rs=\"' + esc(JSON.stringify(u.reply_stages || [])) + '\">Edit</button> ' +",
            "data-rs=\"' + esc(JSON.stringify(u.reply_stages || [])) + '\" data-sid=\"' + esc(u.sales_id || '') + '\">Edit</button> ' +", what='js-uedit')
    j = rep(j, "        if ($('#u_supervisor')) $('#u_supervisor').value = b.dataset.s || '';   // v1.2.59",
            "        if ($('#u_supervisor')) $('#u_supervisor').value = b.dataset.s || '';   // v1.2.59\n"
            "        if ($('#u_sales_id')) { if (b.dataset.sid && !$('#u_sales_id').querySelector('option[value=\"' + b.dataset.sid + '\"]')) $('#u_sales_id').insertAdjacentHTML('beforeend', '<option value=\"' + esc(b.dataset.sid) + '\">' + esc(uSalesName216(b.dataset.sid)) + '</option>'); $('#u_sales_id').value = b.dataset.sid || ''; }   // " + TAG, what='js-ueditset')
    j = rep(j, "    if ($('#u_supervisor')) $('#u_supervisor').value = '';   // v1.2.59",
            "    if ($('#u_supervisor')) $('#u_supervisor').value = '';   // v1.2.59\n    if ($('#u_sales_id')) $('#u_sales_id').value = '';   // " + TAG, what='js-ureset')
    j = rep(j, "((user.role === 'admin' || user.role === 'supervisor') && u.role === 'wa_agent') ||",
            "((user.role === 'admin' || user.role === 'supervisor') && u.role === 'wa_agent') || (user.role === 'admin' && u.role === 'sales') ||", what='js-ucan')
    j = rep(j, "'<td>' + (u.role === 'wa_agent' ? (u.supervisor ? esc(nmBy[u.supervisor] || u.supervisor) : '<span class=\"help\" style=\"font-size:11px\">—</span>') : '') + '</td>' +",
            "'<td>' + (u.role === 'wa_agent' ? (u.supervisor ? esc(nmBy[u.supervisor] || u.supervisor) : '<span class=\"help\" style=\"font-size:11px\">—</span>') : (u.role === 'sales' ? '<span class=\"help\" style=\"font-size:11px\">Data sales: ' + esc(uSalesName216(u.sales_id)) + '</span>' : '')) + '</td>' +", what='js-ucol')
    j = rep(j, "  function loadUsers() {\n", "  function loadUsers() {\n    uSalesLoad216();   // " + TAG + "\n", what='js-uload')
    # Leads: Sales tanpa analisa/hapus
    j = rep(j, "(user.role === 'wa_agent' ? '' : '<button class=\"btn ghost sm lead-reanalyze\">Analisa ulang</button>') +",
            "(user.role === 'wa_agent' || user.role === 'sales' ? '' : '<button class=\"btn ghost sm lead-reanalyze\">Analisa ulang</button>') +", what='js-l-an')
    j = rep(j, "(user.role === 'wa_agent' ? '' : '<button class=\"btn danger sm lead-del\"",
            "(user.role === 'wa_agent' || user.role === 'sales' ? '' : '<button class=\"btn danger sm lead-del\"", what='js-l-del')
    j = rep(j, "(user.role === 'wa_agent' ? '' : '<button type=\"button\" class=\"lk-del\"",
            "(user.role === 'wa_agent' || user.role === 'sales' ? '' : '<button type=\"button\" class=\"lk-del\"", what='js-k-del')
    j = rep(j, "(sales.length ? '<div class=\"row\"><label class=\"fl\">Sales</label>",
            "(sales.length && user.role !== 'sales' ? '<div class=\"row\"><label class=\"fl\">Sales</label>", what='js-nl-sales')
    # Pipeline: tahap
    j = rep(j, "    follow_up: { label: 'Follow-up', bg: '#fed7aa', fg: '#9a3412' },\n",
            "    follow_up: { label: 'Follow-up', bg: '#fed7aa', fg: '#9a3412' },\n"
            "    proposal:  { label: 'Penawaran', bg: '#ede9fe', fg: '#6d28d9' },   // " + TAG + "\n"
            "    negosiasi: { label: 'Negosiasi', bg: '#fef9c3', fg: '#a16207' },\n", what='js-st')
    j = rep(j, "      if (d.legacy && cur !== k) return;", "      if ((d.legacy || d.off) && cur !== k) return;   // " + TAG, what='js-stopt')
    j = rep(j, "      return !LEAD_STATUS[k].legacy || leadData.some(function (l) { return l.status === k; });",
            "      return !(LEAD_STATUS[k].legacy || LEAD_STATUS[k].off) || leadData.some(function (l) { return l.status === k; });   // " + TAG, what='js-kcols')
    j = rep(j, "      leadAll203 = res.leads || []; slLeadSel203();",
            "      leadAll203 = res.leads || []; if (res.pipeline) crmPipeApply216(res.pipeline); /* " + TAG + " */ slLeadSel203();", what='js-fetch')
    j = rep(j, "    leadFilterLegacyBtn();   // v1.2.118\n", "    leadFilterLegacyBtn();   // v1.2.118\n    crmPipeRender216();   // " + TAG + "\n", what='js-render')
    j = rep(j, "'<span class=\"lk-n\">' + byCol[k].length + '</span></div>' +",
            "'<span class=\"lk-n\">' + byCol[k].length + '</span>' + crmColSum216(byCol[k]) + '</div>' +", what='js-colsum')
    j = rep(j, "slLeadBadge203(l) + crmFuChip215(l) + /* v1.2.215: crm-aktivitas */",
            "slLeadBadge203(l) + crmDealChip216(l) + crmFuChip215(l) + /* v1.2.215: crm-aktivitas; " + TAG + " */", what='js-lchip')
    j = rep(j, "crmInfoLine215(l) + (l.fu ? '<div style=\"margin-top:5px\">' + crmFuChip215(l) + '</div>' : '') +",
            "crmInfoLine215(l) + ((l.fu || l.value || l.close_est) ? '<div style=\"margin-top:5px\">' + crmDealChip216(l) + crmFuChip215(l) + '</div>' : '') +", what='js-kchip')
    j = rep(j, "  function saveLead(num, body) {\n    body.number = num;\n",
            "  function saveLead(num, body) {\n"
            "    if (body.status === 'closed_deal' && !body._v216) { body._v216 = 1; crmAskValue216(num, function () { saveLead(num, body); }); return; }   // " + TAG + "\n"
            "    delete body._v216;\n"
            "    body.number = num;\n", what='js-savelead')
    # modal lead: nilai deal
    j = rep(j, "'<details class=\"crm-info\"><summary>Info lead'", "crmDealForm216(info) + '<details class=\"crm-info\"><summary>Info lead'", what='js-dealform')
    j = rep(j, "          ov.querySelector('.tk-box').classList.add('crm-box');\n          function paintTl()",
            "          ov.querySelector('.tk-box').classList.add('crm-box');\n"
            "          crmDealWire216(ov, num, function (x) { if (x.acts) { acts = x.acts; paintTl(); } changed(); });   // " + TAG + "\n"
            "          function paintTl()", what='js-dealwire')
    # lead manual: nilai & perkiraan closing, status dari pipeline
    j = rep(j, "'<div class=\"row\"><label class=\"fl\">Status</label><select class=\"crm-st\"><option value=\"baru\">Baru</option><option value=\"qualified\">Qualified</option><option value=\"follow_up\">Follow-up</option></select></div>' +",
            "'<div class=\"row\"><label class=\"fl\">Status</label><select class=\"crm-st\">' + crmOpenKeys216().filter(function (k) { return !LEAD_STATUS[k].off; }).map(function (k) { return '<option value=\"' + k + '\">' + esc(LEAD_STATUS[k].label) + '</option>'; }).join('') + '</select></div>' +", what='js-nl-st')
    j = rep(j, "'<div class=\"row\"><label class=\"fl\">Catatan</label><textarea class=\"crm-nt\"",
            "'<div class=\"tk-grid\"><div class=\"row\"><label class=\"fl\">Nilai deal (Rp)</label><input type=\"text\" inputmode=\"numeric\" class=\"crm-val\" placeholder=\"Opsional\"></div>' +\n"
            "        '<div class=\"row\"><label class=\"fl\">Perkiraan closing</label><input type=\"date\" class=\"crm-ce\"></div></div>' +   // " + TAG + "\n"
            "        '<div class=\"row\"><label class=\"fl\">Catatan</label><textarea class=\"crm-nt\"", what='js-nl-val')
    j = rep(j, "note: ov.querySelector('.crm-nt').value.trim(), sales: sl ? sl.value : '' };",
            "note: ov.querySelector('.crm-nt').value.trim(), sales: sl ? sl.value : '',\n"
            "                         value: ov.querySelector('.crm-val').value, close_est: ov.querySelector('.crm-ce').value };", what='js-nl-body')
    j = rep(j, "          var nm = ov.querySelector('.crm-nm'); setTimeout(function () { nm.focus(); }, 30);",
            "          var nm = ov.querySelector('.crm-nm'); setTimeout(function () { nm.focus(); }, 30);\n          crmNumIn216(ov.querySelector('.crm-val'));   // " + TAG, what='js-nl-fmt')
    # toolbar: Tahap pipeline
    j = rep(j, "    if ($('#crmRemBtn')) $('#crmRemBtn').onclick = crmRemind215;",
            "    if ($('#crmRemBtn')) $('#crmRemBtn').onclick = crmRemind215;\n    if ($('#crmPipeBtn')) $('#crmPipeBtn').onclick = crmPipeEdit216;   // " + TAG, what='js-pipebtn')
    j = rep(j, "    if (b) b.style.display = leadCrm215 && (user.role === 'super_admin' || user.role === 'admin') ? '' : 'none';",
            "    if (b) b.style.display = leadCrm215 && (user.role === 'super_admin' || user.role === 'admin') ? '' : 'none';\n"
            "    var c216 = $('#crmPipeBtn'); if (c216) c216.style.display = leadCrm215 && (user.role === 'super_admin' || user.role === 'admin') ? '' : 'none';   // " + TAG, what='js-pipeshow')
    save(JS, j)

# ======================= dashboard: index.html =======================
CSS = r'''  /* v1.2.216: pipeline-sales */
  .tag.crm-val{background:#dcfce7;color:#166534;font-weight:600}
  .tag.crm-ce{background:#f1f5f9;color:#334155}
  .tag.crm-ce.late{background:#fee2e2;color:#991b1b}
  .crm-colsum{margin-left:auto;font-size:11.5px;font-weight:700;color:#166534;background:#dcfce7;border-radius:8px;padding:1px 7px}
  .lk-col-h .lk-n + .crm-colsum{margin-left:6px}
  .crm-pipe{padding:14px 16px}
  .crm-pipe-h{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:10px}
  .crm-pipe-h b{display:inline-flex;gap:6px;align-items:center}
  .crm-pipe-h span{color:var(--muted);font-size:12px}
  .crm-pts{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}
  .crm-pt{border:1px solid var(--line);border-radius:10px;padding:9px 11px;background:#fff}
  .crm-pt-l{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.02em}
  .crm-pt-b{font-size:19px;font-weight:700;margin:3px 0 1px;color:var(--brand)}
  .crm-pt-s{font-size:11.5px;color:var(--muted)}
  .crm-pt.good .crm-pt-b{color:#166534}
  .crm-pt.bad .crm-pt-b{color:#b91c1c}
  .crm-stg{margin-top:12px;display:flex;flex-direction:column;gap:5px}
  .crm-stg-r{display:grid;grid-template-columns:150px 1fr 150px;gap:10px;align-items:center;font-size:12.5px}
  .crm-stg-l i{font-style:normal;color:var(--muted);font-size:11px}
  .crm-stg-bar{height:8px;background:#f1f5f9;border-radius:5px;overflow:hidden}
  .crm-stg-bar span{display:block;height:100%;border-radius:5px;opacity:.75}
  .crm-stg-n{text-align:right;color:var(--muted)}
  @media (max-width:640px){.crm-stg-r{grid-template-columns:100px 1fr 110px}}
  .crm-deal{display:flex;gap:8px;align-items:flex-end;flex-wrap:wrap;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:8px 12px;margin-bottom:10px}
  .crm-deal .row{margin:0;flex:1;min-width:150px}
  .crm-deal .cd-save{margin-bottom:2px}
  .crm-pe input[type=text]{width:100%}
  .role-sales .lead-open,.role-sales .lk-chat,.role-sales .crm-chat,.role-sales #leadSalesFlt,.role-sales .tk-go{display:none!important}
'''
h = open(HT, encoding='utf-8').read()
if TAG in h: print('SUDAH', HT)
else:
    assert NEED in h, 'v1.2.215 belum terpasang di index.html'
    h = rep(h, '  .lk-empty{', CSS + '  .lk-empty{', what='html-css')
    h = rep(h, '<button data-tab="leads"    data-role="super_admin,admin,supervisor,wa_agent"', '<button data-tab="leads"    data-role="super_admin,admin,supervisor,wa_agent,sales"', what='html-nav-leads')
    h = rep(h, '<button data-tab="tasks"    data-role="super_admin,admin,supervisor,wa_agent"', '<button data-tab="tasks"    data-role="super_admin,admin,supervisor,wa_agent,sales"', what='html-nav-tasks')
    h = rep(h, '<button class="btn ghost sm lead-filter" data-lead-status="follow_up">Follow-up</button>',
            '<button class="btn ghost sm lead-filter" data-lead-status="follow_up">Follow-up</button>'
            '<button class="btn ghost sm lead-filter" data-lead-status="proposal">Penawaran</button>'
            '<button class="btn ghost sm lead-filter" data-lead-status="negosiasi">Negosiasi</button><!-- ' + TAG + ' -->', what='html-flt')
    h = rep(h, '<button class="btn ghost sm" id="crmRemBtn"', '<button class="btn ghost sm" id="crmPipeBtn" style="display:none" title="Nama tahap, peluang menang, tahap aktif">Tahap pipeline</button><button class="btn ghost sm" id="crmRemBtn"', what='html-pipebtn')
    h = rep(h, '      <div id="leadList"></div>', '      <div id="crmPipe"></div><!-- ' + TAG + ' -->\n      <div id="leadList"></div>', what='html-pipe')
    h = rep(h, '            <option value="wa_agent">WA Agent — hanya balas chat WhatsApp</option>\n          </select></div>',
            '            <option value="wa_agent">WA Agent — hanya balas chat WhatsApp</option>\n'
            '            <option value="sales">Sales — hanya lead &amp; task miliknya (paket Growth)</option><!-- ' + TAG + ' -->\n          </select></div>\n'
            '          <div class="row" id="u_sales_row" style="display:none"><label class="fl">Data Sales</label><select id="u_sales_id"><option value="">— Pilih data Sales —</option></select></div>', what='html-urole')
    h = rep(h, '<strong>WA Agent</strong>: balas chat WhatsApp.</p>', '<strong>WA Agent</strong>: balas chat WhatsApp. <strong>Sales</strong>: hanya lead &amp; task miliknya (terhubung ke data Sales, paket Growth).</p>', what='html-uintro')
    h = rep(h, '<script src="app.js?v=1.2.215"></script>', '<script src="app.js?v=1.2.216"></script><!-- ' + TAG + ' -->', what='html-ver')
    save(HT, h)
print('SELESAI patch', TAG)
