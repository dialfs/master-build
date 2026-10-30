#!/usr/bin/env python3
r"""v1.2.121 wa-balas-kutip: balas satu bubble (quoted reply) di Percakapan WA, seperti aplikasi WhatsApp.
- Simpan id pesan: masuk (wamid), balasan bot (a_wamid), balasan dashboard (out_id), balasan HP (echo_id).
- Kirim dengan context.message_id (Meta) / reply_to (WAHA); tampilkan kutipan, termasuk saat pelanggan mengutip.
Pakai: python3 patch_v12121_wa_balas_kutip.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.120)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.121: wa-balas-kutip'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def patch(rel, edits):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    for old, new in edits:
        n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:90]); s = s.replace(old, new)
    assert TAG in s, rel
    shutil.copy2(p, p + '.bak-v12121-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s); print('OK', rel)

patch('api/index.php', [
 (r"""define('DEI_VERSION', 'v1.2.120');   // v1.2.120: wa-lampiran""",
  r"""define('DEI_VERSION', 'v1.2.121');   // v1.2.121: wa-balas-kutip"""),
 # helper + waSend
 (r"""function waSend($wa, $to, $text) {
    $wa = waChanFor($wa, $to);""",
  r"""/* ---------- v1.2.121: wa-balas-kutip — balas satu bubble (quoted reply) ---------- */
// Id pesan yang sedang dibalas (diisi endpoint agent sebelum kirim, dikosongkan sesudahnya).
function deiReplyToId() { return (string)($GLOBALS['wa_reply_to'] ?? ''); }
function deiQuoteSnippet($t) {
    $t = trim(preg_replace('/\s+/u', ' ', (string)$t));
    return mb_strlen($t) > 160 ? mb_substr($t, 0, 157) . '…' : $t;
}
function deiQuoteText($t, $media) {
    if (is_array($media) && !empty($media['type'])) {
        $isi = trim(preg_replace('/^\[[^\]\n]*\]\n?/', '', (string)$t));
        $lbl = deiWaMediaLabel((string)$media['type']);
        return $isi !== '' ? $lbl . ': ' . $isi : $lbl . (!empty($media['name']) ? ' ' . $media['name'] : '');
    }
    return (string)$t;
}
// Cari pesan ber-id $id di percakapan $num. Hasil ['id','who'=>'in'|'out','text','type'] atau null.
// WAHA (WEBJS) kadang hanya memberi bagian akhir id ("3EB0…") -> cocokkan juga akhiran "_<id>".
function deiQuoteFind($num, $id) {
    $id = trim((string)$id);
    if ($id === '' || strlen($id) > 200) return null;
    $cocok = function ($x) use ($id) { $x = (string)$x; return $x !== '' && ($x === $id || substr($x, -strlen($id) - 1) === '_' . $id); };
    foreach (logReadByNumber($num, 400) as $e) {
        if ($cocok($e['wamid'] ?? '')) {
            $m = is_array($e['media'] ?? null) ? $e['media'] : null;
            return ['id' => (string)$e['wamid'], 'who' => 'in', 'text' => deiQuoteSnippet(deiQuoteText($e['q'] ?? '', $m)), 'type' => (string)($m['type'] ?? '')];
        }
        foreach (['out_id', 'a_wamid', 'echo_id'] as $k) {
            if (!$cocok($e[$k] ?? '')) continue;
            $m = (($e['q'] ?? '') === '' && is_array($e['media'] ?? null)) ? $e['media'] : null;
            return ['id' => (string)$e[$k], 'who' => 'out', 'text' => deiQuoteSnippet(deiQuoteText($e['a'] ?? '', $m)), 'type' => (string)($m['type'] ?? '')];
        }
    }
    return null;
}
function waSend($wa, $to, $text) {
    $GLOBALS['wa_last_out_id'] = '';   // v1.2.121: wa-balas-kutip
    $wa = waChanFor($wa, $to);"""),
 (r"""        'text'              => ['preview_url' => false, 'body' => $text],
    ];""",
  r"""        'text'              => ['preview_url' => false, 'body' => $text],
    ];
    if (deiReplyToId() !== '') $payload['context'] = ['message_id' => deiReplyToId()];   // v1.2.121"""),
 (r"""    if ($code >= 200 && $code < 300) { waOutCount('service'); return true; }   // v1.2.57""",
  r"""    if ($code >= 200 && $code < 300) {   // v1.2.57
        waOutCount('service');
        $dOk = json_decode((string)$resp, true);   // v1.2.121: simpan id pesan keluar
        $GLOBALS['wa_last_out_id'] = is_array($dOk) ? (string)($dOk['messages'][0]['id'] ?? '') : '';
        return true;
    }"""),
 # WAHA teks
 (r"""    list($c, $d) = wahaApi($wa, 'POST', '/api/sendText', ['session' => wahaSession($wa), 'chatId' => $to . '@c.us', 'text' => $text]);""",
  r"""    $wb121 = ['session' => wahaSession($wa), 'chatId' => $to . '@c.us', 'text' => $text];
    if (deiReplyToId() !== '') $wb121['reply_to'] = deiReplyToId();   // v1.2.121
    list($c, $d) = wahaApi($wa, 'POST', '/api/sendText', $wb121);"""),
 (r"""        if ($id !== '') wahaRememberSent($to, $id, '');
        whOut($wa, $to, (string)($GLOBALS['dei_out_src'] ?? 'bot'), true, $id, $text);   // v1.2.104: skor-risiko-wa""",
  r"""        if ($id !== '') wahaRememberSent($to, $id, '');
        $GLOBALS['wa_last_out_id'] = $id;   // v1.2.121
        whOut($wa, $to, (string)($GLOBALS['dei_out_src'] ?? 'bot'), true, $id, $text);   // v1.2.104: skor-risiko-wa"""),
 # waSendFile
 (r"""    $wa = waChanFor($wa, $to); $GLOBALS['wa_out_ch'] = (string)($wa['_ch'] ?? '');
    $GLOBALS['wa_last_error'] = '';
    if (!is_file($path)) { $GLOBALS['wa_last_error'] = 'File tidak ada.'; return false; }""",
  r"""    $wa = waChanFor($wa, $to); $GLOBALS['wa_out_ch'] = (string)($wa['_ch'] ?? '');
    $GLOBALS['wa_last_error'] = ''; $GLOBALS['wa_last_out_id'] = '';   // v1.2.121
    if (!is_file($path)) { $GLOBALS['wa_last_error'] = 'File tidak ada.'; return false; }"""),
 (r"""        if ($caption !== '') $body['caption'] = $caption;
        $ep =""",
  r"""        if ($caption !== '') $body['caption'] = $caption;
        if (deiReplyToId() !== '') $body['reply_to'] = deiReplyToId();   // v1.2.121
        $ep ="""),
 (r"""        if ($c >= 200 && $c < 300) { $id = is_array($d) ? wahaMsgId($d) : ''; if ($id !== '') wahaRememberSent($to, $id, ''); whOut($wa, $to, (string)($GLOBALS['dei_out_src'] ?? 'agent'), true, $id, ''); return true; }""",
  r"""        if ($c >= 200 && $c < 300) { $id = is_array($d) ? wahaMsgId($d) : ''; if ($id !== '') wahaRememberSent($to, $id, ''); $GLOBALS['wa_last_out_id'] = $id; whOut($wa, $to, (string)($GLOBALS['dei_out_src'] ?? 'agent'), true, $id, ''); return true; }"""),
 (r"""    $payload = ['messaging_product' => 'whatsapp', 'recipient_type' => 'individual', 'to' => $to, 'type' => $type, $type => $obj];""",
  r"""    $payload = ['messaging_product' => 'whatsapp', 'recipient_type' => 'individual', 'to' => $to, 'type' => $type, $type => $obj];
    if (deiReplyToId() !== '') $payload['context'] = ['message_id' => deiReplyToId()];   // v1.2.121"""),
 (r"""    if ($code >= 200 && $code < 300) { waOutCount('service'); return true; }
    $d = json_decode((string)$resp, true);
    $GLOBALS['wa_last_error'] = (is_array($d) && isset($d['error']['message'])) ? (string)$d['error']['message'] : ('HTTP ' . $code);
    return false;
}
/* Foto KB diunggah""",
  r"""    $d = json_decode((string)$resp, true);
    if ($code >= 200 && $code < 300) { waOutCount('service'); $GLOBALS['wa_last_out_id'] = is_array($d) ? (string)($d['messages'][0]['id'] ?? '') : ''; return true; }   // v1.2.121
    $GLOBALS['wa_last_error'] = (is_array($d) && isset($d['error']['message'])) ? (string)$d['error']['message'] : ('HTTP ' . $code);
    return false;
}
/* Foto KB diunggah"""),
 # pesan masuk: konteks kutipan
 (r"""    $GLOBALS['dei_in_wamid'] = $wamid;   // v1.2.96: mengetik""",
  r"""    $GLOBALS['dei_in_wamid'] = $wamid;   // v1.2.96: mengetik
    $GLOBALS['dei_in_ctx'] = is_array($msg['context'] ?? null) ? $msg['context'] : null;   // v1.2.121: pelanggan mengutip pesan"""),
 (r"""    $msg = ['from' => $num, 'id' => $id, 'type' => $type];""",
  r"""    $msg = ['from' => $num, 'id' => $id, 'type' => $type];
    $rt121 = is_array($p['replyTo'] ?? null) ? $p['replyTo'] : null;   // v1.2.121: kutipan dari WAHA
    if ($rt121 && !empty($rt121['id'])) {
        $rid = is_array($rt121['id']) ? (string)($rt121['id']['_serialized'] ?? ($rt121['id']['id'] ?? '')) : (string)$rt121['id'];
        if ($rid !== '') $msg['context'] = ['id' => $rid, '_body' => mb_substr((string)($rt121['body'] ?? ''), 0, 300)];
    }"""),
 (r"""    if (!empty($wa['_ch'])) $logBase['wa_ch'] = (string)$wa['_ch'];   // v1.2.98: multi-nomor""",
  r"""    if (!empty($wa['_ch'])) $logBase['wa_ch'] = (string)$wa['_ch'];   // v1.2.98: multi-nomor
    // v1.2.121: wa-balas-kutip — id pesan masuk + kutipan bila pelanggan membalas pesan tertentu
    if (!empty($GLOBALS['dei_in_wamid'])) $logBase['wamid'] = (string)$GLOBALS['dei_in_wamid'];
    $ctx121 = $GLOBALS['dei_in_ctx'] ?? null;
    if (is_array($ctx121) && !empty($ctx121['id'])) {
        try {
            $qf = deiQuoteFind($from, (string)$ctx121['id']);
            if (!$qf) $qf = ['id' => (string)$ctx121['id'], 'who' => '', 'text' => deiQuoteSnippet((string)($ctx121['_body'] ?? '')), 'type' => ''];
            $logBase['reply_to'] = $qf;
        } catch (\Throwable $e) { error_log('kutip: ' . $e->getMessage()); }
    }"""),
 # id balasan bot
 (r"""    $deiSent = (trim($answer) !== '') ? waSend($wa, $from, $answer) : true;   // v1.2.95: kb-foto""",
  r"""    $deiSent = (trim($answer) !== '') ? waSend($wa, $from, $answer) : true;   // v1.2.95: kb-foto
    $deiAid121 = (trim($answer) !== '' && $deiSent) ? (string)($GLOBALS['wa_last_out_id'] ?? '') : '';   // v1.2.121"""),
 (r"""            $deiSent = waSend($wa, $from, $answer);
        }""",
  r"""            $deiSent = waSend($wa, $from, $answer);
            $deiAid121 = $deiSent ? (string)($GLOBALS['wa_last_out_id'] ?? '') : '';   // v1.2.121
        }"""),
 (r"""    $logs = logPrepend(array_merge($logBase, ['a' => $deiLogA], $deiAiError""",
  r"""    $logs = logPrepend(array_merge($logBase, ['a' => $deiLogA], $deiAid121 !== '' ? ['a_wamid' => $deiAid121] : [], $deiAiError"""),
 # wa_send_manual
 (r"""        if (mb_strlen($text) > 4000) $text = mb_substr($text, 0, 4000);""",
  r"""        if (mb_strlen($text) > 4000) $text = mb_substr($text, 0, 4000);
        $rq121 = !empty($in['reply_to']) ? deiQuoteFind($num, (string)$in['reply_to']) : null;   // v1.2.121: wa-balas-kutip"""),
 (r"""        $GLOBALS['dei_out_src'] = 'agent';   // v1.2.104: skor-risiko-wa""",
  r"""        $GLOBALS['dei_out_src'] = 'agent';   // v1.2.104: skor-risiko-wa
        $GLOBALS['wa_reply_to'] = $rq121 ? $rq121['id'] : '';   // v1.2.121"""),
 (r"""        waSetMode($num, 'human', 'agent_reply'); // replying manually = taking over""",
  r"""        $oid121 = (string)($GLOBALS['wa_last_out_id'] ?? ''); $GLOBALS['wa_reply_to'] = '';   // v1.2.121
        waSetMode($num, 'human', 'agent_reply'); // replying manually = taking over"""),
 (r"""            'utm_source' => 'whatsapp', 'utm_medium' => 'manual', 'utm_campaign' => '', 'page' => '', 'referrer' => '',
        ], (int)($s['api']['log_limit'] ?? 500));
        jsonOut(['ok' => true]);""",
  r"""            'utm_source' => 'whatsapp', 'utm_medium' => 'manual', 'utm_campaign' => '', 'page' => '', 'referrer' => '',
        ] + array_filter(['out_id' => $oid121, 'reply_to' => $rq121]), (int)($s['api']['log_limit'] ?? 500));   // v1.2.121
        jsonOut(['ok' => true]);"""),
 # wa_send_media
 (r"""        $GLOBALS['dei_out_src'] = 'agent';
        if (!waSendFile($wa, $num, $p, $type, $mime, $cap, $orig)) {""",
  r"""        $GLOBALS['dei_out_src'] = 'agent';
        $rqM = !empty($_POST['reply_to']) ? deiQuoteFind($num, (string)$_POST['reply_to']) : null;   // v1.2.121
        $GLOBALS['wa_reply_to'] = $rqM ? $rqM['id'] : '';
        if (!waSendFile($wa, $num, $p, $type, $mime, $cap, $orig)) {"""),
 (r"""        waSetMode($num, 'human', 'agent_reply');
        deiRecordAgentReply($num, $u['username'], 'dashboard');
        convReply($num, 'agent');
        $lbl = deiWaMediaLabel($type);""",
  r"""        $oidM = (string)($GLOBALS['wa_last_out_id'] ?? ''); $GLOBALS['wa_reply_to'] = '';   // v1.2.121
        waSetMode($num, 'human', 'agent_reply');
        deiRecordAgentReply($num, $u['username'], 'dashboard');
        convReply($num, 'agent');
        $lbl = deiWaMediaLabel($type);"""),
 (r"""        ], (int)($s['api']['log_limit'] ?? 500));
        jsonOut(['ok' => true, 'type' => $type]);""",
  r"""        ] + array_filter(['out_id' => $oidM, 'reply_to' => $rqM]), (int)($s['api']['log_limit'] ?? 500));   // v1.2.121
        jsonOut(['ok' => true, 'type' => $type]);"""),
 # wa_thread
 (r"""                       'ch' => (string)($e['wa_ch'] ?? '')];   // v1.2.98: multi-nomor""",
  r"""                       'ch' => (string)($e['wa_ch'] ?? ''),   // v1.2.98: multi-nomor
                       // v1.2.121: wa-balas-kutip
                       'wamid' => (string)($e['wamid'] ?? ''),
                       'out_id' => (string)(($e['out_id'] ?? '') ?: (($e['a_wamid'] ?? '') ?: ($e['echo_id'] ?? ''))),
                       'reply_to' => is_array($e['reply_to'] ?? null) ? $e['reply_to'] : null];"""),
])

patch('dashboard/chatbot-ai/index.html', [
 (r"""              <!-- v1.2.120: wa-lampiran -->""",
  r"""              <!-- v1.2.121: wa-balas-kutip -->
              <div id="waQuoteBar" style="display:none;align-items:center;gap:8px;margin-bottom:8px;padding:6px 10px;border-left:3px solid #16a34a;border-radius:8px;font-size:13px;background:var(--brand-soft)"></div>
              <!-- v1.2.120: wa-lampiran -->"""),
])

patch('dashboard/chatbot-ai/app.js', [
 # bubble
 (r"""  function waBubble(text, kind, ts, media, via) {   // v1.2.98: multi-nomor (via = nomor bisnis yang dihubungi)""",
  r"""  function waBubble(text, kind, ts, media, via, rq) {   // v1.2.98: multi-nomor (via = nomor bisnis yang dihubungi); v1.2.121: rq = {id, reply_to}"""),
 (r"""    if (media && media.file) text = String(text || '').replace(/^\[[^\]\n]*\]\n?/, '');   // v1.2.94: label diganti media
    return '<div style="max-width:78%;' + st + ';padding:8px 12px;border-radius:12px;margin:4px 0;white-space:pre-wrap;font-size:14px;line-height:1.45">' +
      waMediaHtml(media) + esc(text) + '<div style="font-size:10px;opacity:.65;margin-top:4px">' + esc((ts || '').slice(11, 16)) + who + (via ? ' · ke ' + esc(via) : '') + '</div></div>';""",
  r"""    if (media && media.file) text = String(text || '').replace(/^\[[^\]\n]*\]\n?/, '');   // v1.2.94: label diganti media
    // v1.2.121: wa-balas-kutip — kutipan di atas isi + tombol Balas
    var rid = (rq && rq.id) ? String(rq.id) : '', qh = '', rb = '';
    if (rid) {
      var snip = String(text || '').replace(/\s+/g, ' ').trim();
      if (!snip && media && media.type) snip = ({ image: 'Gambar', video: 'Video', audio: 'Pesan suara', document: 'Dokumen', sticker: 'Stiker' }[media.type] || 'Media') + (media.name ? ' ' + media.name : '');
      waState.qIdx = waState.qIdx || {};
      waState.qIdx[rid] = { who: kind === 'in' ? 'in' : 'out', text: snip.length > 160 ? snip.slice(0, 157) + '…' : snip };
      if (waState.canQuote) rb = '<a href="#" class="wa-rep" data-rid="' + esc(rid) + '" title="Balas pesan ini" style="color:inherit;opacity:.8;text-decoration:none;margin-left:8px;display:inline-flex;align-items:center;gap:2px;vertical-align:-2px">' + ico('corner-up-left', 12) + ' Balas</a>';
    }
    if (rq && rq.reply_to) qh = waQuoteHtml(rq.reply_to, kind === 'bot');
    return '<div' + (rid ? ' data-mid="' + esc(rid) + '"' : '') + ' style="max-width:78%;' + st + ';padding:8px 12px;border-radius:12px;margin:4px 0;white-space:pre-wrap;font-size:14px;line-height:1.45;transition:box-shadow .3s">' +
      qh + waMediaHtml(media) + esc(text) + '<div style="font-size:10px;opacity:.65;margin-top:4px">' + esc((ts || '').slice(11, 16)) + who + (via ? ' · ke ' + esc(via) : '') + rb + '</div></div>';
  }
  function waQuoteWho(r) { return r.who === 'in' ? 'Pelanggan' : (r.who === 'out' ? 'Anda' : 'Pesan sebelumnya'); }
  function waQuoteHtml(r, onBrand) {
    return '<div class="wa-q" data-qid="' + esc(r.id || '') + '" title="Lihat pesan yang dikutip" style="border-left:3px solid ' + (onBrand ? 'rgba(255,255,255,.75)' : (r.who === 'in' ? '#2563eb' : '#16a34a')) +
      ';background:rgba(0,0,0,.07);border-radius:6px;padding:4px 8px;margin-bottom:6px;font-size:12px;cursor:pointer;white-space:normal">' +
      '<div style="font-weight:600;opacity:.9">' + waQuoteWho(r) + '</div>' +
      '<div style="opacity:.85;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical">' + esc(r.text || '(pesan)') + '</div></div>';
  }
  function waQuoteClear() {
    waState.replyTo = null;
    if ($('#waQuoteBar')) { $('#waQuoteBar').style.display = 'none'; $('#waQuoteBar').innerHTML = ''; }
  }
  function waQuoteSet(id) {
    var q = (waState.qIdx || {})[id];
    if (!q || !waState.current) return;
    if ($('#waReplyInput').disabled) { toast('Anda tidak bisa membalas chat ini sekarang.', true); return; }
    waState.replyTo = { id: id, num: waState.current, who: q.who, text: q.text };
    var bar = $('#waQuoteBar');
    bar.style.borderLeftColor = q.who === 'in' ? '#2563eb' : '#16a34a';
    bar.innerHTML = '<span style="display:inline-flex;color:var(--muted)">' + ico('corner-up-left', 15) + '</span>' +
      '<span style="flex:1;min-width:0"><strong>Membalas ' + (q.who === 'in' ? 'Pelanggan' : 'Anda') + '</strong>' +
      '<span style="display:block;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(q.text || '(pesan)') + '</span></span>' +
      '<button type="button" id="waQuoteX" title="Batal membalas" style="border:0;background:transparent;cursor:pointer;color:var(--muted);display:inline-flex">' + ico('x', 16) + '</button>';
    bar.style.display = 'flex';
    $('#waQuoteX').onclick = waQuoteClear;
    $('#waReplyInput').focus();
  }
  function waQuoteInit() {
    var body = $('#waThreadBody');
    if (!body || waState.quoteBound) return;
    waState.quoteBound = true;
    body.addEventListener('click', function (e) {
      var a = e.target.closest ? e.target.closest('.wa-rep') : null;
      if (a) { e.preventDefault(); waQuoteSet(a.getAttribute('data-rid')); return; }
      var q = e.target.closest ? e.target.closest('.wa-q') : null;
      if (q) {
        var id = q.getAttribute('data-qid'), el = null;
        $$('#waThreadBody [data-mid]').forEach(function (x) { if (!el && x.getAttribute('data-mid') === id) el = x; });
        if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); el.style.boxShadow = '0 0 0 3px #fbbf24'; setTimeout(function () { el.style.boxShadow = ''; }, 1400); }
        else toast('Pesan yang dikutip sudah tidak ada di tampilan ini.');
      }
    });
    $('#waReplyInput').addEventListener('keydown', function (e) { if (e.key === 'Escape' && waState.replyTo) waQuoteClear(); });"""),
 # panggilan bubble
 (r"""      if (m.q) h += waBubble(m.q, 'in', m.ts, m.media, (_chMulti && m.ch) ? (_chL[m.ch] || '') : '');""",
  r"""      if (m.q) h += waBubble(m.q, 'in', m.ts, m.media, (_chMulti && m.ch) ? (_chL[m.ch] || '') : '', { id: m.wamid, reply_to: m.reply_to });   // v1.2.121"""),
 (r"""      if (m.a && !_fotoOnly) h += waBubble(m.a, m.dir === 'manual' ? 'manual' : 'bot', m.ts, m.q ? null : m.media);""",
  r"""      if (m.a && !_fotoOnly) h += waBubble(m.a, m.dir === 'manual' ? 'manual' : 'bot', m.ts, m.q ? null : m.media, '', { id: m.out_id, reply_to: m.q ? null : m.reply_to });   // v1.2.121"""),
 # status per thread
 (r"""  function renderWaThread(res) {
    var num = res.number;""",
  r"""  function renderWaThread(res) {
    var num = res.number;
    waState.canQuote = ['meta', 'waha'].indexOf(res.wa_prov || 'meta') > -1;   // v1.2.121: wa-balas-kutip
    waState.qIdx = {};"""),
 (r"""    if (waState.attach && waState.attachNum !== num) waAttachClear();""",
  r"""    if (waState.attach && waState.attachNum !== num) waAttachClear();
    if (waState.replyTo && (waState.replyTo.num !== num || !canReply)) waQuoteClear();   // v1.2.121"""),
 (r"""    waAttachInit();   // v1.2.120: wa-lampiran""",
  r"""    waAttachInit();   // v1.2.120: wa-lampiran
    waQuoteInit();   // v1.2.121: wa-balas-kutip"""),
 # kirim teks
 (r"""      api('wa_send_manual', { method: 'POST', body: { number: num, text: t } }).then(function (res) {
        if (res && res.ok) { inp.value = ''; fetchWaThread(num); fetchWaConvs(); }""",
  r"""      var b121 = { number: num, text: t };   // v1.2.121: wa-balas-kutip
      if (waState.replyTo && waState.replyTo.num === num) b121.reply_to = waState.replyTo.id;
      api('wa_send_manual', { method: 'POST', body: b121 }).then(function (res) {
        if (res && res.ok) { inp.value = ''; waQuoteClear(); fetchWaThread(num); fetchWaConvs(); }"""),
 # kirim file
 (r"""      fd.append('number', num); fd.append('caption', inp.value.trim()); fd.append('file', f, f.name);""",
  r"""      fd.append('number', num); fd.append('caption', inp.value.trim()); fd.append('file', f, f.name);
      if (waState.replyTo && waState.replyTo.num === num) fd.append('reply_to', waState.replyTo.id);   // v1.2.121"""),
 (r"""        if (res && res.ok) { inp.value = ''; waAttachClear(); toast('File terkirim.'); fetchWaThread(num); fetchWaConvs(); }""",
  r"""        if (res && res.ok) { inp.value = ''; waAttachClear(); waQuoteClear(); toast('File terkirim.'); fetchWaThread(num); fetchWaConvs(); }"""),
])
