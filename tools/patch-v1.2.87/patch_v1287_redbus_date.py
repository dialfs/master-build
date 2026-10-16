#!/usr/bin/env python3
"""v1.2.87 — redBus:
  - Tanpa tanggal: hari ini hanya sebelum jam batas (bawaan 15:00 WIB, 'cutoff_hour' di redbus),
    sesudahnya besok — malam hari bus hari ini sudah berangkat sehingga redBus tampak kosong.
  - Label ganda ("Cek harga & pesan tiket: Cek harga & pesan tiket:") dirapikan.
Idempoten. Pakai: patch_v1287_redbus_date.py <api/index.php>"""
import re, sys, pathlib
P = pathlib.Path(sys.argv[1]); A = P.read_text(encoding='utf-8')
if 'v1.2.87:' in A: print('sudah terpasang'); sys.exit(0)
def rep(old, new, n=1):
    global A
    c = A.count(old)
    if c != n: raise SystemExit(f'ANCHOR {c}x: {old[:80]!r}')
    A = A.replace(old, new)
A = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.87');", A, count=1)
rep(r"""    $d = (preg_match('/^\d{4}-\d{2}-\d{2}$/', (string)$date) && $date >= $today) ? $date : $today;""",
r"""    // v1.2.87: tanpa tanggal -> hari ini sebelum jam batas, sesudahnya besok
    $cut = (int)($c['cutoff_hour'] ?? 15);
    $def = ((int)wibDate('G') >= $cut) ? date('Y-m-d', strtotime($today . ' +1 day')) : $today;
    $d = (preg_match('/^\d{4}-\d{2}-\d{2}$/', (string)$date) && $date >= $today) ? $date : $def;""")
rep(r"""    return trim(preg_replace("/\n{3,}/", "\n\n", (string)$out));""",
r"""    if ($label !== '') $out = preg_replace('/(?:' . preg_quote($label, '/') . '\s*){2,}/u', $label . ' ', (string)$out);   // v1.2.87: label ganda
    return trim(preg_replace("/\n{3,}/", "\n\n", (string)$out));""")
P.write_text(A, encoding='utf-8'); print('OK v1.2.87 terpasang')
