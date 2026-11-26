#!/usr/bin/env python3
"""v1.2.223 (laporan-pdf): Laporan Berkala PDF — mingguan & bulanan, dikirim otomatis ke email (lampiran PDF) & WhatsApp (dokumen PDF).
- Laporan & Log > tab "Laporan Berkala" (Super Admin/Admin): jadwal mingguan (hari & jam) dan bulanan (tanggal & jam), bagian laporan per jadwal
  (Chat & Sumber Lead, Kinerja Layanan, per Agent, Performa Sales & Target, Pipeline & Forecast, Task, Topik, Penggunaan), penerima
  (Admin, Supervisor, Sales = laporan miliknya, email/WA tambahan), saluran (email / WhatsApp / keduanya), buat & unduh PDF sekarang,
  kirim uji, arsip 120 hari, status mesin PDF.
- Mesin PDF: dompdf 3.1.4 (PHP murni, cPanel & VPS) dipasang otomatis sekali dari pusat (/lib/dompdf-3.1.4-dei.zip, sha256 terkunci) ke lib/;
  Chromium/Chrome headless dipakai otomatis bila ada di server (VPS), gagal -> dompdf.
- API: rpt_get, rpt_save, rpt_make, rpt_file, rpt_dl (tautan bertanda tangan 30 hari), rpt_test, rpt_lib. cron_tick: rpSweep223.
Butuh v1.2.222. Idempoten. Pakai: patch_v12223.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil, hashlib
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H + '/dei-tenant'
TD = os.path.dirname(os.path.abspath(__file__))
TAG = 'v1.2.223: laporan-pdf'; NEED = 'v1.2.222: notif-wa'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12223-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
rd = lambda f: open(os.path.join(TD, 'src', f), encoding='utf-8').read()
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'
C = '   // ' + TAG
LIBZIP = os.path.join(TD, 'lib', 'dompdf-3.1.4-dei.zip')
SHA = hashlib.sha256(open(LIBZIP, 'rb').read()).hexdigest()

# ======================= api =======================
s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API)
else:
    assert NEED in s, 'v1.2.222 belum terpasang di ' + API
    s = rep(s, "define('DEI_VERSION', 'v1.2.222');   // v1.2.222:",
            "define('DEI_VERSION', 'v1.2.223');   // " + TAG + " — Laporan Berkala PDF mingguan & bulanan, kirim otomatis ke email (lampiran) & WhatsApp (dokumen); dompdf/Chromium; v1.2.222:", what='ver')
    s = rep(s, "\nfunction deiGuardAgentPrivate($u, $num) {", "\n" + rd('lib223.php').replace('__RP_LIB_SHA256__', SHA) + "function deiGuardAgentPrivate($u, $num) {", what='lib')
    s = rep(s, "    case 'crm_weekly_get': {", rd('cases223.php') + "    case 'crm_weekly_get': {", what='cases')
    s = rep(s, "        try { $cwr = crmWeeklySweep217($s); if ($cwr) $r['crm_weekly'] = $cwr; } catch (\\Throwable $e) { $r['err_crm_weekly'] = $e->getMessage(); }   // v1.2.217: laporan-crm\n",
            "        try { $cwr = crmWeeklySweep217($s); if ($cwr) $r['crm_weekly'] = $cwr; } catch (\\Throwable $e) { $r['err_crm_weekly'] = $e->getMessage(); }   // v1.2.217: laporan-crm\n"
            "        try { $rpr = rpSweep223($s); if ($rpr) $r['report_pdf'] = $rpr; } catch (\\Throwable $e) { $r['err_report_pdf'] = $e->getMessage(); }" + C + "\n", what='cron')
    save(API, s)

# ======================= app.js =======================
s = open(JS, encoding='utf-8').read()
if TAG in s: print('SUDAH', JS)
else:
    s = rep(s, "    if (['summary', 'logs', 'topics', 'service', 'agent', 'sales'].indexOf(v) === -1) v = 'summary';",
            "    if (['summary', 'logs', 'topics', 'service', 'agent', 'sales', 'periodic'].indexOf(v) === -1) v = 'summary';" + C, what='repView-list')
    s = rep(s, "    $('#repSales').style.display = v === 'sales' ? '' : 'none';\n",
            "    $('#repSales').style.display = v === 'sales' ? '' : 'none';\n    if ($('#repPeriodic')) $('#repPeriodic').style.display = v === 'periodic' ? '' : 'none';" + C + "\n", what='repView-show')
    s = rep(s, "    if (v === 'sales') slRepInit205();\n  }\n", "    if (v === 'sales') slRepInit205();\n    if (v === 'periodic') rpInit223();" + C + "\n  }\n", what='repView-init')
    s = rep(s, "  /* v1.2.221: laporan-sales */\n", rd('js223.js') + "  /* v1.2.221: laporan-sales */\n", what='js')
    save(JS, s)

# ======================= index.html =======================
s = open(HT, encoding='utf-8').read()
if TAG in s: print('SUDAH', HT)
else:
    s = rep(s, '        <button type="button" data-v="sales"><span data-ico="briefcase"></span> Per Sales</button><!-- v1.2.205: laporan-pindah -->\n',
            '        <button type="button" data-v="sales"><span data-ico="briefcase"></span> Per Sales</button><!-- v1.2.205: laporan-pindah -->\n'
            '        <button type="button" data-v="periodic" data-role-card="super_admin,admin"><span data-ico="file-text"></span> Laporan Berkala</button><!-- ' + TAG + ' -->\n', what='seg')
    s = rep(s, '      <div id="repSales" style="display:none">\n',
            '      <div id="repPeriodic" style="display:none"><!-- ' + TAG + ' --><div class="card" id="rpCard"><div class="help">Memuat…</div></div></div>\n'
            '      <div id="repSales" style="display:none">\n', what='div')
    s = rep(s, 'app.js?v=1.2.222', 'app.js?v=1.2.223', what='cachebust')
    save(HT, s)

# ======================= pusat: mail_relay =======================
P = H + '/dei-pusat'; PB = P + '/backend/index.php'
s = open(PB, encoding='utf-8').read()
if TAG in s: print('SUDAH', PB)
else:
    # perbaiki bug v1.2.215: jsonOut ikut jadi komentar -> $to tidak terisi untuk jenis yang sah (semua email relay gagal 400)
    s = rep(s, "        if (!in_array($kind, ['pw_reset', 'pw_changed', 'crm_remind', 'crm_weekly'], true))   // v1.2.215: crm-aktivitas jsonOut(['ok' => false, 'error' => 'Jenis email tidak diizinkan.'], 400);\n",
            "        if (!in_array($kind, ['pw_reset', 'pw_changed', 'crm_remind', 'crm_weekly', 'report_pdf'], true)) jsonOut(['ok' => false, 'error' => 'Jenis email tidak diizinkan.'], 400);   // v1.2.215: crm-aktivitas;" + C + " (+report_pdf, perbaiki baris jsonOut yang ikut jadi komentar)\n", what='pusat-kind')
    s = rep(s, "        $from = 'noreply@deintegra.com';\n        $b = 'dei-' . bin2hex(random_bytes(8));\n",
            "        $from = 'noreply@deintegra.com';\n"
            "        $att = null;" + C + " — lampiran PDF (maks. 3 MB) hanya untuk report_pdf\n"
            "        if ($kind === 'report_pdf' && is_array($body['attach'] ?? null)) {\n"
            "            $ad = base64_decode((string)($body['attach']['b64'] ?? ''), true);\n"
            "            $an = preg_replace('/[^A-Za-z0-9._-]/', '-', mb_substr((string)($body['attach']['name'] ?? 'laporan.pdf'), 0, 120));\n"
            "            if ($ad === false || strlen($ad) > 3 * 1024 * 1024 || strncmp($ad, '%PDF', 4) !== 0) jsonOut(['ok' => false, 'error' => 'Lampiran PDF tidak valid atau lebih dari 3 MB.'], 400);\n"
            "            if (substr(strtolower($an), -4) !== '.pdf') $an .= '.pdf';\n"
            "            $att = ['name' => $an, 'data' => $ad];\n"
            "        }\n"
            "        $b = 'dei-' . bin2hex(random_bytes(8));\n", what='pusat-att')
    s = rep(s, "        $subj = '=?UTF-8?B?' . base64_encode($subject) . '?=';\n        $ok = false; $via = '';\n",
            "        if ($att) {" + C + "\n"
            "            $bm = 'deim-' . bin2hex(random_bytes(8));\n"
            "            $hdr = str_replace('Content-Type: multipart/alternative; boundary=\"' . $b . '\"', 'Content-Type: multipart/mixed; boundary=\"' . $bm . '\"', $hdr);\n"
            "            $mb = \"--$bm\\r\\nContent-Type: multipart/alternative; boundary=\\\"$b\\\"\\r\\n\\r\\n\" . $mb\n"
            "                . \"--$bm\\r\\nContent-Type: application/pdf; name=\\\"\" . $att['name'] . \"\\\"\\r\\nContent-Transfer-Encoding: base64\\r\\nContent-Disposition: attachment; filename=\\\"\" . $att['name'] . \"\\\"\\r\\n\\r\\n\" . chunk_split(base64_encode($att['data'])) . \"--$bm--\\r\\n\";\n"
            "        }\n"
            "        $subj = '=?UTF-8?B?' . base64_encode($subject) . '?=';\n        $ok = false; $via = '';\n", what='pusat-mime')
    s = rep(s, "        jsonOut(['ok' => true, 'sent' => (bool)$ok]);\n    }\n\n    /* ========================================================\n     * v1.2.185: master-grup",
            "        jsonOut(['ok' => true, 'sent' => (bool)$ok, 'attached' => (bool)$att]);" + C + "\n    }\n\n    /* ========================================================\n     * v1.2.185: master-grup", what='pusat-out')
    save(PB, s)
# mesin PDF untuk diunduh tenant: <pusat>/lib/dompdf-3.1.4-dei.zip
os.makedirs(P + '/lib', exist_ok=True)
dst = P + '/lib/dompdf-3.1.4-dei.zip'
if not os.path.exists(dst) or hashlib.sha256(open(dst, 'rb').read()).hexdigest() != SHA: shutil.copy2(LIBZIP, dst); print('OK', dst)
else: print('SUDAH', dst)
open(P + '/lib/README.txt', 'w').write('dompdf 3.1.4 (LGPL-2.1) dikemas ulang untuk DEI Chatbot (v1.2.223: laporan-pdf).\nTenant mengunduh berkas ini sekali (sha256 dicek di api/index.php: RP_LIB_SHA256).\nsha256 ' + SHA + '\n')
DS = P + '/dev/deploy.sh'
d = open(DS, encoding='utf-8').read()
if 'admin backend master releases daftar grup mitra lib' not in d:
    d = rep(d, 'find admin backend master releases daftar grup mitra -type d', 'find admin backend master releases daftar grup mitra lib -type d', what='deploy-d')
    d = rep(d, 'find admin backend master releases daftar grup mitra -type f', 'find admin backend master releases daftar grup mitra lib -type f', what='deploy-f')
    open(DS, 'w', encoding='utf-8').write(d); print('OK', DS)
print('selesai')
