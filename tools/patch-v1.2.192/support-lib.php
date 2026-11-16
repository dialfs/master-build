<?php
/* v1.2.192: asisten-support — tenant "DEI Support" sebagai asisten bantuan di dashboard tenant.
 *
 * Pengaturan : data/admin-config.json › support { enabled, tenant_id, base, notify }
 * Umpan KB   : panduan per fitur (satu entri per `key`, bukan per rilis), dikumpulkan dari
 *                - releases/guide.json            { "guide": [ ... ] }  (isi awal & fitur khusus pusat)
 *                - releases/vX/manifest.json › guide [ ... ]           (ikut setiap rilis tenant)
 *              Item yang `updated`-nya lebih baru menimpa item ber-key sama. `remove: true` menghapus entri.
 *              Ditambah satu entri `paket-harga` yang dibangkitkan dari pengaturan pembayaran (tidak diketik tangan).
 * Item guide : { key, title, content, menu?, min_tier?, since?, updated?, remove? }
 *
 * Entri langsung tayang di tenant Support (keputusan Dias 16 Nov 2026), jadi blok guide divalidasi
 * di dev/preflight.sh sebelum deploy; di sini item yang tidak sah dilewati dan dilaporkan ke admin.
 */

function spDefaults() { return ['enabled' => false, 'tenant_id' => '', 'base' => '', 'notify' => true]; }

function spCfg() {
    $all = suRead(SU_DATA . '/admin-config.json', []);
    $c = array_merge(spDefaults(), is_array($all['support'] ?? null) ? $all['support'] : []);
    return [
        'enabled'   => !empty($c['enabled']),
        'tenant_id' => tidNorm((string)$c['tenant_id']),
        'base'      => rtrim(trim((string)$c['base']), '/'),
        'notify'    => !empty($c['notify']),
    ];
}

/** @return array [bool ok, string pesan galat] */
function spSaveCfg($in) {
    $in = is_array($in) ? $in : [];
    $cur = spCfg();
    if (array_key_exists('tenant_id', $in)) $cur['tenant_id'] = tidNorm((string)$in['tenant_id']);
    if (array_key_exists('base', $in))      $cur['base']      = rtrim(trim((string)$in['base']), '/');
    if (array_key_exists('enabled', $in))   $cur['enabled']   = !empty($in['enabled']);
    if (array_key_exists('notify', $in))    $cur['notify']    = !empty($in['notify']);

    if ($cur['base'] !== '' && (strlen($cur['base']) > 200 || !preg_match('#^https?://[A-Za-z0-9.-]+(:\d+)?(/[A-Za-z0-9._~/-]*)?$#', $cur['base']))) {
        return [false, 'Alamat tenant Support tidak sah. Contoh: https://chatbot.deintegra.com/support'];
    }
    if ($cur['tenant_id'] !== '') {
        $found = false;
        foreach (readJson(TENANTS_FILE, []) as $t) { if (is_array($t) && tidEq($t['tenant_id'] ?? '', $cur['tenant_id'])) { $found = true; break; } }
        if (!$found) return [false, 'Tenant "' . $cur['tenant_id'] . '" belum terdaftar di pusat. Daftarkan dulu tenant Support-nya.'];
    }
    if ($cur['enabled'] && ($cur['tenant_id'] === '' || $cur['base'] === '')) {
        return [false, 'Isi tenant Support dan alamatnya dulu sebelum menyalakan tombol Bantuan.'];
    }
    $all = suRead(SU_DATA . '/admin-config.json', []);
    $all['support'] = $cur;
    if (!suWrite(SU_DATA . '/admin-config.json', $all)) return [false, 'Gagal menyimpan pengaturan.'];
    return [true, ''];
}

/* Dikirim ke tenant lewat check_update › support_widget.
 * Tenant biasa: { enabled, base }. Tenant Support sendiri: { enabled:false, self:true } (penanda untuk menarik umpan KB). */
function spWidgetPayload($tenant) {
    $c = spCfg();
    if (is_array($tenant) && $c['tenant_id'] !== '' && tidEq($tenant['tenant_id'] ?? '', $c['tenant_id'])) return ['enabled' => false, 'self' => true];
    if (!$c['enabled'] || $c['base'] === '' || $c['tenant_id'] === '') return ['enabled' => false];
    return ['enabled' => true, 'base' => $c['base']];
}

function spVerOk($v) { return is_string($v) && preg_match('/^v\d+\.\d+\.\d+$/', $v) === 1; }

/** Bersihkan satu item guide. @return array|string  array = item sah, string = alasan ditolak */
function spGuideClean($g) {
    if (!is_array($g)) return 'bukan objek';
    $key = strtolower(trim((string)($g['key'] ?? '')));
    if (!preg_match('/^[a-z0-9][a-z0-9-]{1,39}$/', $key)) return 'key tidak sah';
    if ($key === 'paket-harga') return 'paket-harga: key ini dibangkitkan otomatis';
    if (!empty($g['remove'])) return ['key' => $key, 'remove' => true];
    $title   = trim((string)preg_replace('/\s+/u', ' ', (string)($g['title'] ?? '')));
    $content = trim(str_replace("\r", '', (string)($g['content'] ?? '')));
    if (mb_strlen($title) < 3 || mb_strlen($title) > 120)       return $key . ': title harus 3-120 karakter';
    if (mb_strlen($content) < 20 || mb_strlen($content) > 4000) return $key . ': content harus 20-4000 karakter';
    $menu = strtolower(trim((string)($g['menu'] ?? '')));
    if (!preg_match('/^[a-z0-9_-]{0,24}$/', $menu)) return $key . ': menu tidak sah';
    $tier = strtolower(trim((string)($g['min_tier'] ?? '')));
    if ($tier !== '' && !in_array($tier, BL_TIERS, true)) return $key . ': min_tier tidak dikenal';
    foreach (['since', 'updated'] as $f) {
        if (isset($g[$f]) && $g[$f] !== '' && !spVerOk($g[$f])) return $key . ': ' . $f . ' harus berbentuk vX.Y.Z';
    }
    return ['key' => $key, 'menu' => $menu, 'title' => $title, 'content' => $content, 'min_tier' => $tier,
            'since' => (string)($g['since'] ?? ''), 'updated' => (string)($g['updated'] ?? '')];
}

function spRp($n) { return 'Rp' . number_format((int)$n, 0, ',', '.'); }

/* Entri paket & harga: angka diambil dari pengaturan pembayaran dan tabel kuota paket yang dipakai pusat. */
function spPriceEntry() {
    $c = blCfg(); $pre = blPresets(); $wa = waNumTierMax(); $bu = buTierMax(); $cls = clsTierQuotas(); $su = suCfg();
    $L = ['Paket DEI Chatbot (harga per bulan):'];
    foreach (BL_TIERS as $t) {
        $price = (int)($c['price_' . $t] ?? 0);
        $p = [];
        $p[] = $price > 0 ? spRp($price) . ' per bulan' : 'harga: hubungi tim DEI';
        if (isset($pre[$t][0])) $p[] = 'kuota ' . number_format((int)$pre[$t][0], 0, ',', '.') . ' chat per bulan';
        $n = (int)($wa[$t] ?? 0);  $p[] = $n > 0 ? 'hingga ' . $n . ' nomor WhatsApp tambahan di luar nomor utama' : 'tanpa nomor WhatsApp tambahan (hanya nomor utama)';
        $n = (int)($bu[$t] ?? 0);  $p[] = $n > 0 ? 'hingga ' . $n . ' unit bisnis' : 'tanpa fitur unit bisnis';
        $n = (int)($cls[$t] ?? 0); $p[] = $n > 0 ? 'Filter Topik AI ' . number_format($n, 0, ',', '.') . ' klasifikasi per bulan' : 'tanpa Filter Topik AI';
        $L[] = '- ' . ucfirst($t) . ': ' . implode('; ', $p) . '.';
    }
    $d = [];
    if ((int)$c['disc_3'] > 0)  $d[] = 'bayar 3 bulan diskon ' . (int)$c['disc_3'] . '%';
    if ((int)$c['disc_12'] > 0) $d[] = 'bayar 12 bulan diskon ' . (int)$c['disc_12'] . '%';
    if ($d) $L[] = 'Diskon: ' . implode(', ', $d) . '.';
    $L[] = 'Trial gratis: ' . (int)$su['trial_days'] . ' hari dengan kuota ' . number_format((int)$su['trial_cap'], 0, ',', '.') . ' chat, dengan fitur paket ' . ucfirst((string)$su['trial_tier']) . '.';
    if (!empty($c['enabled'])) $L[] = 'Bayar, perpanjang, atau naik paket bisa dilakukan online lewat tombol bayar di banner lisensi atau kartu paket di dashboard.';
    else $L[] = 'Untuk bayar, perpanjang, atau naik paket, hubungi tim DEI.';
    $L[] = 'Angka untuk tenant tertentu bisa berbeda bila diatur khusus oleh tim DEI; angka yang berlaku tampil di kartu paket di dashboard.';
    return ['key' => 'paket-harga', 'menu' => '', 'title' => 'Paket, harga, dan kuota', 'content' => implode("\n", $L),
            'min_tier' => '', 'since' => '', 'updated' => (string)(latestVersion() ?? '')];
}

/** Kumpulkan entri panduan. $bad diisi daftar item yang dilewati ("sumber: alasan"). */
function spFeedEntries(&$bad = []) {
    $bad = []; $items = [];   // [updated, urutan, since, item]
    $seq = 0;
    $vers = [];
    foreach (@glob(RELEASES_DIR . '/v*', GLOB_ONLYDIR) ?: [] as $d) { if (spVerOk(basename($d))) $vers[] = basename($d); }
    usort($vers, function ($a, $b) { return version_compare(ltrim($a, 'v'), ltrim($b, 'v')); });
    foreach ($vers as $v) {
        $m = loadManifest($v);
        if (!is_array($m) || !isset($m['guide'])) continue;
        if (array_filter(array_map('strval', (array)($m['only_tenants'] ?? [])))) continue;   // rilis khusus klien: bukan panduan umum
        if (!is_array($m['guide'])) { $bad[] = $v . ': guide bukan daftar'; continue; }
        foreach ($m['guide'] as $g) {
            $c = spGuideClean($g);
            if (!is_array($c)) { $bad[] = $v . ': ' . $c; continue; }
            $c['updated'] = $v;
            $items[] = [$v, $seq++, $c];
        }
    }
    $base = readJson(RELEASES_DIR . '/guide.json', null);
    if (is_array($base)) {
        if (!is_array($base['guide'] ?? null)) $bad[] = 'guide.json: guide bukan daftar';
        else foreach ($base['guide'] as $g) {
            $c = spGuideClean($g);
            if (!is_array($c)) { $bad[] = 'guide.json: ' . $c; continue; }
            if (empty($c['remove']) && $c['updated'] === '') $c['updated'] = $c['since'] !== '' ? $c['since'] : 'v0.0.0';
            $c['_base'] = true;
            $items[] = [empty($c['remove']) ? $c['updated'] : (spVerOk($g['updated'] ?? null) ? $g['updated'] : 'v0.0.0'), $seq++, $c];   // seri: guide.json menang
        }
    }
    usort($items, function ($a, $b) { return version_compare(ltrim($a[0], 'v'), ltrim($b[0], 'v')) ?: ($a[1] <=> $b[1]); });
    $out = [];
    foreach ($items as $it) {
        $c = $it[2]; $k = $c['key'];
        if (!empty($c['remove'])) { unset($out[$k]); continue; }
        if ($c['since'] === '') $c['since'] = $out[$k]['since'] ?? (empty($c['_base']) ? $c['updated'] : '');   // guide.json: 'sejak' hanya bila ditulis
        unset($c['_base']);
        if ($c['updated'] === 'v0.0.0') $c['updated'] = '';
        $out[$k] = $c;
    }
    $p = spPriceEntry(); $out[$p['key']] = $p;
    ksort($out);
    return array_values($out);
}

function spFeedSig($entries) {
    $sig = [];
    foreach ($entries as $e) $sig[$e['key']] = md5(json_encode([$e['menu'], $e['title'], $e['content'], $e['min_tier'], $e['since']], JSON_UNESCAPED_UNICODE));
    return $sig;
}

/* Umpan untuk tenant Support. $touch = true: catat keadaan terakhir dan kirim ringkasan perubahan ke Telegram. */
function spFeed($touch = false) {
    $bad = [];
    $entries = spFeedEntries($bad);
    $sig = spFeedSig($entries);
    $rev = md5(json_encode($sig));
    if ($touch) {
        $sf = SU_DATA . '/support-feed-state.json';
        $st = suRead($sf, []);
        if (($st['rev'] ?? '') !== $rev) {
            $old = is_array($st['sig'] ?? null) ? $st['sig'] : null;
            $title = []; foreach ($entries as $e) $title[$e['key']] = $e['title'];
            $add = []; $chg = []; $del = [];
            if ($old !== null) {
                foreach ($sig as $k => $h) { if (!isset($old[$k])) $add[] = $title[$k]; elseif ($old[$k] !== $h) $chg[] = $title[$k]; }
                foreach ($old as $k => $h) { if (!isset($sig[$k])) $del[] = $k; }
            }
            suWrite($sf, ['rev' => $rev, 'sig' => $sig, 'count' => count($entries), 'at' => gmdate('Y-m-d H:i:s')]);
            if (spCfg()['notify']) {
                $cut = function ($a) { return implode(', ', array_slice($a, 0, 12)) . (count($a) > 12 ? ' (+' . (count($a) - 12) . ' lagi)' : ''); };
                $msg = "Asisten Support: KB diperbarui otomatis (" . count($entries) . " entri)";
                if ($old === null) $msg .= "\nIsi awal dimuat ke tenant Support.";
                if ($add) $msg .= "\nBaru: " . $cut($add);
                if ($chg) $msg .= "\nDiubah: " . $cut($chg);
                if ($del) $msg .= "\nDihapus: " . $cut($del);
                if ($bad) $msg .= "\nDilewati (tidak sah): " . $cut($bad);
                suTelegram($msg);
            }
        }
    }
    return ['rev' => $rev, 'entries' => $entries];
}

/* Untuk Admin Pusat: pengaturan + ringkasan umpan (tanpa mengubah keadaan). */
function spCfgAdmin() {
    $bad = [];
    $entries = spFeedEntries($bad);
    $st = suRead(SU_DATA . '/support-feed-state.json', []);
    $rev = md5(json_encode(spFeedSig($entries)));
    $list = [];
    foreach ($entries as $e) $list[] = ['key' => $e['key'], 'title' => $e['title'], 'menu' => $e['menu'], 'min_tier' => $e['min_tier'], 'since' => $e['since'], 'updated' => $e['updated']];
    return spCfg() + ['feed' => ['count' => count($entries), 'entries' => $list, 'invalid' => $bad, 'rev' => $rev,
                                 'pulled_at' => (string)($st['at'] ?? ''), 'in_sync' => ($st['rev'] ?? '') === $rev]];
}
