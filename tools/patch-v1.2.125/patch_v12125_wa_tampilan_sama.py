#!/usr/bin/env python3
r"""v1.2.125 wa-tampilan-sama: samakan tampilan Percakapan WA dengan contoh yang disetujui Dias.
 1. Ringkasan "29 belum dibalas · 340 selesai" + Mode Manual sebaris dengan judul halaman.
 2. Daftar chat: avatar inisial berwarna + kotak cari (nama / nomor / pesan, saring di browser).
 3. Kepala chat: avatar, nama, nomor + via, Lead Rating bertumpuk; Claim/Selesai di kanan;
    baris alat terpisah (status, Serahkan, Pindah nomor, VIP, Analisa). HP: tombol kembali & tombol "lainnya".
 4. Belum di-claim: bar "Claim & Balas" di tempat kotak balas (admin tetap bisa "Balas tanpa claim").
 5. Layar lebar (>= 1280 px): panel info kontak di kanan (status, Lead Rating, nomor bisnis, ditangani, aktivitas).
Pakai: python3 patch_v12125_wa_tampilan_sama.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.124)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.125: wa-tampilan-sama'
STAMP = time.strftime('%Y%m%d-%H%M%S')

def one(s, old, rel):
    n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:90]); return s.index(old)
def rep(s, old, new, rel):
    one(s, old, rel); return s.replace(old, new)
def patch(rel, fn):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    assert 'v1.2.124: wa-layout-penuh' in s, rel + ': butuh v1.2.124'
    s2 = fn(s, rel); assert TAG in s2, rel
    shutil.copy2(p, p + '.bak-v12125-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s2); print('OK', rel)

def f_api(s, rel):
    return rep(s, "define('DEI_VERSION', 'v1.2.124');   // v1.2.124: wa-layout-penuh",
                  "define('DEI_VERSION', 'v1.2.125');   // v1.2.125: wa-tampilan-sama", rel)

CSS = r"""/* === v1.2.125: wa-tampilan-sama — samakan dengan contoh ======================= */
body.wa-full main{min-width:0}
body.wa-full #panel-wachat .ph{display:flex;align-items:center;gap:10px 14px;flex-wrap:wrap}
body.wa-full #panel-wachat .ph h2{margin:0}
body.wa-full #panel-wachat .ph #waFlagCards{padding:0;flex:1;min-width:0}
body.wa-full #waFlagCards .wa-flag-card{background:#fff}
body.wa-full #waFlagCards .wa-flag-card .l svg{display:none}
body.wa-full #waFlagCards .wa-flag-card .l{color:var(--ink)}
body.wa-full #panel-wachat .wa-back-btn{display:none!important}
.wa-av{border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;line-height:1}
#panel-wachat .wachat-lcol{width:320px;flex-shrink:0;display:flex;flex-direction:column;min-height:0;border-right:1px solid var(--line);background:#fff}
#panel-wachat .wachat-lcol .wachat-list{width:auto;border-right:0;flex:1;min-height:0}
.wa-search{position:relative;padding:10px 12px;border-bottom:1px solid var(--line)}
.wa-search .ic-s{position:absolute;left:23px;top:50%;transform:translateY(-50%);color:var(--muted);pointer-events:none;display:inline-flex}
#waSearch{width:100%;padding:8px 12px 8px 34px;border-radius:10px;background:var(--bg);font-size:13.5px}
#panel-wachat .wa-conv{display:flex;gap:10px;align-items:flex-start}
.wa-conv-b{flex:1;min-width:0}
#waThreadHead{display:block;padding:0}
#waThreadHead > span{display:block;padding:12px 16px}
.wa-th-top{display:flex;align-items:center;gap:12px;padding:10px 16px}
.wa-th-id{flex:1;min-width:0}
.wa-th-name{font-weight:700;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.wa-th-sub{font-size:12.5px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.wa-th-sub:empty{display:none}
.wa-th-via{color:#5b21b6}
.wa-th-act{display:flex;align-items:center;gap:6px;flex-wrap:wrap;justify-content:flex-end}
.wa-th-tools{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 16px;border-top:1px solid var(--line);font-size:12px}
.wa-th-tools .wa-assign{margin-left:0}
.wa-th-tools .wa-assign select{max-width:220px}
.wa-th-back,.wa-th-more{display:none;align-items:center;justify-content:center;width:34px;height:34px;border-radius:9px;border:1px solid var(--line);background:#fff;color:var(--ink);cursor:pointer;flex:none;padding:0}
.wa-th-back{border:0;background:none}
.wa-claimbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;background:var(--brand-soft);border-radius:12px;padding:10px 12px;font-size:13px;color:var(--ink)}
.wa-claimbar > span{flex:1;min-width:160px}
.wa-claimbar a{font-weight:600;white-space:nowrap}
.wachat-info{display:none;width:250px;flex-shrink:0;border-left:1px solid var(--line);background:#fff;overflow-y:auto;padding:22px 16px}
.wachat-info .wa-av{margin:0 auto 10px}
.wachat-info h3{text-align:center;font-size:15px;margin:0;word-break:break-word}
.wa-inf-num{text-align:center;color:var(--muted);font-size:12.5px;margin:2px 0 18px}
.wachat-info dl{display:grid;gap:12px;margin:0}
.wachat-info dt{font-size:11.5px;color:var(--muted)}
.wachat-info dd{font-size:13px;font-weight:500;margin:2px 0 0;word-break:break-word}
@media(min-width:1280px){
  body.wa-full #panel-wachat .wachat-info{display:block}
  body.wa-full #panel-wachat .wachat-lcol{width:300px}
}
@media(max-width:860px){
  #panel-wachat .wachat-lcol{width:100%;border-right:0;flex:1;min-height:0}
  #panel-wachat .wachat-wrap.showing-thread .wachat-lcol{display:none}
  #waSearch{font-size:16px}
  .wa-th-back,.wa-th-more{display:inline-flex}
  .wa-th-top{padding:8px 10px;gap:8px}
  #waThreadHead .wa-th-top .wa-av{width:36px!important;height:36px!important;font-size:14px!important}
  .wa-th-act .btn{padding:6px 10px!important;font-size:12.5px!important}
  .wa-th-act{flex-wrap:nowrap}
  #waResolveBtn{font-size:0!important;padding:6px 8px!important;margin-left:0!important}
  #waResolveBtn svg{width:16px;height:16px}
  .wa-claimbar > span{min-width:0;flex-basis:100%}
  .wa-th-tools{display:none;padding:8px 10px}
  #waThreadHead.tools-open .wa-th-tools{display:flex}
  .wa-th-tools .wa-assign select{max-width:42vw}
  .wachat-info{display:none!important}
}

/* === v1.2.0 WA Claim UI ==================================================== */"""

def f_html(s, rel):
    s = rep(s, "/* === v1.2.0 WA Claim UI ==================================================== */", CSS, rel)
    s = rep(s, """          <div class="wachat-list" id="waConvList"><div style="padding:16px;color:var(--muted)">Memuat…</div></div>""",
               """          <div class="wachat-lcol"><!-- v1.2.125: wa-tampilan-sama -->
            <div class="wa-search"><span class="ic-s" data-ico="search" data-ico-size="16"></span><input type="search" id="waSearch" placeholder="Cari nama / nomor / pesan…" autocomplete="off"></div>
            <div class="wachat-list" id="waConvList"><div style="padding:16px;color:var(--muted)">Memuat…</div></div>
          </div>""", rel)
    s = rep(s, """                <button class="btn" id="waReplySend">Kirim</button>
              </div>
            </div>
          </div>
        </div>""", """                <button class="btn" id="waReplySend">Kirim</button>
              </div>
            </div>
          </div>
          <aside class="wachat-info" id="waInfo"></aside><!-- v1.2.125: panel info kontak -->
        </div>""", rel)
    s = rep(s, """<div style="display:flex;gap:8px">
                <button class="btn ghost" id="waAttachBtn\"""", """<div id="waComposeRow" style="display:flex;gap:8px">
                <button class="btn ghost" id="waAttachBtn\"""", rel)
    return s

HELPERS = r"""
  /* v1.2.125: wa-tampilan-sama — avatar inisial & panel info kontak */
  function waAvatarHtml(name, num, sz) {
    var pal = ['#5b3fd1', '#1f7a43', '#c2410c', '#0e7490', '#be185d', '#4338ca', '#b45309', '#7c3aed'];
    var h = 0, s = String(num || ''); for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
    var ch = String(name || '').trim().charAt(0).toUpperCase();
    var inner = (ch && /[A-Z0-9À-ɏ]/.test(ch)) ? esc(ch) : ico('user-round', Math.round(sz * 0.45));
    return '<div class="wa-av" style="width:' + sz + 'px;height:' + sz + 'px;font-size:' + Math.round(sz * 0.38) + 'px;background:' + pal[h % pal.length] + '">' + inner + '</div>';
  }
  function waInfoRender(res, k, claim) {
    var box = $('#waInfo'); if (!box) return;
    var nm = (k && k.name) || '';
    var chL = '', curCh = res.ch || 'utama';
    (res.channels || []).forEach(function (c) { if (c.id === curCh) chL = c.label + ((c.number && c.label !== '+' + c.number) ? ' (+' + c.number + ')' : ''); });
    var cs = CONTACT_STAGE[(k && k.stage) || 'new'] || CONTACT_STAGE.new;
    var row = function (l, v) { return '<div><dt>' + l + '</dt><dd>' + v + '</dd></div>'; };
    var t = (k && k.last_ts) ? waConvTimeInfo(k.last_ts) : null;
    box.innerHTML = waAvatarHtml(nm, res.number, 64) +
      '<h3>' + esc(nm || ('+' + res.number)) + '</h3><div class="wa-inf-num">+' + esc(res.number) + '</div><dl>' +
      row('Status', k ? statusBadgeHtml(k) : '—') +
      row('Lead Rating', '<span class="tag" style="background:' + cs.bg + ';color:' + cs.fg + '">' + esc(cs.label) + '</span>' + (k && k.vip ? ' <span class="tag" style="' + CONTACT_VIP_STYLE + '">' + ico('star', 12) + ' VIP</span>' : '')) +
      (chL ? row('Nomor bisnis', esc(chL)) : '') +
      row('Ditangani', claim ? esc(claim.agent_username) : '<span style="color:var(--muted);font-weight:400">Belum ada</span>') +
      (t && t.label ? row('Aktivitas terakhir', esc(t.label)) : '') +
      (k && k.flag === 'done' && k.flag_note ? row('Catatan', esc(k.flag_note)) : '') +
      '</dl>';
  }
"""

def f_js(s, rel):
    # ikon tambahan
    s = rep(s, "    'tag':           '<path d=\"M12.6 2.6A2",
               "    'more-horizontal': '<circle cx=\"12\" cy=\"12\" r=\"1\"/><circle cx=\"19\" cy=\"12\" r=\"1\"/><circle cx=\"5\" cy=\"12\" r=\"1\"/>',   // v1.2.125: wa-tampilan-sama\n    'tag':           '<path d=\"M12.6 2.6A2", rel)
    # 1. ringkasan sebaris judul
    s = rep(s, "kartu('unreplied', 'unreplied', 'clock-3', 'Belum dibalas')", "kartu('unreplied', 'unreplied', 'clock-3', 'belum dibalas')", rel)
    s = rep(s, "kartu('full_bot', 'fullbot', 'bot', 'Full bot (tanpa agent)')", "kartu('full_bot', 'fullbot', 'bot', 'full bot')", rel)
    s = rep(s, "kartu('done', 'done', 'check-circle-2', 'Selesai (ditandai / diam 24 jam)')", "kartu('done', 'done', 'check-circle-2', 'selesai')", rel)
    s = rep(s, "    wrap.parentNode.insertBefore(cards, wrap);\n",
               "    var _ph125 = $('#panel-wachat .ph');   // v1.2.125: wa-tampilan-sama — ringkasan sebaris judul\n    if (_ph125) _ph125.appendChild(cards); else wrap.parentNode.insertBefore(cards, wrap);\n", rel)
    # 2. daftar: cari + avatar
    s = rep(s, "    $('#waConvList').innerHTML = waState.convs.map(function (c) {",
               """    var _q125 = String(waState.q || '').trim().toLowerCase();   // v1.2.125: wa-tampilan-sama — kotak cari
    var _list125 = waState.convs;
    if (_q125) {
      var _qn125 = _q125.replace(/[^0-9]/g, ''); if (_qn125.charAt(0) === '0') _qn125 = '62' + _qn125.slice(1);
      _list125 = waState.convs.filter(function (c) {
        var hay = (String(c.name || '') + ' ' + String(c.last_q || c.last_text || '')).toLowerCase();
        return hay.indexOf(_q125) > -1 || (_qn125.length >= 3 && String(c.number).indexOf(_qn125) > -1);
      });
      if (!_list125.length) { $('#waConvList').innerHTML = '<div style="padding:16px;color:var(--muted)">Tidak ada yang cocok dengan "' + esc(waState.q.trim()) + '"</div>'; return; }
    }
    $('#waConvList').innerHTML = _list125.map(function (c) {""", rel)
    s = rep(s, """      return '<div class="wa-conv" data-num="' + esc(c.number) + '" style="' + bg + accent + '">' +""",
               """      return '<div class="wa-conv" data-num="' + esc(c.number) + '" style="' + bg + accent + '">' + waAvatarHtml(c.name, c.number, 38) + '<div class="wa-conv-b">' +""", rel)
    s = rep(s, """        '</div>';
    }).join('');
    $$('#waConvList .wa-conv').forEach(function (el) {""", """        '</div></div>';
    }).join('');
    $$('#waConvList .wa-conv').forEach(function (el) {""", rel)
    s = rep(s, "    waQrInit();   // v1.2.122: template-balasan\n",
               "    waQrInit();   // v1.2.122: template-balasan\n    if ($('#waSearch')) $('#waSearch').oninput = function () { waState.q = this.value; renderWaConvs(); };   // v1.2.125: wa-tampilan-sama\n", rel)
    # 3. kepala chat
    s = rep(s, "    var actionBtns = '';\n", "    var actionBtns = '', toolBtns = '';   // v1.2.125: toolBtns = baris alat terpisah\n", rel)
    s = rep(s, "      actionBtns += '<span class=\"wa-assign\">' + ico('user-round',13)", "      toolBtns += '<span class=\"wa-assign\">' + ico('user-round',13)", rel)
    s = rep(s, "      actionBtns += '<span class=\"wa-assign\" title=\"Balasan berikutnya", "      toolBtns += '<span class=\"wa-assign\" title=\"Balasan berikutnya", rel)
    a = one(s, "    var _metaRow =\n", rel)
    b = one(s, "\n    // Attach event handlers\n    if ($('#waEditName'))", rel)
    blok = s[a:b]
    vip = [l for l in blok.split('\n') if 'id="waVipToggle"' in l]
    assert len(vip) == 1, 'baris VIP'
    vipExpr = vip[0].strip()
    assert vipExpr.endswith("' VIP</button>' +"), vipExpr[-30:]
    vipExpr = vipExpr[:-2].rstrip() + ';'
    NEW = r"""    // v1.2.125: wa-tampilan-sama — kepala chat seperti contoh: avatar | nama, nomor + via, Lead Rating | aksi; baris alat terpisah
    var _metaRow = _statusBadge + (_konv ? waFlagBadgeHtml(_konv) : '') + _awaBadge + _attnBadge +
        ((_konv && _konv.flag === 'done' && _konv.flag_note) ? '<span style="color:var(--muted)">' + esc(_konv.flag_note) + '</span>' : '');
    var _csNow = CONTACT_STAGE[_stageNow] || CONTACT_STAGE.new;   // v1.2.124: wa-layout-penuh — Lead Rating di bawah nama/nomor
    var _vipHtml = """ + vipExpr + r"""
    var _viaTxt = (_konv && _konv.ch_label && (res.channels || []).length > 1) ? (_nama ? ' · ' : '') + '<span class="wa-th-via" title="Balasan dikirim dari nomor ini">via ' + esc(_konv.ch_label) + '</span>' : '';
    $('#waThreadHead').innerHTML =
      '<div class="wa-th-top">' +
        '<button type="button" class="wa-th-back" id="waThBack" title="Kembali ke daftar">' + ico('arrow-left',18) + '</button>' +
        waAvatarHtml(_nama, res.number, 44) +
        '<div class="wa-th-id">' +
          '<div class="wa-th-name">' + esc(_nama || ('+' + res.number)) + ' <a href="#" id="waEditName" title="Ubah nama" style="text-decoration:none;font-size:12px;font-weight:400">' + ico('pen-tool',12) + '</a></div>' +
          '<div class="wa-th-sub">' + (_nama ? '+' + esc(res.number) : '') + _viaTxt + '</div>' +
          '<div class="wa-rate-row"><label class="wa-rate" title="Lead Rating" style="background:' + _csNow.bg + ';color:' + _csNow.fg + '">' + ico('tag',12) +
            '<select id="waStageSelect">' + _stageOpts + '</select>' + ico('chevron-down',12) + '</label></div>' +
        '</div>' +
        '<div class="wa-th-act">' + actionBtns + '<button type="button" class="wa-th-more" id="waThMore" title="Serahkan, pindah nomor, VIP, lead">' + ico('more-horizontal',18) + '</button></div>' +
      '</div>' +
      '<div class="wa-th-tools">' + _metaRow + toolBtns + _vipHtml + _leadLink + '</div>';
    $('#waThreadHead').classList.toggle('tools-open', !!waState.thTools);
    if ($('#waThBack')) $('#waThBack').onclick = function () { var w = document.querySelector('.wachat-wrap'); if (w) w.classList.remove('showing-thread'); };
    if ($('#waThMore')) $('#waThMore').onclick = function () { waState.thTools = !waState.thTools; $('#waThreadHead').classList.toggle('tools-open', waState.thTools); };
    waInfoRender(res, _konv, claim);"""
    s = s[:a] + NEW + s[b:]
    # claim: muat daftar dulu (data claim) baru thread, supaya bar Claim langsung hilang
    s = rep(s, "        toast('Anda claim chat ini.');\n        fetchWaThread(num); fetchWaConvs();",
               "        toast('Anda claim chat ini.');\n        var _p125 = fetchWaConvs(); if (_p125 && _p125.then) _p125.then(function () { fetchWaThread(num); }); else fetchWaThread(num);   // v1.2.125", rel)
    # helper sebelum renderWaThread
    s = rep(s, "  function renderWaThread(res) {\n", HELPERS + "  function renderWaThread(res) {\n", rel)
    # 4. bar Claim & Balas
    s = rep(s, "' ke nomor ini. Kirim template lewat Blast dari nomor ini.' : '.');   // v1.2.116\n",
               r"""' ke nomor ini. Kirim template lewat Blast dari nomor ini.' : '.');   // v1.2.116
    // v1.2.125: wa-tampilan-sama — belum di-claim: bar "Claim & Balas" menggantikan kotak ketik
    var _needClaim = open && !claim && !_rsBlock && !!$('#waClaimBtn');
    var _noCl = !!(waState.noClaim && waState.noClaim[num]);
    if (_needClaim) {
      $('#waWindowNote').innerHTML = '<div class="wa-claimbar"><span>' + (waState.replyMode === 'manual'
          ? '<b>Antrean</b> — klik Claim untuk membalas' + (waState.isAdmin ? ', atau serahkan ke agent' : '') + '.'
          : '<b>Dijawab bot</b> — klik Claim agar bot berhenti dan Anda membalas sendiri.') +
        ((canReply && !_noCl) ? ' <a href="#" id="waNoClaimReply" title="Balas tanpa mengambil alih chat">Balas tanpa claim</a>' : '') + '</span>' +
        '<button type="button" class="btn" id="waClaimBar">' + ico('hand',14) + ' Claim &amp; Balas</button></div>';
    }
    if ($('#waComposeRow')) $('#waComposeRow').style.display = (_needClaim && !_noCl) ? 'none' : 'flex';
    if ($('#waClaimBar')) $('#waClaimBar').onclick = function () { waState.focusAfter = num; claimNumber(num); };
    if ($('#waNoClaimReply')) $('#waNoClaimReply').onclick = function (ev) {
      ev.preventDefault(); waState.noClaim = waState.noClaim || {}; waState.noClaim[num] = true; this.style.display = 'none';
      if ($('#waComposeRow')) $('#waComposeRow').style.display = 'flex'; $('#waReplyInput').focus();
    };
    if (waState.focusAfter === num && claim && canReply) { waState.focusAfter = null; setTimeout(function () { if ($('#waReplyInput')) $('#waReplyInput').focus(); }, 60); }
""", rel)
    return s

patch('api/index.php', f_api)
patch('dashboard/chatbot-ai/index.html', f_html)
patch('dashboard/chatbot-ai/app.js', f_js)
print('selesai')
