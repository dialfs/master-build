#!/usr/bin/env python3
"""v1.2.73 — brand per instalasi (khusus server sendiri: data/server.php 'brand' => 'haltebus').
Tanpa kunci 'brand' tampilan DEI tidak berubah (warna lama dipindah ke variabel CSS dengan nilai sama).
Pakai: patch_v1273.py <folder dei-chatbot-ai>   (mengubah api/index.php, dashboard index.html, login.html, app.js)
Idempoten."""
import re, sys, pathlib

ROOT = pathlib.Path(sys.argv[1])
API = ROOT / 'api/index.php'
IDX = ROOT / 'dashboard/chatbot-ai/index.html'
LOG = ROOT / 'dashboard/chatbot-ai/login.html'
APP = ROOT / 'dashboard/chatbot-ai/app.js'

def rep(src, old, new, count=1, name=''):
    n = src.count(old)
    if n != count:
        raise SystemExit(f'ANCHOR {name} {n}x (harus {count}): {old[:80]!r}')
    return src.replace(old, new)

# ---------------------------------------------------------------- api/index.php
s = API.read_text(encoding='utf-8')
if 'function deiBrand()' in s:
    print('api: sudah terpasang')
else:
    if 'function deiDebounceCollect(' not in s: raise SystemExit('butuh v1.2.72 dulu')
    s = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.73');", s, count=1)
    s = rep(s, "function deiDb() {\n", r"""/* v1.2.73: BRAND per instalasi (server sendiri). data/server.php:
 *   'brand' => 'haltebus'                       // preset
 *   'brand' => ['preset' => 'haltebus', 'vendor' => '...']   // timpa sebagian
 * Tanpa kunci itu = tampilan DEI apa adanya. Ikon, logo & manifest.json ditimpa per
 * instalasi oleh add-client.sh (berkas itu tidak pernah diganti updater); warna & nama
 * diterapkan saat halaman dimuat lewat action=brand_js. */
function deiBrandPresets() {
    return [
        'haltebus' => [
            'key' => 'haltebus', 'vendor' => 'Haltebus', 'product' => 'Haltebus Chatbot',
            'theme' => '#B32B26',
            'css' => [
                '--brand' => '#B32B26', '--brand-2' => '#E0533F', '--brand-soft' => '#FCEBE8',
                '--brand-line' => '#F1C3BB', '--brand-tint' => '#FDF4F2', '--brand-tint-2' => '#FDEEEA',
                '--brand-mid' => '#C83A30', '--brand-hero' => '#F08A2A',
                '--brand-rgb' => '179,43,38', '--brand-2-rgb' => '224,83,63', '--brand-hero-rgb' => '240,138,42',
            ],
            'c1' => '#B32B26', 'c2' => '#F08A2A',
            'palette' => ['#B32B26', '#E0533F', '#F08A2A', '#D9A066', '#8C1D22', '#F4B183', '#C9584C', '#94a3b8'],
        ],
    ];
}
function deiBrand() {
    static $b = false;
    if ($b === false) {
        $b = null;
        $c = deiServerConf()['brand'] ?? null;
        $p = deiBrandPresets();
        if (is_string($c) && isset($p[$c])) $b = $p[$c];
        elseif (is_array($c)) {
            $base = $p[(string)($c['preset'] ?? '')] ?? [];
            unset($c['preset']);
            $b = array_replace_recursive($base, $c);
            if (empty($b['vendor']) || empty($b['product'])) $b = null;
        }
    }
    return $b;
}
function deiBrandVendor()  { $b = deiBrand(); return $b ? (string)$b['vendor'] : 'DEI'; }
function deiBrandProduct() { $b = deiBrand(); return $b ? (string)$b['product'] : 'DEI Chatbot'; }

function deiDb() {
""", name='deiDb')
    s = rep(s, "'X-Title: DEI Chatbot',", "'X-Title: ' . deiBrandProduct(),   // v1.2.73", name='xtitle')
    s = rep(s, "'Lihat apa yang baru di DEI Chatbot.'", "'Lihat apa yang baru di ' . deiBrandProduct() . '.'", name='push')
    s = rep(s, "'. Hubungi DEI untuk menambah kursi.'", "'. Hubungi ' . deiBrandVendor() . ' untuk menambah kursi.'", name='kursi')
    s = rep(s, "Hubungi DEI untu", "Hubungi ' . deiBrandVendor() . ' untu", name='kuota')
    s = rep(s, "    return $n !== '' ? $n : 'DEI Chatbot';\n", "    return $n !== '' ? $n : deiBrandProduct();   // v1.2.73\n", name='tenantname')
    s = rep(s, "    case 'cron_tick': {\n", r"""    /* ---------- PUBLIC (v1.2.73): brand per instalasi untuk dashboard ----------
     * Dimuat sinkron di <head> index.html/login.html. Tanpa brand: hanya `window.DEI_BRAND=null`. */
    case 'brand_js': {
        header('Content-Type: application/javascript; charset=utf-8');
        header('Cache-Control: no-cache');
        $b = deiBrand();
        if (!$b) { echo "window.DEI_BRAND=null;\n"; exit; }
        $css = ':root{';
        foreach ((array)($b['css'] ?? []) as $k => $v) {
            if (preg_match('/^--[a-z0-9-]+$/', (string)$k) && preg_match('/^[#0-9a-zA-Z,. ()%-]+$/', (string)$v)) $css .= $k . ':' . $v . ';';
        }
        $css .= '}';
        $pub = ['key' => $b['key'] ?? '', 'vendor' => $b['vendor'], 'product' => $b['product'], 'theme' => $b['theme'] ?? '',
                'c1' => $b['c1'] ?? '', 'c2' => $b['c2'] ?? '', 'palette' => array_values((array)($b['palette'] ?? []))];
        $J = JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG;
        echo 'window.DEI_BRAND=' . json_encode($pub, $J) . ";\n";
        echo 'document.write(' . json_encode('<style id="dei-brand-css">' . $css . '</style>', $J) . ");\n";
        echo <<<'JS'
(function (B) {
  function swap(t) { return String(t).replace(/DEI Chatbot/g, B.product).replace(/\bDEI\b/g, B.vendor); }
  document.title = swap(document.title);
  function apply() {
    document.title = swap(document.title);
    var m = document.querySelector('meta[name="theme-color"]'); if (m && B.theme) m.setAttribute('content', B.theme);
    var el = document.querySelectorAll('[data-brand-text]'); for (var i = 0; i < el.length; i++) el[i].innerHTML = swap(el[i].innerHTML);
    var im = document.querySelectorAll('img[alt="DEI"]'); for (var j = 0; j < im.length; j++) im[j].alt = B.vendor;
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply); else apply();
})(window.DEI_BRAND);
JS;
        exit;
    }

    case 'cron_tick': {
""", name='brandjs')
    API.write_text(s, encoding='utf-8')
    print('api: OK')

# ---------------------------------------------------------------- HTML
LOADER = ("<script>/* v1.2.73: brand per instalasi (DEI: kosong) */(function(){var p=location.pathname,"
          "i=p.indexOf('/dashboard/chatbot-ai'),b=i>=0?p.slice(0,i):p.replace(/\\/[^\\/]*$/,'');"
          "document.write('<script src=\"'+b+'/api/index.php?action=brand_js\"><\\/script>');})();</script>\n")

def css_vars(h, root_old, root_new):
    h = rep(h, root_old, '@@ROOT@@', name='root')
    h = h.replace('#cbc6f3', 'var(--brand-line)').replace('#f6f5fd', 'var(--brand-tint)').replace('#f1effd', 'var(--brand-tint-2)')
    h = h.replace('rgba(20,3,131,', 'rgba(var(--brand-rgb),').replace('rgba(59,47,184,', 'rgba(var(--brand-2-rgb),')
    h = h.replace('rgba(91,79,224,', 'rgba(var(--brand-hero-rgb),').replace('#5b4fe0', 'var(--brand-hero)').replace('#2a1fa8', 'var(--brand-mid)')
    h = h.replace('linear-gradient(135deg,#140383 0%', 'linear-gradient(135deg,var(--brand) 0%').replace('#3b2fb8 100%)', 'var(--brand-2) 100%)')
    h = h.replace('background:#eceaf9', 'background:var(--brand-soft)')
    return h.replace('@@ROOT@@', root_new)

h = IDX.read_text(encoding='utf-8')
if 'action=brand_js' in h:
    print('index.html: sudah terpasang')
else:
    h = css_vars(h, "    --brand:#140383;--brand-2:#3b2fb8;--brand-soft:#eceaf9;\n",
                 "    --brand:#140383;--brand-2:#3b2fb8;--brand-soft:#eceaf9;\n"
                 "    /* v1.2.73: warna yang dulu ditulis langsung — nilai sama, bisa ditimpa brand per instalasi */\n"
                 "    --brand-line:#cbc6f3;--brand-tint:#f6f5fd;--brand-tint-2:#f1effd;--brand-mid:#2a1fa8;--brand-hero:#5b4fe0;\n"
                 "    --brand-rgb:20,3,131;--brand-2-rgb:59,47,184;--brand-hero-rgb:91,79,224;\n")
    h = rep(h, "</style>\n", "</style>\n" + LOADER, name='idx-style')
    h = rep(h, "      <div><b>DEI Chatbot</b><small>Admin Dashboard</small></div>", "      <div data-brand-text><b>DEI Chatbot</b><small>Admin Dashboard</small></div>", name='side')
    h = rep(h, "          <li>Beri nama (mis. \"DEI Chatbot\")", "          <li data-brand-text>Beri nama (mis. \"DEI Chatbot\")", name='li')
    h = rep(h, "        <h2>Apa yang baru di DEI Chatbot</h2>", "        <h2 data-brand-text>Apa yang baru di DEI Chatbot</h2>", name='h2')
    left = [x for x in re.findall(r'#140383|#3b2fb8|#eceaf9|#cbc6f3|#f6f5fd|#f1effd|20,3,131', h)]
    IDX.write_text(h, encoding='utf-8'); print('index.html: OK, sisa warna lama (harus hanya :root/meta):', len(left))

h = LOG.read_text(encoding='utf-8')
if 'action=brand_js' in h:
    print('login.html: sudah terpasang')
else:
    h = css_vars(h, "  :root{--brand:#140383;--brand-2:#3b2fb8;",
                 "  :root{--brand:#140383;--brand-2:#3b2fb8;--brand-rgb:20,3,131;--brand-2-rgb:59,47,184;")
    h = rep(h, "</style>\n", "</style>\n" + LOADER, name='log-style')
    h = rep(h, '      <h1 style="margin:0;font-size:19px;line-height:1.25">DEI Chatbot Dashboard</h1>',
               '      <h1 data-brand-text style="margin:0;font-size:19px;line-height:1.25">DEI Chatbot Dashboard</h1>', name='h1')
    LOG.write_text(h, encoding='utf-8'); print('login.html: OK')

# ---------------------------------------------------------------- app.js
a = APP.read_text(encoding='utf-8')
if 'BRAND_VENDOR' in a:
    print('app.js: sudah terpasang')
else:
    a = rep(a, "  /* ---- base + api ------------------------------------------------------ */\n",
            "  /* v1.2.73: brand per instalasi (window.DEI_BRAND dari action=brand_js; null = DEI) */\n"
            "  var BRAND = window.DEI_BRAND || null;\n"
            "  var BRAND_VENDOR = BRAND ? BRAND.vendor : 'DEI';\n"
            "  var BRAND_C1 = (BRAND && BRAND.c1) || '#140383';\n"
            "  var BRAND_C2 = (BRAND && BRAND.c2) || '#a855f7';\n\n"
            "  /* ---- base + api ------------------------------------------------------ */\n", name='brandvars')
    a = rep(a, "Hubungi DEI untuk menambah kuota.'", "Hubungi ' + BRAND_VENDOR + ' untuk menambah kuota.'", name='kuota')
    a = rep(a, "atau minta DEI menambah kursi paket.'", "atau minta ' + BRAND_VENDOR + ' menambah kursi paket.'", name='kursi1')
    a = rep(a, "atau minta Super Admin/DEI menambah kursi paket.'", "atau minta Super Admin/' + BRAND_VENDOR + ' menambah kursi paket.'", name='kursi2')
    a = rep(a, "sampai diaktifkan oleh DEI.</span>'", "sampai diaktifkan oleh ' + BRAND_VENDOR + '.</span>'", name='wl')
    a = rep(a, "  var PIE_COLORS = [", "  var PIE_COLORS = (BRAND && BRAND.palette && BRAND.palette.length) ? BRAND.palette : [", name='pie')
    a = rep(a, "  var TP_COL = [", "  var TP_COL = (BRAND && BRAND.palette && BRAND.palette.length) ? BRAND.palette : [", name='tp')
    a = rep(a, "poly('count', '#140383') + poly('users', '#a855f7')", "poly('count', BRAND_C1) + poly('users', BRAND_C2)", name='poly')
    a = rep(a, "background:#140383;display:inline-block\"></span>Percakapan", "background:' + BRAND_C1 + ';display:inline-block\"></span>Percakapan", name='leg1')
    a = rep(a, "background:#a855f7;display:inline-block\"></span>Pengunjung unik", "background:' + BRAND_C2 + ';display:inline-block\"></span>Pengunjung unik", name='leg2')
    a = rep(a, "ai: ['Dijawab AI', '#140383']", "ai: ['Dijawab AI', BRAND_C1]", name='lgst')
    APP.write_text(a, encoding='utf-8'); print('app.js: OK')
