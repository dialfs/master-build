#!/usr/bin/env python3
"""v1.2.81 — Link redBus otomatis (aktif hanya bila data/server.php punya kunci 'redbus').
  'redbus' => ['op_id' => '18107', 'cities' => ['Jakarta' => 193490, 'Purwokerto' => 194407, 'Jogja' => 'Yogyakarta', ...]]
  Nilai kota = ID redBus (angka) atau nama kota lain (alias). AI menulis tag
  [[REDBUS:asal|tujuan|YYYY-MM-DD]]; server mengganti tag dengan link. Tanpa kunci = tidak berubah.
Idempoten. Pakai: patch_v1281_redbus.py <api/index.php>"""
import re, sys, pathlib
P = pathlib.Path(sys.argv[1]); A = P.read_text(encoding='utf-8')
if 'function deiRedbusExpand(' in A: print('sudah terpasang'); sys.exit(0)
def rep(old, new, n=1):
    global A
    c = A.count(old)
    if c != n: raise SystemExit(f'ANCHOR {c}x: {old[:80]!r}')
    A = A.replace(old, new)
A = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.81');", A, count=1)

rep("function generateAnswer($s, $message, $history = []) {", r"""/* v1.2.81: LINK redBus otomatis — hanya instalasi yang mengisi 'redbus' di data/server.php. */
function deiRedbusConf() {
    $c = deiServerConf()['redbus'] ?? null;
    if (!is_array($c) || empty($c['cities']) || !is_array($c['cities'])) return null;
    return $c;
}
// Nama kota (atau alias) -> [nama resmi, id]. null bila tidak dikenal.
function deiRedbusCity($name) {
    $c = deiRedbusConf(); if (!$c) return null;
    $norm = function ($x) { return trim(preg_replace('/\s+/u', ' ', mb_strtolower((string)$x))); };
    $map = [];
    foreach ($c['cities'] as $k => $v) $map[$norm($k)] = [$k, $v];
    $key = $norm($name);
    for ($i = 0; $i < 3 && isset($map[$key]); $i++) {
        list($nm, $v) = $map[$key];
        if (is_int($v) || ctype_digit((string)$v)) return [$nm, (string)$v];
        $key = $norm($v);   // alias -> kota lain
    }
    return null;
}
function deiRedbusSlug($s) { return trim(preg_replace('/[^a-z0-9]+/', '-', strtolower($s)), '-'); }
function deiRedbusUrl($from, $to, $date = '') {
    $c = deiRedbusConf(); $f = deiRedbusCity($from); $t = deiRedbusCity($to);
    if (!$c || !$f || !$t || $f[1] === $t[1]) return '';
    $today = wibDate('Y-m-d');
    $d = (preg_match('/^\d{4}-\d{2}-\d{2}$/', (string)$date) && $date >= $today) ? $date : $today;
    $q = ['fromCityName' => $f[0], 'fromCityId' => $f[1], 'srcCountry' => 'Indonesia', 'fromCityType' => 'CITY',
          'toCityName' => $t[0], 'toCityId' => $t[1], 'destCountry' => 'Indonesia', 'toCityType' => 'CITY',
          'onward' => date('d-M-Y', strtotime($d . ' 12:00:00'))];
    if (!empty($c['op_id'])) $q['opId'] = (string)$c['op_id'];
    return 'https://www.redbus.id/tiket-bus/' . deiRedbusSlug($f[0]) . '-ke-' . deiRedbusSlug($t[0]) . '?' . http_build_query($q, '', '&', PHP_QUERY_RFC3986);
}
function deiRedbusPromptBlock() {
    $c = deiRedbusConf(); if (!$c) return '';
    $names = implode(', ', array_keys($c['cities']));
    return "=== LINK PEMESANAN TIKET (redBus) ===\n"
        . "Bila pelanggan menanyakan harga, ketersediaan kursi, atau ingin memesan tiket untuk suatu rute, "
        . "tulis di baris terakhir jawaban tag persis seperti ini: [[REDBUS:<kota asal>|<kota tujuan>|<tanggal YYYY-MM-DD>]].\n"
        . "- Isi tanggal hanya bila pelanggan menyebut tanggal atau hari (hitung dari tanggal hari ini di atas); bila tidak, kosongkan: [[REDBUS:Jakarta|Purwokerto|]].\n"
        . "- Kota yang dikenal: " . $names . ".\n"
        . "- Jangan menulis link redBus sendiri; sistem mengganti tag dengan link resmi. Bila kota asal/tujuan tidak ada di daftar atau belum jelas, jangan tulis tag dan tanyakan kotanya.";
}
// Ganti tag di jawaban AI dengan link; tag yang tidak bisa dibuat linknya dibuang.
function deiRedbusExpand($answer) {
    if (strpos((string)$answer, '[[REDBUS') === false) return $answer;
    $c = deiRedbusConf();
    $label = $c ? (string)($c['label'] ?? 'Cek harga & pesan tiket:') : '';
    $out = preg_replace_callback('/\[\[REDBUS:([^|\]]*)\|([^|\]]*)(?:\|([^\]]*))?\]\]/u', function ($m) use ($label) {
        $u = deiRedbusUrl(trim($m[1]), trim($m[2]), trim($m[3] ?? ''));
        if ($u === '') { error_log('redbus: kota tidak dikenal (' . $m[1] . ' -> ' . $m[2] . ')'); return ''; }
        return trim($label . ' ' . $u);
    }, (string)$answer);
    return trim(preg_replace("/\n{3,}/", "\n\n", (string)$out));
}

function generateAnswer($s, $message, $history = []) {""")
rep("""    $deiPriceBlk = pricelistPromptBlock();   // v1.2.22: '' kalau daftar harga kosong
""", """    $deiPriceBlk = pricelistPromptBlock();   // v1.2.22: '' kalau daftar harga kosong
    $deiRbBlk = deiRedbusPromptBlock();      // v1.2.81: hanya bila redbus aktif di server.php
    if ($deiRbBlk !== '') $deiPriceBlk = trim($deiPriceBlk . "\\n\\n" . $deiRbBlk);
""")
rep("""        list($ok, $answer, $usage) = callClaude($s, $sys, $messages);
        return [$ok, $answer, 0, $usage];""", """        list($ok, $answer, $usage) = callClaude($s, $sys, $messages);
        return [$ok, $ok ? deiRedbusExpand($answer) : $answer, 0, $usage];   // v1.2.81""")
rep("""        list($ok, $answer, $usage) = callClaude($s, $sys, $messages);
        return [$ok, $answer, $kbHitsUsed, $usage];""", """        list($ok, $answer, $usage) = callClaude($s, $sys, $messages);
        return [$ok, $ok ? deiRedbusExpand($answer) : $answer, $kbHitsUsed, $usage];   // v1.2.81""")
rep("""    list($ok, $answer, $usage) = callClaude($s, $systemBlocks, $messages);
    return [$ok, $answer, $kbHitsUsed, $usage];
}""", """    list($ok, $answer, $usage) = callClaude($s, $systemBlocks, $messages);
    return [$ok, $ok ? deiRedbusExpand($answer) : $answer, $kbHitsUsed, $usage];   // v1.2.81
}""")
P.write_text(A, encoding='utf-8'); print('OK v1.2.81 terpasang')
