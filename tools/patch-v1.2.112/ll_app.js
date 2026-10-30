  /* ---- v1.2.112: login-log — Riwayat Login (tab Pengguna) & Riwayat Login Saya (Profil) ---- */
  var LL_REASON = { wrong_password: 'Password salah', unknown_user: 'Username tidak dikenal', locked: 'Terkunci sementara (5x gagal)',
    seat_limit: 'Di luar kursi paket', not_sa: 'Bukan Super Admin', not_admin: 'Bukan Admin' };
  var LL_METHOD = { password: 'Password', sso: 'Tautan dari Pusat' };
  var llRowsCache = [];
  function llStatusHtml(e) {
    return e.ok ? '<span class="tag" style="background:#dcfce7;color:#166534">Berhasil</span>'
      : '<span class="tag" style="background:#fee2e2;color:#b91c1c">Gagal</span>' +
        (e.r ? ' <span class="help" style="font-size:11px">' + esc(LL_REASON[e.r] || e.r) + '</span>' : '');
  }
  function loadLoginLog() {
    var card = $('#llCard');
    if (!card) return;
    if (!can('super_admin,admin')) { card.style.display = 'none'; return; }
    card.style.display = '';
    if (!card.dataset.wired) {
      card.dataset.wired = '1';
      ['#llUser', '#llStatus', '#llDays'].forEach(function (s) { $(s).onchange = loadLoginLog; });
      $('#llRefresh').onclick = loadLoginLog;
      $('#llCsv').onclick = llCsv;
    }
    var q = '&limit=300&days=' + encodeURIComponent($('#llDays').value) +
      '&status=' + encodeURIComponent($('#llStatus').value) + '&user=' + encodeURIComponent($('#llUser').value);
    $('#llRows').innerHTML = '<tr><td colspan="6" class="help">Memuat…</td></tr>';
    api('login_log', { query: q }).then(function (res) {
      if (!res.ok) { $('#llRows').innerHTML = '<tr><td colspan="6" style="color:#b91c1c">' + esc(res.error || 'Gagal memuat riwayat login') + '</td></tr>'; return; }
      var sel = $('#llUser'), cur = sel.value;
      sel.innerHTML = '<option value="">Semua pengguna</option>' + (res.usernames || []).map(function (u) {
        return '<option value="' + esc(u) + '">' + esc(u) + '</option>';
      }).join('');
      sel.value = cur;
      var st = res.stats || {};
      $('#llStats').innerHTML = '24 jam terakhir: <b style="color:#166534">' + (st.ok24 || 0) + '</b> berhasil · <b style="color:#b91c1c">' + (st.fail24 || 0) + '</b> gagal';
      llRowsCache = res.entries || [];
      $('#llRows').innerHTML = llRowsCache.length ? llRowsCache.map(function (e) {
        return '<tr><td class="mono" style="white-space:nowrap">' + esc(e.ts) + '</td>' +
          '<td>' + esc(e.u) + (e.name && e.name !== e.u ? ' <span class="help" style="font-size:11px">' + esc(e.name) + '</span>' : '') +
            (e['in'] ? ' <span class="tag">Tim DEI</span>' : '') + '</td>' +
          '<td>' + llStatusHtml(e) + '</td>' +
          '<td>' + esc(LL_METHOD[e.m] || e.m || '') + '</td>' +
          '<td class="mono">' + esc(e.ip || '') + '</td>' +
          '<td title="' + esc(e.ua || '') + '">' + esc(e.dev || '—') + '</td></tr>';
      }).join('') : '<tr><td colspan="6" class="help">Belum ada catatan login pada rentang ini.</td></tr>';
      $('#llMore').textContent = res.total > llRowsCache.length
        ? ('Menampilkan ' + llRowsCache.length + ' dari ' + res.total + ' catatan. Persempit filter untuk melihat sisanya.')
        : (res.total ? res.total + ' catatan.' : '');
    });
  }
  function llCsv() {
    if (!llRowsCache.length) { toast('Tidak ada data untuk diunduh.', true); return; }
    var cell = function (v) {
      v = String(v == null ? '' : v);
      if (/^[=+\-@]/.test(v)) v = "'" + v;   // cegah formula injection di Excel
      return '"' + v.replace(/"/g, '""') + '"';
    };
    var rows = [['Waktu (WIB)', 'Username', 'Nama', 'Peran', 'Status', 'Alasan', 'Metode', 'IP', 'Perangkat', 'User Agent']]
      .concat(llRowsCache.map(function (e) {
        return [e.ts, e.u, e.name || '', e.role || '', e.ok ? 'Berhasil' : 'Gagal', e.r ? (LL_REASON[e.r] || e.r) : '',
          LL_METHOD[e.m] || e.m || '', e.ip || '', e.dev || '', e.ua || ''];
      }));
    var blob = new Blob(['﻿' + rows.map(function (r) { return r.map(cell).join(','); }).join('\r\n')], { type: 'text/csv;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'riwayat-login-' + new Date().toISOString().slice(0, 10) + '.csv';
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }
  function loadMyLoginLog() {
    var box = $('#myLlRows');
    if (!box) return;
    api('my_login_log').then(function (res) {
      if (!res.ok) { box.innerHTML = esc(res.error || 'Gagal memuat riwayat login.'); return; }
      var en = res.entries || [];
      box.innerHTML = en.length
        ? '<div class="scroll"><table class="tbl"><thead><tr><th>Waktu (WIB)</th><th>Status</th><th>IP</th><th>Perangkat</th></tr></thead><tbody>' +
          en.map(function (e) {
            return '<tr><td class="mono" style="white-space:nowrap">' + esc(e.ts) + '</td><td>' + llStatusHtml(e) + '</td>' +
              '<td class="mono">' + esc(e.ip || '') + '</td><td>' + esc(e.dev || '—') + '</td></tr>';
          }).join('') + '</tbody></table></div>'
        : 'Belum ada catatan login (riwayat mulai tercatat sejak v1.2.112).';
    });
  }
  /* ---- /v1.2.112 ---- */
