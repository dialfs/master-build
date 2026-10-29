#!/usr/bin/env python3
"""v1.2.108: tolak-telepon — telepon WA masuk (WAHA event call.received):
tolak otomatis per nomor (selalu / di luar jam operasional) + pesan balasan yang bisa diedit,
dan setiap telepon masuk dicatat di log (Percakapan WA + Log).
Pakai: python3 patch_v12108_tolak_telepon.py ~/Herd   (idempoten)"""
import sys, os, shutil, time
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd'); T = H + '/dei-tenant'
TAG = 'v1.2.108: tolak-telepon'
stamp = time.strftime('%Y%m%d-%H%M%S')

PHP_FUNCS = r'''/* ''' + TAG + r''' — telepon WhatsApp masuk (WAHA event call.received).
 * WAHA (WhatsApp Web) tidak bisa mengangkat telepon; HP tetap berdering sebentar.
 * Per nomor bisnis (ch) bisa diatur: tolak otomatis (selalu / hanya di luar jam operasional WIB)
 * + pesan balasan. Semua telepon masuk dicatat di log (dir=call) -> Percakapan WA & Log.
 * Pengaturan: data/wa-calls.json {ch: {...}}. Anti-dobel & jeda balasan: data/wa-calls-seen.json.
 * Sesi lama perlu webhook baru (WA_HEALTH_CFG_V 3): dipasang otomatis jam 01–04 WIB / tombol di panel. */
if (!defined('WA_CALLS_FILE')) define('WA_CALLS_FILE', DATA_DIR . '/wa-calls.json');
if (!defined('WA_CALLS_SEEN_FILE')) define('WA_CALLS_SEEN_FILE', DATA_DIR . '/wa-calls-seen.json');
if (!defined('WA_CALL_REPLY_GAP')) define('WA_CALL_REPLY_GAP', 600);   // telepon beruntun: pesan balasan maks 1x / 10 menit / nomor
function wcDefaults() {
    return ['on' => false, 'when' => 'always', 'days' => [1, 2, 3, 4, 5, 6], 'start' => '08:00', 'end' => '17:00',
            'reply_on' => true,
            'msg' => "Mohon maaf, nomor ini hanya melayani chat dan tidak dapat menerima telepon. Silakan ketik pertanyaan Anda di sini, kami bantu segera \xF0\x9F\x99\x8F"];
}
function wcClean($in) {
    $d = wcDefaults();
    $o = ['on' => !empty($in['on']), 'when' => (($in['when'] ?? '') === 'hours') ? 'hours' : 'always'];
    $days = [];
    foreach ((array)($in['days'] ?? []) as $x) { $x = (int)$x; if ($x >= 1 && $x <= 7) $days[$x] = $x; }
    ksort($days);
    $o['days'] = array_values($days);
    foreach (['start', 'end'] as $k) {
        $v = trim((string)($in[$k] ?? $d[$k]));
        $o[$k] = preg_match('/^([01]\d|2[0-3]):[0-5]\d$/', $v) ? $v : $d[$k];
    }
    $o['reply_on'] = !empty($in['reply_on']);
    $o['msg'] = mb_substr(trim(str_replace("\r", '', (string)($in['msg'] ?? ''))), 0, 1000);
    return $o;
}
function wcConf($ch) {
    $all = readJson(WA_CALLS_FILE, []);
    $c = (is_array($all) && is_array($all[$ch] ?? null)) ? $all[$ch] : [];
    return array_replace(wcDefaults(), $c);
}
function wcSave($ch, $conf) {
    deiWithLock('wa-calls', function () use ($ch, $conf) {
        $all = readJson(WA_CALLS_FILE, []);
        if (!is_array($all)) $all = [];
        $all[$ch] = $conf;
        writeJson(WA_CALLS_FILE, $all);
    });
}
// Di dalam jam operasional (WIB)? Mulai = selesai -> 24 jam di hari terpilih.
// Rentang lewat tengah malam (mis. 22:00–06:00) ikut hari mulainya.
function wcInHours($c, $ts = null) {
    $ts = $ts ?? time();
    $days = array_map('intval', (array)($c['days'] ?? []));
    $now = wibDate('H:i', $ts); $st = (string)($c['start'] ?? '08:00'); $en = (string)($c['end'] ?? '17:00');
    $today = in_array((int)wibDate('N', $ts), $days, true);
    if ($st === $en) return $today;
    if ($st < $en) return $today && $now >= $st && $now < $en;
    if ($now >= $st) return $today;
    if ($now < $en) return in_array((int)wibDate('N', $ts - 86400), $days, true);
    return false;
}
// [tolak?, alasan: off | always | in_hours | outside_hours]
function wcDecide($c, $ts = null) {
    if (empty($c['on'])) return [false, 'off'];
    if (($c['when'] ?? 'always') !== 'hours') return [true, 'always'];
    return wcInHours($c, $ts) ? [false, 'in_hours'] : [true, 'outside_hours'];
}
// Teks tampilan entri log telepon ('' bila bukan telepon).
function wcLabel($e) {
    if ((string)($e['dir'] ?? '') !== 'call' || !is_array($e['call'] ?? null)) return '';
    $k = $e['call'];
    $t = "\xF0\x9F\x93\x9E Telepon " . (!empty($k['video']) ? 'video' : 'suara') . ' masuk';
    $act = (string)($k['act'] ?? '');
    if ($act === 'rejected') $t .= " \xE2\x80\x94 ditolak otomatis" . (($k['why'] ?? '') === 'outside_hours' ? ' (di luar jam operasional)' : '');
    elseif ($act === 'reject_failed') $t .= " \xE2\x80\x94 gagal ditolak otomatis";
    elseif (($k['why'] ?? '') === 'in_hours') $t .= " \xE2\x80\x94 jam operasional, tidak ditolak";
    return $t;
}
// Jejak kecil berkunci: $fn(&$all) mengubah isi, nilai kembali diteruskan. Entri > 24 jam dibuang.
function wcSeen($fn) {
    return deiWithLock('wa-calls-seen', function () use ($fn) {
        $all = readJson(WA_CALLS_SEEN_FILE, []);
        if (!is_array($all)) $all = [];
        $now = time();
        foreach ($all as $k => $t) { if ((int)$t < $now - 86400) unset($all[$k]); }
        $r = $fn($all);
        if (count($all) > 3000) $all = array_slice($all, -3000, null, true);
        writeJson(WA_CALLS_SEEN_FILE, $all);
        return $r;
    });
}
function wcHandle($wa, $evt) {
    $p = is_array($evt['payload'] ?? null) ? $evt['payload'] : [];
    if (!empty($p['isGroup'])) return 'group';
    $id = trim((string)($p['id'] ?? '')); $from = trim((string)($p['from'] ?? ''));
    if ($id === '' || $from === '') return 'bad';
    $ch = whCh($wa);
    $first = wcSeen(function (&$all) use ($ch, $id) {
        $k = 'c' . $ch . ':' . $id;
        if (isset($all[$k])) return false;
        $all[$k] = time();
        return true;
    });
    if (!$first) return 'dup';
    whUpdate($ch, function (&$d) { if (!empty($d['call_on'])) return false; $d['call_on'] = time(); });   // langganan call.received terbukti aktif
    $num = wahaResolveNum($wa, $from, $p);
    $c = wcConf($ch);
    list($reject, $why) = wcDecide($c);
    $act = 'none'; $sent = '';
    if ($reject) {
        list($code, $d) = wahaApi($wa, 'POST', '/api/' . rawurlencode(wahaSession($wa)) . '/calls/reject', ['from' => $from, 'id' => $id]);
        $act = ($code >= 200 && $code < 300) ? 'rejected' : 'reject_failed';
        if ($act !== 'rejected') error_log('waha: tolak telepon gagal HTTP ' . $code . ': ' . wahaErr($code, $d));
        $msg = trim((string)($c['msg'] ?? ''));
        if (!empty($c['reply_on']) && $msg !== '' && $num !== '' && empty($GLOBALS['dei_dry'])) {
            $go = wcSeen(function (&$all) use ($ch, $num) {
                $k = 'r' . $ch . ':' . $num;
                if ((int)($all[$k] ?? 0) > time() - WA_CALL_REPLY_GAP) return false;
                $all[$k] = time();
                return true;
            });
            if ($go) {
                $GLOBALS['dei_out_src'] = 'bot';
                if (waSendWaha($wa, $num, $msg)) $sent = $msg;
            }
        }
    }
    if ($num === '') { error_log('waha: telepon masuk, nomor tidak terbaca (' . mb_substr($from, 0, 40) . ')'); return $act; }
    $row = ['ts' => date('Y-m-d H:i:s'), 'q' => '', 'a' => $sent, 'ip' => $num, 'channel' => 'whatsapp', 'dir' => 'call',
            'call' => ['video' => !empty($p['isVideo']), 'act' => $act, 'why' => $why],
            'utm_source' => 'whatsapp', 'utm_medium' => 'call', 'utm_campaign' => '', 'page' => '', 'referrer' => ''];
    if (!empty($wa['_ch'])) $row['wa_ch'] = (string)$wa['_ch'];
    try { $s = getSettings(); logPrepend($row, (int)($s['api']['log_limit'] ?? 500)); }
    catch (\Throwable $e) { error_log('log telepon: ' . $e->getMessage()); }
    return $act;
}
/* ====== /''' + TAG + r''' ====== */

'''

PHP_ACTION = r'''    /* ---------- ''' + TAG + r''' — pengaturan tolak telepon per nomor (WAHA) ---------- */
    case 'wa_calls': {
        $u  = requireAuth(['super_admin', 'admin', 'supervisor']);
        $in = bodyInput();
        $op = (string)($in['op'] ?? ($_GET['op'] ?? 'get'));
        $s  = getSettings();
        $wa = waConf($s);
        if (!whOn($wa)) jsonOut(['ok' => false, 'error' => 'Tolak telepon otomatis khusus penyedia WAHA.'], 400);
        $ch = preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['ch'] ?? ($_GET['ch'] ?? 'utama')));
        $label = ''; $found = false;
        foreach (whChannels($s) as $c) { if ($c[0] === $ch) { $found = true; $label = $c[1]; } }
        if (!$found) jsonOut(['ok' => false, 'error' => 'Nomor tidak ditemukan atau terkunci.'], 404);
        $canEdit = in_array(($u['role'] ?? ''), ['super_admin', 'admin'], true);
        if ($op === 'save') {
            if (!$canEdit) jsonOut(['ok' => false, 'error' => 'Khusus Super Admin / Admin.'], 403);
            $c = wcClean(is_array($in['conf'] ?? null) ? $in['conf'] : []);
            if ($c['on'] && $c['when'] === 'hours' && !$c['days']) jsonOut(['ok' => false, 'error' => 'Pilih minimal satu hari operasional.'], 400);
            if ($c['on'] && $c['reply_on'] && $c['msg'] === '') jsonOut(['ok' => false, 'error' => 'Pesan balasan masih kosong.'], 400);
            wcSave($ch, $c);
            try { waAuditLog('wa_calls_set', $u['username'], '', ['ch' => $ch, 'on' => $c['on'], 'when' => $c['when']]); } catch (\Throwable $e) {}
            list($rej, $why) = wcDecide($c);
            jsonOut(['ok' => true, 'conf' => $c, 'now_reject' => $rej, 'now_why' => $why]);
        }
        $recent = [];
        foreach (logReadAll() as $e) {
            if ((string)($e['dir'] ?? '') !== 'call' || ($e['channel'] ?? '') !== 'whatsapp') continue;
            $ech = (string)($e['wa_ch'] ?? '');
            if (($ech === '' ? 'utama' : $ech) !== $ch) continue;
            $recent[] = ['ts' => (string)($e['ts'] ?? ''), 'num' => (string)($e['ip'] ?? ''), 'txt' => wcLabel($e), 'replied' => (string)($e['a'] ?? '') !== ''];
            if (count($recent) >= 10) break;
        }
        $d = whRead($ch);
        $conf = wcConf($ch);
        list($rej, $why) = wcDecide($conf);
        jsonOut(['ok' => true, 'label' => $label, 'can_edit' => $canEdit, 'conf' => $conf,
                 'cfg_ok' => (int)($d['cfg_v'] ?? 0) >= WA_HEALTH_CFG_V || !empty($d['call_on']),
                 'now_reject' => $rej, 'now_why' => $why, 'recent' => $recent]);
        break;
    }

'''

JS_FUNCS = r'''  /* ''' + TAG + r''' — panel "Telepon masuk" per nomor (WAHA) */
  var WC_DAYS = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min'];
  function wcNowTxt(r) {
    if (r.now_reject) return 'Saat ini telepon masuk <b>ditolak otomatis</b>' + (r.now_why === 'outside_hours' ? ' (di luar jam operasional).' : '.');
    if (r.now_why === 'in_hours') return 'Saat ini jam operasional: telepon <b>tidak ditolak</b> (HP berdering seperti biasa).';
    return 'Tolak otomatis <b>mati</b>: telepon hanya dicatat, HP berdering seperti biasa.';
  }
  function wcOpen(row) {
    var box = $('#wn_call'); if (!box || !row) return;
    box.classList.remove('hide');
    box.innerHTML = '<div class="help">Memuat…</div>';
    api('wa_calls', { query: '&ch=' + encodeURIComponent(row.id) }).then(function (r) {
      if (!r || !r.ok) { box.innerHTML = '<div class="help">' + esc((r && r.error) || 'Gagal memuat.') + '</div>'; return; }
      var c = r.conf || {}, ed = !!r.can_edit, dis = ed ? '' : ' disabled';
      var days = (c.days || []).map(Number);
      var dayH = WC_DAYS.map(function (n, i) {
        var v = i + 1;
        return '<label style="display:inline-flex;align-items:center;gap:4px;margin:0 12px 4px 0;font-weight:400"><input type="checkbox" class="wc_day" value="' + v + '"' + (days.indexOf(v) >= 0 ? ' checked' : '') + dis + '> ' + n + '</label>';
      }).join('');
      var rec = (r.recent || []).map(function (x) {
        return '<li><span class="mono">' + esc(String(x.ts).slice(5, 16)) + '</span> · +' + esc(x.num) + ' — ' + esc(String(x.txt).replace(/^\S+\s/, '')) + (x.replied ? ' · <span style="color:#166534">pesan terkirim</span>' : '') + '</li>';
      }).join('');
      box.innerHTML =
        '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px"><b>' + ico('phone', 15, 'style="vertical-align:-2px"') + ' Telepon masuk — ' + esc(r.label) + '</b>' +
          '<button class="btn ghost sm" type="button" id="wc_close" style="margin-left:auto">Tutup</button></div>' +
        '<div class="help" style="margin-top:0">WAHA tidak bisa mengangkat telepon. Telepon yang ditolak otomatis tetap berdering sebentar di HP, lalu putus di sisi penelepon. Semua telepon masuk tercatat di Percakapan WA &amp; Log.</div>' +
        (!r.cfg_ok ? '<div class="help" style="background:#fef3c7;color:#92400e;padding:8px 10px;border-radius:8px">Sesi ini belum menerima event telepon dari WAHA. Dipasang otomatis jam 01–04 WIB, atau ' +
          (ed ? '<a href="#" id="wc_cfg">pasang sekarang</a> (sesi WAHA restart beberapa detik).' : 'minta Admin memasangnya.') + '</div>' : '') +
        '<div class="help" id="wc_now" style="background:var(--soft,#f4f5f9);padding:8px 10px;border-radius:8px">' + wcNowTxt(r) + '</div>' +
        '<div class="row"><label style="display:flex;align-items:center;gap:8px;font-weight:600"><input type="checkbox" id="wc_on"' + (c.on ? ' checked' : '') + dis + '> Tolak telepon otomatis</label></div>' +
        '<div id="wc_opts">' +
          '<div class="row"><label class="fl">Kapan ditolak</label>' +
            '<label style="display:flex;align-items:center;gap:6px;font-weight:400"><input type="radio" name="wc_when" value="always"' + (c.when !== 'hours' ? ' checked' : '') + dis + '> Selalu</label>' +
            '<label style="display:flex;align-items:center;gap:6px;font-weight:400"><input type="radio" name="wc_when" value="hours"' + (c.when === 'hours' ? ' checked' : '') + dis + '> Hanya di luar jam operasional</label></div>' +
          '<div class="row" id="wc_hours"><label class="fl">Jam operasional (WIB)</label><div>' + dayH + '</div>' +
            '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:4px"><input type="time" id="wc_start" value="' + esc(c.start || '08:00') + '" style="max-width:130px"' + dis + '> s/d <input type="time" id="wc_end" value="' + esc(c.end || '17:00') + '" style="max-width:130px"' + dis + '></div>' +
            '<div class="help">Di dalam jam ini telepon dibiarkan berdering (CS bisa mengangkat dari HP). Jam selesai lebih kecil dari jam mulai = lewat tengah malam.</div></div>' +
          '<div class="row"><label style="display:flex;align-items:center;gap:8px;font-weight:400"><input type="checkbox" id="wc_reply"' + (c.reply_on ? ' checked' : '') + dis + '> Kirim pesan setelah menolak</label>' +
            '<textarea id="wc_msg" rows="3" style="width:100%;margin-top:6px"' + dis + '>' + esc(c.msg || '') + '</textarea>' +
            '<div class="help">Dikirim maksimal sekali per 10 menit ke nomor yang sama (telepon beruntun tidak memicu pesan berulang).</div></div>' +
        '</div>' +
        (ed ? '<div style="display:flex;gap:8px"><button class="btn sm" type="button" id="wc_save">Simpan</button></div>' : '') +
        '<h4 style="margin:14px 0 4px">Telepon terakhir</h4>' +
        (rec ? '<ul style="margin:0;padding-left:18px;font-size:12.5px">' + rec + '</ul>' : '<div class="help">Belum ada telepon masuk tercatat.</div>');
      var sync = function () {
        var on = $('#wc_on').checked, hrs = (box.querySelector('input[name="wc_when"]:checked') || {}).value === 'hours';
        $('#wc_opts').style.opacity = on ? '' : '.55';
        $('#wc_hours').style.display = hrs ? '' : 'none';
        $('#wc_msg').style.display = $('#wc_reply').checked ? '' : 'none';
      };
      box.querySelectorAll('#wc_on,#wc_reply,input[name="wc_when"]').forEach(function (el) { el.onchange = sync; });
      sync();
      $('#wc_close').onclick = function () { box.classList.add('hide'); };
      var cf = $('#wc_cfg');
      if (cf) cf.onclick = function (e) {
        e.preventDefault();
        if (!confirm('Pasang ulang webhook sesi ini? Sesi WAHA restart beberapa detik (pesan masuk saat itu tetap diterima setelah tersambung).')) return;
        api('wa_health', { method: 'POST', body: { op: 'apply_cfg', ch: row.id } }).then(function (x) { if (x && x.ok) { toast('Webhook terpasang.'); wcOpen(row); } else toast((x && x.error) || 'Gagal.', true); });
      };
      var sv = $('#wc_save');
      if (sv) sv.onclick = function () {
        var conf = {
          on: $('#wc_on').checked,
          when: (box.querySelector('input[name="wc_when"]:checked') || {}).value || 'always',
          days: Array.prototype.map.call(box.querySelectorAll('.wc_day:checked'), function (x) { return +x.value; }),
          start: $('#wc_start').value, end: $('#wc_end').value,
          reply_on: $('#wc_reply').checked, msg: $('#wc_msg').value
        };
        sv.disabled = true;
        api('wa_calls', { method: 'POST', body: { op: 'save', ch: row.id, conf: conf } }).then(function (x) {
          sv.disabled = false;
          if (x && x.ok) { toast('Pengaturan telepon disimpan.'); $('#wc_now').innerHTML = wcNowTxt(x); }
          else toast((x && x.error) || 'Gagal menyimpan.', true);
        }).catch(function () { sv.disabled = false; });
      };
    });
  }
'''

JS_PILL = r'''  function waCallPill(txt, ts, chl) {   // ''' + TAG + r'''
    var t = /\d{2}:\d{2}/.exec(String(ts || '').slice(11)) || [''];
    return '<div style="display:flex;justify-content:center;margin:8px 0">' +
           '<span style="background:#e0f2fe;color:#075985;font-size:12px;padding:5px 12px;border-radius:12px;max-width:85%;text-align:center">' +
           esc(txt) + (t[0] ? ' · ' + esc(t[0]) : '') + (chl ? ' · ' + esc(chl) : '') + '</span></div>';
  }
'''

P = {
 'api/index.php': [
  ("define('DEI_VERSION', 'v1.2.107');   // v1.2.107: db-import-percakapan",
   "define('DEI_VERSION', 'v1.2.108');   // " + TAG),
  ("'events'  => ['message.any', 'session.status', 'message.ack'],   // v1.2.104: skor-risiko-wa (centang)",
   "'events'  => ['message.any', 'session.status', 'message.ack', 'call.received'],   // v1.2.104: skor-risiko-wa (centang); " + TAG),
  ("define('WA_HEALTH_CFG_V', 2);   // 2 = webhook berlangganan message.ack",
   "define('WA_HEALTH_CFG_V', 3);   // 2 = webhook berlangganan message.ack; 3 = + call.received (" + TAG + ")"),
  ("        if ((int)($d['cfg_v'] ?? 0) >= WA_HEALTH_CFG_V || !empty($d['ack_on'])) continue;",
   "        if ((int)($d['cfg_v'] ?? 0) >= WA_HEALTH_CFG_V || !empty($d['call_on'])) continue;   // " + TAG + " (sesi v2 dipasang ulang sekali)"),
  ("function waSendWaha($wa, $to, $text) {\n",
   PHP_FUNCS + "function waSendWaha($wa, $to, $text) {\n"),
  ("        if ((string)($evt['event'] ?? '') === 'message.ack') { whAck($wa, is_array($evt['payload'] ?? null) ? $evt['payload'] : []); echo 'OK'; exit; }\n",
   "        if ((string)($evt['event'] ?? '') === 'message.ack') { whAck($wa, is_array($evt['payload'] ?? null) ? $evt['payload'] : []); echo 'OK'; exit; }\n"
   "        if ((string)($evt['event'] ?? '') === 'call.received') { try { wcHandle($wa, $evt); } catch (\\Throwable $e) { error_log('telepon: ' . $e->getMessage()); } echo 'OK'; exit; }   // " + TAG + "\n"),
  ("    if ($d === 'closing') return 'closing';\n",
   "    if ($d === 'closing') return 'closing';\n    if ($d === 'call')    return 'call';   // " + TAG + "\n"),
  ("in_array($st, ['ai', 'awaiting', 'manual', 'closing', 'error'], true) ? $st : '',",
   "in_array($st, ['ai', 'awaiting', 'manual', 'closing', 'error', 'call'], true) ? $st : '',   // " + TAG),
  ("'closing' => 'Closing otomatis', 'error' => 'Gagal / error'][$st] ?? $st;",
   "'closing' => 'Closing otomatis', 'error' => 'Gagal / error', 'call' => 'Telepon masuk'][$st] ?? $st;   // " + TAG),
  ("                'a'        => mb_substr((string)($e['a'] ?? ''), 0, 6000),\n                'who'      => (string)($e['ip'] ?? ''),\n",
   "                'a'        => mb_substr((string)($e['a'] ?? ''), 0, 6000),\n                'call_txt' => wcLabel($e),   // " + TAG + "\n                'who'      => (string)($e['ip'] ?? ''),\n"),
  ("                       'ch' => (string)($e['wa_ch'] ?? '')];   // v1.2.98: multi-nomor\n",
   "                       'call_txt' => wcLabel($e),   // " + TAG + "\n                       'ch' => (string)($e['wa_ch'] ?? '')];   // v1.2.98: multi-nomor\n"),
  ("                    'last_text'       => ($e['q'] ?? '') !== '' ? $e['q'] : ($e['a'] ?? ''),\n",
   "                    'last_text'       => ($e['q'] ?? '') !== '' ? $e['q'] : (wcLabel($e) !== '' ? wcLabel($e) : ($e['a'] ?? '')),   // " + TAG + "\n"),
  ("    case 'wa_health': {\n", PHP_ACTION + "    case 'wa_health': {\n"),
 ],
 'dashboard/chatbot-ai/index.html': [
  ('<script src="app.js?v=1.2.106"></script><!-- v1.2.106: kontak-sinkron -->',
   '<script src="app.js?v=1.2.108"></script><!-- ' + TAG + ' -->'),
  ("  .lg-st.closing{background:#f0f0f4;color:var(--muted)}\n",
   "  .lg-st.closing{background:#f0f0f4;color:var(--muted)}\n  .lg-st.call{background:#e0f2fe;color:#075985}/* " + TAG + " */\n"),
  ('<div id="wn_health" class="hide" style="border:1px solid var(--line,#e6e6ef);border-radius:10px;padding:14px;margin-top:10px"></div><!-- v1.2.104: skor-risiko-wa -->',
   '<div id="wn_health" class="hide" style="border:1px solid var(--line,#e6e6ef);border-radius:10px;padding:14px;margin-top:10px"></div><!-- v1.2.104: skor-risiko-wa -->\n'
   '        <div id="wn_call" class="hide" style="border:1px solid var(--line,#e6e6ef);border-radius:10px;padding:14px;margin-top:10px"></div><!-- ' + TAG + ' -->'),
 ],
 'dashboard/chatbot-ai/app.js': [
  ("error: ['Gagal / error', '#dc2626'] };",
   "error: ['Gagal / error', '#dc2626'], call: ['Telepon masuk', '#0891b2'] };   // " + TAG),
  ("(r.q ? esc(r.q.slice(0, 220)) : '<i style=\"opacity:.6\">(tanpa pesan)</i>')",
   "(r.q ? esc(r.q.slice(0, 220)) : (r.call_txt ? esc(r.call_txt) : '<i style=\"opacity:.6\">(tanpa pesan)</i>'))"),
  ("      (r.q ? '<div class=\"lg-bub q\"><small>Pengunjung</small>' + esc(r.q) + '</div>' : '') +\n",
   "      (r.q ? '<div class=\"lg-bub q\"><small>Pengunjung</small>' + esc(r.q) + '</div>' : '') +\n"
   "      (r.call_txt ? '<div class=\"lg-bub q\"><small>Telepon</small>' + esc(r.call_txt) + '</div>' : '') +   // " + TAG + "\n"),
  ("(r.status === 'closing' ? 'Pesan closing' : 'Jawaban AI')",
   "(r.status === 'closing' ? 'Pesan closing' : (r.status === 'call' ? 'Pesan balasan telepon' : 'Jawaban AI'))"),
  ("  function waDateSepHtml(label) {\n", JS_PILL + "  function waDateSepHtml(label) {\n"),
  ("      if (m.q) h += waBubble(m.q, 'in', m.ts, m.media, (_chMulti && m.ch) ? (_chL[m.ch] || '') : '');",
   "      if (m.call_txt) h += waCallPill(m.call_txt, m.ts, (_chMulti && m.ch) ? (_chL[m.ch] || '') : '');   // " + TAG + "\n"
   "      if (m.q) h += waBubble(m.q, 'in', m.ts, m.media, (_chMulti && m.ch) ? (_chL[m.ch] || '') : '');"),
  ("          if (waha && x.id !== 'utama') acts += '<button class=\"btn ghost sm\" type=\"button\" data-wn=\"qr\" data-id=\"' + esc(x.id) + '\">Koneksi</button> ';\n",
   "          if (waha && x.id !== 'utama') acts += '<button class=\"btn ghost sm\" type=\"button\" data-wn=\"qr\" data-id=\"' + esc(x.id) + '\">Koneksi</button> ';\n"
   "          if (waha && !x.locked) acts += '<button class=\"btn ghost sm\" type=\"button\" data-wn=\"call\" data-id=\"' + esc(x.id) + '\" title=\"Tolak telepon otomatis\">Telepon</button> ';   // " + TAG + "\n"),
  ("        else if (b.dataset.wn === 'health') whOpen(row);   // v1.2.104\n",
   "        else if (b.dataset.wn === 'health') whOpen(row);   // v1.2.104\n"
   "        else if (b.dataset.wn === 'call') wcOpen(row);   // " + TAG + "\n"),
  ("  function wnLoad() {\n", JS_FUNCS + "  function wnLoad() {\n"),
 ],
}
for f, reps in P.items():
    p = T + '/' + f; s = open(p, encoding='utf-8').read(); o = s
    for a, b in reps:
        if b in s: continue
        assert s.count(a) == 1, 'anchor tidak unik/tidak ada di ' + f + ' (' + str(s.count(a)) + '): ' + a[:70]
        s = s.replace(a, b)
    if s != o:
        shutil.copy2(p, p + '.bak-v12108-' + stamp)
        open(p, 'w', encoding='utf-8').write(s); print('patched', f)
    else: print('sudah', f)
