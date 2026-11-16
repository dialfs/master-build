#!/usr/bin/env python3
"""v1.2.194 (asisten-bantuan): Asisten Bantuan di dalam Pusat Bantuan dashboard tenant.
Tenant (paket: api/index.php, dashboard/chatbot-ai/app.js, dashboard/chatbot-ai/index.html):
- action support_info (semua peran): { enabled, base, ctx } — konteks disusun server (tenant, bisnis, paket, versi, lisensi, WA)
- Pusat Bantuan: tombol "Tanya Asisten", panel chat ke tenant Support, tombol "Tunjukkan di layar" / "Buka menu" di bawah jawaban,
  tautan WhatsApp tim DEI (dari pengaturan widget tenant Support)
Hanya tampil bila pusat menyalakan tombol Bantuan (Admin Pusat > Pengaturan > Asisten Support). Butuh v1.2.193.
Idempoten.  Pakai: patch_v12194.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
D = os.path.dirname(os.path.abspath(__file__))
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
T = H + '/dei-tenant'
TAG = 'v1.2.194: asisten-bantuan'; NEED = 'v1.2.193: asisten-support'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12194-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)

PHP_FN = r'''/* v1.2.194: asisten-bantuan — konteks penanya disusun di server (bukan diketik browser), lalu dibersihkan dengan aturan yang sama. */
function deiSupportCtxBuild($s, $u) {
    $cs = $s['central_server'] ?? [];
    $c = ['tenant_id' => (string)($cs['tenant_id'] ?? ''),
          'business'  => trim((string)($s['bot']['persona_company'] ?? '')) ?: trim((string)($s['bot']['bot_name'] ?? '')),
          'user'      => (string)($u['name'] ?? ($u['username'] ?? '')),
          'role'      => (string)($u['role'] ?? ''),
          'version'   => DEI_VERSION];
    try {
        $cap = getCapStatus($s);
        $tr = is_array($cap['trial'] ?? null) ? $cap['trial'] : null;
        $tier = strtolower(trim((string)($cap['tier'] ?? '')));
        if ($tr) { $c['tier'] = 'trial'; $c['trial_tier'] = (($tr['tier'] ?? '') === 'growth') ? 'growth' : 'starter'; $c['trial_days_left'] = (int)($tr['days_left'] ?? 0); }
        elseif ($tier !== '') $c['tier'] = $tier;
        if (isset($cap['pct']) && ($tier !== '' || $tr)) $c['usage_pct'] = round((float)$cap['pct'], 1);
    } catch (\Throwable $e) { error_log('deiSupportCtxBuild cap: ' . $e->getMessage()); }
    try {
        $lic = getLicenseStatus($s);
        if (($lic['source'] ?? '') !== 'no-central') {
            $c['license_status'] = (string)($lic['status'] ?? '');
            if (isset($lic['days_left']) && $lic['days_left'] !== null && empty($c['trial_tier'])) $c['days_left'] = (int)$lic['days_left'];
        }
    } catch (\Throwable $e) { error_log('deiSupportCtxBuild lic: ' . $e->getMessage()); }
    $latest = (string)(readJson(RELNOTIFY_FILE, [])['last_notified'] ?? '');
    if (preg_match('/^v\d+\.\d+\.\d+$/', $latest) && version_compare(ltrim($latest, 'v'), ltrim(DEI_VERSION, 'v'), '>')) $c['latest'] = $latest;   // hanya bila memang ada yang lebih baru
    $w = (array)($s['whatsapp_api'] ?? []);
    $c['wa_provider'] = (!empty($w['enabled']) || deiWaConnected($w)) ? (string)($w['provider'] ?? 'meta') : 'off';
    return deiSupportCtxClean($c);
}
'''

PHP_CASE = r'''    case 'support_info': {   // v1.2.194: asisten-bantuan — alamat tenant Support + konteks penanya untuk Pusat Bantuan
        $spU = requireAuth(['super_admin', 'admin', 'supervisor', 'wa_agent']);
        $spI = deiSupportInfo();
        if (!$spI['enabled'] || $spI['base'] === '') jsonOut(['ok' => true, 'enabled' => false]);
        jsonOut(['ok' => true, 'enabled' => true, 'base' => $spI['base'], 'ctx' => deiSupportCtxBuild(getSettings(), is_array($spU) ? $spU : [])]);
        break;
    }
'''

CSS = r'''  /* v1.2.194: asisten-bantuan */
  #helpRoot .help-ask{margin:0 20px 8px}
  #helpRoot .help-ask[hidden]{display:none}
  #helpRoot .help-ask button{width:100%;display:flex;align-items:center;gap:8px;border:1px dashed var(--brand-line);background:#fff;color:var(--brand);border-radius:11px;padding:10px 14px;font:inherit;font-size:13.5px;font-weight:600;cursor:pointer;text-align:left}
  #helpRoot .help-ask button:hover{background:var(--brand-tint);border-style:solid}
  #helpRoot .help-chat{display:none;flex-direction:column;flex:1;min-height:0}
  #helpRoot .help-box.chat .help-chat{display:flex}
  #helpRoot .help-box.chat .help-search,#helpRoot .help-box.chat .help-ask,#helpRoot .help-box.chat .help-res,#helpRoot .help-box.chat .help-foot{display:none}
  #helpRoot .help-box.chat{height:84vh}
  #helpRoot .hc-top{display:flex;align-items:center;gap:10px;padding:0 20px 10px;border-bottom:1px solid var(--line)}
  #helpRoot .hc-top .btn{display:inline-flex;align-items:center;gap:4px}
  #helpRoot .hc-top b{font-size:14px}
  #helpRoot .hc-top small{color:var(--muted);font-size:11.5px;margin-left:auto;text-align:right}
  #helpRoot .hc-list{flex:1;overflow-y:auto;padding:14px 20px;display:flex;flex-direction:column;gap:10px;background:var(--bg)}
  #helpRoot .hc-m{display:flex;flex-direction:column;align-items:flex-start;max-width:88%}
  #helpRoot .hc-m.u{align-self:flex-end;align-items:flex-end}
  #helpRoot .hc-b{background:#fff;border:1px solid var(--line);border-radius:14px 14px 14px 4px;padding:9px 13px;font-size:13.5px;line-height:1.55;color:var(--ink);overflow-wrap:anywhere}
  #helpRoot .hc-m.u .hc-b{background:var(--brand);border-color:var(--brand);color:#fff;border-radius:14px 14px 4px 14px}
  #helpRoot .hc-m.err .hc-b{border-color:#f0c4c4;background:#fff6f6;color:#8a2c2c}
  #helpRoot .hc-typing{color:var(--muted);font-style:italic}
  #helpRoot .hc-acts{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
  #helpRoot .hc-acts button{display:inline-flex;align-items:center;gap:5px;border:1px solid var(--brand-line);background:#fff;color:var(--brand);border-radius:20px;padding:5px 11px;font:inherit;font-size:12.5px;font-weight:600;cursor:pointer;text-align:left}
  #helpRoot .hc-acts button:hover{background:var(--brand-tint)}
  #helpRoot .hc-wa{padding:8px 20px;font-size:12.5px;color:var(--muted);border-top:1px solid var(--line)}
  #helpRoot .hc-wa[hidden]{display:none}
  #helpRoot .hc-in{display:flex;gap:8px;padding:10px 20px max(12px,env(safe-area-inset-bottom));border-top:1px solid var(--line);background:#fff}
  #helpRoot .hc-in textarea{flex:1;resize:none;border:1.5px solid var(--line);border-radius:10px;padding:9px 12px;font:inherit;font-size:14px;height:42px;min-height:42px;max-height:110px;min-width:0}
  #helpRoot .hc-in textarea:focus{outline:none;border-color:var(--brand)}
  @media(max-width:860px){ #helpRoot .help-box.chat{height:100%} #helpRoot .hc-in textarea{font-size:16px} }
'''

# ------------------------------------------------------------------ api/index.php
API = T + '/api/index.php'; s = rd(API)
if TAG in s: print('sudah:', API)
else:
    assert NEED in s, 'butuh v1.2.193'
    a = "function deiSupportSelf() { return deiSupportInfo()['self']; }\n"
    s = rep(s, a, a + PHP_FN, what='deiSupportSelf')
    a = "    case 'support_status': {   // v1.2.193"
    s = rep(s, a, PHP_CASE + a, what='support_status')
    old = "define('DEI_VERSION', 'v1.2.193');   //"
    i = s.index(old)
    s = s[:i] + "define('DEI_VERSION', 'v1.2.194');   // " + TAG + " — Asisten Bantuan di Pusat Bantuan dashboard;" + s[i + len(old):]
    save(API, s)

# ------------------------------------------------------------------ app.js
JS = T + '/dashboard/chatbot-ai/app.js'; s = rd(JS)
if TAG in s: print('sudah:', JS)
else:
    a = ("      if (e.key === 'Enter') { e.preventDefault(); var first = document.querySelector('#helpRes .help-item [data-h=\"show\"]'); if (first) first.click(); }\n"
         "    });\n    return r;\n")
    s = rep(s, a, a.replace("    return r;\n", "    hsMount(r);   // " + TAG + "\n    return r;\n"), what='helpEls return')
    a = "    helpRender();\n    setTimeout(function () { try { $('#helpQ').focus(); } catch (e) {} }, 30);\n"
    s = rep(s, a, "    helpRender();\n    hsOnOpen();   // " + TAG + "\n    setTimeout(function () { try { $('#helpQ').focus(); } catch (e) {} }, 30);\n", what='helpOpen')
    a = "  window.deiHelp = helpOpen;\n"
    s = rep(s, a, a + rd(D + '/hs.js'), what='deiHelp')
    save(JS, s)

# ------------------------------------------------------------------ index.html
HT = T + '/dashboard/chatbot-ai/index.html'; s = rd(HT)
if TAG in s: print('sudah:', HT)
else:
    a = "  #helpRoot .help-foot .btn{display:inline-flex;align-items:center;gap:6px}\n"
    s = rep(s, a, a + CSS, what='css help-foot')
    a = '<script src="app.js?v=1.2.185"></script>'
    s = rep(s, a, '<script src="app.js?v=1.2.194"></script><!-- ' + TAG + ' -->', what='app.js?v')
    save(HT, s)
print('selesai', TAG)
