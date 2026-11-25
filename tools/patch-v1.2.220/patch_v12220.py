#!/usr/bin/env python3
"""v1.2.220 (sales-di-pengguna): sales dikelola dari Pengguna (Growth+).
- Kartu Sales di Tim & Agent dihapus (disembunyikan; markup tetap untuk kode lama).
- Pengguna > peran Sales: akun otomatis menjadi data sales (nama ikut nama akun) — bisa juga memakai data sales lama.
  Divisi dipilih dari daftar divisi yang sudah ada atau "+ Divisi baru"; nama divisi dinormalisasi
  (spasi, huruf besar/kecil) supaya tidak ada divisi ganda.
- Kartu "Sales tanpa akun login" di Pengguna untuk data sales lama: Buat akun / Nonaktifkan.
- Hapus akun Sales -> data sales dinonaktifkan (riwayat & laporan tetap).
Butuh v1.2.219. Idempoten. Pakai: patch_v12220.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H + '/dei-tenant'
TAG = 'v1.2.220: sales-di-pengguna'; NEED = 'v1.2.219: divisi-sales'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12220-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

DESC = ("Akun peran Sales otomatis menjadi nama sales yang bisa ditandai di chat &amp; lead (PO, Close Deal, laporan per sales). "
        "Hak lihat: lead &amp; laporan miliknya sendiri, satu divisi, atau semua sales — lead sales lain hanya bisa dilihat. "
        "Divisi menentukan cakupan &ldquo;satu divisi&rdquo;.")

# ======================= api =======================
LIB = r'''/* ---------- v1.2.220: sales-di-pengguna — divisi tanpa duplikat ---------- */
function crmDivCanon220($raw) {   // null = tidak diubah; '' = tanpa divisi; nama divisi memakai ejaan yang sudah ada
    if ($raw === null) return null;
    $d = mb_substr(trim(preg_replace('/\s+/u', ' ', (string)$raw)), 0, 40);
    if ($d === '') return '';
    foreach (slAll() as $x) { $e = trim((string)($x['div'] ?? '')); if ($e !== '' && mb_strtolower($e) === mb_strtolower($d)) return $e; }
    return $d;
}
function crmDivList220() {
    $o = [];
    foreach (slAll() as $x) {
        $e = trim((string)($x['div'] ?? '')); if ($e === '') continue;
        $k = mb_strtolower($e); if (!isset($o[$k])) $o[$k] = ['name' => $e, 'n' => 0];
        if (!empty($x['active'])) $o[$k]['n']++;   // hitung sales aktif
    }
    usort($o, function ($a, $b) { return strcasecmp($a['name'], $b['name']); });
    return array_values($o);
}
function crmSalesDiv220($sid) { static $m = null; if ($m === null) $m = slMap(); return (string)($m[(string)$sid]['div'] ?? ''); }
'''

s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API)
else:
    assert NEED in s, 'v1.2.219 belum terpasang di ' + API
    s = rep(s, "define('DEI_VERSION', 'v1.2.219');   // v1.2.219:",
            "define('DEI_VERSION', 'v1.2.220');   // " + TAG + " — sales dikelola dari Pengguna (data sales otomatis, pilih/buat divisi tanpa duplikat); v1.2.219:", what='ver')
    s = rep(s, "\nfunction deiGuardAgentPrivate($u, $num) {", "\n" + LIB + "function deiGuardAgentPrivate($u, $num) {", what='lib')
    # save_user: data sales otomatis
    s = rep(s, "            if ($sid216 === '' || !isset($sm216[$sid216])) jsonOut(['ok' => false, 'error' => 'Pilih data Sales untuk akun ini (tambah dulu di Tim & Agent > Sales bila belum ada).'], 400);",
            "            if ($sid216 === '') {   // " + TAG + ": tanpa pilihan -> pakai data sales akun ini / nama yang sama / buat baru\n"
            "                foreach ($users as $ux220) if (($ux220['username'] ?? '') === $username && ($ux220['role'] ?? '') === 'sales' && isset($sm216[(string)($ux220['sales_id'] ?? '')])) $sid216 = (string)$ux220['sales_id'];\n"
            "            }\n"
            "            if ($sid216 === '' && $name !== '') {\n"
            "                foreach ($sm216 as $id220 => $x220) if (mb_strtolower((string)($x220['name'] ?? '')) === mb_strtolower($name)) { $sid216 = (string)$id220; break; }\n"
            "            }\n"
            "            if ($sid216 !== '' && !isset($sm216[$sid216])) jsonOut(['ok' => false, 'error' => 'Data sales tidak ditemukan.'], 400);", what='su-sid')
    s = rep(s, "        writeJson(USERS_FILE, $users);\n        jsonOut(['ok' => true]);\n        break;\n    }\n\n    case 'delete_user': {",
            "        if ($role === 'sales') {   // " + TAG + ": data sales mengikuti akun (nama, divisi, aktif)\n"
            "            $div220 = crmDivCanon220(array_key_exists('sales_div', $in) ? $in['sales_div'] : null);\n"
            "            $by220 = (string)$me['username'];\n"
            "            $res220 = deiWithLock('sales', function () use ($sid216, $name, $div220, $by220) {\n"
            "                $items = slAll(); $now = wibDate('Y-m-d H:i:s'); $nm = mb_substr($name, 0, 60);\n"
            "                if ($sid216 !== '') {\n"
            "                    $hit = false;\n"
            "                    foreach ($items as $i => $x) {\n"
            "                        if ((string)$x['id'] !== $sid216) continue;\n"
            "                        $hit = true; $dup = false;\n"
            "                        foreach ($items as $y) if ((string)$y['id'] !== $sid216 && mb_strtolower((string)($y['name'] ?? '')) === mb_strtolower($nm)) $dup = true;\n"
            "                        if (!$dup && $nm !== '') $items[$i]['name'] = $nm;\n"
            "                        if ($div220 !== null) $items[$i]['div'] = $div220;\n"
            "                        $items[$i]['active'] = true; $items[$i]['updated_at'] = $now; $items[$i]['updated_by'] = $by220;\n"
            "                    }\n"
            "                    if (!$hit) return ['e' => 'Data sales tidak ditemukan.'];\n"
            "                    $id = $sid216;\n"
            "                } else {\n"
            "                    if (count($items) >= 200) return ['e' => 'Maksimal 200 sales.'];\n"
            "                    $id = 'sl_' . substr(md5(uniqid('', true)), 0, 8);\n"
            "                    $items[] = ['id' => $id, 'name' => $nm !== '' ? $nm : 'Sales', 'phone' => '', 'active' => true, 'div' => (string)$div220, 'created_at' => $now, 'by' => $by220];\n"
            "                }\n"
            "                writeJson(SALES_FILE, ['items' => $items]);\n"
            "                return ['id' => $id];\n"
            "            });\n"
            "            if (!is_array($res220) || !empty($res220['e'])) jsonOut(['ok' => false, 'error' => (string)($res220['e'] ?? 'Gagal menyimpan data sales.')], 400);\n"
            "            foreach ($users as $i220 => $x220) if (($x220['username'] ?? '') === $username) $users[$i220]['sales_id'] = (string)$res220['id'];\n"
            "        }\n"
            "        writeJson(USERS_FILE, $users);\n        jsonOut(['ok' => true]);\n        break;\n    }\n\n    case 'delete_user': {", what='su-write')
    s = rep(s, "        writeJson(USERS_FILE, $remaining);\n        jsonOut(['ok' => true]);",
            "        foreach ($users as $x220) {   // " + TAG + ": akun Sales dihapus -> data sales nonaktif (riwayat tetap)\n"
            "            if (($x220['username'] ?? '') !== $username || ($x220['role'] ?? '') !== 'sales' || empty($x220['sales_id'])) continue;\n"
            "            $sd220 = (string)$x220['sales_id'];\n"
            "            deiWithLock('sales', function () use ($sd220) { $it = slAll(); foreach ($it as $i => $y) if ((string)$y['id'] === $sd220) $it[$i]['active'] = false; writeJson(SALES_FILE, ['items' => $it]); });\n"
            "        }\n"
            "        writeJson(USERS_FILE, $remaining);\n        jsonOut(['ok' => true]);", what='del-user')
    s = rep(s, "                'sales_scope' => (string)($u['sales_scope'] ?? 'own'),   // v1.2.219: divisi-sales",
            "                'sales_scope' => (string)($u['sales_scope'] ?? 'own'),   // v1.2.219: divisi-sales\n"
            "                'sales_div'  => ($u['role'] ?? '') === 'sales' ? crmSalesDiv220($u['sales_id'] ?? '') : '',   // " + TAG, what='get-users')
    # sales_list: akun tertaut + daftar divisi
    s = rep(s, "        jsonOut(['ok' => true, 'locked' => false, 'items' => $items, 'manage' => $mgr]);",
            "        $lk220 = []; foreach ((array)readJson(USERS_FILE, []) as $x220) if (is_array($x220) && ($x220['role'] ?? '') === 'sales' && !empty($x220['sales_id'])) $lk220[(string)$x220['sales_id']] = (string)$x220['username'];   // " + TAG + "\n"
            "        foreach ($items as $i220 => $x220) $items[$i220]['user'] = $mgr ? ($lk220[$x220['id']] ?? '') : '';\n"
            "        jsonOut(['ok' => true, 'locked' => false, 'items' => $items, 'manage' => $mgr, 'divisions' => crmDivList220()]);", what='sl-list')
    s = rep(s, "        $div219 = array_key_exists('div', $in) ? mb_substr(trim(preg_replace('/\\s+/u', ' ', (string)$in['div'])), 0, 40) : null;",
            "        $div219 = array_key_exists('div', $in) ? crmDivCanon220($in['div']) : null;   // " + TAG, what='ss-div')
    save(API, s)

# ======================= dashboard: app.js =======================
JSLIB = r'''
  /* ---- v1.2.220: sales-di-pengguna — divisi & data sales di form Pengguna ---- */
  var uDiv220 = [];
  function uDivFill220() {
    var sel = document.getElementById('u_sales_div'); if (!sel) return;
    var cur = sel.dataset.want !== undefined ? sel.dataset.want : sel.value;
    sel.innerHTML = '<option value="">— Tanpa divisi —</option>' + uDiv220.map(function (d) { return '<option value="' + esc(d.name) + '">' + esc(d.name) + ' (' + d.n + ' sales)</option>'; }).join('') +
      '<option value="__new">＋ Divisi baru…</option>';
    uDivSet220(cur || '');
    sel.onchange = function () { var n = document.getElementById('u_sales_div_new'); if (n) { n.style.display = sel.value === '__new' ? '' : 'none'; if (sel.value === '__new') n.focus(); } };
  }
  function uDivSet220(v) {
    var sel = document.getElementById('u_sales_div'), n = document.getElementById('u_sales_div_new'); if (!sel) return;
    sel.dataset.want = v || '';
    var hit = uDiv220.filter(function (d) { return d.name.toLowerCase() === String(v || '').toLowerCase(); })[0];
    sel.value = hit ? hit.name : '';
    if (n) { n.value = ''; n.style.display = 'none'; }
  }
  function uDivGet220() {   // null = divisi baru belum diisi
    var sel = document.getElementById('u_sales_div'); if (!sel) return '';
    if (sel.value !== '__new') return sel.value;
    var v = ((document.getElementById('u_sales_div_new') || {}).value || '').replace(/\s+/g, ' ').trim();
    if (!v) return null;
    var hit = uDiv220.filter(function (d) { return d.name.toLowerCase() === v.toLowerCase(); })[0];
    return hit ? hit.name : v;   // sama dengan divisi yang ada -> pakai yang ada (tidak dobel)
  }
  function uOrphan220() {
    var box = document.getElementById('uSalesOrphan'); if (!box) return;
    var adm = user.role === 'super_admin' || user.role === 'admin';
    var list = uSales216.filter(function (x) { return x.active && !x.user; });
    if (!adm || !list.length) { box.style.display = 'none'; box.innerHTML = ''; return; }
    box.style.display = '';
    box.innerHTML = '<h3 style="margin-top:0">Sales tanpa akun login</h3><div class="desc">Data sales lama yang belum punya akun. Masih bisa ditandai di chat &amp; lead. Buatkan akun peran Sales, atau nonaktifkan bila sudah tidak dipakai (riwayat &amp; laporan tetap).</div>' +
      '<div class="scroll"><table class="tbl"><thead><tr><th>Nama</th><th>Divisi</th><th></th></tr></thead><tbody>' + list.map(function (x) {
        return '<tr data-id="' + esc(x.id) + '"><td>' + esc(x.name) + '</td><td>' + (x.div ? esc(x.div) : '<span class="help">—</span>') + '</td>' +
          '<td style="text-align:right;white-space:nowrap"><button type="button" class="btn ghost sm uo-acc">Buat akun</button> <button type="button" class="btn ghost sm uo-off">Nonaktifkan</button></td></tr>';
      }).join('') + '</tbody></table></div>';
    Array.prototype.forEach.call(box.querySelectorAll('tr[data-id]'), function (tr) {
      var x = list.filter(function (s) { return s.id === tr.dataset.id; })[0];
      tr.querySelector('.uo-acc').onclick = function () {
        resetUserForm();
        $('#u_role').value = 'sales'; $('#u_name').value = x.name;
        if ($('#u_sales_id')) $('#u_sales_id').value = x.id;
        uDivSet220(x.div || ''); toggleSpvRow(); updateSeatWarn();
        window.scrollTo({ top: 0, behavior: 'smooth' }); setTimeout(function () { $('#u_username').focus(); }, 300);
        toast('Isi username, email & password untuk ' + x.name + ', lalu Simpan Pengguna.');
      };
      tr.querySelector('.uo-off').onclick = function () {
        if (!confirm('Nonaktifkan sales "' + x.name + '"?\n\nTidak muncul lagi di pilihan sales chat & lead. Riwayat & laporan tetap.')) return;
        api('sales_save', { method: 'POST', body: { id: x.id, name: x.name, phone: x.phone || '', active: false } }).then(function (r) {
          if (r && r.ok) { toast('Sales dinonaktifkan.'); uSalesLoad216(); } else toast((r && r.error) || 'Gagal.', true);
        });
      };
    });
  }

'''

j = open(JS, encoding='utf-8').read()
if TAG in j: print('SUDAH', JS)
else:
    assert NEED in j, 'v1.2.219 belum terpasang di app.js'
    j = rep(j, "  // v1.2.147: leads-kanban — pilihan tampilan diingat per browser\n", JSLIB + "  // v1.2.147: leads-kanban — pilihan tampilan diingat per browser\n", what='js-lib')
    j = rep(j, "      sel.innerHTML = uSales216.length ? '<option value=\"\">— Pilih data Sales —</option>' + uSales216.map(function (x) { return '<option value=\"' + esc(x.id) + '\">' + esc(x.name) + (x.div ? ' — ' + esc(x.div) : '') + (x.active ? '' : ' (nonaktif)') + '</option>'; }).join('')\n        : '<option value=\"\">' + (r && r.locked ? 'Butuh paket Growth' : 'Belum ada data Sales — tambah di Tim & Agent > Sales') + '</option>';",
            "      uDiv220 = (r && r.divisions) || []; uDivFill220(); uOrphan220();   // " + TAG + "\n"
            "      sel.innerHTML = (r && r.locked) ? '<option value=\"\">Butuh paket Growth</option>' : '<option value=\"\">＋ Data sales baru (otomatis dari Nama)</option>' + uSales216.map(function (x) {\n"
            "        return '<option value=\"' + esc(x.id) + '\" data-div=\"' + esc(x.div || '') + '\">Pakai data lama: ' + esc(x.name) + (x.div ? ' — ' + esc(x.div) : '') + (x.user ? ' (akun ' + esc(x.user) + ')' : '') + (x.active ? '' : ' (nonaktif)') + '</option>';\n"
            "      }).join('');\n"
            "      sel.onchange = function () { var o = sel.options[sel.selectedIndex]; if (sel.value && o) uDivSet220(o.getAttribute('data-div') || ''); };", what='js-uload')
    j = rep(j, "if (body.role === 'sales') { body.sales_id = ($('#u_sales_id') || {}).value || ''; if (!body.sales_id) { toast('Pilih data Sales untuk akun Sales.', true); return; } }",
            "if (body.role === 'sales') { body.sales_id = ($('#u_sales_id') || {}).value || ''; body.sales_div = uDivGet220(); if (body.sales_div === null) { toast('Isi nama divisi baru.', true); $('#u_sales_div_new').focus(); return; } }   /* " + TAG + " */", what='js-usave')
    j = rep(j, "    var sc219 = document.getElementById('u_scope_row');",
            "    ['u_div_row', 'u_sales_help'].forEach(function (id) { var e = document.getElementById(id); if (e) e.style.display = ($('#u_role') && $('#u_role').value === 'sales') ? '' : 'none'; });   // " + TAG + "\n"
            "    var sc219 = document.getElementById('u_scope_row');", what='js-urow')
    j = rep(j, "data-scope=\"' + esc(u.sales_scope || 'own') + '\"", "data-scope=\"' + esc(u.sales_scope || 'own') + '\" data-div=\"' + esc(u.sales_div || '') + '\"", what='js-uedit')
    j = rep(j, "        if ($('#u_sales_scope')) $('#u_sales_scope').value = b.dataset.scope || 'own';   // v1.2.219: divisi-sales",
            "        if ($('#u_sales_scope')) $('#u_sales_scope').value = b.dataset.scope || 'own';   // v1.2.219: divisi-sales\n        uDivSet220(b.dataset.div || '');   // " + TAG, what='js-ueditset')
    j = rep(j, "    if ($('#u_sales_scope')) $('#u_sales_scope').value = 'own';   // v1.2.219: divisi-sales",
            "    if ($('#u_sales_scope')) $('#u_sales_scope').value = 'own';   // v1.2.219: divisi-sales\n    uDivSet220('');   // " + TAG, what='js-ureset')
    j = rep(j, "'<span class=\"help\" style=\"font-size:11px\">Data sales: ' + esc(uSalesName216(u.sales_id)) + ' · ' +",
            "'<span class=\"help\" style=\"font-size:11px\">' + (u.sales_div ? 'Divisi ' + esc(u.sales_div) : 'Tanpa divisi') + ' · ' +", what='js-ucol')
    j = rep(j, "      if (res.ok) { toast('Pengguna disimpan.'); resetUserForm(); renderUsers(); }",
            "      if (res.ok) { toast('Pengguna disimpan.'); resetUserForm(); renderUsers(); uSalesLoad216(); }   // " + TAG, what='js-usaved')
    j = rep(j, "'<tr><td colspan=\"14\" class=\"help\">Belum ada data Sales. Tambah di Tim &amp; Agent &gt; Sales.</td></tr>'",
            "'<tr><td colspan=\"14\" class=\"help\">Belum ada sales. Buat akun peran Sales di Pengguna.</td></tr>'", what='js-perf-txt')
    j = rep(j, "Di <b>Tim &amp; Agent › Sales</b>, isi kolom <b>Divisi</b> tiap sales (mis. Industri, Government, Corporate).",
            "Di <b>Pengguna</b>, pilih peran <b>Sales</b>, lalu pilih <b>Divisi</b> yang ada atau <b>＋ Divisi baru</b> (mis. Industri, Government, Corporate).", what='js-help219')
    j = rep(j, "(pilih data Sales)", "(data sales &amp; divisi dibuat dari form yang sama)", what='js-help216')
    save(JS, j)

# ======================= dashboard: index.html =======================
CSS = r'''  /* v1.2.220: sales-di-pengguna */
  #slCard{display:none!important}
'''
h = open(HT, encoding='utf-8').read()
if TAG in h: print('SUDAH', HT)
else:
    assert NEED in h, 'v1.2.219 belum terpasang di index.html'
    h = rep(h, '  .lk-empty{', CSS + '  .lk-empty{', what='html-css')
    h = rep(h, 'Mode balasan WhatsApp, routing, kursi tim, dan daftar Sales. Laporan per Agent &amp; per Sales ada di menu Laporan &amp; Log.',
            'Mode balasan WhatsApp, routing, dan kursi tim. Akun Sales dikelola di menu Pengguna. Laporan per Agent &amp; per Sales ada di menu Laporan &amp; Log.', what='html-tim')
    h = rep(h, '          <div class="row" id="u_scope_row" style="display:none">',
            '          <div class="row" id="u_div_row" style="display:none"><label class="fl">Divisi</label>'
            '<div style="display:flex;gap:6px;flex-wrap:wrap"><select id="u_sales_div" style="flex:1;min-width:180px"><option value="">— Tanpa divisi —</option></select>'
            '<input type="text" id="u_sales_div_new" maxlength="40" placeholder="Nama divisi baru, mis. Government" style="display:none;flex:1;min-width:180px"></div></div><!-- ' + TAG + ' -->\n'
            '          <div class="row" id="u_scope_row" style="display:none">', what='html-div')
    h = rep(h, '<div class="row" id="u_sales_row" style="display:none"><label class="fl">Data Sales</label><select id="u_sales_id"><option value="">— Pilih data Sales —</option></select></div>',
            '<div class="row" id="u_sales_row" style="display:none"><label class="fl">Data sales (untuk tag &amp; laporan)</label><select id="u_sales_id"><option value="">＋ Data sales baru (otomatis dari Nama)</option></select></div>\n'
            '          <div class="help" id="u_sales_help" style="display:none;grid-column:1/-1;margin-top:-6px">' + DESC + '</div><!-- ' + TAG + ' -->', what='html-help')
    h = rep(h, '      <div class="card" id="llCard" style="display:none">',
            '      <div class="card" id="uSalesOrphan" style="display:none"></div><!-- ' + TAG + ' -->\n      <div class="card" id="llCard" style="display:none">', what='html-orphan')
    h = rep(h, '<script src="app.js?v=1.2.219"></script>', '<script src="app.js?v=1.2.220"></script><!-- ' + TAG + ' -->', what='html-ver')
    save(HT, h)
print('SELESAI patch', TAG)
