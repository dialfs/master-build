#!/usr/bin/env python3
"""v1.2.74 — Panduan (guided walkthrough) per peran.
  * Tur interaktif (sorotan + kartu langkah) khusus Super Admin, Admin, Supervisor, WA Agent
  * Muncul sekali saat pertama login; status "sudah lihat" disimpan per akun (users.json → tour_seen)
  * Tombol "Panduan" di bawah menu + kartu "Panduan Penggunaan" di Profil Saya
    (peran di atas bisa melihat pratinjau panduan peran di bawahnya untuk melatih tim)
Idempoten. Pakai: patch_v1274.py <root dei-chatbot-ai / dei-tenant>"""
import re, sys, pathlib

ROOT = pathlib.Path(sys.argv[1])
F_API = ROOT / 'api/index.php'
F_JS = ROOT / 'dashboard/chatbot-ai/app.js'
F_HTML = ROOT / 'dashboard/chatbot-ai/index.html'


def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count:
        raise SystemExit(f'ANCHOR {n}x (harus {count}): {old[:90]!r}')
    return src.replace(old, new)


# ------------------------------------------------------------------ API
api = F_API.read_text(encoding='utf-8')
if "case 'tour_seen':" not in api:
    api = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.74');", api, count=1)
    # login: kirim tour_seen bersama data user
    api = rep(api, """                    'user' => [
                        'username' => $username,
                        'name'     => $u['name'] ?? $username,
                        'role'     => $role,
                    ],""", """                    'user' => [
                        'username' => $username,
                        'name'     => $u['name'] ?? $username,
                        'role'     => $role,
                        'tour_seen' => (int)($u['tour_seen'] ?? 0),   // v1.2.74
                    ],""")
    api = rep(api, """            'role'     => $u['role'] ?? 'editor',
        ]]);""", """            'role'     => $u['role'] ?? 'editor',
            'tour_seen' => (int)($u['tour_seen'] ?? 0),   // v1.2.74
        ]]);""")
    api = rep(api, """    case 'release_seen': {""", """    /* ---------- v1.2.74: Panduan — tandai versi tur yang sudah dilihat (semua peran) ---------- */
    case 'tour_seen': {
        $u = requireAuth();
        $in = bodyInput();
        $v = max(0, min(999, (int)($in['ver'] ?? 0)));
        if ($v < 1) jsonOut(['ok' => false, 'error' => 'Versi panduan tidak valid.'], 400);
        $users = readJson(USERS_FILE, []);
        foreach ($users as $i => $x) {
            if (($x['username'] ?? '') !== $u['username']) continue;
            if ((int)($x['tour_seen'] ?? 0) < $v) { $users[$i]['tour_seen'] = $v; writeJson(USERS_FILE, $users); }
            break;
        }
        jsonOut(['ok' => true, 'tour_seen' => $v]);
        break;
    }

    case 'release_seen': {""")
    F_API.write_text(api, encoding='utf-8')
    print('api: ok')
else:
    print('api: sudah terpasang')

# ------------------------------------------------------------------ HTML
html = F_HTML.read_text(encoding='utf-8')
if 'id="btnTour"' not in html:
    html = re.sub(r'app\.js\?v=[0-9.]+', 'app.js?v=1.2.74', html, count=1)
    css = r"""
  /* v1.2.74: PANDUAN (guided walkthrough) */
  #tourRoot{position:fixed;inset:0;z-index:10000}
  #tourRoot .tour-block{position:absolute;inset:0;background:transparent}
  #tourRoot .tour-hole{position:fixed;border-radius:12px;box-shadow:0 0 0 200vmax rgba(12,12,32,.58);outline:2px solid rgba(255,255,255,.95);outline-offset:0;pointer-events:none;transition:left .28s ease,top .28s ease,width .28s ease,height .28s ease}
  #tourRoot.center .tour-hole{outline:none}
  #tourRoot .tour-pop{position:fixed;background:#fff;border-radius:14px;box-shadow:0 18px 50px rgba(10,10,40,.28);padding:18px 18px 14px;color:var(--ink);transition:left .28s ease,top .28s ease;max-height:calc(100vh - 24px);overflow:auto}
  #tourRoot .tour-x{position:absolute;top:10px;right:10px;background:none;border:none;color:var(--muted);cursor:pointer;padding:4px;border-radius:6px;display:flex}
  #tourRoot .tour-x:hover{background:var(--bg);color:var(--ink)}
  #tourRoot .tour-step{font-size:11.5px;font-weight:600;color:var(--brand);letter-spacing:.02em;text-transform:uppercase;margin-bottom:6px;padding-right:28px}
  #tourRoot .tour-prev{display:inline-block;font-size:11px;font-weight:600;background:#fff7e6;color:#9a5b00;border:1px solid #f6d79a;border-radius:20px;padding:2px 9px;margin-bottom:8px}
  #tourRoot h4{font-size:16.5px;font-weight:700;letter-spacing:-.01em;margin:0 0 6px;padding-right:24px;line-height:1.3}
  #tourRoot .tour-body{font-size:13.5px;line-height:1.6;color:#3a3a52}
  #tourRoot .tour-body p+p{margin-top:8px}
  #tourRoot .tour-body ul{margin:6px 0 0 18px}
  #tourRoot .tour-body li{margin:2px 0}
  #tourRoot .tour-prog{height:4px;background:var(--line);border-radius:4px;margin:14px 0 12px;overflow:hidden}
  #tourRoot .tour-prog i{display:block;height:100%;background:var(--brand);border-radius:4px;transition:width .28s ease}
  #tourRoot .tour-foot{display:flex;justify-content:space-between;align-items:center;gap:8px}
  #tourRoot .tour-foot .tour-hint{font-size:11.5px;color:var(--muted)}
  #tourRoot .tour-btns{display:flex;gap:8px;margin-left:auto}
  #tourRoot .tour-btns .btn{white-space:nowrap}
  #tourBtns .btn{display:inline-flex;align-items:center;gap:6px}
  @media(max-width:860px){
    #tourRoot .tour-pop{border-radius:16px}
    #tourRoot h4{font-size:17px}
    #tourRoot .tour-body{font-size:14.5px}
    #tourRoot .tour-foot .tour-hint{display:none}
    #tourRoot .tour-btns .btn{padding:10px 16px;font-size:14px}
  }
</style>
<script>/* v1.2.73: brand"""
    html = rep(html, '</style>\n<script>/* v1.2.73: brand', css.lstrip('\n'))
    html = rep(html, '<button id="btnNotif" type="button"',
               '<button id="btnTour" type="button" title="Tur singkat menu sesuai peran Anda"><span data-ico="circle-help"></span> Panduan</button>'
               '<button id="btnNotif" type="button"')
    html = rep(html, """        <button class="btn" id="btnChangePassword">Simpan Password</button>
      </div>""", """        <button class="btn" id="btnChangePassword">Simpan Password</button>
      </div>
      <!-- v1.2.74: Panduan -->
      <div class="card" id="tourCard" style="margin-top:16px">
        <h3 style="margin:0 0 6px 0;font-size:15px">Panduan Penggunaan</h3>
        <p class="hint" id="tourCardNote" style="font-size:13px;color:var(--muted);margin:0 0 12px">Tur singkat menu &amp; fitur sesuai peran Anda.</p>
        <div id="tourBtns" style="display:flex;gap:8px;flex-wrap:wrap"></div>
      </div>""")
    F_HTML.write_text(html, encoding='utf-8')
    print('html: ok')
else:
    print('html: sudah terpasang')

# ------------------------------------------------------------------ JS
js = F_JS.read_text(encoding='utf-8')
if 'function tourStart(' not in js:
    TOUR_JS = pathlib.Path(__file__).with_name('tour.js').read_text(encoding='utf-8')
    js = rep(js, "  // first tab per role\n", TOUR_JS + "\n  // first tab per role\n")
    js = rep(js, """  showTab(firstTab);
  maybeAutoCheck();""", """  showTab(firstTab);
  tourInit();                                   // v1.2.74: panduan pertama kali
  maybeAutoCheck();""")
    F_JS.write_text(js, encoding='utf-8')
    print('js: ok')
else:
    print('js: sudah terpasang')
