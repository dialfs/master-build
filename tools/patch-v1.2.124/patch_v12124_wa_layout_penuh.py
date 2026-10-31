#!/usr/bin/env python3
r"""v1.2.124 wa-layout-penuh: tampilan Percakapan WA dibuat setinggi layar supaya kotak balasan selalu terlihat
tanpa scroll halaman (desktop & HP).
 1. Halaman Percakapan WA = 1 layar penuh: daftar chat & isi pesan punya scroll sendiri, kotak balas menempel di bawah.
 2. Kartu ringkasan (Belum dibalas / Selesai) diringkas jadi pil kecil; deskripsi halaman disembunyikan.
 3. Filter status tetap terlihat semua (turun baris). Dropdown Nomor & Lead Rating di baris sendiri, lebih mencolok
    (warna penuh bila sedang aktif). Ekspor & Audit di kanan (HP: ikon saja).
 4. Lead Rating dipindah ke bawah nama/nomor — di daftar chat dan di kepala chat (tanpa tulisan "Lead Rating:").
 5. HP: saat chat dibuka, judul/kartu/filter disembunyikan supaya area chat penuh.
Pakai: python3 patch_v12124_wa_layout_penuh.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.123)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.124: wa-layout-penuh'
STAMP = time.strftime('%Y%m%d-%H%M%S')

def one(s, old, rel):
    n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:90]); return s.index(old)

def patch(rel, fn):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    s2 = fn(s, rel)
    assert TAG in s2, rel
    shutil.copy2(p, p + '.bak-v12124-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s2); print('OK', rel)

def rep(s, old, new, rel):
    one(s, old, rel); return s.replace(old, new)

# ---------------------------------------------------------------- api/index.php
def f_api(s, rel):
    return rep(s, "define('DEI_VERSION', 'v1.2.123');   // v1.2.123: wa-scroll-stabil",
                  "define('DEI_VERSION', 'v1.2.124');   // v1.2.124: wa-layout-penuh", rel)

# ---------------------------------------------------------------- index.html (CSS)
CSS = r"""/* === v1.2.124: wa-layout-penuh — Percakapan WA setinggi layar, kotak balas selalu terlihat === */
body.wa-full main{max-width:1440px;height:100vh;height:100dvh;display:flex;flex-direction:column;padding-top:18px;padding-bottom:14px}
body.wa-full #panel-wachat.active{display:flex;flex-direction:column;flex:1;min-height:0;animation:none}
body.wa-full #panel-wachat .ph{margin-bottom:10px}
body.wa-full #panel-wachat .ph h2{font-size:19px}
body.wa-full #panel-wachat .ph p{display:none}
body.wa-full #panel-wachat > .card{flex:1;min-height:0;display:flex;flex-direction:column;margin-bottom:0}
body.wa-full #panel-wachat .wachat-wrap{flex:1;min-height:320px;height:auto}
body.wa-full #waFlagCards{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:10px 16px 0}
body.wa-full #waFlagCards .wa-mode-pill{margin:0;order:9;margin-left:auto}
body.wa-full #waFlagCards .wa-flag-cards{display:flex;flex-wrap:wrap;gap:8px;margin:0}
body.wa-full #waFlagCards .wa-flag-card{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:999px}
body.wa-full #waFlagCards .wa-flag-card .n{font-size:15px}
body.wa-full #waFlagCards .wa-flag-card .l{font-size:12px}
body.wa-full .wa-filter-bar{padding:10px 16px;gap:6px}
.wa-fbar2{flex-basis:100%;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.wa-fbar2 .wa-sp{flex:1}
.wa-fbar2 .wa-audit-toggle{margin-left:0}
.wa-dd{position:relative;display:inline-flex;align-items:center;gap:7px;height:34px;padding:0 30px 0 11px;border:1.5px solid rgba(var(--brand-rgb),.35);background:var(--brand-soft);color:var(--brand);border-radius:10px;font-weight:600;font-size:13px;cursor:pointer;max-width:100%}
.wa-dd:hover{border-color:var(--brand)}
.wa-dd select{appearance:none;-webkit-appearance:none;border:0;background:transparent;color:inherit;font-family:inherit;font-size:13px;font-weight:600;padding:0;margin:0;width:auto;max-width:240px;outline:none;cursor:pointer;box-shadow:none;text-overflow:ellipsis}
.wa-dd select option{color:#111;background:#fff;font-weight:400}
.wa-dd .wa-dd-chev{position:absolute;right:9px;top:50%;transform:translateY(-50%);pointer-events:none;display:inline-flex}
.wa-dd.is-on{background:var(--brand);border-color:var(--brand);color:#fff}
.wa-conv-sub{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:11px;color:var(--muted);margin-top:2px}
.wa-th-id{min-width:0}
.wa-rate-row{display:flex;align-items:center;gap:6px;margin-top:4px;flex-wrap:wrap}
.wa-rate{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:7px;font-size:12px;font-weight:600;cursor:pointer;line-height:1.6}
.wa-rate select{appearance:none;-webkit-appearance:none;border:0;background:transparent;color:inherit;font-family:inherit;font-size:12px;font-weight:600;padding:0;margin:0;width:auto;outline:none;cursor:pointer;box-shadow:none}
.wa-rate select option{color:#111;background:#fff;font-weight:400}
.wa-rate select:disabled{cursor:default}
@media(max-width:860px){
  body.wa-full main{padding:64px 10px calc(env(safe-area-inset-bottom, 0px) + 10px)}
  body.wa-full #panel-wachat .ph{margin-bottom:8px}
  body.wa-full #panel-wachat .wachat-wrap{flex-direction:column;min-height:0}
  body.wa-full #panel-wachat .wachat-list{flex:1;min-height:0;border-bottom:0}
  body.wa-full #panel-wachat .wachat-wrap.showing-thread .wachat-thread{flex:1;min-height:0}
  body.wa-full #panel-wachat .wachat-body{height:auto;flex:1;min-height:0;padding:12px}
  body.wa-full #panel-wachat .wachat-thead{padding:8px 12px}
  body.wa-full #panel-wachat .wachat-reply{padding:8px 10px}
  body.wa-full #panel-wachat:has(.wachat-wrap.showing-thread) .ph,
  body.wa-full #panel-wachat:has(.wachat-wrap.showing-thread) #waFlagCards,
  body.wa-full #panel-wachat:has(.wachat-wrap.showing-thread) #waFilterBar,
  body.wa-full #panel-wachat:has(.wachat-wrap.showing-thread) #waAuditBox{display:none!important}
  body.wa-full #waFlagCards{padding:8px 10px 0}
  body.wa-full #waFlagCards .wa-mode-pill{display:none}
  body.wa-full #waFlagCards .wa-flag-cards{flex-wrap:nowrap;width:100%;gap:6px}
  body.wa-full #waFlagCards .wa-flag-card{flex:1 1 0;min-width:0;padding:4px 10px}
  body.wa-full #waFlagCards .wa-flag-card .l{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
  body.wa-full #waThreadHead .wa-assign{margin-left:0;margin-top:4px}
  body.wa-full #waThreadHead .wa-assign select{max-width:38vw}
  body.wa-full .wa-filter-bar{padding:8px 10px}
  .wa-fbar2{flex-wrap:nowrap;gap:6px}
  .wa-fbar2 .wa-sp{display:none}
  .wa-dd{flex:1 1 0;min-width:0;height:32px;padding:0 24px 0 9px}
  .wa-dd .wa-dd-chev{right:6px}
  .wa-dd select{max-width:none;width:100%;min-width:0;font-size:12.5px}
  .wa-fbar2 .wa-lbl-t{display:none}
  .wa-fbar2 .wa-filter-btn{padding:0 9px;height:32px;flex:none}
}

/* === v1.2.0 WA Claim UI ==================================================== */"""

def f_html(s, rel):
    return rep(s, "/* === v1.2.0 WA Claim UI ==================================================== */", CSS, rel)

# ---------------------------------------------------------------- app.js
def f_js(s, rel):
    # 1. ikon tag
    s = rep(s, """    'chevron-down':  '<path d="m6 9 6 6 6-6"/>'\n  };""",
               """    'chevron-down':  '<path d="m6 9 6 6 6-6"/>',\n    'tag':           '<path d="M12.6 2.6A2 2 0 0 0 11.2 2H4a2 2 0 0 0-2 2v7.2a2 2 0 0 0 .6 1.4l8.7 8.7a2.4 2.4 0 0 0 3.4 0l6.6-6.6a2.4 2.4 0 0 0 0-3.4z"/><circle cx="7.5" cy="7.5" r=".5" fill="currentColor"/>'   // v1.2.124: wa-layout-penuh\n  };""", rel)
    # 2. kelas body saat tab Percakapan WA aktif
    s = rep(s, "    if (tab === 'wachat') {\n      var _wrapNav",
               "    document.body.classList.toggle('wa-full', tab === 'wachat');   // v1.2.124: wa-layout-penuh\n    if (tab === 'wachat') {\n      var _wrapNav", rel)
    # 3. baris filter: dropdown di baris sendiri, lebih mencolok
    a = one(s, """      ((waState.channels || []).length > 1 ? '<select class="wa-ch-filter\"""", rel)
    endm = """' Audit</button>');"""
    b = s.index(endm, a) + len(endm)
    assert b - a < 2000, 'blok filter terlalu panjang'
    NEW = r"""      '<div class="wa-fbar2">' +   // v1.2.124: wa-layout-penuh — dropdown Nomor & Lead Rating di baris sendiri, lebih mencolok
      ((waState.channels || []).length > 1 ? '<label class="wa-dd' + (waState.ch ? ' is-on' : '') + '" title="Saring per nomor WhatsApp">' + ico('phone',14) + '<select class="wa-ch-filter"><option value="">Semua nomor</option>' +   // v1.2.98: multi-nomor
        waState.channels.map(function (c) { return '<option value="' + esc(c.id) + '"' + (waState.ch === c.id ? ' selected' : '') + '>' + esc(c.label) + '</option>'; }).join('') + '</select><span class="wa-dd-chev">' + ico('chevron-down',14) + '</span></label>' : '') +
      '<label class="wa-dd' + (waState.stage ? ' is-on' : '') + '" title="Saring per Lead Rating">' + ico('tag',14) + '<select class="wa-stage-filter' + (waState.stage ? ' is-active' : '') + '">' +   // v1.2.117: filter-lead-rating
        stageFltOptionsHtml(waState.stage || '', waState.stageCounts) + '</select><span class="wa-dd-chev">' + ico('chevron-down',14) + '</span></label>' +
      '<span class="wa-sp"></span>' +
      (waState.isAdmin === false ? '' : '<button class="wa-filter-btn wa-export-contacts" title="Unduh semua kontak WA (.vcf)">' + ico('download',14) + '<span class="wa-lbl-t"> Ekspor Kontak</span></button>') +
      (waState.isAdmin === false ? '' : '<button class="wa-filter-btn wa-audit-toggle" title="Lihat audit log">' + ico('clipboard-list',14) + '<span class="wa-lbl-t"> Audit</span></button>') +
      '</div>';"""
    s = s[:a] + NEW + s[b:]
    s = rep(s, "if (_chSel) _chSel.onchange = function () { waState.ch = this.value; fetchWaConvs(); };",
               "if (_chSel) _chSel.onchange = function () { waState.ch = this.value; this.parentNode.classList.toggle('is-on', !!this.value); fetchWaConvs(); };", rel)
    s = rep(s, "if (_stSel) _stSel.onchange = function () { waState.stage = this.value; fetchWaConvs(); };",
               "if (_stSel) _stSel.onchange = function () { waState.stage = this.value; this.parentNode.classList.toggle('is-on', !!this.value); fetchWaConvs(); };", rel)
    # 4. daftar chat: Lead Rating di bawah nama, sebaris dengan nomor
    s = rep(s, """      var subNomor = c.name ? '<div style="font-size:11px;color:var(--muted)">+' + esc(c.number) + '</div>' : '';""",
               """      var subNomor = '<div class="wa-conv-sub">' + (c.name ? '<span>+' + esc(c.number) + '</span>' : '') + contactStageBadgeHtml(c.stage, c.vip) + '</div>';   // v1.2.124: Lead Rating di bawah nama/nomor""", rel)
    s = rep(s, """      var stageBadge = ' ' + contactStageBadgeHtml(c.stage, c.vip, ';margin-left:2px');""",
               """      var stageBadge = '';   // v1.2.124: Lead Rating pindah ke baris nomor""", rel)
    # 5. kepala chat: Lead Rating + VIP di bawah nama/nomor, tanpa tulisan "Lead Rating:"
    st = """        '<span style="color:var(--muted);margin:0 2px">&middot;</span>' +\n        '<span style="color:var(--muted)">Lead Rating:</span>' +\n"""
    a = one(s, st, rel)
    vipEnd = """' VIP</button>' +\n"""
    b = s.index(vipEnd, a) + len(vipEnd)
    blok = s[a:b]
    vipLine = [l for l in blok.split('\n') if "id=\"waVipToggle\"" in l]
    assert len(vipLine) == 1, 'baris VIP tidak ditemukan'
    s = s[:a] + s[b:]
    head = "    $('#waThreadHead').innerHTML =\n"
    i = one(s, head, rel)
    rate = ("    var _csNow = CONTACT_STAGE[_stageNow] || CONTACT_STAGE.new;   // v1.2.124: wa-layout-penuh — Lead Rating di bawah nama/nomor\n"
            "    var _rateRow = '<div class=\"wa-rate-row\">' +\n"
            "      '<label class=\"wa-rate\" title=\"Lead Rating\" style=\"background:' + _csNow.bg + ';color:' + _csNow.fg + '\">' + ico('tag',12) +\n"
            "      '<select id=\"waStageSelect\">' + _stageOpts + '</select>' + ico('chevron-down',12) + '</label>' +\n"
            + vipLine[0] + "\n"
            "      '</div>';\n")
    s = s[:i] + rate + s[i:]
    s = rep(s, """      '<span>' + _judulThread + ' <a href="#" id="waEditName" title="Ubah nama" style="text-decoration:none;font-size:12px">' + ico('pen-tool',12) + '</a>' + _leadLink + '</span>' +""",
               """      '<div class="wa-th-id"><div>' + _judulThread + ' <a href="#" id="waEditName" title="Ubah nama" style="text-decoration:none;font-size:12px">' + ico('pen-tool',12) + '</a>' + _leadLink + '</div>' + _rateRow + '</div>' +""", rel)
    # 6. area scroll thread: selalu kotak thread sendiri (bukan halaman) di tampilan penuh
    s = rep(s, "    var w = b.closest ? b.closest('.wachat-wrap') : null;",
               "    if (document.body.classList.contains('wa-full')) return b;   // v1.2.124: wa-layout-penuh — thread punya area scroll sendiri (desktop & HP)\n    var w = b.closest ? b.closest('.wachat-wrap') : null;", rel)
    return s

patch('api/index.php', f_api)
patch('dashboard/chatbot-ai/index.html', f_html)
patch('dashboard/chatbot-ai/app.js', f_js)
print('selesai')
