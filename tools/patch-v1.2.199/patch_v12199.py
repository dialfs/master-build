#!/usr/bin/env python3
"""v1.2.199 (template-media): Template Balasan WA bisa membawa lampiran (gambar, video, dokumen, audio).
- api/index.php: qr_save terima multipart (file + remove_media), file disimpan di data/wa-qr-media/,
  qr_media (unduh lampiran template, butuh login), qr_delete ikut hapus file, DEI_VERSION v1.2.199.
- app.js: Kelola template punya kolom Lampiran (pilih/ganti/hapus); memilih template berlampiran
  langsung memasang file di kotak balas (isi template jadi keterangan) -> Kirim / Jadwalkan seperti biasa.
  Daftar template menandai yang berlampiran. Artikel Pusat Bantuan "Memakai template balasan".
- index.html: app.js?v=1.2.199.
Butuh v1.2.198. Idempoten.  Pakai: patch_v12199.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.199: template-media'; NEED = 'v1.2.198: pasang-di-hp'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12199-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)

API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ---------------------------------------------------------------- api/index.php
s = rd(API)
if TAG not in s:
    assert NEED in s, 'butuh v1.2.198 dulu'
    s = rep(s, "define('DEI_VERSION', 'v1.2.198');   // v1.2.198:",
            "define('DEI_VERSION', 'v1.2.199');   // " + TAG + " — Template Balasan WA bisa membawa lampiran (gambar/video/dokumen/audio); v1.2.198:", what='DEI_VERSION')
    # 1) penyimpanan lampiran template
    s = rep(s, "define('WA_QR_MAX', 300);\n",
            "define('WA_QR_MAX', 300);\n"
            "define('WA_QR_MEDIA_DIR', DATA_DIR . '/wa-qr-media');   // " + TAG + "\n"
            "define('WA_QR_MEDIA_MAX', 300 * 1048576);               // total lampiran template per tenant\n"
            "function deiQrMediaPath($it) {\n"
            "    $f = basename((string)($it['media']['f'] ?? ''));\n"
            "    return $f !== '' ? WA_QR_MEDIA_DIR . '/' . $f : '';\n"
            "}\n"
            "function deiQrMediaDrop($it) { $p = deiQrMediaPath($it); if ($p !== '' && is_file($p)) @unlink($p); }\n"
            "function deiQrMediaUsed($exceptId = '') {\n"
            "    $n = 0;\n"
            "    foreach (deiQrAll() as $x) { if (($x['id'] ?? '') !== $exceptId && !empty($x['media'])) $n += (int)($x['media']['size'] ?? 0); }\n"
            "    return $n;\n"
            "}\n", what='WA_QR_MAX')
    # 2) qr_save: multipart + lampiran
    s = rep(s, "    case 'qr_save': {\n"
               "        $u = requireAuth(['super_admin', 'admin', 'supervisor']);\n"
               "        $in = bodyInput();\n",
               "    case 'qr_save': {\n"
               "        $u = requireAuth(['super_admin', 'admin', 'supervisor']);\n"
               "        // " + TAG + ": multipart (dengan file) atau JSON\n"
               "        if (empty($_FILES) && empty($_POST) && (int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 0 && stripos((string)($_SERVER['CONTENT_TYPE'] ?? ''), 'multipart/') !== false) {\n"
               "            jsonOut(['ok' => false, 'error' => 'File terlalu besar untuk server hosting (batas ' . ini_get('post_max_size') . ').'], 413);\n"
               "        }\n"
               "        $in = !empty($_POST) ? $_POST : bodyInput();\n", what='qr_save head')
    s = rep(s, "        if ($text === '') jsonOut(['ok' => false, 'error' => 'Isi template wajib diisi.'], 400);\n"
               "        if (mb_strlen($text) > 4000) jsonOut(['ok' => false, 'error' => 'Isi template maksimal 4.000 karakter.'], 400);\n"
               "        if ($title === '') $title = mb_substr(trim(preg_replace('/\\s+/u', ' ', $text)), 0, 40);\n",
               "        $fu = $_FILES['file'] ?? null;   // " + TAG + "\n"
               "        $nm = (is_array($fu) && (int)($fu['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_NO_FILE) ? schedMediaCheck($fu, ['provider' => 'meta']) : null;\n"
               "        $drop = !empty($in['remove_media']);\n"
               "        $cur = null;\n"
               "        if ($id !== '') { foreach (deiQrAll() as $x) { if (($x['id'] ?? '') === $id) { $cur = $x; break; } } }\n"
               "        $md = $nm ?: (($cur && !$drop && is_array($cur['media'] ?? null)) ? $cur['media'] : null);\n"
               "        if ($text === '' && !$md) jsonOut(['ok' => false, 'error' => 'Isi template wajib diisi (atau pilih lampiran).'], 400);\n"
               "        if (mb_strlen($text) > 4000) jsonOut(['ok' => false, 'error' => 'Isi template maksimal 4.000 karakter.'], 400);\n"
               "        if ($md && $md['type'] === 'audio' && $text !== '') jsonOut(['ok' => false, 'error' => 'Pesan suara tidak bisa diberi keterangan. Kosongkan isi template, atau buat template teks terpisah.'], 400);\n"
               "        if ($md && mb_strlen($text) > 1024) jsonOut(['ok' => false, 'error' => 'Template berlampiran: isi menjadi keterangan, maksimal 1.024 karakter.'], 400);\n"
               "        if ($nm && deiQrMediaUsed($id) + $nm['size'] > WA_QR_MEDIA_MAX) jsonOut(['ok' => false, 'error' => 'Total lampiran template sudah mendekati ' . (int)(WA_QR_MEDIA_MAX / 1048576) . ' MB. Hapus lampiran template yang tidak dipakai dulu.'], 400);\n"
               "        if ($title === '') $title = mb_substr(trim(preg_replace('/\\s+/u', ' ', $text !== '' ? $text : (string)$md['name'])), 0, 40);\n"
               "", what='qr_save validasi')
    s = rep(s, "        if ($sc !== '' && !preg_match('/^[a-z0-9_-]{1,30}$/', $sc)) jsonOut(['ok' => false, 'error' => 'Pintasan hanya boleh huruf kecil, angka, - atau _ (maks 30, tanpa spasi).'], 400);\n",
               "        if ($sc !== '' && !preg_match('/^[a-z0-9_-]{1,30}$/', $sc)) jsonOut(['ok' => false, 'error' => 'Pintasan hanya boleh huruf kecil, angka, - atau _ (maks 30, tanpa spasi).'], 400);\n"
               "        if ($nm) {   // " + TAG + "\n"
               "            if (!is_dir(WA_QR_MEDIA_DIR)) @mkdir(WA_QR_MEDIA_DIR, 0755, true);\n"
               "            $fn = substr(sha1(uniqid('', true) . mt_rand()), 0, 20) . '.' . $nm['ext'];\n"
               "            if (!@move_uploaded_file($nm['tmp'], WA_QR_MEDIA_DIR . '/' . $fn)) jsonOut(['ok' => false, 'error' => 'Gagal menyimpan file di server.'], 500);\n"
               "            $nm = ['type' => $nm['type'], 'mime' => $nm['mime'], 'name' => $nm['name'], 'size' => $nm['size'], 'f' => $fn];\n"
               "        }\n"
               "        $old = null;\n", what='qr_save simpan file')
    s = rep(s, "        $r = deiWithLock('wa-qr', function () use ($id, $text, $title, $sc, $u) {\n",
               "        $r = deiWithLock('wa-qr', function () use ($id, $text, $title, $sc, $u, $nm, $drop, &$old) {   // " + TAG + "\n", what='qr_save lock')
    s = rep(s, "            $item = ['id' => $id, 'title' => $title, 'shortcut' => $sc, 'text' => $text, 'updated_at' => $now, 'by' => (string)($u['username'] ?? '')];\n"
               "            $found = false;\n"
               "            if ($id !== '') {\n"
               "                foreach ($l as $i => $x) { if (($x['id'] ?? '') === $id) { $l[$i] = $item; $found = true; break; } }\n",
               "            $item = ['id' => $id, 'title' => $title, 'shortcut' => $sc, 'text' => $text, 'updated_at' => $now, 'by' => (string)($u['username'] ?? '')];\n"
               "            if ($nm) $item['media'] = $nm;   // " + TAG + "\n"
               "            $found = false;\n"
               "            if ($id !== '') {\n"
               "                foreach ($l as $i => $x) {\n"
               "                    if (($x['id'] ?? '') !== $id) continue;\n"
               "                    if (!$nm && !$drop && !empty($x['media'])) $item['media'] = $x['media'];\n"
               "                    if (($nm || $drop) && !empty($x['media'])) $old = $x;\n"
               "                    $l[$i] = $item; $found = true; break;\n"
               "                }\n", what='qr_save item')
    s = rep(s, "        if (!is_array($r)) jsonOut(['ok' => false, 'error' => (string)$r], 400);\n"
               "        jsonOut(['ok' => true, 'item' => $r, 'items' => deiQrSorted()]);\n",
               "        if (!is_array($r)) { if ($nm) deiQrMediaDrop(['media' => $nm]); jsonOut(['ok' => false, 'error' => (string)$r], 400); }\n"
               "        if ($old) deiQrMediaDrop($old);   // " + TAG + "\n"
               "        jsonOut(['ok' => true, 'item' => $r, 'items' => deiQrSorted()]);\n", what='qr_save out')
    # 3) qr_delete hapus file; qr_media
    s = rep(s, "        deiWithLock('wa-qr', function () use ($id) {\n"
               "            writeJson(WA_QR_FILE, array_values(array_filter(deiQrAll(), function ($x) use ($id) { return ($x['id'] ?? '') !== $id; })));\n"
               "        });\n"
               "        jsonOut(['ok' => true, 'items' => deiQrSorted()]);\n"
               "        break;\n"
               "    }\n",
               "        deiWithLock('wa-qr', function () use ($id) {\n"
               "            foreach (deiQrAll() as $x) { if (($x['id'] ?? '') === $id) deiQrMediaDrop($x); }   // " + TAG + "\n"
               "            writeJson(WA_QR_FILE, array_values(array_filter(deiQrAll(), function ($x) use ($id) { return ($x['id'] ?? '') !== $id; })));\n"
               "        });\n"
               "        jsonOut(['ok' => true, 'items' => deiQrSorted()]);\n"
               "        break;\n"
               "    }\n"
               "    case 'qr_media': {   // " + TAG + ": lampiran template (token boleh di query untuk <img>)\n"
               "        requireAuth(['super_admin', 'admin', 'supervisor', 'wa_agent']);\n"
               "        $id = preg_replace('/[^a-f0-9]/', '', (string)($_GET['id'] ?? ''));\n"
               "        $it = null;\n"
               "        foreach (deiQrAll() as $x) { if ($id !== '' && ($x['id'] ?? '') === $id) { $it = $x; break; } }\n"
               "        $p = $it ? deiQrMediaPath($it) : '';\n"
               "        if ($p === '' || !is_file($p)) { http_response_code(404); header('Content-Type: text/plain'); echo 'Lampiran tidak tersedia'; exit; }\n"
               "        deiWaMediaOutput($p, !empty($_GET['dl']));\n"
               "        exit;\n"
               "    }\n", what='qr_delete')
    save(API, s)
else: print('sudah', API)

# ---------------------------------------------------------------- app.js
s = rd(JS)
if TAG not in s:
    # 1) cari juga nama file lampiran
    s = rep(s, "      var sc = String(x.shortcut || ''), hay = (x.title + ' ' + sc + ' ' + x.text).toLowerCase();\n",
               "      var sc = String(x.shortcut || ''), hay = (x.title + ' ' + sc + ' ' + x.text + ' ' + (x.media ? x.media.name : '')).toLowerCase();   // " + TAG + "\n",
               what='waQrMatch')
    # 2) daftar pilih: tanda lampiran
    s = rep(s, "      var prev = String(x.text).replace(/\\s+/g, ' ');\n",
               "      var prev = String(x.text).replace(/\\s+/g, ' ');\n"
               "      if (x.media) prev = '\\uD83D\\uDCCE ' + x.media.name + (prev ? ' \\u00B7 ' + prev : '');   // " + TAG + "\n",
               what='qr prev')
    # 3) pilih template -> pasang lampiran
    s = rep(s, "  function waQrPick(i) {\n"
               "    var o = waState.qrOpen; if (!o || !o.items || !o.items[i]) return;\n"
               "    var t = waQrFill(o.items[i].text), inp = $('#waReplyInput');\n",
               "  function waQrPick(i) {\n"
               "    var o = waState.qrOpen; if (!o || !o.items || !o.items[i]) return;\n"
               "    var t = waQrFill(o.items[i].text), inp = $('#waReplyInput');\n"
               "    if (o.items[i].media) waQrAttach(o.items[i]);   // " + TAG + "\n",
               what='waQrPick')
    ATT = ("  /* " + TAG + ": lampiran template dipasang ke kotak balas, lalu dikirim/dijadwalkan lewat jalur lampiran biasa */\n"
           "  function waQrMediaUrl(id) { return API + '?action=qr_media&id=' + encodeURIComponent(id) + '&token=' + encodeURIComponent(waMediaTok()); }\n"
           "  function waQrAttach(x) {\n"
           "    var m = x.media, num = waState.current, chip = $('#waAttachChip'), send = $('#waReplySend');\n"
           "    if (!m || !num) return;\n"
           "    if (waState.attach && waState.attachNum === num) toast('Lampiran diganti dengan lampiran template.');\n"
           "    var seq = waState.qrAttSeq = (waState.qrAttSeq || 0) + 1, sendWas = send ? send.disabled : false;\n"
           "    if (send) send.disabled = true;\n"
           "    if (chip) { chip.innerHTML = '<span style=\"display:inline-flex;color:var(--muted)\">' + ico('paperclip', 16) + '</span><span style=\"flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap\">Memuat lampiran template: <strong>' + esc(m.name) + '</strong>…</span>'; chip.style.display = 'flex'; }\n"
           "    var xhr = new XMLHttpRequest();\n"
           "    xhr.open('GET', API + '?action=qr_media&id=' + encodeURIComponent(x.id) + '&_=' + Date.now());\n"
           "    xhr.setRequestHeader('X-Auth-Token', token);\n"
           "    xhr.responseType = 'blob';\n"
           "    var gagal = function (why) {\n"
           "      if (seq !== waState.qrAttSeq) return;\n"
           "      if (send) send.disabled = sendWas;\n"
           "      if (waState.attach && waState.attachNum === num) waAttachRender(''); else if (chip) { chip.style.display = 'none'; chip.innerHTML = ''; }\n"
           "      toast('Lampiran template gagal dimuat' + (why ? ' (' + why + ')' : '') + '. Lampirkan manual lewat tombol lampiran.', true);\n"
           "    };\n"
           "    xhr.onload = function () {\n"
           "      if (seq !== waState.qrAttSeq) return;\n"
           "      if (xhr.status === 401) { logout(); return; }\n"
           "      if (xhr.status !== 200 || !xhr.response) { gagal(xhr.status === 404 ? 'file tidak ada di server' : 'HTTP ' + xhr.status); return; }\n"
           "      if (waState.current !== num) { if (send) send.disabled = sendWas; return; }\n"
           "      var f;\n"
           "      try { f = new File([xhr.response], m.name, { type: m.mime || xhr.response.type }); } catch (e) { f = xhr.response; try { f.name = m.name; } catch (e2) {} }\n"
           "      if (waState.attachUrl) { try { URL.revokeObjectURL(waState.attachUrl); } catch (e) {} waState.attachUrl = null; }\n"
           "      waState.attach = f; waState.attachNum = num;\n"
           "      if (m.type === 'image') { try { waState.attachUrl = URL.createObjectURL(f); } catch (e) {} }\n"
           "      if ($('#waReplyInput')) $('#waReplyInput').placeholder = m.type === 'audio' ? 'Audio dikirim tanpa keterangan' : 'Tulis keterangan (opsional)…';\n"
           "      if (send) send.disabled = sendWas;\n"
           "      waAttachRender('');\n"
           "      if (waState.schedOpen) waSchedMediaRow();\n"
           "    };\n"
           "    xhr.onerror = function () { gagal('koneksi terputus'); };\n"
           "    xhr.send();\n"
           "  }\n")
    s = rep(s, "  function waQrKey(e) {\n", ATT + "  function waQrKey(e) {\n", what='waQrKey')
    # 4) Kelola template: kolom lampiran
    s = rep(s, "      'Variabel: <code>{nama}</code> = nama kontak, <code>{agen}</code> = nama pengirim.</p>' +\n",
               "      'Variabel: <code>{nama}</code> = nama kontak, <code>{agen}</code> = nama pengirim. Template bisa membawa lampiran (gambar, video, dokumen, audio) yang ikut terpasang saat dipilih.</p>' +\n",
               what='mgr help')
    s = rep(s, "        '<div class=\"row\"><label class=\"fl\">Isi</label><textarea id=\"qrmText\" rows=\"5\" maxlength=\"4000\" placeholder=\"Halo Kak {nama}, ...\"></textarea></div>' +\n",
               "        '<div class=\"row\"><label class=\"fl\">Isi</label><textarea id=\"qrmText\" rows=\"5\" maxlength=\"4000\" placeholder=\"Halo Kak {nama}, ...\"></textarea></div>' +\n"
               "        '<div class=\"row\"><label class=\"fl\">Lampiran <span style=\"font-weight:400;color:var(--muted)\">(opsional)</span></label><div id=\"qrmMedia\"></div>' +   // " + TAG + "\n"
               "          '<input type=\"file\" id=\"qrmFile\" accept=\".jpg,.jpeg,.png,.mp4,.3gp,.mp3,.ogg,.m4a,.aac,.amr,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.zip\" style=\"display:none\">' +\n"
               "          '<p class=\"help\" style=\"margin:4px 0 0\">JPG/PNG maks 5 MB; video, audio, PDF/dokumen maks 16 MB. Dengan lampiran, isi menjadi keterangan (maks 1.024 karakter); pesan suara tanpa keterangan.</p></div>' +\n",
               what='mgr isi')
    s = rep(s, "    var reset = function () { editId = ''; $('#qrmTitle').value = ''; $('#qrmSc').value = ''; $('#qrmText').value = ''; $('#qrmMode').textContent = 'Template baru'; };\n",
               "    var mEdit = null, mNew = null, mDrop = false;   // " + TAG + "\n"
               "    var mRender = function () {\n"
               "      var el = $('#qrmMedia'); if (!el) return;\n"
               "      var btn = function (id, lbl, red) { return '<a href=\"#\" id=\"' + id + '\" style=\"font-weight:600;text-decoration:none' + (red ? ';color:#b91c1c' : '') + '\">' + lbl + '</a>'; };\n"
               "      if (mNew) el.innerHTML = ico('paperclip', 14) + ' <b>' + esc(mNew.name) + '</b> <span class=\"help\" style=\"margin:0\">' + waFmtSize(mNew.size) + (mEdit && !mDrop ? ' · menggantikan ' + esc(mEdit.name) : '') + '</span> · ' + btn('qrmMNew', 'Ganti') + ' · ' + btn('qrmMUndo', 'Batal', 1);\n"
               "      else if (mEdit && !mDrop) el.innerHTML = (mEdit.type === 'image' ? '<img src=\"' + waQrMediaUrl(editId) + '\" alt=\"\" style=\"width:44px;height:44px;object-fit:cover;border-radius:6px;vertical-align:middle;margin-right:6px\" onerror=\"this.style.display=\\'none\\'\">' : ico('paperclip', 14) + ' ') +\n"
               "        '<b>' + esc(mEdit.name) + '</b> <span class=\"help\" style=\"margin:0\">' + waFmtSize(mEdit.size || 0) + '</span> · ' + btn('qrmMNew', 'Ganti') + ' · ' + btn('qrmMDel', 'Hapus lampiran', 1);\n"
               "      else el.innerHTML = '<button type=\"button\" class=\"btn ghost sm\" id=\"qrmMNew\">' + ico('paperclip', 14) + ' Pilih file</button>' + (mEdit && mDrop ? ' <span class=\"help\" style=\"margin:0\">lampiran ' + esc(mEdit.name) + ' akan dihapus · </span>' + btn('qrmMUndo', 'Urungkan') : '');\n"
               "      if ($('#qrmMNew')) $('#qrmMNew').onclick = function (e) { e.preventDefault(); $('#qrmFile').click(); };\n"
               "      if ($('#qrmMDel')) $('#qrmMDel').onclick = function (e) { e.preventDefault(); mDrop = true; mRender(); };\n"
               "      if ($('#qrmMUndo')) $('#qrmMUndo').onclick = function (e) { e.preventDefault(); if (mNew) mNew = null; else mDrop = false; $('#qrmFile').value = ''; mRender(); };\n"
               "    };\n"
               "    $('#qrmFile').onchange = function () {\n"
               "      var f = this.files && this.files[0]; if (!f) return;\n"
               "      var ext = (f.name.split('.').pop() || '').toLowerCase(), kind = WA_ATT_KIND[ext];\n"
               "      if (!kind) { toast('Jenis file .' + ext + ' belum didukung. Bisa: JPG/PNG, MP4, MP3/OGG/M4A, PDF, Word, Excel, PowerPoint, TXT, CSV, ZIP.', true); this.value = ''; return; }\n"
               "      if (f.size > WA_ATT_MB[kind] * 1048576) { toast('Batas WhatsApp untuk file ini: ' + WA_ATT_MB[kind] + ' MB (file Anda ' + waFmtSize(f.size) + ').', true); this.value = ''; return; }\n"
               "      mNew = f; mRender();\n"
               "    };\n"
               "    var reset = function () { editId = ''; $('#qrmTitle').value = ''; $('#qrmSc').value = ''; $('#qrmText').value = ''; $('#qrmMode').textContent = 'Template baru'; mEdit = null; mNew = null; mDrop = false; $('#qrmFile').value = ''; mRender(); };\n",
               what='mgr reset')
    s = rep(s, "          '<div style=\"white-space:pre-wrap;font-size:13px;color:var(--muted);margin-top:3px;max-height:4.2em;overflow:hidden\">' + esc(x.text) + '</div></div>' +\n",
               "          (x.media ? '<div style=\"font-size:12.5px;margin-top:3px\">' + ico('paperclip', 13) + ' ' + esc(x.media.name) + ' <span style=\"color:var(--muted)\">' + waFmtSize(x.media.size || 0) + '</span></div>' : '') +   // " + TAG + "\n"
               "          '<div style=\"white-space:pre-wrap;font-size:13px;color:var(--muted);margin-top:3px;max-height:4.2em;overflow:hidden\">' + esc(x.text) + '</div></div>' +\n",
               what='mgr list')
    s = rep(s, "        editId = x.id; $('#qrmTitle').value = x.title || ''; $('#qrmSc').value = x.shortcut || ''; $('#qrmText').value = x.text || '';\n",
               "        editId = x.id; $('#qrmTitle').value = x.title || ''; $('#qrmSc').value = x.shortcut || ''; $('#qrmText').value = x.text || '';\n"
               "        mEdit = x.media || null; mNew = null; mDrop = false; $('#qrmFile').value = ''; mRender();   // " + TAG + "\n",
               what='mgr edit')
    s = rep(s, "      var body = { id: editId, title: $('#qrmTitle').value, shortcut: $('#qrmSc').value, text: $('#qrmText').value };\n"
               "      if (!body.text.trim()) { toast('Isi template wajib diisi.', true); $('#qrmText').focus(); return; }\n"
               "      this.disabled = true; var btn = this;\n"
               "      api('qr_save', { method: 'POST', body: body }).then(function (r) {\n"
               "        btn.disabled = false;\n",
               "      var body = { id: editId, title: $('#qrmTitle').value, shortcut: $('#qrmSc').value, text: $('#qrmText').value };\n"
               "      var hasM = !!mNew || (!!mEdit && !mDrop), mk = mNew ? WA_ATT_KIND[(mNew.name.split('.').pop() || '').toLowerCase()] : (hasM ? mEdit.type : '');   // " + TAG + "\n"
               "      if (!body.text.trim() && !hasM) { toast('Isi template wajib diisi (atau pilih lampiran).', true); $('#qrmText').focus(); return; }\n"
               "      if (mk === 'audio' && body.text.trim()) { toast('Pesan suara tidak bisa diberi keterangan — kosongkan isi, atau buat template teks terpisah.', true); return; }\n"
               "      if (hasM && body.text.trim().length > 1024) { toast('Template berlampiran: isi menjadi keterangan, maksimal 1.024 karakter.', true); return; }\n"
               "      this.disabled = true; var btn = this;\n"
               "      var kirim = (mNew || (mEdit && mDrop)) ? function () {\n"
               "        var fd = new FormData();\n"
               "        Object.keys(body).forEach(function (k) { fd.append(k, body[k]); });\n"
               "        if (mNew) fd.append('file', mNew, mNew.name); else fd.append('remove_media', '1');\n"
               "        return new Promise(function (res) { waSchedUpload('qr_save', fd, mNew ? function (p) { $('#qrmMode').textContent = p < 100 ? 'Mengunggah ' + p + '%…' : 'Menyimpan…'; } : null, res); });\n"
               "      } : function () { return api('qr_save', { method: 'POST', body: body }); };\n"
               "      kirim().then(function (r) {\n"
               "        btn.disabled = false;\n",
               what='mgr save')
    # 5) Pusat Bantuan: artikel template
    s = rep(s, "    { id: 'release', roles: R_ALL, t: 'Mengembalikan chat ke bot / antrean'",
               "    { id: 'template', roles: R_ALL, t: 'Memakai template balasan (teks & lampiran)', k: 'template balasan cepat quick reply pintasan shortcut garis miring slash lampiran gambar foto brosur pdf katalog video file attach media',\n"
               "      s: ['Di kotak balas <b>Percakapan WA</b>, klik tombol <b>Template</b> atau ketik <b>/</b> lalu nama pintasan (mis. <b>/harga</b>), pilih dengan panah lalu <b>Enter</b>.',\n"
               "          'Bila template punya lampiran (brosur, foto, PDF, video), file langsung terpasang di atas kotak balas dan isi template menjadi keterangannya. Periksa, lalu <b>Kirim</b> atau <b>Jadwalkan</b>.',\n"
               "          'Membuat/mengubah template (Admin/Supervisor): klik <b>Kelola template</b>, isi judul, pintasan, isi, lalu <b>Pilih file</b> di Lampiran bila perlu &rsaquo; <b>Simpan template</b>.',\n"
               "          'Lampiran: JPG/PNG maks 5 MB, video/audio/PDF/dokumen maks 16 MB. Keterangan maks 1.024 karakter; pesan suara dikirim tanpa keterangan.'] },   // " + TAG + "\n"
               "    { id: 'release', roles: R_ALL, t: 'Mengembalikan chat ke bot / antrean'", what='artikel template')
    save(JS, s)
else: print('sudah', JS)

# ---------------------------------------------------------------- app.js (2) menu kiri Template Balasan
TAG2 = 'v1.2.199: template-menu'
s = rd(JS)
if TAG2 not in s:
    assert TAG in s, 'bagian template-media belum terpasang'
    s = rep(s, "  function waQrManager() {\n", "  function waQrManager(host) {   // " + TAG2 + ": host = isi halaman menu Template Balasan (tanpa = modal)\n", what='mgr sig')
    s = rep(s, "      '</div><div id=\"qrmList\"></div></div>';\n    document.body.appendChild(ov);\n    var editId = '';\n",
               "      '</div><div id=\"qrmList\"></div></div>';\n"
               "    if (host) {   // " + TAG2 + "\n"
               "      ov.id = ''; ov.style.cssText = ''; host.innerHTML = ''; host.appendChild(ov);\n"
               "      ov.firstChild.style.cssText = 'margin:0;max-width:820px';\n"
               "      $('#qrmX').parentNode.remove();\n"
               "    } else document.body.appendChild(ov);\n"
               "    var editId = '';\n", what='mgr host')
    s = rep(s, "    var esck = function (e) { if (e.key === 'Escape') tutup(); };\n    document.addEventListener('keydown', esck);\n    ov.onclick = function (e) { if (e.target === ov) tutup(); };\n    $('#qrmX').onclick = tutup;\n",
               "    var esck = function (e) { if (e.key === 'Escape') tutup(); };\n"
               "    if (!host) { document.addEventListener('keydown', esck); ov.onclick = function (e) { if (e.target === ov) tutup(); }; $('#qrmX').onclick = tutup; }   // " + TAG2 + "\n", what='mgr esc')
    s = rep(s, "    $('#qrmList').innerHTML = '<p class=\"help\">Memuat…</p>';\n    waQrLoad(true).then(render);\n",
               "    $('#qrmList').innerHTML = '<p class=\"help\">Memuat…</p>';\n    waQrLoad(true).then(render);\n"
               "    if (host) qrtplRefresh = function () { waQrLoad(true).then(render); };   // " + TAG2 + "\n", what='mgr load')
    s = rep(s, "    if ($('#waQrManage')) $('#waQrManage').onclick = function (e) { e.preventDefault(); waQrClose(); waQrManager(); };\n",
               "    if ($('#waQrManage')) $('#waQrManage').onclick = function (e) { e.preventDefault(); waQrClose(); showTab('qrtpl'); };   // " + TAG2 + ": ke menu kiri\n", what='link kelola')
    s = rep(s, "  /* Kelola template (Super Admin/Admin/Supervisor) */\n",
               "  /* Kelola template (Super Admin/Admin/Supervisor) */\n"
               "  var qrtplRefresh = null;   // " + TAG2 + "\n", what='mgr komentar')
    s = rep(s, "    blast: loadBlast,\n", "    blast: loadBlast,\n    qrtpl: function () { waQrManager($('#qrtplRoot')); },   // " + TAG2 + "\n", what='loaders')
    s = rep(s, "    else if (tab === 'kontak') fetchContacts();   // v1.2.106: kontak-sinkron (data Kontak selalu segar)\n",
               "    else if (tab === 'kontak') fetchContacts();   // v1.2.106: kontak-sinkron (data Kontak selalu segar)\n"
               "    else if (tab === 'qrtpl' && qrtplRefresh) qrtplRefresh();   // " + TAG2 + "\n", what='showTab')
    s = rep(s, "klik <b>Kelola template</b>, isi judul, pintasan, isi,", "buka menu <b>Template Balasan</b> di kiri (atau <b>Kelola template</b> di daftar template), isi judul, pintasan, isi,", what='artikel kelola')
    s = rep(s, "pesan suara dikirim tanpa keterangan.'] },   // " + TAG + "\n",
               "pesan suara dikirim tanpa keterangan.'],\n"
               "      show: [{ tab: 'qrtpl', el: '#qrtplRoot', title: 'Template Balasan', body: '<p>Tambah, ubah, atau hapus template beserta lampirannya di sini.</p>' }] },   // " + TAG + "; " + TAG2 + "\n", what='artikel show')
    save(JS, s)
else: print('sudah (menu)', JS)

# ---------------------------------------------------------------- index.html
s = rd(HT)
if TAG not in s:
    s = rep(s, '<script src="app.js?v=1.2.198"></script>', '<script src="app.js?v=1.2.199"></script><!-- ' + TAG + ' -->', what='app.js?v')
    save(HT, s)
else: print('sudah', HT)
s = rd(HT)
if 'template-menu' not in s:
    s = rep(s, '      <button data-tab="webchat"  data-role="super_admin,admin,supervisor,wa_agent" data-icon="monitor-smartphone"><span class="ic"></span> Percakapan Web</button>\n',
            '      <button data-tab="qrtpl"    data-role="super_admin,admin,supervisor" data-icon="file-text"><span class="ic"></span> Template Balasan</button><!-- v1.2.199: template-menu -->\n'
            '      <button data-tab="webchat"  data-role="super_admin,admin,supervisor,wa_agent" data-icon="monitor-smartphone"><span class="ic"></span> Percakapan Web</button>\n', what='nav')
    s = rep(s, '    <section class="panel" id="panel-blast">\n',
            '    <section class="panel" id="panel-qrtpl"><!-- v1.2.199: template-menu -->\n'
            '      <div class="ph"><h2>Template Balasan WA</h2><p>Balasan cepat untuk agent di Percakapan WA &mdash; teks dan lampiran (gambar, video, dokumen, audio).</p></div>\n'
            '      <div id="qrtplRoot"></div>\n'
            '    </section>\n'
            '    <section class="panel" id="panel-blast">\n', what='panel')
    save(HT, s)
else: print('sudah (menu)', HT)
print('patch v1.2.199 selesai')
