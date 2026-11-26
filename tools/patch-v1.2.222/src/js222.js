

  /* ====================================================================== *
   *  v1.2.222: notif-wa — notifikasi tim via WhatsApp (Widget & API + Profil Saya)
   * ====================================================================== */
  var NTF_MODE222 = { email: 'Email saja', wa: 'WhatsApp saja', both: 'Email + WhatsApp', off: 'Mati' };
  var NTF_ROLE222 = { super_admin: 'Super Admin', admin: 'Admin', supervisor: 'Supervisor', wa_agent: 'Agent', sales: 'Sales' };
  var ntfData222 = null;
  function ntfLoad222() {
    var card = $('#ntfCard'); if (!card) return;
    if (!(user.role === 'super_admin' || user.role === 'admin')) { card.style.display = 'none'; return; }
    api('ntf_get').then(function (r) {
      var box = $('#ntfBody'); if (!box) return;
      if (!r || !r.ok) { box.innerHTML = '<div class="help">' + esc((r && r.error) || 'Gagal memuat.') + '</div>'; return; }
      ntfData222 = r; ntfPaint222();
    });
  }
  function ntfPaint222() {
    var r = ntfData222, box = $('#ntfBody'); if (!r || !box) return;
    var chs = r.channels || [];
    var chOpt = chs.length ? chs.map(function (c) {
      return '<option value="' + esc(c.id) + '"' + (c.id === r.ch ? ' selected' : '') + (c.ok ? '' : ' disabled') + '>' + esc(c.label) + (c.number && String(c.label).indexOf(c.number) === -1 ? ' — +' + esc(c.number) : '') + (c.ok ? '' : ' (tidak bisa dipakai)') + '</option>';
    }).join('') : '<option value="">Belum ada nomor WhatsApp</option>';
    var why = chs.filter(function (c) { return !c.ok; }).map(function (c) { return '<li><b>' + esc(c.label) + '</b>: ' + esc(c.why) + '</li>'; }).join('');
    var kinds = (r.kinds || []).map(function (k) {
      return '<tr><td>' + esc(k.label) + '</td><td><select class="ntf-k" data-k="' + esc(k.id) + '" style="width:auto">' + k.opts.map(function (o) { return '<option value="' + o + '"' + (o === k.val ? ' selected' : '') + '>' + NTF_MODE222[o] + '</option>'; }).join('') + '</select></td></tr>';
    }).join('');
    var us = (r.users || []).map(function (u) {
      var lock = user.role === 'admin' && u.role === 'super_admin' && u.username !== user.username;
      return '<tr><td><b>' + esc(u.name) + '</b><div class="help">' + esc(NTF_ROLE222[u.role] || u.role) + (u.email ? '' : ' · tanpa email') + '</div></td>' +
        '<td><input type="text" inputmode="tel" class="ntf-u" data-u="' + esc(u.username) + '" value="' + esc(u.wa ? '0' + u.wa.slice(2) : '') + '" placeholder="08xxxxxxxxxx" style="width:170px"' + (lock ? ' disabled' : '') + '></td>' +
        '<td>' + (u.wa ? '<button type="button" class="btn ghost sm ntf-t" data-u="' + esc(u.username) + '">' + ico('send', 13) + ' Uji</button>' : '') + '</td></tr>';
    }).join('');
    var log = (r.log || []).slice(0, 15).map(function (x) {
      var kl = ((r.kinds || []).filter(function (k) { return k.id === x.kind; })[0] || {}).label || (x.kind === 'test' ? 'Uji' : x.kind);
      return '<tr><td style="white-space:nowrap">' + esc(crmFmtD215(x.at) + ' ' + String(x.at).slice(11, 16)) + '</td><td>' + esc(kl) + '</td><td>' + esc(x.name || '') + ' <span class="help">+' + esc(x.to) + '</span></td><td>' +
        (x.ok ? '<span style="color:#166534">terkirim</span>' : '<span style="color:#b91c1c" title="' + esc(x.err || '') + '">gagal</span>' + (x.err ? '<div class="help">' + esc(x.err) + '</div>' : '')) + '</td></tr>';
    }).join('');
    box.innerHTML =
      '<div class="toggle-row"><div><div class="tt">Kirim notifikasi tim lewat WhatsApp</div><div class="td">Pengingat jatuh tempo, laporan mingguan, task baru, lead untuk Sales, dan chat yang diserahkan dikirim ke nomor WhatsApp anggota tim, dari salah satu nomor bisnis di atas.</div></div>' +
        '<label class="switch"><input type="checkbox" id="ntfOn"' + (r.on ? ' checked' : '') + '><span class="sl"></span></label></div>' +
      '<div class="row" style="margin-top:10px"><label class="fl">Nomor pengirim</label><select id="ntfCh">' + chOpt + '</select>' +
        (why ? '<ul class="help" style="margin:6px 0 0 16px;padding:0">' + why + '</ul>' : '') + '</div>' +
      (r.on && !r.sender_ok ? '<p class="crm-p crm-warn" style="margin-top:8px">' + esc(r.sender_err) + '</p>' : '') +
      '<h4 class="ntf-h">Jenis notifikasi</h4><div class="scroll"><table class="tbl ntf-t"><tbody>' + kinds + '</tbody></table></div>' +
      '<p class="help">WhatsApp saja: anggota tim tanpa nomor WhatsApp tetap menerima email. Email lupa password &amp; keamanan akun tetap lewat email.</p>' +
      '<h4 class="ntf-h">Nomor WhatsApp tim</h4><p class="help" style="margin-top:0">Nomor penerima notifikasi. Setiap anggota juga bisa mengisi sendiri di <b>Profil Saya</b>. Pesan dari nomor ini ke nomor bisnis tidak dijawab bot.</p>' +
      '<div class="scroll"><table class="tbl ntf-t"><tbody>' + (us || '<tr><td class="help">Belum ada pengguna.</td></tr>') + '</tbody></table></div>' +
      '<div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap"><button type="button" class="btn" id="ntfSave">Simpan</button><button type="button" class="btn ghost" id="ntfReload">Muat ulang</button></div>' +
      (log ? '<h4 class="ntf-h">Riwayat terakhir</h4><div class="scroll"><table class="tbl ntf-t"><tbody>' + log + '</tbody></table></div>' : '') +
      (r.updated_at ? '<p class="help" style="margin-top:8px">Diubah ' + esc(r.updated_at) + (r.updated_by ? ' oleh ' + esc(r.updated_by) : '') + '.</p>' : '');
    $('#ntfReload').onclick = ntfLoad222;
    $('#ntfSave').onclick = function () {
      var b = this, kinds = {}, users = {};
      Array.prototype.slice.call(box.querySelectorAll('.ntf-k')).forEach(function (s) { kinds[s.getAttribute('data-k')] = s.value; });
      Array.prototype.slice.call(box.querySelectorAll('.ntf-u')).forEach(function (i) { if (!i.disabled) users[i.getAttribute('data-u')] = i.value.trim(); });
      b.disabled = true;
      api('ntf_save', { method: 'POST', body: { on: $('#ntfOn').checked ? 1 : 0, ch: $('#ntfCh').value, kinds: kinds, users: users } }).then(function (x) {
        b.disabled = false;
        if (!x || !x.ok) { toast((x && x.error) || 'Gagal menyimpan.', true); return; }
        ntfData222 = x; ntfPaint222(); toast('Notifikasi WhatsApp disimpan.');
      });
    };
    Array.prototype.slice.call(box.querySelectorAll('.ntf-t')).forEach(function (bt) {
      bt.onclick = function () {
        bt.disabled = true;
        api('ntf_test', { method: 'POST', body: { username: bt.getAttribute('data-u') } }).then(function (x) {
          bt.disabled = false;
          if (!x || !x.ok) { toast((x && x.error) || 'Gagal mengirim uji.', true); return; }
          toast('Pesan uji terkirim ke +' + x.to + '.'); ntfLoad222();
        });
      };
    });
  }
  function ntfProfile222() {
    var card = $('#ntfMeCard'); if (!card) return;
    api('ntf_me').then(function (r) {
      if (!r || !r.ok) { card.style.display = 'none'; return; }
      card.style.display = '';
      $('#ntfMeWa').value = r.wa ? '0' + r.wa.slice(2) : '';
      $('#ntfMeNote').innerHTML = r.active
        ? 'Notifikasi aktif dari ' + esc(r.sender) + (r.kinds && r.kinds.length ? ': ' + r.kinds.map(esc).join(', ') + '.' : '.')
        : 'Notifikasi WhatsApp belum diaktifkan Admin. Nomor Anda tetap disimpan.';
      $('#ntfMeSave').onclick = function () {
        var b = this; b.disabled = true;
        api('update_own_wa', { method: 'POST', body: { wa: $('#ntfMeWa').value.trim() } }).then(function (x) {
          b.disabled = false;
          if (!x || !x.ok) { toast((x && x.error) || 'Gagal menyimpan.', true); return; }
          $('#ntfMeWa').value = x.wa ? '0' + x.wa.slice(2) : ''; toast(x.wa ? 'Nomor WhatsApp disimpan.' : 'Nomor WhatsApp dihapus.');
        });
      };
      $('#ntfMeTest').onclick = function () {
        var b = this; b.disabled = true;
        api('ntf_test', { method: 'POST', body: {} }).then(function (x) {
          b.disabled = false;
          if (!x || !x.ok) { toast((x && x.error) || 'Gagal mengirim uji.', true); return; }
          toast('Pesan uji terkirim ke +' + x.to + '.');
        });
      };
    });
  }
