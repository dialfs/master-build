#!/usr/bin/env python3
"""v1.2.221 (laporan-sales): menu Laporan Sales (Growth+).
- Sidebar baru "Laporan Sales" (Super Admin, Admin, Supervisor, Sales sesuai hak lihat).
- Tampilan: Performa & Target · Aktivitas · Produktivitas · Forecast · Funnel & Win/Loss · Umur Lead.
- Filter periode (+ kuartal & tahun), sales, divisi; CSV per tampilan.
- Target bulanan per sales (nilai deal, jumlah deal, aktivitas) — Super Admin / Admin; data/sales-targets.json.
- API: sales_rep (GET), sales_target_save (POST). sales_rep masuk daftar aksi peran Sales.
Butuh v1.2.220. Idempoten. Pakai: patch_v12221.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H + '/dei-tenant'
TD = os.path.dirname(os.path.abspath(__file__))
TAG = 'v1.2.221: laporan-sales'; NEED = 'v1.2.220: sales-di-pengguna'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12221-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
rd = lambda f: open(os.path.join(TD, 'src', f), encoding='utf-8').read()
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ======================= api =======================
s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API)
else:
    assert NEED in s, 'v1.2.220 belum terpasang di ' + API
    s = rep(s, "define('DEI_VERSION', 'v1.2.220');   // v1.2.220:",
            "define('DEI_VERSION', 'v1.2.221');   // " + TAG + " — menu Laporan Sales: performa vs target, aktivitas, produktivitas, forecast, funnel & win/loss, umur lead; v1.2.220:", what='ver')
    s = rep(s, "\nfunction deiGuardAgentPrivate($u, $num) {", "\n" + rd('lib221.php') + "function deiGuardAgentPrivate($u, $num) {", what='lib')
    s = rep(s, "    case 'crm_weekly_get': {", rd('cases221.php') + "    case 'crm_weekly_get': {", what='cases')
    s = rep(s, "'crm_badge', 'crm_remind_test', 'crm_sales_perf',", "'crm_badge', 'crm_remind_test', 'crm_sales_perf', 'sales_rep',", what='sales-actions')
    save(API, s)

# ======================= app.js =======================
s = open(JS, encoding='utf-8').read()
if TAG in s: print('SUDAH', JS)
else:
    assert NEED in s, 'v1.2.220 belum terpasang di ' + JS
    s = rep(s, "  if (!ICONS.plus) ICONS.plus", "  if (!ICONS['trending-up']) ICONS['trending-up'] = '<polyline points=\"22 7 13.5 15.5 8.5 10.5 2 17\"/><polyline points=\"16 7 22 7 22 13\"/>';   // " + TAG + "\n  if (!ICONS.plus) ICONS.plus", what='icon')
    s = rep(s, "  /* ---- v1.2.218: sales-di-lead — assign Sales dari kartu Leads ---- */",
            rd('js221.js').replace('  /* ====', '  /* ' + TAG + ' */\n  /* ====', 1) + "\n\n  /* ---- v1.2.218: sales-di-lead — assign Sales dari kartu Leads ---- */", what='js')
    s = rep(s, "    tasks: loadTasks214,   // v1.2.214: task", "    tasks: loadTasks214,   // v1.2.214: task\n    salesrep: srLoad221,   // " + TAG, what='loader')
    s = rep(s, "    { id: 'divisi-sales', roles: R_ALL,",
            "    { id: 'laporan-sales', roles: 'super_admin,admin,supervisor,sales', t: 'Laporan Sales: performa vs target, aktivitas, produktivitas, forecast, funnel', k: 'laporan sales report activity aktivitas forecast proyeksi produktivitas productivity performa performance target kuota funnel konversi win loss kalah menang umur lead aging diam sumber lead',   // " + TAG + "\n"
            "      s: ['Buka menu <b>Laporan Sales</b>. Pilih periode (Bulan ini, Kuartal ini, dst.), lalu saring per sales atau divisi bila perlu.', "
            "'<b>Performa &amp; Target</b>: nilai &amp; jumlah Close Deal dibanding target, win rate, rata-rata deal, lama closing. <b>Aktivitas</b>: grafik harian, per sales &amp; jenis, daftar aktivitas. "
            "<b>Produktivitas</b>: aktivitas per hari kerja, lead disentuh, kepatuhan follow-up, kecepatan respons lead baru.', "
            "'<b>Forecast</b>: pipeline per bulan perkiraan closing (commit, best case, tertimbang) dan proyeksi vs target. <b>Funnel &amp; Win/Loss</b>: konversi antar tahap, per sumber lead, alasan kalah. <b>Umur Lead</b>: lead yang lama tidak disentuh.', "
            "'Admin: tombol <b>Target sales</b> untuk mengisi target bulanan per sales. Semua tampilan bisa diunduh lewat <b>CSV</b>. Akun Sales melihat sesuai hak lihatnya.'],\n"
            "      show: [{ tab: 'salesrep', el: '#srSeg', title: 'Laporan Sales', body: '<p>Pilih tampilan laporan di sini, lalu atur periode &amp; filter di bawahnya.</p>' }] },\n"
            "    { id: 'divisi-sales', roles: R_ALL,", what='help')
    save(JS, s)

# ======================= index.html =======================
CSS = r'''  /* v1.2.221: laporan-sales */
  .sr-bar-card{padding:12px 14px;margin-bottom:12px}
  .sr-per{font-size:13px;font-weight:600;color:var(--brand);margin:2px 2px 10px}
  .sr-card{padding:14px 16px;margin-top:12px}
  .sr-h{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:10px}
  .sr-h b{font-size:14.5px}
  .sr-t th,.sr-t td.num{white-space:nowrap}
  .sr-t td.num{text-align:right;font-variant-numeric:tabular-nums}
  .sr-t td:first-child{min-width:130px}
  .sr-t td.sr-txt{min-width:220px;max-width:420px;white-space:normal}
  .sr-bar{display:inline-block;width:70px;height:7px;border-radius:9px;background:#eceef4;vertical-align:middle;overflow:hidden}
  .sr-bar i{display:block;height:100%;background:var(--brand);border-radius:9px}
  .sr-bar.good i{background:#16a34a}.sr-bar.bad i{background:#dc2626}
  .crm-pt .sr-bar{width:56px;margin-right:3px}
  .sr-rank{display:flex;align-items:center;gap:10px;margin:7px 0;font-size:13px}
  .sr-rank>span:first-child{flex:0 0 150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .sr-rank .sr-bar{flex:1;width:auto;height:9px}
  .sr-rank b{min-width:56px;text-align:right}
  .sr-chips{display:flex;flex-wrap:wrap;gap:6px 14px;margin-bottom:10px}
  .sr-chip{display:inline-flex;align-items:center;gap:5px;font-size:12px;white-space:nowrap}
  .sr-chip i{width:9px;height:9px;border-radius:3px;display:inline-block}
  .sr-chart{display:flex;align-items:flex-end;gap:3px;height:170px;padding-top:6px;border-bottom:1px solid var(--line);overflow-x:auto}
  .sr-col{flex:1;min-width:12px;display:flex;flex-direction:column;align-items:center;height:100%}
  .sr-stack{height:calc(100% - 15px);width:100%;max-width:26px;display:flex;flex-direction:column-reverse}
  .sr-stack i{display:block;width:100%;flex:none}
  .sr-col span{font-size:10px;color:var(--muted);margin-top:3px;height:12px;line-height:12px}
  .sr-col.sun span{color:#dc2626}
  .sr-funnel{display:flex;flex-direction:column;gap:7px}
  .sr-fun{display:flex;align-items:center;gap:10px;font-size:13px}
  .sr-fun-l{flex:0 0 110px}
  .sr-fun-b{flex:1;position:relative;height:26px;background:#f1f2f7;border-radius:7px;overflow:hidden}
  .sr-fun-b i{position:absolute;left:0;top:0;bottom:0;background:var(--brand);opacity:.22}
  .sr-fun-b b{position:relative;padding-left:9px;line-height:26px}
  .sr-fun-p{flex:0 0 230px;font-size:12.5px}
  .sr-2{display:grid;grid-template-columns:1fr 1fr;gap:0 12px}
  .sr-tag{font-size:10.5px;padding:1px 6px;border-radius:6px;background:#eef0f5}
  .sr-tag.bad{background:#fee2e2;color:#b91c1c}
  tr.sr-late td{background:#fff8f8}
  @media (max-width:760px){.sr-2{grid-template-columns:1fr}.sr-fun-p{flex:0 0 auto}.sr-fun-l{flex-basis:80px}.sr-rank>span:first-child{flex-basis:100px}}
'''
PANEL = '''    <!-- LAPORAN SALES (v1.2.221: laporan-sales) -->
    <section class="panel" id="panel-salesrep">
      <div class="ph"><h2>Laporan Sales</h2><p>Performa vs target, aktivitas, produktivitas, forecast, funnel &amp; win/loss, dan umur lead &mdash; dari data Leads &amp; aktivitas sales.</p></div>
      <div id="srRoot"></div>
    </section>

'''
s = open(HT, encoding='utf-8').read()
if TAG in s: print('SUDAH', HT)
else:
    assert NEED in s, 'v1.2.220 belum terpasang di ' + HT
    s = rep(s, "  .crm-perf-bar input[type=date]{width:auto;padding:6px 8px}\n", "  .crm-perf-bar input[type=date]{width:auto;padding:6px 8px}\n" + CSS, what='css')
    s = rep(s, '<button data-tab="tasks"    data-role="super_admin,admin,supervisor,wa_agent,sales" data-icon="list-todo"><span class="ic"></span> Task</button><!-- v1.2.214: task -->',
            '<button data-tab="tasks"    data-role="super_admin,admin,supervisor,wa_agent,sales" data-icon="list-todo"><span class="ic"></span> Task</button><!-- v1.2.214: task -->\n'
            '      <button data-tab="salesrep" data-role="super_admin,admin,supervisor,sales" data-icon="trending-up"><span class="ic"></span> Laporan Sales</button><!-- ' + TAG + ' -->', what='nav')
    s = rep(s, '    <!-- KONTAK (v1.2.39) -->', PANEL + '    <!-- KONTAK (v1.2.39) -->', what='panel')
    s = rep(s, '<script src="app.js?v=1.2.220"></script>', '<script src="app.js?v=1.2.221"></script><!-- ' + TAG + ' -->', what='cache')
    save(HT, s)
print('selesai')
