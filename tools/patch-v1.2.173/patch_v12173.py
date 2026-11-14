#!/usr/bin/env python3
"""v1.2.173 bayar-mandiri (TENANT): tautan bayar/perpanjang mandiri dari pusat (pay_url) disimpan di data/pay-url.json
(dari check_update, cek manual, dan dorongan X-Dei-License tiap menit). Banner lisensi (akan berakhir / expired / suspended)
dan kartu paket Starter berbayar menampilkan tombol bayar online; trial memakai upgrade_url (dari pusat = tautan bayar).
Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HTML = T + '/dashboard/chatbot-ai/index.html'
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

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.172');   // v1.2.172:",
               "define('DEI_VERSION', 'v1.2.173');   // " + TAG + " — tombol bayar/perpanjang online (Duitku) di banner lisensi & kartu paket; v1.2.172:", 'versi')
    s = rep(s, "function deiTrialNorm($t) {\n",
        "/* " + TAG + " — tautan bayar/perpanjang mandiri dari pusat (check_update › pay_url, X-Dei-License › pay_url). */\n"
        "function deiPayUrlSave($u) {\n"
        "    if (!is_string($u)) return;\n"
        "    $u = substr(trim($u), 0, 300);\n"
        "    if ($u !== '' && !preg_match('#^https?://#i', $u)) return;\n"
        "    $f = DATA_DIR . '/pay-url.json';\n"
        "    if ((readJson($f, [])['url'] ?? null) !== $u) writeJson($f, ['url' => $u, 'at' => time()]);\n"
        "}\n"
        "function deiPayUrl() { return (string)(readJson(DATA_DIR . '/pay-url.json', [])['url'] ?? ''); }\n"
        "function deiTrialNorm($t) {\n", 'helper')
    s = rep(s, "    $data = json_decode($resp, true) ?: [];\n    if (empty($data['ok'])) {\n        // Central explicitly rejected",
               "    $data = json_decode($resp, true) ?: [];\n    if (array_key_exists('pay_url', $data)) deiPayUrlSave($data['pay_url']);" + C + "\n    if (empty($data['ok'])) {\n        // Central explicitly rejected", 'lic refresh')
    s = rep(s, "        $data = json_decode($resp, true) ?: [];\n        $s['central_server']['last_check']  = $now;\n",
               "        $data = json_decode($resp, true) ?: [];\n        if (array_key_exists('pay_url', $data)) deiPayUrlSave($data['pay_url']);" + C + "\n        $s['central_server']['last_check']  = $now;\n", 'manual check')
    s = rep(s, "    $j = is_array($raw) ? $raw : json_decode((string)$raw, true);\n    if (!is_array($j)) return null;\n",
               "    $j = is_array($raw) ? $raw : json_decode((string)$raw, true);\n    if (!is_array($j)) return null;\n    if (array_key_exists('pay_url', $j)) deiPayUrlSave($j['pay_url']);" + C + "\n", 'push')
    s = rep(s, "        $lic = getLicenseStatus($s);\n        jsonOut(['ok' => true, 'license' => $lic]);\n",
               "        $lic = getLicenseStatus($s);\n        $lic['pay_url'] = deiPayUrl();" + C + "\n        jsonOut(['ok' => true, 'license' => $lic]);\n", 'license_status')
    s = rep(s, "'upgrade_url' => $tr ? (string)($tr['upgrade_url'] ?? '') : '']);",
               "'upgrade_url' => ($tr && (string)($tr['upgrade_url'] ?? '') !== '') ? (string)$tr['upgrade_url'] : deiPayUrl(), 'pay_url' => deiPayUrl()]);" + C, 'plan_info')
    return s

def js(s):
    s = rep(s, "  function renderLicenseBanner() {\n",
        "  function licPayLink(lic, txt) {" + C + "\n"
        "    return lic && lic.pay_url ? ' <a href=\"' + esc(lic.pay_url) + '\" target=\"_blank\" rel=\"noopener\" style=\"color:inherit;font-weight:700;white-space:nowrap\">' + (txt || 'Perpanjang online') + ' &rarr;</a>' : '';\n"
        "  }\n"
        "  function renderLicenseBanner() {\n", 'helper')
    s = rep(s, "'<div><b>Lisensi akan berakhir dalam ' + lic.days_left + ' hari.</b> Silakan hubungi vendor untuk perpanjangan.</div>'",
               "'<div><b>Lisensi akan berakhir dalam ' + lic.days_left + ' hari.</b> ' + (lic.pay_url ? 'Perpanjang sekarang supaya bot tetap aktif.' + licPayLink(lic, 'Perpanjang online') : 'Silakan hubungi vendor untuk perpanjangan.') + '</div>'", 'expiring')
    s = rep(s, "        msg += ' Hubungi vendor untuk perpanjangan.';\n",
               "        msg += lic.pay_url ? licPayLink(lic, 'Perpanjang online sekarang') : ' Hubungi vendor untuk perpanjangan.';" + C + "\n", 'expired')
    s = rep(s, "Setelah perpanjangan, isi ulang token Claude/WhatsApp/Telegram di menu Widget &amp; API.</div>'",
               "Setelah perpanjangan, isi ulang token Claude/WhatsApp/Telegram di menu Widget &amp; API.' + licPayLink(lic, 'Perpanjang online') + '</div>'", 'suspended')
    s = rep(s, "' Berlangganan Growth</a>'",
               "' ' + (p.trial ? 'Berlangganan Growth' : 'Naik ke Growth') + '</a>'", 'cta label')
    return s

def html(s):
    return rep(s, '<script src="app.js?v=1.2.172"></script><!-- v1.2.172: trial-paket -->',
                  '<script src="app.js?v=1.2.173"></script><!-- ' + TAG + ' --><!-- v1.2.172: trial-paket -->', 'cache-bust')

patch(API, api)
patch(JS, js)
patch(HTML, html)
