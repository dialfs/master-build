#!/usr/bin/env python3
"""v1.2.204 (jam-ai): Jam Aktif AI (WhatsApp). settings.ai_schedule = {enabled, hours "21:00-09:00", full_days [0..6]}.
Di luar jam AI, deiReplyMode() = 'manual' -> semua chat WA ditangani agent (perilaku Mode Manual).
Butuh v1.2.203. Idempoten.  Pakai: patch_v12204.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.204: jam-ai'; NEED = 'v1.2.203: sales-tag'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12204-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ============================== API ==============================
PHP_LIB = r'''/* v1.2.204: jam-ai — JAM AKTIF AI (WhatsApp). AI hanya membalas pada jam tertentu (WIB);
 * di luar jam itu deiReplyMode() = 'manual' -> semua chat ditangani agent (perilaku Mode Manual:
 * antrean/routing, notifikasi & eskalasi jalan, claim tidak lepas otomatis).
 * settings.ai_schedule = { enabled, hours: "21:00-09:00" (boleh lewat tengah malam), full_days: [0..6] (0=Minggu; AI 24 jam) } */
function deiAiSchedConf($s = null) {
    if ($s === null) {
        if (!isset($GLOBALS['dei_ai_sched_cache'])) $GLOBALS['dei_ai_sched_cache'] = deiAiSchedConf(getSettings());
        return $GLOBALS['dei_ai_sched_cache'];
    }
    $a = is_array($s['ai_schedule'] ?? null) ? $s['ai_schedule'] : [];
    $h = trim((string)($a['hours'] ?? ''));
    $ok = preg_match('/^(\d{1,2})[:.](\d{2})\s*-\s*(\d{1,2})[:.](\d{2})$/', $h, $m)
        && (int)$m[1] <= 23 && (int)$m[3] <= 23 && (int)$m[2] <= 59 && (int)$m[4] <= 59;
    $h = $ok ? sprintf('%02d:%02d-%02d:%02d', $m[1], $m[2], $m[3], $m[4]) : '21:00-09:00';
    $days = [];
    foreach ((array)($a['full_days'] ?? []) as $d) { if (is_numeric($d) && (int)$d >= 0 && (int)$d <= 6) $days[(int)$d] = (int)$d; }
    ksort($days);
    return ['enabled' => !empty($a['enabled']) && $ok, 'hours' => $h, 'full_days' => array_values($days)];
}
/* true = AI boleh membalas sekarang (jadwal mati juga = true) */
function deiAiSchedActive($s = null, $ts = null) {
    $c = deiAiSchedConf($s);
    if (!$c['enabled']) return true;
    if (in_array((int)wibDate('w', $ts), $c['full_days'], true)) return true;
    return deiInHours($c['hours'], $ts);
}
function deiAiSchedInfo() {
    $c = deiAiSchedConf();
    return ['enabled' => $c['enabled'], 'active' => deiAiSchedActive(), 'hours' => $c['hours'],
            'full_days' => $c['full_days'], 'base_manual' => deiReplyModeBase() === 'manual'];
}
'''

s = rd(API)
assert NEED in s, 'v1.2.203 belum terpasang'
if TAG not in s:
    s = rep(s, "define('DEI_VERSION', 'v1.2.203');   // v1.2.203:",
            "define('DEI_VERSION', 'v1.2.204');   // " + TAG + " — Jam Aktif AI: AI membalas WhatsApp hanya pada jam tertentu, di luar itu ditangani agent; v1.2.203:", what='DEI_VERSION')
    s = rep(s, '/* v1.2.97: batas-ai — BATAS BALASAN AI per percakapan WhatsApp.', PHP_LIB + '/* v1.2.97: batas-ai — BATAS BALASAN AI per percakapan WhatsApp.', what='lib')
    s = rep(s, '''function deiReplyMode($s = null) {
    if ($s === null) {
        if (!isset($GLOBALS['dei_reply_mode_cache'])) {
            $GLOBALS['dei_reply_mode_cache'] = deiReplyMode(getSettings());
        }
        return $GLOBALS['dei_reply_mode_cache'];
    }''', '''// v1.2.204: jam-ai — mode efektif = mode dasar + jadwal jam AI
function deiReplyMode($s = null) {
    $m = deiReplyModeBase($s);
    if ($m === 'ai' && !deiAiSchedActive($s)) return 'manual';
    return $m;
}
function deiReplyModeBase($s = null) {
    if ($s === null) {
        if (!isset($GLOBALS['dei_reply_mode_cache'])) {
            $GLOBALS['dei_reply_mode_cache'] = deiReplyModeBase(getSettings());
        }
        return $GLOBALS['dei_reply_mode_cache'];
    }''', what='deiReplyMode')
    s = rep(s, "        unset($GLOBALS['dei_reply_mode_cache']);\n",
            "        unset($GLOBALS['dei_reply_mode_cache'], $GLOBALS['dei_ai_sched_cache']);   // " + TAG + "\n", what='unset save')
    s = rep(s, "unset($GLOBALS['dei_reply_mode_cache'], $GLOBALS['dei_features_cache']);",
            "unset($GLOBALS['dei_reply_mode_cache'], $GLOBALS['dei_features_cache'], $GLOBALS['dei_ai_sched_cache']);", what='unset worker')
    s = rep(s, "            if (isset($incoming['ai_limit']) && is_array($incoming['ai_limit'])) {   // v1.2.97: batas-ai",
            "            if (isset($incoming['ai_schedule']) && is_array($incoming['ai_schedule'])) {   // " + TAG + "\n"
            "                $merged['ai_schedule'] = deiMergeSettings($current['ai_schedule'] ?? [], $incoming['ai_schedule']);\n"
            "            }\n"
            "            if (isset($incoming['ai_limit']) && is_array($incoming['ai_limit'])) {   // v1.2.97: batas-ai", what='admin merge')
    s = rep(s, "        if (isset($merged['ai_limit']) && is_array($merged['ai_limit'])) $merged['ai_limit'] = deiAiLimitConf($merged);   // v1.2.97: batas-ai\n",
            "        if (isset($merged['ai_limit']) && is_array($merged['ai_limit'])) $merged['ai_limit'] = deiAiLimitConf($merged);   // v1.2.97: batas-ai\n"
            "        if (isset($merged['ai_schedule']) && is_array($merged['ai_schedule'])) $merged['ai_schedule'] = deiAiSchedConf($merged);   // " + TAG + "\n", what='normalize')
    s = rep(s, "            'reply_mode' => $isManual ? 'manual' : 'ai',\n",
            "            'reply_mode' => $isManual ? 'manual' : 'ai',\n            'ai_sched' => deiAiSchedInfo(),   // " + TAG + "\n", what='inbox')
    save(API, s)
else: print('sudah', API)

# ============================== JS ==============================
s = rd(JS)
if TAG not in s:
    s = rep(s, "      waState.replyMode = res.reply_mode || 'ai';   // v1.2.58\n",
            "      waState.replyMode = res.reply_mode || 'ai';   // v1.2.58\n      waState.aiSched = res.ai_sched || null;   // " + TAG + "\n", what='state')
    s = rep(s, "    cards.innerHTML =\n      (isManual ? '<div class=\"wa-mode-pill\">' + ico('user-round', 13) + ' Mode Manual — AI nonaktif, semua chat dibalas agent</div>' : '') +\n",
            "    var _as204 = waState.aiSched || {}, _asT204 = String(_as204.hours || '').replace('-', '–');   // " + TAG + "\n"
            "    var _asOff204 = isManual && _as204.enabled && !_as204.active && !_as204.base_manual;\n"
            "    cards.innerHTML =\n"
            "      (isManual ? '<div class=\"wa-mode-pill\">' + ico('user-round', 13) + (_asOff204 ? ' AI aktif ' + _asT204 + ' — sekarang di luar jam AI, semua chat dibalas agent' : ' Mode Manual — AI nonaktif, semua chat dibalas agent') + '</div>'\n"
            "        : (_as204.enabled ? '<div class=\"wa-mode-pill\" style=\"background:#dcfce7;color:#166534\">' + ico('bot', 13) + ' Jam AI ' + _asT204 + ' — sekarang AI yang membalas</div>' : '')) +\n", what='pill')
    s = rep(s, "      var al = res.settings.ai_limit || {};   // v1.2.97: batas-ai\n",
            r"""      if ($('#as_enabled')) {   // """ + TAG + r"""
        var as_ = res.settings.ai_schedule || {}, asH = String(as_.hours || '21:00-09:00').split('-');
        $('#as_enabled').checked = as_.enabled === true;
        $('#as_start').value = asH[0] || '21:00'; $('#as_end').value = asH[1] || '09:00';
        $$('#as_days input').forEach(function (c) { c.checked = (as_.full_days || []).indexOf(+c.value) >= 0; });
        var asNow = function () {
          var el = $('#as_now'); if (!el) return;
          if (!$('#as_enabled').checked) { el.textContent = 'Jadwal mati — AI membalas 24 jam (mengikuti Mode Balasan).'; return; }
          var w = new Date(Date.now() + 7 * 3600e3), m = w.getUTCHours() * 60 + w.getUTCMinutes(), d = w.getUTCDay();
          var p = function (v) { v = String(v || '').split(':'); return (+v[0] || 0) * 60 + (+v[1] || 0); };
          var a = p($('#as_start').value), b = p($('#as_end').value);
          var full = $$('#as_days input').some(function (c) { return c.checked && +c.value === d; });
          var on = full || a === b || (a < b ? (m >= a && m < b) : (m >= a || m < b));
          var hh = ('0' + w.getUTCHours()).slice(-2) + ':' + ('0' + w.getUTCMinutes()).slice(-2);
          el.innerHTML = 'Sekarang ' + hh + ' WIB: <b>' + (on ? 'AI yang membalas' : 'agent yang membalas (AI diam)') + '</b>' + (a === b ? ' — jam mulai &amp; sampai sama, AI aktif 24 jam.' : '.');
        };
        ['#as_enabled', '#as_start', '#as_end'].forEach(function (q) { $(q).onchange = asNow; });
        $$('#as_days input').forEach(function (c) { c.onchange = asNow; });
        asNow();
      }
      var al = res.settings.ai_limit || {};   // v1.2.97: batas-ai
""", what='load')
    s = rep(s, "      ai_limit: { max: Math.max(0, Math.min(50, Math.round(+$('#al_max').value || 0))), text: $('#al_text').value.trim() },   // v1.2.97: batas-ai\n",
            "      ai_limit: { max: Math.max(0, Math.min(50, Math.round(+$('#al_max').value || 0))), text: $('#al_text').value.trim() },   // v1.2.97: batas-ai\n"
            "      ai_schedule: $('#as_enabled') ? { enabled: $('#as_enabled').checked, hours: ($('#as_start').value || '21:00') + '-' + ($('#as_end').value || '09:00'),"
            " full_days: $$('#as_days input').filter(function (c) { return c.checked; }).map(function (c) { return +c.value; }) } : undefined,   // " + TAG + "\n", what='save')
    save(JS, s)
else: print('sudah', JS)
s = rd(JS)
if "id: 'jamai'" not in s:
    s = rep(s, "    { id: 'mode', roles: R_SA, t: 'Mengubah mode balasan WhatsApp (AI / Manual)',",
            "    { id: 'jamai', roles: R_ADM, t: 'Mengatur jam aktif AI (mis. AI malam, agent siang)', k: 'jam aktif ai jadwal timer malam siang jam kerja kantor agent shift luar jam operasional',   // " + TAG + "\n"
            "      s: ['Buka menu <b>Respon &amp; Eskalasi</b>.', 'Di kartu <b>Jam Aktif AI (WhatsApp)</b>, nyalakan jadwal dan isi jam AI aktif (mis. 21:00 sampai 09:00).', 'Di luar jam itu semua chat WhatsApp ditangani agent. Klik <b>Simpan</b>.'],\n"
            "      show: [{ tab: 'eskalasi', el: tourCard('eskalasi', 'Jam Aktif AI (WhatsApp)'), title: 'Jam Aktif AI', body: '<p>Atur kapan AI membalas.</p>' }] },\n"
            "    { id: 'mode', roles: R_SA, t: 'Mengubah mode balasan WhatsApp (AI / Manual)',", what='bantuan')
    save(JS, s)

# ============================== HTML ==============================
DAYS = [(1, 'Sen'), (2, 'Sel'), (3, 'Rab'), (4, 'Kam'), (5, 'Jum'), (6, 'Sab'), (0, 'Min')]
HT_CARD = '''      <!-- ''' + TAG + ''' -->
      <div class="card"><h3>Jam Aktif AI (WhatsApp)</h3>
        <div class="desc">AI hanya membalas WhatsApp pada jam di bawah (WIB). Di luar jam itu AI diam dan <b>semua chat ditangani agent</b> seperti Mode Manual: masuk antrean/routing, notifikasi &amp; eskalasi tetap berjalan. Saat jam AI dimulai, chat yang sedang di-claim agent tetap di agent sampai dilepas atau Selesai; chat lain dijawab AI pada pesan berikutnya.</div>
        <div class="toggle-row"><div><div class="tt">Aktifkan jadwal AI</div><div class="help">Mati = AI membalas 24 jam (mengikuti Mode Balasan).</div></div><label class="switch"><input type="checkbox" id="as_enabled"><span class="sl"></span></label></div>
        <div class="grid2">
          <div class="row"><label class="fl">AI aktif mulai</label><input type="time" id="as_start" value="21:00"></div>
          <div class="row"><label class="fl">AI aktif sampai</label><input type="time" id="as_end" value="09:00"><div class="help">Boleh melewati tengah malam, mis. 21:00 sampai 09:00.</div></div>
        </div>
        <div class="row"><label class="fl">AI aktif 24 jam pada hari (opsional)</label><div id="as_days" style="display:flex;gap:12px;flex-wrap:wrap">''' + ''.join(
    '<label style="display:inline-flex;gap:5px;align-items:center;font-weight:400;margin:0"><input type="checkbox" value="%d" style="width:auto;margin:0"> %s</label>' % d for d in DAYS) + '''</div><div class="help">Mis. centang Min bila tidak ada agent yang berjaga di hari Minggu.</div></div>
        <div class="help" id="as_now"></div>
      </div>

'''
s = rd(HT)
if TAG not in s:
    s = rep(s, '<script src="app.js?v=1.2.203"></script><!-- v1.2.203: sales-tag -->',
            '<script src="app.js?v=1.2.204"></script><!-- ' + TAG + ' --><!-- v1.2.203: sales-tag -->', what='app.js?v')
    s = rep(s, '      <!-- v1.2.97: batas-ai -->\n', HT_CARD + '      <!-- v1.2.97: batas-ai -->\n', what='card')
    save(HT, s)
else: print('sudah', HT)
s = rd(HT)
if 'input[type=date],input[type=time],' not in s:
    s = rep(s, 'input[type=text],input[type=password],input[type=number],input[type=date],select,textarea{',
            'input[type=text],input[type=password],input[type=number],input[type=date],input[type=time],select,textarea{', what='css')
    s = rep(s, '    input[type="url"],input[type="date"],textarea,select{', '    input[type="url"],input[type="date"],input[type="time"],textarea,select{', what='css hp')
    save(HT, s)
print('patch v1.2.204 selesai')
