  /* v1.2.105: riwayat-wa-waha — riwayat chat sebelum nomor terhubung (ditarik dari WAHA seperti WhatsApp Web) */
  var _ws = { t: null, ch: '' };
  function wsBody(x) { x.op = 'history'; x.ch = _fonc.ch || 'utama'; return x; }
  function wsFmtTime(sec) { if (!sec) return ''; var d = new Date((sec + 7 * 3600) * 1000).toISOString(); return d.slice(8, 10) + '/' + d.slice(5, 7) + ' ' + d.slice(11, 16); }
  function wsShow(on) {
    var box = $('#fonc_hist'); if (!box) return;
    if (!on || _fonc.action !== 'waha_conn') { box.classList.add('hide'); clearTimeout(_ws.t); return; }
    box.classList.remove('hide');
    if (_ws.ch !== (_fonc.ch || 'utama') || !box.dataset.loaded) { _ws.ch = _fonc.ch || 'utama'; box.dataset.loaded = '1'; wsLoad('get'); }
  }
  function wsLoad(what, extra) {
    clearTimeout(_ws.t);
    return api('waha_conn', { method: 'POST', body: wsBody(Object.assign({ do: what }, extra || {})) }).then(function (r) {
      if (!r || !r.ok) { wsRender(null, null, (r && r.error) || 'Gagal membaca status riwayat.'); return; }
      wsRender(r.history, r.stored);
      var h = r.history;
      if (h && (h.st === 'running' || (h.st === 'pending' && h.due - Date.now() / 1000 < 120))) {
        _ws.t = setTimeout(function () { if (!$('#fonc_hist').classList.contains('hide')) wsLoad('run'); }, h.st === 'running' ? 4000 : 15000);
      }
    }).catch(function () { wsRender(null, null, 'Koneksi bermasalah.'); });
  }
  function wsRender(h, stored, err) {
    var box = $('#fonc_hist'); if (!box) return;
    var st = stored || { nums: 0, msgs: 0 };
    var btn = function (label, cls) { return '<button class="btn ' + (cls || 'ghost') + ' sm" type="button" id="ws_go">' + label + '</button>'; };
    var line = '', act = '', note = '';
    if (err) { line = esc(err); act = btn('Coba lagi'); }
    else if (!h) {
      line = st.msgs ? 'Tersimpan <b>' + st.msgs + '</b> pesan dari <b>' + st.nums + '</b> kontak.' : 'Riwayat chat sebelum terhubung belum ditarik.';
      act = btn(st.msgs ? 'Tarik ulang' : 'Tarik riwayat chat', st.msgs ? 'ghost' : '');
    } else if (h.st === 'pending') {
      line = 'Menunggu riwayat dikirim HP ke WhatsApp… penarikan mulai ' + (h.due > Date.now() / 1000 ? 'sekitar ' + wsFmtTime(h.due) : 'sebentar lagi') + '.';
    } else if (h.st === 'running') {
      line = (h.phase === 'chats' ? 'Membaca daftar chat…' : 'Menarik riwayat: ' + h.done_chats + ' / ' + h.chats + ' chat') + ' · <b>' + h.msgs + '</b> pesan baru' + (h.passes > 1 ? ' <span class="help" style="margin:0">(putaran ' + h.pass + '/' + h.passes + ')</span>' : '');
      line += '<div style="height:6px;background:var(--line);border-radius:6px;margin-top:6px;overflow:hidden"><div style="height:100%;width:' + h.pct + '%;background:var(--brand);transition:width .4s"></div></div>';
    } else if (h.st === 'error') {
      line = '<span style="color:#b91c1c">' + ico('triangle-alert', 13) + ' ' + esc(h.err || 'Penarikan riwayat gagal.') + '</span>';
      act = btn('Coba lagi');
      note = 'Bila WAHA meminta store diaktifkan: Super Admin klik <b>Pasang webhook otomatis</b>, lalu Putuskan dan scan ulang supaya HP mengirim riwayat.';
    } else {
      line = ico('check-circle-2', 13) + ' Tersimpan <b>' + st.msgs + '</b> pesan dari <b>' + st.nums + '</b> kontak' + (h.finished ? ' · ditarik ' + esc(wsFmtTime(h.finished)) : '') + '.';
      if (h.pass < h.passes) line += ' <span class="help" style="margin:0">Pengecekan lanjutan otomatis ' + esc(wsFmtTime(h.due)) + ' (riwayat dari HP bisa datang bertahap).</span>';
      act = btn('Tarik ulang');
    }
    box.innerHTML = '<div style="display:flex;gap:10px;align-items:flex-start;justify-content:space-between;flex-wrap:wrap">' +
        '<div style="flex:1;min-width:220px"><b style="font-size:13px">' + ico('clock-3', 14) + ' Riwayat chat WhatsApp</b><div style="font-size:13px;margin-top:4px">' + line + '</div></div>' + act + '</div>' +
      '<div class="help" style="margin-top:6px">' + (note || 'Seperti WhatsApp Web: HP mengirim riwayat chat saat nomor ditautkan (biasanya beberapa bulan terakhir, tergantung HP). Riwayat tampil di Percakapan WA di atas pesan baru, hanya untuk dibaca — tidak dikirim ulang, tidak memakai kuota, tidak masuk laporan. Nomor yang sudah lama tersambung hanya punya riwayat sejak ditautkan; untuk riwayat lebih lama, Putuskan lalu scan ulang (bot berhenti selama belum tersambung).') + '</div>';
    var g = $('#ws_go');
    if (g) g.onclick = function () { g.disabled = true; wsLoad('start'); };
  }
  function wsStartScan() { wsLoad('start', { reason: 'scan' }); }
  // Riwayat di atas pesan live pada thread
  function wiThreadHtml(res) {
    var im = res.history;
    if (!im || !im.msgs || !im.msgs.length) return '';
    var more = im.total > im.msgs.length;
    var h = '<div style="display:flex;justify-content:center;margin:8px 0 4px"><span style="background:#fef3c7;color:#92400e;font-size:12px;padding:5px 12px;border-radius:12px;text-align:center">' +
      ico('clock-3', 12) + ' Riwayat dari WhatsApp sebelum terhubung · ' + im.total + ' pesan' +
      (more ? ' · <a href="#" id="wiShowAll">tampilkan ' + (im.total > 5000 ? '5.000 terakhir' : 'semua') + '</a> (kini ' + im.msgs.length + ' terakhir)' : '') + '</span></div>';
    var last = '';
    im.msgs.forEach(function (m) {
      var dk = waDateKey(m.ts);
      if (dk && dk !== last) { h += waDateSepHtml(waDateLabel(dk)); last = dk; }
      var st = m.d === 'in' ? 'align-self:flex-start;background:#fff;border:1px dashed var(--line);color:var(--ink)'
        : 'align-self:flex-end;background:#f1f5f9;border:1px dashed #cbd5e1;color:#334155';
      h += '<div style="max-width:78%;' + st + ';padding:8px 12px;border-radius:12px;margin:4px 0;white-space:pre-wrap;font-size:14px;line-height:1.45">' + esc(m.t) +
        '<div style="font-size:10px;opacity:.65;margin-top:4px">' + esc((m.ts || '').slice(11, 16)) + (m.d === 'in' ? '' : ' · bisnis') + ' · riwayat</div></div>';
    });
    h += '<div style="display:flex;align-items:center;gap:8px;margin:12px 0 4px;color:var(--muted);font-size:11px"><span style="flex:1;border-top:1px dashed var(--line)"></span>akhir riwayat · pesan di bawah tercatat dashboard<span style="flex:1;border-top:1px dashed var(--line)"></span></div>';
    return h;
  }
  function wiThreadBind(res) {
    var a = document.getElementById('wiShowAll');
    if (a) a.onclick = function (ev) { ev.preventDefault(); waState.wiAll = waState.wiAll || {}; waState.wiAll[res.number] = true; fetchWaThread(res.number); };
  }

