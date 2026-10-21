#!/usr/bin/env python3
"""v1.2.96 — Jeda balasan AI WhatsApp berdasarkan jumlah karakter.
Pola contoh: 1-50 karakter -> 3 detik, 51-200 -> 5 detik, lebih dari itu -> 8 detik.
Waktu AI berpikir ikut dihitung (bot hanya menunggu sisanya). Maks 20 detik.
Pemakaian: python3 patch_v1296_jeda_balasan.py <root dei-tenant>   (idempoten; backup *.bak-v1296-*)
Butuh v1.2.95 (kb-foto) sudah terpasang."""
import sys, os, time, shutil
TEN = sys.argv[1]
STAMP = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.96: jeda-balasan'

def patch(root, rel, pairs):
    p = os.path.join(root, rel)
    s = open(p, encoding='utf-8').read()
    if MARK in s: print('sudah dipatch:', rel); return
    if rel == 'api/index.php' and 'v1.2.95: kb-foto' not in s: sys.exit('GAGAL: v1.2.95 (kb-foto) belum terpasang')
    for old, new in pairs:
        n = s.count(old)
        if n != 1: sys.exit(f'GAGAL {rel}: anchor {n}x:\n{old[:200]}')
        s = s.replace(old, new)
    shutil.copy2(p, p + '.bak-v1296-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

PHP_FUNCS = r'''/* v1.2.96: jeda-balasan — JEDA BALASAN AI (WhatsApp) berdasarkan jumlah karakter.
 * settings.reply_delay = { enabled, basis: 'answer'|'question',
 *   rules: [{max: 50, sec: 3}, {max: 200, sec: 5}], over_sec: 8 }
 * Teks <= max pertama -> sec-nya; dst. Lebih panjang dari semua max -> over_sec.
 * Jeda dihitung sejak AI mulai memproses (waktu AI berpikir ikut dihitung). Maks 20 detik. */
define('DEI_REPLY_DELAY_MAX', 20);
function deiReplyDelayConf($s = null) {
    if ($s === null) $s = getSettings();
    $r = is_array($s['reply_delay'] ?? null) ? $s['reply_delay'] : [];
    $rules = [];
    foreach ((array)($r['rules'] ?? [['max' => 50, 'sec' => 3], ['max' => 200, 'sec' => 5]]) as $x) {
        if (!is_array($x)) continue;
        $max = (int)($x['max'] ?? 0);
        if ($max < 1) continue;
        $rules[$max] = ['max' => min(100000, $max), 'sec' => max(0, min(DEI_REPLY_DELAY_MAX, (int)($x['sec'] ?? 0)))];
    }
    ksort($rules);
    return [
        'enabled'  => !empty($r['enabled']),
        'basis'    => (($r['basis'] ?? 'answer') === 'question') ? 'question' : 'answer',
        'rules'    => array_slice(array_values($rules), 0, 10),
        'over_sec' => max(0, min(DEI_REPLY_DELAY_MAX, (int)($r['over_sec'] ?? 8))),
    ];
}
function deiReplyDelaySec($c, $len) {
    foreach ($c['rules'] as $x) { if ($len <= $x['max']) return $x['sec']; }
    return $c['over_sec'];
}
// Tunggu sisa jeda sebelum balasan AI dikirim. $t0 = microtime(true) saat AI mulai memproses.
function deiReplyDelayWait($s, $question, $answer, $t0) {
    try {
        $c = deiReplyDelayConf($s);
        if (!$c['enabled']) return 0;
        $len = mb_strlen(trim((string)($c['basis'] === 'question' ? $question : $answer)));
        if ($len < 1) return 0;
        $sisa = deiReplyDelaySec($c, $len) - (microtime(true) - (float)$t0);
        if ($sisa > 0.05) usleep((int)(min(DEI_REPLY_DELAY_MAX, $sisa) * 1000000));
        return max(0, $sisa);
    } catch (\Throwable $e) { error_log('reply_delay: ' . $e->getMessage()); return 0; }
}
'''

patch(TEN, 'api/index.php', [
    ("define('DEI_VERSION', 'v1.2.95');", "define('DEI_VERSION', 'v1.2.96');"),
    ("// Pesan sistem ke satu nomor maks sekali per $ttl detik.",
     PHP_FUNCS + "// Pesan sistem ke satu nomor maks sekali per $ttl detik."),
    ("    $history = $keepCtx ? waLoadHistory($from) : [];\n    list($ok, $answer, $_kbUsed, $usage) = generateAnswer($s, $text, $history, 'whatsapp');   // v1.2.89\n",
     "    $history = $keepCtx ? waLoadHistory($from) : [];\n    $deiT0 = microtime(true);   // v1.2.96: jeda-balasan\n    list($ok, $answer, $_kbUsed, $usage) = generateAnswer($s, $text, $history, 'whatsapp');   // v1.2.89\n"),
    ("    $deiSent = (trim($answer) !== '') ? waSend($wa, $from, $answer) : true;   // v1.2.95: kb-foto\n",
     "    if (!$deiAiError) deiReplyDelayWait($s, $text, $answer, $deiT0);   // v1.2.96: jeda-balasan\n"
     "    $deiSent = (trim($answer) !== '') ? waSend($wa, $from, $answer) : true;   // v1.2.95: kb-foto\n"),
    # izin Admin menyimpan
    ("            if (isset($incoming['wa_hemat']) && is_array($incoming['wa_hemat'])) {   // v1.2.89\n",
     "            if (isset($incoming['reply_delay']) && is_array($incoming['reply_delay'])) {   // v1.2.96: jeda-balasan\n"
     "                $merged['reply_delay'] = deiMergeSettings($current['reply_delay'] ?? [], $incoming['reply_delay']);\n"
     "            }\n"
     "            if (isset($incoming['wa_hemat']) && is_array($incoming['wa_hemat'])) {   // v1.2.89\n"),
    # rapikan nilai sebelum disimpan
    ("        $modeLama = deiReplyMode($current);\n        writeJson(SETTINGS_FILE, $merged);\n",
     "        if (isset($merged['reply_delay']) && is_array($merged['reply_delay'])) {   // v1.2.96: jeda-balasan\n"
     "            $merged['reply_delay'] = deiReplyDelayConf($merged);\n"
     "        }\n"
     "        $modeLama = deiReplyMode($current);\n        writeJson(SETTINGS_FILE, $merged);\n"),
    # beri ruang waktu: gabung pesan (maks 8 dtk) + AI + jeda (maks 20 dtk)
    ("        if ($earlyAck) respondAndContinue('EVENT_RECEIVED');\n        @set_time_limit(60);\n",
     "        if ($earlyAck) respondAndContinue('EVENT_RECEIVED');\n        @set_time_limit(90);   // v1.2.96: jeda-balasan\n"),
    ("        if ($earlyAck) respondAndContinue('OK');\n        @set_time_limit(60);\n        waHandleMetaPayload",
     "        if ($earlyAck) respondAndContinue('OK');\n        @set_time_limit(90);   // v1.2.96: jeda-balasan\n        waHandleMetaPayload"),
])

HTML_CARD = '''      <!-- v1.2.96: jeda-balasan -->
      <div class="card"><h3>Jeda Balasan AI (WhatsApp)</h3>
        <div class="desc">Balasan bot ditahan sesuai panjang teks supaya terasa seperti diketik manusia, tidak muncul instan. Waktu AI berpikir ikut dihitung: bila AI butuh 2 detik dan jeda 5 detik, bot menunggu 3 detik lagi.</div>
        <div class="toggle-row"><div><div class="tt">Aktifkan Jeda Balasan</div></div><label class="switch"><input type="checkbox" id="rd_enabled"><span class="sl"></span></label></div>
        <div class="row"><label class="fl">Hitung dari</label><select id="rd_basis"><option value="answer">Panjang balasan AI</option><option value="question">Panjang pesan pelanggan</option></select></div>
        <div class="row"><label class="fl">Pola jeda</label><div id="rd_rules" style="flex:1"></div><button class="btn ghost" type="button" id="rd_add">+ Tambah pola</button></div>
        <div class="row"><label class="fl">Lebih panjang dari pola terakhir (detik)</label><input type="number" id="rd_over" min="0" max="20" step="1" value="8"></div>
        <div class="help">Maksimal 20 detik per balasan. Tidak berlaku untuk pesan sistem, widget web, dan Tes Chatbot.</div>
      </div>

'''
patch(TEN, 'dashboard/chatbot-ai/index.html', [
    ('      <div class="card"><h3>Eskalasi Darurat (Emergency Call)</h3>',
     HTML_CARD + '      <div class="card"><h3>Eskalasi Darurat (Emergency Call)</h3>'),
])

JS_FUNCS = r'''  /* v1.2.96: jeda-balasan — pola jeda balasan AI per jumlah karakter */
  var rdRules = [];
  function rdRender() {
    var box = $('#rd_rules');
    if (!box) return;
    box.innerHTML = '';
    if (!rdRules.length) box.innerHTML = '<div class="help">Belum ada pola — semua balasan memakai jeda "lebih panjang".</div>';
    var prev = 0;
    rdRules.forEach(function (r, i) {
      var row = document.createElement('div');
      row.style.cssText = 'display:flex;align-items:center;gap:6px;margin-bottom:6px;flex-wrap:wrap';
      row.innerHTML =
        '<span class="rd-from" style="min-width:52px">' + (prev + 1) + ' –</span>' +
        '<input type="number" min="1" data-f="max" style="width:90px" value="' + (r.max || '') + '"> karakter →' +
        '<input type="number" min="0" max="20" data-f="sec" style="width:70px" value="' + (r.sec == null ? '' : r.sec) + '"> detik' +
        '<button class="btn ghost" type="button" title="Hapus">&times;</button>';
      row.querySelectorAll('input').forEach(function (inp) {
        inp.oninput = function () { rdRules[i][inp.dataset.f] = inp.value === '' ? '' : +inp.value; };
        inp.onchange = function () { rdRules.sort(function (a, b) { return (+a.max || 0) - (+b.max || 0); }); rdRender(); };
      });
      row.querySelector('button').onclick = function () { rdRules.splice(i, 1); rdRender(); };
      box.appendChild(row);
      prev = +r.max || prev;
    });
  }
  function rdLoad(rd) {
    rd = rd || {};
    $('#rd_enabled').checked = rd.enabled === true;
    $('#rd_basis').value = rd.basis === 'question' ? 'question' : 'answer';
    $('#rd_over').value = (rd.over_sec === undefined || rd.over_sec === null) ? 8 : rd.over_sec;
    rdRules = (rd.rules && rd.rules.length ? rd.rules : [{ max: 50, sec: 3 }, { max: 200, sec: 5 }])
      .map(function (r) { return { max: r.max, sec: r.sec }; });
    rdRender();
    $('#rd_add').onclick = function () {
      var last = rdRules.length ? (+rdRules[rdRules.length - 1].max || 0) : 0;
      rdRules.push({ max: last ? last * 2 : 50, sec: '' }); rdRender();
    };
  }
  function rdCollect() {
    var seen = {}, rules = [];
    for (var i = 0; i < rdRules.length; i++) {
      var mx = Math.round(+rdRules[i].max || 0), sc = Math.round(+rdRules[i].sec || 0);
      if (mx < 1) continue;
      if (seen[mx]) return { error: 'Batas karakter ' + mx + ' dipakai dua kali.' };
      seen[mx] = 1;
      rules.push({ max: mx, sec: Math.max(0, Math.min(20, sc)) });
    }
    rules.sort(function (a, b) { return a.max - b.max; });
    return { enabled: $('#rd_enabled').checked, basis: $('#rd_basis').value, rules: rules,
      over_sec: Math.max(0, Math.min(20, Math.round(+$('#rd_over').value || 0))) };
  }
  function loadEskalasi() {'''

patch(TEN, 'dashboard/chatbot-ai/app.js', [
    ('  function loadEskalasi() {', JS_FUNCS),
    ("      $('#hm_prompt').checked = hm.prompt !== false;\n",
     "      $('#hm_prompt').checked = hm.prompt !== false;\n      rdLoad(res.settings.reply_delay);   // v1.2.96: jeda-balasan\n"),
    ("    if (esc_.enabled && !esc_.l1_contacts.length && !esc_.l2_contacts.length) { toast('Isi minimal satu kontak eskalasi.', true); return; }\n",
     "    if (esc_.enabled && !esc_.l1_contacts.length && !esc_.l2_contacts.length) { toast('Isi minimal satu kontak eskalasi.', true); return; }\n"
     "    var rd_ = rdCollect();   // v1.2.96: jeda-balasan\n"
     "    if (rd_.error) { toast(rd_.error, true); return; }\n"),
    ("      escalation: esc_,\n      wa_hemat: {   // v1.2.89\n",
     "      escalation: esc_,\n      reply_delay: rd_,   // v1.2.96: jeda-balasan\n      wa_hemat: {   // v1.2.89\n"),
])
print('selesai')
