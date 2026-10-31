#!/usr/bin/env python3
r"""v1.2.133 kb-cari: kolom Cari entri Knowledge Base dipindah dari toolbar ke atas daftar entri
(di atas angka "N entri"). Input yang sama dipindah (bukan dibuat ulang) tiap renderKb supaya
fokus & posisi kursor tidak hilang saat mengetik.
Pakai: python3 patch_v12133_kb_cari.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.132)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.133: kb-cari'
NEED = 'v1.2.132: kb-url'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def rep(s, old, new, rel):
    n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:100]); return s.replace(old, new)
def patch(rel, fn):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    assert NEED in s, rel + ': butuh v1.2.132'
    s2 = fn(s, rel); assert TAG in s2, rel
    shutil.copy2(p, p + '.bak-v12133-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s2); print('OK', rel)

def f_api(s, rel):
    return rep(s, "define('DEI_VERSION', 'v1.2.132');   // v1.2.132: kb-url",
                  "define('DEI_VERSION', 'v1.2.133');   // " + TAG, rel)

def f_js(s, rel):
    s = rep(s, "    var wrap = $('#kbList');\n    wrap.innerHTML =\n",
               "    var wrap = $('#kbList');\n"
               "    var _ks = $('#kbSearch'), _ksFoc = _ks && document.activeElement === _ks, _ksPos = _ks ? _ks.selectionStart : 0;   // " + TAG + "\n"
               "    wrap.innerHTML =\n", rel)
    s = rep(s, "        '<div class=\"kb-side\"><div class=\"kb-count\">' + shown.length + ' entri</div>",
               "        '<div class=\"kb-side\"><div class=\"kb-search\"></div><div class=\"kb-count\">' + shown.length + ' entri" +
               "' + (term ? ' cocok dari ' + kbData.length : '') + '</div>", rel)
    s = rep(s, "    $$('#kbList .kb-chip').forEach(function (c) { c.onclick = function () { kbCatFilter = c.dataset.cat; kbSelId = null; renderKb(); }; });\n",
               "    var _kslot = wrap.querySelector('.kb-search');   // " + TAG + ": pindahkan input yang sama (fokus & kursor tetap)\n"
               "    if (_ks && _kslot) { _kslot.appendChild(_ks); if (_ksFoc) { _ks.focus(); try { _ks.setSelectionRange(_ksPos, _ksPos); } catch (e) {} } }\n"
               "    $$('#kbList .kb-chip').forEach(function (c) { c.onclick = function () { kbCatFilter = c.dataset.cat; kbSelId = null; renderKb(); }; });\n", rel)
    return s

def f_html(s, rel):
    s = rep(s, '<script src="app.js?v=1.2.132"></script><!-- v1.2.132: kb-url -->',
               '<script src="app.js?v=1.2.133"></script><!-- ' + TAG + ' -->', rel)
    s = rep(s, '          <div class="row" style="flex:1"><input type="text" id="kbSearch" placeholder="Cari entri..."></div>\n', '', rel)
    s = rep(s, '      <div id="kbList"></div>\n',
               '      <div id="kbSearchHold" style="display:none"><input type="text" id="kbSearch" placeholder="Cari entri..." autocomplete="off"></div><!-- ' + TAG + ': dipindah renderKb ke atas daftar -->\n'
               '      <div id="kbList"></div>\n', rel)
    s = rep(s, '  .kb-count{padding:10px 14px;font-size:12px;color:var(--muted);border-bottom:1px solid var(--line);background:#fafafd}\n',
               '  .kb-count{padding:10px 14px;font-size:12px;color:var(--muted);border-bottom:1px solid var(--line);background:#fafafd}\n'
               '  .kb-search{padding:10px 12px 0;background:#fafafd}   /* ' + TAG + ' */\n'
               '  .kb-search input{width:100%;box-sizing:border-box}\n'
               '  .kb-search:empty{display:none}\n', rel)
    return s

patch('api/index.php', f_api)
patch('dashboard/chatbot-ai/app.js', f_js)
patch('dashboard/chatbot-ai/index.html', f_html)
