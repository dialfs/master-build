#!/usr/bin/env python3
"""v1.2.93 — "Aktifkan Bot WhatsApp" OFF = hanya balasan AI otomatis yang mati.
Pesan masuk & balasan dari HP (WA Business / WAHA) tetap masuk dashboard; agent tetap bisa membalas.
Pemakaian: python3 patch_v1293_wa_bot_off.py <root dei-tenant>   (idempoten; backup *.bak-v1293-*)"""
import sys, os, time, shutil
TEN = sys.argv[1]
STAMP = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.93: wa-bot-off'

def patch(root, rel, pairs):
    p = os.path.join(root, rel)
    s = open(p, encoding='utf-8').read()
    if MARK in s: print('sudah dipatch:', rel); return
    shutil.copy2(p, p + '.bak-v1293-' + STAMP)
    for old, new in pairs:
        n = s.count(old)
        if n != 1: sys.exit(f'GAGAL {rel}: anchor {n}x:\n{old[:200]}')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

patch(TEN, 'api/index.php', [
    ("define('DEI_VERSION', 'v1.2.92');", "define('DEI_VERSION', 'v1.2.93');"),
    # mode balasan efektif: Manual bila dipilih di Tim, ATAU bot WhatsApp dimatikan
    ("function deiReplyMode($s = null) {\n"
     "    if ($s === null) {\n"
     "        if (!isset($GLOBALS['dei_reply_mode_cache'])) {\n"
     "            $s = getSettings();\n"
     "            $GLOBALS['dei_reply_mode_cache'] = ((($s['reply']['mode'] ?? 'ai') === 'manual') ? 'manual' : 'ai');\n"
     "        }\n"
     "        return $GLOBALS['dei_reply_mode_cache'];\n"
     "    }\n"
     "    return ((($s['reply']['mode'] ?? 'ai') === 'manual') ? 'manual' : 'ai');\n"
     "}\n",
     "function deiReplyMode($s = null) {\n"
     "    if ($s === null) {\n"
     "        if (!isset($GLOBALS['dei_reply_mode_cache'])) {\n"
     "            $GLOBALS['dei_reply_mode_cache'] = deiReplyMode(getSettings());\n"
     "        }\n"
     "        return $GLOBALS['dei_reply_mode_cache'];\n"
     "    }\n"
     "    // " + MARK + " — toggle \"Aktifkan Bot WhatsApp\" mati = AI tidak membalas (perilaku Mode Manual);\n"
     "    // pesan masuk & balasan dari HP tetap tercatat di dashboard.\n"
     "    if (empty($s['whatsapp_api']['enabled'])) return 'manual';\n"
     "    return deiReplyModeSetting($s);\n"
     "}\n"
     "/* " + MARK + ": pilihan Mode Balasan di menu Tim apa adanya (tanpa memperhitungkan toggle bot) */\n"
     "function deiReplyModeSetting($s) { return ((($s['reply']['mode'] ?? 'ai') === 'manual') ? 'manual' : 'ai'); }\n"
     "/* " + MARK + ": nomor WhatsApp tersambung (kredensial ada), lepas dari status bot AI */\n"
     "function deiWaConnected($wa) {\n"
     "    $wa = is_array($wa) ? $wa : [];\n"
     "    $p = (string)($wa['provider'] ?? 'meta');\n"
     "    if ($p === 'waha')   return trim((string)($wa['waha_url'] ?? '')) !== '';\n"
     "    if ($p === 'fonnte') return !empty($wa['fonnte_token']);\n"
     "    return !empty($wa['access_token']) && !empty($wa['phone_number_id']);\n"
     "}\n"),
    # webhook tidak lagi dibuang saat bot mati
    ("    if (!is_array($payload)) return;\n    if (!($wa['enabled'] ?? false)) return;\n",
     "    if (!is_array($payload)) return;\n    // " + MARK + ": tetap diproses walau bot mati (AI diam lewat deiReplyMode)\n"),
    ("        if (!($wa['enabled'] ?? false)) { if (!$earlyAck) { echo 'EVENT_RECEIVED'; } exit; }\n",
     "        // " + MARK + ": bot mati tidak lagi membuang pesan — tetap dicatat, AI tidak membalas\n"),
    ("        if (!is_array($evt) || ($wa['provider'] ?? 'meta') !== 'waha' || !($wa['enabled'] ?? false)) { echo 'OK'; exit; }",
     "        if (!is_array($evt) || ($wa['provider'] ?? 'meta') !== 'waha') { echo 'OK'; exit; }   // " + MARK),
    ("        if (!($wa['enabled'] ?? false))               { if (!$earlyAck) { echo 'OK'; } exit; }\n",
     "        // " + MARK + ": bot mati tetap dicatat (Mode Manual)\n"),
    # status "tersambung" untuk fitur manual (kontak/ucapan, onboarding, stats pusat)
    ("        'wa_provider'           => (function () { $w = (array)(getSettings()['whatsapp_api'] ?? []); return !empty($w['enabled']) ? (string)($w['provider'] ?? 'meta') : 'off'; })(),",
     "        'wa_provider'           => (function () { $w = (array)(getSettings()['whatsapp_api'] ?? []); return (!empty($w['enabled']) || deiWaConnected($w)) ? (string)($w['provider'] ?? 'meta') : 'off'; })(),   // " + MARK),
    ("            'wa_enabled'        => !empty($s['whatsapp_api']['enabled']),\n",
     "            'wa_enabled'        => !empty($s['whatsapp_api']['enabled']) || deiWaConnected($s['whatsapp_api'] ?? []),   // " + MARK + "\n"),
    ("              : (!empty($wa['enabled']) && (!empty($wa['access_token']) || !empty($wa['fonnte_token'])));",
     "              : deiWaConnected($wa);   // " + MARK),
    ("            'reply_mode'  => deiReplyMode($s),\n            'team'",
     "            'reply_mode'  => deiReplyModeSetting($s),   // " + MARK + "\n            'team'"),
    ("            'wa_enabled'  => !empty($s['whatsapp_api']['enabled']),\n        ]);",
     "            'wa_enabled'  => !empty($s['whatsapp_api']['enabled']) || deiWaConnected($s['whatsapp_api'] ?? []),   // " + MARK + "\n        ]);"),
])

patch(TEN, 'dashboard/chatbot-ai/index.html', [
    ('<div class="tt">Aktifkan Bot WhatsApp</div><div class="td">Balas otomatis pesan WhatsApp yang masuk.</div>',
     '<div class="tt">Aktifkan Bot WhatsApp</div><div class="td">Balas otomatis pesan WhatsApp yang masuk dengan AI. Saat OFF, pesan masuk &amp; balasan dari HP (WhatsApp Business) tetap masuk dashboard dan agent tetap bisa membalas — hanya balasan AI yang mati.</div><!-- ' + MARK + ' -->'),
    ('<script src="app.js?v=1.2.92"></script>', '<script src="app.js?v=1.2.93"></script>'),
])

patch(TEN, 'dashboard/chatbot-ai/app.js', [
    ("      if (r.wa_enabled === false) msg += '<br>' + ico('octagon-alert', 13) + ' \"Aktifkan Bot WhatsApp\" di menu Widget &amp; API masih mati — pesan masuk tidak akan tercatat.';",
     "      if (r.wa_enabled === false) msg += '<br>' + ico('octagon-alert', 13) + ' Nomor WhatsApp belum tersambung di menu Widget &amp; API — pesan masuk belum bisa tercatat.';   // " + MARK),
])
print('selesai')
