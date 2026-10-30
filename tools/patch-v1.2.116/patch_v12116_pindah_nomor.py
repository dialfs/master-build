#!/usr/bin/env python3
"""v1.2.116 pindah-nomor: Admin/Supervisor memindah nomor bisnis pengirim sebuah chat (multi-nomor).
Jendela 24 jam Meta kini dihitung per nomor bisnis. Pakai: python3 patch_v12116_pindah_nomor.py [~/Herd/dei-tenant] (idempoten)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.116: pindah-nomor'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def patch(rel, edits):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    shutil.copy2(p, p + '.bak-v12116-' + STAMP)
    for old, new in edits:
        n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:80]); s = s.replace(old, new)
    assert TAG in s, rel; open(p, 'w', encoding='utf-8').write(s); print('OK', rel)

patch('api/index.php', [
 ("define('DEI_VERSION', 'v1.2.115');   // v1.2.115: login-aman",
  "define('DEI_VERSION', 'v1.2.116');   // v1.2.116: pindah-nomor"),
 # helper
 ("""function waContactSetCh($num, $ch) {""",
  """// v1.2.116: pindah-nomor — nomor bisnis aktif sebuah chat ('' = akun satu nomor).
function waCurCh($num, $s = null) {
    if ($s === null) $s = getSettings();
    if (!waMultiOn(waConf($s), $s)) return '';
    $c = null;
    try { $c = waContactGet(waNormNum($num)); } catch (\\Throwable $e) { error_log('waCurCh: ' . $e->getMessage()); }
    $ch = (string)(is_array($c) ? ($c['wa_ch'] ?? '') : '');
    foreach (waChannels($s) as $x) { if ($x['id'] === $ch) return $ch; }
    return 'utama';
}
// Meta: jendela 24 jam milik pasangan (pelanggan, nomor bisnis). '' = semua pesan masuk dihitung.
function waWinCh($num, $s = null) {
    if ($s === null) $s = getSettings();
    if ((string)(waConf($s)['provider'] ?? 'meta') !== 'meta') return '';
    return waCurCh($num, $s);
}
function waInboundOnCh($e, $ch) {
    if ($ch === '') return true;
    $x = (string)($e['wa_ch'] ?? '');
    return ($x === '' ? 'utama' : $x) === $ch;
}
function waContactSetCh($num, $ch) {"""),
 # wa_thread: window per nomor + ch saat ini
 ("""        deiGuardAgentPrivate($u, $num);   // v1.2.58
        $logs = logReadAll();
        $msgs = [];
        $lastInbound = 0;""",
  """        deiGuardAgentPrivate($u, $num);   // v1.2.58
        $logs = logReadAll();
        $msgs = [];
        $lastInbound = 0;
        $s116 = getSettings(); $curCh116 = waCurCh($num, $s116); $winCh116 = waWinCh($num, $s116);   // v1.2.116: pindah-nomor"""),
 ("""            if ($lastInbound === 0 && ($e['q'] ?? '') !== '') $lastInbound = strtotime($e['ts']);""",
  """            if ($lastInbound === 0 && ($e['q'] ?? '') !== '' && waInboundOnCh($e, $winCh116)) $lastInbound = strtotime($e['ts']);   // v1.2.116"""),
 ("""            'channels' => (function () { $s0 = getSettings(); return waMultiOn(waConf($s0), $s0) ? waChannels($s0) : []; })(),   // v1.2.98: multi-nomor
        ]);""",
  """            'channels' => (function () { $s0 = getSettings(); return waMultiOn(waConf($s0), $s0) ? waChannels($s0) : []; })(),   // v1.2.98: multi-nomor
            'ch' => $curCh116, 'win_per_ch' => $winCh116 !== '',   // v1.2.116: pindah-nomor
            'wa_prov' => (string)(waConf($s116)['provider'] ?? 'meta'),
        ]);"""),
 # wa_reply: window per nomor
 ("""        $logs = logReadAll();
        $lastInbound = 0;
        foreach ($logs as $e) {
            if (($e['channel'] ?? '') === 'whatsapp' && waNormNum($e['ip'] ?? '') === $num && ($e['q'] ?? '') !== '') {""",
  """        $logs = logReadAll();
        $lastInbound = 0;
        $winCh116 = waWinCh($num, $s);   // v1.2.116: pindah-nomor — jendela Meta per nomor bisnis
        foreach ($logs as $e) {
            if (($e['channel'] ?? '') === 'whatsapp' && waNormNum($e['ip'] ?? '') === $num && ($e['q'] ?? '') !== '' && waInboundOnCh($e, $winCh116)) {"""),
 ("""            if (!waWindowSelaluTerbuka()) jsonOut(['ok' => false, 'error' => 'Jendela 24 jam tertutup — WhatsApp tidak mengizinkan balasan teks bebas. Pelanggan harus mengirim pesan lagi terlebih dulu.'], 409);
        }

        $GLOBALS['dei_out_src'] = 'agent';""",
  """            if (!waWindowSelaluTerbuka()) jsonOut(['ok' => false, 'error' => 'Jendela 24 jam tertutup' . ($winCh116 !== '' ? ' untuk nomor ini' : '') . ' — WhatsApp tidak mengizinkan balasan teks bebas. Pelanggan harus mengirim pesan lagi terlebih dulu' . ($winCh116 !== '' ? ' ke nomor ini (atau kirim template lewat Blast dari nomor ini).' : '.')], 409);
        }

        $GLOBALS['dei_out_src'] = 'agent';"""),
 # endpoint
 ("""    case 'team_info': {""",
  """    case 'wa_set_ch': {   // v1.2.116: pindah-nomor — ganti nomor bisnis pengirim chat
        $u = requireAuth(['super_admin', 'admin', 'supervisor']);
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        $ch = trim((string)($in['ch'] ?? ''));
        if ($num === '' || $ch === '') jsonOut(['ok' => false, 'error' => 'number & ch wajib'], 400);
        $s = getSettings();
        if (!waMultiOn(waConf($s), $s)) jsonOut(['ok' => false, 'error' => 'Akun ini hanya punya satu nomor WhatsApp.'], 409);
        $lab = [];
        foreach (waChannels($s) as $x) $lab[$x['id']] = $x['label'];
        if (!isset($lab[$ch])) jsonOut(['ok' => false, 'error' => 'Nomor tujuan tidak ditemukan atau di luar paket.'], 404);
        deiGuardSpvScope($u, $num);
        $from = waCurCh($num, $s);
        if ($from === $ch) jsonOut(['ok' => true, 'number' => $num, 'ch' => $ch, 'label' => $lab[$ch], 'note' => 'Chat sudah di nomor ini']);
        waContactUpdate($num, function (&$r) use ($ch) { $r['wa_ch'] = $ch; });
        waAuditLog('ch_move', $u['username'], $num, ['from_ch' => $from, 'to_ch' => $ch]);
        $agent = '';
        if (!waClaimGet($num) && (deiIsManual($s) || waGetMode($num) === 'human')) $agent = (string)deiRouteAssign($num, $ch, $s);
        jsonOut(['ok' => true, 'number' => $num, 'ch' => $ch, 'from_ch' => $from, 'label' => $lab[$ch], 'agent' => $agent]);
        break;
    }

    case 'team_info': {"""),
])

patch('dashboard/chatbot-ai/app.js', [
 ("""      actionBtns += '<span class="wa-assign">' + ico('user-round',13) + '<select id="waAssignSel">' + _opsi + '</select></span>';
    }""",
  """      actionBtns += '<span class="wa-assign">' + ico('user-round',13) + '<select id="waAssignSel">' + _opsi + '</select></span>';
    }
    // v1.2.116: pindah-nomor — Admin/Supervisor memindah nomor bisnis pengirim chat
    var _chs116 = res.channels || [], _cur116 = res.ch || 'utama';
    if (waState.isAdmin && _chs116.length > 1) {
      actionBtns += '<span class="wa-assign" title="Balasan berikutnya (agent & bot) dikirim dari nomor yang dipilih">' + ico('phone',13) +
        '<select id="waChMoveSel"><option value="">Pindah ke nomor…</option>' +
        _chs116.filter(function (c) { return c.id !== _cur116; }).map(function (c) {
          var t = c.label + ((c.number && c.label !== '+' + c.number) ? ' (+' + c.number + ')' : '');
          return '<option value="' + esc(c.id) + '">' + esc(t) + '</option>';
        }).join('') + '</select></span>';
    }"""),
 ("""    if (_konv && _konv.ch_label && (res.channels || []).length > 1) _judulThread +=""",
  """    if ((res.channels || []).length > 1 && res.ch) { (res.channels || []).forEach(function (c) { if (c.id === res.ch && _konv) _konv.ch_label = c.label; }); }   // v1.2.116: label dari nomor terkini
    if (_konv && _konv.ch_label && (res.channels || []).length > 1) _judulThread +="""),
 ("""    if ($('#waAssignSel')) $('#waAssignSel').onchange = function () { assignNumber(num, this.value, this); };   // v1.2.58""",
  """    if ($('#waAssignSel')) $('#waAssignSel').onchange = function () { assignNumber(num, this.value, this); };   // v1.2.58
    if ($('#waChMoveSel')) $('#waChMoveSel').onchange = function () { moveWaChan(num, this.value, this, res.wa_prov); };   // v1.2.116"""),
 ("""  function releaseNumber(num) {""",
  """  // v1.2.116: pindah-nomor
  function moveWaChan(num, ch, sel, prov) {
    if (!ch) return;
    var label = sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].text : ch;
    var msg = 'Pindahkan chat ini ke nomor ' + label + '?\\n\\nBalasan berikutnya (agent & bot) dikirim dari nomor itu. Jika pelanggan masih membalas ke nomor lama, chat otomatis kembali ke nomor lama.';
    if (prov === 'meta') msg += '\\n\\nWhatsApp API resmi: nomor baru belum punya jendela 24 jam dengan pelanggan ini. Kirim template dulu lewat Blast dari nomor itu; balasan teks bebas aktif setelah pelanggan membalas.';
    if (!confirm(msg)) { sel.value = ''; return; }
    api('wa_set_ch', { method: 'POST', body: { number: num, ch: ch } }).then(function (res) {
      if (res && res.ok) {
        toast(res.note || ('Chat dipindah ke ' + (res.label || label) + (res.agent ? ' · diserahkan ke ' + res.agent : '') + '.'));
        fetchWaConvs().then(function () { fetchWaThread(num); });
      } else { toast((res && res.error) || 'Gagal memindah nomor.', true); sel.value = ''; }
    });
  }

  function releaseNumber(num) {"""),
 ("""      : ico('triangle-alert',13) + ' Jendela 24 jam tertutup — WhatsApp tidak mengizinkan balasan teks bebas sampai pelanggan mengirim pesan lagi.';""",
  """      : ico('triangle-alert',13) + ' Jendela 24 jam tertutup' + (res.win_per_ch ? ' untuk nomor ini' : '') + ' — WhatsApp tidak mengizinkan balasan teks bebas sampai pelanggan mengirim pesan lagi' + (res.win_per_ch ? ' ke nomor ini. Kirim template lewat Blast dari nomor ini.' : '.');   // v1.2.116"""),
])

patch('dashboard/chatbot-ai/index.html', [
 ("""<script src="app.js?v=1.2.114"></script><!-- v1.2.114: kontak-jumlah -->""",
  """<script src="app.js?v=1.2.116"></script><!-- v1.2.116: pindah-nomor -->"""),
])
