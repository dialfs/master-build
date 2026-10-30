#!/usr/bin/env python3
r"""v1.2.120 wa-lampiran: agent melampirkan file (gambar/video/audio/dokumen) saat membalas dari Percakapan WA.
Pakai: python3 patch_v12120_wa_lampiran.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.119)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.120: wa-lampiran'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def patch(rel, edits):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    for old, new in edits:
        n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:90]); s = s.replace(old, new)
    assert TAG in s, rel
    shutil.copy2(p, p + '.bak-v12120-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s); print('OK', rel)

patch('api/index.php', [
 (r"""define('DEI_VERSION', 'v1.2.119');   // v1.2.119: agent-stage""",
  r"""define('DEI_VERSION', 'v1.2.120');   // v1.2.120: wa-lampiran"""),
 (r"""/* Foto KB diunggah ke Meta sekali; id disimpan 25 hari (id media Meta berlaku 30 hari). */""",
  r"""/* ---------- v1.2.120: wa-lampiran — agent mengirim file dari Percakapan WA ---------- */
function deiWaOutKind($ext) {
    $d = 'document';
    $m = ['jpg' => ['image', 'image/jpeg'], 'jpeg' => ['image', 'image/jpeg'], 'png' => ['image', 'image/png'],
          'mp4' => ['video', 'video/mp4'], '3gp' => ['video', 'video/3gpp'],
          'mp3' => ['audio', 'audio/mpeg'], 'ogg' => ['audio', 'audio/ogg'], 'm4a' => ['audio', 'audio/mp4'], 'aac' => ['audio', 'audio/aac'], 'amr' => ['audio', 'audio/amr'],
          'pdf' => [$d, 'application/pdf'], 'txt' => [$d, 'text/plain'], 'csv' => [$d, 'text/csv'],
          'doc' => [$d, 'application/msword'], 'docx' => [$d, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
          'xls' => [$d, 'application/vnd.ms-excel'], 'xlsx' => [$d, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
          'ppt' => [$d, 'application/vnd.ms-powerpoint'], 'pptx' => [$d, 'application/vnd.openxmlformats-officedocument.presentationml.presentation'],
          'zip' => [$d, 'application/zip']];
    return $m[strtolower((string)$ext)] ?? null;
}
// Batas WhatsApp per jenis (MB); dokumen dibatasi 16 MB oleh dashboard.
function deiWaOutLimitMb($type) { return ['image' => 5, 'video' => 16, 'audio' => 16, 'document' => 16][$type] ?? 16; }
function deiWahaPostLong($wa, $path, $body, $timeout = 120) {
    $base = rtrim(trim((string)($wa['waha_url'] ?? '')), '/');
    if ($base === '') return [0, ['message' => 'URL WAHA belum diisi.']];
    $ch = curl_init($base . $path);
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => $timeout, CURLOPT_CONNECTTIMEOUT => 8, CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => ['Accept: application/json', 'Content-Type: application/json', 'X-Api-Key: ' . (string)($wa['waha_api_key'] ?? '')],
        CURLOPT_POSTFIELDS => json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $err = curl_error($ch); curl_close($ch);
    if ($resp === false) return [0, ['message' => 'Server WAHA tidak dapat dihubungi: ' . $err]];
    $d = json_decode((string)$resp, true);
    return [$code, is_array($d) ? $d : ['message' => mb_substr(trim((string)$resp), 0, 200)]];
}
function deiMetaUploadFile($wa, $path, $mime, $name) {
    $ch = curl_init('https://graph.facebook.com/v21.0/' . rawurlencode((string)($wa['phone_number_id'] ?? '')) . '/media');
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_POST => true, CURLOPT_TIMEOUT => 120,
        CURLOPT_HTTPHEADER => ['Authorization: Bearer ' . (string)($wa['access_token'] ?? '')],
        CURLOPT_POSTFIELDS => ['messaging_product' => 'whatsapp', 'type' => $mime, 'file' => new CURLFile($path, $mime, $name)]]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    $d = json_decode((string)$resp, true);
    if ($code < 200 || $code >= 300 || !is_array($d) || empty($d['id'])) {
        $GLOBALS['wa_last_error'] = 'Unggah file ke Meta gagal: ' . ((is_array($d) && isset($d['error']['message'])) ? $d['error']['message'] : ('HTTP ' . $code));
        return '';
    }
    return (string)$d['id'];
}
/* Kirim file (image|video|audio|document). Caption tidak berlaku untuk audio. */
function waSendFile($wa, $to, $path, $type, $mime, $caption = '', $name = '') {
    $wa = waChanFor($wa, $to); $GLOBALS['wa_out_ch'] = (string)($wa['_ch'] ?? '');
    $GLOBALS['wa_last_error'] = '';
    if (!is_file($path)) { $GLOBALS['wa_last_error'] = 'File tidak ada.'; return false; }
    if ($name === '') $name = basename($path);
    $caption = ($type === 'audio') ? '' : (string)$caption;
    $prov = (string)($wa['provider'] ?? 'meta');
    if ($prov === 'waha') {
        $to = waNormNum($to);
        $body = ['session' => wahaSession($wa), 'chatId' => $to . '@c.us',
                 'file' => ['mimetype' => $mime, 'filename' => $name, 'data' => base64_encode((string)file_get_contents($path))]];
        if ($caption !== '') $body['caption'] = $caption;
        $ep = ['image' => '/api/sendImage', 'video' => '/api/sendVideo'][$type] ?? '/api/sendFile';
        list($c, $d) = deiWahaPostLong($wa, $ep, $body);
        if (($c < 200 || $c >= 300) && $ep === '/api/sendVideo') list($c, $d) = deiWahaPostLong($wa, '/api/sendFile', $body);   // engine tanpa sendVideo
        if ($c >= 200 && $c < 300) { $id = is_array($d) ? wahaMsgId($d) : ''; if ($id !== '') wahaRememberSent($to, $id, ''); whOut($wa, $to, (string)($GLOBALS['dei_out_src'] ?? 'agent'), true, $id, ''); return true; }
        whOut($wa, $to, (string)($GLOBALS['dei_out_src'] ?? 'agent'), false);
        $GLOBALS['wa_last_error'] = wahaErr($c, $d, 'Kirim file lewat WAHA gagal.');
        return false;
    }
    if ($prov !== 'meta') { $GLOBALS['wa_last_error'] = 'Penyedia ini tidak mendukung kirim file.'; return false; }
    $token = (string)($wa['access_token'] ?? ''); $pnid = (string)($wa['phone_number_id'] ?? '');
    if ($token === '' || $pnid === '') { $GLOBALS['wa_last_error'] = 'Access Token / Phone Number ID kosong.'; return false; }
    $mid = deiMetaUploadFile($wa, $path, $mime, $name);
    if ($mid === '') return false;
    $obj = ['id' => $mid];
    if ($caption !== '') $obj['caption'] = $caption;
    if ($type === 'document') $obj['filename'] = $name;
    $payload = ['messaging_product' => 'whatsapp', 'recipient_type' => 'individual', 'to' => $to, 'type' => $type, $type => $obj];
    $ch = curl_init('https://graph.facebook.com/v21.0/' . rawurlencode($pnid) . '/messages');
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_POST => true, CURLOPT_TIMEOUT => 30,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'Authorization: Bearer ' . $token],
        CURLOPT_POSTFIELDS => json_encode($payload, JSON_UNESCAPED_UNICODE)]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    if ($code >= 200 && $code < 300) { waOutCount('service'); return true; }
    $d = json_decode((string)$resp, true);
    $GLOBALS['wa_last_error'] = (is_array($d) && isset($d['error']['message'])) ? (string)$d['error']['message'] : ('HTTP ' . $code);
    return false;
}
/* Foto KB diunggah ke Meta sekali; id disimpan 25 hari (id media Meta berlaku 30 hari). */"""),
 (r"""    case 'wa_send_manual': {""",
  r"""    case 'wa_send_media': {   // v1.2.120: wa-lampiran — multipart: number, caption, file
        $u = requireAuth(['super_admin','admin','wa_agent']);
        if (empty($_FILES) && empty($_POST) && (int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 0) {   // post_max_size terlampaui
            jsonOut(['ok' => false, 'error' => 'File terlalu besar untuk server hosting (batas ' . ini_get('post_max_size') . ').'], 413);
        }
        $s = getSettings();
        $wa = waConf($s);
        $num = waNormNum($_POST['number'] ?? '');
        $cap = trim((string)($_POST['caption'] ?? ''));
        if (mb_strlen($cap) > 1024) $cap = mb_substr($cap, 0, 1024);
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        $f = $_FILES['file'] ?? null;
        $er = is_array($f) ? (int)($f['error'] ?? UPLOAD_ERR_NO_FILE) : UPLOAD_ERR_NO_FILE;
        if ($er !== UPLOAD_ERR_OK) {
            $msg = in_array($er, [UPLOAD_ERR_INI_SIZE, UPLOAD_ERR_FORM_SIZE], true) ? ('File melebihi batas unggah server hosting (' . ini_get('upload_max_filesize') . ').')
                 : ($er === UPLOAD_ERR_NO_FILE ? 'Pilih file dulu.' : ('Unggah file gagal (kode ' . $er . ').'));
            jsonOut(['ok' => false, 'error' => $msg], 400);
        }
        if (!in_array((string)($wa['provider'] ?? 'meta'), ['meta', 'waha'], true)) jsonOut(['ok' => false, 'error' => 'Penyedia WhatsApp ini tidak mendukung kirim file.'], 400);
        $orig = basename(str_replace('\\', '/', (string)($f['name'] ?? 'file')));
        $orig = mb_substr(trim(preg_replace('/[\x00-\x1f"<>|:*?]/u', '', $orig)), 0, 120);
        $ext = strtolower(pathinfo($orig, PATHINFO_EXTENSION));
        $kind = deiWaOutKind($ext);
        if (!$kind) jsonOut(['ok' => false, 'error' => 'Jenis file .' . $ext . ' belum didukung. Bisa: JPG/PNG, MP4, MP3/OGG/M4A, PDF, Word, Excel, PowerPoint, TXT, CSV, ZIP.'], 400);
        list($type, $mime) = $kind;
        $size = (int)($f['size'] ?? 0);
        if ($size <= 0) jsonOut(['ok' => false, 'error' => 'File kosong.'], 400);
        if ($size > deiWaOutLimitMb($type) * 1048576) jsonOut(['ok' => false, 'error' => 'Batas WhatsApp untuk ' . mb_strtolower(deiWaMediaLabel($type)) . ': ' . deiWaOutLimitMb($type) . ' MB.'], 400);
        if ($type === 'image' && !@getimagesize($f['tmp_name'])) jsonOut(['ok' => false, 'error' => 'File gambar rusak atau bukan gambar.'], 400);
        deiGuardSpvScope($u, $num);
        deiGuardAgentStage($u, $num);
        if ($u['role'] === 'wa_agent') {
            $clM = waClaimGet($num);
            if ($clM && ($clM['agent_username'] ?? '') !== $u['username']) {
                jsonOut(['ok' => false, 'error' => 'Chat ini dipegang ' . ($clM['agent_username'] ?? 'agent lain') . '. Minta take-over dulu.'], 403);
            }
        }
        $lastInbound = 0;
        $winChM = waWinCh($num, $s);
        foreach (logReadAll() as $e) {
            if (($e['channel'] ?? '') === 'whatsapp' && waNormNum($e['ip'] ?? '') === $num && ($e['q'] ?? '') !== '' && waInboundOnCh($e, $winChM)) {
                $lastInbound = strtotime($e['ts']); break;
            }
        }
        if (($lastInbound <= 0 || (time() - $lastInbound) > 24 * 3600) && !waWindowSelaluTerbuka()) {
            jsonOut(['ok' => false, 'error' => 'Jendela 24 jam tertutup — WhatsApp tidak mengizinkan kirim file sampai pelanggan mengirim pesan lagi.'], 409);
        }
        $dir = WA_MEDIA_DIR . '/' . $num;
        if (!is_dir($dir)) @mkdir($dir, 0755, true);
        $fn = substr(sha1($num . '|' . microtime(true) . '|' . mt_rand()), 0, 20) . '.' . $ext;
        $p = $dir . '/' . $fn;
        if (!@move_uploaded_file($f['tmp_name'], $p)) jsonOut(['ok' => false, 'error' => 'Gagal menyimpan file di server.'], 500);
        $GLOBALS['dei_out_src'] = 'agent';
        if (!waSendFile($wa, $num, $p, $type, $mime, $cap, $orig)) {
            @unlink($p);
            $wr = trim((string)($GLOBALS['wa_last_error'] ?? ''));
            jsonOut(['ok' => false, 'error' => 'Gagal mengirim file via WhatsApp' . ($wr !== '' ? ': ' . $wr : '.')], 502);
        }
        waSetMode($num, 'human', 'agent_reply');
        deiRecordAgentReply($num, $u['username'], 'dashboard');
        convReply($num, 'agent');
        $lbl = deiWaMediaLabel($type);
        if ($wa['keep_context'] ?? true) {
            $h = waLoadHistory($num);
            $h[] = ['role' => 'assistant', 'content' => '[Admin mengirim ' . mb_strtolower($lbl) . ' "' . $orig . '"]' . ($cap !== '' ? "\n" . $cap : '')];
            waSaveHistory($num, $h);
        }
        logPrepend([
            'ts' => date('Y-m-d H:i:s'), 'q' => '', 'a' => '[' . $lbl . ': ' . $orig . ']' . ($cap !== '' ? "\n" . $cap : ''), 'ip' => $num,
            'channel' => 'whatsapp', 'dir' => 'manual',
            'media' => ['type' => $type, 'file' => $num . '/' . $fn, 'mime' => $mime, 'name' => $orig, 'size' => $size],
            'utm_source' => 'whatsapp', 'utm_medium' => 'manual', 'utm_campaign' => '', 'page' => '', 'referrer' => '',
        ], (int)($s['api']['log_limit'] ?? 500));
        jsonOut(['ok' => true, 'type' => $type]);
        break;
    }

    case 'wa_send_manual': {"""),
])

patch('dashboard/chatbot-ai/index.html', [
 (r"""              <div style="display:flex;gap:8px">
                <input type="text" id="waReplyInput" placeholder="Tulis balasan manual…" style="flex:1">""",
  r"""              <!-- v1.2.120: wa-lampiran -->
              <div id="waAttachChip" style="display:none;align-items:center;gap:8px;margin-bottom:8px;padding:6px 10px;border:1px solid var(--line);border-radius:8px;font-size:13px;background:var(--brand-soft)"></div>
              <div style="display:flex;gap:8px">
                <button class="btn ghost" id="waAttachBtn" type="button" title="Lampirkan file: gambar, video, audio, atau dokumen" style="padding:7px 10px"><span data-ico="paperclip" data-ico-size="16"></span></button>
                <input type="file" id="waAttachFile" style="display:none" accept=".jpg,.jpeg,.png,.mp4,.3gp,.mp3,.ogg,.m4a,.aac,.amr,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.zip">
                <input type="text" id="waReplyInput" placeholder="Tulis balasan manual…" style="flex:1">"""),
])

patch('dashboard/chatbot-ai/app.js', [
 (r"""    $('#waReplySend').onclick = function () { if (waState.current) sendWaManual(waState.current); };""",
  r"""    $('#waReplySend').onclick = function () { if (waState.current) sendWaManual(waState.current); };
    waAttachInit();   // v1.2.120: wa-lampiran"""),
 (r"""  function sendWaManual(num) {
    var inp = $('#waReplyInput'); var t = inp.value.trim();
    if (!t) return;""",
  r"""  /* ---- v1.2.120: wa-lampiran — lampirkan file di balasan Percakapan WA ---- */
  var WA_ATT_KIND = { jpg: 'image', jpeg: 'image', png: 'image', mp4: 'video', '3gp': 'video',
    mp3: 'audio', ogg: 'audio', m4a: 'audio', aac: 'audio', amr: 'audio',
    pdf: 'document', doc: 'document', docx: 'document', xls: 'document', xlsx: 'document', ppt: 'document', pptx: 'document', txt: 'document', csv: 'document', zip: 'document' };
  var WA_ATT_MB = { image: 5, video: 16, audio: 16, document: 16 };
  function waFmtSize(n) { return n >= 1048576 ? (n / 1048576).toFixed(1).replace('.', ',') + ' MB' : Math.max(1, Math.round(n / 1024)) + ' KB'; }
  function waAttachClear() {
    if (waState.attachUrl) { try { URL.revokeObjectURL(waState.attachUrl); } catch (e) {} }
    waState.attach = null; waState.attachNum = null; waState.attachUrl = null;
    if ($('#waAttachFile')) $('#waAttachFile').value = '';
    if ($('#waAttachChip')) { $('#waAttachChip').style.display = 'none'; $('#waAttachChip').innerHTML = ''; }
    if ($('#waReplyInput')) $('#waReplyInput').placeholder = 'Tulis balasan manual…';
  }
  function waAttachRender(status) {
    var f = waState.attach, chip = $('#waAttachChip');
    if (!f || !chip) return;
    var kind = WA_ATT_KIND[(f.name.split('.').pop() || '').toLowerCase()];
    var thumb = (kind === 'image' && waState.attachUrl)
      ? '<img src="' + waState.attachUrl + '" alt="" style="width:36px;height:36px;object-fit:cover;border-radius:6px">'
      : '<span style="display:inline-flex;color:var(--muted)">' + ico('paperclip', 16) + '</span>';
    chip.innerHTML = thumb + '<span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"><strong>' + esc(f.name) + '</strong> <span style="color:var(--muted)">' + waFmtSize(f.size) + '</span>' +
      (status ? ' <span style="color:var(--muted)">· ' + esc(status) + '</span>' : '') + '</span>' +
      (status ? '' : '<button type="button" id="waAttachX" title="Batalkan lampiran" style="border:0;background:transparent;cursor:pointer;color:var(--muted);display:inline-flex">' + ico('x', 16) + '</button>');
    chip.style.display = 'flex';
    if ($('#waAttachX')) $('#waAttachX').onclick = waAttachClear;
  }
  function waAttachInit() {
    if (!$('#waAttachBtn') || waState.attachBound) return;
    waState.attachBound = true;
    $('#waAttachBtn').onclick = function () { if (!this.disabled) $('#waAttachFile').click(); };
    $('#waAttachFile').onchange = function () {
      var f = this.files && this.files[0];
      if (!f || !waState.current) return;
      var ext = (f.name.split('.').pop() || '').toLowerCase(), kind = WA_ATT_KIND[ext];
      if (!kind) { toast('Jenis file .' + ext + ' belum didukung. Bisa: JPG/PNG, MP4, MP3/OGG/M4A, PDF, Word, Excel, PowerPoint, TXT, CSV, ZIP.', true); this.value = ''; return; }
      if (f.size > WA_ATT_MB[kind] * 1048576) { toast('Batas WhatsApp untuk file ini: ' + WA_ATT_MB[kind] + ' MB (file Anda ' + waFmtSize(f.size) + ').', true); this.value = ''; return; }
      if (waState.attachUrl) { try { URL.revokeObjectURL(waState.attachUrl); } catch (e) {} waState.attachUrl = null; }
      waState.attach = f; waState.attachNum = waState.current;
      if (kind === 'image') { try { waState.attachUrl = URL.createObjectURL(f); } catch (e) {} }
      $('#waReplyInput').placeholder = kind === 'audio' ? 'Audio dikirim tanpa keterangan' : 'Tulis keterangan (opsional)…';
      waAttachRender('');
      $('#waReplyInput').focus();
    };
  }
  function sendWaMedia(num) {
    var inp = $('#waReplyInput'), f = waState.attach;
    if (!f) return;
    $('#waReplySend').disabled = true; $('#waAttachBtn').disabled = true;
    var kirim = function () {
      var fd = new FormData();
      fd.append('number', num); fd.append('caption', inp.value.trim()); fd.append('file', f, f.name);
      var xhr = new XMLHttpRequest();
      xhr.open('POST', API + '?action=wa_send_media&_=' + Date.now());
      xhr.setRequestHeader('X-Auth-Token', token);
      xhr.upload.onprogress = function (e) { if (e.lengthComputable) waAttachRender('mengunggah ' + Math.round(e.loaded / e.total * 100) + '%'); };
      xhr.upload.onload = function () { waAttachRender('mengirim ke WhatsApp…'); };
      var selesai = function (res) {
        if (res && res.ok) { inp.value = ''; waAttachClear(); toast('File terkirim.'); fetchWaThread(num); fetchWaConvs(); }
        else { waAttachRender(''); toast((res && res.error) || 'Gagal mengirim file.', true); }
        $('#waReplySend').disabled = false; $('#waAttachBtn').disabled = false;
      };
      xhr.onload = function () {
        var fresh = xhr.getResponseHeader('X-Auth-Refresh');
        if (fresh) { try { token = fresh; localStorage.setItem('dei_token', fresh); } catch (e) {} }
        if (xhr.status === 401) { logout(); return; }
        var res = null; try { res = JSON.parse(xhr.responseText); } catch (e) {}
        if (!res) res = { ok: false, error: xhr.status === 413 ? 'File terlalu besar untuk server hosting.' : 'Respons tidak valid (HTTP ' + xhr.status + ').' };
        selesai(res);
      };
      xhr.onerror = function () { selesai({ ok: false, error: 'Koneksi terputus saat mengunggah.' }); };
      waAttachRender('mengunggah 0%');
      xhr.send(fd);
    };
    if (!waState.claimDetails[num]) api('wa_claim', { method: 'POST', body: { number: num } }).then(kirim, kirim);   // sama seperti balasan teks
    else kirim();
  }

  function sendWaManual(num) {
    var inp = $('#waReplyInput'); var t = inp.value.trim();
    if (waState.attach && waState.attachNum === num) { sendWaMedia(num); return; }   // v1.2.120: wa-lampiran
    if (!t) return;"""),
 (r"""    $('#waReplySend').disabled = !canReply;
    $('#waWindowNote').innerHTML = """,
  r"""    $('#waReplySend').disabled = !canReply;
    if ($('#waAttachBtn')) $('#waAttachBtn').disabled = !canReply || res.wa_prov === 'fonnte';   // v1.2.120: wa-lampiran
    if (waState.attach && waState.attachNum !== num) waAttachClear();
    $('#waWindowNote').innerHTML = """),
])
