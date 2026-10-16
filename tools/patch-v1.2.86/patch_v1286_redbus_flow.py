#!/usr/bin/env python3
"""v1.2.86 — alur redBus + Tes Chatbot:
  - Tes Chatbot (pengguna dashboard yang login) tidak kena batas permintaan per IP.
  - "ke <kota dikenal>" dihitung niat cek rute walau tanpa kata harga/tiket.
  - Tanggal: "18 oktober", "18 okt", "18/10", jawaban angka saja ("28").
  - AI tidak menanyakan tanggal; jawaban yang menanyakan tanggal diganti link (tanggal bisa diubah di redBus).
  - Riwayat: 3 pesan pelanggan sebelumnya (duplikat pesan sekarang dilewati).
Idempoten. Pakai: patch_v1286_redbus_flow.py <api/index.php>"""
import re, sys, pathlib
P = pathlib.Path(sys.argv[1]); A = P.read_text(encoding='utf-8')
if 'v1.2.86:' in A: print('sudah terpasang'); sys.exit(0)
def rep(old, new, n=1):
    global A
    c = A.count(old)
    if c != n: raise SystemExit(f'ANCHOR {c}x: {old[:80]!r}')
    A = A.replace(old, new)
A = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.86');", A, count=1)

rep("""        $ip = clientIp();
        $limit = (int)($s['api']['rate_limit'] ?? 20);
        if (!checkRateLimit($ip, $limit)) {""", """        $ip = clientIp();
        $limit = (int)($s['api']['rate_limit'] ?? 20);
        // v1.2.86: Tes Chatbot dari dashboard (pengguna login) tidak dihitung batas per IP
        if (!getAuthenticatedUserSilent() && !checkRateLimit($ip, $limit)) {""")

rep('''        . "- Isi tanggal hanya bila pelanggan menyebut tanggal atau hari (hitung dari tanggal hari ini di atas); bila tidak, kosongkan: [[REDBUS:Jakarta|Purwokerto|]].\\n"''',
    '''        . "- Isi tanggal hanya bila pelanggan menyebut tanggal atau hari (hitung dari tanggal hari ini di atas); bila tidak, kosongkan: [[REDBUS:Jakarta|Purwokerto|]]. JANGAN menanyakan tanggal — begitu kota asal & tujuan jelas, langsung tulis tag (tanggal bisa diganti pelanggan di halaman redBus).\\n"''')

rep("""    $texts = [mb_strtolower((string)$message)];
    for ($i = count($history) - 1; $i >= 0 && count($texts) < 3; $i--) {
        if (($history[$i]['role'] ?? '') !== 'assistant') $texts[] = mb_strtolower((string)($history[$i]['content'] ?? ''));
    }""", """    $texts = [mb_strtolower((string)$message)];
    $skip = true;   // v1.2.86: riwayat Tes Chatbot sudah memuat pesan sekarang di akhir
    for ($i = count($history) - 1; $i >= 0 && count($texts) < 4; $i--) {
        if (($history[$i]['role'] ?? '') === 'assistant') { $skip = false; continue; }
        $h = mb_strtolower((string)($history[$i]['content'] ?? ''));
        if ($skip && trim($h) === trim($texts[0])) { $skip = false; continue; }
        $skip = false; $texts[] = $h;
    }""")

rep("""            elseif (preg_match('/\\b(?:tanggal|tgl)\\.?\\s*(\\d{1,2})\\b/u', $t, $m) && (int)$m[1] >= 1 && (int)$m[1] <= 31) {""",
"""            elseif (($dm = deiRedbusDayMonth($t, $ti === 0)) !== '') $date = $dm;   // v1.2.86
            elseif (preg_match('/\\b(?:tanggal|tgl)\\.?\\s*(\\d{1,2})\\b/u', $t, $m) && (int)$m[1] >= 1 && (int)$m[1] <= 31) {""")

rep("""            if ($to === null && preg_match('/\\b(ke|tujuan|menuju|to)\\s*$/u', $before)) $to = $city[0];""",
    """            if ($to === null && preg_match('/\\b(ke|tujuan|menuju|to)\\s*$/u', $before)) { $to = $city[0]; $intent = true; }   // v1.2.86: "ke <kota>" = niat cek rute""")

rep("""// v1.2.82: tebak rute dari pesan pelanggan""", """// v1.2.86: "18 oktober" / "18 okt" / "18/10" / angka saja (hanya pesan sekarang) -> Y-m-d (tahun ini, atau tahun depan bila sudah lewat)
function deiRedbusDayMonth($t, $allowBare = false) {
    $bln = ['jan' => 1, 'feb' => 2, 'mar' => 3, 'apr' => 4, 'mei' => 5, 'may' => 5, 'jun' => 6, 'jul' => 7, 'agu' => 8, 'agt' => 8, 'aug' => 8,
            'sep' => 9, 'okt' => 10, 'oct' => 10, 'nov' => 11, 'des' => 12, 'dec' => 12];
    $today = wibDate('Y-m-d'); $d = 0; $mo = 0;
    if (preg_match('/\\b(\\d{1,2})\\s*(jan|feb|mar|apr|mei|may|jun|jul|agu|agt|aug|sep|okt|oct|nov|des|dec)\\p{L}*/u', $t, $m)) { $d = (int)$m[1]; $mo = $bln[$m[2]]; }
    elseif (preg_match('/\\b(\\d{1,2})[\\/\\-.](\\d{1,2})\\b/', $t, $m)) { $d = (int)$m[1]; $mo = (int)$m[2]; }
    elseif ($allowBare && preg_match('/^\\s*(\\d{1,2})\\s*\\??\\s*$/', $t, $m)) {
        $d = (int)$m[1]; $mo = (int)substr($today, 5, 2);
        if (sprintf('%s-%02d', substr($today, 0, 7), $d) < $today) $mo = $mo % 12 + 1;
    }
    if ($d < 1 || $d > 31 || $mo < 1 || $mo > 12) return '';
    $y = (int)substr($today, 0, 4);
    if (sprintf('%04d-%02d-%02d', $y, $mo, $d) < $today) $y++;
    return checkdate($mo, $d, $y) ? sprintf('%04d-%02d-%02d', $y, $mo, $d) : '';
}
// v1.2.82: tebak rute dari pesan pelanggan""")

# jawaban yang menanyakan tanggal diperlakukan seperti penolakan (diganti link)
rep("""        $refuse = (bool)preg_match('/tidak (memiliki|punya|ada|tersedia)[^.\\n]{0,20}informasi|belum (memiliki|punya|ada) informasi|hubungi (tim|admin|cs|customer)/iu', (string)$answer);""",
    """        $refuse = (bool)preg_match('/tidak (memiliki|punya|ada|tersedia)[^.\\n]{0,20}informasi|belum (memiliki|punya|ada) informasi|hubungi (tim|admin|cs|customer)/iu', (string)$answer);
        $askDate = (bool)preg_match('/(tanggal|kapan|hari apa)[^?\\n]{0,40}\\?/iu', (string)$answer);   // v1.2.86""")
rep("""        if ($refuse) return 'Harga & kursi terbaru rute ' . $nm($g['from']) . ' – ' . $nm($g['to']) . ' bisa dicek langsung di redBus.' . "\\n\\n" . $line;""",
    """        if ($refuse || ($askDate && $g['date'] === '')) return 'Harga & kursi terbaru rute ' . $nm($g['from']) . ' – ' . $nm($g['to']) . ' bisa dicek langsung di redBus' . ($g['date'] === '' ? ' (tanggal keberangkatan bisa diganti di halaman itu)' : '') . '.' . "\\n\\n" . $line;
        $onlyDate = mb_strlen(trim((string)$message)) <= 20 && deiRedbusDayMonth(mb_strtolower((string)$message), true) !== '';   // balasan berupa tanggal saja
        if ($askDate || $onlyDate) return 'Harga & kursi terbaru rute ' . $nm($g['from']) . ' – ' . $nm($g['to']) . ' bisa dicek langsung di redBus.' . "\\n\\n" . $line;""")
P.write_text(A, encoding='utf-8'); print('OK v1.2.86 terpasang')
