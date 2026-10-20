#!/usr/bin/env python3
"""v1.2.95 — Foto di Knowledge Base, dikirim otomatis bot WhatsApp bila pelanggan minta
("bisa kirim foto kamarnya?", "ada foto menunya?", "kirim QR pembayarannya").
Pemakaian: python3 patch_v1295_kb_foto.py <root dei-tenant>   (idempoten; backup *.bak-v1295-*)
Butuh v1.2.94 (wa-media) sudah terpasang."""
import sys, os, time, shutil
TEN = sys.argv[1]
STAMP = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.95: kb-foto'

def patch(root, rel, pairs):
    p = os.path.join(root, rel)
    s = open(p, encoding='utf-8').read()
    if MARK in s: print('sudah dipatch:', rel); return
    if rel == 'api/index.php' and 'v1.2.94: wa-media' not in s: sys.exit('GAGAL: v1.2.94 (wa-media) belum terpasang')
    for old, new in pairs:
        n = s.count(old)
        if n != 1: sys.exit(f'GAGAL {rel}: anchor {n}x:\n{old[:200]}')
        s = s.replace(old, new)
    shutil.copy2(p, p + '.bak-v1295-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

PHP_FUNCS = r'''/* ============================================================================
 * v1.2.95: kb-foto — FOTO di entri Knowledge Base (maks 6/entri, JPG/PNG) di
 * data/kb-media/. Untuk WhatsApp (Meta & WAHA) entri berfoto diberi kode
 * [[FOTO:<id>]] di prompt; bila pelanggan minta melihat foto, AI menulis kode
 * itu, sistem membuangnya dari teks lalu mengirim fotonya setelah balasan.
 * ========================================================================= */
define('KB_MEDIA_DIR', DATA_DIR . '/kb-media');
define('KB_FOTO_MAX', 6);
function deiKbFotoClean($imgs) {
    $out = []; $seen = [];
    foreach ((array)$imgs as $im) {
        $f = is_array($im) ? (string)($im['file'] ?? '') : (string)$im;
        if (!preg_match('/^[a-f0-9]{20}\.(jpg|png)$/', $f) || isset($seen[$f]) || !is_file(KB_MEDIA_DIR . '/' . $f)) continue;
        $seen[$f] = true;
        $out[] = ['file' => $f];
        if (count($out) >= KB_FOTO_MAX) break;
    }
    return $out;
}
function deiKbFotoAktif($s, $channel) {
    return $channel === 'whatsapp' && in_array((string)($s['whatsapp_api']['provider'] ?? 'meta'), ['meta', 'waha'], true);
}
function deiKbFotoPrompt() {
    return "=== FOTO (WhatsApp) ===\n"
        . "Beberapa entri Knowledge Base punya foto, ditandai '(N foto tersedia — kode [[FOTO:...]])'. "
        . "Jika pelanggan meminta melihat foto/gambar/katalog/menu/kamar/produk/QR pembayaran yang sesuai dengan entri bertanda itu, "
        . "jawab singkat lalu tulis kode entri itu PERSIS di baris terakhir jawaban (maksimal 2 kode); fotonya dikirim otomatis setelah teks. "
        . "Jangan mengarang kode, jangan menulis kode bila pelanggan tidak meminta melihat foto, dan jangan menjelaskan kode itu kepada pelanggan. "
        . "Jika foto yang diminta tidak ada di Knowledge Base, katakan fotonya belum tersedia.";
}
/* Buang kode foto dari jawaban AI. Hasil: [teks bersih, daftar id entri]. */
function deiKbFotoExtract($answer) {
    $ids = [];
    $answer = preg_replace_callback('/\[{1,2}\s*FOTO\s*:\s*([A-Za-z0-9_\-]+)\s*\]{1,2}/i', function ($m) use (&$ids) { $ids[] = $m[1]; return ''; }, (string)$answer);
    $answer = preg_replace("/[ \t]+\n/", "\n", $answer);
    $answer = trim(preg_replace("/\n{3,}/", "\n\n", $answer));
    return [$answer, array_values(array_unique($ids))];
}
/* Kirim foto entri KB (maks 2 entri, 8 foto). Hasil: [meta media salinan untuk log, judul entri terkirim, id terkirim]. */
function deiKbFotoSend($wa, $to, $ids) {
    if (!$ids) return [[], [], []];
    $byId = [];
    foreach ((array)readJson(KB_FILE, []) as $e) { if (!empty($e['id'])) $byId[(string)$e['id']] = $e; }
    $num = preg_replace('/\D/', '', (string)$to);
    $sent = []; $titles = []; $okIds = []; $n = 0;
    foreach (array_slice($ids, 0, 2) as $id) {
        $e = $byId[$id] ?? null;
        if (!$e) { error_log('kb-foto: kode tidak dikenal ' . $id); continue; }
        $imgs = deiKbFotoClean($e['images'] ?? []);
        if (!$imgs) continue;
        $kirim = 0;
        foreach ($imgs as $im) {
            if ($n >= 8) break 2;
            $p = KB_MEDIA_DIR . '/' . $im['file'];
            if (!waSendImage($wa, $to, $p)) { error_log('kb-foto: gagal kirim ' . $im['file'] . ' — ' . ($GLOBALS['wa_last_error'] ?? '')); continue; }
            $n++; $kirim++;
            $meta = ['type' => 'image', 'kb' => (string)$id];   // salinan untuk thread dashboard (ikut masa simpan media)
            $dir = WA_MEDIA_DIR . '/' . $num;
            if (!is_dir($dir)) @mkdir($dir, 0755, true);
            $fn = substr(sha1($im['file'] . '|' . microtime(true) . '|' . mt_rand()), 0, 20) . '.' . pathinfo($p, PATHINFO_EXTENSION);
            if ($num !== '' && @copy($p, $dir . '/' . $fn)) { $meta['file'] = $num . '/' . $fn; $meta['size'] = (int)filesize($p); }
            else $meta['error'] = 'unavailable';
            $sent[] = $meta;
        }
        if ($kirim) { $titles[] = trim((string)($e['title'] ?? '')); $okIds[] = (string)$id; }
    }
    return [$sent, $titles, $okIds];
}
function waSendImage($wa, $to, $path, $caption = '') {
    $GLOBALS['wa_last_error'] = '';
    if (!is_file($path)) { $GLOBALS['wa_last_error'] = 'File foto tidak ada.'; return false; }
    $mime = (strtolower(pathinfo($path, PATHINFO_EXTENSION)) === 'png') ? 'image/png' : 'image/jpeg';
    $prov = (string)($wa['provider'] ?? 'meta');
    if ($prov === 'waha') {
        $to = waNormNum($to);
        list($c, $d) = wahaApi($wa, 'POST', '/api/sendImage', ['session' => wahaSession($wa), 'chatId' => $to . '@c.us',
            'file' => ['mimetype' => $mime, 'filename' => basename($path), 'data' => base64_encode((string)file_get_contents($path))],
            'caption' => (string)$caption]);
        if ($c >= 200 && $c < 300) { $id = is_array($d) ? wahaMsgId($d) : ''; if ($id !== '') wahaRememberSent($to, $id, ''); return true; }
        $GLOBALS['wa_last_error'] = wahaErr($c, $d, 'Kirim foto lewat WAHA gagal.');
        return false;
    }
    if ($prov !== 'meta') { $GLOBALS['wa_last_error'] = 'Penyedia ini tidak mendukung kirim foto.'; return false; }
    $token = (string)($wa['access_token'] ?? ''); $pnid = (string)($wa['phone_number_id'] ?? '');
    if ($token === '' || $pnid === '') { $GLOBALS['wa_last_error'] = 'Access Token / Phone Number ID kosong.'; return false; }
    $mid = deiMetaMediaId($wa, $path, $mime);
    if ($mid === '') return false;
    $img = ['id' => $mid]; if ((string)$caption !== '') $img['caption'] = (string)$caption;
    $payload = ['messaging_product' => 'whatsapp', 'recipient_type' => 'individual', 'to' => $to, 'type' => 'image', 'image' => $img];
    $ch = curl_init('https://graph.facebook.com/v21.0/' . rawurlencode($pnid) . '/messages');
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_POST => true, CURLOPT_TIMEOUT => 20,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'Authorization: Bearer ' . $token],
        CURLOPT_POSTFIELDS => json_encode($payload, JSON_UNESCAPED_UNICODE)]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    if ($code >= 200 && $code < 300) { waOutCount('service'); return true; }
    $d = json_decode((string)$resp, true);
    $GLOBALS['wa_last_error'] = (is_array($d) && isset($d['error']['message'])) ? (string)$d['error']['message'] : ('HTTP ' . $code);
    deiMetaMediaIdForget($wa, $path);   // id bisa kedaluwarsa -> unggah ulang lain kali
    return false;
}
/* Foto KB diunggah ke Meta sekali; id disimpan 25 hari (id media Meta berlaku 30 hari). */
function deiMetaMediaKey($wa, $path) { return (string)($wa['phone_number_id'] ?? '') . '|' . basename($path) . '|' . (int)@filemtime($path); }
function deiMetaMediaId($wa, $path, $mime) {
    $cf = KB_MEDIA_DIR . '/.meta-ids.json';
    $k = deiMetaMediaKey($wa, $path);
    $all = readJson($cf, []); if (!is_array($all)) $all = [];
    if (!empty($all[$k]['id']) && time() - (int)($all[$k]['t'] ?? 0) < 25 * 86400) return (string)$all[$k]['id'];
    $ch = curl_init('https://graph.facebook.com/v21.0/' . rawurlencode((string)($wa['phone_number_id'] ?? '')) . '/media');
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_POST => true, CURLOPT_TIMEOUT => 45,
        CURLOPT_HTTPHEADER => ['Authorization: Bearer ' . (string)($wa['access_token'] ?? '')],
        CURLOPT_POSTFIELDS => ['messaging_product' => 'whatsapp', 'type' => $mime, 'file' => new CURLFile($path, $mime, basename($path))]]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    $d = json_decode((string)$resp, true);
    if ($code < 200 || $code >= 300 || !is_array($d) || empty($d['id'])) {
        $GLOBALS['wa_last_error'] = 'Unggah foto ke Meta gagal: ' . ((is_array($d) && isset($d['error']['message'])) ? $d['error']['message'] : ('HTTP ' . $code));
        return '';
    }
    foreach ($all as $kk => $v) { if (time() - (int)($v['t'] ?? 0) > 25 * 86400) unset($all[$kk]); }
    $all[$k] = ['id' => (string)$d['id'], 't' => time()];
    writeJson($cf, $all);
    return (string)$d['id'];
}
function deiMetaMediaIdForget($wa, $path) {
    $cf = KB_MEDIA_DIR . '/.meta-ids.json';
    $all = readJson($cf, []); if (!is_array($all)) return;
    $k = deiMetaMediaKey($wa, $path);
    if (isset($all[$k])) { unset($all[$k]); writeJson($cf, $all); }
}

function buildMessages($message, $history) {'''

patch(TEN, 'api/index.php', [
    ("define('DEI_VERSION', 'v1.2.94');", "define('DEI_VERSION', 'v1.2.95');"),
    ("function buildMessages($message, $history) {", PHP_FUNCS),
    # prompt: tandai entri berfoto (WA saja) + aturan foto
    ("        $kbText .= '[' . $cat . '] ' . $tit . \"\\n\" . $con . \"\\n\\n\";\n    }\n    $kbText = trim($kbText);\n",
     "        $deiFoto = ($deiFotoOn && !empty($e['id'])) ? deiKbFotoClean($e['images'] ?? []) : [];   // " + MARK + "\n"
     "        if ($deiFoto) $deiAdaFoto = true;\n"
     "        $kbText .= '[' . $cat . '] ' . $tit . \"\\n\" . $con . ($deiFoto ? \"\\n(\" . count($deiFoto) . ' foto tersedia — kode [[FOTO:' . $e['id'] . ']])' : '') . \"\\n\\n\";\n"
     "    }\n    $kbText = trim($kbText);\n"
     "    if ($deiAdaFoto) $deiPriceBlk = trim($deiPriceBlk . \"\\n\\n\" . deiKbFotoPrompt());   // " + MARK + "\n"),
    ("    // Build the full-KB block (Strategy B: send everything, let Claude pick what's relevant).\n    $kbText = '';\n",
     "    // Build the full-KB block (Strategy B: send everything, let Claude pick what's relevant).\n    $kbText = '';\n"
     "    $deiFotoOn = deiKbFotoAktif($s, $channel); $deiAdaFoto = false;   // " + MARK + "\n"),
    # WA: ambil kode foto dari jawaban, kirim foto setelah teks
    ("    list($ok, $answer, $_kbUsed, $usage) = generateAnswer($s, $text, $history, 'whatsapp');   // v1.2.89\n",
     "    list($ok, $answer, $_kbUsed, $usage) = generateAnswer($s, $text, $history, 'whatsapp');   // v1.2.89\n"
     "    $deiFotoIds = [];   // " + MARK + "\n"
     "    if ($ok) list($answer, $deiFotoIds) = deiKbFotoExtract($answer);\n"),
    ("    if (!$ok || trim($answer) === '') {\n",
     "    if (!$ok || (trim($answer) === '' && !$deiFotoIds)) {   // " + MARK + ": jawaban boleh hanya foto\n"),
    ("    $deiSent = waSend($wa, $from, $answer);\n",
     "    $deiSent = (trim($answer) !== '') ? waSend($wa, $from, $answer) : true;   // " + MARK + "\n"
     "    $deiFotoOut = []; $deiFotoJudul = []; $deiFotoKirim = [];\n"
     "    if (!$deiAiError && $deiFotoIds) {\n"
     "        try { list($deiFotoOut, $deiFotoJudul, $deiFotoKirim) = deiKbFotoSend($wa, $from, $deiFotoIds); }\n"
     "        catch (\\Throwable $e) { error_log('kb-foto: ' . $e->getMessage()); }\n"
     "        if (trim($answer) === '' && !$deiFotoOut) {   // AI hanya menulis kode tapi foto gagal terkirim\n"
     "            $answer = 'Mohon maaf, fotonya belum bisa kami kirim saat ini. Admin kami akan membantu mengirimkannya.';\n"
     "            $deiSent = waSend($wa, $from, $answer);\n"
     "        }\n"
     "    }\n"),
    ("        $history[] = ['role' => 'assistant', 'content' => $answer];\n",
     "        $history[] = ['role' => 'assistant', 'content' => trim($answer . ($deiFotoKirim ? \"\\n[[FOTO:\" . implode(']] [[FOTO:', $deiFotoKirim) . ']]' : ''))];   // " + MARK + "\n"),
    ("    $logs = logPrepend(array_merge($logBase, ['a' => $answer], $deiAiError ? ['ai_error' => true] : []), $logLimit);  // v1.2.17 + v1.2.58 kunci\n",
     "    $deiLogA = (trim($answer) !== '') ? $answer : ('[Foto: ' . implode(', ', array_filter($deiFotoJudul)) . ']');   // " + MARK + "\n"
     "    $logs = logPrepend(array_merge($logBase, ['a' => $deiLogA], $deiAiError ? ['ai_error' => true] : [], $deiFotoOut ? ['media_out' => $deiFotoOut] : []), $logLimit);  // v1.2.17 + v1.2.58 kunci\n"),
    # simpan KB: foto ikut + bersihkan file yatim
    ("                'topic'    => trim((string)($e['topic'] ?? '')),  // v1.2.12 Fase 3: topic tag untuk routing\n            ];\n        }\n        writeJson(KB_FILE, $clean);\n",
     "                'topic'    => trim((string)($e['topic'] ?? '')),  // v1.2.12 Fase 3: topic tag untuk routing\n"
     "                'images'   => deiKbFotoClean($e['images'] ?? []),   // " + MARK + "\n"
     "            ];\n        }\n        writeJson(KB_FILE, $clean);\n"
     "        try {   // " + MARK + ": foto yang tidak dipakai entri mana pun & berumur > 1 hari dihapus\n"
     "            $refs = [];\n"
     "            foreach ($clean as $c) { foreach ($c['images'] as $im) $refs[$im['file']] = true; }\n"
     "            foreach ((array)glob(KB_MEDIA_DIR . '/*') as $f) {\n"
     "                $b = basename($f);\n"
     "                if (preg_match('/^[a-f0-9]{20}\\.(jpg|png)$/', $b) && !isset($refs[$b]) && time() - (int)@filemtime($f) > 86400) @unlink($f);\n"
     "            }\n"
     "        } catch (\\Throwable $e) {}\n"),
    # gabung duplikat: foto dari semua anggota digabung
    ("                'topic'    => $topik,\n            ];\n",
     "                'topic'    => $topik,\n"
     "                'images'   => deiKbFotoClean(array_merge(...array_map(function ($a) { return (array)($a['images'] ?? []); }, $anggota))),   // " + MARK + "\n"
     "            ];\n"),
    # thread + endpoint foto KB
    ("                       'media' => is_array($e['media'] ?? null) ? $e['media'] : null];   // v1.2.94: wa-media\n",
     "                       'media' => is_array($e['media'] ?? null) ? $e['media'] : null,   // v1.2.94: wa-media\n"
     "                       'media_out' => is_array($e['media_out'] ?? null) ? $e['media_out'] : null];   // " + MARK + "\n"),
    ("    case 'save_kb': {\n",
     "    /* ---------- " + MARK + ": unggah foto entri KB (JPG/PNG, maks 5 MB; dikecilkan di browser) ---------- */\n"
     "    case 'kb_image_upload': {\n"
     "        requireAuth(['super_admin','admin']);\n"
     "        $in = bodyInput();\n"
     "        if (!preg_match('#^data:image/(jpeg|png);base64,(.+)$#s', (string)($in['data'] ?? ''), $mi)) jsonOut(['ok' => false, 'error' => 'Foto harus JPG atau PNG.'], 400);\n"
     "        $bin = base64_decode($mi[2], true);\n"
     "        if ($bin === false || $bin === '') jsonOut(['ok' => false, 'error' => 'Data foto rusak.'], 400);\n"
     "        if (strlen($bin) > 5 * 1024 * 1024) jsonOut(['ok' => false, 'error' => 'Foto maksimal 5 MB.'], 400);\n"
     "        $info = @getimagesizefromstring($bin);\n"
     "        if (!$info || !in_array($info[2], [IMAGETYPE_JPEG, IMAGETYPE_PNG], true)) jsonOut(['ok' => false, 'error' => 'File bukan gambar JPG/PNG yang valid.'], 400);\n"
     "        if (!is_dir(KB_MEDIA_DIR)) @mkdir(KB_MEDIA_DIR, 0755, true);\n"
     "        $fn = substr(sha1($bin . microtime(true) . mt_rand()), 0, 20) . ($info[2] === IMAGETYPE_PNG ? '.png' : '.jpg');\n"
     "        if (@file_put_contents(KB_MEDIA_DIR . '/' . $fn, $bin) === false) jsonOut(['ok' => false, 'error' => 'Gagal menyimpan foto di server.'], 500);\n"
     "        jsonOut(['ok' => true, 'file' => $fn, 'w' => (int)$info[0], 'h' => (int)$info[1], 'size' => strlen($bin)]);\n"
     "        break;\n"
     "    }\n"
     "    case 'kb_media': {\n"
     "        requireAuth(['super_admin','admin']);\n"
     "        $f = (string)($_GET['f'] ?? '');\n"
     "        if (!preg_match('/^[a-f0-9]{20}\\.(jpg|png)$/', $f) || !is_file(KB_MEDIA_DIR . '/' . $f)) { http_response_code(404); header('Content-Type: text/plain'); echo 'not found'; exit; }\n"
     "        deiWaMediaOutput(KB_MEDIA_DIR . '/' . $f);\n"
     "        exit;\n"
     "    }\n\n"
     "    case 'save_kb': {\n"),
])

JS_KB = r'''  /* v1.2.95: kb-foto — foto entri KB yang dikirim bot WhatsApp */
  function kbImgUrl(f) { return API + '?action=kb_media&f=' + encodeURIComponent(f) + '&token=' + encodeURIComponent(token); }
  function kbImgsHtml(e) {
    var imgs = e.images || [];
    return '<div class="kb-imgs" style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:6px">' +
      imgs.map(function (im, i) {
        return '<div style="position:relative;width:84px;height:84px;border-radius:8px;overflow:hidden;border:1px solid var(--line)">' +
          '<a href="' + kbImgUrl(im.file) + '" target="_blank" rel="noopener"><img src="' + kbImgUrl(im.file) + '" alt="" style="width:100%;height:100%;object-fit:cover;display:block"></a>' +
          '<button type="button" class="kb-img-del" data-i="' + i + '" title="Hapus foto" style="position:absolute;top:3px;right:3px;width:22px;height:22px;border-radius:50%;border:0;background:rgba(0,0,0,.65);color:#fff;cursor:pointer;font-size:14px;line-height:22px;padding:0">&times;</button></div>';
      }).join('') +
      (imgs.length < 6 ? '<label style="width:84px;height:84px;border:1px dashed var(--muted);border-radius:8px;display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;font-size:12px;color:var(--muted);text-align:center;gap:2px">' +
        '<span style="font-size:22px;line-height:1">+</span>Tambah foto<input type="file" class="kb-img-in" accept="image/jpeg,image/png,image/webp,image/*" multiple style="display:none"></label>' : '') +
      '</div><div class="help">Dikirim bot WhatsApp bila pelanggan minta, mis. <i>"bisa kirim foto kamarnya?"</i>, <i>"ada foto menunya?"</i>, <i>"kirim QR pembayarannya"</i>. Maks 6 foto per entri. Tulis judul & isi yang jelas supaya bot tahu foto ini tentang apa, lalu klik <b>Simpan</b>.</div>';
  }
  // Foto besar dikecilkan (maks 1600px, JPEG). PNG kecil (mis. QR) dikirim apa adanya supaya tetap tajam.
  function kbPrepImage(file) {
    return new Promise(function (resolve, reject) {
      if (!/^image\//.test(file.type || '')) return reject(new Error(file.name + ' bukan file gambar'));
      var rd = new FileReader();
      rd.onerror = function () { reject(new Error('File tidak terbaca')); };
      rd.onload = function () {
        if (file.type === 'image/png' && file.size <= 1500000) return resolve(rd.result);
        var img = new Image();
        img.onerror = function () { reject(new Error('Format gambar ' + file.name + ' tidak didukung')); };
        img.onload = function () {
          var w = img.naturalWidth, h = img.naturalHeight, r = Math.min(1, 1600 / Math.max(w, h));
          var c = document.createElement('canvas'); c.width = Math.max(1, Math.round(w * r)); c.height = Math.max(1, Math.round(h * r));
          var x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, c.width, c.height); x.drawImage(img, 0, 0, c.width, c.height);
          resolve(c.toDataURL('image/jpeg', 0.88));
        };
        img.src = rd.result;
      };
      rd.readAsDataURL(file);
    });
  }

  function renderKb() {'''

patch(TEN, 'dashboard/chatbot-ai/app.js', [
    ("  function renderKb() {", JS_KB),
    ("        '<small>' + (e.category ? '<em>' + esc(e.category) + '</em> · ' : '') + (esc(snip) || '—') + '</small></button>';",
     "        '<small>' + (e.category ? '<em>' + esc(e.category) + '</em> · ' : '') + ((e.images && e.images.length) ? '<em>' + e.images.length + ' foto</em> · ' : '') + (esc(snip) || '—') + '</small></button>';   // v1.2.95"),
    ("        '<div class=\"row\"><label class=\"fl\">Isi / Jawaban</label><textarea class=\"kb-content\">' + esc(e.content) + '</textarea></div>' +\n",
     "        '<div class=\"row\"><label class=\"fl\">Isi / Jawaban</label><textarea class=\"kb-content\">' + esc(e.content) + '</textarea></div>' +\n"
     "        '<div class=\"row\"><label class=\"fl\">Foto untuk WhatsApp</label>' + kbImgsHtml(e) + '</div>' +   // v1.2.95: kb-foto\n"),
    ("    edEl.querySelector('.kb-topic').onchange = function (ev) { kbData[si].topic = ev.target.value; kbMarkDirty(); };\n",
     "    edEl.querySelector('.kb-topic').onchange = function (ev) { kbData[si].topic = ev.target.value; kbMarkDirty(); };\n"
     "    edEl.querySelectorAll('.kb-img-del').forEach(function (b) {   // v1.2.95: kb-foto\n"
     "      b.onclick = function () { (kbData[si].images || []).splice(+b.dataset.i, 1); kbMarkDirty(); renderKb(); };\n"
     "    });\n"
     "    var kbImgIn = edEl.querySelector('.kb-img-in');\n"
     "    if (kbImgIn) kbImgIn.onchange = function () {\n"
     "      var id = kbData[si].id;\n"
     "      var files = Array.prototype.slice.call(kbImgIn.files || []).slice(0, Math.max(0, 6 - (kbData[si].images || []).length));\n"
     "      if (!files.length) return;\n"
     "      toast('Mengunggah ' + files.length + ' foto…');\n"
     "      var added = 0;\n"
     "      files.reduce(function (p, f) {\n"
     "        return p.then(function () { return kbPrepImage(f); })\n"
     "          .then(function (data) { return api('kb_image_upload', { method: 'POST', body: { data: data } }); })\n"
     "          .then(function (res) {\n"
     "            if (!res || !res.ok) { toast((res && res.error) || 'Gagal mengunggah foto.', true); return; }\n"
     "            var k = kbIdx(id); if (k === -1) return;\n"
     "            kbData[k].images = (kbData[k].images || []).concat([{ file: res.file }]); added++; kbMarkDirty();\n"
     "          });\n"
     "      }, Promise.resolve())\n"
     "        .catch(function (err) { toast((err && err.message) || 'Gagal mengunggah foto.', true); })\n"
     "        .then(function () { renderKb(); if (added) toast(added + ' foto ditambahkan — klik Simpan.'); });\n"
     "    };\n"),
    # thread WA: foto yang dikirim bot
    ("      if (m.a) h += waBubble(m.a, m.dir === 'manual' ? 'manual' : 'bot', m.ts, m.q ? null : m.media);",
     "      var _fotoOnly = m.media_out && m.media_out.length && /^\\[Foto/.test(m.a || '');   // v1.2.95: kb-foto\n"
     "      if (m.a && !_fotoOnly) h += waBubble(m.a, m.dir === 'manual' ? 'manual' : 'bot', m.ts, m.q ? null : m.media);\n"
     "      (m.media_out || []).forEach(function (md) { h += waBubble('', 'bot', m.ts, md); });"),
])

patch(TEN, 'dashboard/chatbot-ai/index.html', [
    ('<script src="app.js?v=1.2.94"></script><!-- v1.2.94: wa-media -->', '<script src="app.js?v=1.2.95"></script><!-- ' + MARK + ' -->'),
])
print('selesai')
