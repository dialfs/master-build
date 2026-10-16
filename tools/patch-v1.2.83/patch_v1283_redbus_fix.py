#!/usr/bin/env python3
"""v1.2.83 — perbaikan cadangan redBus v1.2.82:
  1. Toleransi salah ketik diperketat: huruf pertama sama, jarak 1 (jarak 2 hanya kata >=9 huruf).
     Sebelumnya "malang" terbaca "magelang".
  2. Link cadangan tidak ditempel bila AI sudah menyatakan rute tidak tersedia, dan hanya ditempel
     ke jawaban biasa bila jawaban menyebut kota tujuan itu.
Idempoten. Pakai: patch_v1283_redbus_fix.py <api/index.php>"""
import re, sys, pathlib
P = pathlib.Path(sys.argv[1]); A = P.read_text(encoding='utf-8')
if 'v1.2.83: salah ketik' in A: print('sudah terpasang'); sys.exit(0)
def rep(old, new, n=1):
    global A
    c = A.count(old)
    if c != n: raise SystemExit(f'ANCHOR {c}x: {old[:80]!r}')
    A = A.replace(old, new)
A = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.83');", A, count=1)
rep("""            foreach ($single as $n) { if (abs(strlen($n) - strlen($x)) <= 2 && levenshtein($x, $n) <= (strlen($n) >= 8 ? 2 : 1)) return $n; }""",
"""            // v1.2.83: salah ketik — huruf pertama sama, jarak 1 (2 hanya bila >=9 huruf); "malang" bukan "magelang"
            foreach ($single as $n) { if ($n[0] === $x[0] && abs(strlen($n) - strlen($x)) <= 1 && levenshtein($x, $n) <= (strlen($n) >= 9 ? 2 : 1)) return $n; }""")
rep("""        $u = deiRedbusUrl($g['from'], $g['to'], $g['date']);
        if ($u === '') return $answer;""", """        // v1.2.83: AI sudah bilang rute tidak tersedia -> jangan tempel link
        if (preg_match('/(belum|tidak) (tersedia|bisa dicek|dapat dicek|melayani)|tidak ada di daftar/iu', (string)$answer)) return $answer;
        $u = deiRedbusUrl($g['from'], $g['to'], $g['date']);
        if ($u === '') return $answer;""")
rep("""        return rtrim((string)$answer) . "\\n\\n" . $line;""", """        $toNm = mb_strtolower(trim(preg_replace('/\\s*\\(.*?\\)/', '', $g['to'])));
        if (mb_strpos(mb_strtolower((string)$answer), $toNm) === false) return $answer;   // v1.2.83: jawaban bukan soal rute ini
        return rtrim((string)$answer) . "\\n\\n" . $line;""")
rep("""        if (!preg_match_all($rx, $t, $mm, PREG_OFFSET_CAPTURE)) continue;""", """        // v1.2.83: "ke <kota di luar tabel>" -> tujuan tidak dikenal, biarkan jawaban AI
        if (preg_match_all('/\\b(?:ke|tujuan|menuju)\\s+(\\p{L}{3,})/u', $t, $km)) {
            foreach ($km[1] as $w) { if (!deiRedbusCity($w) && !in_array($w, ['mana', 'sana', 'sini', 'kota', 'arah', 'luar', 'dalam'], true)) $unknown = true; }
        }
        if (!preg_match_all($rx, $t, $mm, PREG_OFFSET_CAPTURE)) continue;""")
rep("""    $intent = false; $to = null;""", """    $unknown = false; $intent = false; $to = null;""")
rep("""    if ($from !== null && $to === null && count($seen) <= 1) {""", """    if ($unknown && $to === null) return ['from' => $from, 'to' => null, 'date' => $date, 'intent' => $intent];   // v1.2.83
    if ($from !== null && $to === null && count($seen) <= 1) {""")
P.write_text(A, encoding='utf-8'); print('OK v1.2.83 terpasang')
