// v1.2.171: produk-varian — varian harga {name, price} per produk (maks 30)
function prVarClean($v) {
    $out = [];
    if (!is_array($v)) return $out;
    foreach ($v as $r) {
        if (!is_array($r)) continue;
        $n = mb_substr(trim((string)($r['name'] ?? '')), 0, 100);
        $p = mb_substr(trim((string)($r['price'] ?? '')), 0, 100);
        if ($n === '' && $p === '') continue;
        $out[] = ['name' => $n, 'price' => $p];
        if (count($out) >= 30) break;
    }
    return $out;
}
// v1.2.171: teks dinormalkan (huruf kecil, tanda baca jadi spasi, diapit spasi) untuk pencocokan nama produk
function prNorm($t) {
    $t = mb_strtolower((string)$t, 'UTF-8');
    $t = preg_replace('/[^\p{L}\p{N}]+/u', ' ', $t);
    return ' ' . trim(preg_replace('/\s+/', ' ', $t)) . ' ';
}
// v1.2.171: skor kecocokan produk dengan pesan sekarang ($now) & pesan pelanggan sebelumnya ($old)
function prMatchScore($it, $now, $old) {
    static $stop = ['produk'=>1,'paket'=>1,'harga'=>1,'layanan'=>1,'item'=>1,'jasa'=>1,'dan'=>1,'yang'=>1,'untuk'=>1,'dengan'=>1,'atau'=>1,'per'=>1,'the'=>1,'and'=>1];
    $nama = prNorm($it['item'] ?? '');
    if (trim($nama) === '') return 0;
    $sc = 0;
    if (mb_strlen(trim($nama)) >= 3) {
        if (strpos($now, $nama) !== false) $sc += 20;
        elseif (strpos($old, $nama) !== false) $sc += 8;
    }
    foreach (array_unique(explode(' ', trim($nama))) as $w) {
        $num = ctype_digit($w);
        if ((!$num && mb_strlen($w) < 3) || ($num && strlen($w) < 2) || isset($stop[$w])) continue;
        if (strpos($now, ' ' . $w . ' ') !== false) $sc += 3;
        elseif (strpos($old, ' ' . $w . ' ') !== false) $sc += 2;
    }
    foreach (prVarClean($it['variants'] ?? []) as $v) {
        $vn = prNorm($v['name']);
        if (mb_strlen(trim($vn)) >= 3 && strpos($now, $vn) !== false) $sc += 2;
    }
    return $sc;
}

// Susun blok instruksi + daftar produk & harga untuk dikirim ke model.
// Return '' kalau daftar kosong — jangan kirim blok kosong.
// v1.2.171: produk punya varian & detail. Bila total detail besar (> 6000 karakter),
// hanya detail maks 5 produk yang paling cocok dengan pesan pelanggan yang dikirim;
// nama + harga semua produk tetap dikirim.
function pricelistPromptBlock($unit = null, $msg = '', $history = []) {   // v1.2.167: unit-bisnis
    $pl = pricelistGet();
    $its = [];
    foreach ($pl['items'] as $it) {
        if (!is_array($it)) continue;
        $iu = (string)($it['unit'] ?? '');   // v1.2.167: item ber-unit hanya untuk unit itu
        if ($iu !== '' && $unit && (string)$unit['id'] !== $iu) continue;   // tanpa unit = semua harga (perilaku lama)
        $nama = trim((string)($it['item'] ?? ''));
        if ($nama === '') continue;
        $var = prVarClean($it['variants'] ?? []);
        $adaHarga = trim((string)($it['price'] ?? '')) !== '';
        foreach ($var as $v) if ($v['price'] !== '') $adaHarga = true;
        $det = trim((string)($it['note'] ?? ''));
        if (!$adaHarga && $det === '') continue;   // baris tanpa harga & tanpa detail tidak dipakai (perilaku lama)
        $it['_var'] = $var; $it['_det'] = $det;
        $its[] = $it;
    }
    if (!$its) return '';

    $detTot = 0;
    foreach ($its as $it) $detTot += mb_strlen($it['_det']);
    $semua = $detTot <= 6000;
    $pilih = [];
    if (!$semua) {
        $now = prNorm($msg); $old = '';
        foreach (array_slice(is_array($history) ? $history : [], -6) as $h) {
            if (is_array($h) && ($h['role'] ?? '') !== 'assistant') $old .= prNorm($h['content'] ?? '');
        }
        $sc = [];
        foreach ($its as $i => $it) { $x = prMatchScore($it, $now, $old); if ($x >= 3) $sc[$i] = $x; }
        arsort($sc);
        $pilih = array_slice(array_keys($sc), 0, 5);
    }

    $rows = ''; $sembunyi = false;
    foreach ($its as $i => $it) {
        $nama = trim((string)$it['item']);
        $harga = trim((string)($it['price'] ?? ''));
        if ($it['_var']) {
            $rows .= '- ' . $nama . ":\n";
            foreach ($it['_var'] as $v) {
                $rows .= '   • ' . ($v['name'] !== '' ? $v['name'] : 'Harga') . ' : ' . ($v['price'] !== '' ? $v['price'] : '(harga belum tersedia)') . "\n";
            }
        } else {
            $rows .= '- ' . $nama . ' : ' . ($harga !== '' ? $harga : '(harga belum tersedia)') . "\n";
        }
        if ($it['_det'] !== '') {
            if ($semua || in_array($i, $pilih, true)) $rows .= '  Detail: ' . str_replace("\n", "\n  ", $it['_det']) . "\n";
            else $sembunyi = true;
        }
    }

    $blk  = "=== DAFTAR PRODUK & HARGA RESMI ===\n";
    $blk .= "Ini sumber harga SATU-SATUNYA. Aturan yang WAJIB dipatuhi:\n";
    $blk .= "1. Untuk pertanyaan harga/tarif/biaya, pakai HANYA angka dari daftar ini.\n";
    $blk .= "2. Kalau ada angka berbeda di Knowledge Base, daftar ini yang benar.\n";
    $blk .= "3. JANGAN menghitung apa pun — tidak boleh mengalikan jumlah malam/unit,\n";
    $blk .= "   menjumlahkan beberapa item, menghitung diskon, pajak, atau total.\n";
    $blk .= "   Sebutkan harga satuan apa adanya, lalu arahkan customer untuk konfirmasi\n";
    $blk .= "   perhitungan total ke admin/tim kami.\n";
    $blk .= "4. Kalau item yang ditanya TIDAK ada di daftar, atau tertulis (harga belum tersedia),\n";
    $blk .= "   katakan terus terang belum tersedia informasinya dan arahkan ke kontak resmi. JANGAN menebak.\n";
    $blk .= "5. Produk bervarian: sebutkan nama varian bersama harganya. Kalau pelanggan belum\n";
    $blk .= "   menyebut varian, sebutkan pilihan variannya.\n";
    $blk .= "6. Baris 'Detail' adalah informasi resmi produk itu (isi, spesifikasi, manfaat, dll.).\n";
    if ($sembunyi) {
        $blk .= "7. Detail sebagian produk tidak ditampilkan di sini. Jika pelanggan menanyakan detail produk\n";
        $blk .= "   yang tidak punya baris Detail dan informasinya juga tidak ada di Knowledge Base,\n";
        $blk .= "   minta pelanggan menyebut nama produknya dengan lengkap. JANGAN menebak isi produk.\n";
    }
    $blk .= "\n" . $rows;
    if ($pl['updated_at'] !== '') {
        $blk .= "\n(Daftar diperbarui " . substr($pl['updated_at'], 0, 10) . ")";
    }
    return $blk;
}
