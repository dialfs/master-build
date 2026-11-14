#!/usr/bin/env python3
"""v1.2.173 bayar-mandiri (PUSAT): pembayaran mandiri lewat Duitku (merchant deintegra.com).
- backend/billing-lib.php, backend/billing-callback.php, bayar/index.html (file baru, disalin dari folder patch)
- index.php: require billing-lib, action billing_info/quote/checkout/order (publik, token) + admin get/save_billing_config,
  billing_orders, billing_link, billing_recheck; check_update mengirim pay_url
- signup-lib.php: tautan trial (banner + pengingat) = tautan bayar per tenant bila pembayaran online aktif
- cron-tick.php: X-Dei-License membawa pay_url; pengingat perpanjangan WA
- admin/index.html: kartu Pembayaran Online + daftar pesanan; tombol Salin link bayar di Detail tenant
Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
P = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-pusat')
SRC = os.path.dirname(os.path.abspath(__file__))
TAG = 'v1.2.173: bayar-mandiri'; stamp = time.strftime('%Y%m%d-%H%M%S')
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    shutil.copy2(p, p + '.bak-v12173-' + stamp); wr(p, fn(s)); print('OK', p)
C = '   // ' + TAG

# --- file baru ---
for rel in ['backend/billing-lib.php', 'backend/billing-callback.php', 'bayar/index.html']:
    dst = P + '/' + rel; os.makedirs(os.path.dirname(dst), exist_ok=True)
    src = SRC + '/files/' + rel
    if os.path.exists(dst) and open(dst, 'rb').read() == open(src, 'rb').read(): print('sama:', dst); continue
    if os.path.exists(dst): shutil.copy2(dst, dst + '.bak-v12173-' + stamp)
    shutil.copy2(src, dst); print('OK', dst)

ACTIONS = r"""
    /* ========================================================
     * v1.2.173: bayar-mandiri — pembayaran Duitku (lihat backend/billing-lib.php)
     * Publik: auth = token tautan bayar (?t=<tenant>.<hmac>)
     * ====================================================== */
    case 'billing_info': {
        $t = blFindByToken((string)($_GET['t'] ?? (bodyInput()['t'] ?? '')), readJson(TENANTS_FILE, []));
        if (!$t) jsonOut(['ok' => false, 'error' => 'Tautan pembayaran tidak valid. Buka lagi dari dashboard chatbot Anda.'], 404);
        $c = blCfg();
        if (empty($c['enabled'])) jsonOut(['ok' => false, 'error' => 'Pembayaran online belum dibuka. Hubungi tim DEI untuk berlangganan.'], 503);
        list($elig, $why) = blEligible($t);
        $feat = blTierFeatures(); $tiers = [];
        foreach (BL_TIERS as $k) { $q = blQuote($t, $k, 1); $tiers[$k] = array_merge(['price' => $c['price_' . $k], 'ok' => !empty($q['ok']), 'note' => (string)($q['error'] ?? '')], $feat[$k]); }
        jsonOut(['ok' => true, 'eligible' => $elig, 'reason' => $why, 'ready' => (bool)blDuitku(), 'tenant' => blTenantView($t), 'tiers' => $tiers,
                 'durations' => [['months' => 1, 'disc' => 0], ['months' => 3, 'disc' => $c['disc_3']], ['months' => 12, 'disc' => $c['disc_12']]],
                 'refund_url' => (string)$c['refund_url']]);
    }
    case 'billing_quote': {
        $in = bodyInput();
        $t = blFindByToken((string)($in['t'] ?? ''), readJson(TENANTS_FILE, []));
        if (!$t) jsonOut(['ok' => false, 'error' => 'Tautan pembayaran tidak valid.'], 404);
        jsonOut(blQuote($t, (string)($in['tier'] ?? ''), (int)($in['months'] ?? 1)));
    }
    case 'billing_checkout': {
        $in = bodyInput();
        $t = blFindByToken((string)($in['t'] ?? ''), readJson(TENANTS_FILE, []));
        if (!$t) jsonOut(['ok' => false, 'error' => 'Tautan pembayaran tidak valid.'], 404);
        if (empty(blCfg()['enabled'])) jsonOut(['ok' => false, 'error' => 'Pembayaran online belum dibuka.'], 503);
        if (!suRateOk('bayar', 8, 3600)) jsonOut(['ok' => false, 'error' => 'Terlalu banyak percobaan. Coba lagi dalam 1 jam.'], 429);
        $r = blCheckout($t, $in);
        jsonOut($r, empty($r['ok']) ? 400 : 200);
    }
    case 'billing_order': {
        $tenants = readJson(TENANTS_FILE, []);
        $t = blFindByToken((string)($_GET['t'] ?? ''), $tenants);
        $o = blOrderLoad((string)($_GET['order'] ?? ''));
        if (!$t || !$o || $o['tenant_id'] !== strtolower((string)$t['tenant_id'])) jsonOut(['ok' => false, 'error' => 'Pesanan tidak ditemukan.'], 404);
        if (($o['status'] ?? '') === 'pending' && time() - strtotime((string)($o['checked_at'] ?? '2000-01-01')) >= 8) {   // callback belum masuk -> tanya Duitku
            $o['checked_at'] = gmdate('c'); blOrderSave($o);
            $s = blDuitkuStatus($o['id']);
            if ($s && ($s['statusCode'] ?? '') === '00' && (int)($s['amount'] ?? 0) === (int)$o['amount']) {
                blMarkPaid($o['id'], ['reference' => (string)($s['reference'] ?? ''), 'resultCode' => '00', 'source' => 'status']);
                $o = blOrderLoad($o['id']);
                $tenants = readJson(TENANTS_FILE, []); $t = blFindByToken((string)$_GET['t'], $tenants) ?: $t;
            } elseif ($s && ($s['statusCode'] ?? '') === '02') { $o['status'] = 'failed'; blOrderSave($o); }
        }
        jsonOut(['ok' => true, 'order' => ['id' => $o['id'], 'status' => $o['status'], 'tier' => $o['tier'], 'months' => $o['months'], 'amount' => $o['amount'],
                 'mode' => $o['mode'], 'ends' => $o['applied']['ends'] ?? ($o['quote']['ends'] ?? ''), 'payment_url' => ($o['status'] === 'pending' ? (string)($o['payment_url'] ?? '') : '')],
                 'tenant' => blTenantView($t)]);
    }
    case 'get_billing_config': {
        requireAdmin();
        jsonOut(['ok' => true, 'billing' => blCfgPublicAdmin()]);
    }
    case 'save_billing_config': {
        requireAdmin();
        blSaveCfg(bodyInput());
        jsonOut(['ok' => true, 'billing' => blCfgPublicAdmin()]);
    }
    case 'billing_orders': {
        requireAdmin();
        $os = array_map(function ($o) { unset($o['token'], $o['ip']); return $o; }, blOrders(300, tidNorm((string)($_GET['tenant_id'] ?? ''))));
        jsonOut(['ok' => true, 'orders' => $os]);
    }
    case 'billing_link': {
        requireAdmin();
        $id = tidNorm((string)(bodyInput()['tenant_id'] ?? ($_GET['tenant_id'] ?? '')));
        foreach (readJson(TENANTS_FILE, []) as $t) {
            if (!tidEq($t['tenant_id'] ?? '', $id)) continue;
            list($elig, $why) = blEligible($t);
            jsonOut(['ok' => true, 'url' => blPayBase() . '/bayar/?t=' . blToken($t), 'eligible' => $elig, 'reason' => $why, 'enabled' => !empty(blCfg()['enabled'])]);
        }
        jsonOut(['ok' => false, 'error' => 'Tenant tidak ditemukan.'], 404);
    }
    case 'billing_recheck': {
        requireAdmin();
        $o = blOrderLoad((string)(bodyInput()['order'] ?? ''));
        if (!$o) jsonOut(['ok' => false, 'error' => 'Pesanan tidak ditemukan.'], 404);
        if (($o['status'] ?? '') === 'paid') jsonOut(['ok' => true, 'message' => 'Sudah lunas.']);
        $s = blDuitkuStatus($o['id']);
        if (!$s) jsonOut(['ok' => false, 'error' => 'Duitku tidak merespons.'], 502);
        if (($s['statusCode'] ?? '') === '00' && (int)($s['amount'] ?? 0) === (int)$o['amount']) {
            blMarkPaid($o['id'], ['reference' => (string)($s['reference'] ?? ''), 'resultCode' => '00', 'source' => 'admin-recheck']);
            jsonOut(['ok' => true, 'message' => 'Lunas — paket tenant sudah diterapkan.']);
        }
        jsonOut(['ok' => true, 'message' => 'Status Duitku: ' . ($s['statusMessage'] ?? $s['statusCode'] ?? '?') . ' (belum lunas).']);
    }

"""

def index(s):
    s = rep(s, "require_once __DIR__ . '/classify-lib.php';   // v1.2.138: filter-topik\n",
               "require_once __DIR__ . '/classify-lib.php';   // v1.2.138: filter-topik\n"
               "require_once __DIR__ . '/billing-lib.php';" + C + " (Duitku)\n", 'require')
    s = rep(s, "            'cap_info'         => $capInfo,\n",
               "            'cap_info'         => $capInfo,\n"
               "            'pay_url'          => $tenant ? blPayUrl($tenant) : '',   // " + TAG + " — tautan bayar/perpanjang mandiri\n", 'pay_url')
    s = rep(s, "    /* v1.2.138: filter-topik: klasifikasi topik chat WA untuk tenant",
               ACTIONS.replace('v1.2.173: bayar-mandiri — pembayaran Duitku', TAG + ' — pembayaran Duitku', 1).lstrip('\n') + "    /* v1.2.138: filter-topik: klasifikasi topik chat WA untuk tenant", 'actions')
    return s

def signup(s):
    s = rep(s, "            'upgrade_url' => (string)($cfg['upgrade_url'] ?? ''), 'tier' => trialTier($t)];   // v1.2.172: trial-paket",
               "            'upgrade_url' => (function_exists('blPayUrl') && ($pu = blPayUrl($t)) !== '') ? $pu : (string)($cfg['upgrade_url'] ?? ''), 'tier' => trialTier($t)];   // v1.2.172: trial-paket;" + " " + TAG, 'trial payload')
    s = rep(s, "        $tr = $t['trial'] ?? null; $phone = (string)($t['signup']['phone'] ?? '');\n",
               "        $tr = $t['trial'] ?? null; $phone = (string)($t['signup']['phone'] ?? '');\n"
               "        $up = (function_exists('blPayUrl') && ($pu = blPayUrl($t)) !== '') ? \"\\nBerlangganan online: \" . $pu : ($cfg['upgrade_url'] !== '' ? \"\\nBerlangganan: \" . $cfg['upgrade_url'] : \"\\nBalas pesan ini untuk berlangganan.\");" + C + "\n", 'reminder url')
    return s

def cron(s):
    s = rep(s, "require_once __DIR__ . '/classify-lib.php';   // v1.2.138: filter-topik\n",
               "require_once __DIR__ . '/classify-lib.php';   // v1.2.138: filter-topik\n"
               "require_once __DIR__ . '/billing-lib.php';" + C + "\n", 'require')
    s = rep(s, "'expires_at' => (string)($t['expires_at'] ?? '')], JSON_UNESCAPED_UNICODE),   // v1.2.111",
               "'expires_at' => (string)($t['expires_at'] ?? ''), 'pay_url' => blPayUrl($t)], JSON_UNESCAPED_UNICODE),   // v1.2.111;" + " " + TAG, 'lic header')
    s = rep(s, "if ($only === '') { try { $rs = suTrialReminders(",
               "if ($only === '') { try { $rb = blRenewReminders($tenants, $dry); if ($rb && !empty($args['v'])) echo 'pengingat perpanjangan: ' . implode(', ', $rb) . \"\\n\"; } catch (\\Throwable $e) { error_log('renew reminders: ' . $e->getMessage()); } }" + C + "\n"
               "if ($only === '') { try { $rs = suTrialReminders(", 'renew')
    return s

def admin(s):
    s = rep(s, '  <div class="card"><!-- v1.2.138: filter-topik -->\n', open(SRC + '/files/admin-card.html', encoding='utf-8').read() + '  <div class="card"><!-- v1.2.138: filter-topik -->\n', 'card')
    s = rep(s, "loadSignupCfg();\n// v1.2.138: filter-topik\n", "loadSignupCfg();\n" + open(SRC + '/files/admin-js.js', encoding='utf-8').read() + "// v1.2.138: filter-topik\n", 'js')
    s = rep(s, """Masuk sebagai Super Admin ↗</button></div>`;""",
               """Masuk sebagai Super Admin ↗</button><button type="button" class="ghost" onclick="billingLink('${esc(t.tenant_id)}')">Salin link bayar</button><!-- """ + TAG + """ --></div><div id="m_bill" class="hint" style="margin:-4px 0 10px"></div>`;""", 'modal btn')
    return s

patch(P + '/backend/index.php', index)
patch(P + '/backend/signup-lib.php', signup)
patch(P + '/backend/cron-tick.php', cron)
patch(P + '/admin/index.html', admin)
