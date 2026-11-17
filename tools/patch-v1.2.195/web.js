  /* v1.2.195: web-balas — balas chat web dari dashboard (Claim / Balas / Kembalikan ke bot) */
  function webHoldTag(c) {
    if (c.hold === 'req') return ' <span class="tag" style="background:#fee2e2;color:#991b1b;padding:2px 8px;font-size:11px;font-weight:600">Minta tim</span>';
    if (c.hold === 'agent') return ' <span class="tag" style="background:#dcfce7;color:#14532d;padding:2px 8px;font-size:11px">Dipegang ' + esc(c.agent_name || 'tim') + '</span>';
    return '';
  }
  function webCtxLine(conv) {   // tenant Support: siapa yang bertanya (paket, versi, peran, menu)
    var x = conv && conv.ctx; if (!x) return '';
    var M = { reports: 'Laporan & Log', wachat: 'Percakapan WA', webchat: 'Percakapan Web', blast: 'Blast WA', leads: 'Leads', kontak: 'Kontak', topik: 'Topik & Divisi',
      gc: 'Customer Feedback', tim: 'Tim & Agent', kb: 'Knowledge Base', content: 'Balasan & Tampilan', test: 'Tes Chatbot', widget: 'Widget & API',
      eskalasi: 'Respon & Eskalasi', users: 'Pengguna', profile: 'Profil Saya', install: 'Pemasangan (GTM)', pembaruan: 'Pembaruan' };
    var p = [];
    if (x.tier) p.push('paket ' + x.tier + (x.trial_tier ? ' (' + x.trial_tier + ')' : ''));
    if (x.version) p.push(x.version);
    if (x.role) p.push(ROLE_LABEL[x.role] || x.role);
    if (x.tab) p.push('menu ' + (M[x.tab] || x.tab));
    if (x.wa_provider) p.push('WA ' + x.wa_provider);
    return p.length ? ' &middot; ' + esc(p.join(' · ')) : '';
  }
  function webAgo(sec) {
    sec = Math.max(0, sec | 0);
    if (sec < 60) return 'baru saja';
    if (sec < 3600) return Math.floor(sec / 60) + ' mnt lalu';
    return Math.floor(sec / 3600) + ' jam lalu';
  }
  function webReplyEl() {
    var r = $('#webReply');
    if (r) return r;
    var body = $('#webThreadBody'); if (!body) return null;
    r = document.createElement('div');
    r.id = 'webReply'; r.className = 'web-reply'; r.hidden = true;
    r.innerHTML = '<div class="wr-st" id="webReplySt"></div>' +
      '<div class="wr-in"><textarea id="webReplyInput" rows="1" maxlength="4000" placeholder="Tulis balasan untuk pengunjung…"></textarea>' +
      '<button type="button" class="btn" id="webReplySend">Kirim</button></div>';
    body.parentNode.insertBefore(r, body.nextSibling);
    $('#webReplySend').onclick = webReplySend;
    $('#webReplyInput').addEventListener('keydown', function (e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); webReplySend(); } });
    r.addEventListener('click', function (e) {
      var b = e.target.closest('[data-wr]'); if (!b || !webState.current) return;
      var act = b.dataset.wr === 'claim' ? 'web_claim' : 'web_release';
      if (act === 'web_release' && !confirm('Kembalikan percakapan ini ke asisten otomatis?')) return;
      b.disabled = true;
      api(act, { method: 'POST', body: { conversation_id: webState.current } }).then(function (res) {
        b.disabled = false;
        if (!res.ok) { toast(res.error || 'Gagal.', true); return; }
        toast(act === 'web_claim' ? 'Percakapan Anda pegang. Asisten otomatis berhenti menjawab.' : 'Dikembalikan ke asisten otomatis.');
        fetchWebThread(webState.current, true); fetchWebConvs(true);
      }).catch(function () { b.disabled = false; toast('Gagal.', true); });
    });
    return r;
  }
  function webReplySync(convId, st) {
    var r = webReplyEl(); if (!r) return;
    if (!st || st.archived || st.hold === undefined) { r.hidden = true; return; }
    r.hidden = false;
    var now = st.now || Math.floor(Date.now() / 1000), h = '', btn = '';
    if (st.hold === 'agent' && st.mine) {
      h = '<b style="color:#15803d">Anda memegang percakapan ini.</b> Asisten otomatis berhenti menjawab sampai dikembalikan (atau 60 menit tanpa balasan Anda).';
      btn = '<button type="button" class="btn ghost sm" data-wr="release">Kembalikan ke asisten</button>';
    } else if (st.hold === 'agent') {
      h = 'Dipegang <b>' + esc(st.agent_name || st.agent) + '</b> · aktif ' + webAgo(now - (st.agent_last || now)) + '.' + (role === 'wa_agent' ? '' : ' Membalas akan mengambil alih.');
      btn = role === 'wa_agent' ? '' : '<button type="button" class="btn ghost sm" data-wr="release">Kembalikan ke asisten</button>';
    } else if (st.hold === 'req') {
      h = '<b style="color:#b91c1c">Pengunjung minta bicara dengan tim</b> · ' + webAgo(now - (st.req_at || now)) + '. Asisten otomatis berhenti menjawab.';
      btn = '<button type="button" class="btn sm" data-wr="claim">Pegang percakapan</button> <button type="button" class="btn ghost sm" data-wr="release">Kembalikan ke asisten</button>';
    } else {
      h = 'Dijawab asisten otomatis. Membalas di sini akan mengambil alih percakapan.';
      btn = '<button type="button" class="btn ghost sm" data-wr="claim">Pegang percakapan</button>';
    }
    $('#webReplySt').innerHTML = '<span>' + h + '</span><span class="wr-btns">' + btn + '</span>';
    var locked = st.hold === 'agent' && !st.mine && role === 'wa_agent';
    $('#webReplyInput').disabled = locked; $('#webReplySend').disabled = locked;
    $('#webReplyInput').placeholder = locked ? 'Percakapan ini dipegang ' + (st.agent_name || st.agent) + '.' : 'Tulis balasan untuk pengunjung…';
  }
  function webReplySend() {
    var inp = $('#webReplyInput'), b = $('#webReplySend'), t = inp ? inp.value.trim() : '';
    if (!t || !webState.current || b.disabled) return;
    b.disabled = true;
    api('web_reply', { method: 'POST', body: { conversation_id: webState.current, text: t } }).then(function (res) {
      b.disabled = false;
      if (!res.ok) { toast(res.error || 'Gagal mengirim.', true); return; }
      inp.value = '';
      fetchWebThread(webState.current, true); fetchWebConvs(true);
    }).catch(function () { b.disabled = false; toast('Gagal mengirim.', true); });
  }

