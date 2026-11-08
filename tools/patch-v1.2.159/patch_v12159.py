#!/usr/bin/env python3
"""v1.2.159 jadwal-media — pesan WA terjadwal bisa membawa lampiran (gambar/video/audio/dokumen) + keterangan.
 - sched_create / sched_update menerima multipart (file) selain JSON; sched_update: ganti / hapus lampiran (remove_media=1).
 - File tertunda disimpan di data/sched-msgs/media/ (tidak ikut disapu masa simpan wa-media), dipindah ke
   data/wa-media/<nomor>/ saat terkirim (tampil di thread seperti lampiran biasa), dihapus bila batal/skip/kedaluwarsa/gagal.
 - Batas total lampiran tertunda 200 MB per tenant; file yatim > 1 jam dibersihkan tiap jam oleh cron.
 - Pesan suara tidak bisa diberi keterangan (ditolak); keterangan lampiran maks 1.024 karakter.
 - Action baru sched_media (pratinjau gambar di gelembung jadwal).
 Idempoten. Pakai: patch_v12159.py <dei-tenant>"""
import sys, shutil, time
T = sys.argv[1]; TAG = 'v1.2.159: jadwal-media'
A = T + '/api/index.php'; J = T + '/dashboard/chatbot-ai/app.js'; Hh = T + '/dashboard/chatbot-ai/index.html'
api = open(A, encoding='utf-8').read()
if TAG in api:
    print('sudah dipatch'); sys.exit(0)
js = open(J, encoding='utf-8').read(); html = open(Hh, encoding='utf-8').read()
st = time.strftime('%Y%m%d-%H%M%S')
for f in (A, J, Hh): shutil.copy2(f, f + '.bak-v12159-' + st)
def rep(s, old, new, cnt=1):
    n = s.count(old); assert n == cnt, f'anchor {n}x (harus {cnt}): {old[:90]!r}'
    return s.replace(old, new)
def between(s, a, b, new):
    i = s.index(a); j = s.index(b, i); assert s.count(a) == 1, a[:60]
    return s[:i] + new + s[j:]

# ---------------------------------------------------------------- API
api = rep(api, "define('DEI_VERSION', 'v1.2.158');   // v1.2.158: rl-wa",
               "define('DEI_VERSION', 'v1.2.159');   // " + TAG)

api = rep(api, "define('SCHED_KEEP', 2 * 86400);\n", r"""define('SCHED_KEEP', 2 * 86400);
// """ + TAG + r""": lampiran terjadwal
define('SCHED_MEDIA_DIR', SCHED_DIR . '/media');
define('SCHED_MEDIA_MAX', 200 * 1048576);   // total lampiran tertunda per tenant
function schedMediaPath($it) {
    $f = (string)($it['media']['f'] ?? '');
    return preg_match('/^[a-f0-9]{20}\.[a-z0-9]{1,5}$/', $f) ? SCHED_MEDIA_DIR . '/' . $f : '';
}
function schedMediaDrop($it) { $p = schedMediaPath($it); if ($p !== '' && is_file($p)) @unlink($p); }
function schedMediaUsed($exceptId = '') {
    $n = 0;
    foreach (schedReadAll() as $it) {
        if (($it['id'] ?? '') === $exceptId || !in_array($it['status'] ?? '', ['pending', 'sending'], true)) continue;
        $n += (int)($it['media']['size'] ?? 0);
    }
    return $n;
}
// Validasi file unggahan (aturan sama dengan wa_send_media). Ditolak -> jsonOut.
function schedMediaCheck($f, $wa) {
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
    return ['type' => $type, 'mime' => $mime, 'name' => $orig, 'size' => $size, 'ext' => $ext, 'tmp' => (string)$f['tmp_name']];
}
// File lampiran yang tidak dipakai jadwal tertunda (> 1 jam) dihapus; paling sering sekali per jam.
function schedMediaOrphans() {
    if (!is_dir(SCHED_MEDIA_DIR)) return;
    $mark = SCHED_MEDIA_DIR . '/.sweep';
    if (is_file($mark) && time() - (int)@filemtime($mark) < 3600) return;
    @touch($mark);
    $keep = [];
    foreach (schedReadAll() as $it) {
        if (in_array($it['status'] ?? '', ['pending', 'sending'], true) && !empty($it['media']['f'])) $keep[(string)$it['media']['f']] = 1;
    }
    foreach ((array)glob(SCHED_MEDIA_DIR . '/*') as $p) {
        if (is_file($p) && !isset($keep[basename($p)]) && time() - (int)@filemtime($p) > 3600) @unlink($p);
    }
}
""")

api = rep(api, """    $o = array_intersect_key($it, array_flip(['id', 'num', 'at', 'text', 'by', 'by_name', 'created_at', 'cancel_on_reply', 'status', 'sent_at', 'reason', 'last_err', 'cancelled_by']));
""", """    $o = array_intersect_key($it, array_flip(['id', 'num', 'at', 'text', 'by', 'by_name', 'created_at', 'cancel_on_reply', 'status', 'sent_at', 'reason', 'last_err', 'cancelled_by']));
    if (is_array($it['media'] ?? null)) $o['media'] = array_intersect_key($it['media'], array_flip(['type', 'name', 'size', 'mime']));   // """ + TAG + """
""")

api = rep(api, "function schedCheckInput($u, $num, $text, $at, $s, $selfId = '') {",
               "function schedCheckInput($u, $num, $text, $at, $s, $selfId = '', $hasMedia = false) {   // " + TAG + ": $hasMedia")
api = rep(api, "    if ($text === '') jsonOut(['ok' => false, 'error' => 'Isi pesan wajib diisi.'], 400);\n",
               "    if ($text === '' && !$hasMedia) jsonOut(['ok' => false, 'error' => 'Isi pesan atau lampiran wajib diisi.'], 400);\n")

# --- schedSendOne: kirim teks atau lampiran
api = between(api, "    $text = (string)$it['text'];\n    if (!empty($GLOBALS['dei_dry']))", "    $logs = null;   // log berubah\n", r"""    $text = (string)$it['text'];
    $md = is_array($it['media'] ?? null) ? $it['media'] : null;   // """ + TAG + r"""
    $mp = $md ? schedMediaPath($it) : '';
    if ($md && ($mp === '' || !is_file($mp))) return ['st' => 'failed', 'reason' => 'File lampiran tidak ditemukan di server.'];
    if (!empty($GLOBALS['dei_dry'])) { $GLOBALS['esc_dry_log'][] = ['sched' => $it['id'], 'to' => $num, 'text' => $text] + ($md ? ['media' => (string)$md['name']] : []); return ['st' => 'pending', 'dry' => 1]; }
    $wa = waConf($s);
    $GLOBALS['dei_out_src'] = 'agent';
    $GLOBALS['wa_reply_to'] = '';
    $okS = $md ? waSendFile($wa, $num, $mp, (string)$md['type'], (string)$md['mime'], $text, (string)$md['name']) : waSend($wa, $num, $text);
    if (!$okS) {
        $wr = trim((string)($GLOBALS['wa_last_error'] ?? '')) ?: 'gagal mengirim via WhatsApp';
        if ($now - $at < SCHED_RETRY) return ['st' => 'pending', 'reason' => '', 'last_err' => $wr];
        return ['st' => 'failed', 'reason' => 'Gagal terkirim selama 30 menit: ' . $wr];
    }
    $oid = (string)($GLOBALS['wa_last_out_id'] ?? '');
    $logA = $text; $histA = $text; $logM = null;
    if ($md) {   // file pindah ke wa-media -> tampil di thread seperti lampiran biasa & ikut masa simpan media
        $dir = WA_MEDIA_DIR . '/' . $num;
        if (!is_dir($dir)) @mkdir($dir, 0755, true);
        $fn = basename($mp); $dst = $dir . '/' . $fn;
        if (!@rename($mp, $dst) && @copy($mp, $dst)) @unlink($mp);
        if (is_file($dst)) { @touch($dst); $logM = ['type' => (string)$md['type'], 'file' => $num . '/' . $fn, 'mime' => (string)$md['mime'], 'name' => (string)$md['name'], 'size' => (int)$md['size']]; }
        $lbl = deiWaMediaLabel((string)$md['type']);
        $logA = '[' . $lbl . ': ' . $md['name'] . ']' . ($text !== '' ? "\n" . $text : '');
        $histA = '[Admin mengirim ' . mb_strtolower($lbl) . ' "' . $md['name'] . '"]' . ($text !== '' ? "\n" . $text : '');
    }
    try { waSetMode($num, 'human', 'agent_reply'); } catch (\Throwable $e) {}
    try { deiRecordAgentReply($num, (string)$it['by'], 'sched'); } catch (\Throwable $e) {}
    try { convReply($num, 'agent'); } catch (\Throwable $e) {}
    if ($wa['keep_context'] ?? true) {
        $h = waLoadHistory($num); $h[] = ['role' => 'assistant', 'content' => $histA]; waSaveHistory($num, $h);
    }
    logPrepend([
        'ts' => date('Y-m-d H:i:s'), 'q' => '', 'a' => $logA, 'ip' => $num,
        'channel' => 'whatsapp', 'dir' => 'manual', 'sched' => (string)$it['id'], 'sched_by' => (string)$it['by'],
        'utm_source' => 'whatsapp', 'utm_medium' => 'manual', 'utm_campaign' => '', 'page' => '', 'referrer' => '',
    ] + array_filter(['out_id' => $oid, 'media' => $logM]), (int)($s['api']['log_limit'] ?? 500));
""")

api = rep(api, "    if ($fin) schedArchive($fin);\n    return $fin;\n}\nfunction schedSweep($s) {\n    $now = time();\n    $all = schedReadAll();\n",
"""    if ($fin) schedArchive($fin);
    if ($fin && $res['st'] !== 'sent') schedMediaDrop($fin);   // """ + TAG + """ (terkirim: file sudah dipindah)
    return $fin;
}
function schedSweep($s) {
    $now = time();
    try { schedMediaOrphans(); } catch (\\Throwable $e) {}   // """ + TAG + """
    $all = schedReadAll();
""")

api = rep(api, "        schedArchive($fin);\n        waAuditLog('sched_cancel'",
               "        schedArchive($fin);\n        schedMediaDrop($fin);   // " + TAG + "\n        waAuditLog('sched_cancel'")

# --- sched_create / sched_update (multipart)
api = between(api, "    case 'sched_create':\n    case 'sched_update': {\n", "    case 'sched_cancel': {\n", r"""    case 'sched_create':
    case 'sched_update': {
        $u = requireAuth(['super_admin','admin','wa_agent']);
        $s = getSettings();
        // """ + TAG + r""": multipart (dengan file) atau JSON
        if (empty($_FILES) && empty($_POST) && (int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 0 && stripos((string)($_SERVER['CONTENT_TYPE'] ?? ''), 'multipart/') !== false) {
            jsonOut(['ok' => false, 'error' => 'File terlalu besar untuk server hosting (batas ' . ini_get('post_max_size') . ').'], 413);
        }
        $in = (!empty($_POST) || !empty($_FILES)) ? $_POST : bodyInput();
        $text = trim((string)($in['text'] ?? ''));
        if (mb_strlen($text) > 4000) $text = mb_substr($text, 0, 4000);
        $at = (int)($in['at'] ?? 0);
        $cor = !array_key_exists('cancel_on_reply', $in) || !empty($in['cancel_on_reply']);
        $fu = $_FILES['file'] ?? null;
        $nm = (is_array($fu) && (int)($fu['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_NO_FILE) ? schedMediaCheck($fu, waConf($s)) : null;
        $drop = !empty($in['remove_media']);
        $cur = null; $id = '';
        if ($action === 'sched_update') {
            $id = (string)($in['id'] ?? '');
            $cur = schedReadAll()[$id] ?? null;
            if (!$cur || ($cur['status'] ?? '') !== 'pending') jsonOut(['ok' => false, 'error' => 'Jadwal tidak ditemukan atau sudah diproses.'], 404);
            if (!schedCanManage($u, $cur)) jsonOut(['ok' => false, 'error' => 'Hanya pembuat jadwal atau Supervisor/Admin yang boleh mengubah.'], 403);
            $num = (string)$cur['num'];
        } else {
            $num = waNormNum($in['number'] ?? '');
            if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
            deiGuardAgentPrivate($u, $num);
        }
        $md = $nm ?: (($cur && !$drop && is_array($cur['media'] ?? null)) ? $cur['media'] : null);
        if ($md) {
            if ($md['type'] === 'audio' && $text !== '') jsonOut(['ok' => false, 'error' => 'Pesan suara tidak bisa diberi keterangan. Kosongkan kotak balas, atau jadwalkan teksnya terpisah.'], 400);
            if (mb_strlen($text) > 1024) jsonOut(['ok' => false, 'error' => 'Keterangan lampiran maksimal 1.024 karakter.'], 400);
        }
        schedCheckInput($u, $num, $text, $at, $s, $id, (bool)$md);
        if ($nm && schedMediaUsed($id) + $nm['size'] > SCHED_MEDIA_MAX) {
            jsonOut(['ok' => false, 'error' => 'Total lampiran terjadwal sudah mendekati ' . (int)(SCHED_MEDIA_MAX / 1048576) . ' MB. Tunggu sebagian terkirim atau batalkan jadwal lain.'], 400);
        }
        if ($nm) {
            if (!is_dir(SCHED_MEDIA_DIR)) @mkdir(SCHED_MEDIA_DIR, 0755, true);
            $fn = substr(sha1($num . '|' . microtime(true) . '|' . mt_rand()), 0, 20) . '.' . $nm['ext'];
            if (!@move_uploaded_file($nm['tmp'], SCHED_MEDIA_DIR . '/' . $fn)) jsonOut(['ok' => false, 'error' => 'Gagal menyimpan file di server.'], 500);
            $nm = ['type' => $nm['type'], 'mime' => $nm['mime'], 'name' => $nm['name'], 'size' => $nm['size'], 'f' => $fn];
        }
        if ($action === 'sched_update') {
            $old = null;
            $it = schedMutate(function (&$db) use ($id, $text, $at, $cor, $nm, $drop, &$old) {
                $x = $db['items'][$id] ?? null;
                if (!$x || ($x['status'] ?? '') !== 'pending') return null;
                $db['items'][$id]['text'] = $text; $db['items'][$id]['at'] = $at; $db['items'][$id]['cancel_on_reply'] = $cor ? 1 : 0;
                if ($nm || $drop) {
                    if (!empty($x['media'])) $old = $x;
                    if ($nm) $db['items'][$id]['media'] = $nm; else unset($db['items'][$id]['media']);
                }
                $db['items'][$id]['updated_at'] = time();
                return $db['items'][$id];
            });
            if (!$it) { if ($nm) schedMediaDrop(['media' => $nm]); jsonOut(['ok' => false, 'error' => 'Jadwal sudah diproses.'], 409); }
            if ($old) schedMediaDrop($old);
            waAuditLog('sched_update', $u['username'], $num, ['id' => $id, 'at' => $at] + ($nm ? ['media' => $nm['name']] : ($drop ? ['media' => '-'] : [])));
        } else {
            $it = ['id' => 's' . wibDate('ymd') . bin2hex(random_bytes(4)), 'num' => $num, 'at' => $at, 'text' => $text,
                   'by' => $u['username'], 'by_name' => (string)($u['name'] ?? $u['username']), 'created_at' => time(),
                   'cancel_on_reply' => $cor ? 1 : 0, 'status' => 'pending'] + ($nm ? ['media' => $nm] : []);
            schedMutate(function (&$db) use ($it) { $db['items'][$it['id']] = $it; });
            waAuditLog('sched_create', $u['username'], $num, ['id' => $it['id'], 'at' => $at] + ($nm ? ['media' => $nm['name']] : []));
        }
        jsonOut(['ok' => true, 'item' => schedPublic($it, $u)]);
        break;
    }
""")

api = rep(api, "    /* ---------- v1.2.153: jadwal-kirim — pesan WA terjadwal ---------- */\n    case 'sched_list': {",
"""    /* ---------- v1.2.153: jadwal-kirim — pesan WA terjadwal ---------- */
    case 'sched_media': {   // """ + TAG + """: pratinjau lampiran jadwal (token boleh di query untuk <img>)
        $u = requireAuth(['super_admin','admin','wa_agent']);
        $it = schedReadAll()[(string)($_GET['id'] ?? '')] ?? null;
        $ok = $it && (deiIsLead((string)($u['role'] ?? '')) || (string)($it['by'] ?? '') === (string)($u['username'] ?? ''));
        if ($ok) deiGuardAgentPrivate($u, (string)$it['num']);
        $p = $ok ? schedMediaPath($it) : '';
        if ($p === '' || !is_file($p)) { http_response_code(404); header('Content-Type: text/plain'); echo 'Lampiran tidak tersedia'; exit; }
        deiWaMediaOutput($p, !empty($_GET['dl']));
        exit;
    }
    case 'sched_list': {""")

# ---------------------------------------------------------------- UI (app.js)
js = rep(js, "    if (waState.attach && waState.attachNum === num) { toast('Lampiran belum bisa dijadwalkan — kirim lampiran langsung, atau hapus lampiran untuk menjadwalkan teks.', true); return; }\n", "")
js = rep(js, "    waState.schedOpen = num; waState.schedEdit = edit ? edit.id : null;\n",
             "    waState.schedOpen = num; waState.schedEdit = edit ? edit.id : null;\n    waState.schedEditMedia = (edit && edit.media) || null; waState.schedDrop = false;   // " + TAG + "\n")
js = rep(js, "      '<div class=\"ws-warn\" id=\"wsWarn\" style=\"display:none\"></div>' +\n",
             "      '<div id=\"wsMedia\" style=\"font-size:12px;color:var(--muted);margin-bottom:8px\"></div>' +\n      '<div class=\"ws-warn\" id=\"wsWarn\" style=\"display:none\"></div>' +\n")
js = rep(js, "Isi pesan diambil dari kotak balas.</span>", "Isi pesan &amp; lampiran diambil dari kotak balas.</span>")
js = rep(js, "    pop.style.display = 'block';\n    if ($('#waSchedBtn')) $('#waSchedBtn').classList.add('active');\n",
             "    pop.style.display = 'block';\n    if ($('#waSchedBtn')) $('#waSchedBtn').classList.add('active');\n    waSchedMediaRow();\n")
js = between(js, "      var text = $('#waReplyInput').value.trim();\n      if (!text) { toast('Tulis isi pesan di kotak balas dulu.'", "    check();\n  }\n  function waSchedInit() {", r"""      var text = $('#waReplyInput').value.trim();
      var f = (waState.attach && waState.attachNum === num) ? waState.attach : null;   // """ + TAG + r"""
      var keep = !f && waState.schedEditMedia && !waState.schedDrop;
      if (!text && !f && !keep) { toast('Tulis isi pesan atau pilih lampiran dulu.', true); $('#waReplyInput').focus(); return; }
      var kind = f ? WA_ATT_KIND[(f.name.split('.').pop() || '').toLowerCase()] : (keep ? waState.schedEditMedia.type : '');
      if (kind === 'audio' && text) { toast('Pesan suara tidak bisa diberi keterangan — kosongkan kotak balas, atau jadwalkan teksnya terpisah.', true); return; }
      if (kind && text.length > 1024) { toast('Keterangan lampiran maksimal 1.024 karakter.', true); return; }
      var btn = this; btn.disabled = true;
      var editing = waState.schedEdit, act = editing ? 'sched_update' : 'sched_create';
      var body = { text: text, at: at(), cancel_on_reply: $('#wsCor').checked ? 1 : 0 };
      if (editing) body.id = editing; else body.number = num;
      if (editing && waState.schedDrop && !f) body.remove_media = 1;
      var selesai = function (r) {
        btn.disabled = false;
        if (r && r.ok) {
          toast((editing ? 'Jadwal diperbarui: ' : 'Pesan dijadwalkan: ') + waSchedFmt(r.item.at) + '.');
          $('#waReplyInput').value = ''; waQuoteClear(); if (f) waAttachClear(); waQrAutosize(); waSchedClose();
          fetchWaThread(num); fetchWaConvs(true);
        } else { if (f) waAttachRender(''); toast((r && r.error) || 'Gagal menjadwalkan.', true); }
      };
      if (!f) { api(act, { method: 'POST', body: body }).then(selesai); return; }
      var fd = new FormData();
      Object.keys(body).forEach(function (k) { fd.append(k, body[k]); });
      fd.append('file', f, f.name);
      waSchedUpload(act, fd, function (p) { waAttachRender(p < 100 ? 'mengunggah ' + p + '%' : 'menyimpan jadwal…'); }, selesai);
    };
""")
js = rep(js, "  function waSchedInit() {\n", r"""  /* ---- """ + TAG + r""" — lampiran ikut dijadwalkan ---- */
  function waSchedMediaRow() {
    var el = $('#wsMedia'), num = waState.current; if (!el || !waState.schedOpen) return;
    var f = (waState.attach && waState.attachNum === num) ? waState.attach : null, em = waState.schedEditMedia;
    if (f) el.innerHTML = ico('paperclip', 13) + ' Lampiran ikut dijadwalkan: <b>' + esc(f.name) + '</b> (' + waFmtSize(f.size) + ')' + (em && !waState.schedDrop ? ' — menggantikan ' + esc(em.name) : '');
    else if (em && !waState.schedDrop) el.innerHTML = ico('paperclip', 13) + ' Lampiran: <b>' + esc(em.name) + '</b> · <a href="#" id="wsMediaX" style="color:#b91c1c;font-weight:600;text-decoration:none">Hapus lampiran</a> · ganti lewat tombol lampiran';
    else el.innerHTML = ico('paperclip', 13) + ' Bisa menyertakan lampiran: pilih file lewat tombol lampiran.';
    if ($('#wsMediaX')) $('#wsMediaX').onclick = function (e) { e.preventDefault(); waState.schedDrop = true; waSchedMediaRow(); };
  }
  function waSchedMediaHtml(x, live) {
    var m = x.media; if (!m) return '';
    var lbl = { image: 'Gambar', video: 'Video', audio: 'Pesan suara', document: 'Dokumen' }[m.type] || 'Lampiran';
    if (live && m.type === 'image') return '<img src="' + API + '?action=sched_media&id=' + encodeURIComponent(x.id) + '&token=' + encodeURIComponent(waMediaTok()) + '" alt="' + esc(m.name || lbl) + '" loading="lazy" style="max-width:200px;max-height:200px;border-radius:8px;display:block;margin-bottom:6px" onerror="this.style.display=\'none\'">';
    return '<span class="ws-att">' + ico('paperclip', 14) + ' ' + esc(lbl) + ': ' + esc(m.name || '') + (m.size ? ' · ' + waFmtSize(m.size) : '') + '</span>';
  }
  function waSchedUpload(action, fd, onProg, cb) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', API + '?action=' + action + '&_=' + Date.now());
    xhr.setRequestHeader('X-Auth-Token', token);
    if (onProg) { xhr.upload.onprogress = function (e) { if (e.lengthComputable) onProg(Math.round(e.loaded / e.total * 100)); }; onProg(0); }
    xhr.onload = function () {
      var fresh = xhr.getResponseHeader('X-Auth-Refresh');
      if (fresh) { try { token = fresh; localStorage.setItem('dei_token', fresh); } catch (e) {} }
      if (xhr.status === 401) { logout(); return; }
      var res = null; try { res = JSON.parse(xhr.responseText); } catch (e) {}
      cb(res || { ok: false, error: xhr.status === 413 ? 'File terlalu besar untuk server hosting.' : 'Respons tidak valid (HTTP ' + xhr.status + ').' });
    };
    xhr.onerror = function () { cb({ ok: false, error: 'Koneksi terputus saat mengunggah.' }); };
    xhr.send(fd);
  }
  function waSchedInit() {
""")
js = rep(js, "      return '<div class=\"wa-sbub' + (live ? '' : ' bad') + '\" data-k=\"s' + esc(x.id) + x.status + x.at + '\">' + esc(x.text) + '<div class=\"ws-meta\">' + meta + '</div></div>';",
             "      return '<div class=\"wa-sbub' + (live ? '' : ' bad') + '\" data-k=\"s' + esc(x.id) + x.status + x.at + esc(x.media ? x.media.name : '') + '\">' + waSchedMediaHtml(x, live) + esc(x.text) + '<div class=\"ws-meta\">' + meta + '</div></div>';   // " + TAG)
js = rep(js, "      waAttachRender('');\n      $('#waReplyInput').focus();\n",
             "      waAttachRender('');\n      $('#waReplyInput').focus();\n      waSchedMediaRow();   // " + TAG + "\n")
js = rep(js, "    if ($('#waReplyInput')) $('#waReplyInput').placeholder = 'Tulis balasan manual…';\n  }\n",
             "    if ($('#waReplyInput')) $('#waReplyInput').placeholder = 'Tulis balasan manual…';\n    if (waState.schedOpen) waSchedMediaRow();   // " + TAG + "\n  }\n")

# ---------------------------------------------------------------- CSS
html = rep(html, ".wa-sbub.bad .ws-meta{color:#991b1b}\n",
               ".wa-sbub.bad .ws-meta{color:#991b1b}\n/* " + TAG + " */\n.wa-sbub .ws-att{display:flex;width:fit-content;max-width:100%;gap:6px;align-items:center;padding:6px 10px;border-radius:8px;background:rgba(0,0,0,.05);font-size:13px;margin-bottom:6px;white-space:normal;word-break:break-word}\n")

import re
html, nv = re.subn(r'app\.js\?v=[0-9.]+', 'app.js?v=1.2.159', html); assert nv == 1, 'cache-bust app.js'
open(A, 'w', encoding='utf-8').write(api); open(J, 'w', encoding='utf-8').write(js); open(Hh, 'w', encoding='utf-8').write(html)
print('OK', TAG)
