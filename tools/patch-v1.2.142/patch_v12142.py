# v1.2.142: mobile-rapi — top bar burger kanan, chip status berwarna (kartu ringkasan disembunyikan di mobile), dropdown filter 1 per baris
import sys, os, shutil, time
T = os.path.expanduser(sys.argv[1])
H = os.path.join(T, 'dashboard/chatbot-ai/index.html')
J = os.path.join(T, 'dashboard/chatbot-ai/app.js')
A = os.path.join(T, 'api/index.php')
ts = time.strftime('%Y%m%d-%H%M%S')
for f in (H, J, A): shutil.copy2(f, f + '.bak-v12142-' + ts)
def rep(path, old, new, cnt=1):
    s = open(path, encoding='utf-8').read()
    if new in s and old not in s: print('skip (sudah):', path, new[:50].replace('\n',' ')); return
    n = s.count(old)
    if n != cnt: sys.exit('ANCHOR %d != %d di %s: %r' % (n, cnt, path, old[:80]))
    open(path, 'w', encoding='utf-8').write(s.replace(old, new))

# --- index.html: top bar mobile ---
rep(H, '<button class="menu-btn" id="menuBtn"><span data-ico="menu" data-ico-size="20"></span></button>',
 '<header class="mtop" id="mtop"><!-- v1.2.142: mobile-rapi — bar atas tetap, burger di kanan -->\n'
 '  <div class="mtop-brand"><img src="./logo-256.png" alt=""><span data-brand-text><b>DEI Chatbot</b></span></div>\n'
 '  <button class="menu-btn" id="menuBtn" aria-label="Menu"><span data-ico="menu" data-ico-size="20"></span></button>\n'
 '</header>')
rep(H, '''    .menu-btn{
      display:flex!important;align-items:center;justify-content:center;
      position:fixed;
      top:calc(env(safe-area-inset-top, 0px) + 12px);
      left:calc(env(safe-area-inset-left, 0px) + 12px);
      z-index:50;
      width:44px;height:44px;border-radius:12px;''',
'''    /* v1.2.142: mobile-rapi — bar atas tetap (latar solid), burger di kanan, tidak menutupi konten */
    .mtop{
      display:flex!important;align-items:center;justify-content:space-between;gap:10px;
      position:fixed;top:0;left:0;right:0;z-index:18;
      height:calc(env(safe-area-inset-top, 0px) + 54px);
      padding:env(safe-area-inset-top, 0px) calc(env(safe-area-inset-right, 0px) + 10px) 0 calc(env(safe-area-inset-left, 0px) + 14px);
      background:#fff;border-bottom:1px solid var(--line);box-shadow:0 1px 6px rgba(15,23,42,.05);
    }
    .mtop-brand{display:flex;align-items:center;gap:9px;min-width:0}
    .mtop-brand img{width:30px;height:30px;border-radius:8px;flex:none}
    .mtop-brand b{font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block}
    .mtop-brand small{display:none}
    .menu-btn{
      display:flex!important;align-items:center;justify-content:center;
      position:static;flex:none;
      width:40px;height:40px;border-radius:11px;''')
rep(H, 'padding:64px 14px calc(env(safe-area-inset-bottom, 0px) + 70px);',
       'padding:calc(env(safe-area-inset-top, 0px) + 68px) 14px calc(env(safe-area-inset-bottom, 0px) + 70px);')
rep(H, 'body.wa-full main{padding:64px 10px calc(env(safe-area-inset-bottom, 0px) + 10px)}',
       'body.wa-full main{padding:calc(env(safe-area-inset-top, 0px) + 64px) 10px calc(env(safe-area-inset-bottom, 0px) + 10px)}')
rep(H, '    .menu-btn{width:42px;height:42px;font-size:20px}', '    .menu-btn{width:40px;height:40px;font-size:20px}')
rep(H, '  .menu-btn{display:none}   /* default tersembunyi di desktop, di-show di @media mobile */',
       '  .menu-btn,.mtop{display:none}   /* default tersembunyi di desktop, di-show di @media mobile */')

# --- index.html: chip berwarna + kartu ringkasan hilang di mobile + dropdown 1 per baris ---
CSS = '''
/* === v1.2.142: mobile-rapi ================================================ */
/* chip status berwarna (menggantikan kartu ringkasan di mobile) */
.wa-filter-btn[data-filter="unreplied"]{color:#b91c1c;border-color:#fecaca;background:#fef2f2}
.wa-filter-btn[data-filter="unreplied"] .wa-filter-count{background:#fee2e2;color:#b91c1c}
.wa-filter-btn[data-filter="unreplied"].active{background:#b91c1c;border-color:#b91c1c;color:#fff}
.wa-filter-btn[data-filter="done"]{color:#047857;border-color:#a7f3d0;background:#ecfdf5}
.wa-filter-btn[data-filter="done"] .wa-filter-count{background:#d1fae5;color:#047857}
.wa-filter-btn[data-filter="done"].active{background:#047857;border-color:#047857;color:#fff}
.wa-filter-btn[data-filter="full_bot"]{color:#1d4ed8;border-color:#bfdbfe;background:#eff6ff}
.wa-filter-btn[data-filter="full_bot"] .wa-filter-count{background:#dbeafe;color:#1d4ed8}
.wa-filter-btn[data-filter="full_bot"].active{background:#1d4ed8;border-color:#1d4ed8;color:#fff}
.wa-filter-btn[data-filter="unreplied"].active .wa-filter-count,
.wa-filter-btn[data-filter="done"].active .wa-filter-count,
.wa-filter-btn[data-filter="full_bot"].active .wa-filter-count{background:rgba(255,255,255,.25);color:#fff}
.wa-chips{display:contents}
@media(max-width:860px){
  body.wa-full #waFlagCards{display:none!important}
  /* chip status: satu baris, geser ke samping */
  .wa-chips{display:flex;flex-wrap:nowrap;gap:6px;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;
    flex:1 1 100%;min-width:0;margin:0 -10px;padding:0 10px 2px;
    -webkit-mask-image:linear-gradient(90deg,#000 calc(100% - 24px),transparent);mask-image:linear-gradient(90deg,#000 calc(100% - 24px),transparent)}
  .wa-chips::-webkit-scrollbar{display:none}
  .wa-chips .wa-filter-btn{flex:none;white-space:nowrap}
  /* dropdown: satu filter per baris, teks utuh */
  .wa-fbar2,.wa-fbar2.tf-on{flex-wrap:wrap;gap:6px}
  .wa-fbar2 .wa-dd,.wa-fbar2.tf-on .wa-dd{flex:1 1 100%;width:100%;height:36px}
  .wa-fbar2 .wa-dd select{font-size:13.5px}
}
'''
rep(H, '</style>\n<script>/* v1.2.73: brand per instalasi', CSS + '</style>\n<script>/* v1.2.73: brand per instalasi')
rep(H, '<script src="app.js?v=1.2.141"></script><!-- v1.2.141: filter-chat-terpilih -->',
       '<script src="app.js?v=1.2.142"></script><!-- v1.2.142: mobile-rapi -->')

# --- app.js: bungkus chip status ---
rep(J, """      '<button class="wa-filter-btn active" data-filter="all">All""",
       """      '<div class="wa-chips">' +   // v1.2.142: mobile-rapi — chip status satu baris geser di mobile
      '<button class="wa-filter-btn active" data-filter="all">All""")
rep(J, """data-count="takeover_requests">0</span></button>' +
      '<div class="wa-fbar2""", """data-count="takeover_requests">0</span></button>' +
      '</div>' +
      '<div class="wa-fbar2""")
# klik di bar atas (luar sidebar) tetap menutup drawer — sudah ditangani: btn.contains

# --- versi ---
rep(A, "define('DEI_VERSION', 'v1.2.141');   // v1.2.141: filter-chat-terpilih",
       "define('DEI_VERSION', 'v1.2.142');   // v1.2.142: mobile-rapi")
print('OK')
