#!/usr/bin/env python3
"""v1.2.193 (asisten-support): tenant Support menarik umpan KB dari pusat dan menerima konteks pengguna di chat web.
Tenant (paket: api/index.php, assets/js/chat-widget.js):
- pusat -> tenant: `support_widget` (check_update) dan header X-Dei-Support (cron_tick) disimpan di data/support-widget.json
- tenant Support (self): cron_tick menarik support_kb_feed tiap 10 menit -> entri `kbg_<key>` di Knowledge Base
  (entri lain tidak disentuh; salinan KB lama di data/kb-guide-history/)
- action=chat: `context` dari widget dibersihkan dan masuk prompt HANYA di tenant Support; tercatat di log & judul percakapan
- action support_status (super_admin): keadaan umpan, POST {pull:true} = tarik sekarang
- widget: window.DEI_CHAT_CONTEXT (objek/fungsi) dikirim sebagai `context`
Pusat: backend/cron-tick.php mengirim header X-Dei-Support (butuh v1.2.192).
Idempoten.  Pakai: patch_v12193.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
D = os.path.dirname(os.path.abspath(__file__))
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
T = H + '/dei-tenant'; P = H + '/dei-pusat'
TAG = 'v1.2.193: asisten-support'; NEED = 'v1.2.186: grup-inbox'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12193-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)

# ------------------------------------------------------------------ tenant: api/index.php
API = T + '/api/index.php'; s = rd(API)
if TAG in s: print('sudah:', API)
else:
    assert NEED in s, 'butuh v1.2.186'
    # 1) pustaka
    a = "function deiPayUrl() { return (string)(readJson(DATA_DIR . '/pay-url.json', [])['url'] ?? ''); }\n"
    s = rep(s, a, a + rd(D + '/t_lib.php'), what='deiPayUrl')
    # 2) jawaban check_update (3 tempat) -> simpan support_widget
    for v, n in (('$data', 2), ('$j', 1)):   # sisipkan SEBELUM komentar baris (bukan di belakangnya)
        a = "if (array_key_exists('pay_url', %s)) deiPayUrlSave(%s['pay_url']);   // v1.2.173: bayar-mandiri\n" % (v, v)
        b = "if (array_key_exists('pay_url', %s)) deiPayUrlSave(%s['pay_url']); if (array_key_exists('support_widget', %s)) deiSupportApply(%s['support_widget']);   // v1.2.173: bayar-mandiri; %s\n" % (v, v, v, v, TAG)
        s = rep(s, a, b, n=n, what='pay_url ' + v)
    # 3) prompt: aturan + konteks, setelah titik cache KB
    a = "    $deiGcBlk = ''; try { $deiGcBlk = gcPromptBlock($channel); } catch (\\Throwable $e) { error_log('gcPromptBlock: ' . $e->getMessage()); }\n"
    s = rep(s, a, "    if (isset($GLOBALS['dei_support_ctx']) && is_array($GLOBALS['dei_support_ctx'])) $deiPriceBlk = trim($deiPriceBlk . \"\\n\\n\" . deiSupportCtxBlock($GLOBALS['dei_support_ctx']));   // " + TAG + "\n" + a, what='gcPromptBlock')
    # 4) chat web: terima konteks hanya di tenant Support
    a = "        $deiUnitCh = 'web';   // v1.2.167: unit-bisnis — Tes Chatbot boleh memilih unit\n"
    s = rep(s, a, "        $deiSpCtx = null;   // " + TAG + " — konteks dari dashboard penanya, hanya di tenant Support\n"
                  "        if (deiSupportSelf()) { $deiSpCtx = deiSupportCtxClean($in['context'] ?? null); $GLOBALS['dei_support_ctx'] = $deiSpCtx; }\n" + a, what='deiUnitCh')
    a = "            'referrer'     => substr((string)($utm['referrer'] ?? ''), 0, 300),\n        ];\n        $logLimit = (int)($s['api']['log_limit'] ?? 500);\n"
    s = rep(s, a, "            'referrer'     => substr((string)($utm['referrer'] ?? ''), 0, 300),\n        ];\n"
                  "        if ($deiSpCtx) $logRow['ctx'] = $deiSpCtx;   // " + TAG + "\n        $logLimit = (int)($s['api']['log_limit'] ?? 500);\n", what='logRow')
    a = "                    $convs[$idx]['title'] = deiWebConvLabel($ipC, $cityC);\n                }\n                webConvWrite($convs);\n"
    s = rep(s, a, "                    $convs[$idx]['title'] = deiWebConvLabel($ipC, $cityC);\n                }\n"
                  "                if ($deiSpCtx && (!empty($deiSpCtx['business']) || !empty($deiSpCtx['tenant_id']))) {   // " + TAG + " — judul = siapa yang bertanya\n"
                  "                    $convs[$idx]['title'] = mb_substr(trim(($deiSpCtx['business'] ?? '') . (!empty($deiSpCtx['tenant_id']) ? ' (' . $deiSpCtx['tenant_id'] . ')' : '') . (!empty($deiSpCtx['user']) ? ' · ' . $deiSpCtx['user'] : '')), 0, 80);\n"
                  "                }\n                webConvWrite($convs);\n", what='webConv title')
    # 5) cron_tick: header dari pusat + tarik umpan
    a = "        if (PHP_SAPI !== 'cli' && !empty($_SERVER['HTTP_X_DEI_LICENSE']))"
    s = rep(s, a, "        if (PHP_SAPI !== 'cli' && !empty($_SERVER['HTTP_X_DEI_SUPPORT'])) deiSupportApply($_SERVER['HTTP_X_DEI_SUPPORT']);   // " + TAG + "\n" + a, what='cron lic')
    a = "        try { $tpr = tpSweep($s); if ($tpr) $r['topics'] = $tpr; }"
    s = rep(s, a, "        try { if (empty($GLOBALS['dei_dry'])) { $spr = deiSupportFeedPull($s); if ($spr) $r['support_kb'] = $spr; } } catch (\\Throwable $e) { $r['err_support_kb'] = $e->getMessage(); }   // " + TAG + "\n" + a, what='cron tpSweep')
    # 6) action support_status
    a = "    case 'save_kb': {\n"
    s = rep(s, a, "    case 'support_status': {   // " + TAG + " — keadaan umpan KB; POST {pull:true} = tarik sekarang\n"
                  "        requireAuth(['super_admin']);\n"
                  "        $spPull = null;\n"
                  "        if ($_SERVER['REQUEST_METHOD'] === 'POST' && !empty(bodyInput()['pull'])) $spPull = deiSupportFeedPull(getSettings(), true);\n"
                  "        jsonOut(['ok' => true, 'support' => deiSupportInfo(), 'feed' => readJson(KBG_STATE_FILE, []), 'pull' => $spPull]);\n"
                  "        break;\n    }\n\n" + a, what='save_kb')
    # 7) versi
    old = "define('DEI_VERSION', 'v1.2.186');   //"
    i = s.index(old)
    s = s[:i] + "define('DEI_VERSION', 'v1.2.193');   // " + TAG + " — tenant Support: umpan KB dari pusat + konteks pengguna di chat;" + s[i + len(old):]
    save(API, s)

# ------------------------------------------------------------------ tenant: widget
W = T + '/assets/js/chat-widget.js'; s = rd(W)
if TAG in s: print('sudah:', W)
else:
    s = rep(s, "/* DEI AI Chat Widget v1.2.175 (v1.2.175: wa-atribusi)", "/* DEI AI Chat Widget v1.2.193 (" + TAG + "; v1.2.175: wa-atribusi)", what='kepala widget')
    a = "  /* ---- UTM + page capture --------------------------------------------- */\n"
    s = rep(s, a, "  /* " + TAG + " — konteks dari halaman pemasang (dashboard tenant): window.DEI_CHAT_CONTEXT = objek atau fungsi */\n"
                  "  function supportCtx() {\n"
                  "    try { var c = window.DEI_CHAT_CONTEXT; if (typeof c === 'function') c = c(); return (c && typeof c === 'object') ? c : undefined; }\n"
                  "    catch (e) { return undefined; }\n"
                  "  }\n\n" + a, what='UTM')
    a = "            history: [],\n            utm: getUTM()\n          })\n"
    s = rep(s, a, "            history: [],\n            utm: getUTM(),\n            context: supportCtx()\n          })\n", what='chat body')
    save(W, s)

# ------------------------------------------------------------------ pusat: cron-tick.php
CT = P + '/backend/cron-tick.php'; s = rd(CT)
if TAG in s: print('sudah:', CT)
else:
    assert os.path.isfile(P + '/backend/support-lib.php'), 'pusat butuh v1.2.192 (support-lib.php)'
    a = "$mh = curl_multi_init();\n"
    s = rep(s, a, "// " + TAG + " — pengaturan tenant Support ikut tiap tick (tombol Bantuan / penanda tenant Support berlaku <= 1 menit)\n"
                  "$ctSp = ctRead(PUSAT_DATA . '/admin-config.json', [])['support'] ?? [];\n"
                  "$ctSp = is_array($ctSp) ? ['enabled' => !empty($ctSp['enabled']), 'tenant_id' => strtolower(trim((string)($ctSp['tenant_id'] ?? ''))), 'base' => rtrim(trim((string)($ctSp['base'] ?? '')), '/')] : ['enabled' => false, 'tenant_id' => '', 'base' => ''];\n"
                  "function ctSupport($sp, $tid) {\n"
                  "    if ($sp['tenant_id'] !== '' && $sp['tenant_id'] === $tid) return ['enabled' => false, 'self' => true];\n"
                  "    if (!$sp['enabled'] || $sp['base'] === '' || $sp['tenant_id'] === '') return ['enabled' => false];\n"
                  "    return ['enabled' => true, 'base' => $sp['base']];\n"
                  "}\n\n" + a, what='curl_multi_init')
    a = "            'X-Dei-Latest: ' . $ctLatest,\n"
    s = rep(s, a, a + "            'X-Dei-Support: ' . json_encode(ctSupport($ctSp, $tid), JSON_UNESCAPED_SLASHES),   // " + TAG + "\n", what='X-Dei-Latest')
    save(CT, s)
print('selesai', TAG)
