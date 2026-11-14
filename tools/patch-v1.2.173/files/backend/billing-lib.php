<?php
/**
 * v1.2.173 — Pembayaran mandiri (Duitku) untuk tenant DEI Chatbot.
 *
 * Alur: tenant membuka /bayar/?t=<token> (dari dashboard, banner trial, atau pengingat WA)
 *   → pilih paket & durasi → billing_checkout membuat pesanan + invoice Duitku → halaman bayar Duitku
 *   → Duitku memanggil backend/billing-callback.php → blMarkPaid(): trial dikonversi / masa aktif diperpanjang
 *   / paket dinaikkan, lisensi aktif, status didorong ke tenant.
 *
 * Kredensial Duitku: memakai merchant yang sama dengan deintegra.com
 *   (bawaan <public_html>/deintegra.com/data/duitku-config.json; data/duitku-config.json di pusat menimpa bila ada).
 * Token tautan bayar: <tenant_id>.<hmac(license_key)> — tetap (tidak kedaluwarsa), batal bila license_key diganti.
 * Pesanan: data/billing-orders/<DCB-...>.json. Harga = sumber kebenaran di server (admin-config.json › billing).
 *
 * Butuh signup-lib.php (su*) dan classify-lib.php (isTrialTenant, waNumTierMax, buTierMax, clsTierQuotas).
 */

if (!defined('SU_DATA')) define('SU_DATA', dirname(__DIR__) . '/data');
define('BL_DIR', SU_DATA . '/billing-orders');
define('BL_TIERS', ['starter', 'growth', 'business', 'pro']);

/* chat cap & cost cap (USD) per paket — sama dengan preset "Jadikan berbayar" (trial_update convert) */
function blPresets() { return ['starter' => [1000, 3], 'growth' => [2000, 6], 'business' => [5000, 15], 'pro' => [15000, 45]]; }

/* ---------- konfigurasi (admin-config.json › billing) ---------- */
function blDefaults() {
    $home = dirname(dirname(__DIR__));   // .../public_html
    return [
        'enabled'        => false,
        'price_starter'  => 500000,
        'price_growth'   => 900000,
        'price_business' => 1800000,
        'price_pro'      => 3750000,
        'disc_3'         => 5,
        'disc_12'        => 10,
        'duitku_file'    => $home . '/deintegra.com/data/duitku-config.json',
        'duitku_env'     => '',          // '' = ikut file Duitku deintegra.com | sandbox | production
        'pay_base'       => '',          // '' = URL pusat (pengaturan pendaftaran)
        'admin_email'    => '',
        'reminders'      => true,        // pengingat perpanjangan WA: H-7, H-3, H-1, lewat, H+6
        'refund_url'     => 'https://deintegra.com/kebijakan-refund',
        'expiry_minutes' => 1440,
    ];
}
function blCfg() {
    $all = suRead(SU_DATA . '/admin-config.json', []);
    $c = array_merge(blDefaults(), is_array($all['billing'] ?? null) ? $all['billing'] : []);
    foreach (BL_TIERS as $k) $c['price_' . $k] = max(0, (int)$c['price_' . $k]);
    $c['disc_3'] = max(0, min(50, (int)$c['disc_3'])); $c['disc_12'] = max(0, min(50, (int)$c['disc_12']));
    $c['expiry_minutes'] = max(30, min(10080, (int)$c['expiry_minutes']));
    if (!in_array($c['duitku_env'], ['', 'sandbox', 'production'], true)) $c['duitku_env'] = '';
    return $c;
}
function blSaveCfg($in) {
    $all = suRead(SU_DATA . '/admin-config.json', []);
    $cur = blCfg();
    foreach (blDefaults() as $k => $def) {
        if (!array_key_exists($k, $in)) continue;
        $v = $in[$k];
        if (is_bool($def)) $cur[$k] = !empty($v);
        elseif (is_int($def)) $cur[$k] = (int)$v;
        else $cur[$k] = trim((string)$v);
    }
    $cur['pay_base'] = rtrim((string)$cur['pay_base'], '/');
    $all['billing'] = $cur;
    suWrite(SU_DATA . '/admin-config.json', $all);
    return blCfg();
}
function blPayBase() {
    $b = rtrim((string)blCfg()['pay_base'], '/');
    if ($b === '') $b = rtrim((string)(suCfg()['pusat_url'] ?? ''), '/');
    return $b !== '' ? $b : 'https://chat.deintegra.com';
}
/** Kredensial Duitku (merchant deintegra.com). null = belum ada. */
function blDuitku() {
    static $c = null;
    if ($c !== null) return $c ?: null;
    $cfg = blCfg();
    foreach ([SU_DATA . '/duitku-config.json', (string)$cfg['duitku_file']] as $f) {
        if ($f === '' || !@is_file($f)) continue;
        $j = json_decode((string)@file_get_contents($f), true);
        if (!is_array($j) || empty($j['merchantCode']) || empty($j['apiKey'])) continue;
        $j['env'] = $cfg['duitku_env'] !== '' ? $cfg['duitku_env'] : ((($j['env'] ?? 'sandbox') === 'production') ? 'production' : 'sandbox');
        $j['_file'] = $f;
        return $c = $j;
    }
    $c = false;
    return null;
}
/** Untuk panel admin (tanpa rahasia). */
function blCfgPublicAdmin() {
    $c = blCfg(); $d = blDuitku();
    $c['duitku_ok'] = (bool)$d;
    $c['duitku_env_eff'] = $d ? $d['env'] : '';
    $c['duitku_merchant'] = $d ? substr((string)$d['merchantCode'], 0, 3) . '•••' : '';
    $c['duitku_from'] = $d ? $d['_file'] : '';
    $c['pay_base_eff'] = blPayBase();
    $c['callback_url'] = blPayBase() . '/backend/billing-callback.php';
    $su = suCfg();
    $c['waha_ok'] = $su['waha_url'] !== '' && $su['waha_key'] !== '';
    return $c;
}

/* ---------- tanggal (WIB, Y-m-d) ---------- */
function blToday() { return gmdate('Y-m-d', time() + 7 * 3600); }
function blAddMonths($ymd, $n) {
    $d = DateTime::createFromFormat('!Y-m-d', (string)$ymd, new DateTimeZone('UTC'));
    if (!$d) $d = new DateTime('today', new DateTimeZone('UTC'));
    $day = (int)$d->format('j');
    $d->modify('first day of this month')->modify('+' . (int)$n . ' month');
    $d->setDate((int)$d->format('Y'), (int)$d->format('n'), min($day, (int)$d->format('t')));
    return $d->format('Y-m-d');
}
function blDays($from, $to) { return (int)round((strtotime($to . ' 00:00:00 UTC') - strtotime($from . ' 00:00:00 UTC')) / 86400); }
function blFmtDate($ymd) {
    $b = [1 => 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
    $t = strtotime($ymd . ' 00:00:00 UTC');
    return $t ? gmdate('j', $t) . ' ' . $b[(int)gmdate('n', $t)] . ' ' . gmdate('Y', $t) : (string)$ymd;
}
function blRp($n) { return 'Rp' . number_format((int)$n, 0, ',', '.'); }

/* ---------- token tautan bayar ---------- */
function blToken($t) {
    $tid = strtolower((string)($t['tenant_id'] ?? ''));
    return $tid . '.' . substr(hash_hmac('sha256', 'bayar|' . $tid, (string)($t['license_key'] ?? '')), 0, 20);
}
function blFindByToken($tok, $tenants) {
    if (!preg_match('/^([a-z0-9][a-z0-9_-]{1,40})\.([a-f0-9]{20})$/', strtolower(trim((string)$tok)), $m)) return null;
    foreach ($tenants as $t) {
        if (strtolower((string)($t['tenant_id'] ?? '')) !== $m[1] || empty($t['license_key'])) continue;
        return hash_equals(blToken($t), $m[0]) ? $t : null;
    }
    return null;
}
/** [boleh bayar mandiri, alasan] */
function blEligible($t) {
    if (!is_array($t) || empty($t['license_key'])) return [false, 'Tenant tidak valid.'];
    if (($t['license_status'] ?? 'active') === 'blocked') return [false, 'Layanan ini sedang diblokir. Hubungi tim DEI.'];
    if (isTrialTenant($t)) return [true, ''];
    $tier = strtolower((string)($t['tier'] ?? ''));
    if (!in_array($tier, BL_TIERS, true)) return [false, 'Paket Anda diatur khusus oleh tim DEI. Hubungi kami untuk perpanjangan.'];
    if (trim((string)($t['expires_at'] ?? '')) === '' && empty($t['billing_self'])) return [false, 'Langganan Anda dikelola manual oleh tim DEI. Hubungi kami untuk pembayaran.'];
    return [true, ''];
}
function blPayUrl($t) {
    if (empty(blCfg()['enabled']) || !blEligible($t)[0]) return '';
    return blPayBase() . '/bayar/?t=' . blToken($t);
}

/* ---------- paket & harga ---------- */
function blTierFeatures() {
    $p = blPresets(); $wa = waNumTierMax(); $bu = buTierMax(); $cls = clsTierQuotas(); $out = [];
    foreach (BL_TIERS as $k) $out[$k] = ['chat_cap' => $p[$k][0], 'wa_numbers' => (int)($wa[$k] ?? 0), 'business_units' => (int)($bu[$k] ?? 0), 'classify' => (int)($cls[$k] ?? 0)];
    return $out;
}
/** Hitung tagihan. mode: trial (konversi) | new | renew | upgrade (kredit sisa paket lama) | downgrade (mulai setelah masa aktif). */
function blQuote($t, $tier, $months) {
    $c = blCfg(); $tier = strtolower((string)$tier); $months = (int)$months;
    if (!in_array($tier, BL_TIERS, true)) return ['ok' => false, 'error' => 'Paket tidak dikenal.'];
    $disc = [1 => 0, 3 => $c['disc_3'], 12 => $c['disc_12']];
    if (!isset($disc[$months])) return ['ok' => false, 'error' => 'Durasi harus 1, 3, atau 12 bulan.'];
    $price = (int)$c['price_' . $tier];
    if ($price <= 0) return ['ok' => false, 'error' => 'Paket ' . ucfirst($tier) . ' belum bisa dibayar online. Hubungi tim DEI.'];
    $gross = $price * $months; $net = (int)round($gross * (100 - $disc[$months]) / 100);
    $today = blToday(); $trial = isTrialTenant($t);
    $cur = $trial ? '' : strtolower((string)($t['tier'] ?? '')); $exp = trim((string)($t['expires_at'] ?? ''));
    $active = !$trial && $exp !== '' && $exp >= $today;
    $rank = array_flip(BL_TIERS); $credit = 0; $mode = $trial ? 'trial' : 'new'; $start = $today; $left = $active ? blDays($today, $exp) : 0;
    if ($active && $cur === $tier) { $mode = 'renew'; $start = $exp; }
    elseif ($active && isset($rank[$cur]) && $rank[$tier] > $rank[$cur]) {
        $mode = 'upgrade';
        $credit = min((int)floor($left * $c['price_' . $cur] / 30), max(0, $net - 10000));   // Duitku: minimal Rp10.000
    } elseif ($active && isset($rank[$cur]) && $rank[$tier] < $rank[$cur]) {
        if ($left > 7) return ['ok' => false, 'error' => 'Turun ke paket ' . ucfirst($tier) . ' bisa dilakukan mulai 7 hari sebelum masa aktif berakhir (' . blFmtDate($exp) . ').'];
        $mode = 'downgrade'; $start = $exp;
    }
    return ['ok' => true, 'tier' => $tier, 'months' => $months, 'price' => $price, 'gross' => $gross, 'disc_pct' => $disc[$months],
            'disc' => $gross - $net, 'credit' => $credit, 'credit_days' => $credit ? $left : 0, 'amount' => $net - $credit, 'mode' => $mode,
            'starts' => $start, 'ends' => blAddMonths($start, $months), 'label' => 'DEI Chatbot ' . ucfirst($tier) . ' — ' . $months . ' bulan'];
}
/** Ringkasan tenant untuk halaman bayar. */
function blTenantView($t) {
    $trial = isTrialTenant($t); $exp = trim((string)($t['expires_at'] ?? ''));
    $v = ['name' => (string)($t['name'] ?? $t['tenant_id']), 'tenant_id' => strtolower((string)$t['tenant_id']), 'trial' => $trial,
          'tier' => $trial ? trialTier($t) : strtolower((string)($t['tier'] ?? '')), 'license_status' => (string)($t['license_status'] ?? 'active'),
          'expires_at' => $exp, 'days_left' => $exp !== '' ? blDays(blToday(), $exp) : null, 'dashboard_url' => suTenantDashUrl($t)];
    if ($trial && is_array($t['trial'] ?? null)) { $v['trial_ends'] = gmdate('Y-m-d', (int)$t['trial']['ends'] + 7 * 3600); $v['days_left'] = (int)ceil(((int)$t['trial']['ends'] - time()) / 86400); }
    $sg = (array)($t['signup'] ?? []);
    $v['customer'] = ['name' => (string)($t['billing_name'] ?? ($sg['name'] ?? '')), 'email' => (string)($t['billing_email'] ?? ($sg['email'] ?? '')),
                      'phone' => (string)($t['billing_phone'] ?? ($sg['phone'] ?? ''))];
    return $v;
}

/* ---------- pesanan (flat-file) ---------- */
function blDir() {
    if (!is_dir(BL_DIR)) { @mkdir(BL_DIR, 0750, true); @file_put_contents(BL_DIR . '/.htaccess', "Require all denied\nDeny from all\n"); }
    return BL_DIR;
}
function blOrderIdValid($id) { return (bool)preg_match('/^DCB-\d{6}-[A-Z0-9]{6}$/', (string)$id); }
function blOrderNewId() {
    $abc = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; $r = '';
    for ($i = 0; $i < 6; $i++) $r .= $abc[random_int(0, strlen($abc) - 1)];
    return 'DCB-' . gmdate('ymd', time() + 7 * 3600) . '-' . $r;
}
function blOrderLoad($id) {
    if (!blOrderIdValid($id)) return null;
    $f = blDir() . '/' . $id . '.json';
    return is_file($f) ? json_decode((string)file_get_contents($f), true) : null;
}
function blOrderSave($o) { $o['updated_at'] = gmdate('c'); suWrite(blDir() . '/' . $o['id'] . '.json', $o); }
function blLog($msg) { @file_put_contents(blDir() . '/billing.log', '[' . gmdate('c') . "] $msg\n", FILE_APPEND | LOCK_EX); }
function blOrders($limit = 200, $tid = '') {
    $fs = glob(blDir() . '/DCB-*.json') ?: [];
    rsort($fs);
    $out = [];
    foreach ($fs as $f) {
        $o = json_decode((string)file_get_contents($f), true);
        if (!is_array($o) || ($tid !== '' && ($o['tenant_id'] ?? '') !== $tid)) continue;
        $out[] = $o;
        if (count($out) >= $limit) break;
    }
    usort($out, function ($a, $b) { return strcmp((string)($b['created_at'] ?? ''), (string)($a['created_at'] ?? '')); });
    return $out;
}

/* ---------- Duitku (POP createInvoice) ---------- */
function blDuitkuEndpoint($what) {
    $prod = (blDuitku()['env'] ?? 'sandbox') === 'production';
    if ($what === 'invoice') return $prod ? 'https://api-prod.duitku.com/api/merchant/createInvoice' : 'https://api-sandbox.duitku.com/api/merchant/createInvoice';
    return $prod ? 'https://passport.duitku.com/webapi/api/merchant/transactionStatus' : 'https://sandbox.duitku.com/webapi/api/merchant/transactionStatus';
}
function blHttp($url, $body, $headers = []) {
    if (defined('BL_HTTP_MOCK') && is_callable(BL_HTTP_MOCK)) return call_user_func(BL_HTTP_MOCK, $url, $body, $headers);   // uji lokal
    $ch = curl_init($url);
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_POSTFIELDS => json_encode($body), CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HTTPHEADER => array_merge(['Content-Type: application/json', 'Accept: application/json'], $headers),
        CURLOPT_TIMEOUT => 30, CURLOPT_CONNECTTIMEOUT => 10]);
    $raw = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $err = curl_error($ch); curl_close($ch);
    return ['http' => $code, 'raw' => $raw === false ? '' : (string)$raw, 'json' => json_decode((string)$raw, true), 'error' => $err];
}
function blDuitkuInvoice($o) {
    $c = blDuitku();
    if (!$c) return ['ok' => false, 'message' => 'Pembayaran online belum dikonfigurasi.'];
    $ts = (string)round(microtime(true) * 1000);
    $nm = explode(' ', trim($o['customer']['name']), 2);
    $hp = preg_replace('/^62/', '0', $o['customer']['phone']);
    $body = [
        'paymentAmount' => (int)$o['amount'], 'merchantOrderId' => $o['id'], 'productDetails' => mb_substr($o['item'], 0, 255),
        'email' => $o['customer']['email'], 'phoneNumber' => $hp, 'customerVaName' => mb_substr($o['customer']['name'], 0, 20),
        'merchantUserInfo' => $o['customer']['email'], 'additionalParam' => 'chatbot:' . $o['tenant_id'],
        'itemDetails' => [['name' => mb_substr($o['item'], 0, 50), 'price' => (int)$o['amount'], 'quantity' => 1]],
        'customerDetail' => ['firstName' => $nm[0], 'lastName' => $nm[1] ?? '', 'email' => $o['customer']['email'], 'phoneNumber' => $hp],
        'returnUrl' => blPayBase() . '/bayar/?t=' . rawurlencode($o['token']) . '&order=' . rawurlencode($o['id']),
        'callbackUrl' => blPayBase() . '/backend/billing-callback.php',
        'expiryPeriod' => blCfg()['expiry_minutes'],
    ];
    $r = blHttp(blDuitkuEndpoint('invoice'), $body, ['x-duitku-signature: ' . hash_hmac('sha256', $c['merchantCode'] . $ts, $c['apiKey']),
        'x-duitku-timestamp: ' . $ts, 'x-duitku-merchantcode: ' . $c['merchantCode']]);
    $j = $r['json'];
    if ($r['http'] === 200 && is_array($j) && ($j['statusCode'] ?? '') === '00' && !empty($j['paymentUrl'])) return ['ok' => true, 'paymentUrl' => $j['paymentUrl'], 'reference' => $j['reference'] ?? ''];
    blLog("createInvoice GAGAL {$o['id']} http={$r['http']} err={$r['error']} body=" . mb_substr($r['raw'], 0, 500));
    return ['ok' => false, 'message' => is_array($j) ? ($j['statusMessage'] ?? $j['Message'] ?? 'Gagal membuat tagihan') : 'Tidak bisa terhubung ke Duitku'];
}
function blDuitkuStatus($id) {
    $c = blDuitku(); if (!$c) return null;
    foreach ([hash_hmac('sha256', $c['merchantCode'] . $id, $c['apiKey']), md5($c['merchantCode'] . $id . $c['apiKey'])] as $sig) {
        $r = blHttp(blDuitkuEndpoint('status'), ['merchantCode' => $c['merchantCode'], 'merchantOrderId' => $id, 'signature' => $sig]);
        if ($r['http'] === 200 && is_array($r['json']) && isset($r['json']['statusCode'])) return $r['json'];
    }
    return null;
}
function blCallbackValid($p) {
    $c = blDuitku(); if (!$c) return false;
    if (($p['merchantCode'] ?? '') !== $c['merchantCode'] || empty($p['signature'])) return false;
    $s = $c['merchantCode'] . ($p['amount'] ?? '') . ($p['merchantOrderId'] ?? '');
    $sig = strtolower((string)$p['signature']);
    return hash_equals(hash_hmac('sha256', $s, $c['apiKey']), $sig) || hash_equals(md5($s . $c['apiKey']), $sig);
}

/* ---------- buat pesanan ---------- */
function blCheckout($t, $in) {
    list($ok, $why) = blEligible($t);
    if (!$ok) return ['ok' => false, 'error' => $why];
    if (!blDuitku()) return ['ok' => false, 'error' => 'Pembayaran online belum siap. Hubungi tim DEI.'];
    $q = blQuote($t, (string)($in['tier'] ?? ''), (int)($in['months'] ?? 1));
    if (empty($q['ok'])) return $q;
    $name = trim(preg_replace('/\s+/', ' ', (string)($in['name'] ?? '')));
    $email = strtolower(trim((string)($in['email'] ?? '')));
    $phone = suPhone((string)($in['phone'] ?? ''));
    if (mb_strlen($name) < 2) return ['ok' => false, 'error' => 'Isi nama pemesan.'];
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) return ['ok' => false, 'error' => 'Email tidak valid.'];
    if (!preg_match('/^62\d{8,13}$/', $phone)) return ['ok' => false, 'error' => 'Nomor WhatsApp tidak valid.'];
    if (empty($in['agree'])) return ['ok' => false, 'error' => 'Setujui kebijakan pembayaran & refund dulu.'];
    $o = ['id' => blOrderNewId(), 'tenant_id' => strtolower((string)$t['tenant_id']), 'tenant_name' => (string)($t['name'] ?? ''),
          'token' => blToken($t), 'tier' => $q['tier'], 'months' => $q['months'], 'mode' => $q['mode'], 'amount' => $q['amount'],
          'quote' => $q, 'item' => $q['label'] . ' (' . ($t['name'] ?? $t['tenant_id']) . ')',
          'from' => ['tier' => isTrialTenant($t) ? 'trial' : (string)($t['tier'] ?? ''), 'expires_at' => (string)($t['expires_at'] ?? '')],
          'customer' => ['name' => mb_substr($name, 0, 80), 'email' => $email, 'phone' => $phone],
          'status' => 'pending', 'created_at' => gmdate('c'), 'ip' => suClientIp(), 'env' => blDuitku()['env']];
    blOrderSave($o);
    $r = blDuitkuInvoice($o);
    if (empty($r['ok'])) { $o['status'] = 'failed'; $o['error'] = $r['message']; blOrderSave($o); return ['ok' => false, 'error' => 'Gagal membuat tagihan: ' . $r['message']]; }
    $o['payment_url'] = $r['paymentUrl']; $o['reference'] = $r['reference']; blOrderSave($o);
    blLog("CHECKOUT {$o['id']} {$o['tenant_id']} {$o['tier']} {$o['months']}bl {$o['amount']} {$o['mode']}");
    return ['ok' => true, 'order_id' => $o['id'], 'payment_url' => $r['paymentUrl']];
}

/* ---------- terapkan pembayaran ke tenant ---------- */
function blApply(&$t, $o) {
    $today = blToday(); $tier = (string)$o['tier']; $months = (int)$o['months'];
    $wasTrial = isTrialTenant($t); $cur = $wasTrial ? '' : strtolower((string)($t['tier'] ?? '')); $exp = trim((string)($t['expires_at'] ?? ''));
    // lanjut dari masa aktif bila paket sama / perpanjang / turun paket; naik paket & trial mulai hari ini
    $start = (!$wasTrial && $exp !== '' && $exp >= $today && ($cur === $tier || in_array($o['mode'] ?? '', ['renew', 'downgrade'], true))) ? $exp : $today;
    $ends = blAddMonths($start, $months);
    if ($wasTrial) {
        if (is_array($t['trial'] ?? null)) $t['trial_history'] = $t['trial'];
        unset($t['trial']);
        $t['converted_at'] = gmdate('Y-m-d H:i:s'); $t['converted_via'] = 'duitku';
    }
    if ($wasTrial || $cur !== $tier) {
        $p = blPresets()[$tier];
        $t['monthly_chat_cap'] = $p[0]; $t['monthly_cost_cap_usd'] = $p[1];
    }
    $t['tier'] = $tier; $t['expires_at'] = $ends;
    $t['license_status'] = 'active'; $t['suspend_message'] = ''; $t['status_changed_at'] = gmdate('Y-m-d H:i:s');
    $t['cap_alert_sent_at'] = ''; $t['billing_self'] = true;
    $t['billing_name'] = $o['customer']['name']; $t['billing_email'] = $o['customer']['email']; $t['billing_phone'] = $o['customer']['phone'];
    $t['billing_last'] = ['order' => $o['id'], 'tier' => $tier, 'months' => $months, 'amount' => (int)$o['amount'], 'paid_at' => gmdate('Y-m-d H:i:s'), 'starts' => $start, 'ends' => $ends];
    return ['from' => $wasTrial ? 'trial' : $cur, 'starts' => $start, 'ends' => $ends, 'converted' => $wasTrial];
}
/** Dorong status lisensi ke tenant sekarang (tidak menunggu cache) — sama dengan set_status. */
function blPushLicense($t) {
    $u = trim((string)($t['api_url'] ?? ''));
    if ($u === '' || (defined('BL_HTTP_MOCK'))) return false;
    $ch = curl_init($u . (strpos($u, '?') === false ? '?' : '&') . 'action=license_push');
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 12, CURLOPT_CONNECTTIMEOUT => 6, CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS => 2, CURLOPT_POST => true, CURLOPT_POSTFIELDS => '',
        CURLOPT_HTTPHEADER => ['X-Tenant-Id: ' . strtolower((string)$t['tenant_id']), 'X-License-Key: ' . ($t['license_key'] ?? ''), 'User-Agent: DEI-Pusat/1.2.173',
            'X-Dei-License: ' . json_encode(['status' => 'active', 'message' => '', 'expires_at' => (string)$t['expires_at'], 'pay_url' => blPayUrl($t)], JSON_UNESCAPED_UNICODE)]]);
    $r = curl_exec($ch); $c = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    $j = json_decode((string)$r, true);
    return $c === 200 && !empty($j['ok']);
}
/** Tandai lunas + terapkan ke tenant (idempoten, dikunci). [ok, order] */
function blMarkPaid($id, $info) {
    $lk = @fopen(blDir() . '/.lock', 'c');
    if ($lk) flock($lk, LOCK_EX);
    $unlock = function () use ($lk) { if ($lk) { flock($lk, LOCK_UN); fclose($lk); } };
    $o = blOrderLoad($id);
    if (!$o) { $unlock(); return [false, null]; }
    if (($o['status'] ?? '') === 'paid') { $unlock(); return [true, $o]; }
    $o['status'] = 'paid'; $o['paid_at'] = gmdate('c'); $o['payment'] = $info;
    $tf = SU_DATA . '/tenants.json'; $tenants = suRead($tf, []); $idx = -1;
    foreach ($tenants as $i => $t) if (strtolower((string)($t['tenant_id'] ?? '')) === $o['tenant_id']) { $idx = $i; break; }
    if ($idx < 0 || !count($tenants)) {
        $o['apply_error'] = 'Tenant tidak ditemukan di registry.'; blOrderSave($o); $unlock();
        blLog("PAID {$id} TAPI tenant {$o['tenant_id']} tidak ada");
        suTelegram("\xE2\x9A\xA0 Pembayaran {$id} " . blRp($o['amount']) . " LUNAS tapi tenant {$o['tenant_id']} tidak ditemukan. Proses manual.");
        return [true, $o];
    }
    $o['applied'] = blApply($tenants[$idx], $o);
    if (!suWrite($tf, $tenants)) {
        $o['apply_error'] = 'Gagal menulis tenants.json.'; unset($o['applied']); blOrderSave($o); $unlock();
        blLog("PAID {$id} GAGAL tulis tenants.json");
        suTelegram("\xE2\x9A\xA0 Pembayaran {$id} LUNAS tapi gagal diterapkan (tenants.json). Cek manual.");
        return [true, $o];
    }
    $t = $tenants[$idx];
    $ip = (string)($t['install_path'] ?? '');
    if ($ip !== '' && is_file(rtrim($ip, '/') . '/data/cap-cache.json')) @unlink(rtrim($ip, '/') . '/data/cap-cache.json');
    blOrderSave($o);
    $unlock();
    blLog("PAID {$id} {$o['tenant_id']} {$o['tier']} {$o['months']}bl " . (int)$o['amount'] . ' s/d ' . $o['applied']['ends'] . ' ref=' . ($info['reference'] ?? ''));
    try { $o['pushed'] = blPushLicense($t); } catch (\Throwable $e) { error_log('blPushLicense: ' . $e->getMessage()); }
    try { blNotifyPaid($o, $t); } catch (\Throwable $e) { error_log('blNotifyPaid: ' . $e->getMessage()); }
    return [true, $o];
}
function blNotifyPaid($o, $t) {
    $a = (array)($o['applied'] ?? []); $biz = (string)($t['name'] ?? $o['tenant_id']); $pk = ucfirst($o['tier']);
    $what = ($a['from'] ?? '') === 'trial' ? 'Trial dikonversi ke paket ' . $pk : (($a['from'] ?? '') === $o['tier'] ? 'Perpanjangan paket ' . $pk : 'Paket kini ' . $pk);
    $txt = "Pembayaran chatbot {$biz} sudah kami terima. Terima kasih!\n\n{$what} · {$o['months']} bulan\nTotal: " . blRp($o['amount']) .
           "\nAktif sampai: " . blFmtDate($a['ends'] ?? '') . "\nNo. pesanan: {$o['id']}\n";
    $dash = suTenantDashUrl($t);
    if (!blTestMode()) {
        $su = suCfg(); $sent = [];
        foreach ([$o['customer']['phone'], (string)($t['signup']['phone'] ?? '')] as $ph) {
            $ph = suPhone($ph); if ($ph === '' || isset($sent[$ph])) continue; $sent[$ph] = 1;
            suWahaSend($su, $ph, $txt . ($dash ? "\nDashboard: {$dash}" : ''));
        }
        suTelegram("\xF0\x9F\x92\xB0 Lunas {$o['id']} · {$o['tenant_id']} ({$biz})\n{$what} · {$o['months']} bln · " . blRp($o['amount']) . "\ns/d " . ($a['ends'] ?? '') . " · {$o['customer']['name']} {$o['customer']['phone']}" . (!empty($o['payment']['paymentCode']) ? ' · ' . $o['payment']['paymentCode'] : ''));
        $hdr = "From: Deintegra <noreply@deintegra.com>\r\nContent-Type: text/plain; charset=UTF-8";
        $adm = trim((string)blCfg()['admin_email']) ?: trim((string)(blDuitku()['adminEmail'] ?? ''));
        if ($adm !== '') @mail($adm, "[Lunas] {$o['id']} — DEI Chatbot {$pk} ({$biz})", $txt . "\nTenant: {$o['tenant_id']}\nPemesan: {$o['customer']['name']} · {$o['customer']['email']} · {$o['customer']['phone']}\nReferensi Duitku: " . ($o['payment']['reference'] ?? '-') . "\n", $hdr);
        @mail($o['customer']['email'], "Pembayaran diterima — {$o['id']}", "Halo {$o['customer']['name']},\n\n{$txt}" . ($dash ? "\nDashboard: {$dash}\n" : '') . "\nDeintegra (PT Daya Estima Integra)\nWhatsApp: +62 851 1123 0487\n", $hdr);
    }
}
function blTestMode() { return defined('BL_HTTP_MOCK'); }

/* ---------- pengingat perpanjangan (cron-tick.php) ---------- */
function blRenewReminders($tenants, $dry = false) {
    $c = blCfg(); $sent = [];
    if (empty($c['enabled']) || empty($c['reminders'])) return $sent;
    $su = suCfg();
    if ($su['waha_url'] === '' || $su['waha_key'] === '') return $sent;
    $nf = SU_DATA . '/billing-notify.json'; $log = suRead($nf, []); $today = blToday(); $hour = (int)gmdate('G', time() + 7 * 3600);
    if (!$dry && ($hour < 8 || $hour >= 20)) return $sent;   // hanya jam 08-20 WIB (dry = tampilkan saja)
    foreach ($tenants as $t) {
        if (isTrialTenant($t) || empty($t['active'])) continue;
        $exp = trim((string)($t['expires_at'] ?? ''));
        if ($exp === '' || !blEligible($t)[0]) continue;
        $phone = suPhone((string)($t['billing_phone'] ?? ($t['signup']['phone'] ?? '')));
        if ($phone === '') continue;
        $tid = strtolower((string)$t['tenant_id']); $d = blDays($today, $exp);
        $k = $d > 7 ? '' : ($d > 3 ? 'd7' : ($d > 1 ? 'd3' : ($d >= 0 ? 'd1' : ($d > -6 ? 'x0' : ($d >= -8 ? 'x6' : '')))));
        if ($k === '') continue;
        $done = (array)($log[$tid] ?? []);
        if (($done['exp'] ?? '') !== $exp) $done = ['exp' => $exp];
        if (isset($done[$k])) continue;
        $biz = (string)($t['name'] ?? $tid); $pk = ucfirst(strtolower((string)$t['tier'])); $url = blPayUrl($t);
        $msg = ['d7' => "Masa aktif chatbot {$biz} (paket {$pk}) berakhir {$d} hari lagi, " . blFmtDate($exp) . '.',
                'd3' => "Masa aktif chatbot {$biz} (paket {$pk}) tinggal {$d} hari, berakhir " . blFmtDate($exp) . '.',
                'd1' => "Masa aktif chatbot {$biz} (paket {$pk}) berakhir " . ($d === 0 ? 'hari ini' : 'besok') . ', ' . blFmtDate($exp) . '. Perpanjang supaya bot tetap membalas pelanggan.',
                'x0' => "Masa aktif chatbot {$biz} sudah berakhir sejak " . blFmtDate($exp) . '. Layanan akan dihentikan sementara 7 hari setelah tanggal tersebut bila belum diperpanjang.',
                'x6' => "Chatbot {$biz} akan dihentikan sementara besok karena masa aktif belum diperpanjang. Data & pengaturan tetap tersimpan."][$k];
        $msg .= "\n\nPerpanjang online (transfer bank, VA, e-wallet, QRIS):\n{$url}";
        if (!$dry) { list($ok) = suWahaSend($su, $phone, $msg); if (!$ok) continue; }
        $done[$k] = gmdate('Y-m-d H:i:s'); $log[$tid] = $done; $sent[] = $tid . ':' . $k;
        if ($k === 'x0' && !$dry) suTelegram("Masa aktif {$tid} ({$biz}) berakhir " . $exp . '. Pengingat bayar terkirim ke ' . $phone . '.');
    }
    if ($sent && !$dry) suWrite($nf, $log);
    return $sent;
}
