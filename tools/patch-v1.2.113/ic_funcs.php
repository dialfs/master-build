// v1.2.113: import-kontak — impor kontak dari file (XLS/XLSX/CSV) ke menu Kontak.
// Kunci kontak = nomor angka saja berawalan kode negara (sama persis dengan nomor
// dari WhatsApp), jadi saat nomor itu chat nanti datanya otomatis menyatu.
function contactImportNormNum($raw) {
    $d = preg_replace('/\D/', '', (string)$raw);
    if ($d === '') return '';
    if (strpos($d, '00') === 0) $d = substr($d, 2);                 // 0062… (format internasional)
    if (strpos($d, '620') === 0) $d = '62' . substr($d, 3);         // +62 0812… -> 62812…
    elseif ($d[0] === '0') $d = '62' . substr($d, 1);               // 0812… -> 62812…
    elseif ($d[0] === '8' && strlen($d) >= 9 && strlen($d) <= 13) $d = '62' . $d;   // 812… -> 62812…
    $n = strlen($d);
    if ($n < 10 || $n > 15) return '';
    if (strpos($d, '62') === 0 && ($d[2] ?? '') !== '8') return '';   // nomor HP Indonesia selalu 628…
    return $d;
}
function contactImportRank($s) {
    $r = ['active_customer' => 6, 'hot_prospect' => 5, 'warm' => 4, 'cold' => 3, 'churned' => 2, 'lost' => 1, 'new' => 0];
    return $r[$s] ?? 0;
}
// Terapkan satu baris impor ke kontak (dipanggil di dalam waContactUpdate).
// Kebijakan: Lead Rating hanya diisi bila kontak baru / masih Unrated, kecuali
// $overwrite; nama tidak menimpa nama yang sudah ada; last_seen dibiarkan kosong
// untuk kontak baru (belum pernah chat -> urut paling bawah).
function contactImportApply(array &$c, $isNew, array $r, $overwrite, $now, &$res) {
    if ($isNew) { $c['last_seen'] = ''; $res = 'created'; }
    $cur = contactStageValid($c['stage'] ?? '') ? $c['stage'] : 'new';
    $stage = $r['stage'];
    if ($stage !== '' && ($isNew || $cur === 'new' || $overwrite)) {
        if ($cur !== $stage || $isNew) {
            $c['stage'] = $stage;
            $c['vip'] = ($stage === 'active_customer') ? !empty($c['vip']) : false;
            $c['stage_updated_at'] = $now;
        }
        if (!$isNew) $res = 'updated';
    } elseif (!$isNew) {
        $res = ($stage !== '' && $cur !== $stage) ? 'kept' : 'updated';
    }
    if ($r['name'] !== '') {
        if (trim((string)($c['cust_name'] ?? '')) === '') $c['cust_name'] = $r['name'];
        if (trim((string)($c['name_manual'] ?? '')) === '' && trim((string)($c['name_wa'] ?? '')) === '') $c['name_manual'] = $r['name'];
    }
    $c['imp'] = ['at' => $now, 'src' => $r['src'], 'st' => $r['st'], 'n' => $r['cnt']];
}
