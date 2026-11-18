#!/usr/bin/env python3
"""v1.2.206 (sales-lead): chat yang di-tag ke Sales otomatis jadi lead baru (status Baru, sales tercatat).
Lead dari tag/PO yang belum pernah dianalisa tetap ikut analisa AI otomatis saat ambang pesan tercapai.
Butuh v1.2.205. Idempoten.  Pakai: patch_v12206.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.206: sales-lead'; NEED = 'v1.2.205: laporan-pindah'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12206-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

s = rd(API)
if TAG not in s:
    assert NEED in s, 'butuh v1.2.205 dulu'
    s = rep(s, "define('DEI_VERSION', 'v1.2.205');   // v1.2.205:",
            "define('DEI_VERSION', 'v1.2.206');   // " + TAG + " — chat di-tag Sales otomatis jadi lead baru; v1.2.205:", what='DEI_VERSION')
    s = rep(s, "function slThreadInfo($num) {",
            "// " + TAG + ": buat lead Baru untuk chat yang di-tag sales bila belum punya lead. true = lead baru dibuat.\n"
            "function slLeadEnsure206($num, $sid) {\n"
            "    return (bool)deiWithLock('leads', function () use ($num, $sid) {\n"
            "        $all = leadsGetAll();\n"
            "        if (isset($all[$num]) && is_array($all[$num])) return false;\n"
            "        $now = date('Y-m-d H:i:s');\n"
            "        $all[$num] = ['number' => $num, 'name' => waContactName($num), 'status' => 'baru', 'note' => '', 'extracted' => [],\n"
            "                      'analyzed_at' => '', 'created_at' => $now, 'updated_at' => $now, 'src' => 'sales', 'sales' => (string)$sid];\n"
            "        writeJson(LEADS_FILE, $all);\n"
            "        return true;\n"
            "    });\n"
            "}\n"
            "function slThreadInfo($num) {", what='lib')
    s = rep(s, "        try { waAuditLog('sales_tag', $by, $num, ['from' => $prevId, 'to' => $sid]); } catch (\\Throwable $e) {}\n"
               "        jsonOut(['ok' => true, 'sales' => slThreadInfo($num)]);\n",
            "        try { waAuditLog('sales_tag', $by, $num, ['from' => $prevId, 'to' => $sid]); } catch (\\Throwable $e) {}\n"
            "        $slNew206 = false;   // " + TAG + "\n"
            "        if ($sid !== '' && !wgPublic($num)) { try { $slNew206 = slLeadEnsure206($num, $sid); } catch (\\Throwable $e) { error_log('sales lead: ' . $e->getMessage()); } }\n"
            "        jsonOut(['ok' => true, 'sales' => slThreadInfo($num), 'lead_created' => $slNew206]);\n", what='sales_tag')
    # lead dari tag/PO yang belum dianalisa tetap boleh dianalisa otomatis
    s = rep(s, "    if (!$force && isset($all[$number])) return false;   // sudah punya kartu -> sekali saja\n",
            "    if (!$force && isset($all[$number]) && (string)($all[$number]['analyzed_at'] ?? '') !== '') return false;   // sudah punya kartu -> sekali saja (" + TAG + ": lead dari tag/PO tanpa analisa tetap dianalisa)\n", what='analyze once')
    s = rep(s, "                'sales_name'    => $slId203 !== '' ? (string)($slMap203[$slId203]['name'] ?? '(sales dihapus)') : '',\n",
            "                'sales_name'    => $slId203 !== '' ? (string)($slMap203[$slId203]['name'] ?? '(sales dihapus)') : '',\n"
            "                'src'           => (string)($l['src'] ?? ''),   // " + TAG + "\n", what='get_leads src')
    save(API, s)
else: print('sudah', API)

s = rd(JS)
if TAG not in s:
    s = rep(s, "'Dibuat dari PO ' + esc((l.updated_at || '').slice(0, 16))",
            "(l.src === 'sales' ? 'Dibuat saat tag sales ' : 'Dibuat dari PO ') + esc((l.created_at || l.updated_at || '').slice(0, 16))", what='lead label')
    s = rep(s, "        if (r && r.ok) toast(v ? 'Sales dipilih.' : 'Tag sales dihapus.');\n",
            "        if (r && r.ok) { toast(v ? (r.lead_created ? 'Sales dipilih. Lead baru dibuat.' : 'Sales dipilih.') : 'Tag sales dihapus.'); if (r.lead_created) fetchWaConvs(); }   // " + TAG + "\n", what='toast')
    save(JS, s)
else: print('sudah', JS)

s = rd(HT)
if TAG not in s:
    s = rep(s, '<script src="app.js?v=1.2.205"></script><!-- v1.2.205: laporan-pindah -->',
            '<script src="app.js?v=1.2.206"></script><!-- ' + TAG + ' --><!-- v1.2.205: laporan-pindah -->', what='app.js?v')
    save(HT, s)
else: print('sudah', HT)
print('patch v1.2.206 selesai')
