  /* ---- v1.2.224: kontak-manual -- tambah satu kontak dari menu Kontak ---- */
  function contactAddOpen() {
    var card = $('#kontakAddCard'); if (!card) return;
    if (card.style.display !== 'none') { card.style.display = 'none'; return; }
    var imp = $('#kontakImportCard'); if (imp) imp.style.display = 'none';
    card.innerHTML =
      '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">' +
        '<h3 style="margin:0">Tambah Kontak</h3>' +
        '<button type="button" class="btn ghost sm" id="caClose" title="Tutup">' + ico('x', 14) + '</button></div>' +
      '<p style="color:var(--muted);font-size:13px;margin:6px 0 10px;line-height:1.5">Nomor otomatis dirapikan ke format WhatsApp (mis. <span class="mono">0812…</span> → <span class="mono">62812…</span>). Saat nomor ini chat nanti, kontaknya langsung menyatu.</p>' +
      '<div class="grid2">' +
        '<div class="row"><label class="fl">Nomor WhatsApp *</label><input type="text" inputmode="tel" id="caNum" placeholder="0812xxxxxxx" autocomplete="off"></div>' +
        '<div class="row"><label class="fl">Nama *</label><input type="text" id="caName" maxlength="100" placeholder="Nama kontak"></div>' +
      '</div>' +
      '<div class="grid2" style="margin-top:8px">' +
        '<div class="row"><label class="fl">Lead Rating</label><select id="caStage">' + contactStageOptionsHtml('new') + '</select></div>' +
        '<div class="row" id="caDobRow" style="display:none"><label class="fl">Tanggal Lahir</label><input type="date" id="caDob"></div>' +
      '</div>' +
      '<label id="caVipRow" style="display:none;gap:6px;align-items:center;font-size:13px;margin-top:8px"><input type="checkbox" id="caVip"> Tandai sebagai VIP</label>' +
      '<div style="display:flex;gap:8px;align-items:center;margin-top:12px;flex-wrap:wrap">' +
        '<button class="btn" id="caSave">Simpan Kontak</button>' +
        '<label style="display:flex;gap:6px;align-items:center;font-size:13px"><input type="checkbox" id="caMore"> Tambah lagi setelah simpan</label>' +
        '<span id="caMsg" style="font-size:13px"></span></div>';
    card.style.display = '';
    var st = $('#caStage');
    function syncStage() {
      var ac = st.value === 'active_customer';
      $('#caVipRow').style.display = ac ? 'flex' : 'none';
      $('#caDobRow').style.display = ac ? '' : 'none';
    }
    st.onchange = syncStage;
    $('#caClose').onclick = function () { card.style.display = 'none'; };
    $('#caNum').focus();
    ['#caNum', '#caName'].forEach(function (s) { $(s).onkeydown = function (e) { if (e.key === 'Enter') { e.preventDefault(); contactAddSave(); } }; });
    $('#caSave').onclick = contactAddSave;
  }
  function contactAddFocus(num) {
    contactOpenState[num] = true;
    if (contactFilter !== 'all') {
      contactFilter = 'all';
      $$('.contact-filter').forEach(function (x) { x.classList.toggle('active', x.dataset.contactStage === 'all'); });
    }
    api('get_contacts').then(function (res) {
      if (res && res.ok) { contactData = res.contacts || []; renderContacts(); }
      var el = document.querySelector('#contactList .card[data-contact="' + num + '"]');
      if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); el.style.outline = '2px solid var(--accent, #2563eb)'; setTimeout(function () { el.style.outline = ''; }, 2500); }
    });
  }
  function contactAddSave() {
    var btn = $('#caSave'), msg = $('#caMsg');
    var body = { number: $('#caNum').value.trim(), name: $('#caName').value.trim(), stage: $('#caStage').value,
                 vip: $('#caVip').checked, cust_dob: $('#caDob').value };
    if (!body.number) { msg.innerHTML = '<span style="color:#b91c1c">Isi nomor WhatsApp.</span>'; $('#caNum').focus(); return; }
    if (!body.name) { msg.innerHTML = '<span style="color:#b91c1c">Isi nama kontak.</span>'; $('#caName').focus(); return; }
    btn.disabled = true; msg.textContent = 'Menyimpan…';
    api('add_contact', { method: 'POST', body: body }).then(function (r) {
      btn.disabled = false;
      if (r && r.ok) {
        toast('Kontak ' + (r.name || ('+' + r.number)) + ' ditambahkan.');
        if ($('#caMore').checked) {
          $('#caNum').value = ''; $('#caName').value = ''; $('#caDob').value = ''; $('#caVip').checked = false;
          msg.innerHTML = '<span style="color:#065f46">' + esc(r.name) + ' (+' + esc(r.number) + ') tersimpan.</span>';
          $('#caNum').focus(); fetchContacts();
        } else {
          $('#kontakAddCard').style.display = 'none';
          contactAddFocus(r.number);
        }
        return;
      }
      msg.innerHTML = '<span style="color:#b91c1c">' + esc((r && r.error) || 'Gagal menyimpan.') + '</span>' +
        (r && r.exists ? ' <button type="button" class="btn ghost sm" id="caGo">Buka kontak</button>' : '');
      var g = $('#caGo'); if (g) g.onclick = function () { $('#kontakAddCard').style.display = 'none'; contactAddFocus(r.number); };
    }).catch(function (e) { btn.disabled = false; msg.innerHTML = '<span style="color:#b91c1c">' + esc(e.message || String(e)) + '</span>'; });
  }
