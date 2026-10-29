  /* ====================================================================== *
   *  v1.2.109: guest-comment / v1.2.110: customer-feedback — survei kepuasan pelanggan (WA + form web), mulai paket Business
   * ====================================================================== */
  ICONS['qr-code'] = '<rect width="5" height="5" x="3" y="3" rx="1"/><rect width="5" height="5" x="16" y="3" rx="1"/><rect width="5" height="5" x="3" y="16" rx="1"/><path d="M21 16h-3a2 2 0 0 0-2 2v3"/><path d="M21 21v.01"/><path d="M12 7v3a2 2 0 0 1-2 2H7"/><path d="M3 12h.01"/><path d="M12 3h.01"/><path d="M12 16v.01"/><path d="M16 12h1"/><path d="M21 12v.01"/><path d="M12 21v-1"/>';
  ICONS['external-link'] = '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>';
  /* qrcode-generator 1.4.4 — (c) 2009 Kazuhiko Arase, MIT license — http://www.d-project.com/ */
  var gcQr = (function () {
    var define, exports, module;   // jangan sentuh global
    /*@@QRLIB@@*/
    qrcode.stringToBytes = qrcode.stringToBytesFuncs['UTF-8'];
    return qrcode;
  })();
  var GC = { d: null, list: null, off: 0, view: 'list' };
  var GC_ST = { baru: ['Baru', '#b45309', '#fef3c7'], ditindak: ['Ditindaklanjuti', '#1d4ed8', '#dbeafe'], selesai: ['Selesai', '#15803d', '#dcfce7'] };
  function gcStars(v) {
    v = +v || 0; var h = '';
    for (var i = 1; i <= 5; i++) h += '<span class="gc-st' + (i <= Math.round(v) ? ' on' : '') + '">★</span>';
    return h;
  }
  function gcQrImg(text, size) {
    try { var q = gcQr(0, 'M'); q.addData(text); q.make(); var n = q.getModuleCount(); var cell = Math.max(2, Math.floor((size || 220) / (n + 8)));
      return q.createDataURL(cell, cell * 4); } catch (e) { return ''; }
  }
  function gcCopy(t) {
    var done = function () { toast('Disalin.'); };
    if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(t).then(done, function () { gcCopyOld(t); }); return; }
    gcCopyOld(t);
  }
  function gcCopyOld(t) { var ta = document.createElement('textarea'); ta.value = t; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); toast('Disalin.'); } catch (e) { toast('Salin manual.', true); } ta.remove(); }
  function loadGc() {
    $$('#gcTabs [data-gcv]').forEach(function (b) { b.onclick = function () { gcView(b.dataset.gcv); }; });
    $('#gcApply').onclick = function () { GC.off = 0; gcLoadList(); };
    $('#gcExport').onclick = gcExport;
    $('#gcQ').onkeydown = function (e) { if (e.key === 'Enter') { GC.off = 0; gcLoadList(); } };
    if (!$('#gcFrom').value) { var d = new Date(Date.now() - 29 * 86400000 + 7 * 3600000); $('#gcFrom').value = d.toISOString().slice(0, 10); }
    api('gc_admin', { query: '&op=get' }).then(function (r) {
      if (!r || !r.ok) { toast((r && r.error) || 'Gagal memuat Customer Feedback.', true); return; }
      GC.d = r;
      var lk = $('#gcLock');
      lk.classList.toggle('hide', !r.locked);
      if (r.locked) lk.innerHTML = '<div class="gc-lock-ic">' + ico('crown', 22) + '</div><div><b>Fitur paket Business</b><p>' + esc(r.locked_msg) +
        (r.plan && r.plan.tier ? ' Paket Anda saat ini: <b>' + esc(r.plan.tier.charAt(0).toUpperCase() + r.plan.tier.slice(1)) + '</b>.' : '') +
        (r.count ? ' Data feedback yang sudah masuk tetap bisa dilihat & diekspor.' : '') + '</p></div>';
      gcStatus();
      gcFillSettings();
      gcRenderLinks();
      gcView(r.locked && !r.count ? 'set' : GC.view);
      gcLoadList();
    });
  }
  function gcStatus() {
    var r = GC.d, el = $('#gcStatus');
    if (!r) return;
    var on = !r.locked && r.conf.enabled;
    el.className = 'pill ' + (on ? 'on' : 'off');
    el.innerHTML = on ? ico('check-circle-2', 13) + ' Aktif' : (r.locked ? ico('ban', 13) + ' Terkunci (paket)' : ico('clock-3', 13) + ' Belum aktif');
  }
  function gcView(v) {
    if (v === 'set' && !can('super_admin,admin')) v = 'list';
    GC.view = v;
    $$('#gcTabs [data-gcv]').forEach(function (b) { b.classList.toggle('active', b.dataset.gcv === v); });
    ['list', 'set', 'link'].forEach(function (k) { $('#gcView-' + k).classList.toggle('hide', k !== v); });
  }
  function gcQuery() {
    return { op: 'list', from: $('#gcFrom').value, to: $('#gcTo').value, channel: $('#gcChan').value, rating: $('#gcRate').value,
             status: $('#gcStat').value, q: $('#gcQ').value.trim() };
  }
  function gcLoadList(more) {
    var body = gcQuery(); body.offset = more ? GC.off : 0; body.limit = 50;
    if (!more) $('#gcList').innerHTML = '<div class="card gc-empty">Memuat…</div>';
    api('gc_admin', { method: 'POST', body: body }).then(function (r) {
      if (!r || !r.ok) { $('#gcList').innerHTML = '<div class="card gc-empty">' + esc((r && r.error) || 'Gagal memuat.') + '</div>'; return; }
      if (!more) { GC.list = r; gcRenderStats(r); } else { GC.list.items = GC.list.items.concat(r.items); }
      GC.off = GC.list.items.length;
      gcRenderList();
    });
  }
  function gcRenderStats(r) {
    var s = r.stats;
    var lowPct = s.n ? Math.round(s.low / s.n * 100) : 0;
    $('#gcKpis').innerHTML =
      '<div class="gc-kpi"><small>Feedback masuk</small><b>' + s.n + '</b><span>WA ' + s.by_channel.whatsapp + ' · Web ' + s.by_channel.web + '</span></div>' +
      '<div class="gc-kpi"><small>Rata-rata</small><b>' + (s.n ? s.avg.toFixed(2) : '–') + '<i>/5</i></b><span class="gc-stars">' + gcStars(s.avg) + '</span></div>' +
      '<div class="gc-kpi' + (s.low ? ' warn' : '') + '"><small>Ada rating rendah (≤' + r.low_th + ')</small><b>' + s.low + '</b><span>' + lowPct + '% dari total</span></div>' +
      '<div class="gc-kpi"><small>Sebaran rata-rata</small><div class="gc-dist">' + [5, 4, 3, 2, 1].map(function (k) {
        var n = s.dist[k] || 0, w = s.n ? Math.round(n / s.n * 100) : 0;
        return '<div><em>' + k + '★</em><span><i style="width:' + w + '%"></i></span><em>' + n + '</em></div>'; }).join('') + '</div></div>';
    $('#gcAsp').innerHTML = s.aspects.length ? s.aspects.map(function (a) {
      var w = Math.round((a.avg || 0) / 5 * 100);
      var cls = !a.n ? '' : (a.avg <= r.low_th + 0.5 ? ' bad' : (a.avg < 4 ? ' mid' : ''));
      return '<div class="gc-asp' + cls + '"><div class="gc-asp-l">' + esc(a.label) + (a.old ? ' <span class="tag none">dihapus</span>' : '') + '</div>' +
        '<div class="gc-bar"><i style="width:' + w + '%"></i></div><div class="gc-asp-v">' + (a.n ? a.avg.toFixed(2) : '–') + '<small> · ' + a.n + '</small></div></div>';
    }).join('') : '<div class="help">Belum ada data.</div>';
  }
  function gcRenderList() {
    var r = GC.list, el = $('#gcList');
    if (!r.items.length) {
      el.innerHTML = '<div class="card gc-empty">' + ico('star', 22) + '<p>Belum ada feedback pada filter ini.</p>' +
        (GC.d && !GC.d.locked && !GC.d.conf.enabled && can('super_admin,admin') ? '<button class="btn sm" type="button" id="gcGoSet">Aktifkan di Pengaturan</button>' : '') + '</div>';
      var g = $('#gcGoSet'); if (g) g.onclick = function () { gcView('set'); };
      $('#gcMore').innerHTML = '';
      return;
    }
    el.innerHTML = r.items.map(gcItemHtml).join('');
    $('#gcMore').innerHTML = r.items.length < r.total ? '<button class="btn ghost sm" type="button" id="gcMoreBtn">Muat lagi (' + (r.total - r.items.length) + ')</button>' : '';
    var mb = $('#gcMoreBtn'); if (mb) mb.onclick = function () { gcLoadList(true); };
    $$('#gcList [data-gcact]').forEach(function (b) { b.onclick = function () { gcAct(b.dataset.gcact, b.dataset.id); }; });
  }
  function gcItemHtml(e) {
    var st = GC_ST[e.status] || GC_ST.baru;
    var asp = Object.keys(e.ratings || {}).map(function (k) {
      var v = e.ratings[k], low = v <= (GC.list ? GC.list.low_th : 2);
      return '<span class="gc-rt' + (low ? ' low' : '') + '">' + esc((e.labels && e.labels[k]) || k) + ' <b>' + v + '</b></span>';
    }).join('');
    var who = esc(e.name || 'Pelanggan') + (e.room ? ' · <span class="gc-room">' + esc(gcRef()) + ' ' + esc(e.room) + '</span>' : '');
    var ct = e.channel === 'whatsapp' ? (ico('message-circle', 13) + ' WhatsApp' + (e.num ? ' · +' + esc(e.num) : '')) : (ico('globe', 13) + ' Form web' + (e.phone ? ' · ' + esc(e.phone) : ''));
    var canDel = can('super_admin,admin');
    return '<div class="card gc-item' + (e.low ? ' low' : '') + '" id="gci-' + esc(e.id) + '">' +
      '<div class="gc-top"><div><div class="gc-who">' + who + '</div><div class="gc-meta">' + ct + ' · ' + esc(e.ts) + (e.lang === 'en' ? ' · EN' : '') + '</div></div>' +
      '<div class="gc-avg"><span class="gc-stars">' + gcStars(e.avg) + '</span><b>' + (+e.avg).toFixed(1) + '</b></div></div>' +
      '<div class="gc-rts">' + asp + '</div>' +
      (e.comment ? '<div class="gc-cm">' + esc(e.comment).replace(/\n/g, '<br>') + '</div>' : '<div class="gc-cm none">(tanpa komentar)</div>') +
      '<div class="gc-foot"><span class="gc-badge" style="color:' + st[1] + ';background:' + st[2] + '">' + st[0] + '</span>' +
      (e.handled_by ? '<span class="gc-meta">oleh ' + esc(e.handled_by) + ' · ' + esc(e.handled_at || '') + '</span>' : '') +
      '<span class="gc-acts">' +
      (e.channel === 'whatsapp' && e.num ? '<button class="btn ghost sm" type="button" data-gcact="wa" data-id="' + esc(e.id) + '">' + ico('message-circle', 13) + ' Buka chat</button>' : '') +
      '<button class="btn ghost sm" type="button" data-gcact="edit" data-id="' + esc(e.id) + '">Tindak lanjut</button>' +
      (canDel ? '<button class="btn danger sm" type="button" data-gcact="del" data-id="' + esc(e.id) + '" title="Hapus">' + ico('trash-2', 13) + '</button>' : '') +
      '</span></div>' +
      (e.note ? '<div class="gc-note"><small>Catatan</small>' + esc(e.note).replace(/\n/g, '<br>') + '</div>' : '') +
      '<div class="gc-edit hide" id="gce-' + esc(e.id) + '"></div></div>';
  }
  function gcFind(id) { var it = null; (GC.list ? GC.list.items : []).forEach(function (x) { if (x.id === id) it = x; }); return it; }
  function gcAct(act, id) {
    var e = gcFind(id); if (!e) return;
    if (act === 'wa') {
      openLeadConv(e.num);
      return;
    }
    if (act === 'del') {
      if (!confirm('Hapus feedback dari ' + (e.name || 'pelanggan') + '? Tidak bisa dibatalkan.')) return;
      api('gc_admin', { method: 'POST', body: { op: 'delete', id: id } }).then(function (r) {
        if (!r || !r.ok) { toast((r && r.error) || 'Gagal menghapus.', true); return; }
        toast('Dihapus.'); gcLoadList();
      });
      return;
    }
    var box = $('#gce-' + id);
    if (!box.classList.contains('hide')) { box.classList.add('hide'); return; }
    box.innerHTML = '<div class="row"><label class="fl">Status</label><select id="gcs-' + esc(id) + '">' + Object.keys(GC_ST).map(function (k) {
        return '<option value="' + k + '"' + (e.status === k ? ' selected' : '') + '>' + GC_ST[k][0] + '</option>'; }).join('') + '</select></div>' +
      '<div class="row"><label class="fl">Catatan tindak lanjut (internal)</label><textarea id="gcn-' + esc(id) + '" rows="2" maxlength="1000" placeholder="mis. sudah dicek ke tim terkait, pelanggan sudah dihubungi">' + esc(e.note || '') + '</textarea></div>' +
      '<button class="btn sm" type="button" id="gcsv-' + esc(id) + '">Simpan</button>';
    box.classList.remove('hide');
    $('#gcsv-' + id).onclick = function () {
      api('gc_admin', { method: 'POST', body: { op: 'update', id: id, status: $('#gcs-' + id).value, note: $('#gcn-' + id).value } }).then(function (r) {
        if (!r || !r.ok) { toast((r && r.error) || 'Gagal menyimpan.', true); return; }
        for (var k in r.item) e[k] = r.item[k];
        var card = $('#gci-' + id); card.outerHTML = gcItemHtml(e);
        $$('#gci-' + id + ' [data-gcact]').forEach(function (b) { b.onclick = function () { gcAct(b.dataset.gcact, b.dataset.id); }; });
        toast('Tersimpan.');
      });
    };
  }
  function gcExport() {
    var body = gcQuery(); body.all = 1;
    api('gc_admin', { method: 'POST', body: body }).then(function (r) {
      if (!r || !r.ok) { toast((r && r.error) || 'Gagal ekspor.', true); return; }
      if (!r.items.length) { toast('Tidak ada data untuk diekspor.', true); return; }
      var asp = r.stats.aspects;
      var head = ['Tanggal', 'Kanal', 'Nama', gcRef(), 'No. WA / HP', 'Bahasa'].concat(asp.map(function (a) { return a.label; })).concat(['Rata-rata', 'Rating rendah', 'Komentar', 'Status', 'Catatan', 'Ditangani oleh']);
      var q = function (v) { v = String(v == null ? '' : v); if (/^[=+\-@]/.test(v)) v = "'" + v; return '"' + v.replace(/"/g, '""') + '"'; };
      var lines = [head.map(q).join(',')];
      r.items.forEach(function (e) {
        lines.push([e.ts, e.channel === 'whatsapp' ? 'WhatsApp' : 'Web', e.name, e.room, e.num ? '+' + e.num : e.phone, (e.lang || 'id').toUpperCase()]
          .concat(asp.map(function (a) { return (e.ratings || {})[a.id] || ''; }))
          .concat([e.avg, e.low ? 'ya' : '', e.comment, (GC_ST[e.status] || GC_ST.baru)[0], e.note, e.handled_by || '']).map(q).join(','));
      });
      var blob = new Blob(['﻿' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' });
      var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'customer-feedback-' + new Date().toISOString().slice(0, 10) + '.csv';
      document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
    });
  }
  function gcRef() { return (GC.d && GC.d.conf && GC.d.conf.ref_label) || 'Nomor pesanan'; }
  /* v1.2.110: preset aspek per industri */
  var GC_PRESETS = {
    umum:   { ref: ['Nomor pesanan', 'Order number'], room: false, a: [['Kesan keseluruhan', 'Overall experience'], ['Kualitas produk / layanan', 'Product / service quality'], ['Keramahan & bantuan staf', 'Staff friendliness & help'], ['Kecepatan pelayanan', 'Speed of service'], ['Harga sesuai kualitas', 'Value for money']] },
    hotel:  { ref: ['Nomor kamar', 'Room number'], room: true, a: [['Kesan keseluruhan', 'Overall experience'], ['Kamar', 'Room'], ['Kebersihan', 'Cleanliness'], ['Pelayanan staf', 'Staff service'], ['Makanan & minuman', 'Food & beverage']] },
    resto:  { ref: ['Nomor meja', 'Table number'], room: true, a: [['Kesan keseluruhan', 'Overall experience'], ['Rasa makanan & minuman', 'Food & drink taste'], ['Kecepatan penyajian', 'Serving speed'], ['Pelayanan', 'Service'], ['Kebersihan', 'Cleanliness'], ['Harga sesuai porsi', 'Value for money']] },
    bus:    { ref: ['Kode booking', 'Booking code'], room: true, a: [['Kesan keseluruhan', 'Overall experience'], ['Ketepatan waktu', 'Punctuality'], ['Kenyamanan armada', 'Bus comfort'], ['Kebersihan armada', 'Bus cleanliness'], ['Pengemudi & kru', 'Driver & crew'], ['Proses pemesanan', 'Booking process']] },
    klinik: { ref: ['Nomor antrean', 'Queue number'], room: false, a: [['Kesan keseluruhan', 'Overall experience'], ['Waktu tunggu', 'Waiting time'], ['Keramahan staf', 'Staff friendliness'], ['Penjelasan dokter / tenaga medis', 'Explanation by doctor / medical staff'], ['Kebersihan fasilitas', 'Facility cleanliness']] },
    toko:   { ref: ['Nomor pesanan', 'Order number'], room: false, a: [['Kesan keseluruhan', 'Overall experience'], ['Kualitas produk', 'Product quality'], ['Kecepatan pengiriman', 'Delivery speed'], ['Respons admin', 'Admin responsiveness'], ['Harga sesuai kualitas', 'Value for money']] },
    jasa:   { ref: ['Nomor proyek / invoice', 'Project / invoice number'], room: false, a: [['Kesan keseluruhan', 'Overall experience'], ['Kualitas hasil kerja', 'Quality of work'], ['Ketepatan waktu', 'Timeliness'], ['Komunikasi', 'Communication'], ['Harga sesuai hasil', 'Value for money']] }
  };
  function gcApplyPreset(k) {
    var p = GC_PRESETS[k]; if (!p) return;
    if (!confirm('Ganti daftar aspek & label nomor referensi dengan preset ini? Klik Simpan setelahnya.')) return;
    $('#gc_aspects').innerHTML = p.a.map(function (x) { return gcAspRow({ label: x[0], label_en: x[1] }); }).join('');
    gcWireAsp();
    $('#gc_ref_label').value = p.ref[0]; $('#gc_ref_label_en').value = p.ref[1]; $('#gc_ask_room').checked = p.room;
    toast('Preset diterapkan — klik Simpan Pengaturan.');
  }
  /* --- pengaturan --- */
  function gcAspRow(a) {
    return '<div class="gc-asprow"><input type="hidden" value="' + esc(a.id || '') + '"><input type="text" maxlength="60" placeholder="Label (Indonesia)" value="' + esc(a.label || '') + '">' +
      '<input type="text" maxlength="60" placeholder="Label (English)" value="' + esc(a.label_en || '') + '"><button class="btn danger sm" type="button" title="Hapus aspek">' + ico('x', 13) + '</button></div>';
  }
  function gcWireAsp() {
    $$('#gc_aspects .gc-asprow button').forEach(function (b) { b.onclick = function () {
      if ($$('#gc_aspects .gc-asprow').length <= 1) { toast('Minimal satu aspek.', true); return; }
      b.parentNode.remove(); }; });
    $('#gc_asp_add').disabled = $$('#gc_aspects .gc-asprow').length >= 8;
  }
  function gcFillSettings() {
    var c = GC.d.conf, ed = GC.d.can_edit, lockd = GC.d.locked;
    $('#gc_enabled').checked = !!c.enabled && !lockd;
    $('#gc_enabled').disabled = lockd || !ed;
    $('#gc_aspects').innerHTML = c.aspects.map(gcAspRow).join('');
    gcWireAsp();
    $('#gc_asp_add').onclick = function () { $('#gc_aspects').insertAdjacentHTML('beforeend', gcAspRow({})); gcWireAsp(); };
    ['ask_name', 'ask_room', 'ask_phone_web', 'ai_hint'].forEach(function (k) { $('#gc_' + k).checked = !!c[k]; });
    ['intro', 'intro_en', 'thanks', 'thanks_en', 'review_url', 'review_text', 'review_text_en', 'alert_wa', 'ref_label', 'ref_label_en'].forEach(function (k) { $('#gc_' + k).value = c[k] || ''; });
    $('#gc_preset').onchange = function () { gcApplyPreset(this.value); this.value = ''; };   // v1.2.110
    $('#gc_low').value = String(c.low);
    $('#gc_keywords').value = (c.keywords || []).join(', ');
    $('#gc_save').disabled = !ed;
    $('#gc_save').onclick = gcSave;
  }
  function gcSave() {
    var asp = $$('#gc_aspects .gc-asprow').map(function (r) { var i = r.querySelectorAll('input'); return { id: i[0].value, label: i[1].value.trim(), label_en: i[2].value.trim() }; })
      .filter(function (a) { return a.label || a.label_en; });
    if (!asp.length) { toast('Isi minimal satu aspek penilaian.', true); return; }
    var ru = $('#gc_review_url').value.trim();
    if (ru && !/^https?:\/\//i.test(ru)) { toast('Tautan ulasan harus diawali https://', true); return; }
    var conf = { enabled: $('#gc_enabled').checked, aspects: asp, low: +$('#gc_low').value, keywords: $('#gc_keywords').value };
    ['ask_name', 'ask_room', 'ask_phone_web', 'ai_hint'].forEach(function (k) { conf[k] = $('#gc_' + k).checked; });
    ['intro', 'intro_en', 'thanks', 'thanks_en', 'review_url', 'review_text', 'review_text_en', 'alert_wa', 'ref_label', 'ref_label_en'].forEach(function (k) { conf[k] = $('#gc_' + k).value; });
    var b = $('#gc_save'); b.disabled = true;
    api('gc_admin', { method: 'POST', body: { op: 'save', conf: conf } }).then(function (r) {
      b.disabled = false;
      if (!r || !r.ok) { toast((r && r.error) || 'Gagal menyimpan.', true); return; }
      GC.d.conf = r.conf; gcFillSettings(); gcStatus(); gcRenderLinks();
      toast(r.conf.enabled ? 'Tersimpan. Customer Feedback aktif.' : 'Tersimpan.');
    });
  }
  /* --- tautan & QR --- */
  function gcRenderLinks() {
    var r = GC.d, room = ($('#gcRoom') ? $('#gcRoom').value : '').replace(/[^A-Za-z0-9-]/g, '').slice(0, 10);
    var kw = ((r.conf.keywords || [])[0] || 'customer feedback').toUpperCase();
    var fu = r.form_url ? r.form_url + (room ? '&room=' + encodeURIComponent(room) : '') : '';
    var items = [];
    if (fu) items.push({ t: 'Form web', s: 'Untuk QR di meja, kasir, kamar, atau tiket — juga bisa ditaruh di email, struk, dan pesan setelah transaksi.', u: fu, k: 'web' });
    (r.wa || []).forEach(function (w) {
      items.push({ t: 'WhatsApp · ' + w.label, s: 'Membuka WA dengan pesan "' + kw + (room ? ' #' + room : '') + '" — bot langsung memandu survei.',
                   u: 'https://wa.me/' + w.number + '?text=' + encodeURIComponent(kw + (room ? ' #' + room : '')), k: 'wa' });
    });
    var off = r.locked ? '<div class="help" style="color:var(--warn)">' + esc(r.locked_msg) + '</div>' : (!r.conf.enabled ? '<div class="help" style="color:var(--warn)">Customer Feedback belum diaktifkan — tautan baru berfungsi setelah diaktifkan di Pengaturan.</div>' : '');
    $('#gcLinks').innerHTML = off + (items.length ? items.map(function (x, i) {
      var img = gcQrImg(x.u, 220);
      return '<div class="gc-link"><div class="gc-qr">' + (img ? '<img src="' + img + '" alt="QR">' : '') + '</div><div class="gc-link-b"><b>' + esc(x.t) + '</b><p>' + esc(x.s) + '</p>' +
        '<code>' + esc(x.u) + '</code><div class="gc-link-a"><button class="btn ghost sm" type="button" data-gccp="' + i + '">' + ico('copy', 13) + ' Salin</button>' +
        '<a class="btn ghost sm" href="' + esc(x.u) + '" target="_blank" rel="noopener">' + ico('external-link', 13) + ' Buka</a>' +
        (img ? '<a class="btn ghost sm" download="qr-feedback-' + x.k + (room ? '-' + room : '') + '.gif" href="' + img + '">' + ico('download', 13) + ' Unduh QR</a>' : '') + '</div></div></div>';
    }).join('') : '<div class="help">Belum ada nomor WhatsApp & URL form belum terbaca. Buka dashboard dari domain tenant Anda.</div>');
    $$('#gcLinks [data-gccp]').forEach(function (b) { b.onclick = function () { gcCopy(items[+b.dataset.gccp].u); }; });
    var rm = $('#gcRoom'); if (rm && !rm.dataset.w) { rm.dataset.w = '1'; rm.oninput = function () { gcRenderLinks(); }; }
  }
