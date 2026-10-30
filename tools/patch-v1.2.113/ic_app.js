  /* ---- v1.2.113: import-kontak -- impor kontak dari XLS/XLSX/CSV ---------- */
  var XLSX_VER = '0.18.5';
  var contactImp = null;   // { file, header, rows, col:{num,name,status,refund}, map:{status->stage}, refundLost, overwrite, defStage }
  function _loadXlsx() {
    if (window.XLSX) return Promise.resolve(window.XLSX);
    return new Promise(function (res, rej) {
      var sc = document.createElement('script');
      sc.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/' + XLSX_VER + '/xlsx.full.min.js';
      sc.onload = function () { window.XLSX ? res(window.XLSX) : rej(new Error('XLSX')); };
      sc.onerror = function () { rej(new Error('Gagal memuat pembaca Excel. Periksa koneksi internet.')); };
      document.head.appendChild(sc);
    });
  }
  // Sama dengan contactImportNormNum() di server.
  function contactImpNorm(raw) {
    var d = String(raw == null ? '' : raw).replace(/\D/g, '');
    if (!d) return '';
    if (d.indexOf('00') === 0) d = d.slice(2);
    if (d.indexOf('620') === 0) d = '62' + d.slice(3);
    else if (d.charAt(0) === '0') d = '62' + d.slice(1);
    else if (d.charAt(0) === '8' && d.length >= 9 && d.length <= 13) d = '62' + d;
    if (d.length < 10 || d.length > 15) return '';
    if (d.indexOf('62') === 0 && d.charAt(2) !== '8') return '';
    return d;
  }
  var CONTACT_IMP_RANK = { active_customer: 6, hot_prospect: 5, warm: 4, cold: 3, churned: 2, lost: 1, 'new': 0 };
  function contactImpSuggest(v) {
    v = String(v || '').toLowerCase();
    if (/batal|cancel|gagal|fail|expire|kadaluarsa|ditolak|reject|ditutup|closed|refund|void/.test(v)) return 'lost';
    if (/menunggu|pending|booking|proses|process|\bdp\b|uang muka|belum|waiting|unpaid/.test(v)) return 'hot_prospect';
    if (/selesai|siap|lunas|complete|done|deliver|terkirim|diterima|sukses|success|paid|dibayar|aktif|active/.test(v)) return 'active_customer';
    return 'new';
  }
  function _impPickCol(header, good, bad) {
    for (var g = 0; g < good.length; g++) {
      for (var i = 0; i < header.length; i++) {
        var h = String(header[i] || '').toLowerCase().trim();
        if (h && good[g].test(h) && !(bad && bad.test(h))) return i;
      }
    }
    return -1;
  }
  function contactImpStart(file) {
    if (!file) return;
    if (file.size > 15 * 1024 * 1024) { toast('File terlalu besar (maks 15 MB).', true); return; }
    var card = $('#kontakImportCard');
    card.style.display = '';
    card.innerHTML = '<div style="color:var(--muted)">Membaca ' + esc(file.name) + '…</div>';
    _loadXlsx().then(function (X) {
      return file.arrayBuffer().then(function (buf) {
        var wb = X.read(new Uint8Array(buf), { type: 'array', raw: false });
        var ws = wb.Sheets[wb.SheetNames[0]];
        var aoa = X.utils.sheet_to_json(ws, { header: 1, raw: true, defval: '' });
        var hi = 0;   // baris header = baris pertama yang punya >= 2 sel terisi
        for (; hi < Math.min(aoa.length, 20); hi++) {
          if (aoa[hi].filter(function (x) { return String(x).trim() !== ''; }).length >= 2) break;
        }
        var header = (aoa[hi] || []).map(function (h) { return String(h).trim(); });
        var rows = aoa.slice(hi + 1).filter(function (r) { return r.some(function (x) { return String(x).trim() !== ''; }); });
        if (!header.length || !rows.length) throw new Error('File kosong atau tidak punya baris data.');
        var col = {
          num: _impPickCol(header, [/^(nomor|no\.?)\s*(wa|whatsapp|hp|handphone|telepon|telp)/, /whatsapp|\bwa\b|\bhp\b|handphone|ponsel|telepon|telp|phone|mobile/], /pesanan|order|transaksi|kontrak|pembayaran|dealer|\bid\b/),
          name: _impPickCol(header, [/nama (penerima|pelanggan|customer|konsumen|pembeli|lengkap)/, /^nama$|^name$|customer name|full ?name/, /nama|name/], /benefit|voucher|toko|store|promotor|sales|dealer|produk|barang|product|item|file/),
          status: _impPickCol(header, [/status (pesanan|order|transaksi|pelanggan|customer)/, /status/], /refund|pengembalian|pembayaran|payment/),
          refund: _impPickCol(header, [/status refund|refund|pengembalian dana/])
        };
        if (col.num < 0) {   // tebak: kolom dengan nomor valid terbanyak
          var best = -1, bestN = 0;
          header.forEach(function (_, i) {
            var n = 0; rows.slice(0, 200).forEach(function (r) { if (contactImpNorm(r[i])) n++; });
            if (n > bestN) { bestN = n; best = i; }
          });
          col.num = best;
        }
        contactImp = { file: file.name, header: header, rows: rows, col: col, map: {}, refundLost: col.refund > -1, overwrite: false, defStage: 'new' };
        contactImpRender();
      });
    }).catch(function (e) {
      card.innerHTML = '<div style="color:#b91c1c">Gagal membaca file: ' + esc(e && e.message ? e.message : String(e)) + '</div>';
    });
  }
  function contactImpCompute() {
    var s = contactImp, out = {}, invalid = 0, skipped = 0;
    s.rows.forEach(function (r) {
      var num = contactImpNorm(s.col.num > -1 ? r[s.col.num] : '');
      if (!num) { invalid++; return; }
      var st = s.col.status > -1 ? String(r[s.col.status] || '').trim() : '';
      var stage = s.col.status > -1 ? (s.map[st] != null ? s.map[st] : contactImpSuggest(st)) : s.defStage;
      if (stage === 'skip') { skipped++; return; }
      if (s.refundLost && s.col.refund > -1 && String(r[s.col.refund] || '').trim() !== '') stage = 'lost';
      var nm = s.col.name > -1 ? String(r[s.col.name] || '').trim() : '';
      var o = out[num];
      if (!o) { out[num] = { n: num, name: nm, stage: stage, st: st, cnt: 1 }; return; }
      o.cnt++;
      if (!o.name && nm) o.name = nm;
      if ((CONTACT_IMP_RANK[stage] || 0) > (CONTACT_IMP_RANK[o.stage] || 0)) { o.stage = stage; o.st = st; }
    });
    var list = Object.keys(out).map(function (k) { return out[k]; });
    var by = {}; list.forEach(function (o) { by[o.stage] = (by[o.stage] || 0) + 1; });
    return { list: list, invalid: invalid, skipped: skipped, by: by };
  }
  function _impStageOpts(sel, withSkip) {
    var h = withSkip ? '<option value="skip"' + (sel === 'skip' ? ' selected' : '') + '>Lewati (tidak diimpor)</option>' : '';
    return h + ['new', 'cold', 'warm', 'hot_prospect', 'lost', 'active_customer', 'churned'].map(function (k) {
      return '<option value="' + k + '"' + (sel === k ? ' selected' : '') + '>' + CONTACT_STAGE[k].label + '</option>';
    }).join('');
  }
  function contactImpRender() {
    var s = contactImp, card = $('#kontakImportCard');
    function colSel(key, optional) {
      return '<select data-impcol="' + key + '">' + (optional ? '<option value="-1">— tidak dipakai —</option>' : '') +
        s.header.map(function (h, i) { return '<option value="' + i + '"' + (s.col[key] === i ? ' selected' : '') + '>' + esc(h || ('Kolom ' + (i + 1))) + '</option>'; }).join('') + '</select>';
    }
    var stCount = {};
    if (s.col.status > -1) s.rows.forEach(function (r) { var v = String(r[s.col.status] || '').trim(); stCount[v] = (stCount[v] || 0) + 1; });
    var stKeys = Object.keys(stCount).sort(function (a, b) { return stCount[b] - stCount[a]; });
    var mapHtml = s.col.status > -1
      ? '<div style="overflow-x:auto"><table class="tbl" style="margin-top:6px"><thead><tr><th>Nilai status di file</th><th style="text-align:right">Baris</th><th>Jadi Lead Rating</th></tr></thead><tbody>' +
        stKeys.map(function (v) {
          var cur = s.map[v] != null ? s.map[v] : contactImpSuggest(v);
          return '<tr><td>' + (v ? esc(v) : '<em style="color:var(--muted)">(kosong)</em>') + '</td><td style="text-align:right">' + stCount[v] +
            '</td><td><select data-impmap="' + esc(v) + '">' + _impStageOpts(cur, true) + '</select></td></tr>';
        }).join('') + '</tbody></table></div>'
      : '<div class="row" style="margin-top:6px"><label class="fl">Lead Rating semua kontak</label><select id="impDefStage">' + _impStageOpts(s.defStage, false) + '</select></div>';
    var c = contactImpCompute();
    var sum = Object.keys(c.by).sort(function (a, b) { return (CONTACT_IMP_RANK[b] || 0) - (CONTACT_IMP_RANK[a] || 0); })
      .map(function (k) { return contactStageBadgeHtml(k, false, '') + ' <strong>' + c.by[k] + '</strong>'; }).join(' &nbsp; ');
    var contoh = c.list.slice(0, 5).map(function (o) {
      return '<tr><td class="mono">+' + esc(o.n) + '</td><td>' + esc(o.name) + '</td><td>' + esc(o.st) + (o.cnt > 1 ? ' <span style="color:var(--muted)">(' + o.cnt + ' baris)</span>' : '') + '</td><td>' + contactStageBadgeHtml(o.stage, false, '') + '</td></tr>';
    }).join('');
    card.innerHTML =
      '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">' +
        '<h3 style="margin:0">Impor Kontak — ' + esc(s.file) + '</h3>' +
        '<button class="btn ghost sm" id="impClose">Tutup</button></div>' +
      '<p style="color:var(--muted);font-size:13px;margin:6px 0 10px;line-height:1.5">' + s.rows.length + ' baris dibaca. Nomor otomatis dirapikan ke format WhatsApp (mis. <span class="mono">+62 0812…</span> → <span class="mono">62812…</span>), jadi saat nomor itu chat nanti, kontaknya langsung menyatu. Nomor yang muncul di beberapa baris digabung dan memakai Lead Rating tertinggi.</p>' +
      '<div class="grid2">' +
        '<div class="row"><label class="fl">Kolom nomor WA</label>' + colSel('num', false) + '</div>' +
        '<div class="row"><label class="fl">Kolom nama</label>' + colSel('name', true) + '</div>' +
        '<div class="row"><label class="fl">Kolom status</label>' + colSel('status', true) + '</div>' +
        '<div class="row"><label class="fl">Kolom refund/batal</label>' + colSel('refund', true) + '</div>' +
      '</div>' +
      (s.col.refund > -1 ? '<label style="display:flex;gap:6px;align-items:flex-start;font-size:13px;margin-top:8px"><input type="checkbox" id="impRefund"' + (s.refundLost ? ' checked' : '') + ' style="margin-top:3px"> <span>Baris yang kolom <strong>' + esc(s.header[s.col.refund]) + '</strong>-nya terisi dijadikan Unqualified</span></label>' : '') +
      mapHtml +
      '<div style="margin-top:12px;padding:10px;border-radius:8px;background:var(--bg)">' +
        '<div style="margin-bottom:6px"><strong>' + c.list.length + '</strong> nomor unik akan diimpor' +
          (c.invalid ? ' · <span style="color:#b45309">' + c.invalid + ' baris nomor tidak valid dilewati</span>' : '') +
          (c.skipped ? ' · ' + c.skipped + ' baris dilewati sesuai pemetaan' : '') + '</div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center">' + (sum || '—') + '</div>' +
        (contoh ? '<div style="overflow-x:auto"><table class="tbl" style="margin-top:8px;font-size:12px"><thead><tr><th>Nomor</th><th>Nama</th><th>Status asli</th><th>Lead Rating</th></tr></thead><tbody>' + contoh + '</tbody></table></div>' : '') +
      '</div>' +
      '<label style="display:flex;gap:6px;align-items:flex-start;font-size:13px;margin-top:10px"><input type="checkbox" id="impOverwrite"' + (s.overwrite ? ' checked' : '') + ' style="margin-top:3px"> <span>Timpa Lead Rating kontak yang sudah diatur. Bila tidak dicentang, kontak yang sudah ada hanya diubah kalau masih Unrated. Nama yang sudah ada tidak pernah ditimpa.</span></label>' +
      '<div style="display:flex;gap:8px;align-items:center;margin-top:12px;flex-wrap:wrap">' +
        '<button class="btn" id="impGo"' + (c.list.length ? '' : ' disabled') + '>Impor ' + c.list.length + ' kontak</button>' +
        '<span id="impProg" style="color:var(--muted);font-size:13px"></span></div>';

    $('#impClose').onclick = function () { contactImp = null; card.style.display = 'none'; card.innerHTML = ''; };
    $$('#kontakImportCard [data-impcol]').forEach(function (el) {
      el.onchange = function () { s.col[el.dataset.impcol] = parseInt(el.value, 10); if (el.dataset.impcol === 'refund') s.refundLost = s.col.refund > -1; contactImpRender(); };
    });
    $$('#kontakImportCard [data-impmap]').forEach(function (el) {
      el.onchange = function () { s.map[el.dataset.impmap] = el.value; contactImpRender(); };
    });
    var r = $('#impRefund'); if (r) r.onchange = function () { s.refundLost = r.checked; contactImpRender(); };
    var d = $('#impDefStage'); if (d) d.onchange = function () { s.defStage = d.value; contactImpRender(); };
    $('#impOverwrite').onchange = function () { s.overwrite = this.checked; };
    $('#impGo').onclick = function () { contactImpSend(c.list); };
  }
  function contactImpSend(list) {
    var s = contactImp, btn = $('#impGo'), prog = $('#impProg');
    if (!list.length) return;
    if (!confirm('Impor ' + list.length + ' kontak ke menu Kontak?')) return;
    btn.disabled = true;
    var CH = 500, i = 0, tot = { created: 0, updated: 0, kept: 0, invalid: 0 };
    function next() {
      if (i >= list.length) {
        prog.innerHTML = '<span style="color:#065f46">Selesai: ' + tot.created + ' kontak baru, ' + tot.updated + ' diperbarui' +
          (tot.kept ? ', ' + tot.kept + ' Lead Rating lama dipertahankan' : '') + (tot.invalid ? ', ' + tot.invalid + ' tidak valid' : '') + '.</span>';
        toast(list.length + ' kontak diimpor.');
        fetchContacts();
        return;
      }
      var part = list.slice(i, i + CH);
      prog.textContent = 'Mengimpor ' + Math.min(i + CH, list.length) + ' / ' + list.length + '…';
      api('import_contacts', { method: 'POST', body: { rows: part, overwrite: s.overwrite, file: s.file } }).then(function (res) {
        if (!res || !res.ok) throw new Error((res && res.error) || 'Gagal mengimpor.');
        tot.created += res.created || 0; tot.updated += res.updated || 0; tot.kept += res.kept || 0; tot.invalid += res.invalid || 0;
        i += CH; next();
      }).catch(function (e) {
        btn.disabled = false;
        prog.innerHTML = '<span style="color:#b91c1c">' + esc(e.message || String(e)) + ' (' + i + ' kontak pertama sudah tersimpan; impor ulang aman)</span>';
      });
    }
    next();
  }
