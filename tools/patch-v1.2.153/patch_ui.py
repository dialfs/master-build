#!/usr/bin/env python3
"""v1.2.153 jadwal-kirim — dashboard (app.js + index.html). Idempoten. Pakai: patch_ui.py <dei-tenant>"""
import sys, shutil, time
T = sys.argv[1]
J = T + '/dashboard/chatbot-ai/app.js'
H = T + '/dashboard/chatbot-ai/index.html'
js = open(J, encoding='utf-8').read()
ht = open(H, encoding='utf-8').read()
if 'v1.2.153: jadwal-kirim' in js and 'v1.2.153: jadwal-kirim' in ht:
    print('sudah dipatch'); sys.exit(0)
stamp = time.strftime('%Y%m%d-%H%M%S')
shutil.copy2(J, J + '.bak-v12153-' + stamp); shutil.copy2(H, H + '.bak-v12153-' + stamp)

def rep(s, old, new, cnt=1):
    n = s.count(old)
    assert n == cnt, f'anchor {n}x (harus {cnt}): {old[:90]!r}'
    return s.replace(old, new)

# ---------- index.html ----------
ht = rep(ht, '<script src="app.js?v=1.2.152"></script><!-- v1.2.152: tombol-warna -->',
             '<script src="app.js?v=1.2.153"></script><!-- v1.2.153: jadwal-kirim -->')
ht = rep(ht, '<div id="waQrPop" style="display:none;',
             '<div id="waSchedPop" class="wa-sched-pop" style="display:none"></div><!-- v1.2.153: jadwal-kirim -->\n              <div id="waQrPop" style="display:none;')
ht = rep(ht, '                <button class="btn" id="waReplySend">Kirim</button>',
             '                <button class="btn ghost" id="waSchedBtn" type="button" title="Jadwalkan kirim pesan ini" style="padding:7px 10px"><span data-ico="alarm-clock" data-ico-size="16"></span></button><!-- v1.2.153: jadwal-kirim -->\n'
             '                <button class="btn" id="waReplySend">Kirim</button>')
ht = rep(ht, '#waComposeRow{align-items:flex-end}',
    '#waComposeRow{align-items:flex-end}\n'
    '/* v1.2.153: jadwal-kirim */\n'
    '.wa-sched-pop{margin-bottom:8px;border:1px solid var(--line);border-radius:10px;background:var(--card,#fff);box-shadow:0 6px 20px rgba(0,0,0,.08);padding:12px;font-size:13px}\n'
    '.wa-sched-pop .ws-row{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:8px}\n'
    '.wa-sched-pop input[type=datetime-local]{font:inherit;padding:6px 8px;border:1px solid var(--line);border-radius:8px;min-width:0;flex:1 1 200px}\n'
    '.wa-sched-pop .ws-chip{border:1px solid var(--line);background:transparent;border-radius:999px;padding:4px 10px;font:inherit;font-size:12px;cursor:pointer;color:inherit}\n'
    '.wa-sched-pop .ws-chip:hover{background:var(--brand-soft)}\n'
    '.wa-sched-pop .ws-warn{color:#b45309;margin-bottom:8px}\n'
    '.wa-sbub{align-self:flex-end;max-width:78%;background:#f8fafc;border:1.5px dashed #94a3b8;color:var(--ink);padding:8px 12px;border-radius:12px;margin:4px 0;white-space:pre-wrap;font-size:14px;line-height:1.45}\n'
    '.wa-sbub.bad{border-color:#fca5a5;background:#fef2f2}\n'
    '.wa-sbub .ws-meta{font-size:11px;color:var(--muted);margin-top:6px;white-space:normal;display:flex;gap:4px 10px;flex-wrap:wrap;align-items:center}\n'
    '.wa-sbub .ws-meta a{color:var(--brand);text-decoration:none;font-weight:600}\n'
    '.wa-sbub.bad .ws-meta{color:#991b1b}')

# ---------- app.js ----------
js = rep(js, "    'clock-3':           '<circle cx=\"12\" cy=\"12\" r=\"10\"/><polyline points=\"12 6 12 12 16.5 12\"/>',\n",
    "    'clock-3':           '<circle cx=\"12\" cy=\"12\" r=\"10\"/><polyline points=\"12 6 12 12 16.5 12\"/>',\n"
    "    'alarm-clock':       '<circle cx=\"12\" cy=\"13\" r=\"8\"/><path d=\"M12 9v4l2 2\"/><path d=\"M5 3 2 6\"/><path d=\"m22 6-3-3\"/><path d=\"M6.38 18.7 4 21\"/><path d=\"M17.64 18.67 20 21\"/>',   // v1.2.153: jadwal-kirim\n")

# daftar: simpan jumlah jadwal tertunda
js = rep(js, "      waState.agents = res.agents || [];\n      waState.channels = res.channels || [];   // v1.2.98: multi-nomor\n",
             "      waState.agents = res.agents || [];\n      waState.schedCounts = res.sched || {};   // v1.2.153: jadwal-kirim\n      waState.channels = res.channels || [];   // v1.2.98: multi-nomor\n")
js = rep(js, "      if (c.has_history) stageBadge += ",
             "      if ((waState.schedCounts || {})[c.number]) stageBadge += ' <span class=\"tag\" style=\"background:#e0f2fe;color:#075985\" title=\"Pesan terjadwal menunggu dikirim\">' + ico('alarm-clock', 11) + ' ' + waState.schedCounts[c.number] + ' terjadwal</span>';   // v1.2.153: jadwal-kirim\n"
             "      if (c.has_history) stageBadge += ")

# thread: gelembung jadwal di akhir thread (ikut dibandingkan supaya polling tidak menggulir)
js = rep(js, "    }).join('') || '<div style=\"color:var(--muted);margin:auto\">Belum ada pesan.</div>';\n    // v1.2.123: wa-scroll-stabil — isi sama persis",
             "    }).join('') || '<div style=\"color:var(--muted);margin:auto\">Belum ada pesan.</div>';\n"
             "    waState.sched = res.sched || []; waState.schedWinEnd = res.win_end || 0; waState.schedNum = num;   // v1.2.153: jadwal-kirim\n"
             "    _waHtml += waSchedHtml(waState.sched);\n"
             "    // v1.2.123: wa-scroll-stabil — isi sama persis")
js = rep(js, "    if ($('#waQrBtn')) $('#waQrBtn').disabled = !canReply;   // v1.2.122: template-balasan\n",
             "    if ($('#waQrBtn')) $('#waQrBtn').disabled = !canReply;   // v1.2.122: template-balasan\n"
             "    if ($('#waSchedBtn')) $('#waSchedBtn').disabled = !canReply;   // v1.2.153: jadwal-kirim\n"
             "    if (!canReply || (waState.schedOpen && waState.schedOpen !== num)) waSchedClose();\n")
js = rep(js, "    waQrInit();   // v1.2.122: template-balasan\n",
             "    waQrInit();   // v1.2.122: template-balasan\n    waSchedInit();   // v1.2.153: jadwal-kirim\n")

FN = r'''
  /* ---- v1.2.153: jadwal-kirim — jadwalkan pesan di thread Percakapan WA ---- */
  function waSchedFmt(ts) {
    var d = new Date(ts * 1000), now = new Date();
    var hm = ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
    var t0 = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    var dd = Math.floor((new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime() - t0) / 86400000);
    if (dd === 0) return 'hari ini ' + hm;
    if (dd === 1) return 'besok ' + hm;
    var H = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab'], B = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
    return H[d.getDay()] + ' ' + d.getDate() + ' ' + B[d.getMonth()] + (d.getFullYear() !== now.getFullYear() ? ' ' + d.getFullYear() : '') + ' ' + hm;
  }
  function waSchedHtml(list) {
    var ST = { skipped: 'Tidak dikirim', expired: 'Kedaluwarsa', failed: 'Gagal terkirim' };
    return (list || []).filter(function (x) { return ['pending', 'sending', 'skipped', 'expired', 'failed'].indexOf(x.status) > -1; }).map(function (x) {
      var live = x.status === 'pending' || x.status === 'sending';
      var meta = live
        ? ico('alarm-clock', 12) + ' <b>Terjadwal ' + esc(waSchedFmt(x.at)) + '</b><span>oleh ' + esc(x.by_name || x.by) + '</span>' +
          (x.cancel_on_reply ? '<span title="Batal otomatis bila pelanggan membalas sebelum jam kirim">· batal bila dibalas</span>' : '') +
          (x.status === 'sending' ? '<span>· sedang dikirim…</span>' : '') +
          (x.last_err ? '<span style="color:#b45309">· dicoba ulang: ' + esc(x.last_err) + '</span>' : '') +
          ((x.can && x.status === 'pending') ? '<a href="#" data-sact="edit" data-sid="' + esc(x.id) + '">Edit</a><a href="#" data-sact="now" data-sid="' + esc(x.id) + '">Kirim sekarang</a><a href="#" data-sact="cancel" data-sid="' + esc(x.id) + '" style="color:#b91c1c">Batal</a>' : '')
        : ico('triangle-alert', 12) + ' <b>' + esc(ST[x.status] || x.status) + '</b><span>(jadwal ' + esc(waSchedFmt(x.at)) + ')</span><span>' + esc(x.reason || '') + '</span>';
      return '<div class="wa-sbub' + (live ? '' : ' bad') + '" data-k="s' + esc(x.id) + x.status + x.at + '">' + esc(x.text) + '<div class="ws-meta">' + meta + '</div></div>';
    }).join('');
  }
  function waSchedClose() {
    if (waState.schedEdit && $('#waReplyInput')) { $('#waReplyInput').value = ''; waQrAutosize(); }   // isi edit jangan tertinggal di kotak balas
    waState.schedOpen = null; waState.schedEdit = null;
    if ($('#waSchedPop')) { $('#waSchedPop').style.display = 'none'; $('#waSchedPop').innerHTML = ''; }
    if ($('#waSchedBtn')) $('#waSchedBtn').classList.remove('active');
  }
  function waSchedLocal(d) {   // Date -> nilai input datetime-local
    var p = function (n) { return ('0' + n).slice(-2); };
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + 'T' + p(d.getHours()) + ':' + p(d.getMinutes());
  }
  function waSchedOpen(edit) {
    var pop = $('#waSchedPop'), num = waState.current; if (!pop || !num) return;
    if (waState.attach && waState.attachNum === num) { toast('Lampiran belum bisa dijadwalkan — kirim lampiran langsung, atau hapus lampiran untuk menjadwalkan teks.', true); return; }
    waQrClose();
    waState.schedOpen = num; waState.schedEdit = edit ? edit.id : null;
    if (edit) { $('#waReplyInput').value = edit.text; waQrAutosize(); }
    var d0 = edit ? new Date(edit.at * 1000) : new Date(Date.now() + 3600000);
    if (!edit) { d0.setMinutes(Math.ceil(d0.getMinutes() / 5) * 5, 0, 0); }
    var mn = new Date(Date.now() + 2 * 60000), mx = new Date(Date.now() + 30 * 86400000);
    pop.innerHTML =
      '<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px"><strong>' + ico('alarm-clock', 14) + ' ' + (edit ? 'Ubah jadwal' : 'Jadwalkan pesan') + '</strong><span style="flex:1"></span>' +
        '<button type="button" id="wsX" title="Tutup" style="border:0;background:transparent;cursor:pointer;color:var(--muted);display:inline-flex">' + ico('x', 16) + '</button></div>' +
      '<div class="ws-row"><input type="datetime-local" id="wsAt" value="' + waSchedLocal(d0) + '" min="' + waSchedLocal(mn) + '" max="' + waSchedLocal(mx) + '"></div>' +
      '<div class="ws-row"><button type="button" class="ws-chip" data-q="1h">+1 jam</button><button type="button" class="ws-chip" data-q="3h">+3 jam</button>' +
        '<button type="button" class="ws-chip" data-q="tom">Besok 09:00</button><button type="button" class="ws-chip" data-q="mon">Senin 09:00</button></div>' +
      '<label class="ws-row" style="cursor:pointer;margin-bottom:8px"><input type="checkbox" id="wsCor"' + ((!edit || edit.cancel_on_reply) ? ' checked' : '') + '> Batalkan otomatis bila pelanggan membalas sebelum jam kirim</label>' +
      '<div class="ws-warn" id="wsWarn" style="display:none"></div>' +
      '<div style="display:flex;gap:8px;align-items:center"><span class="help" style="margin:0;flex:1">Isi pesan diambil dari kotak balas.</span>' +
        '<button type="button" class="btn" id="wsGo">' + ico('alarm-clock', 14) + ' ' + (edit ? 'Simpan jadwal' : 'Jadwalkan') + '</button></div>';
    pop.style.display = 'block';
    if ($('#waSchedBtn')) $('#waSchedBtn').classList.add('active');
    var at = function () { var v = $('#wsAt').value; return v ? Math.floor(new Date(v).getTime() / 1000) : 0; };
    var check = function () {
      var t = at(), w = $('#wsWarn'), msg = '', we = waState.schedNum === num ? waState.schedWinEnd : 0;
      if (!t) msg = 'Pilih tanggal & jam kirim.';
      else if (t < Date.now() / 1000 + 120) msg = 'Waktu kirim minimal 2 menit dari sekarang.';
      else if (t > Date.now() / 1000 + 30 * 86400) msg = 'Jadwal paling lama 30 hari ke depan.';
      else if (we && t >= we) msg = 'Jendela 24 jam WhatsApp API resmi berakhir ' + waSchedFmt(we) + ' — pesan teks bebas tidak bisa dikirim setelah itu.';
      w.style.display = msg ? 'block' : 'none'; w.textContent = msg;
      $('#wsGo').disabled = !!msg;
      return !msg;
    };
    $('#wsAt').oninput = check;
    $$('#waSchedPop .ws-chip').forEach(function (b) { b.onclick = function () {
      var d = new Date(), q = b.dataset.q;
      if (q === '1h' || q === '3h') { d = new Date(Date.now() + (q === '1h' ? 1 : 3) * 3600000); d.setSeconds(0, 0); }
      else { d.setHours(9, 0, 0, 0); if (q === 'tom') d.setDate(d.getDate() + 1); else d.setDate(d.getDate() + (((8 - d.getDay()) % 7) || 7)); }
      $('#wsAt').value = waSchedLocal(d); check();
    }; });
    $('#wsX').onclick = waSchedClose;
    $('#wsGo').onclick = function () {
      if (!check()) return;
      var text = $('#waReplyInput').value.trim();
      if (!text) { toast('Tulis isi pesan di kotak balas dulu.', true); $('#waReplyInput').focus(); return; }
      var btn = this; btn.disabled = true;
      var body = { text: text, at: at(), cancel_on_reply: $('#wsCor').checked ? 1 : 0 };
      if (waState.schedEdit) body.id = waState.schedEdit; else body.number = num;
      api(waState.schedEdit ? 'sched_update' : 'sched_create', { method: 'POST', body: body }).then(function (r) {
        btn.disabled = false;
        if (r && r.ok) {
          toast((waState.schedEdit ? 'Jadwal diperbarui: ' : 'Pesan dijadwalkan: ') + waSchedFmt(r.item.at) + '.');
          $('#waReplyInput').value = ''; waQuoteClear(); waQrAutosize(); waSchedClose();
          fetchWaThread(num); fetchWaConvs(true);
        } else toast((r && r.error) || 'Gagal menjadwalkan.', true);
      });
    };
    check();
  }
  function waSchedInit() {
    if (waState.schedBound) return;
    waState.schedBound = true;
    if ($('#waSchedBtn')) $('#waSchedBtn').onclick = function () { if (this.disabled) return; if (waState.schedOpen) waSchedClose(); else waSchedOpen(null); };
    var body = $('#waThreadBody');
    if (body) body.addEventListener('click', function (ev) {
      var a = ev.target.closest ? ev.target.closest('[data-sact]') : null; if (!a) return;
      ev.preventDefault();
      var id = a.getAttribute('data-sid'), act = a.getAttribute('data-sact'), num = waState.current;
      var it = (waState.sched || []).filter(function (x) { return x.id === id; })[0]; if (!it) return;
      var done = function (r, ok) { if (r && r.ok) { toast(ok); fetchWaThread(num); fetchWaConvs(true); } else { toast((r && r.error) || 'Gagal.', true); fetchWaThread(num); } };
      if (act === 'edit') { waSchedOpen(it); $('#waReplyInput').focus(); }
      else if (act === 'cancel') { if (confirm('Batalkan pesan terjadwal ini?')) api('sched_cancel', { method: 'POST', body: { id: id } }).then(function (r) { if (waState.schedEdit === id) { waSchedClose(); $('#waReplyInput').value = ''; } done(r, 'Jadwal dibatalkan.'); }); }
      else if (act === 'now') { if (confirm('Kirim pesan ini sekarang?')) api('sched_send_now', { method: 'POST', body: { id: id } }).then(function (r) { done(r, 'Pesan terkirim.'); }); }
    });
  }
'''
js = rep(js, "  function waQrClose() {\n", FN + "\n  function waQrClose() {\n")
open(J, 'w', encoding='utf-8').write(js)
open(H, 'w', encoding='utf-8').write(ht)
print('OK')
