#!/usr/bin/env python3
"""v1.2.76 — Penyedia WhatsApp ketiga: WAHA (gateway WhatsApp Web sendiri, Baileys/NOWEB/GOWS/WEBJS).
- kirim: POST {waha}/api/sendText
- webhook: action=wa_webhook_waha (kunci URL + HMAC SHA-512), event message.any -> diterjemahkan ke
  bentuk payload Meta lalu lewat waHandleMetaPayload (antrean redis, debounce, anti-dobel, echo HP = bot mundur)
- koneksi dari dashboard: action=waha_conn (status/qr/kode/logout/webhook) memakai kartu Koneksi WhatsApp v1.2.75
Idempoten. Jalankan: python3 patch_v1276_waha.py <root dei-tenant>"""
import sys, os, shutil, time
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/Herd/dei-tenant')
TS = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.76: WAHA'

def patch(rel, pairs):
    p = os.path.join(ROOT, rel)
    src = open(p, encoding='utf-8').read()
    if MARK in src:
        print('SKIP (sudah):', rel); return
    out = src
    for old, new in pairs:
        n = out.count(old)
        if n != 1:
            sys.exit('ANCHOR di %s ditemukan %d kali: %r' % (rel, n, old[:90]))
        out = out.replace(old, new)
    shutil.copy2(p, p + '.bak-waha-' + TS)
    open(p, 'w', encoding='utf-8').write(out)
    print('OK:', rel)

PHP_HELPERS = r'''/* ============================================================
 * v1.2.76: WAHA — gateway WhatsApp Web sendiri (Docker di VPS)
 * ============================================================
 * Berbeda dengan Fonnte, WAHA meneruskan pesan yang diketik dari HP
 * (event message.any, fromMe=true) sehingga balasan CS dari HP ikut
 * tercatat di dashboard dan bot otomatis mundur — sama seperti echo
 * Coexistence Meta. Kiriman WAHA diterjemahkan ke bentuk payload Meta
 * supaya seluruh alur yang sudah teruji (antrean, debounce, anti-dobel,
 * mode manusia) dipakai ulang tanpa disalin. */
function wahaSession($wa) {
    $n = preg_replace('/[^A-Za-z0-9_-]/', '', (string)($wa['waha_session'] ?? ''));
    return $n !== '' ? $n : 'default';
}
function wahaApi($wa, $method, $path, $body = null) {
    $base = rtrim(trim((string)($wa['waha_url'] ?? '')), '/');
    if ($base === '') return [0, ['message' => 'URL WAHA belum diisi.']];
    $ch = curl_init($base . $path);
    $hdr = ['Accept: application/json', 'X-Api-Key: ' . (string)($wa['waha_api_key'] ?? '')];
    $opt = [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 20, CURLOPT_CONNECTTIMEOUT => 8, CURLOPT_CUSTOMREQUEST => $method];
    if ($body !== null) {
        $hdr[] = 'Content-Type: application/json';
        $opt[CURLOPT_POSTFIELDS] = json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }
    $opt[CURLOPT_HTTPHEADER] = $hdr;
    curl_setopt_array($ch, $opt);
    $resp = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err  = curl_error($ch);
    curl_close($ch);
    if ($resp === false) return [0, ['message' => 'Server WAHA tidak dapat dihubungi: ' . $err]];
    $d = json_decode((string)$resp, true);
    return [$code, is_array($d) ? $d : ['message' => mb_substr(trim((string)$resp), 0, 200)]];
}
function wahaErr($code, $d, $fallback = 'Permintaan ke WAHA gagal.') {
    $m = '';
    if (is_array($d)) {
        $m = $d['message'] ?? ($d['error'] ?? '');
        if (is_array($m)) $m = implode('; ', array_map(function ($x) { return is_scalar($x) ? (string)$x : json_encode($x); }, $m));
    }
    $m = trim((string)$m);
    if ($code === 401) $m = 'API Key WAHA ditolak (401).';
    return $m !== '' ? $m : ($fallback . ($code ? ' (HTTP ' . $code . ')' : ''));
}
function wahaWebhookUrl($wa) {
    $base = deiSelfApiUrl();
    if ($base === '') $base = deiRememberedApiUrl();
    return $base . '?action=wa_webhook_waha&key=' . rawurlencode((string)($wa['waha_webhook_key'] ?? ''));
}
function wahaSessionConfig($wa) {
    return [
        'webhooks' => [[
            'url'     => wahaWebhookUrl($wa),
            'events'  => ['message.any', 'session.status'],
            'hmac'    => ['key' => (string)($wa['waha_webhook_key'] ?? '')],
            'retries' => ['policy' => 'exponential', 'delaySeconds' => 2, 'attempts' => 5],
        ]],
        // NOWEB butuh store aktif supaya pemetaan @lid -> nomor tersedia.
        'noweb' => ['store' => ['enabled' => true, 'fullSync' => false]],
    ];
}
// Pastikan sesi ada & berjalan. Hasil: [ok, data sesi | pesan error].
function wahaEnsureSession($wa) {
    $n = wahaSession($wa);
    list($c, $d) = wahaApi($wa, 'GET', '/api/sessions/' . rawurlencode($n));
    if ($c === 404) {
        list($c, $d) = wahaApi($wa, 'POST', '/api/sessions', ['name' => $n, 'start' => true, 'config' => wahaSessionConfig($wa)]);
        if ($c < 200 || $c >= 300) return [false, wahaErr($c, $d, 'Gagal membuat sesi WAHA.')];
        if (empty($d['status'])) $d['status'] = 'STARTING';
        return [true, $d];
    }
    if ($c < 200 || $c >= 300) return [false, wahaErr($c, $d)];
    $st = (string)($d['status'] ?? '');
    if ($st === 'STOPPED') { wahaApi($wa, 'POST', '/api/sessions/' . rawurlencode($n) . '/start'); $d['status'] = 'STARTING'; }
    elseif ($st === 'FAILED') { wahaApi($wa, 'POST', '/api/sessions/' . rawurlencode($n) . '/restart'); $d['status'] = 'STARTING'; }
    return [true, $d];
}
function wahaJidNum($jid) {
    $jid = strtolower(trim((string)$jid));
    if (preg_match('/^(\d{6,20})(?::\d+)?@(c\.us|s\.whatsapp\.net)$/', $jid, $m)) return $m[1];
    return '';
}
// Nomor lawan bicara. @lid (pengenal privasi WA) dipetakan ke nomor HP:
// medan alternatif dari engine dulu, lalu API /lids WAHA (hasil disimpan).
function wahaResolveNum($wa, $jid, $p) {
    $num = wahaJidNum($jid);
    if ($num !== '') return $num;
    $jid = strtolower(trim((string)$jid));
    if (substr($jid, -4) !== '@lid') return '';
    $k = (is_array($p['_data']['key'] ?? null)) ? $p['_data']['key'] : [];
    foreach (['remoteJidAlt', 'senderPn', 'participantPn'] as $f) {
        $alt = wahaJidNum($k[$f] ?? '');
        if ($alt !== '') return $alt;
    }
    $lid = preg_replace('/\D/', '', substr($jid, 0, -4));
    if ($lid === '') return '';
    $f = DATA_DIR . '/waha-lids.json';
    $cache = readJson($f, []);
    if (!empty($cache[$lid])) return (string)$cache[$lid];
    list($c, $d) = wahaApi($wa, 'GET', '/api/' . rawurlencode(wahaSession($wa)) . '/lids/' . rawurlencode($lid));
    $pn = ($c >= 200 && $c < 300 && is_array($d)) ? wahaJidNum($d['pn'] ?? '') : '';
    if ($pn !== '') {
        deiWithLock('waha-lids', function () use ($f, $lid, $pn) {
            $all = readJson($f, []);
            if (!is_array($all)) $all = [];
            $all[$lid] = $pn;
            if (count($all) > 5000) $all = array_slice($all, -5000, null, true);
            writeJson($f, $all);
        });
    }
    return $pn;
}
// Jejak pesan yang DIKIRIM sistem ini (bot / dashboard), supaya pantulannya
// (fromMe) tidak dianggap balasan CS dari HP. Dicatat SEBELUM kirim karena
// webhook pantulan bisa tiba sebelum respons sendText kembali.
function wahaSentFile() { return DATA_DIR . '/waha-sent.json'; }
function wahaRememberSent($num, $id, $text) {
    deiWithLock('waha-sent', function () use ($num, $id, $text) {
        $now = time();
        $all = readJson(wahaSentFile(), []);
        if (!is_array($all)) $all = [];
        $all = array_values(array_filter($all, function ($r) use ($now) { return ($r['t'] ?? 0) > $now - 900; }));
        $all[] = ['t' => $now, 'id' => (string)$id, 'h' => $text !== '' ? md5(waNormNum($num) . '|' . trim((string)$text)) : ''];
        if (count($all) > 500) $all = array_slice($all, -500);
        writeJson(wahaSentFile(), $all);
    });
}
function wahaSentByUs($num, $id, $text) {
    $all = readJson(wahaSentFile(), []);
    if (!is_array($all)) return false;
    $h = md5(waNormNum($num) . '|' . trim((string)$text));
    $now = time();
    foreach ($all as $r) {
        if (($r['t'] ?? 0) <= $now - 900) continue;
        if ($id !== '' && ($r['id'] ?? '') === $id) return true;
        if (($r['h'] ?? '') === $h) return true;
    }
    return false;
}
function wahaMsgId($p) {
    $id = $p['id'] ?? '';
    if (is_array($id)) $id = $id['_serialized'] ?? ($id['id'] ?? '');
    return (string)$id;
}
// Terjemahkan event WAHA (message / message.any) ke payload bentuk Meta.
// null = abaikan (grup, status, chat ke diri sendiri, pantulan kiriman sendiri).
function wahaToMetaPayload($wa, $evt) {
    $p = is_array($evt['payload'] ?? null) ? $evt['payload'] : [];
    $id = wahaMsgId($p);
    $fromMe = !empty($p['fromMe']);
    $chat = (string)($fromMe ? ($p['to'] ?? '') : ($p['from'] ?? ''));
    if ($chat === '' || preg_match('/@(g\.us|newsletter|broadcast)$/i', $chat)) return null;
    $num = wahaResolveNum($wa, $chat, $p);
    if ($num === '') { error_log('waha: lawan bicara tidak terbaca (' . $chat . ')'); return null; }
    $me = wahaJidNum(preg_replace('/:\d+@/', '@', (string)($evt['me']['id'] ?? '')));
    if ($me !== '' && $me === $num) return null;

    $body = trim((string)($p['body'] ?? ''));
    $type = 'text';
    if (!empty($p['hasMedia'])) {
        $mt = strtolower((string)($p['media']['mimetype'] ?? ''));
        $type = strpos($mt, 'image/') === 0 ? 'image' : (strpos($mt, 'video/') === 0 ? 'video'
              : (strpos($mt, 'audio/') === 0 ? 'audio' : ($mt !== '' ? 'document' : 'media')));
    } elseif ($body === '') {
        $type = 'unsupported';
    }

    if ($fromMe) {
        if (($p['source'] ?? '') === 'api' || wahaSentByUs($num, $id, $body)) return null;
        $etext = ($type === 'text') ? $body : ($body !== '' ? $body . "\n" . deiNonTextLabel($type) : deiNonTextLabel($type));
        return ['entry' => [['changes' => [['value' => [
            'message_echoes' => [['id' => $id, 'to' => $num, 'type' => 'text', 'text' => ['body' => $etext]]],
        ]]]]]];
    }

    $msg = ['from' => $num, 'id' => $id, 'type' => $type];
    if ($type === 'text') $msg['text'] = ['body' => $body];
    $nama = '';
    $dd = is_array($p['_data'] ?? null) ? $p['_data'] : [];
    foreach ([$dd['notifyName'] ?? '', $dd['pushName'] ?? '', $dd['Info']['PushName'] ?? '', $p['notifyName'] ?? ''] as $cand) {
        if (is_string($cand) && trim($cand) !== '') { $nama = trim($cand); break; }
    }
    $val = ['messages' => [$msg]];
    if ($nama !== '') $val['contacts'] = [['wa_id' => $num, 'profile' => ['name' => $nama]]];
    return ['entry' => [['changes' => [['value' => $val]]]]];
}
function waSendWaha($wa, $to, $text) {
    $GLOBALS['wa_last_error'] = '';
    $to = waNormNum($to);
    if ($to === '') { $GLOBALS['wa_last_error'] = 'Nomor tujuan kosong.'; return false; }
    if (trim((string)($wa['waha_url'] ?? '')) === '') { $GLOBALS['wa_last_error'] = 'URL WAHA belum diisi.'; return false; }
    wahaRememberSent($to, '', $text);
    list($c, $d) = wahaApi($wa, 'POST', '/api/sendText', ['session' => wahaSession($wa), 'chatId' => $to . '@c.us', 'text' => $text]);
    if ($c >= 200 && $c < 300) {
        $id = is_array($d) ? wahaMsgId($d) : '';
        if ($id !== '') wahaRememberSent($to, $id, '');
        return true;
    }
    $GLOBALS['wa_last_error'] = wahaErr($c, $d, 'Kirim lewat WAHA gagal.');
    error_log('waSendWaha HTTP ' . $c . ': ' . $GLOBALS['wa_last_error']);
    return false;
}

function waSend($wa, $to, $text) {'''

PHP_WEBHOOK = r'''    /* ---------- v1.2.76: WAHA — PUBLIC webhook gateway WhatsApp Web sendiri ---------- */
    case 'wa_webhook_waha': {
        $s  = getSettings();
        $wa = waConf($s);
        if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo 'method not allowed'; exit; }
        // LAPIS 1 — kunci di URL. LAPIS 2 — HMAC SHA-512 (WAHA menandatangani badan kiriman).
        $kunci = (string)($wa['waha_webhook_key'] ?? '');
        if ($kunci === '' || !hash_equals($kunci, (string)($_GET['key'] ?? ''))) { http_response_code(403); echo 'forbidden'; exit; }
        $raw  = file_get_contents('php://input');
        $hmac = strtolower(trim((string)($_SERVER['HTTP_X_WEBHOOK_HMAC'] ?? '')));
        if ($hmac !== '' && !hash_equals(hash_hmac('sha512', $raw, $kunci), $hmac)) { http_response_code(403); echo 'bad hmac'; exit; }

        $evt = json_decode($raw, true);
        if (!is_array($evt) || ($wa['provider'] ?? 'meta') !== 'waha' || !($wa['enabled'] ?? false)) { echo 'OK'; exit; }
        if ((string)($evt['session'] ?? '') !== wahaSession($wa)) {
            error_log('waha: sesi tidak cocok (' . mb_substr((string)($evt['session'] ?? ''), 0, 40) . ')');
            echo 'OK'; exit;
        }
        if (!empty($wa['waha_debug'])) error_log('waha mentah: ' . mb_substr($raw, 0, 800));
        if (!in_array((string)($evt['event'] ?? ''), ['message', 'message.any'], true)) { echo 'OK'; exit; }

        $payload = wahaToMetaPayload($wa, $evt);
        if ($payload === null) { echo 'OK'; exit; }

        // Mode antrean (server sendiri): jalur sama dengan webhook Meta.
        if (deiQueueRedis()) {
            try {
                deiDebounceBuffer($payload);
                deiRedis()->lPush('q:wa', json_encode(['raw' => json_encode($payload, JSON_UNESCAPED_UNICODE), 'at' => time(), 'try' => 0]));
                echo 'OK'; exit;
            } catch (\Throwable $e) { error_log('antrean WAHA gagal, proses langsung: ' . $e->getMessage()); }
        }
        $earlyAck = function_exists('fastcgi_finish_request') || function_exists('litespeed_finish_request');
        if ($earlyAck) respondAndContinue('OK');
        @set_time_limit(60);
        waHandleMetaPayload($s, $wa, $payload);
        if (!$earlyAck) { echo 'OK'; }
        exit;
    }

    /* ---------- PUBLIC: webhook Fonnte (penyedia alternatif) ---------- */'''

PHP_CONN = r'''    /* ---------- v1.2.76: WAHA — koneksi sesi dari dashboard (scan QR / kode tautan) ---------- */
    case 'waha_conn': {
        $u  = requireAuth(['super_admin', 'admin']);
        $in = bodyInput();
        $op = (string)($in['op'] ?? 'status');
        $s  = getSettings();
        $wa = waConf($s);
        if (($wa['provider'] ?? 'meta') !== 'waha') jsonOut(['ok' => false, 'error' => 'Penyedia WhatsApp bukan WAHA.'], 400);
        if (trim((string)($wa['waha_url'] ?? '')) === '' || (string)($wa['waha_api_key'] ?? '') === '') {
            jsonOut(['ok' => false, 'error' => 'URL / API Key WAHA belum diisi Super Admin.'], 400);
        }
        $n  = wahaSession($wa);
        $sp = rawurlencode($n);

        if ($op === 'status') {
            list($c, $d) = wahaApi($wa, 'GET', '/api/sessions/' . $sp);
            if ($c === 404) jsonOut(['ok' => true, 'connected' => false, 'status' => 'BELUM DIBUAT', 'session' => $n]);
            if ($c < 200 || $c >= 300) jsonOut(['ok' => false, 'error' => wahaErr($c, $d)]);
            $st  = (string)($d['status'] ?? '');
            $dev = wahaJidNum(preg_replace('/:\d+@/', '@', (string)($d['me']['id'] ?? '')));
            if ($dev !== '' && (string)($wa['waha_number'] ?? '') !== $dev) {
                $s2 = getSettings();
                $s2['whatsapp_api']['waha_number'] = $dev;
                writeJson(SETTINGS_FILE, $s2);
            }
            jsonOut(['ok' => true, 'connected' => ($st === 'WORKING'), 'status' => $st, 'session' => $n,
                     'device' => $dev, 'name' => (string)($d['me']['pushName'] ?? '')]);
        }

        if ($op === 'qr') {
            list($ok, $d) = wahaEnsureSession($wa);
            if (!$ok) jsonOut(['ok' => false, 'error' => $d]);
            $st = (string)($d['status'] ?? '');
            if ($st === 'WORKING') jsonOut(['ok' => true, 'connected' => true]);
            if ($st !== 'SCAN_QR_CODE') jsonOut(['ok' => true, 'connected' => false, 'wait' => true, 'status' => $st]);
            if (($in['type'] ?? 'qr') === 'code') {
                $num = preg_replace('/\D/', '', (string)($in['whatsapp'] ?? ''));
                if (strpos($num, '0') === 0) $num = '62' . substr($num, 1);
                if (strlen($num) < 9 || strlen($num) > 15) jsonOut(['ok' => false, 'error' => 'Nomor WhatsApp tidak valid.'], 400);
                list($c, $r) = wahaApi($wa, 'POST', '/api/' . $sp . '/auth/request-code', ['phoneNumber' => $num]);
                if ($c >= 200 && $c < 300 && !empty($r['code'])) jsonOut(['ok' => true, 'connected' => false, 'code' => (string)$r['code']]);
                jsonOut(['ok' => false, 'error' => wahaErr($c, $r, 'Kode tautan tidak tersedia, pakai scan QR.')]);
            }
            list($c, $q) = wahaApi($wa, 'GET', '/api/' . $sp . '/auth/qr?format=image');
            $img = ($c >= 200 && $c < 300) ? preg_replace('/[^A-Za-z0-9+\/=]/', '', (string)($q['data'] ?? '')) : '';
            if ($img !== '') {
                $mime = preg_match('#^image/[a-z]+$#', (string)($q['mimetype'] ?? '')) ? $q['mimetype'] : 'image/png';
                jsonOut(['ok' => true, 'connected' => false, 'qr' => 'data:' . $mime . ';base64,' . $img]);
            }
            jsonOut(['ok' => true, 'connected' => false, 'wait' => true, 'status' => $st]);
        }

        if ($op === 'disconnect') {
            list($c, $d) = wahaApi($wa, 'POST', '/api/sessions/' . $sp . '/logout');
            if ($c >= 200 && $c < 300) {
                try { waAuditLog('waha_logout', $u['username'], '', []); } catch (\Throwable $e) {}
                jsonOut(['ok' => true]);
            }
            jsonOut(['ok' => false, 'error' => wahaErr($c, $d, 'Gagal memutuskan.')]);
        }

        if ($op === 'webhook') {
            if (($u['role'] ?? '') !== 'super_admin') jsonOut(['ok' => false, 'error' => 'Khusus Super Admin.'], 403);
            if ((string)($wa['waha_webhook_key'] ?? '') === '') jsonOut(['ok' => false, 'error' => 'Kunci webhook belum ada — simpan pengaturan dengan penyedia WAHA dulu.'], 400);
            list($c, $d) = wahaApi($wa, 'GET', '/api/sessions/' . $sp);
            if ($c === 404) {
                list($c, $d) = wahaApi($wa, 'POST', '/api/sessions', ['name' => $n, 'start' => true, 'config' => wahaSessionConfig($wa)]);
            } elseif ($c >= 200 && $c < 300) {
                list($c, $d) = wahaApi($wa, 'PUT', '/api/sessions/' . $sp, ['name' => $n, 'config' => wahaSessionConfig($wa)]);
            }
            if ($c < 200 || $c >= 300) jsonOut(['ok' => false, 'error' => wahaErr($c, $d, 'Gagal memasang webhook.')]);
            try { waAuditLog('waha_webhook_set', $u['username'], '', []); } catch (\Throwable $e) {}
            jsonOut(['ok' => true]);
        }

        jsonOut(['ok' => false, 'error' => 'op tidak dikenal'], 400);
        break;
    }

    case 'wa_audit_log': {'''

patch('api/index.php', [
    ("function waSend($wa, $to, $text) {", PHP_HELPERS),
    ("    if (($wa['provider'] ?? 'meta') === 'fonnte') return waSendFonnte($wa, $to, $text);",
     "    if (($wa['provider'] ?? 'meta') === 'fonnte') return waSendFonnte($wa, $to, $text);\n    if (($wa['provider'] ?? 'meta') === 'waha') return waSendWaha($wa, $to, $text);   // v1.2.76: WAHA"),
    ("    if (($wa['provider'] ?? 'meta') !== 'meta') return;\n    $logLimit = (int)($s['api']['log_limit'] ?? 500);",
     "    // v1.2.76: WAHA memakai alur ini juga (payload-nya diterjemahkan ke bentuk Meta)\n    if (!in_array(($wa['provider'] ?? 'meta'), ['meta', 'waha'], true)) return;\n    $logLimit = (int)($s['api']['log_limit'] ?? 500);"),
    ("    /* ---------- PUBLIC: webhook Fonnte (penyedia alternatif) ---------- */", PHP_WEBHOOK),
    ("    case 'wa_audit_log': {", PHP_CONN),
    ("            $s['whatsapp_api']['fonnte_token_is_set'] = !empty($raw['whatsapp_api']['fonnte_token']);",
     "            $s['whatsapp_api']['fonnte_token_is_set'] = !empty($raw['whatsapp_api']['fonnte_token']);\n"
     "            $s['whatsapp_api']['waha_api_key']        = maskKey($raw['whatsapp_api']['waha_api_key'] ?? '');   // v1.2.76\n"
     "            $s['whatsapp_api']['waha_api_key_is_set'] = !empty($raw['whatsapp_api']['waha_api_key']);"),
    ("            $s['whatsapp_api']['fonnte_webhook_key'] = !empty($s['whatsapp_api']['fonnte_webhook_key']) ? '••••' : '';",
     "            $s['whatsapp_api']['fonnte_webhook_key'] = !empty($s['whatsapp_api']['fonnte_webhook_key']) ? '••••' : '';\n"
     "            $s['whatsapp_api']['waha_webhook_key']   = !empty($s['whatsapp_api']['waha_webhook_key']) ? '••••' : '';   // v1.2.76"),
    ("foreach (['access_token', 'app_secret', 'fonnte_token'] as $secf) {   // v1.2.36",
     "foreach (['access_token', 'app_secret', 'fonnte_token', 'waha_api_key'] as $secf) {   // v1.2.36, v1.2.76"),
    ("                $incoming['whatsapp_api']['fonnte_webhook_key'] = bin2hex(random_bytes(16));\n            }",
     "                $incoming['whatsapp_api']['fonnte_webhook_key'] = bin2hex(random_bytes(16));\n            }\n"
     "            // v1.2.76: WAHA — kunci webhook (juga kunci HMAC) dibuat otomatis; rapikan URL & nama sesi\n"
     "            if (($incoming['whatsapp_api']['provider'] ?? '') === 'waha'\n"
     "                && empty($incoming['whatsapp_api']['waha_webhook_key'])\n"
     "                && empty($current['whatsapp_api']['waha_webhook_key'])) {\n"
     "                $incoming['whatsapp_api']['waha_webhook_key'] = bin2hex(random_bytes(24));\n"
     "            }\n"
     "            if (isset($incoming['whatsapp_api']['waha_url'])) {\n"
     "                $wu = rtrim(trim((string)$incoming['whatsapp_api']['waha_url']), '/');\n"
     "                $incoming['whatsapp_api']['waha_url'] = preg_match('#^https?://#i', $wu) ? $wu : '';\n"
     "            }\n"
     "            if (isset($incoming['whatsapp_api']['waha_session'])) {\n"
     "                $incoming['whatsapp_api']['waha_session'] = preg_replace('/[^A-Za-z0-9_-]/', '', (string)$incoming['whatsapp_api']['waha_session']);\n"
     "            }"),
    ("foreach (['verify_token', 'phone_number_id', 'fonnte_webhook_key'] as $f) {   // v1.2.36",
     "foreach (['verify_token', 'phone_number_id', 'fonnte_webhook_key', 'waha_webhook_key'] as $f) {   // v1.2.36, v1.2.76"),
    ("define('DEI_VERSION', 'v1.2.75');", "define('DEI_VERSION', 'v1.2.76');"),
])

# ---------------------------------------------------------------- index.html
patch('dashboard/chatbot-ai/index.html', [
    ('          <option value="fonnte">Fonnte — memakai nomor yang sudah ada, tidak resmi</option>',
     '          <option value="fonnte">Fonnte — memakai nomor yang sudah ada, tidak resmi</option>\n'
     '          <option value="waha">WAHA — gateway sendiri di VPS, balasan dari HP ikut tercatat, tidak resmi</option><!-- v1.2.76: WAHA -->'),
    ('          <div class="help">Tempel di panel Fonnte › Device › Webhook. Alamat ini memuat kunci rahasia — jangan dibagikan.</div></div>',
     '''          <div class="help">Tempel di panel Fonnte › Device › Webhook. Alamat ini memuat kunci rahasia — jangan dibagikan.</div></div>
        <div class="row wa-waha-only"><label class="fl">URL Server WAHA</label><input type="text" id="waha_url" class="mono" placeholder="https://wa.domain-anda.com"><div class="help">Alamat gateway WAHA (Docker) di VPS, tanpa garis miring di akhir.</div></div>
        <div class="grid2">
          <div class="row wa-waha-only"><label class="fl">API Key WAHA</label><input type="text" id="waha_key" class="mono" placeholder="nilai WAHA_API_KEY"><div class="help">Nilai <code>WAHA_API_KEY</code> di server WAHA. Kosongkan untuk tidak mengubah.</div></div>
          <div class="row wa-waha-only"><label class="fl">Nama Sesi</label><input type="text" id="waha_session" class="mono" placeholder="default"><div class="help">Satu sesi = satu nomor. Pakai nama unik per tenant (mis. <code>sinarjaya</code>) bila satu server WAHA melayani banyak nomor — gratis sejak WAHA 2026.6.1.</div></div>
        </div>
        <div class="row wa-waha-only"><label class="fl">Webhook URL (WAHA)</label>
          <div class="row" style="flex-direction:row;gap:8px;align-items:center">
            <input type="text" id="waha_webhook_url" class="mono" readonly style="flex:1">
            <button class="btn ghost" id="btnCopyWahaWebhook" type="button">Salin</button>
          </div>
          <div class="help">Dipasang otomatis saat sesi dibuat atau lewat <b>Pasang webhook otomatis</b> di kartu Koneksi WhatsApp (event <code>message.any</code> + <code>session.status</code>, HMAC SHA-512). Balasan yang diketik dari HP ikut tercatat dan bot mundur di chat itu.</div></div>'''),
    ('        <div class="help" style="margin-top:8px">Fonnte memakai jalur tidak resmi — hindari kirim pesan massal agar nomor tidak diblokir WhatsApp.</div>',
     '        <div class="help" style="margin-top:8px">Jalur tidak resmi (WhatsApp Web) — hindari kirim pesan massal agar nomor tidak diblokir WhatsApp.</div>'),
])

# ---------------------------------------------------------------- app.js
patch('dashboard/chatbot-ai/app.js', [
    ("    var meta = (prov !== 'fonnte');\n"
     "    $$('.wa-meta-only').forEach(function (el)   { el.style.display = meta ? '' : 'none'; });\n"
     "    $$('.wa-fonnte-only').forEach(function (el) { el.style.display = meta ? 'none' : ''; });",
     "    // v1.2.76: WAHA — tiga penyedia\n"
     "    var meta = (prov !== 'fonnte' && prov !== 'waha');\n"
     "    $$('.wa-meta-only').forEach(function (el)   { el.style.display = meta ? '' : 'none'; });\n"
     "    $$('.wa-fonnte-only').forEach(function (el) { el.style.display = prov === 'fonnte' ? '' : 'none'; });\n"
     "    $$('.wa-waha-only').forEach(function (el)   { el.style.display = prov === 'waha' ? '' : 'none'; });"),
    ("  var _fonc = { poll: null, qrT: null, stopT: null, mode: 'qr' };",
     "  var _fonc = { poll: null, qrT: null, stopT: null, waitT: null, mode: 'qr', action: 'fonnte_conn' };"),
    ("    clearInterval(_fonc.poll); clearInterval(_fonc.qrT); clearTimeout(_fonc.stopT);",
     "    clearInterval(_fonc.poll); clearInterval(_fonc.qrT); clearTimeout(_fonc.stopT); clearTimeout(_fonc.waitT);"),
    ("    if (st.expired) bits.push('Aktif s/d ' + st.expired);",
     "    if (st.expired) bits.push('Aktif s/d ' + st.expired);\n"
     "    if (st.name) bits.push(st.name);\n"
     "    if (st.session) bits.push('Sesi ' + st.session);\n"
     "    if (!st.connected && st.status) bits.push('Status ' + st.status);"),
    ("    return api('fonnte_conn', { method: 'POST', body: { op: 'status' } }).then(function (r) {",
     "    return api(_fonc.action, { method: 'POST', body: { op: 'status' } }).then(function (r) {"),
    ("    return api('fonnte_conn', { method: 'POST', body: body }).then(function (r) {",
     "    return api(_fonc.action, { method: 'POST', body: body }).then(function (r) {"),
    ("      } else {\n        h.textContent = 'Fonnte belum mengirim QR. Tunggu sebentar…';\n      }",
     "      } else {\n"
     "        // v1.2.76: sesi masih disiapkan (WAHA: STARTING) — coba lagi sebentar lagi\n"
     "        h.textContent = 'Menyiapkan sesi WhatsApp' + (r.status ? ' (' + r.status + ')' : '') + '… tunggu sebentar.';\n"
     "        clearTimeout(_fonc.waitT);\n"
     "        _fonc.waitT = setTimeout(function () { if (_fonc.poll) foncFetch(num); }, 3000);\n"
     "      }"),
    ("    var on = (wa.provider === 'fonnte') && !!wa.fonnte_token_is_set;",
     "    _fonc.action = (wa.provider === 'waha') ? 'waha_conn' : 'fonnte_conn';   // v1.2.76: WAHA\n"
     "    var on = ((wa.provider === 'fonnte') && !!wa.fonnte_token_is_set)\n"
     "          || ((wa.provider === 'waha') && !!wa.waha_url && !!wa.waha_api_key_is_set);"),
    ("        api('fonnte_conn', { method: 'POST', body: { op: 'disconnect' } }).then(function (r) {",
     "        api(_fonc.action, { method: 'POST', body: { op: 'disconnect' } }).then(function (r) {"),
    ("        api('fonnte_conn', { method: 'POST', body: { op: 'webhook' } }).then(function (r) {",
     "        api(_fonc.action, { method: 'POST', body: { op: 'webhook' } }).then(function (r) {"),
    ("          toast(r.ok ? 'Webhook Fonnte terpasang.' : (r.error || 'Gagal memasang webhook.'), !r.ok);",
     "          toast(r.ok ? 'Webhook terpasang.' : (r.error || 'Gagal memasang webhook.'), !r.ok);"),
    ("      $('#fon_device').value = wa.fonnte_device || '';",
     "      $('#fon_device').value = wa.fonnte_device || '';\n"
     "      // v1.2.76: WAHA\n"
     "      $('#waha_url').value = wa.waha_url || '';\n"
     "      $('#waha_session').value = wa.waha_session || '';\n"
     "      $('#waha_key').value = wa.waha_api_key || '';   // disamarkan server\n"
     "      $('#waha_key').placeholder = wa.waha_api_key_is_set ? '•••• (terisi — kosongkan untuk tidak mengubah)' : 'nilai WAHA_API_KEY';\n"
     "      $('#waha_webhook_url').value = (wa.waha_webhook_key && wa.waha_webhook_key.indexOf('•') === -1)\n"
     "        ? (API + '?action=wa_webhook_waha&key=' + encodeURIComponent(wa.waha_webhook_key))\n"
     "        : '(kunci dibuat otomatis setelah disimpan dengan penyedia WAHA)';\n"
     "      $('#btnCopyWahaWebhook').onclick = function () { var f = $('#waha_webhook_url'); f.select(); copyText(f.value, 'Webhook WAHA disalin.'); };"),
    ("      fonnte_device: $('#fon_device').value.trim(),",
     "      fonnte_device: $('#fon_device').value.trim(),\n"
     "      waha_url: $('#waha_url').value.trim(),                                         // v1.2.76\n"
     "      waha_session: $('#waha_session').value.trim(),\n"
     "      waha_api_key: ($('#waha_key').value.indexOf('•') !== -1) ? '' : $('#waha_key').value.trim(),"),
    ("    var _waOnBd = !!(s.whatsapp_api && s.whatsapp_api.enabled && s.whatsapp_api.provider === 'fonnte');",
     "    var _waOnBd = !!(s.whatsapp_api && s.whatsapp_api.enabled && (s.whatsapp_api.provider === 'fonnte' || s.whatsapp_api.provider === 'waha'));   // v1.2.76"),
    ("        contactWaConfig.wa_enabled = !!r.wa_enabled && r.provider === 'fonnte';   // v1.2.39 fase8b",
     "        contactWaConfig.wa_enabled = !!r.wa_enabled && (r.provider === 'fonnte' || r.provider === 'waha');   // v1.2.39 fase8b, v1.2.76"),
    ("      if (r.wa_provider === 'fonnte') msg += '<br>' + ico('triangle-alert', 13) + ' Fonnte: jalur tidak resmi",
     "      if (r.wa_provider === 'fonnte' || r.wa_provider === 'waha') msg += '<br>' + ico('triangle-alert', 13) + ' ' + (r.wa_provider === 'waha' ? 'WAHA' : 'Fonnte') + ': jalur tidak resmi"),
    ("        if (wo && wo.enabled && wo.provider !== 'fonnte') {",
     "        if (wo && wo.enabled && (wo.provider || 'meta') === 'meta') {   // v1.2.76: hanya Meta"),
])
print('selesai')
