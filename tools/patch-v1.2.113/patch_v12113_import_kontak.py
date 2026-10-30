#!/usr/bin/env python3
"""v1.2.113 import-kontak: impor kontak dari XLS/XLSX/CSV ke menu Kontak (Lead Rating per status).
Pakai: python3 patch_v12113_import_kontak.py [~/Herd/dei-tenant]
Idempoten: backup -> str.replace anchor -> versi. Lint (php -l) dijalankan terpisah."""
import os, sys, time, shutil

ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.113: import-kontak'
STAMP = time.strftime('%Y%m%d-%H%M%S')
HERE = os.path.dirname(os.path.abspath(__file__))
part = lambda n: open(os.path.join(HERE, n), encoding='utf-8').read()

def patch(rel, edits, backup=True):
    p = os.path.join(ROOT, rel)
    s = open(p, encoding='utf-8').read()
    if TAG in s:
        print('sudah dipatch:', rel); return
    if backup: shutil.copy2(p, p + '.bak-v12113-' + STAMP)
    for old, new in edits:
        n = s.count(old)
        assert n == 1, '%s: anchor ditemukan %dx: %r' % (rel, n, old[:80])
        s = s.replace(old, new)
    assert TAG in s, rel + ': TAG tidak masuk'
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

API = [
    ("define('DEI_VERSION', 'v1.2.112');   // v1.2.112: login-log",
     "define('DEI_VERSION', 'v1.2.113');   // v1.2.113: import-kontak"),
    ("function waSetContactInfo($number, $custName, $custDob) {",
     part('ic_funcs.php') + "function waSetContactInfo($number, $custName, $custDob) {"),
    # riwayat WAHA: kontak hasil impor (last_seen kosong) ikut dapat waktu chat terakhir
    ("                            if ($isNew) $ct['last_seen'] = $lastTs;\n",
     "                            if ($isNew || (string)($ct['last_seen'] ?? '') === '') $ct['last_seen'] = $lastTs;   // v1.2.113\n"),
    ("                'cust_dob'    => (string)($c['cust_dob'] ?? ''),    // v1.2.39 fase4\n",
     "                'cust_dob'    => (string)($c['cust_dob'] ?? ''),    // v1.2.39 fase4\n"
     "                'imp'         => (isset($c['imp']) && is_array($c['imp'])) ? $c['imp'] : null,   // v1.2.113\n"),
    ("    case 'save_contact': {",
     part('ic_cases.php') + "    case 'save_contact': {"),
]

HTML = [
    ("          <button class=\"btn ghost sm\" id=\"btnExportKontakCsv\" style=\"margin-left:auto\"",
     "          <button class=\"btn ghost sm\" id=\"btnImportKontak\" style=\"margin-left:auto\" title=\"Impor kontak dari file Excel (.xls/.xlsx) atau CSV\">&#11014; Impor Kontak</button><!-- v1.2.113: import-kontak -->\n"
     "          <input type=\"file\" id=\"kontakImportFile\" accept=\".xls,.xlsx,.csv,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\" style=\"display:none\">\n"
     "          <button class=\"btn ghost sm\" id=\"btnExportKontakCsv\""),
    ("        </div>\n      </div>\n      <div id=\"contactList\"></div>",
     "        </div>\n      </div>\n      <div class=\"card\" id=\"kontakImportCard\" style=\"display:none\"></div>\n      <div id=\"contactList\"></div>"),
    ('<script src="app.js?v=1.2.110"></script><!-- v1.2.110: customer-feedback -->',
     '<script src="app.js?v=1.2.113"></script><!-- v1.2.113: import-kontak -->'),
]

JS = [
    ("  function fetchContacts() {\n",
     part('ic_app.js') + "  function fetchContacts() {\n"),
    ("      _bCsv.onclick = exportContactsCsv;\n    }\n",
     "      _bCsv.onclick = exportContactsCsv;\n    }\n"
     "    // v1.2.113: import-kontak (Super Admin & Admin)\n"
     "    var _bImp = $('#btnImportKontak'), _fImp = $('#kontakImportFile');\n"
     "    if (_bImp && _fImp) {\n"
     "      if (!user || (user.role !== 'super_admin' && user.role !== 'admin')) _bImp.style.display = 'none';\n"
     "      _bImp.onclick = function () { _fImp.value = ''; _fImp.click(); };\n"
     "      _fImp.onchange = function () { contactImpStart(_fImp.files && _fImp.files[0]); };\n"
     "    }\n"),
    ("'<div style=\"color:var(--muted);font-size:12px\">Terakhir aktif ' + esc((c.last_seen || '').slice(0, 16)) + '</div>' +",
     "'<div style=\"color:var(--muted);font-size:12px\">' + (c.last_seen ? 'Terakhir aktif ' + esc(c.last_seen.slice(0, 16)) : 'Belum pernah chat') +\n"
     "                (c.imp ? ' · <span title=\"' + esc('Diimpor ' + (c.imp.at || '') + (c.imp.src ? ' dari ' + c.imp.src : '')) + '\">diimpor</span>' : '') + '</div>' +   // v1.2.113"),
    ("          leadField('Terakhir aktif', (c.last_seen || '').slice(0, 16)) +\n        '</div>' +\n",
     "          leadField('Terakhir aktif', (c.last_seen || '').slice(0, 16)) +\n        '</div>' +\n"
     "        (c.imp ? '<div class=\"grid2\" style=\"margin-top:8px\">' + leadField('Diimpor', (c.imp.at || '').slice(0, 16) + (c.imp.src ? ' · ' + c.imp.src : '')) +\n"
     "          leadField('Status di file', (c.imp.st || '-') + (c.imp.n > 1 ? ' (' + c.imp.n + ' baris)' : '')) + '</div>' : '') +   // v1.2.113\n"),
]

patch('api/index.php', API)
patch('dashboard/chatbot-ai/index.html', HTML)
patch('dashboard/chatbot-ai/app.js', JS)
print('selesai', TAG)
