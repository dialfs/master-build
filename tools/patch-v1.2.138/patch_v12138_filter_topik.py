#!/usr/bin/env python3
"""v1.2.138 filter-topik: klasifikasi topik & divisi chat WA oleh AI (lewat server pusat, key DEI) + filter di
Percakapan WA + menu Topik & Divisi; Customer Feedback kini mulai paket Growth. Idempoten.
Pakai: patch_v12138_filter_topik.py [~/Herd]   (mematch dei-tenant DAN dei-pusat)"""
import os, sys, shutil, time
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd')
T = H + '/dei-tenant'; P = H + '/dei-pusat'; D = os.path.dirname(os.path.abspath(__file__))
TAG = 'v1.2.138: filter-topik'; STAMP = time.strftime('%Y%m%d-%H%M%S'); done = set()
blk = lambda n: open(D + '/' + n, encoding='utf-8').read()

def rep(fp, a, b, root=None):
    s = open(fp, encoding='utf-8').read()
    if b in s: return
    assert s.count(a) == 1, (fp, s.count(a), a[:100])
    if fp not in done: shutil.copy2(fp, fp + '.bak-v12138-' + STAMP); done.add(fp)
    open(fp, 'w', encoding='utf-8').write(s.replace(a, b))

API = T + '/api/index.php'; A = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ================= TENANT: api/index.php =================
rep(API, "define('DEI_VERSION', 'v1.2.137');   // v1.2.137: kembali-bot", "define('DEI_VERSION', 'v1.2.138');   // " + TAG)
# Customer Feedback mulai Growth (sudah dipatch manual 4 Nov — idempoten)
rep(API, "define('GC_TIERS', 'business,pro,custom,enterprise')", "define('GC_TIERS', 'growth,business,pro,custom,enterprise')")
rep(API, "preset aspek per industri). Mulai paket Business.", "preset aspek per industri). Mulai paket Growth.")
rep(API, "// Paket: tanpa server pusat (instalasi sendiri) = boleh. Trial & Starter/Growth = belum.\nfunction gcPlan", "// Paket: tanpa server pusat (instalasi sendiri) = boleh. Trial & Starter = belum.\nfunction gcPlan")
rep(API, "Customer Feedback tersedia mulai paket Business.", "Customer Feedback tersedia mulai paket Growth.")

# blok fungsi
rep(API, "function deiApplyPushedFeatures($raw) {", blk('tp_block.php') + "function deiApplyPushedFeatures($raw) {")
rep(API, "    unset($GLOBALS['dei_gc_plan']);\n", "    unset($GLOBALS['dei_gc_plan'], $GLOBALS['dei_tp_plan'], $GLOBALS['dei_tp_active']);   // " + TAG + "\n")
rep(API, "        'trial'           => deiTrialNorm($cap['trial'] ?? null),   // v1.2.90\n",
         "        'trial'           => deiTrialNorm($cap['trial'] ?? null),   // v1.2.90\n"
         "        'classify_quota'  => (int)($cap['classify_quota'] ?? -1),   // " + TAG + "\n")
# endpoint
rep(API, "    case 'topic_scan_get': {", blk('tp_cases.php') + "    case 'topic_scan_get': {")

# pemicu: pesan pelanggan
rep(API, """    $bye  = deiIsClosingPhrase($text);
    try {
        convStateMutate(function (&$all) use ($num, $text, $lang, $bye) {""", """    $bye  = deiIsClosingPhrase($text);
    $tpInc = false; try { $tpInc = tpActive() && tpCountable($text, $bye); } catch (\\Throwable $e) {}   // """ + TAG + """
    try {
        convStateMutate(function (&$all) use ($num, $text, $lang, $bye, $tpInc) {""")
rep(API, """            $st['last_guest_text'] = mb_substr((string)$text, 0, 160);
            $all[$num] = $st;""", """            $st['last_guest_text'] = mb_substr((string)$text, 0, 160);
            if ($tpInc) $st['tp_n'] = (int)($st['tp_n'] ?? 0) + 1;   // """ + TAG + """
            $all[$num] = $st;""")
# pemicu: ditandai Selesai
rep(API, """            $st['res_at'] = time(); $st['res_by'] = $u['username']; $st['guest_waiting_since'] = 0;
            $st['esc_level'] = 0; $st['esc_inc'] = '';""", """            $st['res_at'] = time(); $st['res_by'] = $u['username']; $st['guest_waiting_since'] = 0;
            $st['esc_level'] = 0; $st['esc_inc'] = '';
            if (tpActive()) $st['tp_due'] = 1;   // """ + TAG)
# cron
rep(API, "        try { $r['routed'] = deiRouteDrain(20, $s); } catch (\\Throwable $e) { $r['err_routing'] = $e->getMessage(); }   // v1.2.100: routing\n",
         "        try { $r['routed'] = deiRouteDrain(20, $s); } catch (\\Throwable $e) { $r['err_routing'] = $e->getMessage(); }   // v1.2.100: routing\n"
         "        try { $tpr = tpSweep($s); if ($tpr) $r['topics'] = $tpr; } catch (\\Throwable $e) { $r['err_topics'] = $e->getMessage(); }   // " + TAG + "\n")
# wa_thread
rep(API, "            'stage' => deiNumStageVip($num)[0], 'vip' => deiNumStageVip($num)[1],\n        ]);",
         "            'stage' => deiNumStageVip($num)[0], 'vip' => deiNumStageVip($num)[1],\n"
         "            'tp' => tpActive() ? tpPublic(waContactGet($num) ?: []) : null,   // " + TAG + "\n        ]);")
# wa_conversations_v2
rep(API, """        $stCounts = deiStageCountsInit();
        $allLeads = leadsGetAll();""", """        $stCounts = deiStageCountsInit();
        $tpOn = tpActive();   // """ + TAG + """
        $tpRaw = (string)($_GET['tpt'] ?? ''); $tpF = (!$tpOn || $tpRaw === '') ? '' : ($tpRaw === '__none' ? '__none' : tpSlug($tpRaw));
        $tpRawD = (string)($_GET['tpd'] ?? ''); $tpDF = (!$tpOn || $tpRawD === '') ? '' : ($tpRawD === '__none' ? '__none' : tpSlug($tpRawD));
        $tpEver = $tpF !== '' && $tpF !== '__none' && !empty($_GET['tpe']);
        $tpCounts = ['all' => 0, '__none' => 0]; $tpDCounts = ['all' => 0, '__none' => 0]; $tpMap = $tpOn ? tpTopicMap() : [];
        $allLeads = leadsGetAll();""")
rep(API, """                'has_history' => isset($wiIx[$num]), 'history_only' => !empty($meta['history_only']),   // v1.2.105: riwayat-wa-waha
            ];""", """                'has_history' => isset($wiIx[$num]), 'history_only' => !empty($meta['history_only']),   // v1.2.105: riwayat-wa-waha
                'tp' => $tpOn ? tpPublic($allContacts[$num] ?? null) : null,   // """ + TAG + """
            ];""")
rep(API, """            if ($show) {   // v1.2.117: jumlah per Lead Rating dihitung dalam filter status aktif
                deiStageCountAdd($stCounts, $item['stage'], $item['vip']);
                if (deiStageMatch($stF, $item['stage'], $item['vip'])) $result[] = $item;
            }""", """            if ($show) {   // v1.2.117: jumlah per Lead Rating dihitung dalam filter status aktif
                deiStageCountAdd($stCounts, $item['stage'], $item['vip']);
                if (deiStageMatch($stF, $item['stage'], $item['vip'])) {
                    if (!$tpOn) $result[] = $item;
                    else {   // """ + TAG + """: jumlah topik dihitung dalam filter status + Lead Rating + divisi; jumlah divisi dalam filter topik
                        $tpI = $item['tp'];
                        $okT = tpMatchTopic($tpI, $tpF, $tpEver); $okD = tpMatchDiv($tpI, $tpDF);
                        if ($okD) {
                            $tpCounts['all']++;
                            if (!$tpI || !$tpI['t']) $tpCounts['__none']++;
                            foreach ($tpI ? ($tpEver ? array_unique(array_merge($tpI['t'], $tpI['h'])) : $tpI['t']) : [] as $x) if (isset($tpMap[$x])) $tpCounts[$x] = ($tpCounts[$x] ?? 0) + 1;
                        }
                        if ($okT) { $tpDCounts['all']++; $dd = $tpI ? $tpI['d'] : ''; if ($dd === '') $tpDCounts['__none']++; else $tpDCounts[$dd] = ($tpDCounts[$dd] ?? 0) + 1; }
                        if ($okT && $okD) $result[] = $item;
                    }
                }
            }""")
rep(API, "            'stage_counts' => $stCounts, 'stage' => $stF,   // v1.2.117: filter-lead-rating\n",
         "            'stage_counts' => $stCounts, 'stage' => $stF,   // v1.2.117: filter-lead-rating\n"
         "            'tp' => $tpOn ? (tpClientConf() + ['f' => $tpF, 'fd' => $tpDF, 'ever' => $tpEver, 'counts' => $tpCounts, 'dcounts' => $tpDCounts]) : ['on' => false],   // " + TAG + "\n")
# Scan Topik memakai taksonomi yang sama
rep(API, """        $hint = [];
        foreach (readJson(KB_FILE, []) as $e) { $c = trim((string)($e['category'] ?? '')); if ($c !== '') $hint[$c] = true; }""",
"""        $hint = [];
        foreach (readJson(KB_FILE, []) as $e) { $c = trim((string)($e['category'] ?? '')); if ($c !== '') $hint[$c] = true; }
        $tpNames = []; if (tpActive()) foreach (tpConf()['topics'] as $tpx) $tpNames[] = $tpx['name'];   // """ + TAG + """: taksonomi bersama""")
rep(API, """             . "Kelompokkan SEMUA percakapan ke dalam 4-10 topik utama berdasarkan maksud/kebutuhan pelanggan.\\n\\n\"""",
"""             . ($tpNames ? "Kelompokkan SEMUA percakapan ke topik dari DAFTAR TETAP ini (pakai nama persis, boleh ada yang kosong): " . implode('; ', $tpNames) . ". Sapaan masuk \\"Sapaan & basa-basi\\", sisanya \\"Lainnya\\".\\n\\n"
                         : "Kelompokkan SEMUA percakapan ke dalam 4-10 topik utama berdasarkan maksud/kebutuhan pelanggan.\\n\\n")   // """ + TAG)

# ================= TENANT: app.js =================
rep(A, "survei kepuasan pelanggan (WA + form web), mulai paket Business", "survei kepuasan pelanggan (WA + form web), mulai paket Growth")
rep(A, "<b>Fitur paket Business</b>", "<b>Fitur paket Growth</b>")
rep(A, "  /* ====================================================================== *\n   *  v1.2.109: guest-comment",
       blk('tp_block.js') + "\n  /* ====================================================================== *\n   *  v1.2.109: guest-comment")
rep(A, "    gc: loadGc   // v1.2.109: guest-comment", "    topik: loadTopik,   // " + TAG + "\n    gc: loadGc   // v1.2.109: guest-comment")
rep(A, """        stageFltOptionsHtml(waState.stage || '', waState.stageCounts) + '</select><span class="wa-dd-chev">' + ico('chevron-down',14) + '</span></label>' +
      '<span class="wa-sp"></span>' +""", """        stageFltOptionsHtml(waState.stage || '', waState.stageCounts) + '</select><span class="wa-dd-chev">' + ico('chevron-down',14) + '</span></label>' +
      tfFilterBarHtml() +   // """ + TAG + """
      '<span class="wa-sp"></span>' +""")
rep(A, """      '<div class="wa-fbar2">' +   // v1.2.124""", """      '<div class="wa-fbar2' + (tfOn() ? ' tf-on' : '') + '">' +   // v1.2.124""")
rep(A, "    if (_stSel) _stSel.onchange = function () { waState.stage = this.value; this.parentNode.classList.toggle('is-on', !!this.value); fetchWaConvs(); };\n",
       "    if (_stSel) _stSel.onchange = function () { waState.stage = this.value; this.parentNode.classList.toggle('is-on', !!this.value); fetchWaConvs(); };\n"
       "    tfBindFilterBar();   // " + TAG + "\n")
rep(A, "    if (waState.stage) query += '&stage=' + encodeURIComponent(waState.stage);   // v1.2.117: filter-lead-rating\n",
       "    if (waState.stage) query += '&stage=' + encodeURIComponent(waState.stage);   // v1.2.117: filter-lead-rating\n"
       "    query += tfQuery();   // " + TAG + "\n")
rep(A, "      if (res.stage !== undefined) waState.stage = res.stage || '';\n",
       "      if (res.stage !== undefined) waState.stage = res.stage || '';\n"
       "      tfFromList(res);   // " + TAG + "\n")
rep(A, """ + ' dengan Lead Rating "' + stageFltLabel(waState.stage) + '"';   // v1.2.117
""", """ + ' dengan Lead Rating "' + stageFltLabel(waState.stage) + '"';   // v1.2.117
      if (tfOn() && (waState.tfF || waState.tfDF)) msg = ((waState.filter && waState.filter !== 'all') || waState.stage ? msg : 'Tidak ada percakapan') + tfEmptySuffix();   // """ + TAG + """
""")
rep(A, "        '<div style=\"margin-top:5px\">' + badge + waFlagBadgeHtml(c) + awa + attn + stageBadge + '</div>' +",
       "        '<div style=\"margin-top:5px\">' + badge + waFlagBadgeHtml(c) + awa + attn + stageBadge + tfBadgeHtml(c.tp) + '</div>' +   // " + TAG)
rep(A, """            '<select id="waStageSelect">' + _stageOpts + '</select>' + ico('chevron-down',12) + '</label></div>' +""",
       """            '<select id="waStageSelect">' + _stageOpts + '</select>' + ico('chevron-down',12) + '</label></div>' +
          tfThreadRowHtml(res) +   // """ + TAG)
rep(A, "    waInfoRender(res, _konv, claim);\n", "    waInfoRender(res, _konv, claim);\n    tfBindThread(num, res);   // " + TAG + "\n")

# ================= TENANT: index.html =================
rep(HT, '<script src="app.js?v=1.2.137"></script><!-- v1.2.137: kembali-bot -->', '<script src="app.js?v=1.2.138"></script><!-- ' + TAG + ' -->')
rep(HT, "\n</style>", "\n" + blk('tp_css.css') + "</style>")
rep(HT, """      <button data-tab="gc"       data-role="super_admin,admin,supervisor" data-icon="message-square-heart">""",
        """      <button data-tab="topik"    data-role="super_admin,admin" data-icon="tag"><span class="ic"></span> Topik &amp; Divisi</button><!-- """ + TAG + """ -->
      <button data-tab="gc"       data-role="super_admin,admin,supervisor" data-icon="message-square-heart">""")
rep(HT, '    <section class="panel" id="panel-gc">', blk('tp_panel.html') + '    <section class="panel" id="panel-gc">')

# ================= PUSAT =================
PB = P + '/backend/index.php'; PC = P + '/backend/cron-tick.php'; PA = P + '/admin/index.html'; PL = P + '/backend/classify-lib.php'
lib = blk('classify-lib.php')
if not os.path.exists(PL) or open(PL, encoding='utf-8').read() != lib:
    if os.path.exists(PL): shutil.copy2(PL, PL + '.bak-v12138-' + STAMP)
    open(PL, 'w', encoding='utf-8').write(lib)
rep(PB, "require_once __DIR__ . '/signup-lib.php';   // v1.2.90: pendaftaran mandiri & trial\n",
        "require_once __DIR__ . '/signup-lib.php';   // v1.2.90: pendaftaran mandiri & trial\n"
        "require_once __DIR__ . '/classify-lib.php';   // " + TAG + "\n")
rep(PB, "    /* v1.2.91: wa-api — permintaan koneksi WhatsApp API resmi dari tenant (auth tenant_id + license_key) */\n    case 'wa_api_request': {",
        """    /* """ + TAG + """: klasifikasi topik chat WA untuk tenant (auth tenant_id + license_key; key OpenRouter pusat) */
    case 'classify': {
        list($clsCode, $clsOut) = clsHandle(readJson(TENANTS_FILE, []), bodyInput());
        jsonOut($clsOut, $clsCode);
    }
    case 'get_classify_config': {
        requireAdmin();
        jsonOut(['ok' => true, 'classify' => clsConfigPublic()]);
    }
    case 'save_classify_config': {
        requireAdmin();
        jsonOut(['ok' => true, 'classify' => clsSaveConfig(bodyInput())]);
    }

    /* v1.2.91: wa-api — permintaan koneksi WhatsApp API resmi dari tenant (auth tenant_id + license_key) */
    case 'wa_api_request': {""")
rep(PB, "                'max_wa_numbers'       => (int)($tenant['max_wa_numbers'] ?? 0),      // v1.2.99: lisensi-nomor (nomor WA tambahan)\n",
        "                'max_wa_numbers'       => (int)($tenant['max_wa_numbers'] ?? 0),      // v1.2.99: lisensi-nomor (nomor WA tambahan)\n"
        "                'classify_quota'       => clsQuota($tenant),                          // " + TAG + "\n")
rep(PB, "        $mwIn      = array_key_exists('max_wa_numbers', $in) ? (int)$in['max_wa_numbers'] : null;   // v1.2.99: lisensi-nomor\n",
        "        $mwIn      = array_key_exists('max_wa_numbers', $in) ? (int)$in['max_wa_numbers'] : null;   // v1.2.99: lisensi-nomor\n"
        "        $clsIn     = array_key_exists('classify_quota', $in) ? $in['classify_quota'] : false;   // " + TAG + ": null/'' = ikut paket\n"
        "        if ($clsIn !== false && $clsIn !== null && $clsIn !== '' && ((int)$clsIn < 0 || (int)$clsIn > 1000000)) jsonOut(['ok' => false, 'error' => 'Kuota klasifikasi topik harus 0..1000000 (kosong = ikut paket).'], 400);\n")
rep(PB, "                if ($mwIn !== null)      $t['max_wa_numbers'] = $mwIn;      // v1.2.99\n",
        "                if ($mwIn !== null)      $t['max_wa_numbers'] = $mwIn;      // v1.2.99\n"
        "                if ($clsIn !== false) { if ($clsIn === null || $clsIn === '') unset($t['classify_quota']); else $t['classify_quota'] = (int)$clsIn; }   // " + TAG + "\n")
rep(PB, "        foreach ($tenants as &$tt) { $tt['cron'] = $cronSt[tidNorm((string)($tt['tenant_id'] ?? ''))] ?? null; }\n",
        "        foreach ($tenants as &$tt) { $tt['cron'] = $cronSt[tidNorm((string)($tt['tenant_id'] ?? ''))] ?? null;\n"
        "            $tt['classify'] = ['quota' => clsQuota($tt), 'used' => (int)(clsUsageFor((string)($tt['tenant_id'] ?? ''))['n'] ?? 0)]; }   // " + TAG + "\n")
rep(PC, "require_once __DIR__ . '/signup-lib.php';   // v1.2.90: trial\n",
        "require_once __DIR__ . '/signup-lib.php';   // v1.2.90: trial\nrequire_once __DIR__ . '/classify-lib.php';   // " + TAG + "\n")
rep(PC, "                'max_wa_numbers' => (int)($t['max_wa_numbers'] ?? 0), 'tier' => strtolower((string)($t['tier'] ?? 'custom'))])],",
        "                'max_wa_numbers' => (int)($t['max_wa_numbers'] ?? 0), 'tier' => strtolower((string)($t['tier'] ?? 'custom')), 'classify_quota' => clsQuota($t)])],   // " + TAG)
# admin panel pusat
rep(PA, """        <label><input type="checkbox" id="m_white_label" ${t.white_label?'checked':''}>""",
        """        <div class="row" style="gap:8px;margin-top:8px"><!-- """ + TAG + """ -->
          <div style="flex:1"><label>Kuota Klasifikasi Topik / bulan</label><input id="m_cls_quota" type="number" min="0" max="1000000" placeholder="ikut paket" value="${t.classify_quota ?? ''}"></div>
          <div style="flex:1;align-self:end" class="hint">${t.classify ? 'Terpakai bulan ini: <b>'+t.classify.used+'</b> / '+t.classify.quota : ''}<br>Kosong = ikut paket (Growth 5.000 · Business 15.000 · Pro 30.000). 0 = mati. ±Rp3 per klasifikasi.</div>
        </div>
        <label><input type="checkbox" id="m_white_label" ${t.white_label?'checked':''}>""")
rep(PA, "    topic_scan_quota: Math.max(0, parseInt($('#m_topic_quota').value, 10) || 0),\n  };",
        "    topic_scan_quota: Math.max(0, parseInt($('#m_topic_quota').value, 10) || 0),\n"
        "    classify_quota: $('#m_cls_quota').value.trim()==='' ? null : Math.max(0, parseInt($('#m_cls_quota').value, 10) || 0),   // " + TAG + "\n  };")
rep(PA, """  <div class="card">
    <h2><span style="color:var(--brand)" id="adminCfgIcon"></span> Konfigurasi Admin (Cap Alerts)</h2>""",
        """  <div class="card"><!-- """ + TAG + """ -->
    <h2>Klasifikasi Topik AI (Filter Topik tenant)</h2>
    <div class="hint" style="margin-bottom:10px">Tenant paket Growth ke atas memakai key ini untuk melabeli topik chat WA. Kuota bawaan per bulan: Growth 5.000 · Business 15.000 · Pro 30.000 (ubah per tenant di modal tenant). Key kosong = memakai key OpenRouter pendaftaran.</div>
    <div class="row" style="gap:10px">
      <div style="flex:1;min-width:260px"><label>OpenRouter API Key klasifikasi</label><input id="cls_key" style="width:100%" placeholder="sk-or-v1-…"></div>
      <div style="flex:1;min-width:220px"><label>Model</label><input id="cls_model" style="width:100%" placeholder="anthropic/claude-haiku-5.5"></div>
    </div>
    <label style="font-size:13px;margin-top:8px;display:block"><input type="checkbox" id="cls_enabled"> Layanan klasifikasi aktif</label>
    <div class="hint" id="clsState" style="margin-top:6px"></div>
    <button onclick="saveClsCfg()" style="margin-top:10px">Simpan Klasifikasi Topik</button>
  </div>

  <div class="card">
    <h2><span style="color:var(--brand)" id="adminCfgIcon"></span> Konfigurasi Admin (Cap Alerts)</h2>""")
rep(PA, "loadSignupCfg();\n", """loadSignupCfg();
// """ + TAG + """
function loadClsCfg(){
  api('get_classify_config').then(res=>{
    if(!res.ok) return;
    const c=res.classify;
    $('#cls_model').value=c.model||''; $('#cls_enabled').checked=!!c.enabled;
    $('#cls_key').value=''; $('#cls_key').placeholder=c.own_key?c.key_masked:(c.key_set?'(memakai key pendaftaran)':'sk-or-v1-…');
    const u=Object.entries(c.usage||{}).sort((a,b)=>(b[1].n||0)-(a[1].n||0));
    const tot=u.reduce((s,x)=>s+(x[1].n||0),0), cost=u.reduce((s,x)=>s+(x[1].cost||0),0);
    $('#clsState').innerHTML=(c.key_set?'':'<span style="color:var(--err)">Key belum diatur. </span>')+'Bulan '+esc(c.month)+': <b>'+tot.toLocaleString('id-ID')+'</b> klasifikasi, $'+cost.toFixed(3)
      +(u.length?' — '+u.slice(0,8).map(x=>esc(x[0])+' '+x[1].n).join(' · '):'');
  });
}
window.saveClsCfg=function(){
  api('save_classify_config',{method:'POST',body:{openrouter_key:$('#cls_key').value.trim(),model:$('#cls_model').value.trim(),enabled:$('#cls_enabled').checked}})
    .then(res=>{ if(res.ok){ toast('Pengaturan klasifikasi tersimpan.'); loadClsCfg(); } else toast(res.error||'Gagal.',true); });
};
loadClsCfg();
""")
print('patch v1.2.138 OK; file diubah:', len(done))
