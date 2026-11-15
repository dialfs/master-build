#!/usr/bin/env python3
"""v1.2.179 notif-putus-wa (TENANT + PUSAT, di atas v1.2.178).
Saat WhatsApp melepas tautan nomor WAHA tenant (logout paksa: WORKING -> SCAN_QR_CODE, bukan diputus dari dashboard),
tenant memanggil pusat (action=wa_down_notify). Pusat mengirim WA dari sesi dei-otp ke:
  1) settings.wa_alert.phone tenant (kolom baru di kartu Koneksi WhatsApp, Admin & Super Admin), atau
  2) nomor billing / nomor pendaftar (signup) di tenants.json.
Tanpa nomor -> Telegram ke tim DEI. Maks 1x per 6 jam per tenant+nomor.
Idempoten: backup -> replace anchor.  Pakai: patch_v12179.py [~/Herd]"""
import os, sys, time, shutil
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
T = H + '/dei-tenant'; P = H + '/dei-pusat'
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HTML = T + '/dashboard/chatbot-ai/index.html'
PB = P + '/backend/index.php'
TAG = 'v1.2.179: notif-putus-wa'; stamp = time.strftime('%Y%m%d-%H%M%S')
NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn, need):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    assert need in s, 'butuh versi sebelumnya: ' + p
    if not NOBAK: shutil.copy2(p, p + '.bak-v12179-' + stamp)
    wr(p, fn(s)); print('OK', p)
C = '   // ' + TAG

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.178');   // v1.2.178:",
               "define('DEI_VERSION', 'v1.2.179');   // " + TAG + " — WA pemberitahuan ke pemilik saat nomor WAHA terputus (perlu scan ulang); v1.2.178:", 'versi')
    # whAlert: logout paksa -> minta pusat kirim WA ke pemilik
    s = rep(s, "        if ($targets) sendPushToUsers($targets, $title, $body, deiDashboardUrl(), 'dei-wa-health');\n",
               "        if ($targets) sendPushToUsers($targets, $title, $body, deiDashboardUrl(), 'dei-wa-health');\n"
               "        if ($kind === 'logout') deiWaDownNotify($label, (string)((whRead($ch)['num'] ?? '') ?: ($wa['waha_number'] ?? '')));" + C + "\n", 'whAlert')
    s = rep(s, "// Pasang ulang konfigurasi sesi (webhook + message.ack). PUT me-restart sesi WAHA beberapa detik.\n",
               "/* " + TAG + ": nomor tenant terputus -> pusat kirim WA (sesi dei-otp) ke settings.wa_alert.phone,\n"
               " * atau nomor billing/pendaftar di pusat. Pusat membatasi 1x / 6 jam per tenant+nomor. */\n"
               "function deiWaDownNotify($label, $num) {\n"
               "    try {\n"
               "        if (!empty($GLOBALS['dei_dry'])) return;\n"
               "        $s = getSettings(); $cs = $s['central_server'] ?? [];\n"
               "        if (empty($cs['url']) || empty($cs['tenant_id']) || empty($cs['license_key'])) return;\n"
               "        $ch = curl_init(rtrim($cs['url'], '/') . '/backend/index.php?action=wa_down_notify');\n"
               "        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 12, CURLOPT_CONNECTTIMEOUT => 5,\n"
               "            CURLOPT_POST => true, CURLOPT_HTTPHEADER => ['Content-Type: application/json'],\n"
               "            CURLOPT_POSTFIELDS => json_encode(['tenant_id' => $cs['tenant_id'], 'license_key' => $cs['license_key'],\n"
               "                'label' => mb_substr((string)$label, 0, 60), 'number' => waNormNum($num),\n"
               "                'phone' => waNormNum($s['wa_alert']['phone'] ?? ''), 'dashboard' => deiDashboardUrl()])]);\n"
               "        $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);\n"
               "        error_log('[wa-down-notify] HTTP ' . $code . ' ' . mb_substr((string)$resp, 0, 200));\n"
               "    } catch (\\Throwable $e) { error_log('wa-down-notify: ' . $e->getMessage()); }\n"
               "}\n"
               "// Pasang ulang konfigurasi sesi (webhook + message.ack). PUT me-restart sesi WAHA beberapa detik.\n", 'fungsi')
    # save_settings: rapikan nomor (semua peran), Admin boleh menyimpan
    s = rep(s, "        // Super Admin: full edit, preserve masked secrets.\n",
               "        if (array_key_exists('wa_alert', $incoming)) {" + C + "\n"
               "            $wp = preg_replace('/\\D/', '', (string)(is_array($incoming['wa_alert']) ? ($incoming['wa_alert']['phone'] ?? '') : ''));\n"
               "            if (strpos($wp, '0') === 0) $wp = '62' . substr($wp, 1); elseif (strpos($wp, '8') === 0) $wp = '62' . $wp;\n"
               "            if ($wp !== '' && (strlen($wp) < 10 || strlen($wp) > 15)) jsonOut(['ok' => false, 'error' => 'Nomor notifikasi WA tidak valid. Contoh: 0812xxxxxxx'], 400);\n"
               "            $incoming['wa_alert'] = ['phone' => $wp];\n"
               "        }\n"
               "        // Super Admin: full edit, preserve masked secrets.\n", 'save normalisasi')
    s = rep(s, "            // Handoff keywords + on/off.\n",
               "            if (isset($incoming['wa_alert'])) $merged['wa_alert'] = $incoming['wa_alert'];" + C + "\n"
               "            // Handoff keywords + on/off.\n", 'save admin')
    return s

def js(s):
    s = rep(s, "      $('#tg_web').checked = tg.notify_web !== false;\n",
               "      $('#tg_web').checked = tg.notify_web !== false;\n"
               "      if ($('#wa_alert_phone')) $('#wa_alert_phone').value = (s.wa_alert && s.wa_alert.phone) || '';" + C + "\n", 'load')
    s = rep(s, "      handoff: hoBlock\n    } };\n",
               "      handoff: hoBlock\n    } };\n"
               "    if ($('#wa_alert_phone')) body.settings.wa_alert = { phone: $('#wa_alert_phone').value.trim() };" + C + "\n", 'save')
    return s

def html(s):
    return rep(s, '        <div class="help" style="margin-top:8px">Jalur tidak resmi (WhatsApp Web)',
        '        <div class="row" style="margin-top:12px"><!-- ' + TAG + ' -->\n'
        '          <label class="fl">Nomor pemberitahuan bila WA terputus</label>\n'
        '          <input type="tel" id="wa_alert_phone" class="mono" placeholder="Kosong = nomor pendaftar akun (mis. 0812xxxxxxx)">\n'
        '          <div class="help">Kalau WhatsApp melepas tautan nomor chatbot (perlu scan QR ulang), pemberitahuan dikirim lewat WhatsApp dari nomor DEI ke nomor ini. Pakai nomor lain dari nomor chatbot. Kosongkan untuk memakai nomor pendaftar akun. Simpan dengan tombol <b>Simpan Semua</b> di bawah.</div>\n'
        '        </div>\n'
        '        <div class="help" style="margin-top:8px">Jalur tidak resmi (WhatsApp Web)', 'kartu')

def pusat(s):
    s = rep(s, " *   - release_notes     daftar catatan rilis (butuh tenant_id + license_key)\n",
               " *   - release_notes     daftar catatan rilis (butuh tenant_id + license_key)\n"
               " *   - wa_down_notify    tenant: nomor WAHA terputus -> WA ke pemilik lewat sesi OTP (" + TAG + ")\n", 'doc')
    s = rep(s, "    case 'report_back': {\n",
               "    /* " + TAG + ": nomor WAHA tenant terputus (logout paksa) -> WA ke pemilik dari sesi OTP pusat.\n"
               "     * Tujuan: phone dari tenant (settings.wa_alert) > billing_phone > signup.phone. Maks 1x / 6 jam per tenant+nomor. */\n"
               "    case 'wa_down_notify': {\n"
               "        $body = bodyInput();\n"
               "        $tenantId = trim((string)($body['tenant_id'] ?? '')); $licenseKey = trim((string)($body['license_key'] ?? ''));\n"
               "        if ($tenantId === '' || $licenseKey === '') jsonOut(['ok' => false, 'error' => 'tenant_id & license_key wajib.'], 400);\n"
               "        $tenant = null;\n"
               "        foreach (readJson(TENANTS_FILE, []) as $t) { if (tidEq($t['tenant_id'] ?? '', $tenantId)) { $tenant = $t; break; } }\n"
               "        if (!$tenant) jsonOut(['ok' => false, 'error' => 'Tenant tidak terdaftar di server pusat.'], 404);\n"
               "        if (!hash_equals((string)($tenant['license_key'] ?? ''), $licenseKey)) jsonOut(['ok' => false, 'error' => 'License key tidak cocok.'], 403);\n"
               "        $tid = strtolower((string)$tenant['tenant_id']); $name = (string)($tenant['name'] ?? $tid);\n"
               "        $label = mb_substr(trim(strip_tags((string)($body['label'] ?? ''))), 0, 60);\n"
               "        $num = preg_replace('/\\D/', '', (string)($body['number'] ?? ''));\n"
               "        $phone = suPhone((string)($body['phone'] ?? ''));\n"
               "        if ($phone === '') $phone = suPhone((string)($tenant['billing_phone'] ?? ''));\n"
               "        if ($phone === '') $phone = suPhone((string)($tenant['signup']['phone'] ?? ''));\n"
               "        // batas 1x / 6 jam per tenant+nomor\n"
               "        $rf = DATA_DIR . '/wa-down-notify.json'; $key = $tid . '|' . ($num !== '' ? $num : $label); $now = time();\n"
               "        $fp = @fopen($rf, 'c+'); $sent = [];\n"
               "        if ($fp) { flock($fp, LOCK_EX); $sent = json_decode((string)stream_get_contents($fp), true); if (!is_array($sent)) $sent = []; }\n"
               "        foreach ($sent as $k => $ts) if ((int)$ts < $now - 86400) unset($sent[$k]);\n"
               "        if ((int)($sent[$key] ?? 0) > $now - 6 * 3600) { if ($fp) { flock($fp, LOCK_UN); fclose($fp); } jsonOut(['ok' => true, 'sent' => false, 'reason' => 'throttled']); }\n"
               "        $sent[$key] = $now;\n"
               "        if ($fp) { ftruncate($fp, 0); rewind($fp); fwrite($fp, json_encode($sent)); fflush($fp); flock($fp, LOCK_UN); fclose($fp); }\n"
               "        $numTxt = $num !== '' ? ' ' . (strpos($num, '62') === 0 ? '0' . substr($num, 2) : $num) : '';\n"
               "        $lbl = ($label !== '' && $label !== 'Nomor utama' && preg_replace('/\\D/', '', $label) !== $num) ? ' (' . $label . ')' : '';\n"
               "        if ($phone === '') {\n"
               "            suTelegram(\"Nomor WA{$numTxt}{$lbl} tenant {$name} ({$tid}) terputus (perlu scan QR ulang). Tidak ada nomor pemberitahuan pemilik.\");\n"
               "            jsonOut(['ok' => true, 'sent' => false, 'reason' => 'no_phone']);\n"
               "        }\n"
               "        $dash = suTenantDashUrl($tenant);\n"
               "        if ($dash === '') { $du = trim((string)($body['dashboard'] ?? '')); if (preg_match('#^https://[^\\s]+$#', $du)) $dash = $du; }\n"
               "        $txt = \"⚠️ *Nomor WhatsApp chatbot {$name} terputus*{$lbl}\\n\\n\"\n"
               "             . \"WhatsApp melepas tautan nomor{$numTxt}, jadi bot berhenti membalas chat di nomor itu.\\n\\n\"\n"
               "             . \"Cara menyambungkan lagi: buka dashboard › Widget & API › Koneksi WhatsApp › *Hubungkan (scan QR)*, lalu scan dari HP nomor tersebut (WhatsApp › Perangkat Tertaut).\"\n"
               "             . ($dash !== '' ? \"\\n{$dash}\" : '')\n"
               "             . \"\\n\\n_Pesan otomatis DEI Chatbot._\";\n"
               "        list($ok, $err) = suWahaSend(suCfg(), $phone, $txt);\n"
               "        if (!$ok) suTelegram(\"Gagal kirim WA pemberitahuan putus ke {$name} ({$tid}) — {$err}\");\n"
               "        jsonOut(['ok' => true, 'sent' => (bool)$ok, 'to' => suPhoneMask($phone)]);\n"
               "    }\n\n"
               "    case 'report_back': {\n", 'case')
    return s

patch(API, api, "define('DEI_VERSION', 'v1.2.178');")
patch(JS, js, "tg.notify_web")
patch(HTML, html, 'id="fonConnCard"')
patch(PB, pusat, "case 'release_notes'")
