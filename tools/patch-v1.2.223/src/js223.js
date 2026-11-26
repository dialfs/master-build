  /* ====================================================================== *
   *  v1.2.223: laporan-pdf — Laporan & Log > Laporan Berkala (PDF mingguan & bulanan → email & WhatsApp)
   * ====================================================================== */
  var rpS223 = { d: null };
  if (!ICONS['file-text']) ICONS['file-text'] = '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>';
  if (!ICONS['calendar-days']) ICONS['calendar-days'] = '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/>';
  if (!ICONS.cpu) ICONS.cpu = '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>';
  if (!ICONS['file-down']) ICONS['file-down'] = '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M12 18v-6"/><path d="m9 15 3 3 3-3"/>';
  function rpCss223() {
    if (document.getElementById('rpCss223')) return;
    var st = document.createElement('style'); st.id = 'rpCss223';
    st.textContent = '.rp-g{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:820px){.rp-g{grid-template-columns:1fr}}' +
      '.rp-box{border:1px solid var(--line,#e6e6ef);border-radius:12px;padding:14px}.rp-box h4{margin:0 0 10px;font-size:14px;display:flex;align-items:center;gap:8px}' +
      '.rp-row{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end;margin-bottom:10px}.rp-row>div{min-width:120px}' +
      '.rp-secs{display:grid;grid-template-columns:1fr 1fr;gap:4px 10px;margin:6px 0 4px}.rp-secs label{font-size:13px;display:flex;gap:6px;align-items:flex-start;cursor:pointer}.rp-secs label.off{opacity:.5}' +
      '.rp-st{font-size:12.5px;color:var(--muted);margin-top:8px;line-height:1.5}.rp-ok{color:#15803d;font-weight:600}.rp-bad{color:#b91c1c;font-weight:600}' +
      '.rp-pill{display:inline-block;font-size:11px;padding:2px 8px;border-radius:99px;background:#eef0fb;color:#33334d;margin:0 4px 4px 0}' +
      '.rp-act{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:14px}';
    document.head.appendChild(st);
  }
  function rpInit223() {
    rpCss223();
    if (!can('super_admin,admin')) { repView('summary'); return; }
    var box = $('#rpCard'); if (!box) return;
    box.innerHTML = '<div class="help">Memuat…</div>';
    api('rpt_get').then(function (r) {
      if (!r || !r.ok) { box.innerHTML = '<h3>Laporan Berkala (PDF)</h3><div class="crm-p ' + (r && r.locked ? 'crm-warn' : '') + '">' + esc((r && r.error) || 'Gagal memuat.') + '</div>'; return; }
      rpS223.d = r; rpRender223();
    });
  }
  function rpSecBox223(r, kind) {
    var on = r.conf[kind].sections || [];
    return '<div class="rp-secs">' + r.sections.map(function (x) {
      return '<label class="' + (x.avail ? '' : 'off') + '" title="' + (x.avail ? '' : 'Butuh fitur CRM (paket Growth+)') + '"><input type="checkbox" class="rp-sec" data-k="' + kind + '" value="' + x.key + '"' + (on.indexOf(x.key) > -1 ? ' checked' : '') + (x.avail ? '' : ' disabled') + '> ' + esc(x.label) + (x.sales ? '' : '') + '</label>';
    }).join('') + '</div>';
  }
  function rpHours223(sel) { var h = ''; for (var i = 5; i <= 21; i++) h += '<option value="' + i + '"' + (i === sel ? ' selected' : '') + '>' + String(i).padStart(2, '0') + ':00 WIB</option>'; return h; }
  function rpPer223(p) {
    if (!p) return '';
    return (p.skipped ? 'Jadwal aktif mulai periode berikutnya (periode <b>' + esc(p.label) + '</b> dilewati karena jadwalnya sudah lewat saat diaktifkan).' : 'Periode laporan berikutnya/terakhir: <b>' + esc(p.label) + '</b> — ' + (p.done ? '<span class="rp-ok">terkirim' + (p.done_at ? ' ' + esc(p.done_at) : '') + '</span>' : 'belum dikirim')) +
      (p.err ? '<br><span class="rp-bad">Gagal: ' + esc(p.err) + '</span>' : '');
  }
  function rpRender223() {
    var r = rpS223.d, c = r.conf, E = r.engine, box = $('#rpCard'), sa = role === 'super_admin';
    var days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'], dom = '';
    for (var i = 1; i <= 28; i++) dom += '<option value="' + i + '"' + (i === c.monthly.dom ? ' selected' : '') + '>Tanggal ' + i + '</option>';
    var rc = r.recipients || [];
    var eng = E.active === 'chrome' ? 'Chromium (' + esc(E.chrome_bin) + ')' : (E.dompdf ? 'dompdf ' + esc(E.dompdf_ver) + (E.dompdf_via === 'vendor' ? ' (composer)' : '') : '<span class="rp-bad">dompdf belum terpasang</span> — dipasang otomatis saat PDF pertama dibuat');
    var h = '<h3 style="display:flex;align-items:center;gap:8px">' + ico('file-text', 17) + ' Laporan Berkala (PDF)</h3>' +
      '<p class="crm-p">Laporan PDF dibuat dan dikirim otomatis setiap minggu dan/atau setiap bulan ke email (lampiran PDF) dan WhatsApp (dokumen PDF). Admin menerima laporan lengkap; akun Sales hanya menerima performa, pipeline, dan task miliknya.</p>' +
      '<div class="rp-g">' +
        '<div class="rp-box"><h4>' + ico('calendar', 15) + ' Mingguan</h4>' +
          '<label class="crm-ck"><input type="checkbox" class="rp-on" data-k="weekly"' + (c.weekly.on ? ' checked' : '') + '> Kirim laporan mingguan</label>' +
          '<div class="rp-row" style="margin-top:10px"><div><label class="fl">Hari kirim</label><select class="rp-dow">' + days.map(function (d, i) { return '<option value="' + (i + 1) + '"' + (i + 1 === c.weekly.dow ? ' selected' : '') + '>' + d + '</option>'; }).join('') + '</select></div>' +
          '<div><label class="fl">Jam</label><select class="rp-h" data-k="weekly">' + rpHours223(c.weekly.hour) + '</select></div></div>' +
          '<div class="fl">Isi laporan (7 hari sebelum hari kirim)</div>' + rpSecBox223(r, 'weekly') +
          '<div class="rp-st">' + rpPer223(r.period.weekly) + '</div></div>' +
        '<div class="rp-box"><h4>' + ico('calendar-days', 15) + ' Bulanan</h4>' +
          '<label class="crm-ck"><input type="checkbox" class="rp-on" data-k="monthly"' + (c.monthly.on ? ' checked' : '') + '> Kirim laporan bulanan</label>' +
          '<div class="rp-row" style="margin-top:10px"><div><label class="fl">Tanggal kirim</label><select class="rp-dom">' + dom + '</select></div>' +
          '<div><label class="fl">Jam</label><select class="rp-h" data-k="monthly">' + rpHours223(c.monthly.hour) + '</select></div></div>' +
          '<div class="fl">Isi laporan (bulan sebelumnya, dibandingkan bulan sebelumnya lagi)</div>' + rpSecBox223(r, 'monthly') +
          '<div class="rp-st">' + rpPer223(r.period.monthly) + '</div></div>' +
        '<div class="rp-box"><h4>' + ico('users', 15) + ' Penerima & saluran</h4>' +
          '<label class="crm-ck" style="font-weight:400"><input type="checkbox" class="rp-adm"' + (c.to_admins ? ' checked' : '') + '> Super Admin &amp; Admin (laporan lengkap)</label>' +
          '<label class="crm-ck" style="font-weight:400;margin-top:6px"><input type="checkbox" class="rp-spv"' + (c.to_spv ? ' checked' : '') + '> Supervisor (laporan lengkap)</label>' +
          '<label class="crm-ck" style="font-weight:400;margin-top:6px"><input type="checkbox" class="rp-sales"' + (c.to_sales ? ' checked' : '') + '> Akun Sales (laporan miliknya)</label>' +
          '<div class="row" style="margin-top:10px"><label class="fl">Email tambahan (laporan lengkap, maks. 10)</label><input type="text" class="rp-em" value="' + esc((c.extra_email || []).join(', ')) + '" placeholder="owner@perusahaan.com, direksi@perusahaan.com"></div>' +
          '<div class="row"><label class="fl">Nomor WhatsApp tambahan (laporan lengkap, maks. 10)</label><input type="text" class="rp-wa" value="' + esc((c.extra_wa || []).join(', ')) + '" placeholder="62812xxxx, 62813xxxx"></div>' +
          '<div class="row"><label class="fl">Kirim lewat</label><select class="rp-via"><option value="email"' + (c.via === 'email' ? ' selected' : '') + '>Email saja</option><option value="wa"' + (c.via === 'wa' ? ' selected' : '') + '>WhatsApp saja</option><option value="both"' + (c.via === 'both' ? ' selected' : '') + '>Email &amp; WhatsApp</option></select></div>' +
          (!r.wa_ready ? '<p class="crm-p crm-warn">WhatsApp belum bisa dipakai: ' + esc(r.wa_why) + ' Penerima tetap dikirimi lewat email.</p>' : '') +
          '<div class="rp-st"><b>' + rc.length + ' penerima</b> dengan pengaturan tersimpan:<br>' + (rc.length ? rc.map(function (x) {
            return '<span class="rp-pill">' + esc(x.name) + (x.own ? ' · milik sendiri' : '') + ' · ' + [x.via_email ? 'email' : '', x.via_wa ? 'WA' : ''].filter(Boolean).join(' + ') + (!x.via_email && !x.via_wa ? '<span class="rp-bad">tanpa email/WA</span>' : '') + '</span>';
          }).join('') : 'belum ada') + '</div>' +
          '<p class="help" style="margin-top:6px">Email & nomor WhatsApp anggota tim diisi di menu Pengguna / Profil Saya. WhatsApp dikirim dari nomor pengirim Notifikasi Tim (Widget &amp; API).</p></div>' +
        '<div class="rp-box"><h4>' + ico('cpu', 15) + ' Mesin PDF</h4>' +
          '<div class="rp-st" style="margin-top:0">Dipakai sekarang: <b>' + eng + '</b>' + (E.chrome && E.active !== 'chrome' ? '<br>Chromium terdeteksi: ' + esc(E.chrome_bin) : '') +
          (E.php_missing && E.php_missing.length ? '<br><span class="rp-bad">Ekstensi PHP belum aktif: ' + esc(E.php_missing.join(', ')) + '</span>' : '') + '</div>' +
          '<div class="row" style="margin-top:10px"><label class="fl">Mesin</label><select class="rp-eng"><option value="auto"' + (c.engine === 'auto' ? ' selected' : '') + '>Otomatis (Chromium bila ada di server, selain itu dompdf)</option><option value="dompdf"' + (c.engine === 'dompdf' ? ' selected' : '') + '>dompdf saja</option><option value="chrome"' + (c.engine === 'chrome' ? ' selected' : '') + '>Chromium (cadangan dompdf)</option></select></div>' +
          (sa ? '<div class="row"><label class="fl">Lokasi Chromium/Chrome (opsional, untuk VPS)</label><input type="text" class="rp-cb" value="' + esc(c.chrome_bin || '') + '" placeholder="/usr/bin/chromium"></div>' : '') +
          '<p class="help">dompdf jalan di cPanel maupun VPS (butuh ekstensi PHP dom, mbstring, gd). Di VPS Ubuntu: <code>sudo apt install php-xml php-mbstring php-gd</code>; opsional Chromium: <code>sudo apt install chromium-browser</code>.</p>' +
          (!E.dompdf ? '<button type="button" class="btn ghost sm rp-lib">' + ico('download', 14) + ' Pasang mesin PDF sekarang</button>' : '') + '</div>' +
      '</div>' +
      '<div class="rp-act"><button type="button" class="btn rp-save">' + ico('save', 15) + ' Simpan</button>' +
        '<span style="flex:1"></span>' +
        '<select class="rp-mk" style="width:auto"><option value="weekly">Mingguan terakhir</option><option value="monthly">Bulan lalu</option><option value="custom">Pilih tanggal…</option></select>' +
        '<input type="date" class="rp-f" style="width:auto;display:none"><input type="date" class="rp-t" style="width:auto;display:none">' +
        '<button type="button" class="btn ghost rp-make">' + ico('file-down', 15) + ' Buat &amp; unduh PDF</button>' +
        '<button type="button" class="btn ghost rp-test">' + ico('send', 15) + ' Kirim uji ke saya</button></div>' +
      '<h4 style="margin:22px 0 8px;font-size:14px">Arsip PDF</h4>' +
      '<div class="scroll"><table class="tbl"><thead><tr><th>Dibuat</th><th>Jenis</th><th>Periode</th><th>Untuk</th><th>Mesin</th><th style="text-align:right">Ukuran</th><th></th></tr></thead><tbody>' +
        ((r.archive || []).length ? r.archive.map(function (a) {
          var k = { weekly: 'Mingguan', monthly: 'Bulanan', custom: 'Pilih tanggal' }[a.kind] || a.kind;
          return '<tr><td>' + esc(String(a.at || '').slice(0, 16)) + '</td><td>' + esc(k) + (a.test ? ' <span class="help">(uji)</span>' : '') + '</td><td>' + esc(a.from) + ' – ' + esc(a.to) + '</td><td>' + esc(a.own ? a.for : 'Lengkap') + '</td><td>' + esc(a.engine || '') + '</td>' +
            '<td style="text-align:right">' + Math.max(1, Math.round((a.size || 0) / 1024)) + ' KB</td><td><button type="button" class="btn ghost sm rp-dl" data-id="' + esc(a.id) + '">' + ico('download', 13) + ' Unduh</button></td></tr>';
        }).join('') : '<tr><td colspan="7" class="help">Belum ada laporan PDF.</td></tr>') + '</tbody></table></div>' +
      rpLog223(r);
    box.innerHTML = h;
    var mk = box.querySelector('.rp-mk');
    mk.onchange = function () { var cu = mk.value === 'custom'; box.querySelector('.rp-f').style.display = cu ? '' : 'none'; box.querySelector('.rp-t').style.display = cu ? '' : 'none'; };
    box.querySelector('.rp-save').onclick = rpSave223;
    box.querySelector('.rp-make').onclick = function () { rpMake223(this); };
    box.querySelector('.rp-test').onclick = function () { rpTest223(this); };
    if (box.querySelector('.rp-lib')) box.querySelector('.rp-lib').onclick = function () {
      var bt = this; bt.disabled = true; bt.textContent = 'Memasang…';
      api('rpt_lib', { method: 'POST', body: {} }).then(function (x) {
        if (!x || !x.ok) { bt.disabled = false; bt.textContent = 'Coba lagi'; toast((x && x.error) || 'Gagal memasang mesin PDF.', true); return; }
        toast('Mesin PDF terpasang.'); rpS223.d = x; rpRender223();
      });
    };
    Array.prototype.forEach.call(box.querySelectorAll('.rp-dl'), function (b) { b.onclick = function () { rpDownload223(b.dataset.id, b); }; });
  }
  function rpLog223(r) {
    var L = [];
    ['monthly', 'weekly'].forEach(function (k) { (r.period[k].log || []).forEach(function (x) { L.push([k, x]); }); });
    if (!L.length) return '';
    return '<h4 style="margin:18px 0 8px;font-size:14px">Riwayat kirim periode terakhir</h4><div class="scroll"><table class="tbl"><thead><tr><th>Waktu</th><th>Jenis</th><th>Penerima</th><th>Lewat</th><th>Status</th></tr></thead><tbody>' +
      L.slice(0, 30).map(function (p) { var x = p[1];
        return '<tr><td>' + esc(x.at) + '</td><td>' + (p[0] === 'monthly' ? 'Bulanan' : 'Mingguan') + '</td><td>' + esc(x.name) + ' <span class="help">' + esc(x.to) + '</span></td><td>' + (x.ch === 'wa' ? 'WhatsApp' : 'Email') + '</td><td>' + (x.ok ? '<span class="rp-ok">terkirim</span>' : '<span class="rp-bad">gagal</span> <span class="help">' + esc(x.err || '') + '</span>') + '</td></tr>';
      }).join('') + '</tbody></table></div>';
  }
  function rpCollect223() {
    var box = $('#rpCard'), q = function (s) { return box.querySelector(s); };
    var secs = function (k) { return Array.prototype.filter.call(box.querySelectorAll('.rp-sec[data-k="' + k + '"]'), function (x) { return x.checked; }).map(function (x) { return x.value; }); };
    var b = {
      weekly: { on: q('.rp-on[data-k="weekly"]').checked ? 1 : 0, dow: +q('.rp-dow').value, hour: +q('.rp-h[data-k="weekly"]').value, sections: secs('weekly') },
      monthly: { on: q('.rp-on[data-k="monthly"]').checked ? 1 : 0, dom: +q('.rp-dom').value, hour: +q('.rp-h[data-k="monthly"]').value, sections: secs('monthly') },
      to_admins: q('.rp-adm').checked ? 1 : 0, to_spv: q('.rp-spv').checked ? 1 : 0, to_sales: q('.rp-sales').checked ? 1 : 0,
      extra_email: q('.rp-em').value, extra_wa: q('.rp-wa').value, via: q('.rp-via').value, engine: q('.rp-eng').value
    };
    if (q('.rp-cb')) b.chrome_bin = q('.rp-cb').value;
    return b;
  }
  function rpSave223() {
    var bt = $('#rpCard .rp-save'); bt.disabled = true;
    return api('rpt_save', { method: 'POST', body: rpCollect223() }).then(function (x) {
      bt.disabled = false;
      if (!x || !x.ok) { toast((x && x.error) || 'Gagal menyimpan.', true); return false; }
      toast('Pengaturan Laporan Berkala disimpan.'); rpS223.d = x; rpRender223(); return true;
    });
  }
  function rpDownload223(id, bt) {
    if (bt) bt.disabled = true;
    fetch(API + '?action=rpt_file&id=' + encodeURIComponent(id) + '&_=' + Date.now(), { headers: { 'X-Auth-Token': token }, cache: 'no-store' }).then(function (res) {
      if (!res.ok) return res.json().then(function (j) { throw new Error((j && j.error) || ('HTTP ' + res.status)); }, function () { throw new Error('HTTP ' + res.status); });
      var cd = res.headers.get('Content-Disposition') || '', m = /filename="([^"]+)"/.exec(cd);
      return res.blob().then(function (b) {
        var a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = m ? m[1] : 'laporan.pdf';
        document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
      });
    }).catch(function (e) { toast(e.message || 'Gagal mengunduh.', true); }).then(function () { if (bt) bt.disabled = false; });
  }
  function rpMake223(bt) {
    var box = $('#rpCard'), k = box.querySelector('.rp-mk').value, body = { kind: k };
    if (k === 'custom') {
      body.from = box.querySelector('.rp-f').value; body.to = box.querySelector('.rp-t').value;
      if (!body.from || !body.to) { toast('Isi tanggal dari & sampai.', true); return; }
    } else body.sections = Array.prototype.filter.call(box.querySelectorAll('.rp-sec[data-k="' + k + '"]'), function (x) { return x.checked; }).map(function (x) { return x.value; });
    var t0 = bt.innerHTML; bt.disabled = true; bt.innerHTML = 'Membuat PDF…';
    api('rpt_make', { method: 'POST', body: body }).then(function (x) {
      bt.disabled = false; bt.innerHTML = t0;
      if (!x || !x.ok) { toast((x && x.error) || 'Gagal membuat PDF.', true); return; }
      if (x.warn) toast(x.warn, true);
      rpDownload223(x.id); api('rpt_get').then(function (r) { if (r && r.ok) { rpS223.d = r; rpRender223(); } });
    });
  }
  function rpTest223(bt) {
    var k = $('#rpCard .rp-mk').value === 'monthly' ? 'monthly' : 'weekly';
    var t0 = bt.innerHTML; bt.disabled = true; bt.innerHTML = 'Mengirim…';
    api('rpt_test', { method: 'POST', body: { kind: k } }).then(function (x) {
      bt.disabled = false; bt.innerHTML = t0;
      if (!x || (!x.ok && !x.email && !x.wa)) { toast((x && x.error) || 'Gagal mengirim laporan uji.', true); return; }
      var m = [];
      if (x.email) m.push(x.email.ok ? 'email ke ' + x.email.to + (x.email.attached ? ' (lampiran PDF)' : ' (tautan unduh)') : 'email gagal: ' + x.email.error);
      if (x.wa) m.push(x.wa.ok ? 'WhatsApp ke ' + x.wa.to + (x.wa.via === 'link' ? ' (tautan unduh)' : ' (dokumen PDF)') : 'WhatsApp gagal: ' + x.wa.error);
      toast('Laporan ' + (k === 'monthly' ? 'bulanan' : 'mingguan') + ' uji: ' + m.join(' · '), !x.ok);
      api('rpt_get').then(function (r) { if (r && r.ok) { rpS223.d = r; rpRender223(); } });
    });
  }

