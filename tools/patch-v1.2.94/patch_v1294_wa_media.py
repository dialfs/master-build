#!/usr/bin/env python3
"""v1.2.94 — Media WhatsApp (gambar, video, audio, dokumen, stiker) masuk & tampil di dashboard.
Disimpan di data/wa-media/<nomor>/, dihapus otomatis setelah 30 hari (whatsapp_api.media_days).
Pemakaian: python3 patch_v1294_wa_media.py <root dei-tenant>   (idempoten; backup *.bak-v1294-*)"""
import sys, os, time, shutil
TEN = sys.argv[1]
STAMP = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.94: wa-media'

def patch(root, rel, pairs):
    p = os.path.join(root, rel)
    s = open(p, encoding='utf-8').read()
    if MARK in s: print('sudah dipatch:', rel); return
    for old, new in pairs:
        n = s.count(old)
        if n != 1: sys.exit(f'GAGAL {rel}: anchor {n}x:\n{old[:200]}')
        s = s.replace(old, new)
    shutil.copy2(p, p + '.bak-v1294-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

PHP_FUNCS = r'''/* ============================================================================
 * v1.2.94: wa-media — MEDIA WhatsApp (gambar/video/audio/dokumen/stiker).
 * Diunduh saat pesan masuk (Meta: lewat media id; WAHA: media.url, file di WAHA
 * hanya bertahan ~3 menit) ke data/wa-media/<nomor>/, disajikan lewat action
 * wa_media (wajib login), dihapus otomatis setelah media_days hari (bawaan 30).
 * Salinan asli tetap ada di HP / aplikasi WhatsApp Business.
 * ========================================================================= */
define('WA_MEDIA_DIR', DATA_DIR . '/wa-media');
define('WA_MEDIA_MAX_BYTES', 16 * 1024 * 1024);
function deiWaMediaTypes() { return ['image', 'video', 'audio', 'document', 'sticker', 'media']; }   // 'media' = WAHA tanpa mimetype
function deiWaMediaDays($s = null) {
    if ($s === null) $s = getSettings();
    return max(1, min(365, (int)($s['whatsapp_api']['media_days'] ?? 30)));
}
function deiWaMediaLabel($type) {
    $m = ['image' => 'Gambar', 'video' => 'Video', 'audio' => 'Pesan suara', 'document' => 'Dokumen', 'sticker' => 'Stiker'];
    return $m[$type] ?? 'Media';
}
function deiWaMediaExt($mime, $fname = '') {
    $e = strtolower(pathinfo((string)$fname, PATHINFO_EXTENSION));
    if ($e !== '' && preg_match('/^[a-z0-9]{1,5}$/', $e) && !in_array($e, ['php', 'phtml', 'phar', 'html', 'htm', 'shtml', 'svg', 'js', 'cgi', 'pl', 'py'], true)) return $e;
    $mime = strtolower(trim(explode(';', (string)$mime)[0]));
    $map = ['image/jpeg' => 'jpg', 'image/png' => 'png', 'image/webp' => 'webp', 'image/gif' => 'gif',
            'video/mp4' => 'mp4', 'video/3gpp' => '3gp', 'video/webm' => 'webm', 'video/quicktime' => 'mov',
            'audio/ogg' => 'ogg', 'audio/mpeg' => 'mp3', 'audio/mp4' => 'm4a', 'audio/aac' => 'aac', 'audio/amr' => 'amr', 'audio/webm' => 'weba',
            'application/pdf' => 'pdf', 'text/plain' => 'txt', 'text/csv' => 'csv',
            'application/msword' => 'doc', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' => 'docx',
            'application/vnd.ms-excel' => 'xls', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' => 'xlsx',
            'application/vnd.ms-powerpoint' => 'ppt', 'application/vnd.openxmlformats-officedocument.presentationml.presentation' => 'pptx',
            'application/zip' => 'zip'];
    return $map[$mime] ?? 'bin';
}
/* GET dengan batas ukuran. Hasil: [kode HTTP, isi|null, content-type, pesan galat]. */
function deiHttpGetCapped($url, $headers, $max) {
    if (!function_exists('curl_init')) return [0, null, '', 'curl tidak ada'];
    $buf = ''; $over = false;
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_HTTPHEADER => $headers, CURLOPT_FOLLOWLOCATION => true, CURLOPT_MAXREDIRS => 3,
        CURLOPT_CONNECTTIMEOUT => 8, CURLOPT_TIMEOUT => 45, CURLOPT_USERAGENT => 'DEI-Chatbot/1.0',
        CURLOPT_WRITEFUNCTION => function ($c, $d) use (&$buf, &$over, $max) {
            if (strlen($buf) + strlen($d) > $max) { $over = true; return 0; }
            $buf .= $d; return strlen($d);
        },
    ]);
    curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $ct   = (string)curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
    $err  = curl_error($ch);
    curl_close($ch);
    if ($over) return [$code, null, $ct, 'too_big'];
    if ($code < 200 || $code >= 300 || $buf === '') return [$code, null, $ct, $err !== '' ? $err : ('HTTP ' . $code)];
    return [$code, $buf, $ct, ''];
}
/* Ambil isi media. $m = objek media dari pesan (Meta: id/mime_type; WAHA: _waha_url). Hasil: [isi|null, mime, galat]. */
function deiWaMediaFetch($wa, $m) {
    $m = is_array($m) ? $m : [];
    if (array_key_exists('_waha_url', $m)) {
        $base = rtrim(trim((string)($wa['waha_url'] ?? '')), '/');
        $u = parse_url((string)$m['_waha_url']);
        $path = (string)($u['path'] ?? '') . (isset($u['query']) ? '?' . $u['query'] : '');
        if ($base === '' || $path === '') return [null, '', 'url media WAHA kosong (WAHA_DOWNLOAD_MEDIA mati?)'];
        list(, $b, $ct, $e) = deiHttpGetCapped($base . $path, ['X-Api-Key: ' . (string)($wa['waha_api_key'] ?? '')], WA_MEDIA_MAX_BYTES);
        return [$b, (string)($m['mime_type'] ?? '') ?: $ct, $e];
    }
    $id = (string)($m['id'] ?? '');
    $tok = (string)($wa['access_token'] ?? '');
    if ($id === '' || $tok === '') return [null, '', 'media id kosong'];
    list(, $j, , $e) = deiHttpGetCapped('https://graph.facebook.com/v21.0/' . rawurlencode($id), ['Authorization: Bearer ' . $tok], 65536);
    $d = json_decode((string)$j, true);
    if (!is_array($d) || empty($d['url'])) return [null, '', 'info media: ' . ($e ?: 'kosong')];
    if ((int)($d['file_size'] ?? 0) > WA_MEDIA_MAX_BYTES) return [null, '', 'too_big'];
    list(, $b, $ct, $e) = deiHttpGetCapped((string)$d['url'], ['Authorization: Bearer ' . $tok], WA_MEDIA_MAX_BYTES);
    return [$b, (string)($d['mime_type'] ?? '') ?: $ct, $e];
}
/* Unduh & simpan. Hasil meta: {type, file, mime, name, size} atau {type, error}. */
function deiWaMediaStore($wa, $num, $msgId, $type, $m) {
    $num = preg_replace('/\D/', '', (string)$num);
    $name = trim((string)($m['filename'] ?? ''));
    $meta = ['type' => $type];
    if ($name !== '') $meta['name'] = mb_substr($name, 0, 120);
    try { deiWaMediaSweep(); } catch (\Throwable $e) {}
    if ($num === '') { $meta['error'] = 'unavailable'; return $meta; }
    list($bytes, $mime, $err) = deiWaMediaFetch($wa, $m);
    if ($bytes === null) {
        $meta['error'] = ($err === 'too_big') ? 'too_big' : 'unavailable';
        if ($err !== 'too_big') error_log('wa-media: gagal unduh ' . $type . ' dari ' . $num . ' — ' . mb_substr((string)$err, 0, 160));
        return $meta;
    }
    $dir = WA_MEDIA_DIR . '/' . $num;
    if (!is_dir($dir)) @mkdir($dir, 0755, true);
    $fn = substr(sha1($msgId . '|' . microtime(true) . '|' . mt_rand()), 0, 20) . '.' . deiWaMediaExt($mime, $name);
    if (@file_put_contents($dir . '/' . $fn, $bytes) === false) { $meta['error'] = 'unavailable'; error_log('wa-media: gagal tulis ' . $dir); return $meta; }
    $meta['file'] = $num . '/' . $fn;
    $meta['mime'] = strtolower(trim(explode(';', (string)$mime)[0]));
    $meta['size'] = strlen($bytes);
    return $meta;
}
/* Pesan media (format Meta) -> [meta media, teks tampil di log, teks untuk AI]. */
function deiWaMediaFromMsg($wa, $num, $msg) {
    $type = (string)($msg['type'] ?? '');
    $m = is_array($msg[$type] ?? null) ? $msg[$type] : [];
    $cap = trim((string)($m['caption'] ?? ''));
    $meta = deiWaMediaStore($wa, $num, (string)($msg['id'] ?? ''), $type, $m);
    $lbl = deiWaMediaLabel($type);
    $show = '[' . $lbl . (!empty($meta['name']) ? ': ' . $meta['name'] : '') . ']' . ($cap !== '' ? "\n" . $cap : '');
    $ai = '[Pelanggan mengirim ' . mb_strtolower($lbl) . (!empty($meta['name']) ? ' "' . $meta['name'] . '"' : '')
        . '. Bot tidak bisa melihat isinya; bila perlu, sampaikan bahwa admin akan mengeceknya.]' . ($cap !== '' ? "\n" . $cap : '');
    return [$meta, $show, $ai];
}
/* Hapus media lebih tua dari media_days. Paling sering sekali per jam. */
function deiWaMediaSweep($force = false) {
    if (!is_dir(WA_MEDIA_DIR)) return 0;
    $mark = WA_MEDIA_DIR . '/.sweep';
    if (!$force && is_file($mark) && time() - (int)@filemtime($mark) < 3600) return 0;
    @touch($mark);
    $batas = time() - deiWaMediaDays() * 86400;
    $n = 0;
    foreach ((array)glob(WA_MEDIA_DIR . '/*', GLOB_ONLYDIR) as $d) {
        foreach ((array)glob($d . '/*') as $f) {
            if (is_file($f) && (int)@filemtime($f) < $batas && @unlink($f)) $n++;
        }
        if (!glob($d . '/*')) @rmdir($d);
    }
    return $n;
}
/* Kirim file ke browser: tipe aman tampil inline, lainnya diunduh. Mendukung Range (video di Safari). */
function deiWaMediaOutput($path, $download = false) {
    $ext = strtolower(pathinfo($path, PATHINFO_EXTENSION));
    $inline = ['jpg' => 'image/jpeg', 'png' => 'image/png', 'webp' => 'image/webp', 'gif' => 'image/gif',
               'mp4' => 'video/mp4', '3gp' => 'video/3gpp', 'webm' => 'video/webm', 'mov' => 'video/quicktime',
               'ogg' => 'audio/ogg', 'mp3' => 'audio/mpeg', 'm4a' => 'audio/mp4', 'aac' => 'audio/aac', 'amr' => 'audio/amr', 'weba' => 'audio/webm',
               'pdf' => 'application/pdf'];
    $ct = $inline[$ext] ?? 'application/octet-stream';
    $size = (int)filesize($path);
    $start = 0; $end = $size - 1;
    if (!empty($_SERVER['HTTP_RANGE']) && preg_match('/bytes=(\d*)-(\d*)/', $_SERVER['HTTP_RANGE'], $r)) {
        if ($r[1] !== '') { $start = (int)$r[1]; if ($r[2] !== '') $end = min((int)$r[2], $size - 1); }
        elseif ($r[2] !== '') { $start = max(0, $size - (int)$r[2]); }
        if ($start > $end || $start >= $size) { http_response_code(416); header('Content-Range: bytes */' . $size); exit; }
        http_response_code(206);
        header('Content-Range: bytes ' . $start . '-' . $end . '/' . $size);
    }
    header('Content-Type: ' . $ct);
    header('X-Content-Type-Options: nosniff');
    header("Content-Security-Policy: default-src 'none'; img-src 'self'; media-src 'self'; sandbox");
    header('Cache-Control: private, max-age=86400');
    header('Accept-Ranges: bytes');
    header('Content-Length: ' . ($end - $start + 1));
    $dl = $download || !isset($inline[$ext]);
    header('Content-Disposition: ' . ($dl ? 'attachment' : 'inline') . '; filename="' . basename($path) . '"');
    $fh = fopen($path, 'rb');
    fseek($fh, $start);
    $left = $end - $start + 1;
    while ($left > 0 && !feof($fh)) { $chunk = fread($fh, min(65536, $left)); echo $chunk; $left -= strlen($chunk); }
    fclose($fh);
}

function waHandleMetaMessage($s, $wa, $msg, $waProfileNames, $metadata) {'''

patch(TEN, 'api/index.php', [
    ("define('DEI_VERSION', 'v1.2.93');", "define('DEI_VERSION', 'v1.2.94');"),
    ("function waHandleMetaMessage($s, $wa, $msg, $waProfileNames, $metadata) {", PHP_FUNCS),
    # pesan masuk bermedia
    ("        if (($msg['type'] ?? '') !== 'text') {\n"
     "            // v1.2.58: mode Manual tidak membalas otomatis; tandai saja supaya agent tahu\n",
     "        if (($msg['type'] ?? '') !== 'text') {\n"
     "            // " + MARK + ": media diunduh & dicatat; AI menjawab caption-nya (stiker tanpa caption tidak dibalas)\n"
     "            if (in_array((string)($msg['type'] ?? ''), deiWaMediaTypes(), true)) {\n"
     "                list($wmMeta, $wmShow, $wmAi) = deiWaMediaFromMsg($wa, $from, $msg);\n"
     "                $wmCap = trim((string)($msg[$msg['type']]['caption'] ?? ''));\n"
     "                waProcessIncoming($s, $wa, $from, $wmAi, $deiWaName, array_merge((array)$metadata,\n"
     "                    ['_media' => $wmMeta, '_q_show' => $wmShow, '_no_reply' => ($msg['type'] === 'sticker' && $wmCap === '')]));\n"
     "                return;\n"
     "            }\n"
     "            // v1.2.58: mode Manual tidak membalas otomatis; tandai saja supaya agent tahu\n"),
    # log: tampilkan label+caption, simpan meta media
    ("        'referrer'     => '',\n    ];\n\n    if ($mode === 'human') {",
     "        'referrer'     => '',\n    ];\n"
     "    if (isset($metaInfo['_q_show'])) $logBase['q'] = (string)$metaInfo['_q_show'];   // " + MARK + "\n"
     "    if (!empty($metaInfo['_media'])) $logBase['media'] = $metaInfo['_media'];\n\n"
     "    if ($mode === 'human') {"),
    ("    // v1.2.89: ucapan penutup (\"ok makasih\", 👍) setelah jawaban bot yang bukan pertanyaan -> tidak dibalas\n",
     "    // " + MARK + ": stiker tanpa caption = seperti ucapan penutup, dicatat tanpa dibalas\n"
     "    if (!empty($metaInfo['_no_reply'])) {\n"
     "        if ($keepCtx) { $hSt = waLoadHistory($from); $hSt[] = ['role' => 'user', 'content' => $text]; waSaveHistory($from, $hSt); }\n"
     "        logPrepend(array_merge($logBase, ['a' => '', 'hemat' => 'ack']), $logLimit);\n"
     "        waOutCount('saved');\n"
     "        return;\n"
     "    }\n"
     "    // v1.2.89: ucapan penutup (\"ok makasih\", 👍) setelah jawaban bot yang bukan pertanyaan -> tidak dibalas\n"),
    # echo dari HP (Meta coexistence + WAHA fromMe)
    ("                $etext = (($echo['type'] ?? '') === 'text') ? trim($echo['text']['body'] ?? '') : '';\n"
     "                if ($etext === '') continue;\n",
     "                $etext = (($echo['type'] ?? '') === 'text') ? trim($echo['text']['body'] ?? '') : '';\n"
     "                $emedia = null;   // " + MARK + "\n"
     "                if (in_array((string)($echo['type'] ?? ''), deiWaMediaTypes(), true)) {\n"
     "                    list($emedia, $etext) = deiWaMediaFromMsg($wa, $eto, $echo);\n"
     "                }\n"
     "                if ($etext === '') continue;\n"),
    ("                    logMutate(function (&$elogs) use ($eid, $etext, $eto, &$dup) {\n"
     "                        if ($eid !== '') { foreach ($elogs as $el) { if (($el['echo_id'] ?? '') === $eid) { $dup = true; return false; } } }\n"
     "                        array_unshift($elogs, [\n"
     "                            'ts' => date('Y-m-d H:i:s'), 'q' => '', 'a' => $etext, 'ip' => $eto,\n"
     "                            'channel' => 'whatsapp', 'dir' => 'manual', 'src' => 'hp', 'echo_id' => $eid,\n"
     "                            'utm_source' => 'whatsapp', 'utm_medium' => 'hp', 'utm_campaign' => '', 'page' => '', 'referrer' => '',\n"
     "                        ]);\n",
     "                    logMutate(function (&$elogs) use ($eid, $etext, $eto, &$dup, $emedia) {\n"
     "                        if ($eid !== '') { foreach ($elogs as $el) { if (($el['echo_id'] ?? '') === $eid) { $dup = true; return false; } } }\n"
     "                        array_unshift($elogs, array_merge([\n"
     "                            'ts' => date('Y-m-d H:i:s'), 'q' => '', 'a' => $etext, 'ip' => $eto,\n"
     "                            'channel' => 'whatsapp', 'dir' => 'manual', 'src' => 'hp', 'echo_id' => $eid,\n"
     "                            'utm_source' => 'whatsapp', 'utm_medium' => 'hp', 'utm_campaign' => '', 'page' => '', 'referrer' => '',\n"
     "                        ], $emedia ? ['media' => $emedia] : []));   // " + MARK + "\n"),
    ("                    }, $logLimit);\n                    if (!$dup) {\n",
     "                    }, $logLimit);\n"
     "                    if ($dup && !empty($emedia['file'])) @unlink(WA_MEDIA_DIR . '/' . $emedia['file']);   // " + MARK + ": kiriman ulang\n"
     "                    if (!$dup) {\n"),
    # WAHA -> bentuk Meta: bawa url media
    ("        if (($p['source'] ?? '') === 'api' || wahaSentByUs($num, $id, $body)) return null;\n"
     "        $etext = ($type === 'text') ? $body : ($body !== '' ? $body . \"\\n\" . deiNonTextLabel($type) : deiNonTextLabel($type));\n",
     "        if (($p['source'] ?? '') === 'api' || wahaSentByUs($num, $id, $body)) return null;\n"
     "        if (in_array($type, deiWaMediaTypes(), true)) {   // " + MARK + "\n"
     "            return ['entry' => [['changes' => [['value' => [\n"
     "                'message_echoes' => [['id' => $id, 'to' => $num, 'type' => $type, $type => wahaMediaObj($p, $body)]],\n"
     "            ]]]]]];\n"
     "        }\n"
     "        $etext = ($type === 'text') ? $body : ($body !== '' ? $body . \"\\n\" . deiNonTextLabel($type) : deiNonTextLabel($type));\n"),
    ("    if ($type === 'text') $msg['text'] = ['body' => $body];\n    $nama = '';",
     "    if ($type === 'text') $msg['text'] = ['body' => $body];\n"
     "    elseif (in_array($type, deiWaMediaTypes(), true)) $msg[$type] = wahaMediaObj($p, $body);   // " + MARK + "\n"
     "    $nama = '';"),
    ("function waSendWaha($wa, $to, $text) {",
     "/* " + MARK + ": objek media WAHA dalam bentuk Meta (url diunduh lewat deiWaMediaFetch) */\n"
     "function wahaMediaObj($p, $caption) {\n"
     "    $md = is_array($p['media'] ?? null) ? $p['media'] : [];\n"
     "    return ['_waha_url' => (string)($md['url'] ?? ''), 'mime_type' => (string)($md['mimetype'] ?? ''),\n"
     "            'filename' => (string)($md['filename'] ?? ''), 'caption' => (string)$caption];\n"
     "}\n"
     "function waSendWaha($wa, $to, $text) {"),
    # thread + endpoint media
    ("            $msgs[] = ['ts' => $e['ts'] ?? '', 'q' => $e['q'] ?? '', 'a' => $e['a'] ?? '', 'dir' => $e['dir'] ?? '', 'awaiting' => !empty($e['awaiting'])];\n",
     "            $msgs[] = ['ts' => $e['ts'] ?? '', 'q' => $e['q'] ?? '', 'a' => $e['a'] ?? '', 'dir' => $e['dir'] ?? '', 'awaiting' => !empty($e['awaiting']),\n"
     "                       'media' => is_array($e['media'] ?? null) ? $e['media'] : null];   // " + MARK + "\n"),
    ("    case 'wa_thread': {\n",
     "    /* ---------- " + MARK + ": file media WA (login wajib; token boleh di query untuk <img>/<video>) ---------- */\n"
     "    case 'wa_media': {\n"
     "        $u = requireAuth(['super_admin','admin','wa_agent']);\n"
     "        $f = (string)($_GET['f'] ?? '');\n"
     "        if (!preg_match('#^(\\d{6,20})/([a-f0-9]{20}\\.[a-z0-9]{1,5})$#', $f, $mf)) { http_response_code(400); header('Content-Type: text/plain'); echo 'bad request'; exit; }\n"
     "        deiGuardAgentPrivate($u, $mf[1]);\n"
     "        $p = WA_MEDIA_DIR . '/' . $mf[1] . '/' . $mf[2];\n"
     "        if (!is_file($p)) { http_response_code(404); header('Content-Type: text/plain'); echo 'Media sudah tidak tersedia'; exit; }\n"
     "        deiWaMediaOutput($p, !empty($_GET['dl']));\n"
     "        exit;\n"
     "    }\n\n"
     "    case 'wa_thread': {\n"),
    # cron: sapu media
    ("        try { $r['sessions_purged'] = deiPurgeSessions(); } catch (\\Throwable $e) { $r['err_purge'] = $e->getMessage(); }   // v1.2.71\n",
     "        try { $r['sessions_purged'] = deiPurgeSessions(); } catch (\\Throwable $e) { $r['err_purge'] = $e->getMessage(); }   // v1.2.71\n"
     "        try { $r['media_purged'] = deiWaMediaSweep(); } catch (\\Throwable $e) { $r['err_media'] = $e->getMessage(); }   // " + MARK + "\n"),
])

JS_MEDIA = r'''  /* v1.2.94: wa-media — gambar/video/audio/dokumen di thread WA */
  function waMediaHtml(md) {
    if (!md || !md.type) return '';
    var lbl = { image: 'Gambar', video: 'Video', audio: 'Pesan suara', document: 'Dokumen', sticker: 'Stiker' }[md.type] || 'Media';
    var note = function (t) { return '<div style="font-size:12px;opacity:.8;margin-bottom:4px">' + ico('triangle-alert', 13) + ' ' + esc(t) + '</div>'; };
    if (!md.file) return note(md.error === 'too_big' ? lbl + ' terlalu besar (> 16 MB) — lihat di HP' : lbl + ' tidak dapat diunduh — lihat di HP');
    var u = API + '?action=wa_media&f=' + encodeURIComponent(md.file) + '&token=' + encodeURIComponent(token);
    var gone = ' onerror="this.outerHTML=\'<div style=&quot;font-size:12px;opacity:.8&quot;>' + lbl + ' sudah dihapus dari dashboard (lewat masa simpan) — lihat di HP</div>\'"';
    if (md.type === 'image' || md.type === 'sticker') {
      var mx = md.type === 'sticker' ? 'max-width:120px;max-height:120px' : 'max-width:240px;max-height:320px';
      return '<a href="' + u + '" target="_blank" rel="noopener" style="display:block;margin-bottom:4px"><img src="' + u + '" loading="lazy" alt="' + lbl + '" style="' + mx + ';border-radius:8px;display:block"' + gone + '></a>';
    }
    if (md.type === 'video') return '<video controls preload="metadata" src="' + u + '" style="max-width:260px;max-height:320px;border-radius:8px;display:block;margin-bottom:4px"' + gone + '></video>';
    if (md.type === 'audio') return '<audio controls preload="none" src="' + u + '" style="max-width:240px;display:block;margin-bottom:4px"' + gone + '></audio>';
    var kb = md.size ? (md.size > 1048576 ? (md.size / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(md.size / 1024)) + ' KB') : '';
    return '<a href="' + u + '&dl=1" style="display:flex;gap:6px;align-items:center;padding:8px 10px;border-radius:8px;background:rgba(0,0,0,.06);color:inherit;text-decoration:none;margin-bottom:4px">' +
      ico('file-text', 16) + '<span style="overflow:hidden;text-overflow:ellipsis">' + esc(md.name || 'Dokumen') + '</span><span style="opacity:.65;font-size:11px">' + kb + '</span></a>';
  }

  function waBubble(text, kind, ts, media) {'''

patch(TEN, 'dashboard/chatbot-ai/app.js', [
    ("  function waBubble(text, kind, ts) {", JS_MEDIA),
    ("    return '<div style=\"max-width:78%;' + st + ';padding:8px 12px;border-radius:12px;margin:4px 0;white-space:pre-wrap;font-size:14px;line-height:1.45\">' +\n"
     "      esc(text) + '<div style=\"font-size:10px;opacity:.65;margin-top:4px\">'",
     "    if (media && media.file) text = String(text || '').replace(/^\\[[^\\]\\n]*\\]\\n?/, '');   // v1.2.94: label diganti media\n"
     "    return '<div style=\"max-width:78%;' + st + ';padding:8px 12px;border-radius:12px;margin:4px 0;white-space:pre-wrap;font-size:14px;line-height:1.45\">' +\n"
     "      waMediaHtml(media) + esc(text) + '<div style=\"font-size:10px;opacity:.65;margin-top:4px\">'"),
    ("      if (m.q) h += waBubble(m.q, 'in', m.ts);\n      if (m.a) h += waBubble(m.a, m.dir === 'manual' ? 'manual' : 'bot', m.ts);",
     "      if (m.q) h += waBubble(m.q, 'in', m.ts, m.media);   // v1.2.94: media milik pesan tamu, atau balasan HP bila q kosong\n"
     "      if (m.a) h += waBubble(m.a, m.dir === 'manual' ? 'manual' : 'bot', m.ts, m.q ? null : m.media);"),
])

patch(TEN, 'dashboard/chatbot-ai/index.html', [
    ('<script src="app.js?v=1.2.93"></script>', '<script src="app.js?v=1.2.94"></script><!-- ' + MARK + ' -->'),
])
print('selesai')
