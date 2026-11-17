#!/usr/bin/env python3
"""v1.2.196 (tombol-bantuan): tombol bulat ikon headset di sebelah nama pengguna (bawah sidebar) yang langsung membuka
chat Asisten Bantuan. Berkedip halus 3x saat dashboard dibuka, titik merah saat ada balasan baru dari tim DEI,
tersembunyi bila Asisten Bantuan belum diaktifkan pusat.
Tenant (paket: api/index.php [versi], dashboard/chatbot-ai/app.js, dashboard/chatbot-ai/index.html). Butuh v1.2.195.
Idempoten.  Pakai: patch_v12196.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
T = H + '/dei-tenant'
TAG = 'v1.2.196: tombol-bantuan'; NEED = 'v1.2.195: web-balas'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12196-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)

API = T + '/api/index.php'; s = rd(API)
if TAG in s: print('sudah:', API)
else:
    assert NEED in s, 'butuh v1.2.195'
    old = "define('DEI_VERSION', 'v1.2.195');   //"
    i = s.index(old)
    s = s[:i] + "define('DEI_VERSION', 'v1.2.196');   // " + TAG + " — tombol Bantuan (headset) di sebelah nama pengguna;" + s[i + len(old):]
    save(API, s)

JS = T + '/dashboard/chatbot-ai/app.js'; s = rd(JS)
if TAG in s: print('sudah:', JS)
else:
    assert NEED in s, 'app.js butuh v1.2.195'
    a = "        if (got) { if (isOpen && !HS.busy) hsRender(false); else if (!isOpen) toast('Balasan baru dari tim DEI. Klik Panduan untuk membacanya.'); }\n"
    s = rep(s, a, "        if (got) { if (isOpen && !HS.busy) hsRender(false); else if (!isOpen) { toast('Balasan baru dari tim DEI. Klik tombol Bantuan (ikon headset) di bawah menu.'); if ($('#btnSupport')) $('#btnSupport').classList.add('has-new'); } }   // " + TAG + "\n", what='hsPoll toast')
    a = "  function hsPollSchedule() {\n"
    s = rep(s, a, r'''  /* v1.2.196: tombol-bantuan — tombol headset di sebelah nama pengguna, langsung ke chat Asisten */
  function hsSupInit() {
    var b = $('#btnSupport'); if (!b || b.dataset.wired) return;
    b.dataset.wired = '1';
    b.innerHTML = ico('headphones', 18) + '<i class="dot"></i>';
    b.onclick = function (e) {
      e.stopPropagation();
      b.classList.remove('has-new', 'pulse');
      helpOpen('');
      hsLoad(function (inf) { if (inf.enabled) hsOpenChat(''); });
    };
    hsLoad(function (inf) {
      b.hidden = !inf.enabled;
      if (inf.enabled) b.classList.add('pulse');
    });
  }
  setTimeout(hsSupInit, 0);
''' + a, what='hsPollSchedule')
    save(JS, s)

HT = T + '/dashboard/chatbot-ai/index.html'; s = rd(HT)
if TAG in s: print('sudah:', HT)
else:
    a = '      <div class="nm" id="whoName">—</div>\n      <span class="badge" id="whoRole">—</span>\n'
    s = rep(s, a, '      <div class="who-top"><div class="who-id"><div class="nm" id="whoName">—</div>\n      <span class="badge" id="whoRole">—</span></div>\n'
                  '      <button id="btnSupport" type="button" class="who-sup" hidden title="Bantuan: tanya Asisten atau tim DEI" aria-label="Bantuan"></button></div><!-- ' + TAG + ' -->\n', what='who')
    a = "  .who .badge{"
    s = rep(s, a, "  /* " + TAG + " */\n"
        "  .who-top{display:flex;align-items:center;justify-content:space-between;gap:10px}\n"
        "  .who-id{min-width:0}\n"
        "  .who-id .nm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\n"
        "  .who .who-sup{position:relative;flex-shrink:0;width:40px;height:40px;margin:0;padding:0;border-radius:50%;border:none;background:var(--brand);color:#fff;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 4px 12px rgba(var(--brand-rgb),.35);transition:transform .15s}\n"
        "  .who .who-sup[hidden]{display:none}\n"
        "  .who .who-sup:hover{transform:scale(1.07);color:#fff;border:none}\n"
        "  .who-sup.pulse,.who-sup.has-new{animation:supPulse 2.2s 3}\n"
        "  .who-sup.has-new{animation-iteration-count:infinite}\n"
        "  .who-sup .dot{position:absolute;top:-1px;right:-1px;width:12px;height:12px;border-radius:50%;background:#ef4444;border:2px solid #fff;display:none}\n"
        "  .who-sup.has-new .dot{display:block}\n"
        "  @keyframes supPulse{0%{box-shadow:0 0 0 0 rgba(var(--brand-rgb),.5)}70%{box-shadow:0 0 0 10px rgba(var(--brand-rgb),0)}100%{box-shadow:0 0 0 0 rgba(var(--brand-rgb),0)}}\n" + a, what='css')
    a = '<script src="app.js?v=1.2.195"></script>'
    s = rep(s, a, '<script src="app.js?v=1.2.196"></script><!-- ' + TAG + ' -->', what='app.js?v')
    save(HT, s)
print('selesai', TAG)
