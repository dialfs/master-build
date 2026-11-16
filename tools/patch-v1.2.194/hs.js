
  /* ====================================================================== *
   *  v1.2.194: asisten-bantuan — Asisten Bantuan di dalam Pusat Bantuan.
   *  Pertanyaan dikirim ke tenant Support (alamat dari pusat lewat
   *  support_info) beserta konteks: bisnis, peran, paket, versi, menu aktif.
   *  Di bawah jawaban: "Tunjukkan di layar" (artikel Pusat Bantuan yang cocok)
   *  dan "Buka menu …" (menu yang disebut jawaban).
   * ====================================================================== */
  var HS = { info: null, at: 0, conv: '', busy: false, msgs: [], wa: null, waAsked: false };
  var HS_MENUS = { reports: 'Laporan & Log', wachat: 'Percakapan WA', webchat: 'Percakapan Web', blast: 'Blast WA', leads: 'Leads', kontak: 'Kontak',
    topik: 'Topik & Divisi', gc: 'Customer Feedback', tim: 'Tim & Agent', kb: 'Knowledge Base', content: 'Balasan & Tampilan', test: 'Tes Chatbot',
    widget: 'Widget & API', eskalasi: 'Respon & Eskalasi', users: 'Pengguna', profile: 'Profil Saya', install: 'Pemasangan (GTM)', pembaruan: 'Pembaruan' };
  function hsLoad(cb) {
    if (HS.info && Date.now() - HS.at < 300000) { cb(HS.info); return; }
    api('support_info').then(function (r) {
      HS.info = (r && r.ok && r.enabled && r.base) ? r : { enabled: false }; HS.at = Date.now(); cb(HS.info);
    }).catch(function () { cb({ enabled: false }); });
  }
  function hsPost(action, body) {
    return fetch(HS.info.base + '/api/index.php?action=' + action, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) })
      .then(function (r) { return r.json(); });
  }
  function hsVid(v) {
    var k = 'dei_sp_vid';
    try { if (v) { localStorage.setItem(k, v); return v; } return localStorage.getItem(k) || ''; } catch (e) { return v || ''; }
  }
  function hsCtx() {
    var c = {}, src = (HS.info && HS.info.ctx) || {}, a = document.querySelector('#nav button.active');
    Object.keys(src).forEach(function (k) { c[k] = src[k]; });
    if (a && a.dataset.tab) c.tab = a.dataset.tab;
    return c;
  }
  function hsMount(r) {
    var box = r.querySelector('.help-box'), res = r.querySelector('#helpRes'), foot = r.querySelector('.help-foot');
    if (!box || !res || r.querySelector('#helpAsk')) return;
    var ask = document.createElement('div');
    ask.className = 'help-ask'; ask.id = 'helpAsk'; ask.hidden = true;
    ask.innerHTML = '<button type="button" data-hs="ask">' + ico('sparkles', 15) + ' <span id="helpAskTxt">Tanya Asisten Bantuan</span></button>';
    box.insertBefore(ask, res);
    var chat = document.createElement('div');
    chat.className = 'help-chat'; chat.id = 'helpChat';
    chat.innerHTML = '<div class="hc-top"><button type="button" class="btn sm" data-hs="back">' + ico('arrow-left', 14) + ' Panduan</button><b>Asisten Bantuan</b><small>Dijawab AI. Periksa lagi hal penting.</small></div>' +
      '<div class="hc-list" id="hcList"></div>' +
      '<div class="hc-wa" id="hcWa" hidden></div>' +
      '<form class="hc-in" id="hcForm"><textarea id="hcQ" rows="1" maxlength="1000" placeholder="Tulis pertanyaan… mis. cara tambah nomor WhatsApp"></textarea><button type="submit" class="btn" id="hcSend">Kirim</button></form>';
    box.insertBefore(chat, foot);
    r.addEventListener('click', function (e) {
      var b = e.target.closest('[data-hs]'); if (!b) return;
      var h = b.dataset.hs;
      if (h === 'ask') hsOpenChat($('#helpQ').value.trim());
      else if (h === 'back') { box.classList.remove('chat'); try { $('#helpQ').focus(); } catch (er) {} }
      else if (h === 'show') helpShow(b.dataset.id);
      else if (h === 'menu') { helpClose(); showTab(b.dataset.tab); }
    });
    $('#hcForm').addEventListener('submit', function (e) { e.preventDefault(); var t = $('#hcQ').value.trim(); if (t) { $('#hcQ').value = ''; hsSend(t); } });
    $('#hcQ').addEventListener('keydown', function (e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('#hcForm').dispatchEvent(new Event('submit', { cancelable: true })); } });
    $('#helpQ').addEventListener('input', hsAskLabel);
    $('#helpQ').addEventListener('keydown', function (e) {   // Enter tanpa hasil panduan -> tanya asisten
      if (e.key === 'Enter' && !$('#helpAsk').hidden && $('#helpQ').value.trim() && !document.querySelector('#helpRes .help-item [data-h="show"]')) { e.preventDefault(); hsOpenChat($('#helpQ').value.trim()); }
    });
  }
  function hsAskLabel() {
    var q = ($('#helpQ') ? $('#helpQ').value.trim() : ''), t = $('#helpAskTxt');
    if (t) t.textContent = q ? 'Tanya Asisten: "' + (q.length > 48 ? q.slice(0, 48) + '…' : q) + '"' : 'Tanya Asisten Bantuan';
  }
  function hsOnOpen() {
    var r = document.getElementById('helpRoot'); if (!r) return;
    var box = r.querySelector('.help-box'); if (box) box.classList.remove('chat');
    hsAskLabel();
    hsLoad(function (inf) { var a = $('#helpAsk'); if (a) a.hidden = !inf.enabled; });
  }
  function hsOpenChat(q) {
    var box = document.querySelector('#helpRoot .help-box'); if (!box || !HS.info || !HS.info.enabled) return;
    box.classList.add('chat');
    if (!HS.msgs.length) HS.msgs.push({ r: 'a', t: 'Halo! Saya Asisten Bantuan DEI Chatbot. Tanyakan cara pengaturan, letak menu, atau paket.' });
    hsRender();
    hsWa();
    if (q) hsSend(q); else setTimeout(function () { try { $('#hcQ').focus(); } catch (e) {} }, 30);
  }
  function hsWa() {
    if (HS.waAsked) return; HS.waAsked = true;
    fetch(HS.info.base + '/api/index.php?action=bootstrap').then(function (r) { return r.json(); }).then(function (j) {
      var c = (j && j.config) || {}, n = String(c.whatsapp_number || '').replace(/\D/g, '');
      if (!c.whatsapp_enabled || n.length < 8) return;
      var x = hsCtx(), txt = 'Halo tim DEI, saya butuh bantuan DEI Chatbot.' + (x.tenant_id ? ' (tenant ' + x.tenant_id + (x.version ? ', ' + x.version : '') + ')' : '');
      HS.wa = 'https://wa.me/' + n + '?text=' + encodeURIComponent(txt);
      var el = $('#hcWa'); if (el) { el.hidden = false; el.innerHTML = 'Belum terjawab? <a href="' + esc(HS.wa) + '" target="_blank" rel="noopener">Chat tim DEI lewat WhatsApp</a>'; }
    }).catch(function () {});
  }
  function hsActions(q, ans) {
    var acts = [], toks = helpTokens(q);
    if (toks.length) {
      var best = helpList().map(function (a) { return { a: a, s: helpScore(a, toks) }; }).filter(function (x) { return x.a.show && x.s >= 5; }).sort(function (x, y) { return y.s - x.s; })[0];
      if (best) acts.push({ k: 'show', id: best.a.id, t: best.a.t });
    }
    var low = String(ans || '').toLowerCase(), n = 0;
    Object.keys(HS_MENUS).forEach(function (tab) {
      if (n >= 2 || low.indexOf(HS_MENUS[tab].toLowerCase()) === -1) return;
      if (!document.querySelector('#nav button[data-tab="' + tab + '"]') || !tourTabAllowed(tab)) return;
      if (acts.some(function (x) { return x.k === 'show' && (HELP.filter(function (h) { return h.id === x.id; })[0].show[0] || {}).tab === tab; })) return;   // sudah diwakili "Tunjukkan di layar"
      acts.push({ k: 'menu', tab: tab, t: HS_MENUS[tab] }); n++;
    });
    return acts;
  }
  function hsRender(typing) {
    var el = $('#hcList'); if (!el) return;
    el.innerHTML = HS.msgs.map(function (m) {
      var h = '<div class="hc-m ' + (m.r === 'u' ? 'u' : 'a') + (m.err ? ' err' : '') + '"><div class="hc-b">' + esc(m.t).replace(/\n/g, '<br>') + '</div>';
      if (m.acts && m.acts.length) h += '<div class="hc-acts">' + m.acts.map(function (x) {
        return x.k === 'show' ? '<button type="button" data-hs="show" data-id="' + esc(x.id) + '">' + ico('sparkles', 13) + ' Tunjukkan di layar: ' + x.t + '</button>'
                              : '<button type="button" data-hs="menu" data-tab="' + esc(x.tab) + '">Buka menu ' + esc(x.t) + ' →</button>'; }).join('') + '</div>';
      return h + '</div>';
    }).join('') + (typing ? '<div class="hc-m a"><div class="hc-b hc-typing">Asisten sedang mengetik…</div></div>' : '');
    el.scrollTop = el.scrollHeight;
  }
  function hsSend(text) {
    if (HS.busy || !HS.info || !HS.info.enabled) return;
    text = String(text).slice(0, 1000);
    HS.busy = true; HS.msgs.push({ r: 'u', t: text }); hsRender(true);
    if ($('#hcSend')) $('#hcSend').disabled = true;
    var fail = function (msg) { HS.msgs.push({ r: 'a', err: true, t: msg || 'Asisten sedang tidak bisa dihubungi. Coba lagi sebentar lagi' + (HS.wa ? ', atau chat tim DEI lewat WhatsApp di bawah.' : '.') }); };
    var conv = HS.conv ? Promise.resolve(HS.conv) : hsPost('web_conv_new', { visitor_id: hsVid() }).then(function (j) {
      if (!j || !j.ok || !j.conversation_id) throw new Error((j && j.error) || 'conv');
      hsVid(j.visitor_id || ''); HS.conv = j.conversation_id; return HS.conv;
    });
    conv.then(function (cid) {
      return hsPost('chat', { message: text, conversation_id: cid, visitor_id: hsVid(), history: [], context: hsCtx() });
    }).then(function (j) {
      if (j && j.ok && j.answer) HS.msgs.push({ r: 'a', t: String(j.answer), acts: (j.suspended || j.cap_reached) ? [] : hsActions(text, j.answer) });
      else fail(j && j.error && /terlalu banyak/i.test(j.error) ? j.error : '');
    }).catch(function () { fail(''); }).then(function () {
      HS.busy = false; hsRender(false);
      if ($('#hcSend')) $('#hcSend').disabled = false;
      try { $('#hcQ').focus(); } catch (e) {}
    });
  }
