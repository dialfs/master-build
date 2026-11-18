#!/usr/bin/env python3
"""v1.2.208 (sales-untag): aturan lepas/ganti tag Sales terhadap lead.
- Lepas tag & lead masih Baru: lead yang dibuat dari tag sales (src=sales) ikut dihapus; lead lain hanya kehilangan nama sales.
- Lead sudah naik dari Baru: tag tidak bisa dikosongkan (API 409, pilihan kosong dinonaktifkan) — hanya bisa ganti sales.
- Ganti sales: lead.sales ikut diganti (termasuk lead Close).
- Menu Leads dimuat ulang setelah tag/Close Deal (dulu tetap menampilkan data lama).
Butuh v1.2.207. Idempoten.  Pakai: patch_v12208.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.208: sales-untag'; NEED = 'v1.2.207: hapus-lead'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12208-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

LIB = r'''// v1.2.208: sales-untag — sesuaikan lead setelah tag sales diganti / dilepas. true = lead dihapus.
function slLeadStLabel208($st) {
    $m = ['baru' => 'Baru', 'qualified' => 'Qualified', 'follow_up' => 'Follow-up', 'closed_deal' => 'Close Deal', 'closed_lost' => 'Close Lose', 'closed' => 'Closed'];
    return $m[$st] ?? $st;
}
function slLeadAfterTag208($num, $sid) {
    return (bool)deiWithLock('leads', function () use ($num, $sid) {
        $all = leadsGetAll();
        if (!isset($all[$num]) || !is_array($all[$num])) return false;
        $l = $all[$num];
        if ($sid !== '') {
            if ((string)($l['sales'] ?? '') === $sid) return false;
            $all[$num]['sales'] = $sid;
            writeJson(LEADS_FILE, $all);
            return false;
        }
        if ((string)($l['status'] ?? 'baru') === 'baru' && (string)($l['src'] ?? '') === 'sales') {
            unset($all[$num]);
            writeJson(LEADS_FILE, $all);
            return true;
        }
        if (!array_key_exists('sales', $l)) return false;
        unset($all[$num]['sales']);
        writeJson(LEADS_FILE, $all);
        return false;
    });
}
'''

s = rd(API)
if TAG not in s:
    assert NEED in s, 'butuh v1.2.207 dulu'
    s = rep(s, "define('DEI_VERSION', 'v1.2.207');   // v1.2.207:",
            "define('DEI_VERSION', 'v1.2.208');   // " + TAG + " — lepas tag Sales: lead Baru dari tag ikut hilang, lead yang sudah naik status wajib ganti sales; v1.2.207:", what='DEI_VERSION')
    s = rep(s, "function slThreadInfo($num) {", LIB + "function slThreadInfo($num) {", what='lib')
    s = rep(s, "        if ($prevId === $sid) jsonOut(['ok' => true, 'sales' => slThreadInfo($num)]);\n",
            "        if ($prevId === $sid) jsonOut(['ok' => true, 'sales' => slThreadInfo($num)]);\n"
            "        if ($sid === '') {   // " + TAG + ": lead yang sudah naik dari Baru wajib tetap punya sales\n"
            "            $slSt208 = slLeadStatus($num);\n"
            "            if ($slSt208 !== '' && $slSt208 !== 'baru') jsonOut(['ok' => false, 'error' => 'Lead chat ini sudah berstatus ' . slLeadStLabel208($slSt208) . ', jadi tag sales tidak bisa dikosongkan. Pilih sales lain.'], 409);\n"
            "        }\n", what='guard')
    s = rep(s, "        $slNew206 = false;   // v1.2.206: sales-lead\n"
               "        if ($sid !== '' && !wgPublic($num)) { try { $slNew206 = slLeadEnsure206($num, $sid); } catch (\\Throwable $e) { error_log('sales lead: ' . $e->getMessage()); } }\n"
               "        jsonOut(['ok' => true, 'sales' => slThreadInfo($num), 'lead_created' => $slNew206]);\n",
            "        $slNew206 = false;   // v1.2.206: sales-lead\n"
            "        if ($sid !== '' && !wgPublic($num)) { try { $slNew206 = slLeadEnsure206($num, $sid); } catch (\\Throwable $e) { error_log('sales lead: ' . $e->getMessage()); } }\n"
            "        $slDel208 = false;   // " + TAG + "\n"
            "        try { $slDel208 = slLeadAfterTag208($num, $sid); } catch (\\Throwable $e) { error_log('sales untag: ' . $e->getMessage()); }\n"
            "        jsonOut(['ok' => true, 'sales' => slThreadInfo($num), 'lead_created' => $slNew206, 'lead_removed' => $slDel208]);\n", what='sales_tag out')
    save(API, s)
else: print('sudah', API)

s = rd(JS)
if TAG not in s:
    s = rep(s, "    var opts = '<option value=\"\">' + (list.length ? 'Sales: —' : 'Sales: belum ada (atur di Tim & Agent)') + '</option>' + list.map(function (o) {\n",
            "    var lock208 = !!(S.cur && S.lead && S.lead !== 'baru');   // " + TAG + ": lead sudah naik status -> hanya bisa ganti sales\n"
            "    var opts = '<option value=\"\"' + (lock208 ? ' disabled' : '') + '>' + (lock208 ? 'Sales: — (lead sudah ' + esc((LEAD_STATUS[S.lead] || {}).label || S.lead) + ', pilih sales lain)' : (list.length ? 'Sales: —' : 'Sales: belum ada (atur di Tim & Agent)')) + '</option>' + list.map(function (o) {\n", what='opts')
    s = rep(s, "        if (r && r.ok) { toast(v ? (r.lead_created ? 'Sales dipilih. Lead baru dibuat.' : 'Sales dipilih.') : 'Tag sales dihapus.'); if (r.lead_created) fetchWaConvs(); }   // v1.2.206: sales-lead\n",
            "        if (r && r.ok) { toast(v ? (r.lead_created ? 'Sales dipilih. Lead baru dibuat.' : 'Sales dipilih.') : (r.lead_removed ? 'Tag sales dihapus. Lead berstatus Baru ikut dihapus.' : 'Tag sales dihapus.')); loaded.leads = false; if (r.lead_created || r.lead_removed) fetchWaConvs(); }   // v1.2.206: sales-lead; " + TAG + "\n", what='toast')
    s = rep(s, "if (x && x.ok) { toast('Lead ditandai Close Deal.'); draw(); refresh(); fetchWaConvs(); }",
            "if (x && x.ok) { toast('Lead ditandai Close Deal.'); loaded.leads = false; draw(); refresh(); fetchWaConvs(); }", what='deal reload')
    save(JS, s)
else: print('sudah', JS)

s = rd(HT)
if TAG not in s:
    s = rep(s, '<script src="app.js?v=1.2.207"></script><!-- v1.2.207: hapus-lead -->',
            '<script src="app.js?v=1.2.208"></script><!-- ' + TAG + ' --><!-- v1.2.207: hapus-lead -->', what='app.js?v')
    save(HT, s)
else: print('sudah', HT)
print('patch v1.2.208 selesai')
