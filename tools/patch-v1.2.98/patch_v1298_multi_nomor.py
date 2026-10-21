#!/usr/bin/env python3
"""v1.2.98 — Multi-nomor WhatsApp: satu tenant bisa memakai beberapa nomor WA (Meta Cloud API atau WAHA).
- settings.wa_numbers = daftar nomor tambahan; nomor utama tetap whatsapp_api (id 'utama').
  Nomor tambahan memakai penyedia yang sama dengan nomor utama. Kolom kosong (token/WABA, URL/API key WAHA)
  mewarisi nomor utama.
- Pesan masuk dikenali nomornya (Meta: metadata.phone_number_id; WAHA: nama sesi). Kontak menyimpan
  wa_ch = nomor bisnis terakhir yang dipakai pelanggan; SEMUA kiriman ke pelanggan itu (bot, agent, foto KB,
  closing, eskalasi, mengetik) keluar dari nomor yang sama.
- Dashboard: kartu "Nomor WhatsApp" (tambah/ubah/hapus, ambil nomor dari WABA, scan QR per nomor WAHA),
  label + filter nomor di Percakapan WA, label nomor per pesan di thread, pilih nomor pengirim di Blast,
  pesan keluar per nomor di kartu pemakaian.
- Tanpa nomor tambahan perilaku sama persis dengan v1.2.97.
Pemakaian: python3 patch_v1298_multi_nomor.py <root dei-tenant>   (idempoten; backup *.bak-v1298-*)
Butuh v1.2.97 sudah terpasang."""
import sys, os, time, shutil
TEN = sys.argv[1]
STAMP = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.98: multi-nomor'

def patch(root, rel, pairs):
    p = os.path.join(root, rel)
    s = open(p, encoding='utf-8').read()
    if MARK in s: print('sudah dipatch:', rel); return
    if 'v1.2.97: batas-ai' not in s: sys.exit('GAGAL: v1.2.97 belum terpasang di ' + rel)
    for old, new in pairs:
        n = s.count(old)
        if n != 1: sys.exit(f'GAGAL {rel}: anchor {n}x:\n{old[:300]}')
        s = s.replace(old, new)
    shutil.copy2(p, p + '.bak-v1298-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

# ============================================================== PHP
PHP_FUNCS = r'''
/* v1.2.98: multi-nomor — beberapa nomor WhatsApp dalam satu tenant.
 * settings.wa_numbers = [{id, label, phone_number_id, display_number, verified_name, access_token, waba_id,
 *                         waha_session, waha_url, waha_api_key, waha_number, created_at}]
 * Nomor utama = whatsapp_api (id 'utama'). Nomor tambahan memakai penyedia yang sama (Meta / WAHA);
 * kolom kosong (token, WABA, URL & API key WAHA) mewarisi nomor utama.
 * Percakapan tetap per nomor pelanggan. Kontak menyimpan wa_ch = nomor bisnis terakhir yang dipakai
 * pelanggan; semua kiriman ke pelanggan itu keluar dari nomor yang sama (waChanFor). */
if (!defined('WA_NUMBERS_MAX')) define('WA_NUMBERS_MAX', 9);
function waNumbersRaw($s = null) {
    if ($s === null) $s = getSettings();
    $l = $s['wa_numbers'] ?? [];
    if (!is_array($l)) return [];
    $out = [];
    foreach ($l as $x) { if (is_array($x) && !empty($x['id'])) $out[] = $x; }
    return $out;
}
function waMultiProv($wa) { return in_array((string)($wa['provider'] ?? 'meta'), ['meta', 'waha'], true); }
function waMultiOn($wa, $s = null) { return waMultiProv($wa) && count(waNumbersRaw($s)) > 0; }
function waChanNumOf($x, $prov) {
    return waNormNum($prov === 'waha' ? ($x['waha_number'] ?? '') : ($x['display_number'] ?? ''));
}
function waChanLabelOf($x, $prov, $fallback) {
    $l = trim((string)($x['label'] ?? ''));
    if ($l !== '') return $l;
    $n = waChanNumOf($x, $prov);
    return $n !== '' ? '+' . $n : $fallback;
}
// Daftar nomor (utama dulu) untuk label di dashboard. Tanpa rahasia.
function waChannels($s = null) {
    if ($s === null) $s = getSettings();
    $wa = waConf($s); $prov = (string)($wa['provider'] ?? 'meta');
    $out = [['id' => 'utama', 'label' => waChanLabelOf($wa, $prov, 'Nomor utama'), 'number' => waChanNumOf($wa, $prov), 'primary' => true]];
    if (!waMultiProv($wa)) return $out;
    $i = 1;
    foreach (waNumbersRaw($s) as $x) {
        $i++;
        $out[] = ['id' => (string)$x['id'], 'label' => waChanLabelOf($x, $prov, 'Nomor ' . $i), 'number' => waChanNumOf($x, $prov), 'primary' => false];
    }
    return $out;
}
// Konfigurasi kirim untuk satu nomor. $wa = whatsapp_api (nomor utama). Id tak dikenal -> nomor utama.
function waChanConf($wa, $id, $s = null) {
    $id = (string)$id;
    if ($id !== '' && $id !== 'utama' && waMultiProv($wa)) {
        $prov = (string)($wa['provider'] ?? 'meta');
        foreach (waNumbersRaw($s) as $x) {
            if ((string)$x['id'] !== $id) continue;
            $c = $wa;
            if ($prov === 'waha') {
                $c['waha_session'] = (string)($x['waha_session'] ?? '');
                if (trim((string)($x['waha_url'] ?? '')) !== '') $c['waha_url'] = (string)$x['waha_url'];
                if ((string)($x['waha_api_key'] ?? '') !== '') $c['waha_api_key'] = (string)$x['waha_api_key'];
                $c['waha_number'] = (string)($x['waha_number'] ?? '');
            } else {
                $c['phone_number_id'] = (string)($x['phone_number_id'] ?? '');
                $c['display_number'] = (string)($x['display_number'] ?? '');
                if ((string)($x['access_token'] ?? '') !== '') $c['access_token'] = (string)$x['access_token'];
                if ((string)($x['waba_id'] ?? '') !== '') $c['waba_id'] = (string)$x['waba_id'];
            }
            $c['_ch'] = $id;
            return $c;
        }
    }
    $wa['_ch'] = 'utama';
    return $wa;
}
// Nomor pengirim untuk pelanggan $to: yang sudah ditetapkan (_ch) dipakai apa adanya,
// selain itu nomor bisnis terakhir yang dipakai pelanggan (kontak.wa_ch).
function waChanFor($wa, $to) {
    if (!empty($wa['_ch']) || !waMultiOn($wa)) return $wa;
    $c = null;
    try { $c = waContactGet($to); } catch (\Throwable $e) { error_log('waChanFor: ' . $e->getMessage()); }
    return waChanConf($wa, (string)(is_array($c) ? ($c['wa_ch'] ?? '') : ''));
}
// Nomor penerima kiriman webhook (value.metadata). Tanpa nomor tambahan: $wa apa adanya (perilaku lama).
function waChanFromMeta($wa, $meta) {
    if (!waMultiOn($wa)) return $wa;
    $meta = is_array($meta) ? $meta : [];
    if (!empty($meta['_dei_ch'])) return waChanConf($wa, (string)$meta['_dei_ch']);
    $pid = (string)($meta['phone_number_id'] ?? '');
    if ($pid !== '' && ($wa['provider'] ?? 'meta') === 'meta') {
        foreach (waNumbersRaw() as $x) {
            if ((string)($x['phone_number_id'] ?? '') === $pid) return waChanConf($wa, (string)$x['id']);
        }
    }
    return waChanConf($wa, 'utama');
}
// WAHA: cari nomor dari nama sesi event. null = sesi bukan milik tenant ini.
function waWahaChanBySession($wa, $sess) {
    $sess = (string)$sess;
    if ($sess === wahaSession($wa)) return waMultiOn($wa) ? waChanConf($wa, 'utama') : $wa;
    if (($wa['provider'] ?? 'meta') !== 'waha') return null;
    foreach (waNumbersRaw() as $x) {
        $c = waChanConf($wa, (string)$x['id']);
        if (trim((string)($x['waha_session'] ?? '')) !== '' && wahaSession($c) === $sess) return $c;
    }
    return null;
}
function waContactSetCh($num, $ch) {
    $num = waNormNum($num); $ch = (string)$ch;
    if ($num === '' || $ch === '') return;
    try {
        $c = waContactGet($num);
        if (is_array($c) && (string)($c['wa_ch'] ?? '') === $ch) return;
        waContactUpdate($num, function (&$r) use ($ch) { $r['wa_ch'] = $ch; });
    } catch (\Throwable $e) { error_log('waContactSetCh: ' . $e->getMessage()); }
}
// Nomor WAHA yang terbaca dari sesi -> simpan ke nomor yang sesuai.
function waChanSetWahaNumber($wa, $dev) {
    $s2 = getSettings();
    $id = (string)($wa['_ch'] ?? '');
    if ($id === '' || $id === 'utama') {
        $s2['whatsapp_api']['waha_number'] = $dev;
    } else {
        $l = is_array($s2['wa_numbers'] ?? null) ? $s2['wa_numbers'] : [];
        foreach ($l as $i => $x) { if (is_array($x) && (string)($x['id'] ?? '') === $id) $l[$i]['waha_number'] = $dev; }
        $s2['wa_numbers'] = $l;
    }
    writeJson(SETTINGS_FILE, $s2);
}
// Info nomor Meta (display_phone_number, verified_name). [ok, data|pesan]
function waMetaPhoneInfo($token, $pnid) {
    if ($token === '' || $pnid === '') return [false, 'Token / Phone Number ID kosong.'];
    list($c, $j, , $e) = deiHttpGetCapped('https://graph.facebook.com/v21.0/' . rawurlencode($pnid) . '?fields=display_phone_number,verified_name',
        ['Authorization: Bearer ' . $token], 65536);
    $d = json_decode((string)$j, true);
    if ($c >= 200 && $c < 300 && is_array($d)) return [true, $d];
    return [false, 'Meta menolak Phone Number ID ini (' . ($e !== '' ? $e : 'HTTP ' . $c) . ') — cek ID & izin token.'];
}
'''

PHP_ENDPOINT = r'''    /* ---------- v1.2.98: multi-nomor — kelola nomor WhatsApp tambahan ---------- */
    case 'wa_numbers': {
        $u  = requireAuth(['super_admin', 'admin', 'supervisor']);
        $in = bodyInput();
        $op = (string)($in['op'] ?? ($_GET['op'] ?? 'list'));
        $s  = getSettings();
        $wa = waConf($s);
        $prov = (string)($wa['provider'] ?? 'meta');
        $isSa = (($u['role'] ?? '') === 'super_admin');
        if ($op !== 'list' && !$isSa) jsonOut(['ok' => false, 'error' => 'Khusus Super Admin.'], 403);

        if ($op === 'list') {
            // nomor tampil nomor utama (Meta) diambil sekali per Phone Number ID
            $pn0 = (string)($wa['phone_number_id'] ?? '');
            if ($isSa && $prov === 'meta' && $pn0 !== '' && (string)($wa['display_pnid'] ?? '') !== $pn0 && (string)($wa['access_token'] ?? '') !== '') {
                list($okI, $inf) = waMetaPhoneInfo((string)$wa['access_token'], $pn0);
                if ($okI) {
                    $s = getSettings();
                    $s['whatsapp_api']['display_number'] = waNormNum($inf['display_phone_number'] ?? '');
                    $s['whatsapp_api']['display_pnid'] = $pn0;
                    writeJson(SETTINGS_FILE, $s);
                    $wa = waConf($s);
                }
            }
            $rows = [];
            $p = ['id' => 'utama', 'primary' => true, 'label' => (string)($wa['label'] ?? ''), 'number' => waChanNumOf($wa, $prov),
                  'waha_session' => wahaSession($wa)];
            if ($isSa) $p['phone_number_id'] = (string)($wa['phone_number_id'] ?? '');
            $rows[] = $p;
            if (waMultiProv($wa)) {
                foreach (waNumbersRaw($s) as $x) {
                    $r = ['id' => (string)$x['id'], 'primary' => false, 'label' => (string)($x['label'] ?? ''),
                          'number' => waChanNumOf($x, $prov), 'verified_name' => (string)($x['verified_name'] ?? ''),
                          'waha_session' => (string)($x['waha_session'] ?? '')];
                    if ($isSa) {
                        $r['phone_number_id'] = (string)($x['phone_number_id'] ?? '');
                        $r['waba_id'] = (string)($x['waba_id'] ?? '');
                        $r['token_is_set'] = (string)($x['access_token'] ?? '') !== '';
                        $r['waha_url'] = (string)($x['waha_url'] ?? '');
                        $r['waha_key_is_set'] = (string)($x['waha_api_key'] ?? '') !== '';
                    }
                    $rows[] = $r;
                }
            }
            jsonOut(['ok' => true, 'provider' => $prov, 'supported' => waMultiProv($wa), 'max' => WA_NUMBERS_MAX,
                     'channels' => waChannels($s), 'numbers' => $rows]);
        }
        if (!waMultiProv($wa)) jsonOut(['ok' => false, 'error' => 'Nomor tambahan hanya untuk penyedia Meta Cloud API atau WAHA.'], 400);

        // Daftar nomor di WABA (Meta) supaya Phone Number ID tidak perlu dicari manual.
        if ($op === 'meta_phones') {
            if ($prov !== 'meta') jsonOut(['ok' => false, 'error' => 'Hanya untuk Meta Cloud API.'], 400);
            $waba = preg_replace('/\D/', '', (string)($in['waba_id'] ?? '')) ?: (string)($wa['waba_id'] ?? '');
            $tok  = trim((string)($in['access_token'] ?? ''));
            if ($tok === '' || strpos($tok, '•') !== false) $tok = (string)($wa['access_token'] ?? '');
            if ($waba === '' || $tok === '') jsonOut(['ok' => false, 'error' => 'WABA ID / Access Token belum ada.'], 400);
            list($c, $j, , $e) = deiHttpGetCapped('https://graph.facebook.com/v21.0/' . rawurlencode($waba)
                . '/phone_numbers?fields=id,display_phone_number,verified_name&limit=100', ['Authorization: Bearer ' . $tok], 262144);
            $d = json_decode((string)$j, true);
            if ($c < 200 || $c >= 300 || !is_array($d)) jsonOut(['ok' => false, 'error' => 'Gagal membaca nomor di WABA (' . ($e !== '' ? $e : 'HTTP ' . $c) . ').'], 502);
            $used = [(string)($wa['phone_number_id'] ?? '') => 'utama'];
            foreach (waNumbersRaw($s) as $x) $used[(string)($x['phone_number_id'] ?? '')] = (string)$x['id'];
            $out = [];
            foreach ((array)($d['data'] ?? []) as $ph) {
                $id = (string)($ph['id'] ?? '');
                if ($id === '') continue;
                $out[] = ['phone_number_id' => $id, 'number' => waNormNum($ph['display_phone_number'] ?? ''),
                          'verified_name' => (string)($ph['verified_name'] ?? ''), 'used_by' => $used[$id] ?? ''];
            }
            jsonOut(['ok' => true, 'waba_id' => $waba, 'phones' => $out]);
        }

        if ($op === 'save') {
            $id    = preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['id'] ?? ''));
            $label = mb_substr(trim((string)($in['label'] ?? '')), 0, 40);
            if ($id === 'utama') {
                $s['whatsapp_api']['label'] = $label;
                writeJson(SETTINGS_FILE, $s);
                try { waAuditLog('wa_number_label', $u['username'], '', ['ch' => 'utama', 'label' => $label]); } catch (\Throwable $e) {}
                jsonOut(['ok' => true, 'id' => 'utama']);
            }
            $list = waNumbersRaw($s);
            $idx = -1;
            foreach ($list as $i => $x) { if ((string)$x['id'] === $id) { $idx = $i; break; } }
            if ($id !== '' && $idx < 0) jsonOut(['ok' => false, 'error' => 'Nomor tidak ditemukan.'], 404);
            if ($idx < 0 && count($list) >= WA_NUMBERS_MAX) jsonOut(['ok' => false, 'error' => 'Maksimal ' . WA_NUMBERS_MAX . ' nomor tambahan.'], 400);
            $row = $idx >= 0 ? $list[$idx] : ['id' => 'n' . bin2hex(random_bytes(4)), 'created_at' => date('Y-m-d H:i:s')];
            $row['label'] = $label;
            $warn = '';
            if ($prov === 'meta') {
                $pnid = preg_replace('/\D/', '', (string)($in['phone_number_id'] ?? ''));
                if ($pnid === '') jsonOut(['ok' => false, 'error' => 'Phone Number ID wajib diisi.'], 400);
                if ($pnid === (string)($wa['phone_number_id'] ?? '')) jsonOut(['ok' => false, 'error' => 'Phone Number ID ini sudah dipakai nomor utama.'], 400);
                foreach ($list as $i => $x) {
                    if ($i !== $idx && (string)($x['phone_number_id'] ?? '') === $pnid) jsonOut(['ok' => false, 'error' => 'Phone Number ID ini sudah terdaftar.'], 400);
                }
                $row['phone_number_id'] = $pnid;
                $tok = trim((string)($in['access_token'] ?? ''));
                if (!empty($in['clear_token'])) $row['access_token'] = '';
                elseif ($tok !== '' && strpos($tok, '•') === false) $row['access_token'] = $tok;
                $row['waba_id'] = preg_replace('/\D/', '', (string)($in['waba_id'] ?? ''));
                $useTok = (string)($row['access_token'] ?? '') !== '' ? (string)$row['access_token'] : (string)($wa['access_token'] ?? '');
                list($okInfo, $info) = waMetaPhoneInfo($useTok, $pnid);
                if ($okInfo) {
                    $row['display_number'] = waNormNum($info['display_phone_number'] ?? '');
                    $row['verified_name'] = mb_substr((string)($info['verified_name'] ?? ''), 0, 80);
                } else {
                    $warn = $info;
                }
            } else {
                $sess = preg_replace('/[^A-Za-z0-9_-]/', '', (string)($in['waha_session'] ?? ''));
                if ($sess === '') jsonOut(['ok' => false, 'error' => 'Nama sesi WAHA wajib diisi (satu sesi = satu nomor).'], 400);
                if ($sess === wahaSession($wa)) jsonOut(['ok' => false, 'error' => 'Nama sesi ini sudah dipakai nomor utama.'], 400);
                foreach ($list as $i => $x) {
                    if ($i !== $idx && (string)($x['waha_session'] ?? '') === $sess) jsonOut(['ok' => false, 'error' => 'Nama sesi ini sudah terdaftar.'], 400);
                }
                if ((string)($row['waha_session'] ?? '') !== $sess) $row['waha_number'] = '';
                $row['waha_session'] = $sess;
                $wu = rtrim(trim((string)($in['waha_url'] ?? '')), '/');
                $row['waha_url'] = preg_match('#^https?://#i', $wu) ? $wu : '';
                $key = trim((string)($in['waha_api_key'] ?? ''));
                if (!empty($in['clear_key'])) $row['waha_api_key'] = '';
                elseif ($key !== '' && strpos($key, '•') === false) $row['waha_api_key'] = $key;
            }
            $s = getSettings();   // baca ulang tepat sebelum menulis
            $cur = is_array($s['wa_numbers'] ?? null) ? array_values(array_filter($s['wa_numbers'], 'is_array')) : [];
            $put = false;
            foreach ($cur as $i => $x) { if ((string)($x['id'] ?? '') === $row['id']) { $cur[$i] = $row; $put = true; } }
            if (!$put) $cur[] = $row;
            $s['wa_numbers'] = array_values($cur);
            writeJson(SETTINGS_FILE, $s);
            try { waAuditLog($idx >= 0 ? 'wa_number_edit' : 'wa_number_add', $u['username'], '', ['ch' => $row['id'], 'label' => $label]); } catch (\Throwable $e) {}
            jsonOut(['ok' => true, 'id' => $row['id'], 'warning' => $warn]);
        }

        if ($op === 'delete') {
            $id = preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['id'] ?? ''));
            if ($id === '' || $id === 'utama') jsonOut(['ok' => false, 'error' => 'Nomor utama tidak bisa dihapus dari sini.'], 400);
            $cur = is_array($s['wa_numbers'] ?? null) ? $s['wa_numbers'] : [];
            $n0 = count($cur);
            $cur = array_values(array_filter($cur, function ($x) use ($id) { return !(is_array($x) && (string)($x['id'] ?? '') === $id); }));
            if (count($cur) === $n0) jsonOut(['ok' => false, 'error' => 'Nomor tidak ditemukan.'], 404);
            $s['wa_numbers'] = $cur;
            writeJson(SETTINGS_FILE, $s);
            try { waAuditLog('wa_number_delete', $u['username'], '', ['ch' => $id]); } catch (\Throwable $e) {}
            jsonOut(['ok' => true]);
        }
        jsonOut(['ok' => false, 'error' => 'op tidak dikenal'], 400);
        break;
    }

'''

php = [
    ("define('DEI_VERSION', 'v1.2.97');", "define('DEI_VERSION', 'v1.2.98');"),
    # fungsi inti
    ("function waConf($s) {\n    return is_array($s['whatsapp_api'] ?? null) ? $s['whatsapp_api'] : [];\n}\n",
     "function waConf($s) {\n    return is_array($s['whatsapp_api'] ?? null) ? $s['whatsapp_api'] : [];\n}\n" + PHP_FUNCS),
    # kiriman keluar memilih nomor pelanggan
    ("function waSend($wa, $to, $text) {\n",
     "function waSend($wa, $to, $text) {\n"
     "    $wa = waChanFor($wa, $to); $GLOBALS['wa_out_ch'] = (string)($wa['_ch'] ?? '');   // v1.2.98: multi-nomor\n"),
    ("function waSendImage($wa, $to, $path, $caption = '') {\n",
     "function waSendImage($wa, $to, $path, $caption = '') {\n"
     "    $wa = waChanFor($wa, $to); $GLOBALS['wa_out_ch'] = (string)($wa['_ch'] ?? '');   // v1.2.98: multi-nomor\n"),
    ("function waSendTemplate($wa, $to, $name, $lang, $vars = []) {\n",
     "function waSendTemplate($wa, $to, $name, $lang, $vars = []) {\n"
     "    $wa = waChanFor($wa, $to); $GLOBALS['wa_out_ch'] = (string)($wa['_ch'] ?? '');   // v1.2.98: multi-nomor\n"),
    ("function deiTypingStart($s, $wa, $to) {\n",
     "function deiTypingStart($s, $wa, $to) {\n    $wa = waChanFor($wa, $to);   // v1.2.98: multi-nomor\n"),
    ("function deiTypingStop($wa, $to) {\n",
     "function deiTypingStop($wa, $to) {\n    $wa = waChanFor($wa, $to);   // v1.2.98: multi-nomor\n"),
    # hitungan pesan keluar per nomor
    ("        $all[$m][$k] = (int)($all[$m][$k] ?? 0) + 1;\n",
     "        $all[$m][$k] = (int)($all[$m][$k] ?? 0) + 1;\n"
     "        $och = (string)($GLOBALS['wa_out_ch'] ?? '');   // v1.2.98: multi-nomor\n"
     "        if ($k !== 'saved' && $och !== '') {\n"
     "            if (!isset($all[$m]['ch']) || !is_array($all[$m]['ch'])) $all[$m]['ch'] = [];\n"
     "            $all[$m]['ch'][$och][$k] = (int)($all[$m]['ch'][$och][$k] ?? 0) + 1;\n"
     "        }\n"),
    ("    return ['service' => (int)($r['service'] ?? 0), 'template' => (int)($r['template'] ?? 0), 'saved' => (int)($r['saved'] ?? 0)];   // v1.2.89\n",
     "    return ['service' => (int)($r['service'] ?? 0), 'template' => (int)($r['template'] ?? 0), 'saved' => (int)($r['saved'] ?? 0),   // v1.2.89\n"
     "            'ch' => is_array($r['ch'] ?? null) ? $r['ch'] : []];   // v1.2.98: multi-nomor\n"),
    # webhook: kenali nomor penerima per change
    ("    foreach (($payload['entry'] ?? []) as $entry) {\n        foreach (($entry['changes'] ?? []) as $change) {\n",
     "    $waBase = $wa;   // v1.2.98: multi-nomor\n"
     "    foreach (($payload['entry'] ?? []) as $entry) {\n        foreach (($entry['changes'] ?? []) as $change) {\n"
     "            $wa = waChanFromMeta($waBase, $change['value']['metadata'] ?? []);   // v1.2.98: multi-nomor\n"),
    ("                    if (!$dup) {\n                        waSetMode($eto, 'human'); // agent balas dari HP = ambil alih -> bot mundur\n",
     "                    if (!$dup) {\n                        if (!empty($wa['_ch'])) waContactSetCh($eto, $wa['_ch']);   // v1.2.98: multi-nomor\n"
     "                        waSetMode($eto, 'human'); // agent balas dari HP = ambil alih -> bot mundur\n"),
    ("        try { waSaveContact($from, $deiWaName); }\n",
     "        try { waSaveContact($from, $deiWaName, (string)($wa['_ch'] ?? '')); }   // v1.2.98: multi-nomor\n"),
    ("function waSaveContact($number, $nameWa) {\n",
     "function waSaveContact($number, $nameWa, $ch = '') {   // v1.2.98: multi-nomor ($ch = nomor bisnis penerima)\n"),
    ("    waContactUpdate($number, function (&$c) use ($nameWa) {   // v1.2.71: atomik, dua mode\n",
     "    waContactUpdate($number, function (&$c) use ($nameWa, $ch) {   // v1.2.71: atomik, dua mode; v1.2.98: + $ch\n"),
    ("        if ($nameWa !== '') $c['name_wa'] = mb_substr($nameWa, 0, 100);\n        $c['last_seen'] = date('Y-m-d H:i:s');\n    });\n",
     "        if ($nameWa !== '') $c['name_wa'] = mb_substr($nameWa, 0, 100);\n        $c['last_seen'] = date('Y-m-d H:i:s');\n"
     "        if ((string)$ch !== '') $c['wa_ch'] = (string)$ch;   // v1.2.98: multi-nomor\n    });\n"),
    ("    if (!empty($metaInfo['_media'])) $logBase['media'] = $metaInfo['_media'];\n",
     "    if (!empty($metaInfo['_media'])) $logBase['media'] = $metaInfo['_media'];\n"
     "    if (!empty($wa['_ch'])) $logBase['wa_ch'] = (string)$wa['_ch'];   // v1.2.98: multi-nomor\n"),
    # webhook WAHA: sesi -> nomor
    ("        if ((string)($evt['session'] ?? '') !== wahaSession($wa)) {\n"
     "            error_log('waha: sesi tidak cocok (' . mb_substr((string)($evt['session'] ?? ''), 0, 40) . ')');\n"
     "            echo 'OK'; exit;\n        }\n",
     "        $waCh = waWahaChanBySession($wa, (string)($evt['session'] ?? ''));   // v1.2.98: multi-nomor\n"
     "        if ($waCh === null) {\n"
     "            error_log('waha: sesi tidak cocok (' . mb_substr((string)($evt['session'] ?? ''), 0, 40) . ')');\n"
     "            echo 'OK'; exit;\n        }\n"
     "        $wa = $waCh;\n"),
    ("        if ($payload === null) { echo 'OK'; exit; }\n",
     "        if ($payload === null) { echo 'OK'; exit; }\n"
     "        if (!empty($wa['_ch'])) $payload['entry'][0]['changes'][0]['value']['metadata'] = ['_dei_ch' => (string)$wa['_ch']];   // v1.2.98: multi-nomor (ikut ke antrean)\n"),
    # waha_conn per nomor
    ("        $wa = waConf($s);\n        if (($wa['provider'] ?? 'meta') !== 'waha') jsonOut(['ok' => false, 'error' => 'Penyedia WhatsApp bukan WAHA.'], 400);\n",
     "        $wa = waConf($s);\n        if (($wa['provider'] ?? 'meta') !== 'waha') jsonOut(['ok' => false, 'error' => 'Penyedia WhatsApp bukan WAHA.'], 400);\n"
     "        $chId = preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['ch'] ?? ''));   // v1.2.98: multi-nomor\n"
     "        if ($chId !== '' && $chId !== 'utama') {\n"
     "            $wa = waChanConf($wa, $chId, $s);\n"
     "            if (($wa['_ch'] ?? '') !== $chId) jsonOut(['ok' => false, 'error' => 'Nomor tidak ditemukan.'], 404);\n"
     "        }\n"),
    ("            if ($dev !== '' && (string)($wa['waha_number'] ?? '') !== $dev) {\n"
     "                $s2 = getSettings();\n"
     "                $s2['whatsapp_api']['waha_number'] = $dev;\n"
     "                writeJson(SETTINGS_FILE, $s2);\n            }\n",
     "            if ($dev !== '' && (string)($wa['waha_number'] ?? '') !== $dev) waChanSetWahaNumber($wa, $dev);   // v1.2.98: multi-nomor\n"),
    ("    case 'waha_conn': {\n", PHP_ENDPOINT + "    case 'waha_conn': {\n"),
    # get_settings: daftar nomor tambahan (berisi token) tidak ikut
    ("        jsonOut(['ok' => true, 'settings' => $s, 'role' => $role]);\n",
     "        unset($s['wa_numbers']);   // v1.2.98: multi-nomor — dikelola lewat wa_numbers (token tidak dikirim)\n"
     "        jsonOut(['ok' => true, 'settings' => $s, 'role' => $role]);\n"),
    ("        $incoming = is_array($in['settings'] ?? null) ? $in['settings'] : [];\n",
     "        $incoming = is_array($in['settings'] ?? null) ? $in['settings'] : [];\n"
     "        unset($incoming['wa_numbers']);   // v1.2.98: multi-nomor — hanya lewat action wa_numbers\n"),
    # percakapan: label + filter nomor
    ("        $allContacts = waGetContacts();   // v1.2.19: 1 file read untuk semua nomor\n",
     "        $allContacts = waGetContacts();   // v1.2.19: 1 file read untuk semua nomor\n"
     "        $chMulti = waMultiOn(waConf($s58), $s58);   // v1.2.98: multi-nomor\n"
     "        $chList = $chMulti ? waChannels($s58) : [];\n"
     "        $chMap = []; foreach ($chList as $chx) $chMap[$chx['id']] = $chx['label'];\n"
     "        $chF = preg_replace('/[^A-Za-z0-9_]/', '', (string)($_GET['ch'] ?? ''));\n"
     "        if (!isset($chMap[$chF])) $chF = '';\n"),
    ("            if ($spvScope !== null && !deiSpvSeesOwner($spvScope, (string)($claim['agent_username'] ?? ''))) continue;   // v1.2.59\n            $visible[$num] = true;\n",
     "            if ($spvScope !== null && !deiSpvSeesOwner($spvScope, (string)($claim['agent_username'] ?? ''))) continue;   // v1.2.59\n"
     "            $numCh = '';   // v1.2.98: multi-nomor\n"
     "            if ($chMulti) { $cc = (string)($allContacts[$num]['wa_ch'] ?? ''); $numCh = isset($chMap[$cc]) ? $cc : 'utama'; }\n"
     "            if ($chF !== '' && $numCh !== $chF) continue;\n"
     "            $visible[$num] = true;\n"),
    ("                'last_from' => $fl['last_from'],\n            ];\n",
     "                'last_from' => $fl['last_from'],\n"
     "                'ch' => $numCh, 'ch_label' => $numCh !== '' ? $chMap[$numCh] : '',   // v1.2.98: multi-nomor\n            ];\n"),
    ("            'spv_team' => $spvScope !== null,   // v1.2.59\n",
     "            'spv_team' => $spvScope !== null,   // v1.2.59\n"
     "            'channels' => $chList, 'ch' => $chF,   // v1.2.98: multi-nomor\n"),
    # thread: nomor per pesan
    ("                       'media_out' => is_array($e['media_out'] ?? null) ? $e['media_out'] : null];   // v1.2.95: kb-foto\n",
     "                       'media_out' => is_array($e['media_out'] ?? null) ? $e['media_out'] : null,   // v1.2.95: kb-foto\n"
     "                       'ch' => (string)($e['wa_ch'] ?? '')];   // v1.2.98: multi-nomor\n"),
    ("            'messages' => $msgs,\n        ]);\n",
     "            'messages' => $msgs,\n"
     "            'channels' => (function () { $s0 = getSettings(); return waMultiOn(waConf($s0), $s0) ? waChannels($s0) : []; })(),   // v1.2.98: multi-nomor\n"
     "        ]);\n"),
    # blast: pilih nomor pengirim
    ("        requireAuth(['super_admin', 'admin', 'supervisor']);\n        $wa = waConf(getSettings());\n        if (($wa['provider'] ?? 'meta') !== 'meta') {\n",
     "        requireAuth(['super_admin', 'admin', 'supervisor']);\n        $wa = waConf(getSettings());\n"
     "        $wa = waChanConf($wa, preg_replace('/[^A-Za-z0-9_]/', '', (string)($_GET['ch'] ?? '')));   // v1.2.98: multi-nomor (template per WABA nomor)\n"
     "        if (($wa['provider'] ?? 'meta') !== 'meta') {\n"),
    ("        jsonOut(['ok' => true, 'templates' => $out]);\n",
     "        $s0 = getSettings();\n"
     "        jsonOut(['ok' => true, 'templates' => $out, 'ch' => (string)$wa['_ch'],\n"
     "                 'channels' => waMultiOn(waConf($s0), $s0) ? waChannels($s0) : []]);   // v1.2.98: multi-nomor\n"),
    ("            'source'        => $source,\n            'total'         => count($rows),\n",
     "            'source'        => $source,\n"
     "            'ch'            => (string)waChanConf($wa, preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['ch'] ?? '')))['_ch'],   // v1.2.98: multi-nomor\n"
     "            'total'         => count($rows),\n"),
    ("            $r = waSendTemplate($wa, $row['num'], $job['template_name'], $job['language'], $vars);\n",
     "            $r = waSendTemplate(waChanConf($wa, (string)($job['ch'] ?? 'utama')), $row['num'], $job['template_name'], $job['language'], $vars);   // v1.2.98: multi-nomor\n"),
    # kartu pemakaian: pesan keluar per nomor
    ("                                            'service' => $o['service'], 'template' => $o['template'], 'saved' => $o['saved'],   // v1.2.89\n",
     "                                            'service' => $o['service'], 'template' => $o['template'], 'saved' => $o['saved'],   // v1.2.89\n"
     "                                            'by_ch' => (function () use ($s0, $w, $o) {   // v1.2.98: multi-nomor\n"
     "                                                if (!waMultiOn($w, $s0)) return [];\n"
     "                                                $r = [];\n"
     "                                                foreach (waChannels($s0) as $c) $r[] = ['id' => $c['id'], 'label' => $c['label'],\n"
     "                                                    'service' => (int)($o['ch'][$c['id']]['service'] ?? 0), 'template' => (int)($o['ch'][$c['id']]['template'] ?? 0)];\n"
     "                                                return $r; })(),\n"),
]
patch(TEN, 'api/index.php', php)

# ============================================================== HTML
HTML_CARD = '''      <!-- v1.2.98: multi-nomor -->
      <div class="card" data-role-card="super_admin,admin" id="waNumsCard" style="display:none"><h3>Nomor WhatsApp</h3>
        <div class="desc">Satu akun bisa menjawab dari beberapa nomor WhatsApp (mis. per cabang atau divisi). Semua chat masuk ke satu dashboard; balasan bot &amp; agent selalu keluar dari nomor yang dihubungi pelanggan. Nomor tambahan memakai penyedia yang sama dengan nomor utama.</div>
        <div id="wn_list"></div>
        <div id="wn_form" class="hide" style="border:1px dashed var(--line,#d0d0d0);border-radius:8px;padding:12px;margin-top:10px">
          <input type="hidden" id="wn_id">
          <div class="row"><label class="fl">Label</label><input type="text" id="wn_label" maxlength="40" placeholder="mis. Cabang Bandung / CS Tiket"><div class="help">Tampil di daftar percakapan supaya agent tahu chat masuk lewat nomor mana.</div></div>
          <div class="wn-meta">
            <div class="row"><label class="fl">Phone Number ID</label>
              <div style="display:flex;gap:8px;flex-wrap:wrap"><input type="text" id="wn_pnid" class="mono" placeholder="1234567890" style="flex:1;min-width:180px"><button class="btn ghost" id="wn_pick" type="button">Ambil dari WABA</button></div>
              <select id="wn_pick_sel" class="hide" style="margin-top:6px"></select>
              <div class="help">Nomor tambahan di WABA yang sama cukup diisi Phone Number ID — token &amp; webhook memakai milik nomor utama.</div></div>
            <div class="grid2">
              <div class="row"><label class="fl">Access Token (opsional)</label><input type="text" id="wn_token" class="mono" placeholder="kosong = pakai token nomor utama"><div class="help">Isi hanya bila nomor ini di WABA / Business Manager lain.</div></div>
              <div class="row"><label class="fl">WABA ID (opsional)</label><input type="text" id="wn_waba" class="mono" placeholder="kosong = WABA nomor utama"><div class="help">Untuk template Blast nomor ini. Pastikan app sudah subscribe ke WABA tsb.</div></div>
            </div>
          </div>
          <div class="wn-waha">
            <div class="row"><label class="fl">Nama Sesi WAHA</label><input type="text" id="wn_sess" class="mono" placeholder="mis. cabang2"><div class="help">Satu sesi = satu nomor. Harus berbeda dari sesi nomor utama.</div></div>
            <div class="grid2">
              <div class="row"><label class="fl">URL Server WAHA (opsional)</label><input type="text" id="wn_wurl" class="mono" placeholder="kosong = server nomor utama"></div>
              <div class="row"><label class="fl">API Key WAHA (opsional)</label><input type="text" id="wn_wkey" class="mono" placeholder="kosong = API key nomor utama"></div>
            </div>
          </div>
          <div class="row" style="flex-direction:row;gap:8px;flex-wrap:wrap">
            <button class="btn" id="wn_save" type="button">Simpan nomor</button>
            <button class="btn ghost" id="wn_cancel" type="button">Batal</button>
          </div>
        </div>
        <div class="row" style="flex-direction:row;gap:8px;flex-wrap:wrap;margin-top:10px" data-role-card="super_admin">
          <button class="btn ghost" id="wn_add" type="button">+ Tambah nomor</button>
          <span class="help" id="wn_hint" style="margin:0"></span>
        </div>
        <div class="help" style="margin-top:8px">Pelanggan yang menghubungi lebih dari satu nomor tetap tampil sebagai satu percakapan; balasan keluar dari nomor yang terakhir ia hubungi.</div>
      </div>

'''
patch(TEN, 'dashboard/chatbot-ai/index.html', [
    ('      <div class="card" data-role-card="super_admin"><h3>WhatsApp Bot</h3>\n',
     HTML_CARD + '      <div class="card" data-role-card="super_admin"><h3>WhatsApp Bot</h3>\n'),
    ('          <span class="pill off" id="fonc_pill">Memeriksa…</span>\n',
     '          <select id="fonc_ch" class="hide" style="max-width:220px"></select><!-- v1.2.98: multi-nomor -->\n'
     '          <span class="pill off" id="fonc_pill">Memeriksa…</span>\n'),
    ('          <div class="row"><label class="fl">Template</label>\n            <div style="display:flex;gap:8px">\n              <select id="blastTemplate"',
     '          <div class="row" id="blastChRow" style="display:none"><label class="fl">Kirim dari nomor</label><select id="blastCh"></select></div><!-- v1.2.98: multi-nomor -->\n'
     '          <div class="row"><label class="fl">Template</label>\n            <div style="display:flex;gap:8px">\n              <select id="blastTemplate"'),
    ('<script src="app.js?v=1.2.95"></script><!-- v1.2.95: kb-foto -->',
     '<script src="app.js?v=1.2.98"></script><!-- v1.2.98: multi-nomor -->'),
])

# ============================================================== JS
JS_NUMS = r'''
  /* v1.2.98: multi-nomor — kartu "Nomor WhatsApp" */
  var _wn = { prov: 'meta', rows: [], max: 9 };
  function wnInit(wa) {
    var card = $('#waNumsCard'); if (!card) return;
    var prov = (wa && wa.provider) || 'meta';
    _wn.prov = prov;
    if (prov !== 'meta' && prov !== 'waha') { card.style.display = 'none'; return; }
    card.style.display = '';
    $$('#waNumsCard .wn-meta').forEach(function (el) { el.style.display = prov === 'meta' ? '' : 'none'; });
    $$('#waNumsCard .wn-waha').forEach(function (el) { el.style.display = prov === 'waha' ? '' : 'none'; });
    if (card.dataset.wired !== '1') {
      card.dataset.wired = '1';
      $('#wn_add').onclick = function () { wnForm(null); };
      $('#wn_cancel').onclick = function () { $('#wn_form').classList.add('hide'); };
      $('#wn_save').onclick = wnSave;
      $('#wn_pick').onclick = wnPick;
      $('#wn_pick_sel').onchange = function () {
        var o = this.options[this.selectedIndex]; if (!o || !o.value) return;
        $('#wn_pnid').value = o.value;
        if (!$('#wn_label').value.trim() && o.dataset.name) $('#wn_label').value = o.dataset.name;
      };
      $('#wn_list').onclick = function (ev) {
        var b = ev.target.closest('button[data-wn]'); if (!b) return;
        var id = b.dataset.id, row = _wn.rows.filter(function (r) { return r.id === id; })[0];
        if (b.dataset.wn === 'edit') wnForm(row);
        else if (b.dataset.wn === 'del') wnDelete(row);
        else if (b.dataset.wn === 'qr') wnConnect(row);
      };
    }
    wnLoad();
  }
  function wnLoad() {
    return api('wa_numbers').then(function (r) {
      if (!r || !r.ok) { $('#wn_list').innerHTML = '<div class="help">' + esc((r && r.error) || 'Gagal memuat nomor.') + '</div>'; return; }
      _wn.rows = r.numbers || []; _wn.max = r.max || 9;
      var sa = role === 'super_admin', waha = r.provider === 'waha';
      var extra = _wn.rows.length - 1;
      $('#wn_list').innerHTML = '<div class="tbl-wrap"><table class="tbl" style="width:100%"><thead><tr><th>Label</th><th>Nomor</th><th>' + (waha ? 'Sesi WAHA' : 'Phone Number ID') + '</th><th></th></tr></thead><tbody>' +
        _wn.rows.map(function (x) {
          var idc = waha ? (x.waha_session || '') : (x.phone_number_id || (sa ? '' : '••••'));
          var acts = '';
          if (waha && x.id !== 'utama') acts += '<button class="btn ghost sm" type="button" data-wn="qr" data-id="' + esc(x.id) + '">Koneksi</button> ';
          if (sa) acts += '<button class="btn ghost sm" type="button" data-wn="edit" data-id="' + esc(x.id) + '">Ubah</button> ';
          if (sa && !x.primary) acts += '<button class="btn ghost sm" type="button" data-wn="del" data-id="' + esc(x.id) + '">Hapus</button>';
          return '<tr><td>' + (x.primary ? '<span class="tag" style="margin-right:4px">Utama</span>' : '') + esc(x.label || (x.primary ? 'Nomor utama' : '')) + '</td>' +
            '<td class="mono">' + (x.number ? '+' + esc(x.number) : '<span style="color:var(--muted)">—</span>') + (x.verified_name ? '<div class="help" style="margin:0">' + esc(x.verified_name) + '</div>' : '') + '</td>' +
            '<td class="mono" style="font-size:12px">' + esc(idc) + '</td><td style="white-space:nowrap;text-align:right">' + acts + '</td></tr>';
        }).join('') + '</tbody></table></div>';
      $('#wn_add').disabled = extra >= _wn.max;
      $('#wn_hint').textContent = extra > 0 ? (extra + ' nomor tambahan (maks ' + _wn.max + ')') : 'Belum ada nomor tambahan.';
      foncChannels(r.channels || []);
    });
  }
  function wnForm(row) {
    var f = $('#wn_form'); f.classList.remove('hide');
    var isPrim = !!(row && row.primary);
    $('#wn_id').value = row ? row.id : '';
    $('#wn_label').value = row ? (row.label || '') : '';
    $('#wn_pnid').value = row ? (row.phone_number_id || '') : '';
    $('#wn_token').value = ''; $('#wn_token').placeholder = (row && row.token_is_set) ? '•••• (terisi — kosongkan untuk tidak mengubah)' : 'kosong = pakai token nomor utama';
    $('#wn_waba').value = row ? (row.waba_id || '') : '';
    $('#wn_sess').value = row ? (row.waha_session || '') : '';
    $('#wn_wurl').value = row ? (row.waha_url || '') : '';
    $('#wn_wkey').value = ''; $('#wn_wkey').placeholder = (row && row.waha_key_is_set) ? '•••• (terisi — kosongkan untuk tidak mengubah)' : 'kosong = API key nomor utama';
    $('#wn_pick_sel').classList.add('hide');
    // nomor utama: hanya label (kredensialnya diatur di kartu WhatsApp Bot)
    $$('#waNumsCard .wn-meta, #waNumsCard .wn-waha').forEach(function (el) { el.style.display = 'none'; });
    if (!isPrim) $$(_wn.prov === 'waha' ? '#waNumsCard .wn-waha' : '#waNumsCard .wn-meta').forEach(function (el) { el.style.display = ''; });
    $('#wn_label').focus();
  }
  function wnSave() {
    var id = $('#wn_id').value, b = $('#wn_save');
    var body = { op: 'save', id: id, label: $('#wn_label').value.trim() };
    if (id !== 'utama') {
      if (_wn.prov === 'waha') {
        body.waha_session = $('#wn_sess').value.trim(); body.waha_url = $('#wn_wurl').value.trim(); body.waha_api_key = $('#wn_wkey').value.trim();
        if (!body.waha_session) { toast('Isi nama sesi WAHA.', true); return; }
      } else {
        body.phone_number_id = $('#wn_pnid').value.trim(); body.access_token = $('#wn_token').value.trim(); body.waba_id = $('#wn_waba').value.trim();
        if (!body.phone_number_id) { toast('Isi Phone Number ID.', true); return; }
      }
    }
    b.disabled = true;
    api('wa_numbers', { method: 'POST', body: body }).then(function (r) {
      b.disabled = false;
      if (!r || !r.ok) { toast((r && r.error) || 'Gagal menyimpan.', true); return; }
      $('#wn_form').classList.add('hide');
      toast(r.warning ? ('Tersimpan. ' + r.warning) : 'Nomor tersimpan.', !!r.warning);
      wnLoad().then(function () {
        if (_wn.prov === 'waha' && !id && r.id) { var nr = _wn.rows.filter(function (x) { return x.id === r.id; })[0]; if (nr) wnConnect(nr); }
      });
    }).catch(function () { b.disabled = false; toast('Koneksi bermasalah.', true); });
  }
  function wnDelete(row) {
    if (!row || !confirm('Hapus nomor "' + (row.label || row.number || row.id) + '" dari chatbot? Pelanggan nomor ini selanjutnya dibalas dari nomor utama.' + (_wn.prov === 'waha' ? ' Sesi WAHA tidak dihapus dari server.' : ''))) return;
    api('wa_numbers', { method: 'POST', body: { op: 'delete', id: row.id } }).then(function (r) {
      toast(r && r.ok ? 'Nomor dihapus.' : ((r && r.error) || 'Gagal menghapus.'), !(r && r.ok));
      wnLoad();
    });
  }
  function wnPick() {
    var b = $('#wn_pick'), sel = $('#wn_pick_sel');
    b.disabled = true;
    api('wa_numbers', { method: 'POST', body: { op: 'meta_phones', waba_id: $('#wn_waba').value.trim(), access_token: $('#wn_token').value.trim() } }).then(function (r) {
      b.disabled = false;
      if (!r || !r.ok) { toast((r && r.error) || 'Gagal membaca WABA.', true); return; }
      var ph = r.phones || [];
      if (!ph.length) { toast('Tidak ada nomor di WABA ini.', true); return; }
      sel.innerHTML = '<option value="">— Pilih nomor dari WABA ' + esc(r.waba_id) + ' —</option>' + ph.map(function (p) {
        var used = p.used_by ? (p.used_by === 'utama' ? ' (nomor utama)' : ' (sudah terdaftar)') : '';
        return '<option value="' + esc(p.phone_number_id) + '" data-name="' + esc(p.verified_name || '') + '"' + (p.used_by ? ' disabled' : '') + '>+' + esc(p.number) + ' · ' + esc(p.verified_name || '') + used + '</option>';
      }).join('');
      sel.classList.remove('hide');
    }).catch(function () { b.disabled = false; });
  }
  function wnConnect(row) {
    var sel = $('#fonc_ch'), card = $('#fonConnCard');
    if (!sel || !card || card.style.display === 'none') { toast('Isi URL & API Key WAHA nomor utama dulu.', true); return; }
    sel.value = row.id; _fonc.ch = row.id; foncStop(); foncStatus();
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  // Pilihan nomor di kartu Koneksi WhatsApp (WAHA)
  function foncChannels(chs) {
    var sel = $('#fonc_ch'); if (!sel) return;
    if (_wn.prov !== 'waha' || chs.length < 2) { sel.classList.add('hide'); if (_fonc.ch && _fonc.ch !== 'utama') { _fonc.ch = 'utama'; foncStatus(); } return; }
    var cur = _fonc.ch || 'utama';
    sel.innerHTML = chs.map(function (c) { return '<option value="' + esc(c.id) + '">' + esc(c.label) + '</option>'; }).join('');
    if (!chs.some(function (c) { return c.id === cur; })) cur = 'utama';
    sel.value = cur; _fonc.ch = cur;
    sel.classList.remove('hide');
    if (sel.dataset.wired !== '1') {
      sel.dataset.wired = '1';
      sel.onchange = function () { _fonc.ch = this.value; foncStop(); foncStatus(); };
    }
  }
'''

js = [
    # kartu koneksi: kirim ch ke waha_conn
    ("  var _fonc = { poll: null, qrT: null, stopT: null, waitT: null, mode: 'qr', action: 'fonnte_conn' };\n",
     "  var _fonc = { poll: null, qrT: null, stopT: null, waitT: null, mode: 'qr', action: 'fonnte_conn', ch: 'utama' };   // v1.2.98: multi-nomor (ch)\n"
     "  function foncBody(b) { if (_fonc.action === 'waha_conn' && _fonc.ch && _fonc.ch !== 'utama') b.ch = _fonc.ch; return b; }\n"),
    ("    return api(_fonc.action, { method: 'POST', body: { op: 'status' } }).then(function (r) {\n",
     "    return api(_fonc.action, { method: 'POST', body: foncBody({ op: 'status' }) }).then(function (r) {\n"),
    ("    var body = { op: 'qr' };\n",
     "    var body = foncBody({ op: 'qr' });\n"),
    ("        api(_fonc.action, { method: 'POST', body: { op: 'disconnect' } }).then(function (r) {\n",
     "        api(_fonc.action, { method: 'POST', body: foncBody({ op: 'disconnect' }) }).then(function (r) {\n"),
    ("        api(_fonc.action, { method: 'POST', body: { op: 'webhook' } }).then(function (r) {\n",
     "        api(_fonc.action, { method: 'POST', body: foncBody({ op: 'webhook' }) }).then(function (r) {\n"),
    ("  // v1.2.54: Embedded Signup coexistence (WA Business App + Cloud API di satu nomor)\n",
     JS_NUMS + "\n  // v1.2.54: Embedded Signup coexistence (WA Business App + Cloud API di satu nomor)\n"),
    ("      foncInit(s.whatsapp_api || {});   // v1.2.75\n",
     "      foncInit(s.whatsapp_api || {});   // v1.2.75\n"
     "      wnInit(s.whatsapp_api || {});     // v1.2.98: multi-nomor\n"),
    # percakapan: filter + label
    ("    var query = '&filter=' + encodeURIComponent(waState.filter || 'all');\n",
     "    var query = '&filter=' + encodeURIComponent(waState.filter || 'all');\n"
     "    if (waState.ch) query += '&ch=' + encodeURIComponent(waState.ch);   // v1.2.98: multi-nomor\n"),
    ("      waState.agents = res.agents || [];\n",
     "      waState.agents = res.agents || [];\n"
     "      waState.channels = res.channels || [];   // v1.2.98: multi-nomor\n"
     "      if (waState.ch && !waState.channels.some(function (c) { return c.id === waState.ch; })) waState.ch = '';\n"),
    ("      (waState.isAdmin === false ? '' : '<button class=\"wa-filter-btn wa-export-contacts\"",
     "      ((waState.channels || []).length > 1 ? '<select class=\"wa-ch-filter\" title=\"Saring per nomor WhatsApp\" style=\"width:auto;max-width:220px;flex:0 0 auto;padding:5px 10px;border-radius:999px;font-size:12px\"><option value=\"\">Semua nomor</option>' +   // v1.2.98: multi-nomor\n"
     "        waState.channels.map(function (c) { return '<option value=\"' + esc(c.id) + '\"' + (waState.ch === c.id ? ' selected' : '') + '>' + esc(c.label) + '</option>'; }).join('') + '</select>' : '') +\n"
     "      (waState.isAdmin === false ? '' : '<button class=\"wa-filter-btn wa-export-contacts\""),
    ("    $$('#waFilterBar .wa-filter-btn').forEach(function (btn) {\n      if (btn.classList.contains('wa-audit-toggle')) {\n",
     "    var _chSel = $('#waFilterBar .wa-ch-filter');   // v1.2.98: multi-nomor\n"
     "    if (_chSel) _chSel.onchange = function () { waState.ch = this.value; fetchWaConvs(); };\n"
     "    $$('#waFilterBar .wa-filter-btn').forEach(function (btn) {\n      if (btn.classList.contains('wa-audit-toggle')) {\n"),
    ("      var stageBadge = ' ' + contactStageBadgeHtml(c.stage, c.vip, ';margin-left:2px');\n",
     "      var stageBadge = ' ' + contactStageBadgeHtml(c.stage, c.vip, ';margin-left:2px');\n"
     "      if (c.ch_label && (waState.channels || []).length > 1) stageBadge += ' <span class=\"tag\" style=\"background:#ede9fe;color:#5b21b6\" title=\"Nomor WhatsApp yang dihubungi\">' + ico('phone', 11) + ' ' + esc(c.ch_label) + '</span>';   // v1.2.98: multi-nomor\n"),
    ("    var _judulThread = _nama\n      ? '<strong>' + esc(_nama) + '</strong> <span style=\"color:var(--muted);font-size:12px\">+' + esc(res.number) + '</span>'\n      : '<strong>+' + esc(res.number) + '</strong>';\n",
     "    var _judulThread = _nama\n      ? '<strong>' + esc(_nama) + '</strong> <span style=\"color:var(--muted);font-size:12px\">+' + esc(res.number) + '</span>'\n      : '<strong>+' + esc(res.number) + '</strong>';\n"
     "    if (_konv && _konv.ch_label && (res.channels || []).length > 1) _judulThread += ' <span class=\"tag\" style=\"background:#ede9fe;color:#5b21b6;font-size:11px\" title=\"Balasan dikirim dari nomor ini\">via ' + esc(_konv.ch_label) + '</span>';   // v1.2.98: multi-nomor\n"),
    # thread: nomor tujuan per pesan masuk
    ("  function waBubble(text, kind, ts, media) {\n",
     "  function waBubble(text, kind, ts, media, via) {   // v1.2.98: multi-nomor (via = nomor bisnis yang dihubungi)\n"),
    ("      waMediaHtml(media) + esc(text) + '<div style=\"font-size:10px;opacity:.65;margin-top:4px\">' + esc((ts || '').slice(11, 16)) + who + '</div></div>';\n",
     "      waMediaHtml(media) + esc(text) + '<div style=\"font-size:10px;opacity:.65;margin-top:4px\">' + esc((ts || '').slice(11, 16)) + who + (via ? ' · ke ' + esc(via) : '') + '</div></div>';\n"),
    ("    var _waLastDate = '';   // v1.2.15: reset tiap render -> aman untuk polling\n",
     "    var _waLastDate = '';   // v1.2.15: reset tiap render -> aman untuk polling\n"
     "    var _chL = {}; (res.channels || []).forEach(function (c) { _chL[c.id] = c.label; });   // v1.2.98: multi-nomor\n"
     "    var _chMulti = (res.channels || []).length > 1;\n"),
    ("      if (m.q) h += waBubble(m.q, 'in', m.ts, m.media);",
     "      if (m.q) h += waBubble(m.q, 'in', m.ts, m.media, (_chMulti && m.ch) ? (_chL[m.ch] || '') : '');"),
    # blast
    ("    api('wa_templates').then(function(res){\n      if (!res.ok) { if(hint) hint.textContent = res.error || 'Gagal memuat template.'; return; }\n",
     "    var _bch = $('#blastCh') ? $('#blastCh').value : '';   // v1.2.98: multi-nomor\n"
     "    api('wa_templates', { query: _bch ? '&ch=' + encodeURIComponent(_bch) : '' }).then(function(res){\n"
     "      if (!res.ok) { if(hint) hint.textContent = res.error || 'Gagal memuat template.'; return; }\n"
     "      var chs = res.channels || [], cs = $('#blastCh');   // v1.2.98: multi-nomor\n"
     "      if (cs) {\n"
     "        $('#blastChRow').style.display = chs.length > 1 ? '' : 'none';\n"
     "        if (chs.length > 1 && cs.options.length !== chs.length) {\n"
     "          cs.innerHTML = chs.map(function (c) { return '<option value=\"' + esc(c.id) + '\">' + esc(c.label) + '</option>'; }).join('');\n"
     "          cs.value = res.ch || 'utama';\n"
     "        }\n"
     "        if (!cs.dataset.wired) { cs.dataset.wired = '1'; cs.onchange = fetchBlastTemplates; }\n"
     "      }\n"),
    ("    var body={ template_name:t.name, language:t.language||'id', vars:vars, source:source };\n",
     "    var body={ template_name:t.name, language:t.language||'id', vars:vars, source:source };\n"
     "    if ($('#blastCh') && $('#blastCh').value) body.ch = $('#blastCh').value;   // v1.2.98: multi-nomor\n"),
    # kartu pemakaian: rincian per nomor
    ("          if (wo.saved > 0) note += ' · ' + wo.saved + ' dihemat';   // v1.2.89\n",
     "          if (wo.saved > 0) note += ' · ' + wo.saved + ' dihemat';   // v1.2.89\n"
     "          if ((wo.by_ch || []).length > 1) note += ' · ' + wo.by_ch.map(function (c) { return c.label + ': ' + c.service + (c.template ? ' + ' + c.template + ' tpl' : ''); }).join(', ');   // v1.2.98: multi-nomor\n"),
]
patch(TEN, 'dashboard/chatbot-ai/app.js', js)
print('selesai')
