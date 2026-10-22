  /* v1.2.104: skor-risiko-wa — lencana & panel Kesehatan nomor (WAHA) */
  var WH_LV = { aman: ['Aman', '#dcfce7', '#166534'], waspada: ['Waspada', '#fef3c7', '#92400e'], bahaya: ['Bahaya', '#fee2e2', '#991b1b'] };
  function whBadge(h, id) {
    if (!h) return '<button class="btn ghost sm" type="button" data-wn="health" data-id="' + esc(id) + '" title="Belum ada skor — dihitung tiap 15 menit">Cek</button>';
    var lv = WH_LV[h.level] || WH_LV.aman;
    return '<button type="button" data-wn="health" data-id="' + esc(id) + '" title="' + esc((h.top || []).join('\n') || 'Tidak ada faktor risiko') + '" style="border:0;cursor:pointer;border-radius:999px;padding:3px 10px;font:600 12px/1.4 inherit;background:' + lv[1] + ';color:' + lv[2] + '">' +
      h.score + ' · ' + lv[0] + (h.partial ? '*' : '') + '</button>';
  }
  function whOpen(row) {
    var box = $('#wn_health'); if (!box || !row) return;
    box.classList.remove('hide');
    box.innerHTML = '<div class="help">Menghitung skor…</div>';
    api('wa_health', { query: '&ch=' + encodeURIComponent(row.id) }).then(function (r) {
      if (!r || !r.ok) { box.innerHTML = '<div class="help">' + esc((r && r.error) || 'Gagal memuat.') + '</div>'; return; }
      var h = r.health, m = h.m || {}, lv = WH_LV[h.level] || WH_LV.aman;
      var pct = function (v) { return v == null ? '—' : v + '%'; };
      var max = 1; (h.series || []).forEach(function (d) { max = Math.max(max, d.in, d.out); });
      var bars = (h.series || []).map(function (d) {
        var hi = Math.round(d.in / max * 60), ho = Math.round(d.out / max * 60), hn = Math.round(d['new'] / max * 60);
        return '<div style="flex:1;text-align:center;min-width:0"><div style="height:62px;display:flex;align-items:flex-end;justify-content:center;gap:2px">' +
          '<span title="Masuk ' + d.in + '" style="width:9px;height:' + hi + 'px;background:#93c5fd;border-radius:2px 2px 0 0"></span>' +
          '<span title="Keluar ' + d.out + ' (chat duluan ' + d['new'] + ')" style="width:9px;height:' + ho + 'px;background:linear-gradient(to top,#f97316 ' + (ho ? Math.round(hn / ho * 100) : 0) + '%,#a5b4fc 0);border-radius:2px 2px 0 0"></span></div>' +
          '<div class="help" style="margin:2px 0 0;font-size:10.5px">' + esc(d.d.slice(8)) + '/' + esc(d.d.slice(5, 7)) + '</div></div>';
      }).join('');
      var stat = function (k, v) { return '<div style="padding:8px 10px;border:1px solid var(--line);border-radius:8px"><div class="help" style="margin:0;font-size:11px">' + k + '</div><b>' + v + '</b></div>'; };
      var since = h.since ? new Date((h.since + 7 * 3600) * 1000).toISOString().slice(0, 10) : '';
      var evs = (h.events || []).slice(0, 6).map(function (e) {
        var t = new Date((e[0] + 7 * 3600) * 1000).toISOString().replace('T', ' ').slice(5, 16);
        return '<li>' + esc(t) + ' — ' + esc(e[1]) + (e[2] ? ' <b style="color:#b91c1c">(' + esc({ logout: 'logout paksa', failed: 'gagal', drop: 'putus' }[e[2]] || e[2]) + ')</b>' : '') + '</li>';
      }).join('');
      box.innerHTML =
        '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:10px">' +
          '<div style="font-size:30px;font-weight:700;color:' + lv[2] + '">' + h.score + '<span style="font-size:14px;color:var(--muted)">/100</span></div>' +
          '<div><b>' + esc(r.label) + '</b>' + (m.number && String(r.label).indexOf(m.number) < 0 ? ' <span class="mono">+' + esc(m.number) + '</span>' : '') + '<br><span class="tag" style="background:' + lv[1] + ';color:' + lv[2] + '">' + lv[0] + '</span>' +
          (m.status ? ' <span class="help" style="margin:0">Sesi: ' + esc(m.status) + '</span>' : '') + '</div>' +
          '<button class="btn ghost sm" type="button" id="wh_close" style="margin-left:auto">Tutup</button></div>' +
        (h.partial ? '<div class="help" style="color:#92400e">* Data belum 24 jam — skor masih bisa berubah.</div>' : '') +
        (!h.cfg_ok ? '<div class="help" style="background:#fef3c7;color:#92400e;padding:8px 10px;border-radius:8px">Status centang (terkirim/dibaca) belum dipantau untuk sesi ini. Dipasang otomatis jam 01–04 WIB, atau ' +
          (r.can_edit ? '<a href="#" id="wh_cfg">pasang sekarang</a> (sesi WAHA restart beberapa detik).' : 'minta Admin memasangnya.') + '</div>' : '') +
        '<h4 style="margin:12px 0 6px">Faktor risiko</h4>' +
        (h.factors.length ? '<ul style="margin:0;padding-left:18px">' + h.factors.map(function (f) { return '<li><b>+' + f.p + '</b> ' + esc(f.t) + '</li>'; }).join('') + '</ul>'
          : '<div class="help">Tidak ada faktor risiko terdeteksi. Pola penggunaan wajar (membalas chat masuk).</div>') +
        '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px;margin-top:12px">' +
          stat('Masuk 24 jam', m.in) + stat('Keluar 24 jam', m.out + ' <span class="help" style="margin:0;font-weight:400">bot ' + m.out_bot + ' · agent ' + m.out_agent + ' · HP ' + m.out_hp + '</span>') +
          stat('Chat duluan 24 jam', m.out_new) + stat('Dibalas (chat duluan 7h)', pct(m.reply_pct)) +
          stat('Centang 1 > 6 jam', m.ack_on ? pct(m.stuck_pct) : '—') + stat('Dibaca', m.ack_on ? pct(m.read_pct) : '—') +
          stat('Gagal kirim 24 jam', m.fail) + stat('Umur nomor', m.age_days == null ? 'tidak diketahui' : m.age_days + ' hari') +
        '</div>' +
        '<h4 style="margin:14px 0 4px">7 hari terakhir</h4><div class="help" style="margin:0 0 4px"><span style="color:#3b82f6">■</span> masuk &nbsp; <span style="color:#818cf8">■</span> keluar &nbsp; <span style="color:#f97316">■</span> chat duluan</div>' +
        '<div style="display:flex;gap:4px;padding:6px 0;border-bottom:1px solid var(--line)">' + bars + '</div>' +
        (evs ? '<h4 style="margin:14px 0 4px">Riwayat sesi</h4><ul style="margin:0;padding-left:18px;font-size:12.5px">' + evs + '</ul>' : '') +
        (r.can_edit ? '<div class="row" style="margin-top:12px"><label class="fl">Nomor mulai dipakai sejak</label><div style="display:flex;gap:8px;flex-wrap:wrap"><input type="date" id="wh_since" value="' + esc(since) + '" style="max-width:180px"><button class="btn ghost sm" type="button" id="wh_since_save">Simpan</button></div>' +
          '<div class="help">Untuk menghitung umur nomor. Terisi otomatis saat nomor baru di-scan; nomor yang terhubung sebelum pemantauan perlu diisi manual.</div></div>' : '') +
        '<div class="help" style="margin-top:10px">Skor ini perkiraan dari pola penggunaan, bukan data resmi WhatsApp — laporan/report pengguna tidak terbaca. Tips aman: hindari chat duluan massal dari HP, jangan kirim teks sama ke banyak nomor, naikkan volume nomor baru bertahap.</div>';
      $('#wh_close').onclick = function () { box.classList.add('hide'); };
      var cf = $('#wh_cfg');
      if (cf) cf.onclick = function (e) {
        e.preventDefault();
        if (!confirm('Pasang ulang webhook sesi ini? Sesi WAHA restart beberapa detik (pesan masuk saat itu tetap diterima setelah tersambung).')) return;
        api('wa_health', { method: 'POST', body: { op: 'apply_cfg', ch: row.id } }).then(function (x) { if (x && x.ok) { toast('Pemantauan centang aktif.'); whOpen(row); } else toast((x && x.error) || 'Gagal.', true); });
      };
      var sv = $('#wh_since_save');
      if (sv) sv.onclick = function () {
        api('wa_health', { method: 'POST', body: { op: 'set_since', ch: row.id, date: $('#wh_since').value } }).then(function (x) { if (x && x.ok) { toast('Tersimpan.'); whOpen(row); wnLoad(); } else toast((x && x.error) || 'Gagal.', true); });
      };
    });
  }
