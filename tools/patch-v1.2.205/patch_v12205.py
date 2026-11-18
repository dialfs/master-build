#!/usr/bin/env python3
"""v1.2.205 (laporan-pindah): kartu Laporan per Agent & Laporan per Sales pindah dari Tim & Agent
ke menu Laporan & Log (sub-tab Per Agent / Per Sales). Hanya tampilan (app.js + index.html).
Butuh v1.2.204. Idempoten.  Pakai: patch_v12205.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil, re
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.205: laporan-pindah'; NEED = 'v1.2.204: jam-ai'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12205-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ============================== API (versi saja) ==============================
s = rd(API)
assert NEED in s, 'v1.2.204 belum terpasang'
if TAG not in s:
    s = rep(s, "define('DEI_VERSION', 'v1.2.204');   // v1.2.204:",
            "define('DEI_VERSION', 'v1.2.205');   // " + TAG + " — Laporan per Agent & per Sales pindah ke menu Laporan & Log; v1.2.204:", what='DEI_VERSION')
    save(API, s)
else: print('sudah', API)

# ============================== HTML ==============================
s = rd(HT)
if TAG not in s:
    s = rep(s, '<script src="app.js?v=1.2.204"></script><!-- v1.2.204: jam-ai -->',
            '<script src="app.js?v=1.2.205"></script><!-- ' + TAG + ' --><!-- v1.2.204: jam-ai -->', what='app.js?v')
    # potong kedua kartu laporan dari panel Tim
    a = s.index('      <div class="card" data-role-card="super_admin,admin,supervisor" id="slrCard"><h3>Laporan per Sales</h3>')
    b0 = s.index('      <div class="card"><h3>Laporan per Agent</h3>', a)
    b1 = s.index('    </section>', b0)
    sales_card = s[a:b0].rstrip() + '\n'
    agent_card = s[b0:b1].rstrip() + '\n'
    assert agent_card.count('<div') == agent_card.count('</div>'), 'kartu agent tidak seimbang'
    assert sales_card.count('<div') == sales_card.count('</div>'), 'kartu sales tidak seimbang'
    s = s[:a] + s[b1:]
    agent_card = agent_card.replace('<div class="card"><h3>Laporan per Agent</h3>', '<div class="card" id="arCard"><h3>Laporan per Agent</h3>', 1)
    blok = ('      <!-- ' + TAG + ' -->\n      <div id="repAgent" style="display:none">\n' + agent_card + '      </div>\n'
            '      <div id="repSales" style="display:none">\n'
            '        <div class="card" id="slrLocked" style="display:none;background:#fef2f2;border:1px solid #fecaca;color:#b91c1c;font-size:13px"></div>\n'
            + sales_card + '      </div>\n\n')
    s = rep(s, '      <!-- v1.2.66: LOG PERCAKAPAN terstruktur -->', blok + '      <!-- v1.2.66: LOG PERCAKAPAN terstruktur -->', what='repLogs')
    s = rep(s, '<button type="button" data-v="service"><span data-ico="headphones"></span> Kinerja Layanan</button><!-- v1.2.101: percakapan -->',
            '<button type="button" data-v="service"><span data-ico="headphones"></span> Kinerja Layanan</button><!-- v1.2.101: percakapan -->\n'
            '        <button type="button" data-v="agent"><span data-ico="users"></span> Per Agent</button>\n'
            '        <button type="button" data-v="sales"><span data-ico="briefcase"></span> Per Sales</button><!-- ' + TAG + ' -->', what='seg')
    s = rep(s, '<div class="ph"><h2>Tim &amp; Agent</h2><p>Mode balasan WhatsApp, pengaturan tim, dan laporan kinerja per agent.</p></div>',
            '<div class="ph"><h2>Tim &amp; Agent</h2><p>Mode balasan WhatsApp, routing, kursi tim, dan daftar Sales. Laporan per Agent &amp; per Sales ada di menu Laporan &amp; Log.</p></div>', what='ph tim')
    s = rep(s, '<div class="ph"><h2>Laporan &amp; Log</h2><p>Statistik percakapan, sumber traffic (UTM), dan ekspor data.</p></div>',
            '<div class="ph"><h2>Laporan &amp; Log</h2><p>Statistik percakapan, sumber traffic (UTM), laporan per agent &amp; sales, dan ekspor data.</p></div>', what='ph rep')
    save(HT, s)
else: print('sudah', HT)

# ============================== JS ==============================
s = rd(JS)
if TAG not in s:
    s = rep(s, "    if (['summary', 'logs', 'topics', 'service'].indexOf(v) === -1) v = 'summary';   // v1.2.101: + service\n",
            "    if (['summary', 'logs', 'topics', 'service', 'agent', 'sales'].indexOf(v) === -1) v = 'summary';   // v1.2.101: + service; " + TAG + "\n", what='repView list')
    s = rep(s, "    $('#repService').style.display = v === 'service' ? '' : 'none';   // v1.2.101\n",
            "    $('#repService').style.display = v === 'service' ? '' : 'none';   // v1.2.101\n"
            "    $('#repAgent').style.display = v === 'agent' ? '' : 'none';   // " + TAG + "\n"
            "    $('#repSales').style.display = v === 'sales' ? '' : 'none';\n", what='repView show')
    s = rep(s, "    if (v === 'service') svInit();   // v1.2.101: percakapan\n",
            "    if (v === 'service') svInit();   // v1.2.101: percakapan\n"
            "    if (v === 'agent') arInit205();   // " + TAG + "\n"
            "    if (v === 'sales') slRepInit205();\n", what='repView init')
    s = rep(s, "    if (!$('#arFrom').value) $('#arFrom').value = ymd(new Date(today.getFullYear(), today.getMonth(), 1));\n"
               "    if (!$('#arTo').value) $('#arTo').value = ymd(today);\n"
               "    $('#btnArLoad').onclick = loadAgentReport;\n", '', what='loadTim ar')
    s = rep(s, "    loadAgentReport();\n    slTimLoad203();   // v1.2.203: sales-tag\n  }\n  function timModeNote() {",
            "    slTimLoad203();   // v1.2.203: sales-tag\n  }\n"
            "  // " + TAG + " — Laporan per Agent & per Sales di menu Laporan & Log\n"
            "  function arInit205() {\n"
            "    var pad = function (n) { return String(n).padStart(2, '0'); };\n"
            "    var ymd = function (d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); };\n"
            "    var t = new Date();\n"
            "    if (!$('#arFrom').value) $('#arFrom').value = ymd(new Date(t.getFullYear(), t.getMonth(), 1));\n"
            "    if (!$('#arTo').value) $('#arTo').value = ymd(t);\n"
            "    $('#btnArLoad').onclick = loadAgentReport;\n"
            "    loadAgentReport();\n"
            "  }\n"
            "  function slRepInit205() {\n"
            "    if (!$('#slrFrom').value) { var d = new Date(); $('#slrFrom').value = slYmd203(new Date(d.getFullYear(), d.getMonth(), 1)); $('#slrTo').value = slYmd203(d); }\n"
            "    $('#btnSlrLoad').onclick = slReport203;\n"
            "    $('#btnSlrCsv').onclick = slReportCsv203;\n"
            "    slList203(true);\n"
            "  }\n"
            "  function timModeNote() {", what='loadTim end')
    s = rep(s, "    $('#btnSlAdd').onclick = function () { slSave203({ name: $('#slName').value, phone: $('#slPhone').value }, function () { $('#slName').value = ''; $('#slPhone').value = ''; }); };\n    slList203(true);\n",
            "    $('#btnSlAdd').onclick = function () { slSave203({ name: $('#slName').value, phone: $('#slPhone').value }, function () { $('#slName').value = ''; $('#slPhone').value = ''; }); };\n    slList203(false);   // " + TAG + ": laporan pindah ke Laporan & Log\n", what='slTim')
    s = rep(s, "      $('#slrCard').style.display = lk ? 'none' : '';\n",
            "      $('#slrCard').style.display = lk ? 'none' : '';\n"
            "      if ($('#slrLocked')) { $('#slrLocked').style.display = lk ? '' : 'none'; $('#slrLocked').innerHTML = lk ? ico('octagon-alert', 13) + ' ' + esc(r.locked_msg || '') : ''; }   // " + TAG + "\n", what='locked')
    # panduan & bantuan
    s = rep(s, "    agentReport: function (title, body) { return { tab: 'tim', el: tourCard('tim', 'Laporan per Agent'), title: title, body: body }; },",
            "    agentReport: function (title, body) { return { tab: 'reports', pre: function () { repView('agent'); }, el: '#arCard', title: title, body: body }; },   // " + TAG, what='TS')
    s = rep(s, "      TS.agentReport('Kinerja Anda', '<p>Jumlah chat yang Anda tangani dan rata-rata <b>waktu respon</b>. Waktu dihitung sejak pelanggan menunggu sampai Anda membalas — balas secepatnya.</p>'),\n", '', what='tour agent')
    s = rep(s, "    { id: 'kinerja', roles: R_ALL, t: 'Melihat kinerja agent & waktu respon',", "    { id: 'kinerja', roles: R_SPV, t: 'Melihat kinerja agent & waktu respon',", what='help roles')
    s = rep(s, "      s: ['Buka menu <b>Tim &amp; Agent</b>.', 'Di <b>Laporan per Agent</b>, pilih tanggal lalu <b>Tampilkan</b>.'],\n"
               "      show: [{ tab: 'tim', el: tourCard('tim', 'Laporan per Agent'), title: 'Laporan per Agent', body: '<p>Chat ditangani, balasan, respon pertama, dan belum dibalas per agent.</p>' }] },\n",
            "      s: ['Buka menu <b>Laporan &amp; Log</b>, tab <b>Per Agent</b>.', 'Pilih tanggal lalu <b>Tampilkan</b>.'],\n"
            "      show: [{ tab: 'reports', pre: hClick('#repSeg [data-v=\"agent\"]'), el: '#arCard', title: 'Laporan per Agent', body: '<p>Chat ditangani, balasan, respon pertama, dan belum dibalas per agent.</p>' }] },\n"
            "    { id: 'laporansales', roles: R_SPV, t: 'Melihat laporan per Sales (chat, PO, Close Deal)', k: 'laporan sales penjualan po close deal lose konversi csv per sales',   // " + TAG + "\n"
            "      s: ['Buka menu <b>Laporan &amp; Log</b>, tab <b>Per Sales</b>.', 'Pilih tanggal lalu <b>Tampilkan</b>, atau <b>Unduh CSV</b>.'],\n"
            "      show: [{ tab: 'reports', pre: hClick('#repSeg [data-v=\"sales\"]'), el: '#slrCard', title: 'Laporan per Sales', body: '<p>Chat di-tag, PO, Close Deal, Close Lose, dan konversi per sales.</p>' }] },\n", what='help kinerja')
    save(JS, s)
else: print('sudah', JS)
print('patch v1.2.205 selesai')
