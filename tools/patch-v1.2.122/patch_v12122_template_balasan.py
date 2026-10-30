#!/usr/bin/env python3
r"""v1.2.122 template-balasan: template balasan cepat di Percakapan WA.
Template bersama dikelola Super Admin/Admin/Supervisor; semua (termasuk WA Agent) bisa memakai.
Pakai: tombol Template di kotak balas, atau ketik "/" + pintasan. Variabel {nama} dan {agen}.
Kotak balas jadi textarea (Shift+Enter = baris baru) supaya template berbaris banyak utuh.
Pakai: python3 patch_v12122_template_balasan.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.121)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.122: template-balasan'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def patch(rel, edits):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    for old, new in edits:
        n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:90]); s = s.replace(old, new)
    assert TAG in s, rel
    shutil.copy2(p, p + '.bak-v12122-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s); print('OK', rel)

patch('api/index.php', [
 (r"""define('DEI_VERSION', 'v1.2.121');   // v1.2.121: wa-balas-kutip""",
  r"""define('DEI_VERSION', 'v1.2.122');   // v1.2.122: template-balasan"""),
 (r"""function waSend($wa, $to, $text) {
    $GLOBALS['wa_last_out_id'] = '';""",
  r"""/* ---------- v1.2.122: template-balasan — template balasan cepat Percakapan WA ---------- */
define('WA_QR_FILE', DATA_DIR . '/wa-quick-replies.json');
define('WA_QR_MAX', 300);
function deiQrAll() {
    $a = readJson(WA_QR_FILE, []);
    return is_array($a) ? array_values(array_filter($a, 'is_array')) : [];
}
function deiQrSorted() {
    $l = deiQrAll();
    usort($l, function ($a, $b) { return strnatcasecmp((string)($a['title'] ?? ''), (string)($b['title'] ?? '')); });
    return $l;
}
function waSend($wa, $to, $text) {
    $GLOBALS['wa_last_out_id'] = '';"""),
 (r"""    case 'wa_send_media': {   // v1.2.120: wa-lampiran — multipart: number, caption, file""",
  r"""    /* ---------- v1.2.122: template-balasan ---------- */
    case 'qr_list': {
        requireAuth(['super_admin', 'admin', 'supervisor', 'wa_agent']);
        jsonOut(['ok' => true, 'items' => deiQrSorted(), 'max' => WA_QR_MAX]);
        break;
    }
    case 'qr_save': {
        $u = requireAuth(['super_admin', 'admin', 'supervisor']);
        $in = bodyInput();
        $id = preg_replace('/[^a-f0-9]/', '', (string)($in['id'] ?? ''));
        $text = trim(str_replace(["\r\n", "\r"], "\n", (string)($in['text'] ?? '')));
        $title = mb_substr(trim(preg_replace('/\s+/u', ' ', (string)($in['title'] ?? ''))), 0, 80);
        $sc = ltrim(strtolower(trim((string)($in['shortcut'] ?? ''))), '/');
        if ($text === '') jsonOut(['ok' => false, 'error' => 'Isi template wajib diisi.'], 400);
        if (mb_strlen($text) > 4000) jsonOut(['ok' => false, 'error' => 'Isi template maksimal 4.000 karakter.'], 400);
        if ($title === '') $title = mb_substr(trim(preg_replace('/\s+/u', ' ', $text)), 0, 40);
        if ($sc !== '' && !preg_match('/^[a-z0-9_-]{1,30}$/', $sc)) jsonOut(['ok' => false, 'error' => 'Pintasan hanya boleh huruf kecil, angka, - atau _ (maks 30, tanpa spasi).'], 400);
        $r = deiWithLock('wa-qr', function () use ($id, $text, $title, $sc, $u) {
            $l = deiQrAll();
            foreach ($l as $x) {
                if ($sc !== '' && ($x['shortcut'] ?? '') === $sc && ($x['id'] ?? '') !== $id) return 'Pintasan /' . $sc . ' sudah dipakai template "' . ($x['title'] ?? '') . '".';
            }
            $now = date('Y-m-d H:i:s');
            $item = ['id' => $id, 'title' => $title, 'shortcut' => $sc, 'text' => $text, 'updated_at' => $now, 'by' => (string)($u['username'] ?? '')];
            $found = false;
            if ($id !== '') {
                foreach ($l as $i => $x) { if (($x['id'] ?? '') === $id) { $l[$i] = $item; $found = true; break; } }
                if (!$found) return 'Template tidak ditemukan (mungkin sudah dihapus).';
            } else {
                if (count($l) >= WA_QR_MAX) return 'Batas ' . WA_QR_MAX . ' template tercapai. Hapus yang tidak dipakai dulu.';
                $item['id'] = substr(sha1(uniqid('', true) . mt_rand()), 0, 16);
                $l[] = $item;
            }
            writeJson(WA_QR_FILE, array_values($l));
            return $item;
        });
        if (!is_array($r)) jsonOut(['ok' => false, 'error' => (string)$r], 400);
        jsonOut(['ok' => true, 'item' => $r, 'items' => deiQrSorted()]);
        break;
    }
    case 'qr_delete': {
        requireAuth(['super_admin', 'admin', 'supervisor']);
        $in = bodyInput();
        $id = preg_replace('/[^a-f0-9]/', '', (string)($in['id'] ?? ''));
        if ($id === '') jsonOut(['ok' => false, 'error' => 'id wajib'], 400);
        deiWithLock('wa-qr', function () use ($id) {
            writeJson(WA_QR_FILE, array_values(array_filter(deiQrAll(), function ($x) use ($id) { return ($x['id'] ?? '') !== $id; })));
        });
        jsonOut(['ok' => true, 'items' => deiQrSorted()]);
        break;
    }

    case 'wa_send_media': {   // v1.2.120: wa-lampiran — multipart: number, caption, file"""),
])

patch('dashboard/chatbot-ai/index.html', [
 (r"""    .wachat-reply input{font-size:16px}""",
  r"""    .wachat-reply input, .wachat-reply textarea{font-size:16px}"""),
 (r"""                <input type="text" id="waReplyInput" placeholder="Tulis balasan manual…" style="flex:1">""",
  r"""                <button class="btn ghost" id="waQrBtn" type="button" title="Template balasan (atau ketik / di kotak balas)" style="padding:7px 10px"><span data-ico="file-text" data-ico-size="16"></span></button><!-- v1.2.122: template-balasan -->
                <textarea id="waReplyInput" rows="1" placeholder="Tulis balasan manual…" style="flex:1;resize:none;min-height:38px;max-height:150px;line-height:1.4;padding:8px 10px;font:inherit;border:1px solid var(--line);border-radius:8px;overflow-y:auto"></textarea>"""),
 (r"""              <!-- v1.2.121: wa-balas-kutip -->""",
  r"""              <div id="waQrPop" style="display:none;margin-bottom:8px;border:1px solid var(--line);border-radius:10px;background:var(--card, #fff);box-shadow:0 6px 20px rgba(0,0,0,.08);overflow:hidden"></div><!-- v1.2.122: template-balasan -->
              <!-- v1.2.121: wa-balas-kutip -->"""),
])

patch('dashboard/chatbot-ai/app.js', [
 (r"""    if ($('#waAttachBtn')) $('#waAttachBtn').disabled = !canReply || res.wa_prov === 'fonnte';   // v1.2.120: wa-lampiran""",
  r"""    if ($('#waAttachBtn')) $('#waAttachBtn').disabled = !canReply || res.wa_prov === 'fonnte';   // v1.2.120: wa-lampiran
    if ($('#waQrBtn')) $('#waQrBtn').disabled = !canReply;   // v1.2.122: template-balasan
    if (!canReply) waQrClose();"""),
 (r"""    waQuoteInit();   // v1.2.121: wa-balas-kutip""",
  r"""    waQuoteInit();   // v1.2.121: wa-balas-kutip
    waQrInit();   // v1.2.122: template-balasan"""),
 (r"""  function sendWaManual(num) {
    var inp = $('#waReplyInput'); var t = inp.value.trim();""",
  r"""  /* ---- v1.2.122: template-balasan — template balasan cepat (tombol Template / ketik "/") ---- */
  function waQrIsLead() { return !!user && ['super_admin', 'admin', 'supervisor'].indexOf(user.role) > -1; }
  function waQrLoad(force) {
    if (!force && waState.qrList && Date.now() - (waState.qrAt || 0) < 60000) return Promise.resolve(waState.qrList);
    return api('qr_list').then(function (r) {
      if (r && r.ok) { waState.qrList = r.items || []; waState.qrAt = Date.now(); }
      return waState.qrList || [];
    });
  }
  function waQrFill(t) {
    var nm = '', c = (waState.convs || []).filter(function (x) { return String(x.number) === String(waState.current); })[0];
    if (c && c.name) nm = String(c.name).trim();
    var ag = (user && (user.name || user.username)) || '';
    return String(t || '').replace(/\{nama\}/gi, nm).replace(/\{agen\}/gi, ag)
      .replace(/[ \t]{2,}/g, ' ').replace(/ +([,.!?])/g, '$1').replace(/^[ \t]+|[ \t]+$/gm, '');
  }
  function waQrMatch(q) {
    q = String(q || '').toLowerCase().trim();
    var l = waState.qrList || [];
    if (!q) return l.slice();
    var a = [], b = [];
    l.forEach(function (x) {
      var sc = String(x.shortcut || ''), hay = (x.title + ' ' + sc + ' ' + x.text).toLowerCase();
      if (sc && sc.indexOf(q) === 0) a.push(x); else if (hay.indexOf(q) > -1) b.push(x);
    });
    return a.concat(b);
  }
  function waQrAutosize() {
    var el = $('#waReplyInput'); if (!el || el.tagName !== 'TEXTAREA') return;
    el.style.height = 'auto'; el.style.height = Math.min(150, Math.max(38, el.scrollHeight + 2)) + 'px';
  }
  function waQrClose() {
    waState.qrOpen = null;
    if ($('#waQrPop')) { $('#waQrPop').style.display = 'none'; $('#waQrPop').innerHTML = ''; }
  }
  // mode: 'btn' (dari tombol, ada kotak cari) | 'slash' (ketik "/" di kotak balas)
  function waQrOpen(mode, q) {
    var pop = $('#waQrPop'); if (!pop) return;
    waState.qrOpen = { mode: mode, q: q || '', sel: 0 };
    if (mode === 'btn') {
      pop.innerHTML = '<div style="padding:8px;border-bottom:1px solid var(--line)"><input type="text" id="waQrSearch" placeholder="Cari template…" autocomplete="off" style="width:100%"></div><div id="waQrList"></div>' + waQrFoot();
      pop.style.display = 'block';
      $('#waQrSearch').value = q || '';
      $('#waQrSearch').oninput = function () { waState.qrOpen.q = this.value; waState.qrOpen.sel = 0; waQrRenderList(); };
      $('#waQrSearch').onkeydown = waQrKey;
      setTimeout(function () { if ($('#waQrSearch')) $('#waQrSearch').focus(); }, 0);
    } else {
      pop.innerHTML = '<div id="waQrList"></div>' + waQrFoot();
      pop.style.display = 'block';
    }
    if ($('#waQrManage')) $('#waQrManage').onclick = function (e) { e.preventDefault(); waQrClose(); waQrManager(); };
    waQrRenderList();
    waQrLoad(false).then(function () { if (waState.qrOpen) waQrRenderList(); });
  }
  function waQrFoot() {
    return '<div style="display:flex;justify-content:space-between;gap:8px;padding:6px 10px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)">' +
      '<span>Ketik <strong>/</strong> di kotak balas untuk cari cepat · ↑↓ Enter</span>' +
      (waQrIsLead() ? '<a href="#" id="waQrManage">Kelola template</a>' : '') + '</div>';
  }
  function waQrRenderList() {
    var o = waState.qrOpen, box = $('#waQrList'); if (!o || !box) return;
    var l = waQrMatch(o.q);
    o.items = l;
    if (o.sel >= l.length) o.sel = Math.max(0, l.length - 1);
    if (!waState.qrList) { box.innerHTML = '<div style="padding:12px;color:var(--muted);font-size:13px">Memuat…</div>'; return; }
    if (!l.length) {
      box.innerHTML = '<div style="padding:12px;color:var(--muted);font-size:13px">' +
        (waState.qrList.length ? 'Tidak ada template yang cocok.' : 'Belum ada template.' + (waQrIsLead() ? ' Klik <strong>Kelola template</strong> untuk menambah.' : ' Minta Admin/Supervisor menambahkannya.')) + '</div>';
      return;
    }
    box.innerHTML = '<div style="max-height:230px;overflow-y:auto">' + l.map(function (x, i) {
      var prev = String(x.text).replace(/\s+/g, ' ');
      return '<div class="wa-qr-it" data-i="' + i + '" style="padding:7px 12px;cursor:pointer;' + (i === o.sel ? 'background:var(--brand-soft)' : '') + '">' +
        '<div style="display:flex;gap:8px;align-items:center;font-size:13px"><strong style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(x.title) + '</strong>' +
        (x.shortcut ? '<span class="tag" style="font-size:11px;padding:1px 6px">/' + esc(x.shortcut) + '</span>' : '') + '</div>' +
        '<div style="font-size:12px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(prev) + '</div></div>';
    }).join('') + '</div>';
    $$('#waQrList .wa-qr-it').forEach(function (el) {
      el.onmousedown = function (e) { e.preventDefault(); waQrPick(+el.getAttribute('data-i')); };
    });
    var cur = box.querySelector('.wa-qr-it[data-i="' + o.sel + '"]');
    if (cur && cur.scrollIntoView) cur.scrollIntoView({ block: 'nearest' });
  }
  function waQrPick(i) {
    var o = waState.qrOpen; if (!o || !o.items || !o.items[i]) return;
    var t = waQrFill(o.items[i].text), inp = $('#waReplyInput');
    if (o.mode === 'slash' || !inp.value.trim()) inp.value = t;
    else {
      var s = inp.selectionStart != null ? inp.selectionStart : inp.value.length, e = inp.selectionEnd != null ? inp.selectionEnd : s;
      var pre = inp.value.slice(0, s), post = inp.value.slice(e);
      inp.value = pre + (pre && !/\s$/.test(pre) ? ' ' : '') + t + post;
    }
    waQrClose();
    inp.focus();
    try { inp.setSelectionRange(inp.value.length, inp.value.length); } catch (er) {}
    waQrAutosize();
  }
  function waQrKey(e) {
    var o = waState.qrOpen; if (!o) return false;
    var n = (o.items || []).length;
    if (e.key === 'ArrowDown') { o.sel = n ? (o.sel + 1) % n : 0; waQrRenderList(); }
    else if (e.key === 'ArrowUp') { o.sel = n ? (o.sel - 1 + n) % n : 0; waQrRenderList(); }
    else if (e.key === 'Enter' || e.key === 'Tab') { if (!n) { if (o.mode === 'slash' && e.key === 'Enter') return false; waQrClose(); } else waQrPick(o.sel); }
    else if (e.key === 'Escape') { waQrClose(); if (o.mode === 'btn') $('#waReplyInput').focus(); }
    else return false;
    e.preventDefault(); e.stopImmediatePropagation();
    return true;
  }
  function waQrInit() {
    var inp = $('#waReplyInput');
    if (!inp || waState.qrBound) return;
    waState.qrBound = true;
    $('#waQrBtn').onclick = function () {
      if (this.disabled) return;
      if (waState.qrOpen && waState.qrOpen.mode === 'btn') { waQrClose(); return; }
      waQrOpen('btn', '');
    };
    // capture: berjalan sebelum handler Enter = kirim (bawaan)
    inp.addEventListener('keydown', function (e) {
      if (waState.qrOpen && waState.qrOpen.mode === 'slash' && waQrKey(e)) return;
      if (e.key === 'Enter' && e.shiftKey) { e.stopImmediatePropagation(); return; }   // Shift+Enter = baris baru
      if (e.key === 'Enter' && !e.isComposing) e.preventDefault();                      // Enter = kirim (tanpa baris baru)
    }, true);
    inp.addEventListener('input', function () {
      waQrAutosize();
      var m = /^\/(\S{0,30})$/.exec(inp.value);
      if (m && !inp.disabled) {
        if (!waState.qrOpen || waState.qrOpen.mode !== 'slash') waQrOpen('slash', m[1]);
        else { waState.qrOpen.q = m[1]; waState.qrOpen.sel = 0; waQrRenderList(); }
      } else if (waState.qrOpen && waState.qrOpen.mode === 'slash') waQrClose();
    });
    inp.addEventListener('blur', function () { setTimeout(function () { if (waState.qrOpen && waState.qrOpen.mode === 'slash' && document.activeElement !== inp) waQrClose(); }, 150); });
    document.addEventListener('mousedown', function (e) {
      var o = waState.qrOpen; if (!o || o.mode !== 'btn') return;
      if (!e.target.closest('#waQrPop') && !e.target.closest('#waQrBtn')) waQrClose();
    });
  }
  /* Kelola template (Super Admin/Admin/Supervisor) */
  function waQrManager() {
    var ov = document.createElement('div');
    ov.id = 'waQrMgr';
    ov.style.cssText = 'position:fixed;inset:0;background:rgba(15,23,42,.45);z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px';
    ov.innerHTML = '<div class="card" style="width:100%;max-width:720px;max-height:92vh;overflow:auto;margin:0">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:10px"><h3 style="margin:0">Template Balasan WA</h3>' +
      '<button type="button" id="qrmX" class="btn ghost sm" title="Tutup">' + ico('x', 16) + '</button></div>' +
      '<p class="help" style="margin:0 0 12px">Dipakai semua agent dari kotak balas Percakapan WA (tombol ' + ico('file-text', 13) + ' atau ketik <strong>/pintasan</strong>). ' +
      'Variabel: <code>{nama}</code> = nama kontak, <code>{agen}</code> = nama pengirim.</p>' +
      '<div style="border:1px solid var(--line);border-radius:10px;padding:12px;margin-bottom:12px">' +
        '<div class="grid2"><div class="row"><label class="fl">Judul</label><input type="text" id="qrmTitle" maxlength="80" placeholder="mis. Info harga paket"></div>' +
        '<div class="row"><label class="fl">Pintasan</label><input type="text" id="qrmSc" maxlength="31" placeholder="mis. harga (dipanggil /harga)"></div></div>' +
        '<div class="row"><label class="fl">Isi</label><textarea id="qrmText" rows="5" maxlength="4000" placeholder="Halo Kak {nama}, ..."></textarea></div>' +
        '<div style="display:flex;gap:8px;flex-wrap:wrap"><button type="button" class="btn" id="qrmSave">Simpan template</button>' +
        '<button type="button" class="btn ghost" id="qrmReset">Baru</button><span id="qrmMode" class="help" style="align-self:center"></span></div>' +
      '</div><div id="qrmList"></div></div>';
    document.body.appendChild(ov);
    var editId = '';
    var tutup = function () { ov.remove(); document.removeEventListener('keydown', esck); };
    var esck = function (e) { if (e.key === 'Escape') tutup(); };
    document.addEventListener('keydown', esck);
    ov.onclick = function (e) { if (e.target === ov) tutup(); };
    $('#qrmX').onclick = tutup;
    var reset = function () { editId = ''; $('#qrmTitle').value = ''; $('#qrmSc').value = ''; $('#qrmText').value = ''; $('#qrmMode').textContent = 'Template baru'; };
    var render = function () {
      var l = waState.qrList || [];
      $('#qrmList').innerHTML = l.length ? l.map(function (x) {
        return '<div style="border-top:1px solid var(--line);padding:10px 2px;display:flex;gap:10px;align-items:flex-start">' +
          '<div style="flex:1;min-width:0"><strong>' + esc(x.title) + '</strong>' + (x.shortcut ? ' <span class="tag" style="font-size:11px">/' + esc(x.shortcut) + '</span>' : '') +
          '<div style="white-space:pre-wrap;font-size:13px;color:var(--muted);margin-top:3px;max-height:4.2em;overflow:hidden">' + esc(x.text) + '</div></div>' +
          '<div style="white-space:nowrap"><button type="button" class="btn ghost sm qrm-e" data-id="' + esc(x.id) + '">Edit</button> ' +
          '<button type="button" class="btn danger sm qrm-d" data-id="' + esc(x.id) + '">Hapus</button></div></div>';
      }).join('') : '<p class="help" style="margin:0">Belum ada template.</p>';
      $$('#qrmList .qrm-e').forEach(function (b) { b.onclick = function () {
        var x = (waState.qrList || []).filter(function (y) { return y.id === b.dataset.id; })[0]; if (!x) return;
        editId = x.id; $('#qrmTitle').value = x.title || ''; $('#qrmSc').value = x.shortcut || ''; $('#qrmText').value = x.text || '';
        $('#qrmMode').textContent = 'Mengedit "' + x.title + '"'; $('#qrmText').focus();
      }; });
      $$('#qrmList .qrm-d').forEach(function (b) { b.onclick = function () {
        if (!confirm('Hapus template ini?')) return;
        api('qr_delete', { method: 'POST', body: { id: b.dataset.id } }).then(function (r) {
          if (r && r.ok) { waState.qrList = r.items || []; waState.qrAt = Date.now(); if (editId === b.dataset.id) reset(); render(); toast('Template dihapus.'); }
          else toast((r && r.error) || 'Gagal menghapus.', true);
        });
      }; });
    };
    $('#qrmReset').onclick = reset;
    $('#qrmSave').onclick = function () {
      var body = { id: editId, title: $('#qrmTitle').value, shortcut: $('#qrmSc').value, text: $('#qrmText').value };
      if (!body.text.trim()) { toast('Isi template wajib diisi.', true); $('#qrmText').focus(); return; }
      this.disabled = true; var btn = this;
      api('qr_save', { method: 'POST', body: body }).then(function (r) {
        btn.disabled = false;
        if (r && r.ok) { waState.qrList = r.items || []; waState.qrAt = Date.now(); toast(editId ? 'Template diperbarui.' : 'Template ditambahkan.'); reset(); render(); }
        else toast((r && r.error) || 'Gagal menyimpan.', true);
      });
    };
    reset();
    $('#qrmList').innerHTML = '<p class="help">Memuat…</p>';
    waQrLoad(true).then(render);
  }

  function sendWaManual(num) {
    var inp = $('#waReplyInput'); var t = inp.value.trim();"""),
 # setelah kirim teks: kecilkan lagi textarea
 (r"""        if (res && res.ok) { inp.value = ''; waQuoteClear(); fetchWaThread(num); fetchWaConvs(); }""",
  r"""        if (res && res.ok) { inp.value = ''; waQuoteClear(); waQrAutosize(); fetchWaThread(num); fetchWaConvs(); }   // v1.2.122"""),
])
