#!/usr/bin/env python3
r"""v1.2.128 wa-campur: penyedia per nomor — nomor utama & nomor tambahan boleh beda penyedia
(mis. nomor utama Meta Cloud API resmi + nomor cabang WAHA, atau sebaliknya).
- wa_numbers[].provider ('meta' | 'waha'; kosong = ikut nomor utama, data lama tidak berubah).
- waChanConf memasang provider per nomor -> semua kiriman (teks, foto, file, template, mengetik) ikut nomor itu.
- Webhook Meta / WAHA diterima selama ada minimal satu nomor dengan penyedia itu.
- Jendela 24 jam hanya untuk chat yang nomornya Meta (waWinFree). Blast template hanya dari nomor Meta.
- Fitur khusus WAHA (kesehatan, telepon, riwayat, koneksi QR) jalan per nomor WAHA.
- UI kartu Nomor WhatsApp: pilihan penyedia per nomor; kartu Koneksi WhatsApp muncul bila ada nomor WAHA.
Pakai: python3 patch_v12128_wa_campur.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.127)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.128: wa-campur'
STAMP = time.strftime('%Y%m%d-%H%M%S')

def rep(s, old, new, rel):
    n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:100]); return s.replace(old, new)

def rep_between(s, start, end, new, rel):
    assert s.count(start) == 1, '%s: start %dx: %r' % (rel, s.count(start), start[:100])
    i = s.index(start); j = s.find(end, i)
    assert j > i, '%s: end tidak ketemu: %r' % (rel, end[:100])
    return s[:i] + new + s[j + len(end):]

def patch(rel, fn, need):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    assert need in s, rel + ': butuh v1.2.127'
    s2 = fn(s, rel); assert TAG in s2, rel
    shutil.copy2(p, p + '.bak-v12128-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s2); print('OK', rel)

# ======================================================================
def f_api(s, rel):
    s = rep(s, "define('DEI_VERSION', 'v1.2.127');   // v1.2.127: respon-kata",
               "define('DEI_VERSION', 'v1.2.128');   // v1.2.128: wa-campur", rel)
    s = rep(s, " * Nomor utama = whatsapp_api (id 'utama'). Nomor tambahan memakai penyedia yang sama (Meta / WAHA);\n",
               " * Nomor utama = whatsapp_api (id 'utama'). v1.2.128: wa-campur — nomor tambahan boleh beda penyedia\n"
               " * (wa_numbers[].provider 'meta' | 'waha'; kosong = ikut nomor utama). Untuk penyedia yang sama,\n", rel)

    # ---- helper penyedia per nomor ----
    s = rep(s, "function waMultiOn($wa, $s = null) { return waMultiProv($wa) && count(waNumbersRaw($s)) > 0; }\n",
        "function waMultiOn($wa, $s = null) { return waMultiProv($wa) && count(waNumbersRaw($s)) > 0; }\n"
        "// v1.2.128: wa-campur — penyedia per nomor. Kosong = ikut nomor utama (data lama).\n"
        "function waNumProv($x, $wa) {\n"
        "    $p = (string)(is_array($x) ? ($x['provider'] ?? '') : '');\n"
        "    return in_array($p, ['meta', 'waha'], true) ? $p : (string)($wa['provider'] ?? 'meta');\n"
        "}\n"
        "// Penyedia $p dipakai nomor utama atau salah satu nomor tambahan aktif.\n"
        "function waHasProv($p, $s = null) {\n"
        "    if ($s === null) $s = getSettings();\n"
        "    $wa = waConf($s);\n"
        "    if ((string)($wa['provider'] ?? 'meta') === $p) return true;\n"
        "    if (!waMultiProv($wa)) return false;\n"
        "    foreach (waNumbersRaw($s) as $x) { if (waNumProv($x, $wa) === $p) return true; }\n"
        "    return false;\n"
        "}\n"
        "function waChanProv($id, $s = null) {\n"
        "    if ($s === null) $s = getSettings();\n"
        "    $id = ((string)$id === '') ? 'utama' : (string)$id;\n"
        "    foreach (waChannels($s) as $c) { if ($c['id'] === $id) return (string)$c['prov']; }\n"
        "    return (string)(waConf($s)['provider'] ?? 'meta');\n"
        "}\n"
        "// Nomor-nomor tenant memakai lebih dari satu penyedia (Meta + WAHA).\n"
        "function waMixed($s = null) {\n"
        "    $p = [];\n"
        "    foreach (waChannels($s) as $c) $p[(string)$c['prov']] = 1;\n"
        "    return count($p) > 1;\n"
        "}\n"
        "// Jendela 24 jam tidak berlaku untuk chat ini (nomor bisnisnya bukan Meta).\n"
        "function waWinFree($num, $s = null) {\n"
        "    if ($s === null) $s = getSettings();\n"
        "    if (!waMixed($s)) return waWindowSelaluTerbuka();\n"
        "    return waChanProv(waCurCh($num, $s), $s) !== 'meta';\n"
        "}\n"
        "// Nomor untuk Blast/template: tanpa pilihan & nomor utama bukan Meta -> nomor Meta pertama.\n"
        "function waMetaChanConf($wa, $id, $s = null) {\n"
        "    $c = waChanConf($wa, $id, $s);\n"
        "    if ((string)$id !== '' || (string)($c['provider'] ?? 'meta') === 'meta') return $c;\n"
        "    foreach (waChannels($s) as $x) { if ($x['prov'] === 'meta') return waChanConf($wa, $x['id'], $s); }\n"
        "    return $c;\n"
        "}\n", rel)

    # ---- waChannels: penyedia per nomor ----
    s = rep(s, "    $out = [['id' => 'utama', 'label' => waChanLabelOf($wa, $prov, 'Nomor utama'), 'number' => waChanNumOf($wa, $prov), 'primary' => true]];\n",
               "    $out = [['id' => 'utama', 'label' => waChanLabelOf($wa, $prov, 'Nomor utama'), 'number' => waChanNumOf($wa, $prov), 'primary' => true, 'prov' => $prov]];   // v1.2.128: wa-campur\n", rel)
    s = rep(s, "        $out[] = ['id' => (string)$x['id'], 'label' => waChanLabelOf($x, $prov, 'Nomor ' . $i), 'number' => waChanNumOf($x, $prov), 'primary' => false];\n",
               "        $xp = waNumProv($x, $wa);   // v1.2.128: wa-campur\n"
               "        $out[] = ['id' => (string)$x['id'], 'label' => waChanLabelOf($x, $xp, 'Nomor ' . $i), 'number' => waChanNumOf($x, $xp), 'primary' => false, 'prov' => $xp];\n", rel)

    # ---- waChanConf: provider per nomor; kredensial Meta tidak diwarisi dari nomor utama non-Meta ----
    s = rep_between(s, "            $c = $wa;\n            if ($prov === 'waha') {\n",
        "            $c['_ch'] = $id;\n            return $c;\n",
        "            $xp = waNumProv($x, $wa); $same = ($xp === $prov);   // v1.2.128: wa-campur\n"
        "            $c = $wa; $c['provider'] = $xp;\n"
        "            if ($xp === 'waha') {\n"
        "                $c['waha_session'] = (string)($x['waha_session'] ?? '');\n"
        "                if (trim((string)($x['waha_url'] ?? '')) !== '') $c['waha_url'] = (string)$x['waha_url'];\n"
        "                if ((string)($x['waha_api_key'] ?? '') !== '') $c['waha_api_key'] = (string)$x['waha_api_key'];\n"
        "                $c['waha_number'] = (string)($x['waha_number'] ?? '');\n"
        "            } else {\n"
        "                $c['phone_number_id'] = (string)($x['phone_number_id'] ?? '');\n"
        "                $c['display_number'] = (string)($x['display_number'] ?? '');\n"
        "                if (!$same) { $c['access_token'] = ''; $c['waba_id'] = ''; }   // nomor utama bukan Meta: tidak ada yang diwarisi\n"
        "                if ((string)($x['access_token'] ?? '') !== '') $c['access_token'] = (string)$x['access_token'];\n"
        "                if ((string)($x['waba_id'] ?? '') !== '') $c['waba_id'] = (string)$x['waba_id'];\n"
        "            }\n"
        "            $c['_ch'] = $id;\n            return $c;\n", rel)

    # ---- waChanFromMeta ----
    s = rep_between(s, "function waChanFromMeta($wa, $meta) {\n", "    return waChanConf($wa, 'utama');\n}\n",
        "function waChanFromMeta($wa, $meta) {\n"
        "    $meta = is_array($meta) ? $meta : [];\n"
        "    $pid = (string)($meta['phone_number_id'] ?? '');\n"
        "    $mp = (string)($wa['provider'] ?? 'meta');   // v1.2.128: wa-campur\n"
        "    if ($pid !== '' && !($mp === 'meta' && $pid === (string)($wa['phone_number_id'] ?? ''))) {\n"
        "        if (waMultiProv($wa)) {\n"
        "            $act = [];\n"
        "            foreach (waNumbersRaw() as $x) $act[(string)$x['id']] = true;\n"
        "            foreach (waNumbersRaw(null, true) as $x) {\n"
        "                if (waNumProv($x, $wa) !== 'meta' || (string)($x['phone_number_id'] ?? '') !== $pid) continue;\n"
        "                return isset($act[(string)$x['id']]) ? waChanConf($wa, (string)$x['id']) : null;\n"
        "            }\n"
        "        }\n"
        "        if ($mp !== 'meta') return null;   // kiriman Meta untuk nomor yang tidak terdaftar — jangan dijawab dari nomor WAHA\n"
        "    }\n"
        "    if (!waMultiOn($wa)) return $wa;\n"
        "    if (!empty($meta['_dei_ch'])) return waChanConf($wa, (string)$meta['_dei_ch']);\n"
        "    return waChanConf($wa, 'utama');\n}\n", rel)

    # ---- waWahaChanBySession ----
    s = rep_between(s, "function waWahaChanBySession($wa, $sess) {\n", "    return null;\n}\n",
        "function waWahaChanBySession($wa, $sess) {\n"
        "    $sess = (string)$sess;\n"
        "    if ((string)($wa['provider'] ?? 'meta') === 'waha' && $sess === wahaSession($wa)) return waMultiOn($wa) ? waChanConf($wa, 'utama') : $wa;\n"
        "    if (!waMultiProv($wa)) return null;   // v1.2.128: wa-campur — nomor WAHA tambahan walau nomor utama Meta\n"
        "    foreach (waNumbersRaw() as $x) {\n"
        "        if (waNumProv($x, $wa) !== 'waha' || trim((string)($x['waha_session'] ?? '')) === '') continue;\n"
        "        $c = waChanConf($wa, (string)$x['id']);\n"
        "        if (wahaSession($c) === $sess) return $c;\n"
        "    }\n"
        "    return null;\n}\n", rel)

    s = rep(s, "    if ((string)(waConf($s)['provider'] ?? 'meta') !== 'meta') return '';\n    return waCurCh($num, $s);\n",
               "    if (!waHasProv('meta', $s)) return '';   // v1.2.128: wa-campur\n    return waCurCh($num, $s);\n", rel)

    # ---- whChannels: hanya nomor WAHA ----
    s = rep_between(s, "function whChannels($s = null) {\n", "    return $out;\n}\n",
        "function whChannels($s = null) {\n"
        "    if ($s === null) $s = getSettings();\n"
        "    $wa = waConf($s);\n"
        "    $out = [];\n"
        "    foreach (waChannels($s) as $c) {\n"
        "        if (($c['prov'] ?? '') !== 'waha') continue;   // v1.2.128: wa-campur — per nomor\n"
        "        $conf = $c['id'] === 'utama' ? $wa : waChanConf($wa, $c['id'], $s);\n"
        "        if ($c['id'] !== 'utama' && ($conf['_ch'] ?? '') !== $c['id']) continue;\n"
        "        $out[] = [$c['id'], (string)$c['label'], $conf];\n"
        "    }\n"
        "    return $out;\n}\n", rel)

    # ---- escSendWa: pilih nomor dulu, baru penyedia ----
    s = rep(s, "    $wa = waConf($s);\n    if (($wa['provider'] ?? 'meta') === 'meta' && $ec['wa_template'] !== '') {\n",
               "    $wa = waChanFor(waConf($s), $to);   // v1.2.128: wa-campur\n    if (($wa['provider'] ?? 'meta') === 'meta' && $ec['wa_template'] !== '') {\n", rel)

    # ---- Blast ----
    s = rep(s, "        $wa = waChanConf($wa, preg_replace('/[^A-Za-z0-9_]/', '', (string)($_GET['ch'] ?? '')));   // v1.2.98: multi-nomor (template per WABA nomor)\n",
               "        $wa = waMetaChanConf($wa, preg_replace('/[^A-Za-z0-9_]/', '', (string)($_GET['ch'] ?? '')));   // v1.2.98: multi-nomor (template per WABA nomor); v1.2.128: nomor Meta\n", rel)
    s = rep(s, "                 'channels' => waMultiOn(waConf($s0), $s0) ? waChannels($s0) : []]);   // v1.2.98: multi-nomor\n",
               "                 'channels' => waMultiOn(waConf($s0), $s0) ? array_values(array_filter(waChannels($s0), function ($c) { return $c['prov'] === 'meta'; })) : []]);   // v1.2.98; v1.2.128: hanya nomor Meta\n", rel)
    s = rep(s, "        $wa = waConf(getSettings());\n        if (($wa['provider'] ?? 'meta') !== 'meta') jsonOut(['ok' => false, 'error' => 'Hanya untuk Meta Cloud API resmi.'], 400);\n        $in = bodyInput();\n",
               "        $wa = waConf(getSettings());\n        $in = bodyInput();\n"
               "        $wcB = waMetaChanConf($wa, preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['ch'] ?? '')));   // v1.2.128: wa-campur\n"
               "        if (($wcB['provider'] ?? 'meta') !== 'meta') jsonOut(['ok' => false, 'error' => 'Blast template hanya dari nomor Meta Cloud API resmi.'], 400);\n", rel)
    s = rep(s, "            'ch'            => (string)waChanConf($wa, preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['ch'] ?? '')))['_ch'],   // v1.2.98: multi-nomor\n",
               "            'ch'            => (string)$wcB['_ch'],   // v1.2.98: multi-nomor; v1.2.128\n", rel)

    # ---- Webhook ----
    s = rep(s, "        if (($wa['provider'] ?? 'meta') !== 'meta') { if (!$earlyAck) { echo 'EVENT_RECEIVED'; } exit; }\n",
               "        if (!waHasProv('meta', $s)) { if (!$earlyAck) { echo 'EVENT_RECEIVED'; } exit; }   // v1.2.128: wa-campur — cukup satu nomor Meta\n", rel)
    s = rep(s, "        if (!is_array($evt) || ($wa['provider'] ?? 'meta') !== 'waha') { echo 'OK'; exit; }   // v1.2.93: wa-bot-off\n",
               "        if (!is_array($evt) || !waHasProv('waha', $s)) { echo 'OK'; exit; }   // v1.2.93: wa-bot-off; v1.2.128: wa-campur\n", rel)

    # ---- Jendela 24 jam per penyedia nomor ----
    s = rep(s, "        foreach ($byNum as $num => $c) {\n            $c['mode'] = waGetMode($num);\n",
               "        $mx128 = waMixed();   // v1.2.128: wa-campur\n        foreach ($byNum as $num => $c) {\n            $c['mode'] = waGetMode($num);\n", rel)
    s = rep(s, "            $c['window_open'] = waWindowSelaluTerbuka() || ($inTs > 0",
               "            $c['window_open'] = ($mx128 ? waWinFree($num) : waWindowSelaluTerbuka()) || ($inTs > 0", rel)
    s = rep(s, "            'window_open' => waWindowSelaluTerbuka() || ($lastInbound > 0",
               "            'window_open' => waWinFree($num, $s116) || ($lastInbound > 0", rel)
    s = rep(s, "            'wa_prov' => (string)(waConf($s116)['provider'] ?? 'meta'),\n",
               "            'wa_prov' => waChanProv($curCh116, $s116),   // v1.2.128: wa-campur — penyedia nomor chat ini\n", rel)
    s = rep(s, "(time() - $lastInbound) > 24 * 3600) && !waWindowSelaluTerbuka()) {",
               "(time() - $lastInbound) > 24 * 3600) && !waWinFree($num, $s)) {", rel)
    s = rep(s, "            if (!waWindowSelaluTerbuka()) jsonOut(['ok' => false, 'error' => 'Jendela 24 jam tertutup'",
               "            if (!waWinFree($num, $s)) jsonOut(['ok' => false, 'error' => 'Jendela 24 jam tertutup'", rel)

    # ---- wa_calls / wa_health: cukup ada nomor WAHA ----
    s = rep(s, "        if (!whOn($wa)) jsonOut(['ok' => false, 'error' => 'Tolak telepon otomatis khusus penyedia WAHA.'], 400);\n"
               "        $ch = preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['ch'] ?? ($_GET['ch'] ?? 'utama')));\n",
               "        $whc128 = whChannels($s);   // v1.2.128: wa-campur\n"
               "        if (!$whc128) jsonOut(['ok' => false, 'error' => 'Tolak telepon otomatis khusus nomor WAHA.'], 400);\n"
               "        $ch = preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['ch'] ?? ($_GET['ch'] ?? 'utama')));\n"
               "        if ($ch === 'utama' && !whOn($wa)) $ch = (string)$whc128[0][0];\n", rel)
    s = rep(s, "        if (!whOn($wa)) jsonOut(['ok' => false, 'error' => 'Pemantauan kesehatan nomor khusus penyedia WAHA.'], 400);\n",
               "        $whc128 = whChannels($s);   // v1.2.128: wa-campur\n"
               "        if (!$whc128) jsonOut(['ok' => false, 'error' => 'Pemantauan kesehatan nomor khusus nomor WAHA.'], 400);\n", rel)
    s = rep(s, "        $ch = preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['ch'] ?? ($_GET['ch'] ?? 'utama')));\n        $conf = null; $label = '';\n",
               "        $ch = preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['ch'] ?? ($_GET['ch'] ?? 'utama')));\n"
               "        if ($ch === 'utama' && !whOn($wa)) $ch = (string)$whc128[0][0];\n        $conf = null; $label = '';\n", rel)

    # ---- wa_numbers ----
    s = rep(s, "            $p = ['id' => 'utama', 'primary' => true, 'label' => (string)($wa['label'] ?? ''), 'number' => waChanNumOf($wa, $prov),\n",
               "            $p = ['id' => 'utama', 'primary' => true, 'provider' => $prov, 'label' => (string)($wa['label'] ?? ''), 'number' => waChanNumOf($wa, $prov),   // v1.2.128\n", rel)
    s = rep(s, "                          'number' => waChanNumOf($x, $prov), 'verified_name' => (string)($x['verified_name'] ?? ''),\n",
               "                          'provider' => waNumProv($x, $wa), 'number' => waChanNumOf($x, waNumProv($x, $wa)), 'verified_name' => (string)($x['verified_name'] ?? ''),   // v1.2.128\n", rel)
    s = rep(s, "                     'channels' => waChannels($s), 'numbers' => $rows,\n                     'health' => whOn($wa) ? (object)",
               "                     'channels' => waChannels($s), 'numbers' => $rows,\n"
               "                     'main_waha_ok' => trim((string)($wa['waha_url'] ?? '')) !== '' && (string)($wa['waha_api_key'] ?? '') !== '',   // v1.2.128: wa-campur\n"
               "                     'health' => whChannels($s) ? (object)", rel)
    s = rep(s, "            if ($prov !== 'meta') jsonOut(['ok' => false, 'error' => 'Hanya untuk Meta Cloud API.'], 400);\n"
               "            $waba = preg_replace('/\\D/', '', (string)($in['waba_id'] ?? '')) ?: (string)($wa['waba_id'] ?? '');\n"
               "            $tok  = trim((string)($in['access_token'] ?? ''));\n"
               "            if ($tok === '' || strpos($tok, '•') !== false) $tok = (string)($wa['access_token'] ?? '');\n",
               "            $mm = ($prov === 'meta');   // v1.2.128: wa-campur — nomor utama bukan Meta: token & WABA milik nomor ini\n"
               "            $waba = preg_replace('/\\D/', '', (string)($in['waba_id'] ?? '')) ?: ($mm ? (string)($wa['waba_id'] ?? '') : '');\n"
               "            $tok  = trim((string)($in['access_token'] ?? ''));\n"
               "            if ($tok === '' || strpos($tok, '•') !== false) {\n"
               "                $tok = $mm ? (string)($wa['access_token'] ?? '') : '';\n"
               "                foreach (waNumbersRaw($s, true) as $x) { if ((string)$x['id'] === (string)($in['id'] ?? '') && (string)($x['access_token'] ?? '') !== '') $tok = (string)$x['access_token']; }\n"
               "            }\n", rel)
    s = rep(s, "            $warn = '';\n            if ($prov === 'meta') {\n",
               "            $warn = ''; $note128 = '';\n"
               "            $np = (string)($in['provider'] ?? '');   // v1.2.128: wa-campur — penyedia per nomor\n"
               "            if (!in_array($np, ['meta', 'waha'], true)) $np = waNumProv($row, $wa);\n"
               "            $row['provider'] = $np;\n"
               "            $same128 = ($np === $prov);\n"
               "            if ($np === 'meta') {\n", rel)
    s = rep(s, "                if ($pnid === (string)($wa['phone_number_id'] ?? '')) jsonOut(",
               "                if ($same128 && $pnid === (string)($wa['phone_number_id'] ?? '')) jsonOut(", rel)
    s = rep(s, "                    if ($i !== $idx && (string)($x['phone_number_id'] ?? '') === $pnid) jsonOut(",
               "                    if ($i !== $idx && waNumProv($x, $wa) === 'meta' && (string)($x['phone_number_id'] ?? '') === $pnid) jsonOut(", rel)
    s = rep(s, "                $useTok = (string)($row['access_token'] ?? '') !== '' ? (string)$row['access_token'] : (string)($wa['access_token'] ?? '');\n",
               "                $useTok = (string)($row['access_token'] ?? '') !== '' ? (string)$row['access_token'] : ($same128 ? (string)($wa['access_token'] ?? '') : '');\n"
               "                if ($useTok === '') jsonOut(['ok' => false, 'error' => 'Access Token wajib diisi — nomor utama tidak memakai Meta.'], 400);   // v1.2.128\n", rel)
    s = rep(s, "                if ($sess === wahaSession($wa)) jsonOut(",
               "                if ($prov === 'waha' && $sess === wahaSession($wa)) jsonOut(", rel)
    s = rep(s, "                    if ($i !== $idx && (string)($x['waha_session'] ?? '') === $sess) jsonOut(",
               "                    if ($i !== $idx && waNumProv($x, $wa) === 'waha' && (string)($x['waha_session'] ?? '') === $sess) jsonOut(", rel)
    s = rep(s, "                elseif ($key !== '' && strpos($key, '•') === false) $row['waha_api_key'] = $key;\n",
               "                elseif ($key !== '' && strpos($key, '•') === false) $row['waha_api_key'] = $key;\n"
               "                if (((string)$row['waha_url'] === '' && trim((string)($wa['waha_url'] ?? '')) === '')   // v1.2.128: wa-campur\n"
               "                    || ((string)($row['waha_api_key'] ?? '') === '' && (string)($wa['waha_api_key'] ?? '') === '')) {\n"
               "                    jsonOut(['ok' => false, 'error' => 'URL & API Key server WAHA wajib diisi untuk nomor ini.'], 400);\n"
               "                }\n", rel)
    s = rep(s, "            $s['wa_numbers'] = array_values($cur);\n            writeJson(SETTINGS_FILE, $s);\n",
               "            $s['wa_numbers'] = array_values($cur);\n"
               "            // v1.2.128: wa-campur — kunci webhook penyedia yang belum pernah dipakai nomor utama\n"
               "            if ($np === 'waha' && (string)($s['whatsapp_api']['waha_webhook_key'] ?? '') === '') $s['whatsapp_api']['waha_webhook_key'] = bin2hex(random_bytes(24));\n"
               "            if ($np === 'meta' && (string)($s['whatsapp_api']['verify_token'] ?? '') === '') $s['whatsapp_api']['verify_token'] = bin2hex(random_bytes(12));\n"
               "            if (!$same128) $note128 = ($np === 'meta')\n"
               "                ? 'Daftarkan webhook Meta untuk nomor ini: Callback URL & Verify Token ada di kartu WhatsApp Bot.'\n"
               "                : 'Sambungkan nomor ini lewat kartu Koneksi WhatsApp (scan QR).';\n"
               "            writeJson(SETTINGS_FILE, $s);\n", rel)
    s = rep(s, "            jsonOut(['ok' => true, 'id' => $row['id'], 'warning' => $warn]);\n",
               "            jsonOut(['ok' => true, 'id' => $row['id'], 'warning' => $warn, 'note' => $note128]);\n", rel)

    # ---- waha_conn: cek penyedia per nomor ----
    s = rep(s, "        if (($wa['provider'] ?? 'meta') !== 'waha') jsonOut(['ok' => false, 'error' => 'Penyedia WhatsApp bukan WAHA.'], 400);\n"
               "        $chId = preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['ch'] ?? ''));   // v1.2.98: multi-nomor\n"
               "        if ($chId !== '' && $chId !== 'utama') {\n"
               "            $wa = waChanConf($wa, $chId, $s);\n"
               "            if (($wa['_ch'] ?? '') !== $chId) jsonOut(['ok' => false, 'error' => 'Nomor tidak ditemukan atau terkunci (di luar paket).'], 404);   // v1.2.99\n"
               "        }\n",
               "        $chId = preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['ch'] ?? ''));   // v1.2.98: multi-nomor\n"
               "        if ($chId !== '' && $chId !== 'utama') {\n"
               "            $wa = waChanConf($wa, $chId, $s);\n"
               "            if (($wa['_ch'] ?? '') !== $chId) jsonOut(['ok' => false, 'error' => 'Nomor tidak ditemukan atau terkunci (di luar paket).'], 404);   // v1.2.99\n"
               "        }\n"
               "        if (($wa['provider'] ?? 'meta') !== 'waha') jsonOut(['ok' => false, 'error' => 'Nomor ini tidak memakai WAHA.'], 400);   // v1.2.128: wa-campur — cek per nomor\n", rel)
    return s

# ======================================================================
def f_js(s, rel):
    # webhook Meta tetap terlihat di kartu WhatsApp Bot bila ada nomor tambahan Meta
    s = rep(s, "    $$('.wa-waha-only').forEach(function (el)   { el.style.display = prov === 'waha' ? '' : 'none'; });\n  }\n",
               "    $$('.wa-waha-only').forEach(function (el)   { el.style.display = prov === 'waha' ? '' : 'none'; });\n"
               "    waMetaHookRows();   // v1.2.128: wa-campur\n  }\n"
               "  // v1.2.128: wa-campur — Callback URL, Verify Token & App Secret tetap tampil bila ada nomor tambahan Meta\n"
               "  function waMetaHookRows() {\n"
               "    if (typeof _wn === 'undefined' || !_wn || !_wn.hasMeta) return;\n"
               "    ['#wa_verify', '#wa_secret', '#wa_webhook_url'].forEach(function (id) { var el = $(id), r = el && el.closest('.wa-meta-only'); if (r) r.style.display = ''; });\n"
               "  }\n", rel)
    s = rep(s, "      $('#wn_save').onclick = wnSave;\n",
               "      $('#wn_save').onclick = wnSave;\n"
               "      $('#wn_prov').onchange = function () { wnFormProv(false); };   // v1.2.128: wa-campur\n", rel)
    # tabel nomor: penyedia per baris
    s = rep_between(s, "      var sa = role === 'super_admin', waha = r.provider === 'waha';\n",
        "        }).join('') + '</tbody></table></div>';\n",
        "      var sa = role === 'super_admin';\n"
        "      // v1.2.128: wa-campur — penyedia per nomor\n"
        "      _wn.hasMeta = _wn.rows.some(function (x) { return !x.locked && (x.provider || r.provider) === 'meta'; });\n"
        "      _wn.hasWaha = _wn.rows.some(function (x) { return !x.locked && (x.provider || r.provider) === 'waha'; });\n"
        "      _wn.mainWahaOk = !!r.main_waha_ok;\n"
        "      var mixed = _wn.hasMeta && _wn.hasWaha, waha = _wn.hasWaha;\n"
        "      var extra = _wn.rows.length - 1;\n"
        "      $('#wn_list').innerHTML = '<div class=\"tbl-wrap\"><table class=\"tbl\" style=\"width:100%\"><thead><tr><th>Label</th><th>Nomor</th><th>' + (mixed ? 'Penyedia · ID' : (waha ? 'Sesi WAHA' : 'Phone Number ID')) + '</th><th>Tim</th>' + (waha ? '<th>Kesehatan</th>' : '') + '<th></th></tr></thead><tbody>' +   // v1.2.100: routing; v1.2.104: kesehatan\n"
        "        _wn.rows.map(function (x) {\n"
        "          var xw = (x.provider || r.provider) === 'waha';\n"
        "          var idc = xw ? (x.waha_session || '') : (x.phone_number_id || (sa ? '' : '••••'));\n"
        "          var acts = '';\n"
        "          if (xw && x.id !== 'utama') acts += '<button class=\"btn ghost sm\" type=\"button\" data-wn=\"qr\" data-id=\"' + esc(x.id) + '\">Koneksi</button> ';\n"
        "          if (xw && !x.locked) acts += '<button class=\"btn ghost sm\" type=\"button\" data-wn=\"call\" data-id=\"' + esc(x.id) + '\" title=\"Tolak telepon otomatis\">Telepon</button> ';   // v1.2.108: tolak-telepon\n"
        "          if (sa) acts += '<button class=\"btn ghost sm\" type=\"button\" data-wn=\"edit\" data-id=\"' + esc(x.id) + '\">Ubah</button> ';\n"
        "          if (sa && !x.primary) acts += '<button class=\"btn ghost sm\" type=\"button\" data-wn=\"del\" data-id=\"' + esc(x.id) + '\">Hapus</button>';\n"
        "          return '<tr' + (x.locked ? ' style=\"opacity:.6\"' : '') + '><td>' + (x.primary ? '<span class=\"tag\" style=\"margin-right:4px\">Utama</span>' : '') + esc(x.label || (x.primary ? 'Nomor utama' : '')) +\n"
        "            (x.locked ? ' <span class=\"tag\" style=\"background:#fee2e2;color:#991b1b\" title=\"Di luar batas paket: nomor ini tidak menerima & tidak mengirim pesan\">Terkunci</span>' : '') + '</td>' +   // v1.2.99\n"
        "            '<td class=\"mono\">' + (x.number ? '+' + esc(x.number) : '<span style=\"color:var(--muted)\">—</span>') + (x.verified_name ? '<div class=\"help\" style=\"margin:0\">' + esc(x.verified_name) + '</div>' : '') + '</td>' +\n"
        "            '<td class=\"mono\" style=\"font-size:12px\">' + (mixed ? '<span class=\"tag\" style=\"margin-right:4px\">' + (xw ? 'WAHA' : 'Meta') + '</span>' : '') + esc(idc) + '</td><td style=\"font-size:12px\">' + (x.team ? esc(_tn[x.team] || x.team) : '<span style=\"color:var(--muted)\">Semua</span>') + '</td>' + (waha ? '<td>' + (x.locked || !xw ? '' : whBadge(_wh[x.id], x.id)) + '</td>' : '') + '<td style=\"white-space:nowrap;text-align:right\">' + acts + '</td></tr>';\n"
        "        }).join('') + '</tbody></table></div>';\n", rel)
    s = rep(s, "      foncChannels(r.channels || []);\n    });\n  }\n",
               "      foncChannels(r.channels || []);\n      waMetaHookRows();   // v1.2.128: wa-campur\n    });\n  }\n", rel)
    # form: pilihan penyedia
    s = rep(s, "    $$('#waNumsCard .wn-meta, #waNumsCard .wn-waha').forEach(function (el) { el.style.display = 'none'; });\n"
               "    if (!isPrim) $$(_wn.prov === 'waha' ? '#waNumsCard .wn-waha' : '#waNumsCard .wn-meta').forEach(function (el) { el.style.display = ''; });\n"
               "    $('#wn_label').focus();\n  }\n",
               "    _wn.editRow = row || null;   // v1.2.128: wa-campur — penyedia per nomor\n"
               "    $('#wn_prov_row').style.display = isPrim ? 'none' : '';\n"
               "    $('#wn_prov').value = (row && row.provider) || _wn.prov;\n"
               "    wnFormProv(isPrim);\n"
               "    $('#wn_label').focus();\n  }\n"
               "  function wnFormProv(isPrim) {   // v1.2.128: wa-campur\n"
               "    var p = $('#wn_prov').value, row = _wn.editRow, same = (p === _wn.prov);\n"
               "    $$('#waNumsCard .wn-meta, #waNumsCard .wn-waha').forEach(function (el) { el.style.display = 'none'; });\n"
               "    if (isPrim) return;\n"
               "    $$(p === 'waha' ? '#waNumsCard .wn-waha' : '#waNumsCard .wn-meta').forEach(function (el) { el.style.display = ''; });\n"
               "    $('#wn_token').placeholder = (row && row.token_is_set) ? '•••• (terisi — kosongkan untuk tidak mengubah)' : (same ? 'kosong = pakai token nomor utama' : 'wajib diisi');\n"
               "    $('#wn_waba').placeholder = same ? 'kosong = WABA nomor utama' : 'wajib untuk Blast template';\n"
               "    $('#wn_wurl').placeholder = same ? 'kosong = server nomor utama' : (_wn.mainWahaOk ? 'kosong = server WAHA yang tersimpan' : 'wajib diisi, mis. https://wa.domain.com');\n"
               "    $('#wn_wkey').placeholder = (row && row.waha_key_is_set) ? '•••• (terisi — kosongkan untuk tidak mengubah)' : (same ? 'kosong = API key nomor utama' : (_wn.mainWahaOk ? 'kosong = API key yang tersimpan' : 'wajib diisi'));\n"
               "    var n = $('#wn_meta_note');\n"
               "    if (n) n.innerHTML = same ? 'Nomor tambahan di WABA yang sama cukup diisi Phone Number ID — token &amp; webhook memakai milik nomor utama.'\n"
               "      : 'Nomor utama memakai WAHA, jadi isi Access Token (dan WABA ID untuk Blast) nomor ini. Daftarkan webhook di Meta App memakai Callback URL &amp; Verify Token di kartu <b>WhatsApp Bot</b>, lalu subscribe field <code>messages</code>.';\n"
               "  }\n", rel)
    s = rep(s, "      if (_wn.prov === 'waha') {\n        body.waha_session = $('#wn_sess').value.trim();",
               "      body.provider = $('#wn_prov').value;   // v1.2.128: wa-campur\n"
               "      if (body.provider === 'waha') {\n        body.waha_session = $('#wn_sess').value.trim();", rel)
    s = rep(s, "      toast(r.warning ? ('Tersimpan. ' + r.warning) : 'Nomor tersimpan.', !!r.warning);\n",
               "      toast(r.warning ? ('Tersimpan. ' + r.warning) : ('Nomor tersimpan.' + (r.note ? ' ' + r.note : '')), !!r.warning);   // v1.2.128\n", rel)
    s = rep(s, "        if (_wn.prov === 'waha' && !id && r.id) {",
               "        if (body.provider === 'waha' && !id && r.id) {", rel)
    s = rep(s, "(_wn.prov === 'waha' ? ' Sesi WAHA tidak dihapus dari server.' : '')",
               "((row.provider || _wn.prov) === 'waha' ? ' Sesi WAHA tidak dihapus dari server.' : '')", rel)
    s = rep(s, "{ op: 'meta_phones', waba_id: ", "{ op: 'meta_phones', id: $('#wn_id').value, waba_id: ", rel)
    # kartu Koneksi WhatsApp: hanya nomor WAHA; muncul walau nomor utama Meta
    s = rep(s, "    if (_wn.prov !== 'waha' || chs.length < 2) { sel.classList.add('hide'); if (_fonc.ch && _fonc.ch !== 'utama') { _fonc.ch = 'utama'; foncStatus(); } return; }\n"
               "    var cur = _fonc.ch || 'utama';\n",
               "    chs = (chs || []).filter(function (c) { return (c.prov || _wn.prov) === 'waha'; });   // v1.2.128: wa-campur — hanya nomor WAHA\n"
               "    if (_wn.prov !== 'waha') {\n"
               "      var card128 = $('#fonConnCard');\n"
               "      if (!chs.length) { sel.classList.add('hide'); return; }\n"
               "      if (!chs.some(function (c) { return c.id === _fonc.ch; })) _fonc.ch = chs[0].id;\n"
               "      if (card128 && card128.style.display === 'none') foncInit({ provider: 'waha', waha_url: '1', waha_api_key_is_set: true });\n"
               "    } else if (chs.length < 2) { sel.classList.add('hide'); if (_fonc.ch && _fonc.ch !== 'utama') { _fonc.ch = 'utama'; foncStatus(); } return; }\n"
               "    var cur = _fonc.ch || chs[0].id;\n", rel)
    s = rep(s, "    if (!chs.some(function (c) { return c.id === cur; })) cur = 'utama';\n",
               "    if (!chs.some(function (c) { return c.id === cur; })) cur = chs[0].id;\n", rel)
    # pindah nomor: peringatan jendela 24 jam sesuai penyedia nomor tujuan
    s = rep(s, "moveWaChan(num, this.value, this, res.wa_prov); };   // v1.2.116\n",
               "var tc128 = (res.channels || []).filter(function (c) { return c.id === this.value; }, this)[0]; moveWaChan(num, this.value, this, (tc128 && tc128.prov) || res.wa_prov); };   // v1.2.116; v1.2.128: wa-campur\n", rel)
    return s

# ======================================================================
def f_html(s, rel):
    s = rep(s, '<script src="app.js?v=1.2.126"></script><!-- v1.2.126: respon-median -->',
               '<script src="app.js?v=1.2.128"></script><!-- v1.2.128: wa-campur -->', rel)
    s = rep(s, "Nomor tambahan memakai penyedia yang sama dengan nomor utama.</div>",
               "Tiap nomor boleh memakai penyedia sendiri: Meta Cloud API resmi atau WAHA (scan QR).</div>", rel)
    s = rep(s, '          <div class="row"><label class="fl">Label</label><input type="text" id="wn_label"',
               '          <div class="row" id="wn_prov_row"><label class="fl">Penyedia nomor ini</label><select id="wn_prov"><option value="meta">Meta Cloud API — resmi</option><option value="waha">WAHA — scan QR, tidak resmi</option></select><div class="help">Boleh berbeda dari nomor utama, mis. nomor utama Meta resmi + nomor cabang WAHA. Chat lewat nomor Meta tetap mengikuti aturan jendela 24 jam; chat lewat nomor WAHA tidak.</div></div><!-- v1.2.128: wa-campur -->\n'
               '          <div class="row"><label class="fl">Label</label><input type="text" id="wn_label"', rel)
    s = rep(s, '              <div class="help">Nomor tambahan di WABA yang sama cukup diisi Phone Number ID — token &amp; webhook memakai milik nomor utama.</div></div>',
               '              <div class="help" id="wn_meta_note">Nomor tambahan di WABA yang sama cukup diisi Phone Number ID — token &amp; webhook memakai milik nomor utama.</div></div>', rel)
    return s

patch('api/index.php', f_api, 'v1.2.127: respon-kata')
patch('dashboard/chatbot-ai/app.js', f_js, 'v1.2.127: respon-kata')
patch('dashboard/chatbot-ai/index.html', f_html, 'v1.2.126: respon-median')
print('selesai')
