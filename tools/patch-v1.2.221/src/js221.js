

  /* ====================================================================== *
   *  v1.2.221: laporan-sales — menu Laporan Sales (Growth+)
   *  Performa & Target · Aktivitas · Produktivitas · Forecast · Funnel & Win/Loss · Umur Lead
   * ====================================================================== */
  var SR_PRESETS221 = { thismonth: 'Bulan ini', lastmonth: 'Bulan lalu', thisweek: 'Minggu ini', lastweek: 'Minggu lalu', last7: '7 hari terakhir', last30: '30 hari terakhir',
                        thisquarter: 'Kuartal ini', lastquarter: 'Kuartal lalu', thisyear: 'Tahun ini', custom: 'Pilih tanggal' };
  function srRange221(p) {
    var t = new Date(); t.setHours(12, 0, 0, 0);
    var q = Math.floor(t.getMonth() / 3);
    if (p === 'thisquarter') return [crmYmd217(new Date(t.getFullYear(), q * 3, 1, 12)), crmYmd217(t)];
    if (p === 'lastquarter') return [crmYmd217(new Date(t.getFullYear(), q * 3 - 3, 1, 12)), crmYmd217(new Date(t.getFullYear(), q * 3, 0, 12))];
    if (p === 'thisyear') return [crmYmd217(new Date(t.getFullYear(), 0, 1, 12)), crmYmd217(t)];
    return crmRange217(p);
  }
  var srS221 = { preset: 'thismonth', from: '', to: '', sales: '', div: '', view: 'perf', data: null, actType: '', actQ: '' };
  try { var _sr = JSON.parse(localStorage.getItem('dei_sr221') || '{}'); if (_sr.preset && SR_PRESETS221[_sr.preset] && _sr.preset !== 'custom') srS221.preset = _sr.preset; if (_sr.view) srS221.view = _sr.view; } catch (e) {}
  var SR_VIEWS221 = [['perf', 'target', 'Performa &amp; Target'], ['act', 'activity', 'Aktivitas'], ['prod', 'clock-3', 'Produktivitas'],
                     ['fc', 'wallet', 'Forecast'], ['fun', 'layers', 'Funnel &amp; Win/Loss'], ['age', 'alarm-clock', 'Umur Lead']];
  var SR_COL221 = { call: '#4f46e5', wa: '#16a34a', meeting: '#ea580c', visit: '#0891b2', email: '#9333ea', presentasi: '#db2777', penawaran: '#ca8a04', other: '#64748b' };
  var SR_MON221 = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
  function srSave221() { try { localStorage.setItem('dei_sr221', JSON.stringify({ preset: srS221.preset, view: srS221.view })); } catch (e) {} }
  function srMon221(ym) { var p = String(ym).split('-'); return p.length === 2 ? SR_MON221[(+p[1]) - 1] + ' ' + p[0] : ym; }
  function srPct221(v) { return v === null || v === undefined ? '—' : v + '%'; }
  function srNum221(v) { return v === null || v === undefined ? '—' : String(v).replace('.', ','); }
  function srDays221(v) { return v === null || v === undefined ? '—' : (+v < 1 ? '&lt; 1' : srNum221(v)); }
  function srBar221(pct, cls) { pct = Math.max(0, Math.min(100, +pct || 0)); return '<span class="sr-bar' + (cls ? ' ' + cls : '') + '"><i style="width:' + pct + '%"></i></span>'; }
  function srAttCls221(p) { return p === null || p === undefined ? '' : (p >= 100 ? 'good' : (p >= 70 ? '' : 'bad')); }
  function srTile221(l, b, s, c) { return '<div class="crm-pt' + (c ? ' ' + c : '') + '"><div class="crm-pt-l">' + l + '</div><div class="crm-pt-b">' + b + '</div><div class="crm-pt-s">' + (s || '') + '</div></div>'; }
  function srTbl221(head, rows, cls) {
    return '<div class="scroll"><table class="tbl sr-t' + (cls ? ' ' + cls : '') + '"><thead><tr>' + head.map(function (h) { return '<th>' + h + '</th>'; }).join('') + '</tr></thead><tbody>' +
      (rows.length ? rows.join('') : '<tr><td colspan="' + head.length + '" class="help">Belum ada data untuk periode / filter ini.</td></tr>') + '</tbody></table></div>';
  }
  function srSec221(title, sub, inner) { return '<div class="card sr-card"><div class="sr-h"><b>' + title + '</b>' + (sub ? '<span class="help">' + sub + '</span>' : '') + '</div>' + inner + '</div>'; }

  function srLoad221() {
    var root = $('#srRoot'); if (!root) return;
    var S = srS221;
    if (!S.from) { var r0 = srRange221(S.preset); S.from = r0[0]; S.to = r0[1]; }
    root.innerHTML =
      '<div class="rep-seg" id="srSeg">' + SR_VIEWS221.map(function (v) { return '<button type="button" data-v="' + v[0] + '"' + (v[0] === S.view ? ' class="on"' : '') + '>' + ico(v[1], 15, 'style="vertical-align:-3px"') + ' ' + v[2] + '</button>'; }).join('') + '</div>' +
      '<div class="card sr-bar-card"><div class="crm-perf-bar" style="margin:0">' +
        '<select id="srPre" style="width:auto">' + Object.keys(SR_PRESETS221).map(function (k) { return '<option value="' + k + '"' + (k === S.preset ? ' selected' : '') + '>' + SR_PRESETS221[k] + '</option>'; }).join('') + '</select>' +
        '<input type="date" id="srFrom"><span class="help">s/d</span><input type="date" id="srTo">' +
        '<select id="srSales" style="width:auto;display:none" title="Filter sales"></select>' +
        '<select id="srDiv" style="width:auto;display:none" title="Filter divisi"></select>' +
        '<button type="button" class="btn ghost sm" id="srGo">Tampilkan</button>' +
        '<button type="button" class="btn ghost sm" id="srCsv">' + ico('download', 14) + ' CSV</button>' +
        '<button type="button" class="btn ghost sm" id="srTgt" style="display:none;margin-left:auto">' + ico('target', 14) + ' Target sales</button>' +
      '</div></div>' +
      '<div id="srBody"><div class="card help">Memuat…</div></div>';
    $('#srFrom').value = S.from; $('#srTo').value = S.to;
    $$('#srSeg button').forEach(function (b) { b.onclick = function () { S.view = b.dataset.v; srSave221(); $$('#srSeg button').forEach(function (x) { x.classList.toggle('on', x === b); }); srPaint221(); }; });
    $('#srPre').onchange = function () {
      S.preset = this.value; srSave221();
      if (S.preset !== 'custom') { var r = srRange221(S.preset); S.from = r[0]; S.to = r[1]; $('#srFrom').value = S.from; $('#srTo').value = S.to; srFetch221(); }
    };
    var cust = function () { S.preset = 'custom'; $('#srPre').value = 'custom'; };
    $('#srFrom').onchange = cust; $('#srTo').onchange = cust;
    $('#srGo').onclick = function () { S.from = $('#srFrom').value; S.to = $('#srTo').value; srFetch221(); };
    $('#srSales').onchange = function () { S.sales = this.value; srFetch221(); };
    $('#srDiv').onchange = function () { S.div = this.value; srFetch221(); };
    $('#srCsv').onclick = srCsv221;
    $('#srTgt').onclick = srTargets221;
    srFetch221();
  }
  function srFetch221() {
    var S = srS221, body = $('#srBody'); if (!body) return;
    if (!S.from || !S.to) { toast('Isi tanggal awal & akhir.', true); return; }
    body.style.opacity = '.5';
    api('sales_rep', { query: '&from=' + encodeURIComponent(S.from) + '&to=' + encodeURIComponent(S.to) + '&sales=' + encodeURIComponent(S.sales) + '&div=' + encodeURIComponent(S.div) }).then(function (r) {
      body.style.opacity = '';
      if (!r || !r.ok) {
        body.innerHTML = '<div class="card" style="text-align:center;color:var(--muted)">' + esc((r && r.error) || 'Gagal memuat laporan.') + '</div>';
        return;
      }
      S.data = r; srFilters221(); srPaint221();
    });
  }
  function srFilters221() {
    var r = srS221.data, sel = $('#srSales'), dv = $('#srDiv');
    if (!r || r.own) { sel.style.display = 'none'; dv.style.display = 'none'; }
    else {
      sel.innerHTML = '<option value="">Semua sales</option>' + (r.sales || []).map(function (x) { return '<option value="' + esc(x.id) + '"' + (x.id === srS221.sales ? ' selected' : '') + '>' + esc(x.name) + (x.active ? '' : ' (nonaktif)') + '</option>'; }).join('') +
        '<option value="_none"' + (srS221.sales === '_none' ? ' selected' : '') + '>Tanpa sales</option>';
      sel.style.display = '';
      if ((r.divs || []).length) {
        dv.innerHTML = '<option value="">Semua divisi</option>' + r.divs.map(function (d) { return '<option value="' + esc(d) + '"' + (d === srS221.div ? ' selected' : '') + '>' + esc(d) + '</option>'; }).join('');
        dv.style.display = '';
      } else dv.style.display = 'none';
    }
    $('#srTgt').style.display = r && r.can_target ? '' : 'none';
  }
  function srPaint221() {
    var r = srS221.data, body = $('#srBody'); if (!r || !body) return;
    var per = crmFmtD215(r.from) + ' – ' + crmFmtD215(r.to);
    var who = r.own ? 'Kinerja Anda' : (srS221.sales ? ((r.sales || []).filter(function (x) { return x.id === srS221.sales; })[0] || { name: 'Tanpa sales' }).name : (srS221.div ? 'Divisi ' + srS221.div : 'Semua sales'));
    var head = '<div class="sr-per">' + esc(who) + ' · ' + esc(per) + ' <span class="help">· dibuat ' + esc(r.generated) + ' WIB</span></div>';
    var v = srS221.view, h = '';
    if (v === 'act') h = srAct221(r); else if (v === 'prod') h = srProd221(r); else if (v === 'fc') h = srFc221(r);
    else if (v === 'fun') h = srFun221(r); else if (v === 'age') h = srAge221(r); else h = srPerf221(r);
    body.innerHTML = head + h;
    var q = $('#srActQ'), ty = $('#srActTy');
    if (q) q.oninput = function () { srS221.actQ = q.value; srActList221(); };
    if (ty) ty.onchange = function () { srS221.actType = ty.value; srActList221(); };
    if (q) srActList221();
  }

  /* ---- Performa & Target ---- */
  function srPerf221(r) {
    var P = r.perf, T = P.total, tg = T.target;
    var tiles = '<div class="crm-pts">' +
      srTile221('Nilai Close Deal', esc(crmRpShort216(T.deal_v)), tg && tg.rev ? srBar221(T.att_rev, srAttCls221(T.att_rev)) + ' ' + srPct221(T.att_rev) + ' dari target ' + esc(crmRpShort216(tg.rev)) : T.deal + ' deal · target belum diatur', 'good') +
      srTile221('Jumlah deal', T.deal, tg && tg.deals ? srPct221(T.att_deals) + ' dari target ' + tg.deals : 'PO ' + T.po + ' · lose ' + T.lost) +
      srTile221('Win rate', srPct221(T.win), T.deal + ' deal · ' + T.lost + ' lose') +
      srTile221('Rata-rata deal', esc(crmRpShort216(T.avg_deal)), T.cycle === null ? 'lama closing —' : '±' + srDays221(T.cycle) + ' hari dari lead ke closing') +
      srTile221('Lead baru', T.new, 'masuk dalam periode') +
      srTile221('Aktivitas', T.acts, tg && tg.acts ? srPct221(Math.round(T.acts * 100 / tg.acts)) + ' dari target ' + tg.acts : 'follow-up selesai ' + T.fu_done) +
      srTile221('Pipeline terbuka', esc(crmRpShort216(T.open_v)), T.open + ' lead · tertimbang ' + esc(crmRpShort216(T.weighted))) +
    '</div>';
    var rows = P.rows.map(function (x) {
      var t = x.target;
      return '<tr><td><b>' + esc(x.name) + '</b>' + (x.active || !x.id ? '' : ' <span class="help">(nonaktif)</span>') + (x.div ? '<div class="help">' + esc(x.div) + '</div>' : '') + '</td>' +
        '<td class="num">' + esc(crmRpFmt216(x.deal_v)) + '</td><td class="num">' + (t && t.rev ? esc(crmRpShort216(t.rev)) : '—') + '</td>' +
        '<td style="min-width:120px">' + (x.att_rev === null ? '<span class="help">—</span>' : srBar221(x.att_rev, srAttCls221(x.att_rev)) + ' <b>' + x.att_rev + '%</b>') + '</td>' +
        '<td class="num">' + x.deal + (t && t.deals ? ' <span class="help">/ ' + t.deals + '</span>' : '') + '</td>' +
        '<td class="num">' + x.acts + (t && t.acts ? ' <span class="help">/ ' + t.acts + '</span>' : '') + '</td>' +
        '<td class="num">' + srPct221(x.win) + '</td><td class="num">' + esc(crmRpShort216(x.avg_deal)) + '</td><td class="num">' + (x.cycle === null ? '—' : srDays221(x.cycle) + ' hr') + '</td>' +
        '<td class="num">' + x.new + '</td><td class="num">' + x.po + '</td><td class="num">' + x.lost + '</td>' +
        '<td class="num">' + esc(crmRpShort216(x.open_v)) + ' <span class="help">(' + x.open + ')</span></td></tr>';
    });
    var rank = P.rows.filter(function (x) { return x.id; }).slice().sort(function (a, b) { return b.deal_v - a.deal_v; }).slice(0, 5);
    var mx = rank.length ? Math.max(1, rank[0].deal_v) : 1;
    return tiles +
      srSec221('Pencapaian per sales', 'Target bulanan dihitung pro-rata sesuai panjang periode (' + srNum221(P.month_frac) + ' bulan).',
        srTbl221(['Sales', 'Nilai deal', 'Target', 'Pencapaian', 'Deal', 'Aktivitas', 'Win', 'Rata-rata', 'Lama closing', 'Lead baru', 'PO', 'Lose', 'Pipeline'], rows)) +
      (rank.length > 1 ? srSec221('Peringkat nilai deal', '', rank.map(function (x, i) { return '<div class="sr-rank"><span>' + (i + 1) + '. ' + esc(x.name) + '</span>' + srBar221(x.deal_v * 100 / mx) + '<b>' + esc(crmRpShort216(x.deal_v)) + '</b></div>'; }).join('')) : '') +
      (r.can_target && !T.target ? '<p class="help" style="margin:8px 2px">Belum ada target. Klik <b>Target sales</b> untuk mengisi target bulanan (nilai deal, jumlah deal, aktivitas) per sales.</p>' : '');
  }

  /* ---- Aktivitas ---- */
  function srAct221(r) {
    var A = r.activity, types = r.types || {};
    var chips = Object.keys(A.by_type || {}).map(function (k) { return '<span class="sr-chip"><i style="background:' + (SR_COL221[k] || '#64748b') + '"></i>' + esc(types[k] || k) + ' <b>' + A.by_type[k] + '</b></span>'; }).join('');
    var mx = 1; A.days.forEach(function (d) { if (d.n > mx) mx = d.n; });
    var tkeys = Object.keys(A.by_type || {});
    var chart = '<div class="sr-chart">' + A.days.map(function (d) {
      var seg = tkeys.map(function (k) { var n = (d.t || {})[k] || 0; return n ? '<i style="height:' + (n * 100 / mx) + '%;background:' + (SR_COL221[k] || '#64748b') + '"></i>' : ''; }).join('');
      var dt = new Date(d.d + 'T12:00:00'), sun = dt.getDay() === 0;
      return '<div class="sr-col' + (sun ? ' sun' : '') + '" title="' + esc(crmFmtD215(d.d)) + ': ' + d.n + ' aktivitas"><div class="sr-stack">' + seg + '</div><span>' + (A.days.length <= 31 ? dt.getDate() : '') + '</span></div>';
    }).join('') + '</div>';
    var mrows = (A.by_sales || []).map(function (x) {
      return '<tr><td><b>' + esc(x.name) + '</b></td><td class="num"><b>' + x.n + '</b></td>' + tkeys.map(function (k) { return '<td class="num">' + ((x.t || {})[k] || '<span class="help">0</span>') + '</td>'; }).join('') + '</tr>';
    });
    var tyOpt = '<option value="">Semua jenis</option>' + tkeys.map(function (k) { return '<option value="' + esc(k) + '"' + (k === srS221.actType ? ' selected' : '') + '>' + esc(types[k] || k) + '</option>'; }).join('');
    return '<div class="crm-pts">' + srTile221('Total aktivitas', A.total, 'dicatat sales di lead (tanpa catatan sistem)') +
        srTile221('Rata-rata per hari', srNum221(Math.round(A.total * 10 / Math.max(1, A.days.length)) / 10), A.days.length + ' hari dalam periode') +
        srTile221('Jenis terbanyak', tkeys.length ? esc(types[tkeys[0]] || tkeys[0]) : '—', tkeys.length ? A.by_type[tkeys[0]] + ' kali' : '') + '</div>' +
      srSec221('Aktivitas per hari', '', (chips ? '<div class="sr-chips">' + chips + '</div>' : '') + chart) +
      srSec221('Per sales &amp; jenis', 'Dihitung ke sales pemilik lead.', srTbl221(['Sales', 'Total'].concat(tkeys.map(function (k) { return esc(types[k] || k); })), mrows)) +
      srSec221('Daftar aktivitas', A.list_more ? 'Menampilkan 500 terbaru dari ' + A.total + '.' : '',
        '<div class="crm-perf-bar" style="margin:0 0 8px"><select id="srActTy" style="width:auto">' + tyOpt + '</select><input type="search" id="srActQ" placeholder="Cari lead, catatan, pencatat…" value="' + esc(srS221.actQ) + '" style="flex:1;min-width:160px;max-width:320px"></div><div id="srActList"></div>');
  }
  function srActList221() {
    var r = srS221.data, box = $('#srActList'); if (!r || !box) return;
    var types = r.types || {}, q = (srS221.actQ || '').toLowerCase(), ty = srS221.actType;
    var L = (r.activity.list || []).filter(function (a) { return (!ty || a.type === ty) && (!q || (a.lead + ' ' + a.text + ' ' + a.by + ' ' + a.sales).toLowerCase().indexOf(q) !== -1); });
    box.innerHTML = srTbl221(['Waktu', 'Jenis', 'Lead', 'Catatan', 'Sales', 'Dicatat oleh', 'Follow-up'], L.slice(0, 300).map(function (a) {
      return '<tr><td style="white-space:nowrap">' + esc(crmFmtD215(a.at) + ' ' + String(a.at).slice(11, 16)) + '</td><td><span class="sr-chip"><i style="background:' + (SR_COL221[a.type] || '#64748b') + '"></i>' + esc(types[a.type] || a.type) + '</span></td>' +
        '<td><b>' + esc(a.lead) + '</b></td><td class="sr-txt">' + esc(a.text) + '</td><td>' + esc(a.sales) + '</td><td>' + esc(a.by) + '</td><td>' + (a.next ? esc(crmFmtD215(a.next)) : '') + '</td></tr>';
    })) + (L.length > 300 ? '<p class="help">' + (L.length - 300) + ' lagi — persempit dengan pencarian atau unduh CSV.</p>' : '');
  }

  /* ---- Produktivitas ---- */
  function srProd221(r) {
    var P = r.productivity, T = P.total;
    var rows = P.rows.map(function (x) {
      return '<tr><td><b>' + esc(x.name) + '</b>' + (x.active || !x.id ? '' : ' <span class="help">(nonaktif)</span>') + '</td><td class="num">' + x.acts + '</td><td class="num">' + srNum221(x.per_day) + '</td>' +
        '<td class="num">' + x.active_days + '<span class="help"> / ' + x.workdays + '</span></td><td class="num">' + x.touched + '</td><td class="num">' + srNum221(x.per_lead) + '</td>' +
        '<td class="num">' + x.fu_due + '</td><td class="num">' + x.fu_ontime + '</td><td class="num">' + x.fu_late_done + '</td><td class="num"' + (x.fu_missed ? ' style="color:#b91c1c;font-weight:600"' : '') + '>' + x.fu_missed + '</td>' +
        '<td style="min-width:110px">' + (x.compliance === null ? '<span class="help">—</span>' : srBar221(x.compliance, srAttCls221(x.compliance >= 90 ? 100 : x.compliance)) + ' <b>' + x.compliance + '%</b>') + '</td>' +
        '<td class="num">' + (x.resp_med_h === null ? '—' : srNum221(x.resp_med_h) + ' jam') + (x.resp_none ? '<div class="help">' + x.resp_none + ' belum disentuh</div>' : '') + '</td>' +
        '<td class="num">' + x.open + '</td><td class="num"' + (x.idle ? ' style="color:#b45309;font-weight:600"' : '') + '>' + x.idle + '</td></tr>';
    });
    return '<div class="crm-pts">' +
        srTile221('Aktivitas per hari kerja', srNum221(T.per_day), T.acts + ' aktivitas · ' + P.workdays + ' hari kerja (Sen–Sab)') +
        srTile221('Lead disentuh', T.touched, srNum221(T.per_lead) + ' aktivitas per lead') +
        srTile221('Kepatuhan follow-up', srPct221(T.compliance), T.fu_ontime + ' tepat waktu · ' + T.fu_late_done + ' telat · ' + T.fu_missed + ' terlewat', T.compliance !== null && T.compliance < 70 ? 'bad' : (T.compliance >= 90 ? 'good' : '')) +
        srTile221('Respons lead baru', T.resp_med_h === null ? '—' : srNum221(T.resp_med_h) + ' jam', 'median lead masuk → aktivitas pertama' + (T.resp_none ? ' · ' + T.resp_none + ' belum disentuh' : '')) +
        srTile221('Lead diam &gt; 7 hari', T.idle, 'termasuk belum disentuh · dari ' + T.open + ' lead terbuka (saat ini)', T.idle ? 'bad' : '') +
      '</div>' +
      srSec221('Produktivitas per sales', 'Follow-up = jadwal follow-up yang jatuh tempo dalam periode. Tepat waktu = ditandai selesai paling lambat di tanggal jatuh temponya.',
        srTbl221(['Sales', 'Aktivitas', 'Per hari', 'Hari aktif', 'Lead disentuh', 'Akt./lead', 'FU jatuh tempo', 'Tepat waktu', 'Selesai telat', 'Terlewat', 'Kepatuhan', 'Respons lead baru', 'Lead terbuka', 'Diam &gt;7 hr'], rows));
  }

  /* ---- Forecast ---- */
  function srFc221(r) {
    var F = r.forecast, m0 = F.months[0], m1 = F.months[1];
    var b0 = F.buckets.filter(function (b) { return b.key === m0; })[0] || {}, bo = F.buckets.filter(function (b) { return b.key === 'overdue'; })[0] || {};
    var won0 = 0, tg0 = 0, wt0 = 0;
    F.by_sales.forEach(function (x) { var m = x.months[m0] || {}; won0 += m.won || 0; tg0 += m.target || 0; wt0 += m.weighted || 0; });
    var proj = won0 + wt0, att = tg0 ? Math.round(proj * 100 / tg0) : null;
    var mxp = 1; F.buckets.forEach(function (b) { if (b.pipe > mxp) mxp = b.pipe; });
    var bRows = F.buckets.map(function (b) {
      var lab = b.key === 'overdue' ? '<span style="color:#b91c1c">Lewat perkiraan closing</span>' : (b.key === 'later' ? 'Sesudahnya' : (b.key === 'none' ? 'Tanpa perkiraan closing' : srMon221(b.key)));
      return '<tr><td><b>' + lab + '</b></td><td class="num">' + b.n + '</td><td style="min-width:140px">' + srBar221(b.pipe * 100 / mxp) + ' ' + esc(crmRpShort216(b.pipe)) + '</td><td class="num">' + esc(crmRpShort216(b.best)) + '</td><td class="num">' + esc(crmRpShort216(b.commit)) + '</td><td class="num"><b>' + esc(crmRpShort216(b.weighted)) + '</b></td></tr>';
    });
    var sRows = F.by_sales.map(function (x) {
      var cell = function (mm) { var m = x.months[mm] || {}; return '<td class="num">' + (m.target ? esc(crmRpShort216(m.target)) : '—') + '</td><td class="num">' + esc(crmRpShort216(m.won || 0)) + '</td><td class="num">' + esc(crmRpShort216(m.commit || 0)) + '</td><td class="num">' + esc(crmRpShort216(m.weighted || 0)) + '</td><td style="min-width:110px">' + (m.att === null || m.att === undefined ? '<b>' + esc(crmRpShort216(m.projected || 0)) + '</b>' : srBar221(m.att, srAttCls221(m.att)) + ' <b>' + m.att + '%</b>') + '</td>'; };
      return '<tr><td><b>' + esc(x.name) + '</b></td>' + cell(m0) + cell(m1) + '</tr>';
    });
    var dRows = F.deals.map(function (d) {
      return '<tr' + (d.overdue ? ' class="sr-late"' : '') + '><td style="white-space:nowrap">' + esc(crmFmtD215(d.ce)) + (d.overdue ? ' <span class="sr-tag bad">lewat</span>' : '') + '</td><td><b>' + esc(d.lead) + '</b>' + (d.company ? '<div class="help">' + esc(d.company) + '</div>' : '') + '</td><td>' + esc(d.sales) + '</td>' +
        '<td>' + esc(d.st_label) + ' <span class="help">' + d.prob + '%</span></td><td class="num">' + esc(crmRpFmt216(d.v)) + '</td><td class="num">' + esc(crmRpShort216(d.weighted)) + '</td><td>' + (d.last ? esc(crmFmtD215(d.last)) : '<span class="help">belum ada</span>') + '</td></tr>';
    });
    var stg = (F.stages || []).map(function (s) { return esc(s.label) + ' ' + s.prob + '%'; }).join(' · ');
    return '<div class="crm-pts">' +
        srTile221('Proyeksi ' + srMon221(m0), esc(crmRpShort216(proj)), (att === null ? 'sudah closing ' + esc(crmRpShort216(won0)) + ' + tertimbang ' + esc(crmRpShort216(wt0)) : srBar221(att, srAttCls221(att)) + ' ' + att + '% dari target ' + esc(crmRpShort216(tg0))), 'good') +
        srTile221('Commit ' + srMon221(m0), esc(crmRpShort216((b0.commit || 0) + (bo.commit || 0))), 'tahap peluang ≥ 70%, closing bulan ini / lewat') +
        srTile221('Best case ' + srMon221(m0), esc(crmRpShort216((b0.best || 0) + (bo.best || 0))), 'tahap peluang ≥ 40%') +
        srTile221('Lewat perkiraan closing', bo.n || 0, esc(crmRpShort216(bo.pipe || 0)) + ' — perbarui tanggal atau status', bo.n ? 'bad' : '') +
      '</div>' +
      srSec221('Forecast per bulan perkiraan closing', 'Kondisi pipeline saat ini (tidak terpengaruh periode). Tertimbang = nilai × peluang tahap (' + stg + ').',
        srTbl221(['Bulan closing', 'Lead', 'Pipeline', 'Best case', 'Commit', 'Tertimbang'], bRows)) +
      srSec221('Forecast per sales', 'Proyeksi = sudah Close Deal di bulan itu + nilai tertimbang. Bulan ini termasuk lead yang lewat perkiraan closing.',
        srTbl221(['Sales', 'Target ' + srMon221(m0), 'Closing', 'Commit', 'Tertimbang', 'Proyeksi', 'Target ' + srMon221(m1), 'Closing', 'Commit', 'Tertimbang', 'Proyeksi'], sRows)) +
      srSec221('Deal yang diperkirakan closing', 'Lead terbuka dengan perkiraan closing sampai ' + srMon221(F.months[3]) + ', urut tanggal.',
        srTbl221(['Perkiraan closing', 'Lead', 'Sales', 'Tahap', 'Nilai', 'Tertimbang', 'Aktivitas terakhir'], dRows));
  }

  /* ---- Funnel & Win/Loss ---- */
  function srFun221(r) {
    var F = r.funnel;
    var fun = F.stages.map(function (s, i) {
      return '<div class="sr-fun"><span class="sr-fun-l">' + esc(s.label) + '</span><span class="sr-fun-b"><i style="width:' + (s.pct || 0) + '%"></i><b>' + s.n + '</b></span>' +
        '<span class="sr-fun-p">' + srPct221(s.pct) + (i && s.step !== null ? '<span class="help"> · ' + s.step + '% dari tahap sebelumnya</span>' : '') + '</span></div>';
    }).join('');
    var src = F.by_source.map(function (x) {
      return '<tr><td><b>' + esc(x.label) + '</b></td><td class="num">' + x.leads + '</td><td class="num">' + x.deal + '</td><td class="num">' + x.lost + '</td><td class="num">' + x.open + '</td><td class="num">' + srPct221(x.conv) + '</td><td class="num">' + srPct221(x.win) + '</td><td class="num">' + esc(crmRpShort216(x.deal_v)) + '</td><td class="num">' + esc(crmRpShort216(x.pipe)) + '</td></tr>';
    });
    var dur = F.stage_days.map(function (x) { return '<tr><td>' + esc(x.label) + '</td><td class="num">' + (x.avg_d === null ? '—' : srNum221(x.avg_d) + ' hari') + '</td><td class="num help">' + x.n + '</td></tr>'; });
    var lost = F.lost_list.map(function (x) { return '<tr><td>' + esc(crmFmtD215(x.at)) + '</td><td><b>' + esc(x.lead) + '</b></td><td>' + esc(x.sales) + '</td><td>' + esc(x.stage) + '</td><td class="num">' + esc(crmRpFmt216(x.v)) + '</td><td class="sr-txt">' + (x.reason ? esc(x.reason) : '<span class="help">tanpa catatan</span>') + '</td></tr>'; });
    return '<div class="crm-pts">' +
        srTile221('Lead baru (kohort)', F.cohort, 'dibuat dalam periode; funnel di bawah mengikuti lead ini') +
        srTile221('Win rate', srPct221(F.win), F.won + ' deal · ' + F.lost + ' lose (ditutup dalam periode)', 'good') +
        srTile221('Nilai menang', esc(crmRpShort216(F.won_v)), 'kalah ' + esc(crmRpShort216(F.lost_v))) +
        srTile221('Lama closing', F.cycle === null ? '—' : srDays221(F.cycle) + ' hari', 'rata-rata lead dibuat → Close Deal') +
      '</div>' +
      srSec221('Funnel konversi', 'Tahap tertinggi yang pernah dicapai tiap lead (dari riwayat status). Tahap opsional yang dilewati tidak dihitung.', '<div class="sr-funnel">' + fun + '</div>') +
      srSec221('Per sumber lead', 'Konversi = Close Deal ÷ lead. Win = deal ÷ (deal + lose).', srTbl221(['Sumber', 'Lead', 'Deal', 'Lose', 'Masih jalan', 'Konversi', 'Win', 'Nilai deal', 'Pipeline'], src)) +
      '<div class="sr-2">' +
        srSec221('Rata-rata lama di tiap tahap', 'Semua lead yang pindah tahap.', srTbl221(['Tahap', 'Rata-rata', 'Data'], dur)) +
        srSec221('Kalah di tahap', '', F.lost_at.length ? F.lost_at.map(function (x) { return '<div class="sr-rank"><span>' + esc(x.label) + '</span>' + srBar221(x.n * 100 / Math.max(1, F.lost), 'bad') + '<b>' + x.n + '</b></div>'; }).join('') : '<p class="help">Belum ada Close Lose dalam periode.</p>') +
      '</div>' +
      srSec221('Close Lose &amp; alasannya', 'Alasan diambil dari catatan lead. Isi catatan saat menandai Close Lose supaya analisa kekalahan lebih tajam.', srTbl221(['Tanggal', 'Lead', 'Sales', 'Tahap terakhir', 'Nilai', 'Alasan / catatan'], lost));
  }

  /* ---- Umur Lead ---- */
  function srAge221(r) {
    var A = r.aging, ks = ['0-3', '4-7', '8-14', '15-30', '>30'];
    var mxI = 1, mxA = 1; ks.concat(['never']).forEach(function (k) { if (A.idle[k] && A.idle[k].n > mxI) mxI = A.idle[k].n; }); ks.forEach(function (k) { if (A.age[k].n > mxA) mxA = A.age[k].n; });
    var row = function (lab, x, mx, cls) { return '<div class="sr-rank"><span>' + lab + '</span>' + srBar221(x.n * 100 / mx, cls) + '<b>' + x.n + '</b><span class="help" style="min-width:70px;text-align:right">' + esc(crmRpShort216(x.v)) + '</span></div>'; };
    var idle7 = A.idle['8-14'].n + A.idle['15-30'].n + A.idle['>30'].n;
    var list = A.list.map(function (x) {
      return '<tr><td><b>' + esc(x.lead) + '</b></td><td>' + esc(x.sales) + '</td><td>' + esc(x.st_label) + '</td><td class="num">' + esc(crmRpShort216(x.v)) + '</td><td class="num">' + (x.age === null ? '—' : x.age + ' hr') + '</td>' +
        '<td class="num"' + (x.idle === null || x.idle > 7 ? ' style="color:#b91c1c;font-weight:600"' : '') + '>' + (x.idle === null ? 'belum pernah' : x.idle + ' hr') + '</td><td>' + (x.fu ? esc(crmFmtD215(x.fu)) : '<span class="help">tidak ada</span>') + '</td></tr>';
    });
    var bs = A.by_stage.map(function (x) { return '<tr><td><b>' + esc(x.label) + '</b></td><td class="num">' + x.n + '</td><td class="num">' + srNum221(x.avg_age) + ' hari</td><td class="num">' + (x.avg_idle === null ? '—' : srNum221(x.avg_idle) + ' hari') + '</td></tr>'; });
    return '<div class="crm-pts">' +
        srTile221('Lead terbuka', A.open, 'kondisi saat ini (tidak terpengaruh periode)') +
        srTile221('Diam &gt; 7 hari', idle7, 'tanpa aktivitas sales lebih dari seminggu', idle7 ? 'bad' : 'good') +
        srTile221('Belum pernah disentuh', A.idle.never.n, 'belum ada aktivitas sama sekali', A.idle.never.n ? 'bad' : '') +
      '</div>' +
      '<div class="sr-2">' +
        srSec221('Hari sejak aktivitas terakhir', '', ks.map(function (k) { return row(k + ' hari', A.idle[k], mxI, k === '0-3' || k === '4-7' ? '' : 'bad'); }).join('') + row('belum pernah', A.idle.never, mxI, 'bad')) +
        srSec221('Umur lead (sejak dibuat)', '', ks.map(function (k) { return row(k + ' hari', A.age[k], mxA); }).join('')) +
      '</div>' +
      srSec221('Per tahap', '', srTbl221(['Tahap', 'Lead', 'Rata-rata umur', 'Rata-rata diam'], bs)) +
      srSec221('Lead perlu perhatian', 'Urut dari yang paling lama tidak disentuh.', srTbl221(['Lead', 'Sales', 'Tahap', 'Nilai', 'Umur', 'Diam', 'Follow-up berikut'], list));
  }

  /* ---- CSV per tampilan ---- */
  function srCsv221() {
    var r = srS221.data; if (!r) return;
    var q = function (v) { v = String(v === null || v === undefined ? '' : v); return /[",\n;]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var L = [], v = srS221.view, types = r.types || {}, name = 'laporan-sales';
    var add = function (a) { L.push(a.map(q).join(',')); };
    if (v === 'perf') {
      name = 'performa-target'; add(['Sales', 'Divisi', 'Nilai deal (Rp)', 'Target nilai (Rp)', 'Pencapaian nilai (%)', 'Deal', 'Target deal', 'Aktivitas', 'Target aktivitas', 'Win rate (%)', 'Rata-rata deal', 'Lama closing (hari)', 'Lead baru', 'PO', 'Close Lose', 'Pipeline (Rp)', 'Lead terbuka']);
      r.perf.rows.forEach(function (x) { var t = x.target || {}; add([x.name, x.div, x.deal_v, t.rev, x.att_rev, x.deal, t.deals, x.acts, t.acts, x.win, x.avg_deal, x.cycle, x.new, x.po, x.lost, x.open_v, x.open]); });
    } else if (v === 'act') {
      name = 'aktivitas'; add(['Waktu', 'Jenis', 'Lead', 'Nomor', 'Catatan', 'Sales', 'Dicatat oleh', 'Follow-up']);
      r.activity.list.forEach(function (a) { add([a.at, types[a.type] || a.type, a.lead, a.num, a.text, a.sales, a.by, a.next]); });
    } else if (v === 'prod') {
      name = 'produktivitas'; add(['Sales', 'Aktivitas', 'Per hari kerja', 'Hari aktif', 'Hari kerja', 'Lead disentuh', 'Aktivitas per lead', 'FU jatuh tempo', 'Tepat waktu', 'Selesai telat', 'Terlewat', 'Kepatuhan (%)', 'Lead baru', 'Respons median (jam)', 'Belum disentuh', 'Lead terbuka', 'Diam >7 hari']);
      r.productivity.rows.forEach(function (x) { add([x.name, x.acts, x.per_day, x.active_days, x.workdays, x.touched, x.per_lead, x.fu_due, x.fu_ontime, x.fu_late_done, x.fu_missed, x.compliance, x.new, x.resp_med_h, x.resp_none, x.open, x.idle]); });
    } else if (v === 'fc') {
      name = 'forecast'; add(['Perkiraan closing', 'Lead', 'Nomor', 'Perusahaan', 'Sales', 'Tahap', 'Peluang (%)', 'Nilai (Rp)', 'Tertimbang (Rp)', 'Lewat perkiraan', 'Aktivitas terakhir']);
      r.forecast.deals.forEach(function (d) { add([d.ce, d.lead, d.num, d.company, d.sales, d.st_label, d.prob, d.v, d.weighted, d.overdue ? 'ya' : '', d.last]); });
    } else if (v === 'fun') {
      name = 'funnel-winloss'; add(['Tahap', 'Lead mencapai', '% kohort', '% dari tahap sebelumnya']);
      r.funnel.stages.forEach(function (s) { add([s.label, s.n, s.pct, s.step]); });
      add([]); add(['Sumber', 'Lead', 'Deal', 'Lose', 'Masih jalan', 'Konversi (%)', 'Win (%)', 'Nilai deal (Rp)', 'Pipeline (Rp)']);
      r.funnel.by_source.forEach(function (x) { add([x.label, x.leads, x.deal, x.lost, x.open, x.conv, x.win, x.deal_v, x.pipe]); });
      add([]); add(['Tanggal lose', 'Lead', 'Nomor', 'Sales', 'Tahap terakhir', 'Nilai (Rp)', 'Alasan']);
      r.funnel.lost_list.forEach(function (x) { add([x.at, x.lead, x.num, x.sales, x.stage, x.v, x.reason]); });
    } else {
      name = 'umur-lead'; add(['Lead', 'Nomor', 'Sales', 'Tahap', 'Nilai (Rp)', 'Umur (hari)', 'Diam (hari)', 'Aktivitas terakhir', 'Follow-up berikut']);
      r.aging.list.forEach(function (x) { add([x.lead, x.num, x.sales, x.st_label, x.v, x.age, x.idle === null ? 'belum pernah' : x.idle, x.last, x.fu]); });
    }
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob(['﻿' + L.join('\n')], { type: 'text/csv;charset=utf-8' }));
    a.download = 'laporan-sales-' + name + '-' + r.from + '_' + r.to + '.csv';
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }

  /* ---- Target sales (Super Admin / Admin) ---- */
  function srTargets221() {
    var r = srS221.data; if (!r || !r.can_target) return;
    var tg = r.targets || {}, act = (r.sales || []).filter(function (x) { return x.active; });
    if (!act.length) { toast('Belum ada sales aktif. Buat akun peran Sales di Pengguna.', true); return; }
    var rows = act.map(function (x) {
      var t = tg[x.id] || {};
      return '<tr data-sid="' + esc(x.id) + '"><td><b>' + esc(x.name) + '</b>' + (x.div ? '<div class="help">' + esc(x.div) + '</div>' : '') + '</td>' +
        '<td><input type="text" inputmode="numeric" class="st-rev" value="' + (t.rev ? esc(crmRpFmt216(t.rev).replace('Rp ', '')) : '') + '" placeholder="0" style="width:140px"></td>' +
        '<td><input type="number" min="0" class="st-deals" value="' + (t.deals || '') + '" placeholder="0" style="width:80px"></td>' +
        '<td><input type="number" min="0" class="st-acts" value="' + (t.acts || '') + '" placeholder="0" style="width:90px"></td></tr>';
    }).join('');
    tkModal214(ico('target', 17) + ' Target sales per bulan',
      '<p class="crm-p">Target dipakai di <b>Performa &amp; Target</b> (dihitung pro-rata sesuai panjang periode) dan <b>Forecast</b> (proyeksi bulan ini &amp; bulan depan). Kosongkan bila tidak ada target.</p>' +
      '<div class="scroll"><table class="tbl sr-t"><thead><tr><th>Sales</th><th>Nilai deal (Rp)</th><th>Jumlah deal</th><th>Aktivitas</th></tr></thead><tbody>' + rows + '</tbody></table></div>' +
      '<div class="tk-foot"><button type="button" class="btn ghost tk-x">Batal</button><button type="button" class="btn st-save">Simpan target</button></div>',
      function (ov, close) {
        Array.prototype.slice.call(ov.querySelectorAll('.st-rev')).forEach(function (inp) { inp.oninput = function () { var d = inp.value.replace(/\D/g, ''); inp.value = d ? d.replace(/\B(?=(\d{3})+(?!\d))/g, '.') : ''; }; });
        ov.querySelector('.st-save').onclick = function () {
          var out = {};
          Array.prototype.slice.call(ov.querySelectorAll('tr[data-sid]')).forEach(function (tr) {
            out[tr.getAttribute('data-sid')] = { rev: tr.querySelector('.st-rev').value.replace(/\D/g, ''), deals: +tr.querySelector('.st-deals').value || 0, acts: +tr.querySelector('.st-acts').value || 0 };
          });
          api('sales_target_save', { method: 'POST', body: { targets: out } }).then(function (x) {
            if (!x || !x.ok) { toast((x && x.error) || 'Gagal menyimpan target.', true); return; }
            close(); toast('Target sales disimpan.'); srFetch221();
          });
        };
      });
  }
