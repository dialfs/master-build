#!/usr/bin/env python3
"""v1.2.109: guest-comment — survei kepuasan tamu lewat chatbot WA (alur terpandu tanpa AI) + form web publik
(?action=gc_form untuk QR kamar/front desk) + tab dashboard "Guest Comment". Mulai paket Business (business/pro/custom).
Pusat: cron-tick ikut mengirim tier di X-Dei-Features supaya upgrade paket berlaku <= 1 menit.
Pakai: python3 patch_v12109_guest_comment.py ~/Herd   (idempoten)"""
import sys, os, shutil, time
D = os.path.dirname(os.path.abspath(__file__))
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd'); T = H + '/dei-tenant'; PU = H + '/dei-pusat'
TAG = 'v1.2.109: guest-comment'
stamp = time.strftime('%Y%m%d-%H%M%S')
rd = lambda f: open(os.path.join(D, f), encoding='utf-8').read()
PHP_FUNCS = rd('gc_funcs.php')
PHP_CASES = rd('gc_cases.php')
JS_FUNCS = rd('gc_app.js').replace('/*@@QRLIB@@*/', rd('qrcode.min.js').strip()) if os.path.exists(os.path.join(D, 'gc_app.js')) else None
HTML_PANEL = rd('gc_panel.html') if os.path.exists(os.path.join(D, 'gc_panel.html')) else None

P = {
 'api/index.php': [
  ("define('DEI_VERSION', 'v1.2.108');   // v1.2.108: tolak-telepon",
   "define('DEI_VERSION', 'v1.2.109');   // " + TAG),
  ("'web_lead_save', 'web_closing'];   // v1.2.56",
   "'web_lead_save', 'web_closing', 'gc_submit'];   // v1.2.56; " + TAG),
  ("function waProcessIncoming($s, $wa, $from, $text, $senderName = '', $metaInfo = []) {\n",
   PHP_FUNCS + "\nfunction waProcessIncoming($s, $wa, $from, $text, $senderName = '', $metaInfo = []) {\n"),
  ("    $mode = waGetMode($from);\n    // Auto-handoff: a keyword flips this number to human mode.\n",
   "    $mode = waGetMode($from);\n"
   "    // " + TAG + " — survei terpandu (sebelum handoff kata kunci & batas AI; tanpa panggilan AI)\n"
   "    if ($mode === 'bot' && !deiIsManual($s)) {\n"
   "        try { if (gcWaHandle($s, $wa, $from, $text, $senderName, $metaInfo)) return; }\n"
   "        catch (\\Throwable $e) { error_log('guest-comment: ' . $e->getMessage()); }\n"
   "    }\n"
   "    // Auto-handoff: a keyword flips this number to human mode.\n"),
  ('        . "Jika pelanggan mengeluh ditanya berulang, minta maaf singkat dan JANGAN bertanya lagi.");\n',
   '        . "Jika pelanggan mengeluh ditanya berulang, minta maaf singkat dan JANGAN bertanya lagi.");\n'
   "    $deiGcBlk = ''; try { $deiGcBlk = gcPromptBlock($channel); } catch (\\Throwable $e) { error_log('gcPromptBlock: ' . $e->getMessage()); }\n"
   "    if ($deiGcBlk !== '') $deiPriceBlk = trim($deiPriceBlk . \"\\n\\n\" . $deiGcBlk);   // " + TAG + "\n"),
  ("    case 'wa_calls': {\n", PHP_CASES + "    case 'wa_calls': {\n"),
  ("    $f = deiFeaturesFromCap(is_array($j) ? $j : null);\n    if (!$f) return false;\n    $cache = readJson(CAP_CACHE_FILE, []);\n    if (($cache['features'] ?? null) == $f) return false;\n    $cache['features'] = $f;\n",
   "    $f = deiFeaturesFromCap(is_array($j) ? $j : null);\n    if (!$f) return false;\n    $cache = readJson(CAP_CACHE_FILE, []);\n"
   "    $tierP = (is_array($j) && isset($j['tier'])) ? strtolower(trim((string)$j['tier'])) : '';   // " + TAG + ": tier ikut didorong pusat\n"
   "    if (($cache['features'] ?? null) == $f && ($tierP === '' || (string)($cache['tier'] ?? '') === $tierP)) return false;\n"
   "    $cache['features'] = $f;\n    if ($tierP !== '') $cache['tier'] = $tierP;\n    unset($GLOBALS['dei_gc_plan']);\n"),
 ],
}
PUSAT = {
 'backend/cron-tick.php': [
  ("                'max_wa_numbers' => (int)($t['max_wa_numbers'] ?? 0)])],   // v1.2.90: trial; v1.2.99: lisensi-nomor",
   "                'max_wa_numbers' => (int)($t['max_wa_numbers'] ?? 0), 'tier' => strtolower((string)($t['tier'] ?? 'custom'))])],   // v1.2.90: trial; v1.2.99: lisensi-nomor; " + TAG),
 ],
}
if JS_FUNCS is not None:
    P['dashboard/chatbot-ai/app.js'] = [
  ("    pembaruan: function () { loadPembaruan(false); }   // v1.2.65\n  };",
   "    pembaruan: function () { loadPembaruan(false); },   // v1.2.65\n    gc: loadGc   // " + TAG + "\n  };"),
  ("  var loaders = {\n    eskalasi: loadEskalasi,", JS_FUNCS + "\n  var loaders = {\n    eskalasi: loadEskalasi,"),
  ("  if (location.hash === '#pembaruan' && relCanSee()) firstTab = 'pembaruan';\n",
   "  if (location.hash === '#pembaruan' && relCanSee()) firstTab = 'pembaruan';\n"
   "  if (location.hash === '#gc' && can('super_admin,admin,supervisor')) firstTab = 'gc';   // " + TAG + "\n"),
    ]
if HTML_PANEL is not None:
    P['dashboard/chatbot-ai/index.html'] = [
  ('      <button data-tab="kontak"   data-role="super_admin,admin,supervisor,wa_agent" data-icon="users"><span class="ic"></span> Kontak</button>\n',
   '      <button data-tab="kontak"   data-role="super_admin,admin,supervisor,wa_agent" data-icon="users"><span class="ic"></span> Kontak</button>\n'
   '      <button data-tab="gc"       data-role="super_admin,admin,supervisor" data-icon="star"><span class="ic"></span> Guest Comment</button><!-- ' + TAG + ' -->\n'),
  ('    <!-- v1.2.65: PEMBARUAN (catatan rilis, khusus super_admin/admin) -->\n', HTML_PANEL + '\n    <!-- v1.2.65: PEMBARUAN (catatan rilis, khusus super_admin/admin) -->\n'),
  ('<script src="app.js?v=1.2.108"></script><!-- v1.2.108: tolak-telepon -->',
   '<script src="app.js?v=1.2.109"></script><!-- ' + TAG + ' -->'),
    ]

def run(root, spec, sfx):
    for f, reps in spec.items():
        p = root + '/' + f; s = open(p, encoding='utf-8').read(); o = s
        for a, b in reps:
            if b in s: continue
            assert s.count(a) == 1, 'anchor tidak unik/tidak ada di ' + f + ' (' + str(s.count(a)) + '): ' + a[:70]
            s = s.replace(a, b)
        if s != o:
            shutil.copy2(p, p + '.bak-' + sfx + '-' + stamp)
            open(p, 'w', encoding='utf-8').write(s); print('patched', f)
        else: print('sudah', f)
run(T, P, 'v12109')
if os.path.isdir(PU): run(PU, PUSAT, 'v12109')
