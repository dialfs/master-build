
  /* ====================================================================== *
   *  v1.2.101: percakapan — Laporan › Kinerja Layanan
   * ====================================================================== */
  var sv = { wired: false, kind: '', page: 1, per: 25, last: null };
  var SV_STATUS = { open: ['Ditangani bot', '#e0e7ff', '#3730a3'], handover: ['Menunggu agent', '#fee2e2', '#b91c1c'], assigned: ['Ditangani agent', '#fef3c7', '#92400e'],
                    resolved: ['Selesai', '#dcfce7', '#166534'], expired: ['Kedaluwarsa', '#e5e7eb', '#374151'] };
  var SV_REASON = { keyword: 'Kata kunci handoff', ai_limit: 'Batas balasan AI', ai_fail: 'AI gagal menjawab', manual_mode: 'Mode Manual', mode_human: 'Nomor sudah mode manusia',
                    takeover: 'Diambil alih admin', agent_reply: 'Agent langsung membalas', assign: 'Di-assign admin/routing', claimed: 'Masih dipegang agent',
                    escalation: 'Eskalasi darurat', outbound: 'Agent memulai chat', lainnya: 'Lainnya' };
  var SV_DAYS = ['', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'];
  function svDur(s) {
    if (s == null) return '–';
    s = Math.max(0, Math.round(s));
    if (s < 60) return s + ' dtk';
    var d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60), x = s % 60;
    if (d) return d + ' hari ' + h + ' jam';
    if (h) return h + ' jam ' + m + ' mnt';
    return m + ' mnt ' + x + ' dtk';
  }
  function svNum(n) { return n == null ? '–' : Number(n).toLocaleString('id-ID'); }
  function svPct(n) { return n == null ? '–' : String(n).replace('.', ',') + '%'; }
  // selisih vs periode sebelumnya. lowerBetter: waktu (makin kecil makin baik)
  function svDelta(cur, prev, isTime, lowerBetter) {
    if (!sv.last || !sv.last.prev || !sv.last.prev.has_data || cur == null || prev == null) return '<div class="sv-d">–</div>';
    var diff = cur - prev;
    if (diff === 0) return '<div class="sv-d">sama dengan periode lalu</div>';
    var good = lowerBetter ? diff < 0 : diff > 0;
    var txt;
    if (isTime) txt = (diff < 0 ? 'lebih cepat ' : 'lebih lambat ') + svDur(Math.abs(diff));
    else txt = (diff > 0 ? '▲ ' : '▼ ') + svNum(Math.abs(diff)) + (prev ? ' (' + Math.round(Math.abs(diff) * 100 / prev) + '%)' : '');
    return '<div class="sv-d ' + (good ? 'up' : 'down') + '">' + txt + '</div>';
  }
  function svCard(label, value, sub, delta, tip, kind) {
    return '<div class="sv-c' + (kind ? ' sv-click' : '') + '"' + (kind ? ' data-kind="' + kind + '"' : '') + (tip ? ' title="' + esc(tip) + '"' : '') + '>' +
      '<div class="sv-l">' + label + '</div><div class="sv-v">' + value + '</div>' +
      (sub ? '<div class="sv-s">' + sub + '</div>' : '') + (delta || '') + '</div>';
  }
  function svBars(vals, labels, color, fmt) {
    var max = Math.max(1, Math.max.apply(null, vals));
    var W = 520, H = 170, pl = 30, pb = 22, pt = 14, n = vals.length, bw = (W - pl - 6) / n;
    var g = '';
    for (var k = 0; k <= 4; k++) {
      var yy = pt + (H - pt - pb) * k / 4;
      g += '<line x1="' + pl + '" y1="' + yy + '" x2="' + W + '" y2="' + yy + '" stroke="var(--line)"/><text x="' + (pl - 4) + '" y="' + (yy + 3) + '" text-anchor="end" font-size="9" fill="var(--muted)">' + Math.round(max * (1 - k / 4)) + '</text>';
    }
    vals.forEach(function (v, i) {
      var h = (H - pt - pb) * v / max, x = pl + i * bw + bw * 0.15;
      g += '<rect x="' + x.toFixed(1) + '" y="' + (H - pb - h).toFixed(1) + '" width="' + (bw * 0.7).toFixed(1) + '" height="' + h.toFixed(1) + '" rx="2" fill="' + color + '"><title>' + esc(labels[i]) + ': ' + (fmt ? fmt(v) : v) + '</title></rect>';
      if (n <= 8 || i % 3 === 0) g += '<text x="' + (x + bw * 0.35).toFixed(1) + '" y="' + (H - 7) + '" text-anchor="middle" font-size="9" fill="var(--muted)">' + esc(labels[i]) + '</text>';
    });
    return '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" style="max-width:560px;display:block">' + g + '</svg>';
  }
  function svLines(rows, series) {
    if (!rows.length) return '<div style="color:var(--muted);padding:24px;text-align:center">Belum ada data.</div>';
    var W = 520, H = 190, pl = 30, pb = 22, pt = 10, pr = 8, n = rows.length;
    var max = 1; rows.forEach(function (d) { series.forEach(function (s) { max = Math.max(max, d[s.key]); }); });
    function X(i) { return pl + (n <= 1 ? (W - pl - pr) / 2 : i / (n - 1) * (W - pl - pr)); }
    function Y(v) { return pt + (H - pt - pb) * (1 - v / max); }
    var g = '';
    for (var k = 0; k <= 4; k++) { var yy = pt + (H - pt - pb) * k / 4; g += '<line x1="' + pl + '" y1="' + yy + '" x2="' + (W - pr) + '" y2="' + yy + '" stroke="var(--line)"/><text x="' + (pl - 4) + '" y="' + (yy + 3) + '" text-anchor="end" font-size="9" fill="var(--muted)">' + Math.round(max * (1 - k / 4)) + '</text>'; }
    series.forEach(function (s) {
      g += '<polyline fill="none" stroke="' + s.color + '" stroke-width="2" points="' + rows.map(function (d, i) { return X(i).toFixed(1) + ',' + Y(d[s.key]).toFixed(1); }).join(' ') + '"/>';
      if (n <= 45) g += rows.map(function (d, i) { return '<circle cx="' + X(i).toFixed(1) + '" cy="' + Y(d[s.key]).toFixed(1) + '" r="2.4" fill="' + s.color + '"><title>' + d.date + ' · ' + s.label + ': ' + d[s.key] + '</title></circle>'; }).join('');
    });
    var ev = Math.ceil(n / 8);
    rows.forEach(function (d, i) { if (i % ev === 0 || i === n - 1) g += '<text x="' + X(i).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="middle" font-size="8.5" fill="var(--muted)">' + d.date.slice(8) + '/' + d.date.slice(5, 7) + '</text>'; });
    var lg = series.map(function (s) { return '<span style="display:inline-flex;align-items:center;gap:5px;margin-right:14px"><span style="width:14px;height:3px;border-radius:2px;background:' + s.color + '"></span>' + s.label + '</span>'; }).join('');
    return '<div style="font-size:12px;color:var(--muted);margin-bottom:6px">' + lg + '</div><svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" style="max-width:560px;display:block">' + g + '</svg>';
  }
  function svQuery() {
    var q = '&from=' + encodeURIComponent($('#svFrom').value) + '&to=' + encodeURIComponent($('#svTo').value);
    if ($('#svCh') && $('#svCh').value) q += '&ch=' + encodeURIComponent($('#svCh').value);
    return q;
  }
  function svLoad() {
    $('#svConv').innerHTML = '<div style="color:var(--muted);padding:8px">Memuat…</div>';
    api('conv_report', { query: svQuery() }).then(function (r) {
      if (!r || !r.ok) { $('#svConv').innerHTML = '<div style="color:#b91c1c;padding:8px">' + esc((r && r.error) || 'Gagal memuat laporan.') + '</div>'; return; }
      sv.last = r; svRender(r);
      sv.page = 1; svList();
    });
  }
  function svRender(r) {
    var T = r.totals, A = r.avg, P = r.prev.totals, PA = r.prev.avg;
    var chs = r.channels_all || [];
    if (chs.length > 1 && $('#svCh').options.length <= 1) {
      $('#svCh').innerHTML = '<option value="">Semua nomor</option>' + chs.map(function (c) { return '<option value="' + esc(c.id) + '">' + esc(c.label) + '</option>'; }).join('');
      $('#svChWrap').style.display = '';
    }
    var since = r.tracking_since ? new Date(r.tracking_since * 1000).toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' }) : null;
    $('#svNote').innerHTML = (since ? 'Data percakapan tercatat sejak <b>' + since + '</b>. ' : 'Belum ada percakapan tercatat — data mulai terkumpul sejak pembaruan ini terpasang. ') +
      'Dibandingkan dengan ' + esc(r.prev.from) + ' s/d ' + esc(r.prev.to) + '. Percakapan selesai otomatis bila pelanggan diam ' + r.timeout_hours + ' jam setelah balasan terakhir; pesan dalam ' + r.reopen_minutes + ' menit setelah selesai membuka percakapan yang sama.';
    var dl = function (k, lb) { return svDelta(T[k], P[k], false, lb); };
    var dt = function (k) { return svDelta(A[k], PA[k], true, true); };
    $('#svConv').innerHTML =
      svCard('Total Percakapan', svNum(T.total), svNum(T.customers) + ' pelanggan · ' + svNum(T.outbound) + ' dimulai agent', dl('total'), '', 'all') +
      svCard('Belum Di-assign', svNum(T.unassigned), 'menunggu agent saat ini', '', 'Sudah diserahkan ke manusia tapi belum ada agent yang memegang.', 'unassigned') +
      svCard('Di-assign ke Agent', svNum(T.assigned), svNum(T.in_progress) + ' masih berjalan', dl('assigned'), '', 'assigned') +
      svCard('Diselesaikan', svNum(T.resolved), svPct(A.resolved_rate) + ' · ' + svNum(T.resolved_agent) + ' ditandai agent', dl('resolved'), 'Ditandai Selesai oleh agent, pelanggan pamit, atau pelanggan diam 24 jam setelah dibalas.', 'resolved');
    $('#svTime').innerHTML =
      svCard('Respon Pertama', svDur(A.frt), 'bot atau agent', dt('frt'), 'Rata-rata jeda dari pesan pertama pelanggan sampai balasan pertama.') +
      svCard('Respon Pertama Agent', svDur(A.frt_agent), 'sejak diserahkan ke agent', dt('frt_agent'), 'Rata-rata jeda dari diserahkan ke manusia sampai balasan pertama agent.') +
      svCard('Waktu Antre', svDur(A.wait), 'sampai di-assign', dt('wait'), 'Rata-rata jeda dari diserahkan ke manusia sampai ada agent yang memegang.') +
      svCard('Waktu Respon Agent', svDur(A.resp_agent), 'tiap pesan pelanggan', dt('resp_agent'), 'Rata-rata jeda setiap pesan pelanggan sampai dibalas agent.') +
      svCard('Waktu Penyelesaian', svDur(A.resolution), 'dibuka → selesai', dt('resolution'), 'Rata-rata dari percakapan dibuka sampai selesai.');
    $('#svBot').innerHTML = T.bot_handled === 0
      ? '<div class="sv-c" style="grid-column:1/-1;color:var(--muted)">Belum ada percakapan yang dijawab bot pada periode ini' + (T.total ? ' (Mode Manual / bot WhatsApp nonaktif).' : '.') + '</div>'
      : svCard('Ditangani Bot', svNum(T.bot_handled), 'percakapan dibalas bot', dl('bot_handled')) +
        svCard('Diselesaikan Bot', svNum(T.bot_resolved), svPct(A.bot_rate) + ' tanpa bantuan agent', dl('bot_resolved'), '', 'bot_resolved') +
        svCard('Diserahkan ke Agent', svNum(T.to_agent), svPct(A.handover_rate) + ' dari yang ditangani bot', dl('to_agent', true), '', 'to_agent') +
        svCard('Waktu Selesai oleh Bot', svDur(A.bot_resolution), 'dibuka → selesai', dt('bot_resolution'));
    $('#svTrend').innerHTML = svLines(r.daily, [{ key: 'bot_resolved', label: 'Diselesaikan bot', color: BRAND_C1 }, { key: 'to_agent', label: 'Diserahkan ke agent', color: '#f59e0b' }, { key: 'total', label: 'Total', color: '#94a3b8' }]);
    var rs = Object.keys(r.handover_reasons || {}), rtot = rs.reduce(function (a, k) { return a + r.handover_reasons[k]; }, 0);
    $('#svReasons').innerHTML = rs.length ? rs.map(function (k) {
      var v = r.handover_reasons[k], p = Math.round(v * 100 / rtot);
      return '<div style="margin:8px 0"><div style="display:flex;justify-content:space-between;font-size:13px"><span>' + esc(SV_REASON[k] || k) + '</span><span class="mono" style="color:var(--muted)">' + v + ' · ' + p + '%</span></div>' +
        '<div style="height:7px;background:var(--brand-soft);border-radius:4px;margin-top:4px"><div style="height:100%;width:' + p + '%;background:var(--brand);border-radius:4px"></div></div></div>';
    }).join('') : '<div style="color:var(--muted);padding:24px;text-align:center">Tidak ada percakapan yang diserahkan ke agent.</div>';
    var hl = []; for (var h = 0; h < 24; h++) hl.push((h < 10 ? '0' : '') + h);
    $('#svHourly').innerHTML = svBars(r.hourly, hl, BRAND_C1);
    var pk = r.hourly.indexOf(Math.max.apply(null, r.hourly));
    $('#svHourlyNote').textContent = T.inbound ? 'Paling ramai pukul ' + hl[pk] + ':00–' + hl[(pk + 1) % 24] + ':00 WIB.' : '';
    $('#svWeekday').innerHTML = svBars(r.weekday.map(function (w) { return w.avg; }), r.weekday.map(function (w) { return SV_DAYS[w.day].slice(0, 3); }), BRAND_C2, function (v) { return String(v).replace('.', ',') + ' per hari'; });
    $('#svAgents').innerHTML = r.agents.length ? r.agents.map(function (a) {
      return '<tr><td><b>' + esc(a.name || a.agent) + '</b>' + (a.name && a.name !== a.agent ? ' <span style="color:var(--muted);font-size:12px">' + esc(a.agent) + '</span>' : '') + '</td>' +
        '<td class="mono r">' + svNum(a.assigned) + '</td><td class="mono r">' + svNum(a.resolved) + '</td><td class="mono r">' + svNum(a.in_progress) + '</td>' +
        '<td class="mono r">' + svDur(a.frt) + '</td><td class="mono r">' + svDur(a.resp) + '</td><td class="mono r">' + svDur(a.resolution) + '</td><td class="mono r">' + svNum(a.msgs) + '</td></tr>';
    }).join('') : emptyRow(8);
    $('#svChCard').style.display = (r.channels.length > 1 || chs.length > 1) ? '' : 'none';
    $('#svChans').innerHTML = r.channels.length ? r.channels.map(function (c) {
      return '<tr><td><b>' + esc(c.label) + '</b></td><td class="mono r">' + svNum(c.total) + '</td><td class="mono r">' + svNum(c.bot_resolved) + '</td><td class="mono r">' + svNum(c.to_agent) + '</td>' +
        '<td class="mono r">' + svNum(c.unassigned) + '</td><td class="mono r">' + svNum(c.resolved) + '</td><td class="mono r">' + svDur(c.frt) + '</td><td class="mono r">' + svDur(c.frt_agent) + '</td><td class="mono r">' + svDur(c.resolution) + '</td></tr>';
    }).join('') : emptyRow(9);
    $$('#repService .sv-click').forEach(function (el) { el.onclick = function () { svSetKind(el.dataset.kind === 'all' ? '' : el.dataset.kind); $('#svListCard').scrollIntoView({ behavior: 'smooth', block: 'start' }); }; });
  }
  function svSetKind(k) {
    sv.kind = k; sv.page = 1;
    $$('#svChips .lg-chip').forEach(function (b) { b.classList.toggle('on', b.dataset.k === k); });
    svList();
  }
  function svList() {
    api('conv_list', { query: svQuery() + '&kind=' + encodeURIComponent(sv.kind) + '&page=' + sv.page + '&per=' + sv.per }).then(function (r) {
      if (!r || !r.ok) { $('#svRows').innerHTML = emptyRow(7); return; }
      var RB = { agent: 'Agent', guest_bye: 'Pelanggan pamit', timeout: 'Otomatis (diam 24 jam)' };
      $('#svRows').innerHTML = r.rows.length ? r.rows.map(function (c) {
        var st = SV_STATUS[c.status] || [c.status, '#eee', '#333'];
        var opened = new Date(c.opened_at * 1000);
        var tgl = opened.toLocaleDateString('id-ID', { day: '2-digit', month: 'short' }) + ' ' + opened.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
        var frt = c.first_reply_at ? c.first_reply_at - c.opened_at : null;
        var res = c.resolved_at ? c.resolved_at - c.opened_at : null;
        var by = c.status === 'resolved' ? (RB[c.resolved_by] || c.resolved_by) + (c.resolved_by === 'agent' && c.resolver ? ' (' + esc(c.resolver) + ')' : '') : '';
        return '<tr class="sv-row" data-num="' + esc(c.num) + '"><td class="mono" style="white-space:nowrap">' + esc(tgl) + '</td>' +
          '<td><b>' + esc(c.name || ('+' + c.num)) + '</b>' + (c.name ? '<div style="color:var(--muted);font-size:12px">+' + esc(c.num) + '</div>' : '') +
          (c.origin === 'outbound' ? ' <span class="tag" style="background:#ede9fe;color:#5b21b6">dimulai agent</span>' : '') + (c.reopen_n ? ' <span class="tag">dibuka ulang ' + c.reopen_n + 'x</span>' : '') + '</td>' +
          '<td><span class="tag" style="background:' + st[1] + ';color:' + st[2] + '">' + st[0] + '</span>' + (c.handover_reason ? '<div style="color:var(--muted);font-size:11.5px;margin-top:3px">' + esc(SV_REASON[c.handover_reason] || c.handover_reason) + '</div>' : '') + '</td>' +
          '<td>' + esc(c.agent || '–') + '</td><td class="mono r">' + svDur(frt) + '</td><td class="mono r">' + svDur(res) + '</td><td style="font-size:12.5px">' + (by || '–') + '</td></tr>';
      }).join('') : emptyRow(7);
      var pages = Math.max(1, Math.ceil(r.total / r.per));
      $('#svPageInfo').textContent = svNum(r.total) + ' percakapan · hal ' + r.page + '/' + pages;
      $('#svPrev').disabled = r.page <= 1; $('#svNext').disabled = r.page >= pages;
      $$('#svRows .sv-row').forEach(function (tr) { tr.onclick = function () { openLeadConv(tr.dataset.num); }; });
    });
  }
  function svInit() {
    if (sv.wired) { if (!sv.last) svLoad(); return; }
    sv.wired = true;
    var now = new Date(Date.now() + 7 * 3600e3), today = now.toISOString().slice(0, 10);
    $('#svFrom').value = today.slice(0, 8) + '01'; $('#svTo').value = today;
    $$('#svPresets button').forEach(function (b) {
      b.onclick = function () {
        var p = b.dataset.p, t = new Date(Date.now() + 7 * 3600e3), f;
        if (p === 'month') f = t.toISOString().slice(0, 8) + '01';
        else if (p === 'last') { var d = new Date(Date.UTC(t.getUTCFullYear(), t.getUTCMonth(), 0)); $('#svTo').value = d.toISOString().slice(0, 10); f = d.toISOString().slice(0, 8) + '01'; }
        else f = new Date(t.getTime() - (+p - 1) * 864e5).toISOString().slice(0, 10);
        $('#svFrom').value = f; if (p !== 'last') $('#svTo').value = t.toISOString().slice(0, 10);
        $$('#svPresets button').forEach(function (x) { x.classList.toggle('on', x === b); });
        svLoad();
      };
    });
    $('#svApply').onclick = svLoad;
    $('#svCh').onchange = svLoad;
    $('#svExport').onclick = function () {
      window.location.href = API + '?action=conv_export&token=' + encodeURIComponent(token) + svQuery() + '&kind=' + encodeURIComponent(sv.kind);
      toast('Mengunduh CSV…');
    };
    $$('#svChips .lg-chip').forEach(function (b) { b.onclick = function () { svSetKind(b.dataset.k); }; });
    $('#svPrev').onclick = function () { if (sv.page > 1) { sv.page--; svList(); } };
    $('#svNext').onclick = function () { sv.page++; svList(); };
    svLoad();
  }

  // v1.2.101: tombol Selesai di thread WA
  function resolveConv(num) {
    var b = $('#waResolveBtn'); if (b) b.disabled = true;
    api('wa_resolve', { method: 'POST', body: { number: num } }).then(function (res) {
      if (res && res.ok) { toast('Percakapan ditandai selesai.'); fetchWaThread(num); fetchWaConvs(); }
      else { toast((res && res.error) || 'Gagal menandai selesai.', true); if (b) b.disabled = false; }
    });
  }
