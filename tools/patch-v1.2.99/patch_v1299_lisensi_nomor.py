#!/usr/bin/env python3
"""v1.2.99 — Lisensi nomor WhatsApp tambahan (tenant).
Jumlah nomor tambahan (v1.2.98 multi-nomor) kini dibatasi paket dari pusat: fitur `max_wa_numbers`
(dikirim pusat lewat cap_info / header X-Dei-Features, disimpan di cap-cache — tidak bisa ditembus dengan
mengedit settings.json). Bawaan 0 = tanpa nomor tambahan. Bila paket diturunkan, nomor yang TERAKHIR
ditambahkan terkunci lebih dulu: tidak menerima/mengirim (pesan masuk ke nomor terkunci diabaikan, bukan
dibalas dari nomor lain). Pemakaian dilaporkan ke pusat (stats.seats.wa_numbers / max_wa_numbers).
Pemakaian: python3 patch_v1299_lisensi_nomor.py <root dei-tenant>   (idempoten; backup *.bak-v1299-*)
Butuh v1.2.98."""
import sys, os, time, shutil
TEN = sys.argv[1]
STAMP = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.99: lisensi-nomor'

def patch(root, rel, pairs):
    p = os.path.join(root, rel)
    s = open(p, encoding='utf-8').read()
    if MARK in s: print('sudah dipatch:', rel); return
    if 'v1.2.98: multi-nomor' not in s: sys.exit('GAGAL: v1.2.98 belum terpasang di ' + rel)
    for old, new in pairs:
        n = s.count(old)
        if n != 1: sys.exit(f'GAGAL {rel}: anchor {n}x:\n{old[:300]}')
        s = s.replace(old, new)
    shutil.copy2(p, p + '.bak-v1299-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

php = [
    ("define('DEI_VERSION', 'v1.2.98');", "define('DEI_VERSION', 'v1.2.99');"),
    ("if (!defined('WA_NUMBERS_MAX')) define('WA_NUMBERS_MAX', 9);\n"
     "function waNumbersRaw($s = null) {\n"
     "    if ($s === null) $s = getSettings();\n"
     "    $l = $s['wa_numbers'] ?? [];\n"
     "    if (!is_array($l)) return [];\n"
     "    $out = [];\n"
     "    foreach ($l as $x) { if (is_array($x) && !empty($x['id'])) $out[] = $x; }\n"
     "    return $out;\n}\n",
     "if (!defined('WA_NUMBERS_MAX')) define('WA_NUMBERS_MAX', 20);   // v1.2.99: lisensi-nomor (batas teknis; batas paket dari pusat)\n"
     "if (!defined('DEI_DEFAULT_MAX_WA_NUMBERS')) define('DEI_DEFAULT_MAX_WA_NUMBERS', 0);\n"
     "// v1.2.99: lisensi-nomor — jumlah nomor tambahan yang diizinkan paket (fitur pusat max_wa_numbers).\n"
     "function waNumbersLimit() {\n"
     "    $f = [];\n"
     "    try { $f = deiFeatures(); } catch (\\Throwable $e) { error_log('waNumbersLimit: ' . $e->getMessage()); }\n"
     "    return max(0, min(WA_NUMBERS_MAX, (int)($f['max_wa_numbers'] ?? DEI_DEFAULT_MAX_WA_NUMBERS)));\n"
     "}\n"
     "// $all = false: hanya nomor yang masuk paket (urutan penambahan; yang terakhir terkunci lebih dulu).\n"
     "function waNumbersRaw($s = null, $all = false) {\n"
     "    if ($s === null) $s = getSettings();\n"
     "    $l = $s['wa_numbers'] ?? [];\n"
     "    if (!is_array($l)) return [];\n"
     "    $out = [];\n"
     "    foreach ($l as $x) { if (is_array($x) && !empty($x['id'])) $out[] = $x; }\n"
     "    if (!$all && $out) $out = array_slice($out, 0, waNumbersLimit());\n"
     "    return $out;\n}\n"),
    ("function waChanFromMeta($wa, $meta) {\n"
     "    if (!waMultiOn($wa)) return $wa;\n"
     "    $meta = is_array($meta) ? $meta : [];\n"
     "    if (!empty($meta['_dei_ch'])) return waChanConf($wa, (string)$meta['_dei_ch']);\n"
     "    $pid = (string)($meta['phone_number_id'] ?? '');\n"
     "    if ($pid !== '' && ($wa['provider'] ?? 'meta') === 'meta') {\n"
     "        foreach (waNumbersRaw() as $x) {\n"
     "            if ((string)($x['phone_number_id'] ?? '') === $pid) return waChanConf($wa, (string)$x['id']);\n"
     "        }\n"
     "    }\n"
     "    return waChanConf($wa, 'utama');\n}\n",
     "// v1.2.99: lisensi-nomor — null = nomor tambahan di luar paket (pesan diabaikan, tidak dibalas dari nomor lain).\n"
     "function waChanFromMeta($wa, $meta) {\n"
     "    $meta = is_array($meta) ? $meta : [];\n"
     "    $pid = (string)($meta['phone_number_id'] ?? '');\n"
     "    if ($pid !== '' && ($wa['provider'] ?? 'meta') === 'meta' && $pid !== (string)($wa['phone_number_id'] ?? '')) {\n"
     "        $act = [];\n"
     "        foreach (waNumbersRaw() as $x) $act[(string)$x['id']] = true;\n"
     "        foreach (waNumbersRaw(null, true) as $x) {\n"
     "            if ((string)($x['phone_number_id'] ?? '') !== $pid) continue;\n"
     "            return isset($act[(string)$x['id']]) ? waChanConf($wa, (string)$x['id']) : null;\n"
     "        }\n"
     "    }\n"
     "    if (!waMultiOn($wa)) return $wa;\n"
     "    if (!empty($meta['_dei_ch'])) return waChanConf($wa, (string)$meta['_dei_ch']);\n"
     "    return waChanConf($wa, 'utama');\n}\n"),
    ("            $wa = waChanFromMeta($waBase, $change['value']['metadata'] ?? []);   // v1.2.98: multi-nomor\n",
     "            $wa = waChanFromMeta($waBase, $change['value']['metadata'] ?? []);   // v1.2.98: multi-nomor\n"
     "            if ($wa === null) {   // v1.2.99: lisensi-nomor\n"
     "                error_log('wa: pesan ke nomor tambahan di luar paket diabaikan (' . mb_substr((string)($change['value']['metadata']['phone_number_id'] ?? ''), 0, 30) . ')');\n"
     "                $wa = $waBase; continue;\n"
     "            }\n"),
    # fitur dari pusat
    ("        'topic_scan_quota' => max(0, (int)($cap['topic_scan_quota'] ?? DEI_DEFAULT_TOPIC_SCANS)),   // v1.2.68\n",
     "        'topic_scan_quota' => max(0, (int)($cap['topic_scan_quota'] ?? DEI_DEFAULT_TOPIC_SCANS)),   // v1.2.68\n"
     "        'max_wa_numbers'  => max(0, (int)($cap['max_wa_numbers'] ?? DEI_DEFAULT_MAX_WA_NUMBERS)),   // v1.2.99: lisensi-nomor\n"),
    ("          'white_label' => false, 'topic_scan_quota' => DEI_DEFAULT_TOPIC_SCANS, 'source' => 'default'];\n",
     "          'white_label' => false, 'topic_scan_quota' => DEI_DEFAULT_TOPIC_SCANS, 'source' => 'default',\n"
     "          'max_wa_numbers' => DEI_DEFAULT_MAX_WA_NUMBERS];   // v1.2.99: lisensi-nomor\n"),
    # laporan pemakaian ke pusat (baca cache saja — tanpa deiFeatures)
    ("    return ['agents' => $ag, 'supervisors' => $sp,\n"
     "            'max_agents' => (int)$f['max_agents'], 'max_supervisors' => (int)$f['max_supervisors'],\n",
     "    $wn = 0;   // v1.2.99: lisensi-nomor\n"
     "    try { $wn = count(waNumbersRaw(getSettings(), true)); } catch (\\Throwable $e) {}\n"
     "    return ['agents' => $ag, 'supervisors' => $sp,\n"
     "            'wa_numbers' => $wn, 'max_wa_numbers' => (int)($f['max_wa_numbers'] ?? DEI_DEFAULT_MAX_WA_NUMBERS),   // v1.2.99\n"
     "            'max_agents' => (int)$f['max_agents'], 'max_supervisors' => (int)$f['max_supervisors'],\n"),
    # endpoint wa_numbers
    ("            if (waMultiProv($wa)) {\n                foreach (waNumbersRaw($s) as $x) {\n"
     "                    $r = ['id' => (string)$x['id'], 'primary' => false, 'label' => (string)($x['label'] ?? ''),\n",
     "            $lim = waNumbersLimit(); $ord = 0;   // v1.2.99: lisensi-nomor\n"
     "            if (waMultiProv($wa)) {\n                foreach (waNumbersRaw($s, true) as $x) {\n"
     "                    $r = ['id' => (string)$x['id'], 'primary' => false, 'label' => (string)($x['label'] ?? ''), 'locked' => (++$ord > $lim),\n"),
    ("            jsonOut(['ok' => true, 'provider' => $prov, 'supported' => waMultiProv($wa), 'max' => WA_NUMBERS_MAX,\n",
     "            jsonOut(['ok' => true, 'provider' => $prov, 'supported' => waMultiProv($wa), 'max' => WA_NUMBERS_MAX,\n"
     "                     'limit' => $lim, 'vendor' => deiBrandVendor(),   // v1.2.99: lisensi-nomor\n"),
    ("            foreach (waNumbersRaw($s) as $x) $used[(string)($x['phone_number_id'] ?? '')] = (string)$x['id'];\n",
     "            foreach (waNumbersRaw($s, true) as $x) $used[(string)($x['phone_number_id'] ?? '')] = (string)$x['id'];\n"),
    ("            $list = waNumbersRaw($s);\n            $idx = -1;\n",
     "            $list = waNumbersRaw($s, true);   // v1.2.99: termasuk yang terkunci\n            $idx = -1;\n"),
    ("            if ($idx < 0 && count($list) >= WA_NUMBERS_MAX) jsonOut(['ok' => false, 'error' => 'Maksimal ' . WA_NUMBERS_MAX . ' nomor tambahan.'], 400);\n",
     "            if ($idx < 0) {   // v1.2.99: lisensi-nomor — cek paket dari pusat\n"
     "                $lim = waNumbersLimit();\n"
     "                if (count($list) >= $lim) jsonOut(['ok' => false, 'error' => $lim > 0\n"
     "                    ? 'Batas paket: maksimal ' . $lim . ' nomor tambahan. Hubungi ' . deiBrandVendor() . ' untuk menambah.'\n"
     "                    : 'Paket Anda belum termasuk nomor WhatsApp tambahan. Hubungi ' . deiBrandVendor() . ' untuk menambahkan.'], 403);\n"
     "            }\n"),
    ("        if ($chId !== '' && $chId !== 'utama') {\n"
     "            $wa = waChanConf($wa, $chId, $s);\n"
     "            if (($wa['_ch'] ?? '') !== $chId) jsonOut(['ok' => false, 'error' => 'Nomor tidak ditemukan.'], 404);\n",
     "        if ($chId !== '' && $chId !== 'utama') {\n"
     "            $wa = waChanConf($wa, $chId, $s);\n"
     "            if (($wa['_ch'] ?? '') !== $chId) jsonOut(['ok' => false, 'error' => 'Nomor tidak ditemukan atau terkunci (di luar paket).'], 404);   // v1.2.99\n"),
]
patch(TEN, 'api/index.php', php)

patch(TEN, 'dashboard/chatbot-ai/index.html', [
    ('<script src="app.js?v=1.2.98"></script><!-- v1.2.98: multi-nomor -->',
     '<script src="app.js?v=1.2.99"></script><!-- v1.2.99: lisensi-nomor -->'),
])

js = [
    ("      _wn.rows = r.numbers || []; _wn.max = r.max || 9;\n",
     "      _wn.rows = r.numbers || []; _wn.max = (r.limit != null) ? r.limit : (r.max || 0);   // v1.2.99: lisensi-nomor (batas paket)\n"),
    ("      return '<tr><td>' + (x.primary ? '<span class=\"tag\" style=\"margin-right:4px\">Utama</span>' : '') + esc(x.label || (x.primary ? 'Nomor utama' : '')) + '</td>' +\n",
     "      return '<tr' + (x.locked ? ' style=\"opacity:.6\"' : '') + '><td>' + (x.primary ? '<span class=\"tag\" style=\"margin-right:4px\">Utama</span>' : '') + esc(x.label || (x.primary ? 'Nomor utama' : '')) +\n"
     "            (x.locked ? ' <span class=\"tag\" style=\"background:#fee2e2;color:#991b1b\" title=\"Di luar batas paket: nomor ini tidak menerima & tidak mengirim pesan\">Terkunci</span>' : '') + '</td>' +   // v1.2.99\n"),
    ("      $('#wn_add').disabled = extra >= _wn.max;\n"
     "      $('#wn_hint').textContent = extra > 0 ? (extra + ' nomor tambahan (maks ' + _wn.max + ')') : 'Belum ada nomor tambahan.';\n",
     "      $('#wn_add').disabled = extra >= _wn.max;   // v1.2.99: lisensi-nomor\n"
     "      var vend = r.vendor || 'tim kami';\n"
     "      $('#wn_hint').innerHTML = (_wn.max > 0\n"
     "        ? 'Paket: ' + extra + ' / ' + _wn.max + ' nomor tambahan terpakai.' + (extra > _wn.max ? ' <b style=\"color:#b91c1c\">' + (extra - _wn.max) + ' nomor terkunci.</b>' : (extra >= _wn.max ? ' Hubungi ' + esc(vend) + ' untuk menambah.' : ''))\n"
     "        : 'Paket Anda belum termasuk nomor tambahan. Hubungi ' + esc(vend) + ' untuk menambahkan.' + (extra > 0 ? ' <b style=\"color:#b91c1c\">' + extra + ' nomor terkunci.</b>' : ''))\n"
     "        + ' <a href=\"#\" id=\"wn_sync\">Sinkron ulang</a>';\n"
     "      $('#wn_sync').onclick = function (e) { e.preventDefault(); api('refresh_seats', { method: 'POST', body: {} }).then(function () { wnLoad(); toast('Paket disinkronkan.'); }); };\n"),
]
patch(TEN, 'dashboard/chatbot-ai/app.js', js)
print('selesai')
