<?php
/**
 * v1.2.187: mitra — Program Mitra (reseller / referral) DEI Chatbot.
 *
 * Alur: mitra punya KODE → calon pelanggan mengisi kode di /daftar/ (atau datang lewat /daftar/?ref=KODE)
 *   → tenant tercatat milik mitra (tenants.json › partner) → tiap pesanan Duitku yang lunas (otomatis lewat
 *   blMarkPaid) menghasilkan satu baris komisi di buku komisi.
 * v1.2.188b: mitra-duitku — komisi HANYA dari pembayaran lewat Duitku; pembayaran transfer/invoice manual tidak dicatat.
 *
 * Komisi dihitung dari uang yang benar-benar diterima (nominal pesanan setelah diskon/kredit), dengan
 * persentase tier mitra PADA SAAT pembayaran. Tier = jumlah tenant aktif berbayar milik mitra:
 *   bawaan 1–9 tenant 20%, 10–24 tenant 30%, 25+ tenant 35% (admin-config.json › partner › tiers).
 * Mitra tipe "referral": persentase tetap, hanya untuk pembayaran dalam N bulan sejak pembayaran pertama.
 *
 * v1.2.191: mitra-skema — skema komisi per mitra: default (tier umum), fixed (persentase tetap), tiers (tier khusus mitra).
 *   Kolom mitra: scheme, scheme_pct, scheme_tiers, scheme_at, scheme_by. Berlaku untuk pembayaran berikutnya saja.
 * Data: data/partners.json (daftar mitra), data/partner-ledger.json (buku komisi).
 * Butuh signup-lib.php (su*) dan classify-lib.php (isTrialTenant). Fungsi berawalan pt*.
 * v1.2.188: mitra-portal — mitra bisa login di /mitra/ (lihat partner-portal-lib.php): email unik, password tidak pernah dikirim ke panel.
 */

if (!defined('SU_DATA')) define('SU_DATA', dirname(__DIR__) . '/data');
define('PT_FILE',   SU_DATA . '/partners.json');
define('PT_LEDGER', SU_DATA . '/partner-ledger.json');

/* ---------- konfigurasi (admin-config.json › partner) ---------- */
function ptDefaults() {
    return ['signup_field' => true, 'tiers' => [[1, 20], [10, 30], [25, 35]], 'referral_pct' => 20, 'referral_months' => 12, 'min_payout' => 250000];
}
/** Daftar [minimal tenant, persen], urut naik, tier pertama selalu mulai 1 tenant. */
function ptTiersNorm($in) {
    $by = [];
    foreach ((array)$in as $r) {
        if (!is_array($r) || count($r) < 2) continue;
        $r = array_values($r);
        $min = max(1, min(100000, (int)$r[0])); $pct = max(0, min(90, (int)$r[1]));
        $by[$min] = $pct;
    }
    if (!$by) return ptDefaults()['tiers'];
    ksort($by);
    $out = [];
    foreach ($by as $min => $pct) { $out[] = [$min, $pct]; if (count($out) >= 6) break; }
    $out[0][0] = 1;
    return $out;
}
function ptCfg() {
    $all = suRead(SU_DATA . '/admin-config.json', []);
    $c = array_merge(ptDefaults(), is_array($all['partner'] ?? null) ? $all['partner'] : []);
    $c['signup_field']    = !empty($c['signup_field']);
    $c['tiers']           = ptTiersNorm($c['tiers']);
    $c['referral_pct']    = max(0, min(90, (int)$c['referral_pct']));
    $c['referral_months'] = max(1, min(120, (int)$c['referral_months']));
    $c['min_payout']      = max(0, (int)$c['min_payout']);
    return $c;
}
function ptSaveCfg($in) {
    $all = suRead(SU_DATA . '/admin-config.json', []);
    $cur = ptCfg();
    foreach (['referral_pct', 'referral_months', 'min_payout'] as $k) if (array_key_exists($k, $in)) $cur[$k] = (int)$in[$k];
    if (array_key_exists('signup_field', $in)) $cur['signup_field'] = !empty($in['signup_field']);
    if (array_key_exists('tiers', $in)) $cur['tiers'] = ptTiersNorm($in['tiers']);
    $all['partner'] = $cur;
    suWrite(SU_DATA . '/admin-config.json', $all);
    return ptCfg();
}

/* ---------- utilitas ---------- */
function ptToday() { return gmdate('Y-m-d', time() + 7 * 3600); }   // WIB
function ptMonth() { return substr(ptToday(), 0, 7); }
function ptDateOk($d) { return (bool)preg_match('/^\d{4}-\d{2}-\d{2}$/', (string)$d) && strtotime($d . ' 00:00:00 UTC') !== false; }
function ptAddMonths($ymd, $n) {
    $d = DateTime::createFromFormat('!Y-m-d', (string)$ymd, new DateTimeZone('UTC'));
    if (!$d) return (string)$ymd;
    $day = (int)$d->format('j');
    $d->modify('first day of this month')->modify('+' . (int)$n . ' month');
    $d->setDate((int)$d->format('Y'), (int)$d->format('n'), min($day, (int)$d->format('t')));
    return $d->format('Y-m-d');
}
function ptSignupBase() {
    $b = rtrim((string)(suCfg()['pusat_url'] ?? ''), '/');
    return ($b !== '' ? $b : 'https://chat.deintegra.com') . '/daftar/';
}
function ptLock() { $f = @fopen(SU_DATA . '/partner.lock', 'c'); if ($f) flock($f, LOCK_EX); return $f; }
function ptUnlock($f) { if ($f) { flock($f, LOCK_UN); fclose($f); } }

/* ---------- mitra ---------- */
function ptAll() { return array_values(array_filter(suRead(PT_FILE, []), 'is_array')); }
function ptSaveAll($a) { return suWrite(PT_FILE, array_values($a)); }
function ptCodeNorm($c) { return strtoupper(preg_replace('/[^A-Za-z0-9]/', '', (string)$c)); }
function ptCodeValid($c) { return (bool)preg_match('/^[A-Z0-9]{4,16}$/', (string)$c); }
function ptFind($id, $all = null) {
    $id = (string)$id; if ($id === '') return null;
    foreach (($all ?? ptAll()) as $p) if (($p['id'] ?? '') === $id) return $p;
    return null;
}
/** Hanya mitra aktif: kode mitra nonaktif tidak bisa dipakai mendaftar. */
function ptFindByCode($code, $all = null) {
    $code = ptCodeNorm($code); if (!ptCodeValid($code)) return null;
    foreach (($all ?? ptAll()) as $p) if (($p['code'] ?? '') === $code) return !empty($p['active']) ? $p : null;
    return null;
}
function ptCodeTaken($code, $all, $exceptId = '') {
    foreach ($all as $p) if (($p['code'] ?? '') === $code && ($p['id'] ?? '') !== $exceptId) return true;
    return false;
}
function ptSuggestCode($name, $all) {
    $b = substr(ptCodeNorm($name), 0, 8);
    if (strlen($b) < 4) $b = str_pad($b, 4, 'X');
    if (!ptCodeTaken($b, $all)) return $b;
    for ($i = 2; $i < 500; $i++) { $c = substr($b, 0, 13) . $i; if (!ptCodeTaken($c, $all)) return $c; }
    return substr($b, 0, 8) . strtoupper(bin2hex(random_bytes(3)));
}
/** Simpan mitra baru / ubah. [true, mitra] atau [false, pesan]. */
function ptSave($in) {
    $name = trim(preg_replace('/\s+/', ' ', (string)($in['name'] ?? '')));
    if (mb_strlen($name) < 2 || mb_strlen($name) > 80) return [false, 'Nama mitra 2–80 karakter.'];
    $type = ($in['type'] ?? 'reseller') === 'referral' ? 'referral' : 'reseller';
    $email = strtolower(trim((string)($in['email'] ?? '')));
    if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) return [false, 'Email tidak valid.'];
    $phoneRaw = trim((string)($in['phone'] ?? '')); $phone = $phoneRaw === '' ? '' : suPhone($phoneRaw);
    if ($phoneRaw !== '' && $phone === '') return [false, 'Nomor WhatsApp tidak valid.'];
    $lk = ptLock();
    $all = ptAll(); $id = (string)($in['id'] ?? ''); $idx = -1;
    foreach ($all as $i => $p) if ($id !== '' && ($p['id'] ?? '') === $id) { $idx = $i; break; }
    if ($id !== '' && $idx < 0) { ptUnlock($lk); return [false, 'Mitra tidak ditemukan.']; }
    $code = ptCodeNorm((string)($in['code'] ?? ''));
    if ($code === '') $code = $idx >= 0 ? (string)$all[$idx]['code'] : ptSuggestCode($name, $all);
    if (!ptCodeValid($code)) { ptUnlock($lk); return [false, 'Kode mitra 4–16 karakter, hanya huruf dan angka.']; }
    if (ptCodeTaken($code, $all, $id)) { ptUnlock($lk); return [false, 'Kode ' . $code . ' sudah dipakai mitra lain.']; }
    if ($email !== '') foreach ($all as $p) if (($p['id'] ?? '') !== $id && strtolower((string)($p['email'] ?? '')) === $email) { ptUnlock($lk); return [false, 'Email ini sudah dipakai mitra lain (email dipakai untuk login portal mitra).']; }   // v1.2.188: mitra-portal
    // v1.2.191: mitra-skema — skema komisi khusus mitra ini (tidak dikirim = pertahankan yang lama)
    $old = $idx >= 0 ? $all[$idx] : [];
    $sch = ['scheme' => (string)($old['scheme'] ?? 'default'), 'scheme_pct' => (int)($old['scheme_pct'] ?? 0), 'scheme_tiers' => (array)($old['scheme_tiers'] ?? [])];
    if (array_key_exists('scheme', $in)) {
        $sc = in_array($in['scheme'], ['fixed', 'tiers'], true) ? (string)$in['scheme'] : 'default';
        if ($sc === 'fixed') {
            $sp = $in['scheme_pct'] ?? null;
            if (!is_numeric($sp) || (int)$sp < 0 || (int)$sp > 90) { ptUnlock($lk); return [false, 'Komisi tetap harus angka 0–90%.']; }
            $sch = ['scheme' => 'fixed', 'scheme_pct' => (int)$sp, 'scheme_tiers' => []];
        } elseif ($sc === 'tiers') {
            if ($type === 'referral') { ptUnlock($lk); return [false, 'Tier khusus hanya untuk tipe Reseller. Untuk Referral pakai Persentase tetap.']; }
            $valid = array_filter((array)($in['scheme_tiers'] ?? []), function ($r) { return is_array($r) && count($r) >= 2 && (int)array_values($r)[0] >= 1; });
            if (!$valid) { ptUnlock($lk); return [false, 'Isi minimal satu baris tier khusus.']; }
            $sch = ['scheme' => 'tiers', 'scheme_pct' => 0, 'scheme_tiers' => ptTiersNorm($valid)];
        } else $sch = ['scheme' => 'default', 'scheme_pct' => 0, 'scheme_tiers' => []];
    }
    if ($sch['scheme'] === 'tiers' && $type === 'referral') $sch = ['scheme' => 'default', 'scheme_pct' => 0, 'scheme_tiers' => []];
    $schChanged = [$sch['scheme'], $sch['scheme_pct'], $sch['scheme_tiers']] != [(string)($old['scheme'] ?? 'default'), (int)($old['scheme_pct'] ?? 0), (array)($old['scheme_tiers'] ?? [])];
    $rec = ['name' => $name, 'code' => $code, 'type' => $type, 'contact' => mb_substr(trim((string)($in['contact'] ?? '')), 0, 80),
            'phone' => $phone, 'email' => $email, 'notes' => mb_substr(trim((string)($in['notes'] ?? '')), 0, 500),
            'active' => !array_key_exists('active', $in) || !empty($in['active'])] + $sch;
    if ($schChanged) { $rec['scheme_at'] = gmdate('Y-m-d H:i:s'); $rec['scheme_by'] = mb_substr((string)($in['_by'] ?? ''), 0, 60); }
    if ($idx >= 0) $all[$idx] = array_merge($all[$idx], $rec, ['updated' => gmdate('Y-m-d H:i:s')]);
    else { $rec = array_merge(['id' => 'm' . bin2hex(random_bytes(5))], $rec, ['created' => gmdate('Y-m-d H:i:s')]); $all[] = $rec; $idx = count($all) - 1; }
    $ok = ptSaveAll($all);
    ptUnlock($lk);
    return $ok ? [true, $all[$idx]] : [false, 'Gagal menyimpan data mitra.'];
}

/** v1.2.188: mitra-portal — data mitra untuk panel/portal: tanpa hash password. */
function ptPublic($p) {
    $p['has_password'] = !empty($p['password']); $p['last_login'] = (string)($p['last_login'] ?? '');
    unset($p['password'], $p['pw_changed_at']);
    return $p;
}

/* ---------- tenant & tier ---------- */
/** Tenant aktif berbayar: bukan trial, aktif, lisensi aktif, belum lewat masa aktif (kosong = dikelola manual). */
function ptIsPaying($t) {
    if (!is_array($t) || isTrialTenant($t)) return false;
    if (array_key_exists('active', $t) && empty($t['active'])) return false;
    if (($t['license_status'] ?? 'active') !== 'active') return false;
    $exp = trim((string)($t['expires_at'] ?? ''));
    return $exp === '' || $exp >= ptToday();
}
function ptTenantsOf($pid, $tenants) {
    $out = [];
    foreach ((array)$tenants as $t) if (is_array($t) && (string)($t['partner'] ?? '') === (string)$pid && $pid !== '') $out[] = $t;
    return $out;
}
function ptCount($pid, $tenants) { return count(array_filter(ptTenantsOf($pid, $tenants), 'ptIsPaying')); }
function ptPctFor($n, $cfg) {
    $pct = (int)$cfg['tiers'][0][1];
    foreach ($cfg['tiers'] as $r) if ($n >= $r[0]) $pct = (int)$r[1];
    return $pct;
}
/** Persentase yang berlaku sekarang untuk mitra. next = [minimal tenant, persen] tier berikutnya atau null. */
function ptRate($partner, $tenants, $cfg = null) {
    $cfg = $cfg ?: ptCfg();
    $n = ptCount((string)($partner['id'] ?? ''), $tenants);
    $scheme = (string)($partner['scheme'] ?? 'default');   // v1.2.191: mitra-skema
    if ($scheme === 'fixed') return ['pct' => max(0, min(90, (int)($partner['scheme_pct'] ?? 0))), 'n' => $n, 'next' => null, 'scheme' => 'fixed', 'tiers' => []];
    if (($partner['type'] ?? 'reseller') === 'referral') return ['pct' => (int)$cfg['referral_pct'], 'n' => $n, 'next' => null, 'scheme' => 'default', 'tiers' => []];
    $tiers = $cfg['tiers'];
    if ($scheme === 'tiers' && !empty($partner['scheme_tiers'])) $tiers = ptTiersNorm($partner['scheme_tiers']); else $scheme = 'default';
    $next = null;
    foreach ($tiers as $r) if ($r[0] > max($n, 1)) { $next = $r; break; }   // 0 tenant sudah di tier pertama
    return ['pct' => ptPctFor($n, ['tiers' => $tiers]), 'n' => $n, 'next' => $next, 'scheme' => $scheme, 'tiers' => $tiers];
}

/* ---------- buku komisi ---------- */
function ptLedger() { return array_values(array_filter(suRead(PT_LEDGER, []), 'is_array')); }
/** Referral: masih dalam N bulan sejak pembayaran pertama tenant ini? (belum ada pembayaran = ya) */
function ptReferralOk($pid, $tid, $date, $ledger, $cfg) {
    $first = '';
    foreach ($ledger as $e) {
        if (!empty($e['void']) || ($e['partner_id'] ?? '') !== $pid || ($e['tenant_id'] ?? '') !== $tid) continue;
        $d = (string)($e['date'] ?? '');
        if ($d !== '' && ($first === '' || $d < $first)) $first = $d;
    }
    return $first === '' || $date < ptAddMonths($first, (int)$cfg['referral_months']);
}
/**
 * Catat satu komisi. Idempoten per $ref (nomor pesanan). [true, entri, baru?] atau [false, pesan].
 * $pctOverride: persentase khusus dari admin (null = ikut tier / referral).
 */
function ptCommission($partner, $t, $tenants, $base, $date, $ref, $source, $note = '', $pctOverride = null) {
    $base = (int)$base;
    if ($base <= 0) return [false, 'Nominal pembayaran harus lebih dari 0.'];
    if (!ptDateOk($date)) return [false, 'Tanggal tidak valid.'];
    $cfg = ptCfg(); $pid = (string)$partner['id']; $tid = strtolower((string)($t['tenant_id'] ?? ''));
    $rate = ptRate($partner, $tenants, $cfg);
    $pct = $pctOverride !== null ? max(0, min(90, (int)$pctOverride)) : (int)$rate['pct'];
    $lk = ptLock();
    $led = ptLedger();
    // satu pesanan = satu komisi; yang sudah dibatalkan (refund) juga tidak dicatat ulang oleh callback/susulan
    foreach ($led as $e) if (($e['ref'] ?? '') === $ref) { ptUnlock($lk); return [true, $e, false]; }
    if ($pctOverride === null && ($partner['type'] ?? 'reseller') === 'referral' && !ptReferralOk($pid, $tid, $date, $led, $cfg)) {
        ptUnlock($lk);
        return [false, 'Masa komisi referral (' . $cfg['referral_months'] . ' bulan sejak pembayaran pertama) untuk tenant ini sudah lewat.'];
    }
    $e = ['id' => 'k' . bin2hex(random_bytes(6)), 'partner_id' => $pid, 'tenant_id' => $tid, 'tenant_name' => (string)($t['name'] ?? $tid),
          'ref' => (string)$ref, 'source' => (string)$source, 'date' => (string)$date, 'month' => substr((string)$date, 0, 7),
          'base' => $base, 'pct' => $pct, 'amount' => (int)round($base * $pct / 100), 'n' => (int)$rate['n'],
          'note' => mb_substr((string)$note, 0, 200), 'created' => gmdate('Y-m-d H:i:s')];
    $led[] = $e;
    $ok = suWrite(PT_LEDGER, $led);
    ptUnlock($lk);
    return $ok ? [true, $e, true] : [false, 'Gagal menulis buku komisi.'];
}
function ptOrderNote($o) {
    $mode = ['trial' => 'trial → berbayar', 'new' => 'baru', 'renew' => 'perpanjang', 'upgrade' => 'naik paket', 'downgrade' => 'turun paket'];
    return ucfirst((string)($o['tier'] ?? '')) . ' · ' . (int)($o['months'] ?? 1) . ' bln · ' . ($mode[$o['mode'] ?? ''] ?? (string)($o['mode'] ?? ''));
}
function ptOrderDate($o) {
    $ts = strtotime((string)($o['paid_at'] ?? ''));
    return gmdate('Y-m-d', ($ts ?: time()) + 7 * 3600);
}
/** Dipanggil blMarkPaid setelah pembayaran diterapkan ke tenant. Mengembalikan entri komisi baru atau null. */
function ptOnPaid($o, $t, $tenants) {
    $pid = trim((string)($t['partner'] ?? ''));
    if ($pid === '' || ($o['env'] ?? '') === 'sandbox') return null;
    $p = ptFind($pid);
    if (!$p || empty($p['active'])) return null;
    $r = ptCommission($p, $t, $tenants, (int)($o['amount'] ?? 0), ptOrderDate($o), (string)$o['id'], 'duitku', ptOrderNote($o));
    if (empty($r[0])) { error_log('ptOnPaid ' . ($o['id'] ?? '') . ': ' . $r[1]); return null; }
    if (!empty($r[2])) {
        $e = $r[1];
        suTelegram("\xF0\x9F\xA4\x9D Komisi mitra {$p['name']} ({$p['code']}): Rp" . number_format($e['amount'], 0, ',', '.') . " ({$e['pct']}% dari Rp" . number_format($e['base'], 0, ',', '.') . ") · {$e['tenant_id']} · {$o['id']}");
        return $e;
    }
    return null;
}
/** Susulkan komisi dari pesanan Duitku lunas yang belum tercatat (dibayar setelah tenant dihubungkan ke mitra). */
function ptSync($tenants, $onlyPid = '') {
    if (!function_exists('blOrders')) return 0;
    $byId = [];
    foreach ((array)$tenants as $t) if (is_array($t)) $byId[strtolower((string)($t['tenant_id'] ?? ''))] = $t;
    $parts = ptAll(); $n = 0;
    foreach (array_reverse(blOrders(5000)) as $o) {
        if (($o['status'] ?? '') !== 'paid' || ($o['env'] ?? '') === 'sandbox' || empty($o['applied'])) continue;
        $t = $byId[(string)($o['tenant_id'] ?? '')] ?? null;
        $pid = $t ? trim((string)($t['partner'] ?? '')) : '';
        if ($pid === '' || ($onlyPid !== '' && $pid !== $onlyPid)) continue;
        $p = ptFind($pid, $parts);
        if (!$p || empty($p['active'])) continue;
        $since = strtotime((string)($t['partner_at'] ?? '') . ' UTC'); $paid = strtotime((string)($o['paid_at'] ?? ''));
        if ($since && $paid && $paid < $since) continue;   // dibayar sebelum jadi tenant mitra
        $r = ptCommission($p, $t, $tenants, (int)$o['amount'], ptOrderDate($o), (string)$o['id'], 'duitku', ptOrderNote($o) . ' · susulan');
        if (!empty($r[0]) && !empty($r[2])) $n++;
    }
    return $n;
}
/** Batalkan satu komisi (mis. refund). Yang sudah dibayarkan ke mitra tidak bisa dibatalkan. */
function ptVoid($id, $reason) {
    $lk = ptLock(); $led = ptLedger();
    foreach ($led as $i => $e) {
        if (($e['id'] ?? '') !== (string)$id) continue;
        if (!empty($e['paid_out'])) { ptUnlock($lk); return [false, 'Komisi ini sudah dibayarkan ke mitra. Catat koreksinya di pembayaran berikutnya.']; }
        if (!empty($e['void'])) { ptUnlock($lk); return [true, $e]; }
        $led[$i]['void'] = ['at' => gmdate('Y-m-d H:i:s'), 'reason' => mb_substr(trim((string)$reason), 0, 200)];
        $ok = suWrite(PT_LEDGER, $led); ptUnlock($lk);
        return $ok ? [true, $led[$i]] : [false, 'Gagal menulis buku komisi.'];
    }
    ptUnlock($lk);
    return [false, 'Komisi tidak ditemukan.'];
}
/** Tandai semua komisi mitra yang belum dibayar (sampai bulan $upto, kosong = semua) sebagai sudah dibayarkan. */
function ptPayout($pid, $upto, $note) {
    $upto = preg_match('/^\d{4}-\d{2}$/', (string)$upto) ? (string)$upto : '';
    $lk = ptLock(); $led = ptLedger(); $sum = 0; $cnt = 0;
    $batch = 'b' . bin2hex(random_bytes(4)); $at = gmdate('Y-m-d H:i:s');
    foreach ($led as $i => $e) {
        if (($e['partner_id'] ?? '') !== (string)$pid || !empty($e['void']) || !empty($e['paid_out'])) continue;
        if ($upto !== '' && (string)($e['month'] ?? '') > $upto) continue;
        $led[$i]['paid_out'] = ['at' => $at, 'batch' => $batch, 'note' => mb_substr(trim((string)$note), 0, 200)];
        $sum += (int)($e['amount'] ?? 0); $cnt++;
    }
    if (!$cnt) { ptUnlock($lk); return [false, 'Tidak ada komisi yang belum dibayar.']; }
    $ok = suWrite(PT_LEDGER, $led); ptUnlock($lk);
    return $ok ? [true, ['count' => $cnt, 'total' => $sum, 'batch' => $batch]] : [false, 'Gagal menulis buku komisi.'];
}

/* ---------- ringkasan untuk panel admin ---------- */
function ptTotals($pid, $ledger) {
    $m = ptMonth(); $o = ['month' => 0, 'unpaid' => 0, 'total' => 0, 'entries' => 0];
    foreach ($ledger as $e) {
        if (($e['partner_id'] ?? '') !== $pid || !empty($e['void'])) continue;
        $a = (int)($e['amount'] ?? 0);
        $o['total'] += $a; $o['entries']++;
        if (($e['month'] ?? '') === $m) $o['month'] += $a;
        if (empty($e['paid_out'])) $o['unpaid'] += $a;
    }
    return $o;
}
function ptSummary($tenants) {
    $cfg = ptCfg(); $led = ptLedger(); $out = [];
    foreach (ptAll() as $p) {
        $r = ptRate($p, $tenants, $cfg);
        $out[] = array_merge(ptPublic($p), ptTotals((string)$p['id'], $led),
            ['tenants' => count(ptTenantsOf((string)$p['id'], $tenants)), 'paying' => $r['n'], 'pct' => $r['pct'], 'next' => $r['next'], 'scheme' => $r['scheme'], 'tiers_eff' => $r['tiers'],
             'link' => ptSignupBase() . '?ref=' . $p['code']]);
    }
    usort($out, function ($a, $b) { return [$b['paying'], $b['total']] <=> [$a['paying'], $a['total']] ?: strcasecmp((string)$a['name'], (string)$b['name']); });
    return $out;
}
function ptTenantRow($t) {
    $trial = isTrialTenant($t);
    return ['tenant_id' => strtolower((string)($t['tenant_id'] ?? '')), 'name' => (string)($t['name'] ?? ''),
            'tier' => $trial ? 'trial' : strtolower((string)($t['tier'] ?? '')), 'paying' => ptIsPaying($t),
            'license_status' => (string)($t['license_status'] ?? 'active'), 'expires_at' => (string)($t['expires_at'] ?? ''),
            'partner_at' => (string)($t['partner_at'] ?? ''), 'partner_via' => (string)($t['partner_via'] ?? ''),
            'duitku' => function_exists('blEligible') ? (bool)blEligible($t)[0] : true];   // v1.2.188b: bisa bayar lewat /bayar/ ?
}
function ptDetail($pid, $tenants) {
    $p = ptFind($pid);
    if (!$p) return null;
    $led = array_values(array_filter(ptLedger(), function ($e) use ($pid) { return ($e['partner_id'] ?? '') === $pid; }));
    usort($led, function ($a, $b) { return strcmp((string)($b['date'] ?? '') . ($b['created'] ?? ''), (string)($a['date'] ?? '') . ($a['created'] ?? '')); });
    $r = ptRate($p, $tenants);
    return ['partner' => array_merge(ptPublic($p), ptTotals($pid, $led), ['paying' => $r['n'], 'pct' => $r['pct'], 'next' => $r['next'], 'scheme' => $r['scheme'], 'tiers_eff' => $r['tiers'], 'link' => ptSignupBase() . '?ref=' . $p['code']]),
            'tenants' => array_map('ptTenantRow', ptTenantsOf($pid, $tenants)), 'ledger' => $led];
}
