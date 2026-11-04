  /* ====================================================================== *
   *  v1.2.138: filter-topik — filter & label topik/divisi Percakapan WA (klasifikasi AI) + menu Topik & Divisi
   * ====================================================================== */
  var TF_COLORS = [['#dbeafe', '#1e40af'], ['#dcfce7', '#166534'], ['#fef3c7', '#92400e'], ['#fce7f3', '#9d174d'], ['#ede9fe', '#5b21b6'],
                   ['#cffafe', '#155e75'], ['#ffedd5', '#9a3412'], ['#e0e7ff', '#3730a3'], ['#f1f5f9', '#334155'], ['#fee2e2', '#991b1b'],
                   ['#ecfccb', '#3f6212'], ['#f5f5f4', '#44403c']];
  var TF = { conf: null, presets: [], d: null, dirty: false };
  function tfOn() { return !!(waState.tp && waState.tp.on); }
  function tfTopic(id) { var l = (waState.tp && waState.tp.topics) || []; for (var i = 0; i < l.length; i++) if (l[i].id === id) return l[i]; return null; }
  function tfDiv(id) { var l = (waState.tp && waState.tp.divisions) || []; for (var i = 0; i < l.length; i++) if (l[i].id === id) return l[i]; return null; }
  function tfDivColor(id) {
    var l = (waState.tp && waState.tp.divisions) || [];
    for (var i = 0; i < l.length; i++) if (l[i].id === id) return TF_COLORS[i % TF_COLORS.length];
    return TF_COLORS[8];
  }
  function tfChip(id, extra) {
    var t = tfTopic(id); if (!t) return '';
    var c = tfDivColor(t.div);
    return '<span class="tag tf-chip" style="background:' + c[0] + ';color:' + c[1] + (extra || '') + '" title="' + esc((tfDiv(t.div) || {}).name || 'Tanpa divisi') + '">' + esc(t.name) + '</span>';
  }
  function tfQuery() {
    var q = '';
    if (waState.tfF) q += '&tpt=' + encodeURIComponent(waState.tfF);
    if (waState.tfDF) q += '&tpd=' + encodeURIComponent(waState.tfDF);
    if (waState.tfF && waState.tfEver) q += '&tpe=1';
    return q;
  }
  function tfFromList(res) {
    waState.tp = res.tp || null;
    if (!tfOn()) { waState.tfF = ''; waState.tfDF = ''; return; }
    if (res.tp.f !== undefined) waState.tfF = res.tp.f || '';
    if (res.tp.fd !== undefined) waState.tfDF = res.tp.fd || '';
  }
  function tfFilterBarHtml() {
    if (!tfOn()) return '';
    var tp = waState.tp, cn = tp.counts || {}, dc = tp.dcounts || {};
    var n = function (v) { return v != null ? ' (' + Number(v).toLocaleString('id-ID') + ')' : ''; };
    var dOpts = '<option value="">Semua divisi' + n(dc.all) + '</option>' + (tp.divisions || []).map(function (d) {
      return '<option value="' + esc(d.id) + '"' + (waState.tfDF === d.id ? ' selected' : '') + '>' + esc(d.name) + n(dc[d.id] || 0) + '</option>';
    }).join('') + '<option value="__none"' + (waState.tfDF === '__none' ? ' selected' : '') + '>Belum berlabel' + n(dc.__none || 0) + '</option>';
    var tl = (tp.topics || []).filter(function (t) { return !waState.tfDF || waState.tfDF === '__none' || t.div === waState.tfDF; });
    var tOpts = '<option value="">Semua topik' + n(cn.all) + '</option>' + tl.map(function (t) {
      return '<option value="' + esc(t.id) + '"' + (waState.tfF === t.id ? ' selected' : '') + '>' + esc(t.name) + n(cn[t.id] || 0) + '</option>';
    }).join('') + '<option value="__none"' + (waState.tfF === '__none' ? ' selected' : '') + '>Belum berlabel' + n(cn.__none || 0) + '</option>';
    return '<label class="wa-dd' + (waState.tfDF ? ' is-on' : '') + '" title="Saring per divisi">' + ico('briefcase-business', 14) + '<select class="wa-tpd-filter">' + dOpts + '</select><span class="wa-dd-chev">' + ico('chevron-down', 14) + '</span></label>' +
      '<label class="wa-dd' + (waState.tfF ? ' is-on' : '') + '" title="Saring per topik (klasifikasi AI)">' + ico('message-circle', 14) + '<select class="wa-tpt-filter">' + tOpts + '</select><span class="wa-dd-chev">' + ico('chevron-down', 14) + '</span></label>' +
      (waState.tfF && waState.tfF !== '__none' ? '<label class="wa-dd' + (waState.tfEver ? ' is-on' : '') + '" title="Topik saat ini, atau pernah ditanyakan sebelumnya (untuk follow-up)"><select class="wa-tpe-filter"><option value="">Topik saat ini</option><option value="1"' + (waState.tfEver ? ' selected' : '') + '>Pernah ditanyakan</option></select><span class="wa-dd-chev">' + ico('chevron-down', 14) + '</span></label>' : '');
  }
  function tfBindFilterBar() {
    var d = $('#waFilterBar .wa-tpd-filter'), t = $('#waFilterBar .wa-tpt-filter'), e = $('#waFilterBar .wa-tpe-filter');
    if (d) d.onchange = function () { waState.tfDF = this.value; var tt = tfTopic(waState.tfF); if (tt && waState.tfDF && waState.tfDF !== '__none' && tt.div !== waState.tfDF) waState.tfF = ''; fetchWaConvs(); };
    if (t) t.onchange = function () { waState.tfF = this.value; if (!this.value || this.value === '__none') waState.tfEver = false; fetchWaConvs(); };
    if (e) e.onchange = function () { waState.tfEver = this.value === '1'; fetchWaConvs(); };
  }
  function tfEmptySuffix() {
    if (!tfOn()) return '';
    var s = '';
    if (waState.tfDF) s += ' · divisi "' + (waState.tfDF === '__none' ? 'Belum berlabel' : ((tfDiv(waState.tfDF) || {}).name || waState.tfDF)) + '"';
    if (waState.tfF) s += ' · topik "' + (waState.tfF === '__none' ? 'Belum berlabel' : ((tfTopic(waState.tfF) || {}).name || waState.tfF)) + '"' + (waState.tfEver ? ' (pernah ditanyakan)' : '');
    return s;
  }
  function tfBadgeHtml(tp) {
    if (!tfOn() || !tp || !tp.t || !tp.t.length) return '';
    var main = tp.m || tp.t[0];
    var more = tp.t.length - 1;
    return ' ' + tfChip(main) + (more > 0 ? ' <span class="tag" style="background:#f1f5f9;color:#475569" title="' + esc(tp.t.filter(function (x) { return x !== main; }).map(function (x) { return (tfTopic(x) || {}).name || x; }).join(', ')) + '">+' + more + '</span>' : '') +
      (tp.lk ? ' <span title="Label dikoreksi manual (' + esc(tp.by) + ')" style="color:var(--muted)">' + ico('pen-tool', 11) + '</span>' : '');
  }
  function tfThreadRowHtml(res) {
    if (!tfOn()) return '';
    var tp = res.tp;
    var chips = (tp && tp.t && tp.t.length) ? tp.t.map(function (x) { return tfChip(x, x === tp.m ? ';outline:2px solid currentColor;outline-offset:-1px' : ''); }).join(' ') : '<span style="color:var(--muted);font-size:12px">Topik belum terdeteksi</span>';
    var past = (tp && tp.h) ? tp.h.filter(function (x) { return tp.t.indexOf(x) < 0 && tfTopic(x); }) : [];
    var info = tp ? (tp.lk ? 'dikoreksi ' + esc(tp.by) : 'AI') : '';
    return '<div class="tf-th-row">' + ico('message-circle', 12) + ' ' + chips +
      (info ? ' <span style="color:var(--muted);font-size:11px">· ' + info + '</span>' : '') +
      ' <a href="#" id="tfEditBtn" style="font-size:12px;text-decoration:none">' + ico('pen-tool', 12) + ' ubah</a>' +
      (past.length ? '<div style="font-size:11px;color:var(--muted);margin-top:2px">Pernah tanya: ' + past.map(function (x) { return esc(tfTopic(x).name); }).join(', ') + '</div>' : '') +
      '</div>';
  }
  function tfBindThread(num, res) {
    var b = $('#tfEditBtn');
    if (b) b.onclick = function (ev) { ev.preventDefault(); tfEditModal(num, res.tp); };
  }
  function tfEditModal(num, tp) {
    var old = $('#tfModal'); if (old) old.remove();
    var sel = (tp && tp.t) ? tp.t.slice() : [], main = (tp && tp.m) || '';
    var conf = waState.tp || {};
    var groups = (conf.divisions || []).concat([{ id: '', name: 'Tanpa divisi' }]).map(function (d) {
      var ts = (conf.topics || []).filter(function (t) { return (t.div || '') === d.id; });
      if (!ts.length) return '';
      return '<div class="tf-m-grp"><div class="tf-m-gh">' + esc(d.name) + '</div>' + ts.map(function (t) {
        var on = sel.indexOf(t.id) > -1;
        return '<div class="tf-m-row"><label><input type="checkbox" data-tpc="' + esc(t.id) + '"' + (on ? ' checked' : '') + '> ' + esc(t.name) + '</label>' +
          '<label class="tf-m-main" title="Topik utama"><input type="radio" name="tfMain" value="' + esc(t.id) + '"' + (main === t.id ? ' checked' : '') + '> utama</label></div>';
      }).join('') + '</div>';
    }).join('');
    var m = document.createElement('div');
    m.id = 'tfModal'; m.className = 'tf-modal';
    m.innerHTML = '<div class="tf-modal-box"><div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><b>Topik percakapan</b><button type="button" class="btn ghost sm" id="tfMClose">' + ico('x', 14) + '</button></div>' +
      '<p style="font-size:12px;color:var(--muted);margin:4px 0 10px">Label yang Anda simpan dikunci — AI tidak akan menimpanya. Pilih "Kembalikan ke AI" untuk klasifikasi otomatis lagi.</p>' +
      '<div class="tf-m-list">' + groups + '</div>' +
      '<div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px;flex-wrap:wrap">' +
        (tp ? '<button type="button" class="btn ghost sm" id="tfMAuto">' + ico('sparkles', 14) + ' Kembalikan ke AI</button>' : '') +
        '<button type="button" class="btn sm" id="tfMSave">' + ico('save', 14) + ' Simpan</button></div></div>';
    document.body.appendChild(m);
    var close = function () { m.remove(); };
    m.onclick = function (e) { if (e.target === m) close(); };
    $('#tfMClose').onclick = close;
    $$('#tfModal [data-tpc]').forEach(function (c) { c.onchange = function () { var r = $('#tfModal input[name="tfMain"][value="' + c.dataset.tpc + '"]'); if (!c.checked && r && r.checked) r.checked = false; if (c.checked && !$('#tfModal input[name="tfMain"]:checked') && r) r.checked = true; }; });
    $$('#tfModal input[name="tfMain"]').forEach(function (r) { r.onchange = function () { var c = $('#tfModal [data-tpc="' + r.value + '"]'); if (c) c.checked = true; }; });
    var done = function (r) {
      if (r && r.ok) { toast('Topik disimpan.'); close(); fetchWaConvs(); if (String(waState.current) === String(num)) fetchWaThread(num, true); }
      else toast((r && r.error) || 'Gagal menyimpan topik.', true);
    };
    $('#tfMSave').onclick = function () {
      var t = $$('#tfModal [data-tpc]').filter(function (c) { return c.checked; }).map(function (c) { return c.dataset.tpc; });
      var mm = $('#tfModal input[name="tfMain"]:checked');
      api('tp_label', { method: 'POST', body: { number: num, op: 'set', t: t, m: mm ? mm.value : (t[0] || '') } }).then(done);
    };
    if ($('#tfMAuto')) $('#tfMAuto').onclick = function () {
      api('tp_label', { method: 'POST', body: { number: num, op: 'auto' } }).then(function (r) { if (r && r.ok) toast('AI akan mengklasifikasi ulang dalam ±1 menit.'); done(r); });
    };
  }

  /* ---- menu Topik & Divisi ---- */
  function loadTopik() {
    tfBindPanel();
    api('tp_get').then(function (r) {
      if (!r || !r.ok) { toast((r && r.error) || 'Gagal memuat Topik & Divisi.', true); return; }
      TF.d = r; TF.conf = JSON.parse(JSON.stringify(r.conf)); TF.presets = r.presets || []; TF.dirty = false;
      tfRender();
    });
  }
  function tfRender() {
    var r = TF.d, c = TF.conf, q = r.quota || {};
    var lk = $('#tfLock');
    lk.classList.toggle('hide', !r.locked);
    if (r.locked) lk.innerHTML = '<div class="gc-lock-ic">' + ico('crown', 22) + '</div><div><b>Fitur paket Growth</b><p>' + esc(r.locked_msg) +
      (r.plan && r.plan.tier ? ' Paket Anda saat ini: <b>' + esc(r.plan.tier.charAt(0).toUpperCase() + r.plan.tier.slice(1)) + '</b>.' : '') + '</p></div>';
    var st = $('#tfStatus');
    st.className = 'pill ' + (r.active ? 'on' : 'off');
    st.textContent = r.active ? 'Aktif' : (r.locked ? 'Terkunci' : 'Nonaktif');
    // kuota & backfill
    var qh = '';
    if (q.central) {
      if (q.limit > 0) {
        var pct = Math.min(100, q.pct || 0);
        qh = '<div style="display:flex;justify-content:space-between;font-size:13px"><span>Kuota klasifikasi bulan ini</span><b>' + Number(q.used).toLocaleString('id-ID') + ' / ' + Number(q.limit).toLocaleString('id-ID') + '</b></div>' +
          '<div class="tf-bar"><span style="width:' + pct + '%;background:' + (pct >= 100 ? '#dc2626' : pct >= 80 ? '#f59e0b' : 'var(--brand)') + '"></span></div>' +
          '<div style="font-size:12px;color:var(--muted)">Reset ' + esc(q.reset) + '. Satu chat rata-rata 1–3 klasifikasi.' + (q.out ? ' <b style="color:#b91c1c">Kuota habis — label lama tetap bisa difilter, label baru berhenti sampai reset.</b>' : (pct >= 80 ? ' <b style="color:#b45309">Kuota hampir habis.</b>' : '')) + '</div>';
      } else qh = '<div style="font-size:13px;color:var(--muted)">Kuota klasifikasi: ' + (q.limit === 0 ? 'tidak termasuk paket ini.' : 'akan tampil setelah klasifikasi pertama.') + '</div>';
    } else qh = '<div style="font-size:13px;color:var(--muted)">Instalasi mandiri: klasifikasi memakai API key AI di menu Widget &amp; API (tanpa kuota).</div>';
    var bf = r.backfill;
    if (bf) {
      var tot = bf.total || 0, dn = (bf.done || 0) + (bf.fail || 0);
      qh += '<div style="margin-top:10px;font-size:13px">' + ico('rotate-cw', 13) + ' Klasifikasi chat lama: ' +
        (bf.finished_at ? 'selesai — ' + bf.done + ' chat' + (bf.fail ? ', ' + bf.fail + ' gagal' : '') : dn + ' / ' + tot + ' chat (berjalan di latar, ±10 chat per menit)') + '</div>';
    }
    if (r.labeled != null) qh += '<div style="font-size:12px;color:var(--muted);margin-top:4px">' + Number(r.labeled).toLocaleString('id-ID') + ' kontak sudah berlabel topik.</div>';
    qh += '<div style="margin-top:10px"><button type="button" class="btn ghost sm" id="tfBackfillBtn"' + (r.active ? '' : ' disabled') + '>' + ico('rotate-cw', 14) + ' Klasifikasi chat 7 hari terakhir</button></div>';
    $('#tfQuota').innerHTML = qh;
    // pengaturan
    $('#tfEnabled').checked = !!c.enabled;
    $('#tfEnabled').disabled = !!r.locked && !c.enabled;
    $('#tfPreset').innerHTML = '<option value="">— Pilih preset industri —</option>' + TF.presets.map(function (p) {
      return '<option value="' + esc(p.key) + '"' + (c.preset === p.key ? ' selected' : '') + '>' + esc(p.name) + '</option>';
    }).join('');
    tfRenderLists();
    $('#tfBackfillBtn').onclick = function () {
      if (!confirm('Klasifikasikan semua chat WA 7 hari terakhir yang belum berlabel? Memakai kuota klasifikasi.')) return;
      api('tp_backfill', { method: 'POST', body: { days: 7 } }).then(function (x) { if (x && x.ok) { toast('Diantrekan ' + x.backfill.total + ' chat.'); loadTopik(); } else toast((x && x.error) || 'Gagal.', true); });
    };
  }
  function tfRenderLists() {
    var c = TF.conf;
    $('#tfDivList').innerHTML = c.divisions.map(function (d, i) {
      var col = TF_COLORS[i % TF_COLORS.length];
      return '<div class="tf-row"><span class="tf-dot" style="background:' + col[1] + '"></span><input type="text" data-tpdn="' + i + '" value="' + esc(d.name) + '" maxlength="40" placeholder="Nama divisi">' +
        '<button type="button" class="btn ghost sm" data-tpdx="' + i + '" title="Hapus">' + ico('trash-2', 14) + '</button></div>';
    }).join('') || '<div style="color:var(--muted);font-size:13px">Belum ada divisi.</div>';
    var dSel = function (cur) { return '<option value="">Tanpa divisi</option>' + c.divisions.map(function (d) { return '<option value="' + esc(d.id) + '"' + (cur === d.id ? ' selected' : '') + '>' + esc(d.name) + '</option>'; }).join(''); };
    $('#tfTopicList').innerHTML = c.topics.map(function (t, i) {
      return '<div class="tf-trow"><input type="text" data-tptn="' + i + '" value="' + esc(t.name) + '" maxlength="50" placeholder="Nama topik">' +
        '<input type="text" data-tptd="' + i + '" value="' + esc(t.desc || '') + '" maxlength="160" placeholder="Petunjuk untuk AI (contoh kata/kalimat pelanggan)">' +
        '<select data-tpts="' + i + '">' + dSel(t.div) + '</select>' +
        '<button type="button" class="btn ghost sm" data-tptx="' + i + '" title="Hapus">' + ico('trash-2', 14) + '</button></div>';
    }).join('') || '<div style="color:var(--muted);font-size:13px">Belum ada topik. Pilih preset industri atau tambah manual.</div>';
    $('#tfCount').textContent = c.topics.length + ' topik · ' + c.divisions.length + ' divisi';
    var mark = function () { TF.dirty = true; };
    $$('#tfDivList [data-tpdn]').forEach(function (el) { el.oninput = function () { c.divisions[+el.dataset.tpdn].name = el.value; mark(); }; });
    $$('#tfDivList [data-tpdx]').forEach(function (el) { el.onclick = function () {
      var id = c.divisions[+el.dataset.tpdx].id; c.divisions.splice(+el.dataset.tpdx, 1);
      c.topics.forEach(function (t) { if (t.div === id) t.div = ''; }); mark(); tfRenderLists(); }; });
    $$('#tfTopicList [data-tptn]').forEach(function (el) { el.oninput = function () { c.topics[+el.dataset.tptn].name = el.value; mark(); }; });
    $$('#tfTopicList [data-tptd]').forEach(function (el) { el.oninput = function () { c.topics[+el.dataset.tptd].desc = el.value; mark(); }; });
    $$('#tfTopicList [data-tpts]').forEach(function (el) { el.onchange = function () { c.topics[+el.dataset.tpts].div = el.value; mark(); }; });
    $$('#tfTopicList [data-tptx]').forEach(function (el) { el.onclick = function () { c.topics.splice(+el.dataset.tptx, 1); mark(); tfRenderLists(); }; });
  }
  function tfNewId(name, list) {
    var b = String(name || 'x').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 28) || 'x', id = b, i = 2;
    while (list.some(function (x) { return x.id === id; })) id = b + '_' + i++;
    return id;
  }
  function tfBindPanel() {
    if (tfBindPanel.done) return; tfBindPanel.done = true;
    $('#tfApplyPreset').onclick = function () {
      var k = $('#tfPreset').value; if (!k) { toast('Pilih preset dulu.', true); return; }
      var p = TF.presets.filter(function (x) { return x.key === k; })[0]; if (!p) return;
      if ((TF.conf.topics.length || TF.conf.divisions.length) && !confirm('Ganti semua divisi & topik dengan preset "' + p.name + '"? Label chat lama dengan topik yang tidak ada di preset tidak lagi tampil di filter.')) return;
      TF.conf.preset = k; TF.conf.divisions = JSON.parse(JSON.stringify(p.divisions)); TF.conf.topics = JSON.parse(JSON.stringify(p.topics)); TF.dirty = true;
      tfRenderLists(); toast('Preset diterapkan — klik Simpan.');
    };
    $('#tfAddDiv').onclick = function () {
      if (TF.conf.divisions.length >= 12) { toast('Maksimal 12 divisi.', true); return; }
      TF.conf.divisions.push({ id: tfNewId('divisi ' + (TF.conf.divisions.length + 1), TF.conf.divisions), name: '' }); TF.dirty = true; tfRenderLists();
      var l = $$('#tfDivList [data-tpdn]'); if (l.length) l[l.length - 1].focus();
    };
    $('#tfAddTopic').onclick = function () {
      if (TF.conf.topics.length >= 40) { toast('Maksimal 40 topik.', true); return; }
      TF.conf.topics.push({ id: tfNewId('topik ' + (TF.conf.topics.length + 1), TF.conf.topics), name: '', desc: '', div: '' }); TF.dirty = true; tfRenderLists();
      var l = $$('#tfTopicList [data-tptn]'); if (l.length) l[l.length - 1].focus();
    };
    $('#tfSave').onclick = function () {
      var c = TF.conf;
      c.enabled = $('#tfEnabled').checked;
      if (c.topics.some(function (t) { return !String(t.name || '').trim(); })) { toast('Ada topik tanpa nama.', true); return; }
      if (c.divisions.some(function (d) { return !String(d.name || '').trim(); })) { toast('Ada divisi tanpa nama.', true); return; }
      var first = c.enabled && !TF.d.conf.enabled;
      api('tp_save', { method: 'POST', body: c }).then(function (r) {
        if (!r || !r.ok) { toast((r && r.error) || 'Gagal menyimpan.', true); return; }
        toast(first && r.backfill && r.backfill.total ? 'Tersimpan. ' + r.backfill.total + ' chat 7 hari terakhir sedang diklasifikasi di latar.' : 'Pengaturan topik tersimpan.');
        loaded.wachat && fetchWaConvs && fetchWaConvs(true);
        loadTopik();
      });
    };
  }
