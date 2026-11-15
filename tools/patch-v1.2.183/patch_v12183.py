#!/usr/bin/env python3
"""v1.2.183 (foto-otomatis-cocok): pencocokan jawaban -> entri foto_auto (v1.2.182) dilonggarkan untuk jawaban ringkas/parafrase.
- Angka uang dinormalkan (Rp 350.000 / Rp350 rb / 99 ribu -> 350000 / 99000), bobot 3; huruf & angka dipisah (rp99 -> rp, 99).
- Akhiran -nya/-kah/-lah/-pun dibuang, kata fungsi umum diabaikan.
- Cocok bila bobot cocok >= 3 dan >= 15% bobot kata khas entri (sebelumnya >= 4 kata & >= 40%).
Uji: bonus / harga ("Rp350 rb jadi Rp99 rb") / cara beli ringkas -> foto; sapaan, isi materi, hanya link, produk lain -> tanpa foto.
Idempoten.  Pakai: patch_v12183.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil, re
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
API = H + '/dei-tenant/api/index.php'
TAG = 'v1.2.183: foto-otomatis-cocok'; NEED = 'v1.2.182: foto-otomatis-pasti'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
NEWFN = "function deiKbTok($s) {\n    $s = mb_strtolower(preg_replace('~https?://\\S+~u', ' ', (string)$s));\n    $s = preg_replace('/(\\d+)[.,](\\d{3})(?:[.,](\\d{3}))?/', '$1$2$3', $s);\n    $s = preg_replace_callback('/(\\d+)\\s*(rb|ribu|k|jt|juta)\\b/u', function ($m) { return $m[1] . (in_array($m[2], ['jt', 'juta'], true) ? '000000' : '000'); }, $s);\n    $s = preg_replace('/(?<=\\p{L})(?=\\d)|(?<=\\d)(?=\\p{L})/u', ' ', $s);\n    $w = preg_split('/[^\\p{L}\\p{N}]+/u', $s, -1, PREG_SPLIT_NO_EMPTY);\n    static $stop = null;\n    if ($stop === null) $stop = array_flip(['dari','untuk','dengan','yang','akan','dalam','anda','kakak','lalu','juga','bisa','saja','sudah','hanya','atau','tidak','ini','itu','pada','oleh','agar','supaya','sampai','hingga','bahkan','tapi','tetapi','karena','jika','kalau','saya','kami','kita','mereka','silakan','silahkan','sini','disini','tersedia','adalah','ada','cara','buat','bagi','lebih','sangat','semua','setiap','sekali','aja','dapat','dapatkan','mendapatkan','halo','terima','kasih','mohon','maaf','baik','boleh','mau','ingin']);\n    $o = [];\n    foreach ((array)$w as $t) {\n        if (ctype_digit($t)) { if (strlen($t) >= 2) $o[$t] = 3; continue; }\n        if (mb_strlen($t) > 6) $t = preg_replace('/(nya|kah|lah|pun)$/u', '', $t);\n        if (mb_strlen($t) >= 4 && !isset($stop[$t])) $o[$t] = 1;\n    }\n    return $o;\n}\nfunction deiKbFotoAutoMatch($kb, $answer) {\n    $kb = array_values(array_filter((array)$kb, function ($e) { return is_array($e) && trim((string)($e['content'] ?? '')) !== ''; }));\n    $n = count($kb); if (!$n || trim((string)$answer) === '') return [];\n    $df = []; $toks = [];\n    foreach ($kb as $i => $e) { $toks[$i] = deiKbTok($e['content']); foreach ($toks[$i] as $t => $_) $df[$t] = ($df[$t] ?? 0) + 1; }\n    $lim = max(2, (int)ceil($n * 0.3));\n    $ans = deiKbTok($answer); $hit = [];\n    foreach ($kb as $i => $e) {\n        if (empty($e['foto_auto']) || empty($e['id']) || !deiKbFotoClean($e['images'] ?? [])) continue;\n        $tot = 0; $m = 0;\n        foreach ($toks[$i] as $t => $w) { if ($df[$t] > $lim) continue; $tot += $w; if (isset($ans[$t])) $m += $w; }\n        if ($tot < 3) continue;\n        if ($m >= 3 && $m / $tot >= 0.15) $hit[(string)$e['id']] = $m / $tot;\n    }\n    arsort($hit);\n    return array_slice(array_keys($hit), 0, 2);\n}\n"
s = open(API, encoding='utf-8').read()
if TAG in s: print('sudah:', API); sys.exit(0)
assert NEED in s, 'butuh v1.2.182'
a = s.index('function deiKbTok($s) {'); b = s.index('function deiKbRev() {')
assert a < b and s[a:b].count('function deiKbFotoAutoMatch(') == 1, 'blok fungsi tidak dikenali'
s = s[:a] + '// ' + TAG + ' — normalisasi angka, akhiran, kata fungsi; ambang 3 bobot & 15%\n' + NEWFN + s[b:]
old = "define('DEI_VERSION', 'v1.2.182');   //"
assert s.count(old) == 1, 'versi'
s = s.replace(old, "define('DEI_VERSION', 'v1.2.183');   // " + TAG + " — foto Kirim otomatis cocok juga untuk jawaban ringkas; v1.2.182:")
if not NOBAK: shutil.copy2(API, API + '.bak-v12183-' + stamp)
open(API, 'w', encoding='utf-8').write(s); print('OK', API)
