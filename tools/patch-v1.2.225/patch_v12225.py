#!/usr/bin/env python3
"""v1.2.225 (es-coex): Embedded Signup coexistence siap dipakai banyak tenant di satu Meta App.
- wa_es_exchange: verify_token disiapkan & disimpan dulu, lalu subscribe app ke WABA dengan
  override_callback_uri = webhook tenant ini (fallback: subscribe biasa).
- Setelah onboarding otomatis minta sinkron kontak (smb_app_state_sync) & riwayat chat 6 bulan (history).
- API baru wa_es_sync + tombol "Sinkron ulang" (Super Admin) untuk mengulang dalam 24 jam.
- FB.login extras: sessionInfoVersion '3'.
Butuh v1.2.224. Idempoten. Pakai: patch_v12225.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H + '/dei-tenant'
TD = os.path.dirname(os.path.abspath(__file__))
TAG = 'v1.2.225: es-coex'; NEED = 'v1.2.224: kontak-manual'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12225-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
rd = lambda f: open(os.path.join(TD, 'src', f), encoding='utf-8').read()
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API)
else:
    assert NEED in s, 'v1.2.224 belum terpasang di ' + API
    s = rep(s, "define('DEI_VERSION', 'v1.2.224');   // v1.2.224:",
            "define('DEI_VERSION', 'v1.2.225');   // " + TAG + " — Embedded Signup coexistence: webhook per tenant (override_callback_uri), sinkron kontak & riwayat otomatis, tombol Sinkron ulang; v1.2.224:", what='ver')
    s = rep(s, "function deiSelfApiUrl() {\n", rd('fn225.php') + "function deiSelfApiUrl() {\n", what='fn')
    a = s.index("        // 2) Langganan app ke WABA supaya webhook")
    assert s.index("    case 'wa_es_exchange': {") < a
    b = s.index("    /* ---------- knowledge base (admin only) ---------- */", a)
    s = s[:a] + rd('exch225.php') + "\n" + s[b:]
    save(API, s)

s = open(JS, encoding='utf-8').read()
if TAG in s: print('SUDAH', JS)
else:
    s = rep(s, "extras: { featureType: 'whatsapp_business_app_onboarding' } });",
            "extras: { featureType: 'whatsapp_business_app_onboarding', sessionInfoVersion: '3' } });   // " + TAG, what='extras')
    s = rep(s, "    if (appId) esLoadSdk(appId, version);\n",
            "    if (appId) esLoadSdk(appId, version);\n" + rd('js225.js'), what='sync')
    s = rep(s, "          if (r.warning) toast(r.warning);\n",
            "          if (r.sync && st) st.textContent += ' · Kontak: ' + (r.sync.smb_app_state_sync === 'ok' ? 'diminta' : 'gagal') + ' · Riwayat: ' + (r.sync.history === 'ok' ? 'diminta' : 'gagal');   // " + TAG + "\n"
            "          if (r.warning) toast(r.warning);\n", what='status')
    save(JS, s)

s = open(HT, encoding='utf-8').read()
if TAG in s: print('SUDAH', HT)
else:
    s = rep(s, '<button class="btn" id="btnEsConnect" type="button">Hubungkan WhatsApp (Coexistence)</button>',
            '<button class="btn" id="btnEsConnect" type="button">Hubungkan WhatsApp (Coexistence)</button>\n'
            '            <button class="btn ghost" id="btnEsSync" type="button" title="Ulangi subscribe webhook &amp; sinkron kontak + riwayat (maks. 24 jam setelah terhubung)">Sinkron ulang</button><!-- ' + TAG + ' -->', what='btn')
    s = rep(s, 'Setelah terhubung, subscribe field <code>messages</code>, <code>smb_message_echoes</code>, <code>smb_app_state_sync</code>, <code>history</code> di webhook Meta.',
            'Setelah terhubung, webhook WABA otomatis diarahkan ke dashboard ini dan kontak + riwayat chat 6 bulan ditarik dari HP. Di Meta App, pastikan field <code>messages</code>, <code>smb_message_echoes</code>, <code>smb_app_state_sync</code>, <code>history</code> sudah di-subscribe.<!-- ' + TAG + ' -->', what='help')
    s = rep(s, 'app.js?v=1.2.224', 'app.js?v=1.2.225', what='cachebust')
    save(HT, s)
