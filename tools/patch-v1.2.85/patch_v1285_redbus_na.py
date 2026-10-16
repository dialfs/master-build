#!/usr/bin/env python3
"""v1.2.85 — jawaban AI "tidak memiliki informasi harga tiket ke <Kota>":
  kota di luar tabel -> "rute ke <Kota> belum tersedia di <operator>" + contoh kota tujuan;
  kota di tabel -> diproses cadangan biasa (link / tanya kota asal).
Idempoten. Pakai: patch_v1285_redbus_na.py <api/index.php>"""
import re, sys, pathlib
P = pathlib.Path(sys.argv[1]); A = P.read_text(encoding='utf-8')
if 'v1.2.85: penolakan' in A: print('sudah terpasang'); sys.exit(0)
def rep(old, new, n=1):
    global A
    c = A.count(old)
    if c != n: raise SystemExit(f'ANCHOR {c}x: {old[:80]!r}')
    A = A.replace(old, new)
A = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.85');", A, count=1)
rep("""    return deiRedbusExpandCore($answer, $message, $history);
}""", """    // v1.2.85: penolakan AI soal harga/tiket ke kota di luar tabel -> kabar "belum tersedia" + contoh tujuan
    if (strpos((string)$answer, '[[REDBUS') === false
        && preg_match('/tidak (memiliki|punya|ada|tersedia)[^.\\n]{0,20}informasi|belum (memiliki|punya|ada) informasi/iu', (string)$answer)
        && preg_match('/(?:harga|tiket|rute|tarif)[^.\\n]{0,40}?\\bke\\s+(\\p{Lu}[\\p{L}]+(?:\\s\\p{Lu}[\\p{L}]+)?)/u', (string)$answer, $km)
        && !deiRedbusCity($km[1])
        && !(($gg = deiRedbusGuess($message, $history)) && $gg['to'] !== null)) {   // pesan pelanggan sudah berisi rute dikenal -> cadangan biasa
        $c = deiRedbusConf(); $op = trim((string)($c['operator'] ?? ''));
        $ex = [];
        foreach ($c['cities'] as $k => $v) { if (is_int($v) || ctype_digit((string)$v)) $ex[] = trim(preg_replace('/\\s*\\(.*?\\)/', '', $k)); if (count($ex) >= 8) break; }
        return 'Mohon maaf, rute ke ' . $km[1] . ' belum tersedia' . ($op !== '' ? ' di ' . $op : '') . '. '
            . 'Kota yang tersedia antara lain ' . implode(', ', $ex) . '. Mau cek rute yang mana?';
    }
    return deiRedbusExpandCore($answer, $message, $history);
}""")
P.write_text(A, encoding='utf-8'); print('OK v1.2.85 terpasang')
