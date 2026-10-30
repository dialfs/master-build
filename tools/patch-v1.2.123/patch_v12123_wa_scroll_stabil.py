#!/usr/bin/env python3
r"""v1.2.123 wa-scroll-stabil: perbaikan bug Percakapan WA — pada percakapan panjang layar naik sendiri saat di-scroll.
Sebab: token login diperbarui di setiap permintaan dan ikut di URL media; polling 6 detik menggambar ulang seluruh thread
dengan URL baru -> semua gambar dimuat ulang (tinggi 0 sementara, lazy) -> hitungan posisi scroll meleset.
Perbaikan (frontend saja):
 1. URL media memakai token tetap (diperbarui 30 menit sekali).
 2. Thread tidak digambar ulang bila isinya sama persis.
 3. Bila berubah: posisi baca dikunci ke bubble yang sedang terlihat (bukan selisih tinggi).
 4. Saat di posisi paling bawah, tetap menempel ke bawah walau gambar/video selesai dimuat belakangan.
Pakai: python3 patch_v12123_wa_scroll_stabil.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.122)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.123: wa-scroll-stabil'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def patch(rel, edits):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    for old, new in edits:
        n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:90]); s = s.replace(old, new)
    assert TAG in s, rel
    shutil.copy2(p, p + '.bak-v12123-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s); print('OK', rel)

patch('api/index.php', [
 (r"""define('DEI_VERSION', 'v1.2.122');   // v1.2.122: template-balasan""",
  r"""define('DEI_VERSION', 'v1.2.123');   // v1.2.123: wa-scroll-stabil"""),
])

patch('dashboard/chatbot-ai/app.js', [
 # 1. token media tetap
 (r"""  /* v1.2.94: wa-media — gambar/video/audio/dokumen di thread WA */""",
  r"""  /* v1.2.123: wa-scroll-stabil — token untuk URL media dibuat tetap (token login berganti di setiap
   * permintaan; bila ikut berganti, semua gambar dimuat ulang tiap polling dan posisi scroll meleset).
   * Token lama tetap sah sampai 8 jam tanpa aktivitas; diperbarui 30 menit sekali. */
  function waMediaTok() {
    if (!waState.mTok || Date.now() - (waState.mTokAt || 0) > 30 * 60000) { waState.mTok = token; waState.mTokAt = Date.now(); }
    return waState.mTok;
  }
  /* v1.2.94: wa-media — gambar/video/audio/dokumen di thread WA */"""),
 (r"""'?action=wa_media&f=' + encodeURIComponent(md.file) + '&token=' + encodeURIComponent(token);""",
  r"""'?action=wa_media&f=' + encodeURIComponent(md.file) + '&token=' + encodeURIComponent(waMediaTok());   // v1.2.123"""),
 # 2. kunci bubble (data-k)
 (r"""return '<div' + (rid ? ' data-mid="' + esc(rid) + '"' : '') + ' style="max-width:78%;'""",
  r"""return '<div' + (rid ? ' data-mid="' + esc(rid) + '"' : '') + ((rq && rq.k) ? ' data-k="' + esc(rq.k) + '"' : '') /* v1.2.123 */ + ' style="max-width:78%;'"""),
 (r"""{ id: m.wamid, reply_to: m.reply_to }""",
  r"""{ id: m.wamid, reply_to: m.reply_to, k: 'q' + m.ts + (m.wamid || '') }"""),
 (r"""{ id: m.out_id, reply_to: m.q ? null : m.reply_to }""",
  r"""{ id: m.out_id, reply_to: m.q ? null : m.reply_to, k: 'a' + m.ts + (m.out_id || '') }"""),
 (r"""(m.media_out || []).forEach(function (md) { h += waBubble('', 'bot', m.ts, md); });""",
  r"""(m.media_out || []).forEach(function (md, j) { h += waBubble('', 'bot', m.ts, md, '', { k: 'o' + j + m.ts }); });   // v1.2.123"""),
 # 3. render stabil
 (r"""    // wa-scroll-preserve: cek posisi scroll SEBELUM re-render
    var _waBody = $('#waThreadBody');
    var _waWasBottom = _waBody ? (_waBody.scrollHeight - _waBody.scrollTop - _waBody.clientHeight < 60) : true;
    var _waPrevTop = _waBody ? _waBody.scrollTop : 0;
    var _waPrevHeight = _waBody ? _waBody.scrollHeight : 0;""",
  r"""    // v1.2.123: wa-scroll-stabil — catat posisi SEBELUM render: di bawah? atau bubble mana yang sedang terlihat
    var _waBody = $('#waThreadBody');
    var _waSame = waState.bodyNum === num;
    var _sc = waScroller(), _win = _sc && _sc !== _waBody;   // desktop: kotak thread; HP: halaman
    var _waWasBottom = _sc ? (_win ? (_waSame && (waState.waStick || waScGap(_sc) < 60))
                                   : (!_waSame || waState.waStick || waScGap(_sc) < 60)) : true;
    var _waPrevTop = _sc ? _sc.scrollTop : 0;
    var _waAnc = null;
    if (_sc && _waSame && !_waWasBottom) {
      var _bt = waScTop(_sc), _ks = _waBody.querySelectorAll('[data-k]');
      for (var _i = 0; _i < _ks.length; _i++) {
        var _rc = _ks[_i].getBoundingClientRect();
        if (_rc.bottom > _bt + 1) { _waAnc = { k: _ks[_i].getAttribute('data-k'), off: _rc.top - _bt }; break; }
      }
    }"""),
 (r"""    $('#waThreadBody').innerHTML = _wiH + (res.messages || []).map(function (m) {""",
  r"""    var _waHtml = _wiH + (res.messages || []).map(function (m) {   // v1.2.123: dirakit dulu, dipasang hanya bila berubah"""),
 (r"""    }).join('') || '<div style="color:var(--muted);margin:auto">Belum ada pesan.</div>';
    // wa-scroll-preserve: scroll ke bawah HANYA kalau user tadi di bawah (ngikutin chat).
    // Kalau user scroll ke atas baca history, pertahankan posisi (jangan ketarik ke bawah).
    if (_waBody) {
      if (_waWasBottom) {
        _waBody.scrollTop = _waBody.scrollHeight;
      } else {
        // pertahankan posisi relatif: kompensasi kalau ada pesan baru di bawah (tinggi bertambah)
        _waBody.scrollTop = _waPrevTop + (_waBody.scrollHeight - _waPrevHeight);
      }
    }""",
  r"""    }).join('') || '<div style="color:var(--muted);margin:auto">Belum ada pesan.</div>';
    // v1.2.123: wa-scroll-stabil — isi sama persis (polling tanpa pesan baru): DOM & gambar dibiarkan, posisi tidak disentuh
    if (_waBody && !(_waSame && waState.bodyHtml === _waHtml)) {
      _waBody.innerHTML = _waHtml;
      waState.bodyNum = num; waState.bodyHtml = _waHtml;
      _sc = waScroller(); _win = _sc && _sc !== _waBody;
      if (!_sc) {}
      else if (_waWasBottom) {
        _sc.scrollTop = _sc.scrollHeight;   // ikuti chat
        waState.waStick = true; waState.waLastTop = _sc.scrollTop;
      } else if (!_waSame && _win) {
        waState.waStick = false; waState.waLastTop = _sc.scrollTop;   // HP: buka chat lain, posisi halaman tidak diubah (seperti sebelumnya)
      } else {
        // sedang membaca pesan lama: kunci ke bubble yang tadi terlihat
        var _el = null;
        if (_waAnc) { var _ks2 = _waBody.querySelectorAll('[data-k]'); for (var _j = 0; _j < _ks2.length; _j++) { if (_ks2[_j].getAttribute('data-k') === _waAnc.k) { _el = _ks2[_j]; break; } } }
        if (_el) _sc.scrollTop += (_el.getBoundingClientRect().top - waScTop(_sc)) - _waAnc.off;
        else _sc.scrollTop = _waPrevTop;
        waState.waStick = false; waState.waLastTop = _sc.scrollTop;
      }
    }"""),
 (r"""    wiThreadBind(res);   // v1.2.105
    $('#waReplyBar').style.display = 'block';""",
  r"""    wiThreadBind(res);   // v1.2.105
    $('#waReplyBar').style.display = 'block';
    if (waState.waStick && (_sc = waScroller())) { _sc.scrollTop = _sc.scrollHeight; waState.waLastTop = _sc.scrollTop; }   // v1.2.123: kotak balas memperkecil area chat"""),
 # 4. tetap di bawah walau media dimuat belakangan
 (r"""    waQuoteInit();   // v1.2.121: wa-balas-kutip""",
  r"""    waQuoteInit();   // v1.2.121: wa-balas-kutip
    waScrollInit();   // v1.2.123: wa-scroll-stabil"""),
 (r"""  function waQuoteWho(r) {""",
  r"""  // v1.2.123: wa-scroll-stabil — penggulir thread: kotak thread (desktop) atau halaman (HP, thread memanjang)
  function waScroller() {
    var b = $('#waThreadBody'); if (!b) return null;
    var w = b.closest ? b.closest('.wachat-wrap') : null;
    return (w && getComputedStyle(w).flexDirection === 'column') ? (document.scrollingElement || document.documentElement) : b;
  }
  function waScIsWin(sc) { return sc === document.scrollingElement || sc === document.documentElement; }
  function waScTop(sc) { return waScIsWin(sc) ? 0 : sc.getBoundingClientRect().top; }
  function waScGap(sc) { return sc.scrollHeight - sc.scrollTop - (waScIsWin(sc) ? window.innerHeight : sc.clientHeight); }
  // Saat di posisi paling bawah, tetap di bawah walau gambar/video selesai dimuat belakangan.
  // "Menempel di bawah" hanya lepas bila pengguna menggulir KE ATAS (bukan karena tata letak berubah, mis. kotak balas muncul).
  function waScrollInit() {
    var b = $('#waThreadBody');
    if (!b || waState.scrollBound) return;
    waState.scrollBound = true;
    var onScroll = function (fromWin) {
      var sc = waScroller(); if (!sc || waScIsWin(sc) !== fromWin) return;
      if (!$('#panel-wachat') || !$('#panel-wachat').classList.contains('active')) return;
      var t = sc.scrollTop;
      if (waScGap(sc) < 60) waState.waStick = true;
      else if (t < (waState.waLastTop || 0) - 1) waState.waStick = false;
      waState.waLastTop = t;
    };
    b.addEventListener('scroll', function () { onScroll(false); }, { passive: true });
    window.addEventListener('scroll', function () { onScroll(true); }, { passive: true });
    var tempel = function () { var sc = waScroller(); if (sc && waState.waStick) { sc.scrollTop = sc.scrollHeight; waState.waLastTop = sc.scrollTop; } };
    b.addEventListener('load', tempel, true);             // <img> (event load tidak menggelembung -> capture)
    b.addEventListener('loadedmetadata', tempel, true);   // <video>/<audio>
  }
  function waQuoteWho(r) {"""),
])
