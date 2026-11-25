#!/usr/bin/env python3
"""v1.2.219 (divisi-sales): divisi Sales + hak lihat per akun Sales (Growth+).
- Data Sales (Tim & Agent > Sales) punya kolom Divisi (mis. Industri, Government, Corporate).
- Akun Sales (Pengguna) punya Hak lihat: Miliknya saja / Satu divisi / Semua sales.
  Lead & laporan sales lain dalam cakupan itu bisa DILIHAT (Leads, Pipeline, Performa, email mingguan),
  tapi yang bisa diubah tetap hanya lead miliknya (kartu lain bertanda "Lihat saja").
- Perbaiki teks petunjuk lokasi data Sales (Tim & Agent > Sales).
Butuh v1.2.218. Idempoten. Pakai: patch_v12219.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H + '/dei-tenant'
TAG = 'v1.2.219: divisi-sales'; NEED = 'v1.2.218: sales-di-lead'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12219-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ======================= api =======================
LIB = r'''/* ---------- v1.2.219: divisi-sales — hak lihat akun Sales: own | division | all ---------- */
function crmSalesScope219($u) { $s = (string)($u['sales_scope'] ?? 'own'); return in_array($s, ['own', 'division', 'all'], true) ? $s : 'own'; }
function crmSalesVisible219($u) {   // null = semua lead; array = id data Sales yang boleh dilihat
    $sid = crmMySales216($u); $sc = crmSalesScope219($u);
    if ($sc === 'all') return null;
    if ($sid === '') return [];
    if ($sc === 'division') {
        $map = slMap(); $div = mb_strtolower(trim((string)($map[$sid]['div'] ?? '')));
        if ($div !== '') { $o = []; foreach ($map as $id => $x) if (mb_strtolower(trim((string)($x['div'] ?? ''))) === $div) $o[] = (string)$id; return $o; }
    }
    return [$sid];
}
function crmSalesCanRead219($u, $num) {
    if (crmSalesOwns216($u, $num)) return true;
    $num = waNormNum($num); $l = leadsGetAll()[$num] ?? null;
    if (!is_array($l)) return false;
    $vis = crmSalesVisible219($u);
    return $vis === null || in_array(slLeadSalesId($l, $num, [$num => waContactGet($num)]), $vis, true);
}
'''

s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API)
else:
    assert NEED in s, 'v1.2.218 belum terpasang di ' + API
    s = rep(s, "define('DEI_VERSION', 'v1.2.218');   // v1.2.218:",
            "define('DEI_VERSION', 'v1.2.219');   // " + TAG + " — divisi Sales + hak lihat akun Sales (miliknya / satu divisi / semua, lihat saja); v1.2.218:", what='ver')
    s = rep(s, "\nfunction deiGuardAgentPrivate($u, $num) {", "\n" + LIB + "function deiGuardAgentPrivate($u, $num) {", what='lib')
    s = rep(s, "Laporan & Log > Per Sales", "Tim & Agent > Sales", what='txt')
    # data Sales: divisi
    s = rep(s, "        $act = array_key_exists('active', $in) ? !empty($in['active']) : null;\n",
            "        $act = array_key_exists('active', $in) ? !empty($in['active']) : null;\n"
            "        $div219 = array_key_exists('div', $in) ? mb_substr(trim(preg_replace('/\\s+/u', ' ', (string)$in['div'])), 0, 40) : null;   // " + TAG + "\n", what='ss-div')
    s = rep(s, "$res = deiWithLock('sales', function () use ($id, $name, $phone, $act, $by) {",
            "$res = deiWithLock('sales', function () use ($id, $name, $phone, $act, $by, $div219) {", what='ss-use')
    s = rep(s, "                if ($act !== null) $x['active'] = $act;\n",
            "                if ($act !== null) $x['active'] = $act;\n                if ($div219 !== null) $x['div'] = $div219;\n", what='ss-upd')
    s = rep(s, "'active' => true, 'created_at' => wibDate('Y-m-d H:i:s'), 'by' => $by];",
            "'active' => true, 'div' => (string)$div219, 'created_at' => wibDate('Y-m-d H:i:s'), 'by' => $by];", what='ss-new')
    s = rep(s, "$items[] = ['id' => (string)$x['id'], 'name' => (string)($x['name'] ?? ''), 'phone' => (string)($x['phone'] ?? ''), 'active' => !empty($x['active'])];",
            "$items[] = ['id' => (string)$x['id'], 'name' => (string)($x['name'] ?? ''), 'phone' => (string)($x['phone'] ?? ''), 'active' => !empty($x['active']), 'div' => (string)($x['div'] ?? '')];", what='sl-list')
    # Pengguna: hak lihat
    s = rep(s, "        $sid216 = '';   // v1.2.216: pipeline-sales: akun Sales terhubung ke satu data Sales\n",
            "        $sid216 = '';   // v1.2.216: pipeline-sales: akun Sales terhubung ke satu data Sales\n"
            "        $scope219 = in_array((string)($in['sales_scope'] ?? 'own'), ['own', 'division', 'all'], true) ? (string)($in['sales_scope'] ?? 'own') : 'own';   // " + TAG + "\n", what='u-scope')
    s = rep(s, "                if ($role === 'sales') $users[$i]['sales_id'] = $sid216; else unset($users[$i]['sales_id']);",
            "                if ($role === 'sales') { $users[$i]['sales_id'] = $sid216; $users[$i]['sales_scope'] = $scope219; } else unset($users[$i]['sales_id'], $users[$i]['sales_scope']);   // " + TAG, what='u-upd')
    s = rep(s, "            if ($role === 'sales') $users[count($users) - 1]['sales_id'] = $sid216;",
            "            if ($role === 'sales') { $users[count($users) - 1]['sales_id'] = $sid216; $users[count($users) - 1]['sales_scope'] = $scope219; }   // " + TAG, what='u-new')
    s = rep(s, "                'sales_id'   => (string)($u['sales_id'] ?? ''),",
            "                'sales_id'   => (string)($u['sales_id'] ?? ''),\n                'sales_scope' => (string)($u['sales_scope'] ?? 'own'),   // " + TAG, what='u-get')
    # get_leads: cakupan lihat + tanda ro
    s = rep(s, "        if (($u216['role'] ?? '') === 'sales') { $my216 = crmMySales216($u216); $out = array_values(array_filter($out, function ($x) use ($my216) { return $my216 !== '' && $x['sales_id'] === $my216; })); }",
            "        if (($u216['role'] ?? '') === 'sales') {   // " + TAG + ": cakupan lihat; selain miliknya = lihat saja\n"
            "            $my216 = crmMySales216($u216); $vis219 = crmSalesVisible219($u216);\n"
            "            $out = array_values(array_filter($out, function ($x) use ($my216, $vis219) { return ($my216 !== '' && $x['sales_id'] === $my216) || $vis219 === null || in_array($x['sales_id'], $vis219, true); }));\n"
            "            foreach ($out as &$o219) $o219['ro'] = !($my216 !== '' && $o219['sales_id'] === $my216);\n"
            "            unset($o219);\n"
            "        }", what='gl-filter')
    s = rep(s, "'pipeline' => crmOk215() ? crmPipeConf216() : null]);",
            "'pipeline' => crmOk215() ? crmPipeConf216() : null, 'sales_scope' => (($u216['role'] ?? '') === 'sales' ? crmSalesScope219($u216) : '')]);", what='gl-out')
    # lead_acts: Sales boleh baca lead dalam cakupan
    s = rep(s, "        $num = waNormNum($_GET['number'] ?? '');\n        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);\n        deiGuardAgentPrivate($u, $num);\n        $l = leadsGetAll()[$num] ?? null;",
            "        $num = waNormNum($_GET['number'] ?? '');\n        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);\n"
            "        $ro219 = false;   // " + TAG + "\n"
            "        if (($u['role'] ?? '') === 'sales') { if (!crmSalesCanRead219($u, $num)) jsonOut(['ok' => false, 'error' => 'Lead ini di luar cakupan Anda.'], 403); $ro219 = !crmSalesOwns216($u, $num); }\n"
            "        else deiGuardAgentPrivate($u, $num);\n"
            "        $l = leadsGetAll()[$num] ?? null;", what='acts-guard')
    s = rep(s, "            if (tkCanSee214($u, $t)) $tasks[] = tkPublic214($u, $t);",
            "            if (tkCanSee214($u, $t) || $ro219) $tasks[] = tkPublic214($u, $t);", what='acts-tasks')
    s = rep(s, "        jsonOut(['ok' => true, 'number' => $num,\n            'lead' => is_array($l)",
            "        jsonOut(['ok' => true, 'number' => $num, 'ro' => $ro219,\n            'lead' => is_array($l)", what='acts-ro')
    # Performa & email mingguan: cakupan
    s = rep(s, "        $only = ($u['role'] ?? '') === 'sales' ? crmMySales216($u) : null;\n        if ($only === '') jsonOut(['ok' => false, 'error' => 'Akun Sales Anda belum terhubung ke data Sales.'], 400);\n        jsonOut(['ok' => true, 'own' => $only !== null] + crmPerf217($fromD, $toD, $only));",
            "        $only = null; $own = false;   // " + TAG + "\n"
            "        if (($u['role'] ?? '') === 'sales') {\n"
            "            if (crmMySales216($u) === '') jsonOut(['ok' => false, 'error' => 'Akun Sales Anda belum terhubung ke data Sales.'], 400);\n"
            "            $only = crmSalesVisible219($u); $own = is_array($only) && count($only) === 1;\n"
            "        }\n"
            "        jsonOut(['ok' => true, 'own' => $own] + crmPerf217($fromD, $toD, $only));", what='perf')
    s = rep(s, "        if ($onlySid !== null && (string)$id !== $onlySid) continue;",
            "        if ($onlySid !== null && !in_array((string)$id, (array)$onlySid, true)) continue;   // " + TAG, what='perf-only')
    s = rep(s, "if ($onlySid === null || $sid === $onlySid) $users[$bn]", "if ($onlySid === null || in_array($sid, (array)$onlySid, true)) $users[$bn]", what='perf-users')
    s = rep(s, "{ $out[] = [$em, $nm, (string)$x['sales_id']]; $seen[$em] = 1; }",
            "{ $out[] = [$em, $nm, crmSalesVisible219($x)]; $seen[$em] = 1; }   // " + TAG, what='wk-rc')
    s = rep(s, "        $r = crmWeeklyMail217($em, $nm, $rep, $sid !== null);",
            "        $r = crmWeeklyMail217($em, $nm, $rep, $sid !== null && count((array)$sid) === 1);   // " + TAG, what='wk-own')
    save(API, s)

# ======================= dashboard: app.js =======================
HELP_ADD = r'''    { id: 'divisi-sales', roles: R_ALL, t: 'Divisi sales & hak lihat akun Sales', k: 'divisi sales industri government corporate hak lihat akses role peran cakupan laporan sales lain lihat saja',   // v1.2.219: divisi-sales
      s: ['Di <b>Tim &amp; Agent › Sales</b>, isi kolom <b>Divisi</b> tiap sales (mis. Industri, Government, Corporate).', 'Di <b>Pengguna</b>, akun Sales punya <b>Hak lihat</b>: Miliknya saja, Satu divisi (semua sales dengan divisi yang sama), atau Semua sales.', 'Lead &amp; laporan sales lain dalam cakupan itu hanya bisa dilihat (tanda <b>Lihat saja</b>); yang bisa diubah tetap lead miliknya sendiri.'],
      show: [{ tab: 'users', el: '#u_role', title: 'Peran Sales', body: '<p>Pilih Sales, data Sales, lalu Hak lihat.</p>' }] },
'''
SCOPE_LBL = "({ own: 'lihat miliknya', division: 'lihat satu divisi', all: 'lihat semua sales' }[u.sales_scope || 'own'])"

j = open(JS, encoding='utf-8').read()
if TAG in j: print('SUDAH', JS)
else:
    assert NEED in j, 'v1.2.218 belum terpasang di app.js'
    j = rep(j, "    { id: 'kontak', roles: R_ALL,", HELP_ADD + "    { id: 'kontak', roles: R_ALL,", what='js-help')
    j = rep(j, "Laporan & Log > Per Sales", "Tim & Agent > Sales", what='js-txt1')
    j = rep(j, "Laporan &amp; Log &gt; Per Sales", "Tim &amp; Agent &gt; Sales", what='js-txt2')
    # Tim & Agent > Sales: kolom Divisi
    j = rep(j, "'<td><input type=\"text\" class=\"sl-ph\" value=\"' + esc(s.phone) + '\" maxlength=\"20\" placeholder=\"opsional\" style=\"min-width:110px\"></td>' +",
            "'<td><input type=\"text\" class=\"sl-ph\" value=\"' + esc(s.phone) + '\" maxlength=\"20\" placeholder=\"opsional\" style=\"min-width:110px\"></td>' +\n"
            "          '<td><input type=\"text\" class=\"sl-div\" value=\"' + esc(s.div || '') + '\" maxlength=\"40\" list=\"slDivList\" placeholder=\"mis. Corporate\" style=\"min-width:120px\"></td>' +   // " + TAG, what='js-sl-td')
    j = rep(j, "'<tr><td colspan=\"4\" style=\"color:var(--muted)\">Belum ada sales. Tambahkan di bawah.</td></tr>'",
            "'<tr><td colspan=\"5\" style=\"color:var(--muted)\">Belum ada sales. Tambahkan di bawah.</td></tr>'", what='js-sl-empty')
    j = rep(j, "        var sv = function () { slSave203({ id: id, name: tr.querySelector('.sl-nm').value, phone: tr.querySelector('.sl-ph').value, active: tr.querySelector('.sl-on').checked }); };",
            "        var sv = function () { slSave203({ id: id, name: tr.querySelector('.sl-nm').value, phone: tr.querySelector('.sl-ph').value, div: tr.querySelector('.sl-div').value, active: tr.querySelector('.sl-on').checked }); };   // " + TAG + "\n"
            "        tr.querySelector('.sl-div').onkeydown = function (e) { if (e.key === 'Enter') sv(); };", what='js-sl-sv')
    j = rep(j, "      $$('#tblSl tr[data-sl]').forEach(function (tr) {",
            "      var dl219 = document.getElementById('slDivList'), dv219 = {};   // " + TAG + "\n"
            "      it.forEach(function (s) { if (s.div) dv219[s.div] = 1; });\n"
            "      if (dl219) dl219.innerHTML = Object.keys(dv219).sort().map(function (d) { return '<option value=\"' + esc(d) + '\">'; }).join('');\n"
            "      $$('#tblSl tr[data-sl]').forEach(function (tr) {", what='js-sl-dl')
    j = rep(j, "    $('#btnSlAdd').onclick = function () { slSave203({ name: $('#slName').value, phone: $('#slPhone').value }, function () { $('#slName').value = ''; $('#slPhone').value = ''; }); };",
            "    $('#btnSlAdd').onclick = function () { slSave203({ name: $('#slName').value, phone: $('#slPhone').value, div: ($('#slDiv') || {}).value || '' }, function () { $('#slName').value = ''; $('#slPhone').value = ''; }); };   // " + TAG, what='js-sl-add')
    j = rep(j, "esc(x.name) + (x.active ? '' : ' (nonaktif)')", "esc(x.name) + (x.div ? ' — ' + esc(x.div) : '') + (x.active ? '' : ' (nonaktif)')", what='js-u-opt')
    # Pengguna: Hak lihat
    j = rep(j, "    var sr216 = document.getElementById('u_sales_row');",
            "    var sc219 = document.getElementById('u_scope_row'); if (sc219) sc219.style.display = ($('#u_role') && $('#u_role').value === 'sales') ? '' : 'none';   // " + TAG + "\n"
            "    var sr216 = document.getElementById('u_sales_row');", what='js-u-row')
    j = rep(j, "    if (body.role === 'sales') { body.sales_id",
            "    if (body.role === 'sales' && $('#u_sales_scope')) body.sales_scope = $('#u_sales_scope').value;   // " + TAG + "\n"
            "    if (body.role === 'sales') { body.sales_id", what='js-u-save')
    j = rep(j, "data-sid=\"' + esc(u.sales_id || '') + '\"", "data-sid=\"' + esc(u.sales_id || '') + '\" data-scope=\"' + esc(u.sales_scope || 'own') + '\"", what='js-u-edit')
    j = rep(j, "$('#u_sales_id').value = b.dataset.sid || ''; }   // v1.2.216: pipeline-sales",
            "$('#u_sales_id').value = b.dataset.sid || ''; }   // v1.2.216: pipeline-sales\n"
            "        if ($('#u_sales_scope')) $('#u_sales_scope').value = b.dataset.scope || 'own';   // " + TAG, what='js-u-editset')
    j = rep(j, "    if ($('#u_sales_id')) $('#u_sales_id').value = '';   // v1.2.216: pipeline-sales",
            "    if ($('#u_sales_id')) $('#u_sales_id').value = '';   // v1.2.216: pipeline-sales\n    if ($('#u_sales_scope')) $('#u_sales_scope').value = 'own';   // " + TAG, what='js-u-reset')
    j = rep(j, "esc(uSalesName216(u.sales_id)) + '</span>'", "esc(uSalesName216(u.sales_id)) + ' · ' + " + SCOPE_LBL + " + '</span>'", what='js-u-col')
    # Leads: lihat saja
    j = rep(j, "      leadCrm215 = !!res.crm; crmToolbar215();   // v1.2.215: crm-aktivitas\n",
            "      leadCrm215 = !!res.crm; crmToolbar215();   // v1.2.215: crm-aktivitas\n"
            "      document.body.classList.toggle('sales-wide', !!res.sales_scope && res.sales_scope !== 'own');   // " + TAG + "\n", what='js-wide')
    j = rep(j, "slLeadBadge203(l) + crmDealChip216(l) + crmFuChip215(l) + /* v1.2.215: crm-aktivitas; v1.2.216: pipeline-sales */",
            "slLeadBadge203(l) + crmDealChip216(l) + crmFuChip215(l) + (l.ro ? ' <span class=\"tag crm-ro-t\" title=\"Lead sales lain — hanya bisa dilihat\">Lihat saja</span>' : '') + /* v1.2.215: crm-aktivitas; v1.2.216: pipeline-sales; " + TAG + " */", what='js-l-ro')
    j = rep(j, "'<select class=\"lead-status\">' + opsi + '</select></div>' +", "'<select class=\"lead-status\"' + (l.ro ? ' disabled' : '') + '>' + opsi + '</select></div>' +", what='js-l-st')
    j = rep(j, "'<textarea class=\"lead-note\" rows=\"2\" placeholder=\"Catatan agent...\">'", "'<textarea class=\"lead-note\" rows=\"2\" placeholder=\"Catatan agent...\"' + (l.ro ? ' readonly' : '') + '>'", what='js-l-note')
    j = rep(j, "'<div class=\"lk-card\" draggable=\"true\" data-lead=\"' + esc(l.number) + '\"",
            "'<div class=\"lk-card' + (l.ro ? ' lk-ro' : '') + '\" draggable=\"' + (l.ro ? 'false' : 'true') + '\" data-lead=\"' + esc(l.number) + '\"", what='js-k-drag')
    j = rep(j, "'<div class=\"lk-f\"><select class=\"lk-st\" aria-label=\"Status\">' + leadStatusOptionsHtml(l.status",
            "(l.ro ? '<div class=\"lk-s\"><span class=\"tag crm-ro-t\">Lihat saja</span></div>' : '') + '<div class=\"lk-f\"><select class=\"lk-st\" aria-label=\"Status\"' + (l.ro ? ' disabled' : '') + '>' + leadStatusOptionsHtml(l.status", what='js-k-st')
    j = rep(j, "          crmDealWire216(ov, num, function (x) { if (x.acts) { acts = x.acts; paintTl(); } changed(); });   // v1.2.216: pipeline-sales\n",
            "          crmDealWire216(ov, num, function (x) { if (x.acts) { acts = x.acts; paintTl(); } changed(); });   // v1.2.216: pipeline-sales\n"
            "          if (r.ro) {   // " + TAG + ": lead sales lain — lihat saja\n"
            "            ov.querySelector('.tk-box').classList.add('crm-ro');\n"
            "            Array.prototype.forEach.call(ov.querySelectorAll('.crm-deal input, .crm-info input, .crm-info select'), function (x) { x.disabled = true; });\n"
            "            ov.querySelector('.crm-hd').insertAdjacentHTML('afterend', '<div class=\"crm-ro-n\">' + ico('eye', 13) + ' Lihat saja — lead ini dipegang ' + esc(l.sales_name || 'sales lain') + '. Hanya lead milik Anda yang bisa diubah.</div>');\n"
            "          }\n", what='js-modal-ro')
    j = rep(j, "  // Expose for inline replacement of static markup\n  window._ico = ico;",
            "  if (!ICONS.eye) ICONS.eye = '<path d=\"M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z\"/><circle cx=\"12\" cy=\"12\" r=\"3\"/>';   // " + TAG + "\n"
            "  // Expose for inline replacement of static markup\n  window._ico = ico;", what='js-icon')
    save(JS, j)

# ======================= dashboard: index.html =======================
CSS = r'''  /* v1.2.219: divisi-sales */
  .tag.crm-ro-t{background:#f1f5f9;color:#475569}
  .lk-card.lk-ro{background:#fbfbfd}
  .crm-ro-n{display:flex;gap:6px;align-items:center;background:#f1f5f9;color:#475569;border-radius:8px;padding:7px 10px;font-size:12.5px;margin:-4px 0 10px}
  .crm-ro .crm-form,.crm-ro .cd-save,.crm-ro .ci-save,.crm-ro .crm-tnew,.crm-ro .crm-del{display:none!important}
  .crm-ro .crm-fu-ck,.crm-ro .crm-tk{pointer-events:none}
  .role-sales.sales-wide #leadSalesFlt{display:inline-block!important}
'''
h = open(HT, encoding='utf-8').read()
if TAG in h: print('SUDAH', HT)
else:
    assert NEED in h, 'v1.2.218 belum terpasang di index.html'
    h = rep(h, '  .lk-empty{', CSS + '  .lk-empty{', what='html-css')
    h = rep(h, '<th>Nama</th><th>No. HP</th><th>Aktif</th><th></th>', '<th>Nama</th><th>No. HP</th><th>Divisi</th><th>Aktif</th><th></th>', what='html-sl-th')
    h = rep(h, '            <div><label class="fl">No. HP (opsional)</label><input type="text" id="slPhone" maxlength="20" style="width:auto"></div>',
            '            <div><label class="fl">No. HP (opsional)</label><input type="text" id="slPhone" maxlength="20" style="width:auto"></div>\n'
            '            <div><label class="fl">Divisi (opsional)</label><input type="text" id="slDiv" maxlength="40" list="slDivList" placeholder="mis. Corporate" style="width:auto"><datalist id="slDivList"></datalist></div><!-- ' + TAG + ' -->', what='html-sl-add')
    h = rep(h, 'Sales tidak perlu akun login.', 'Sales tidak wajib punya akun login; bila perlu, buat akun peran Sales di Pengguna. Kolom Divisi dipakai untuk hak lihat akun Sales (satu divisi).', what='html-sl-desc')
    h = rep(h, '          <div class="row" id="u_sales_row" style="display:none">',
            '          <div class="row" id="u_scope_row" style="display:none"><label class="fl">Hak lihat</label><select id="u_sales_scope">'
            '<option value="own">Miliknya saja — lead &amp; laporan sendiri</option>'
            '<option value="division">Satu divisi — lihat lead &amp; laporan sales sedivisi</option>'
            '<option value="all">Semua sales — lihat semua lead &amp; laporan</option></select></div><!-- ' + TAG + ' -->\n'
            '          <div class="row" id="u_sales_row" style="display:none">', what='html-u-scope')
    h = rep(h, '<strong>Sales</strong>: hanya lead &amp; task miliknya (terhubung ke data Sales, paket Growth).</p>', '<strong>Sales</strong>: lead &amp; task miliknya; bisa diberi hak lihat satu divisi atau semua sales (lihat saja, paket Growth).</p>', what='html-uintro')
    h = rep(h, '<script src="app.js?v=1.2.218"></script>', '<script src="app.js?v=1.2.219"></script><!-- ' + TAG + ' -->', what='html-ver')
    save(HT, h)
print('SELESAI patch', TAG)
