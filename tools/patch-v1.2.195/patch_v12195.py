#!/usr/bin/env python3
"""v1.2.195 (web-balas): tim membalas chat web dari menu Percakapan Web; pengunjung bisa minta bicara dengan tim.
Tenant (paket: api/index.php, assets/js/chat-widget.js, dashboard/chatbot-ai/app.js + index.html):
- action publik web_human (minta tim) & web_poll (ambil balasan tim); admin web_claim / web_reply / web_release
- chat: percakapan yang ditahan (dipegang tim / minta tim, <= 60 mnt) tidak dijawab AI; pesan diteruskan + notifikasi push
- riwayat ke AI: balasan tim dibaca sebagai assistant; auto-closing web dilewati saat ditahan
- widget website: tombol "Bicara dengan tim kami" (Widget & API > Status Widget), status, balasan tim muncul otomatis
- Asisten Bantuan (Pusat Bantuan): tombol "Bicara dengan tim DEI" menggantikan tautan WhatsApp; balasan tim muncul di panel
- Percakapan Web: penanda Minta tim / Dipegang, kotak balas, Pegang / Kembalikan ke asisten, konteks penanya (tenant Support)
Butuh v1.2.194. Idempoten.  Pakai: patch_v12195.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
D = os.path.dirname(os.path.abspath(__file__))
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
T = H + '/dei-tenant'
TAG = 'v1.2.195: web-balas'; NEED = 'v1.2.194: asisten-bantuan'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12195-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
M = '   // ' + TAG

# ================================================================== api/index.php
API = T + '/api/index.php'; s = rd(API)
if TAG in s: print('sudah:', API)
else:
    assert NEED in s, 'butuh v1.2.194'
    a = "$PUBLIC_ACTIONS = ['bootstrap', 'chat', 'web_conv_list', 'web_conv_thread', 'web_conv_new', 'web_lead_save', 'web_closing', 'gc_submit', 'wa_ref'];"
    s = rep(s, a, a[:-2] + ", 'web_human', 'web_poll'];" + M, what='PUBLIC_ACTIONS')
    a = "function deiSupportSelf() { return deiSupportInfo()['self']; }\n"
    s = rep(s, a, a + rd(D + '/t_lib.php'), what='lib')
    # chat: percakapan ditahan -> teruskan ke tim (sebelum kuota AI: membalas manusia tidak memakai kuota)
    a = "        // v1.1.4: cap enforcement (cache 24h, tiered: 90%=graceful, 100%=halt total)\n"
    s = rep(s, a, "        if (!$isAdminTest) {" + M + " — percakapan yang ditahan: tanpa AI, diteruskan ke tim\n"
                  "            $deiWebIn = bodyInput(); $deiWebCid = trim((string)($deiWebIn['conversation_id'] ?? ''));\n"
                  "            if ($deiWebCid !== '') { $deiWebR = deiWebHeldChat($s, $deiWebCid, trim((string)($deiWebIn['visitor_id'] ?? '')), (string)($deiWebIn['message'] ?? '')); if ($deiWebR) jsonOut($deiWebR, empty($deiWebR['ok']) ? 429 : 200); }\n"
                  "        }\n" + a, what='cap enforcement')
    a = "                    return ['role' => $m['role'], 'content' => $m['content']];\n"
    s = rep(s, a, "                    return ['role' => (($m['role'] ?? '') === 'user') ? 'user' : 'assistant', 'content' => $m['content']];" + M + " — balasan tim = assistant\n", what='history map')
    a = "                if ($deiSpCtx && (!empty($deiSpCtx['business']) || !empty($deiSpCtx['tenant_id']))) {   // v1.2.193: asisten-support — judul = siapa yang bertanya\n"
    s = rep(s, a, a + "                    $convs[$idx]['ctx'] = $deiSpCtx;" + M + "\n", what='ctx meta')
    a = "        if ($idx < 0 || ($convs[$idx]['visitor_id'] ?? '') !== $visitorId) jsonOut(['ok' => false, 'error' => 'Conversation not found'], 404);\n        $msgs = webConvLoadMessages($convId);\n        $last = end($msgs);\n"
    s = rep(s, a, a.replace("        $last = end($msgs);\n", "        if (deiWebHold($convs[$idx]) !== '') jsonOut(['ok' => true, 'skip' => 'held']);" + M + "\n        $last = end($msgs);\n"), what='web_closing')
    a = "        $messages = webConvLoadMessages($convId);\n        jsonOut([\n            'ok'       => true,\n            'conversation' => $convs[$idx],\n            'messages' => $messages,\n"
    s = rep(s, a, "        $messages = webConvLoadMessages($convId);\n        jsonOut([\n            'ok'       => true,\n            'conversation' => $convs[$idx],\n"
                  "            'messages' => array_map('deiWebMsgOut', $messages),\n            'status'   => deiWebPub($convs[$idx]),"  + M + "\n", what='web_conv_thread')
    a = "        $slice = array_slice($convs, ($page - 1) * $perPage, $perPage);\n"
    s = rep(s, a, "        usort($convs, function ($a, $b) { return (deiWebHold($b) === 'req') <=> (deiWebHold($a) === 'req'); });" + M + " — minta tim di atas (usort PHP 8 stabil)\n"
                  + a + "        foreach ($slice as &$deiSl) { $deiSl = array_merge($deiSl, deiWebPub($deiSl)); } unset($deiSl);" + M + "\n", what='slice')
    a = "            'conversation' => deiWebConvStage($convs[$idx], $cts117),   // v1.2.117: filter-lead-rating\n            'messages'     => $messages,\n"
    s = rep(s, a, a + "            'web'          => deiWebAdminStatus($convs[$idx], $u)," + M + "\n", what='web_thread_admin')
    a = "    case 'web_conv_migrate': {\n"
    s = rep(s, a, rd(D + '/t_cases.php') + a, what='cases')
    a = "                'wa_attr'          => (bool)($s['widget']['wa_attr'] ?? true),   // v1.2.175: wa-atribusi\n"
    s = rep(s, a, a + "                'web_human'        => deiWebHumanConf($s)," + M + "\n", what='bootstrap')
    a = "            $allowedWidget = ['chatbot_enabled', 'whatsapp_enabled', 'whatsapp_number', 'whatsapp_message', 'lead_form', 'wa_attr'];"
    s = rep(s, a, a[:-2] + ", 'web_human'];" + M, what='allowedWidget')
    old = "define('DEI_VERSION', 'v1.2.194');   //"
    i = s.index(old)
    s = s[:i] + "define('DEI_VERSION', 'v1.2.195');   // " + TAG + " — tim membalas chat web dari Percakapan Web, tombol Bicara dengan tim;" + s[i + len(old):]
    save(API, s)

# ================================================================== chat-widget.js
W = T + '/assets/js/chat-widget.js'; s = rd(W)
if TAG in s: print('sudah:', W)
else:
    s = rep(s, "/* DEI AI Chat Widget v1.2.193 (", "/* DEI AI Chat Widget v1.2.195 (" + TAG + "; ", what='kepala')
    a = "      '.dch-foot{display:flex;gap:8px;padding:12px;border-top:1px solid #eee;background:#fff;flex-shrink:0}',\n"
    s = rep(s, a, a +
        "      '.dch-human{padding:8px 12px;border-top:1px solid #eee;background:#fafbff;font-size:12.5px;color:#555;flex-shrink:0;display:flex;align-items:center;gap:6px}',\n"
        "      '.dch-human button{background:none;border:1px solid ' + color + ';color:' + color + ';border-radius:16px;padding:5px 12px;font-size:12.5px;cursor:pointer}',\n"
        "      '.dch-human button:hover{background:' + color + ';color:#fff}',\n"
        "      '.dch-human .dh-on{width:8px;height:8px;border-radius:50%;background:#22c55e;display:inline-block}',\n"
        "      '.dm-by{font-size:11px;font-weight:600;color:' + color + ';margin-bottom:2px}',\n", what='css')
    a = "          '<div class=\"dch-foot\" id=\"dei-foot\" style=\"display:none\">' +\n"
    s = rep(s, a, "          '<div class=\"dch-human\" id=\"dei-human\" style=\"display:none\"></div>' +\n" + a, what='html')
    a = "      function showView(view) {\n        currentView = view;\n"
    s = rep(s, a, a + "        if (typeof humanSync === 'function') humanSync();" + "   /* " + TAG + " */\n", what='showView')
    a = "          foot.style.display = '';\n"
    s = rep(s, a, a + "          if (typeof humanSync === 'function') humanSync();\n", what='showView thread')
    a = "                addMsg(m.role === 'user' ? 'user' : 'bot', m.content);\n"
    s = rep(s, a, "                addMsg(m.role === 'user' ? 'user' : 'bot', m.content, m.role === 'agent' ? (m.by || 'Tim') : '');\n", what='openThread render')
    a = "            quick.innerHTML = '';\n            input.focus();\n"
    s = rep(s, a, "            wb.seen = (res && res.messages) ? res.messages.length : 0;   /* " + TAG + " */\n            wbStatus(res && res.status);\n" + a, what='openThread done')
    a = ("      function addMsg(role, text) {\n        var m = el('<div class=\"dm ' + role + '\"><div class=\"dm-b\"></div></div>');\n"
         "        m.querySelector('.dm-b').textContent = text;\n")
    s = rep(s, a, "      function addMsg(role, text, by) {\n        var m = el('<div class=\"dm ' + role + '\"><div class=\"dm-b\"></div></div>');\n"
                  "        if (by) {   /* " + TAG + ": balasan tim diberi nama */\n"
                  "          var bb = m.querySelector('.dm-b'); bb.innerHTML = '<div class=\"dm-by\"></div><div class=\"dm-t\"></div>';\n"
                  "          bb.querySelector('.dm-by').textContent = by; bb.querySelector('.dm-t').textContent = text;\n"
                  "        } else m.querySelector('.dm-b').textContent = text;\n", what='addMsg')
    a = "            if (res && res.ok) {\n              addMsg('bot', res.answer);\n"
    s = rep(s, a, "            if (res && res.ok && res.held) {   /* " + TAG + ": diteruskan ke tim, tanpa jawaban AI */\n              wbStatus(res.status);\n"
                  "            } else if (res && res.ok) {\n              addMsg('bot', res.answer);\n", what='send')
    a = "      /* ---- send message ---- */\n"
    s = rep(s, a, r'''      /* ---- v1.2.195: web-balas — bicara dengan tim + terima balasan tim ---- */
      var humanCfg = cfg.web_human || {};
      var humanEl = win.querySelector('#dei-human');
      var wb = { seen: 0, hold: '', agent: '', timer: null };
      function wbStatus(st) {
        st = st || {}; wb.hold = st.hold || ''; wb.agent = st.agent_name || '';
        humanSync(); wbSchedule();
      }
      function humanSync() {
        if (!humanEl) return;
        if (currentView !== 'thread' || !currentConvId) { humanEl.style.display = 'none'; return; }
        if (wb.hold === 'agent') { humanEl.innerHTML = '<span class="dh-on"></span>'; humanEl.appendChild(document.createTextNode(' Terhubung dengan ' + (wb.agent || 'tim kami'))); humanEl.style.display = ''; }
        else if (wb.hold === 'req') { humanEl.textContent = 'Menunggu tim membalas… Anda tetap bisa menulis pesan.'; humanEl.style.display = ''; }
        else if (humanCfg.enabled) {
          humanEl.innerHTML = '<button type="button"></button>';
          var hb = humanEl.querySelector('button'); hb.textContent = humanCfg.label || 'Bicara dengan tim kami'; hb.onclick = askHuman;
          humanEl.style.display = '';
        } else humanEl.style.display = 'none';
      }
      function askHuman() {
        if (!currentConvId) return;
        var cid = currentConvId;
        fetch(API + '?action=web_human', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ conversation_id: cid, visitor_id: visitorId, context: supportCtx() }) })
          .then(function (r) { return r.json(); })
          .then(function (res) {
            if (!res || !res.ok || cid !== currentConvId) return;
            (res.messages || []).forEach(function (m) { if (m.sys === 'human_req') addMsg('bot', m.content); });
            wb.seen = Math.max(wb.seen, res.total || 0);
            clearClosing();
            wbStatus(res.status);
          }).catch(function () {});
      }
      function wbSchedule() {
        if (wb.timer) { clearTimeout(wb.timer); wb.timer = null; }
        if (!opened || currentView !== 'thread' || !currentConvId) return;
        wb.timer = setTimeout(wbPoll, wb.hold ? 4000 : 15000);
      }
      function wbPoll() {
        wb.timer = null;
        if (!opened || currentView !== 'thread' || !currentConvId) return;
        var cid = currentConvId;
        fetch(API + '?action=web_poll&conversation_id=' + encodeURIComponent(cid) + '&visitor_id=' + encodeURIComponent(visitorId) + '&after=' + wb.seen)
          .then(function (r) { return r.json(); })
          .then(function (res) {
            if (!res || !res.ok || cid !== currentConvId) { wbSchedule(); return; }
            (res.messages || []).forEach(function (m) {
              if (m.role === 'agent') { addMsg('bot', m.content, m.by || 'Tim'); clearClosing(); }
              else if (m.sys && m.sys !== 'human_req') addMsg('bot', m.content);
            });
            wb.seen = Math.max(wb.seen, res.total || 0);
            wbStatus(res.status);
          }).catch(function () { wbSchedule(); });
      }

''' + a, what='send message')
    save(W, s)

# ================================================================== app.js
JS = T + '/dashboard/chatbot-ai/app.js'; s = rd(JS)
if TAG in s: print('sudah:', JS)
else:
    assert NEED in s
    # --- Percakapan Web
    a = "  function loadWachat() {\n"
    s = rep(s, a, rd(D + '/web.js') + a, what='loadWachat')
    a = "'<div style=\"margin-top:6px\">' + badge + mig + (c.lead_number"
    s = rep(s, a, "'<div style=\"margin-top:6px\">' + badge + mig + webHoldTag(c) + (c.lead_number", what='list tag')
    a = "            h += waBubble(m.content || '', (m.role === 'user' ? 'in' : 'bot'), m.ts);\n"
    s = rep(s, a, "            h += waBubble((m.role === 'agent' && m.by ? m.by + ': ' : '') + (m.content || ''), (m.role === 'user' ? 'in' : m.role === 'agent' ? 'manual' : 'bot'), m.ts);" + M + "\n", what='bubble')
    a = "'<div style=\"font-size:12px;color:var(--muted)\">Pengunjung web &middot; ' + count + ' pesan' + (conv.migrated ? ' &middot; arsip' : '') + '</div>'"
    s = rep(s, a, "'<div style=\"font-size:12px;color:var(--muted)\">Pengunjung web &middot; ' + count + ' pesan' + (conv.migrated ? ' &middot; arsip' : '') + webCtxLine(conv) + '</div>'", what='head ctx')
    a = "        renderWebConvs(webState.convs);\n      })\n      .catch(function () {\n        if (head) head.innerHTML = '<span style=\"color:var(--err)\">Gagal memuat.</span>';"
    s = rep(s, a, "        webReplySync(convId, res.web);" + M + "\n" + a, what='thread sync')
    # --- pengaturan widget
    a = "      if ($('#w_wa_attr')) $('#w_wa_attr').checked = w.wa_attr !== false;   // v1.2.175: wa-atribusi\n"
    s = rep(s, a, a + "      if ($('#w_web_human')) $('#w_web_human').checked = !!(w.web_human && w.web_human.enabled);" + M + "\n", what='load setting')
    a = "        wa_attr: $('#w_wa_attr') ? $('#w_wa_attr').checked : true,   // v1.2.175: wa-atribusi\n"
    s = rep(s, a, a + "        web_human: { enabled: $('#w_web_human') ? $('#w_web_human').checked : false }," + M + "\n", what='save setting')
    # --- Asisten Bantuan: tim DEI membalas di panel (menggantikan tautan WhatsApp)
    a = "  var HS = { info: null, at: 0, conv: '', busy: false, msgs: [], wa: null, waAsked: false };"
    s = rep(s, a, "  var HS = { info: null, at: 0, conv: '', busy: false, msgs: [], wa: null, waAsked: false, human: null, seen: 0, hold: '', agentName: '', timer: null };" + M, what='HS')
    a = "      else if (h === 'menu') { helpClose(); showTab(b.dataset.tab); }\n"
    s = rep(s, a, a + "      else if (h === 'human') hsHuman();" + M + "\n", what='hs click')
    a = "    hsRender();\n    hsWa();\n"
    s = rep(s, a, "    hsRender();\n    hsWa();\n    if (HS.conv) hsPoll();" + M + "\n", what='hsOpenChat')
    a = ("      if (!c.whatsapp_enabled || n.length < 8) return;\n"
         "      var x = hsCtx(), txt = 'Halo tim DEI, saya butuh bantuan DEI Chatbot.' + (x.tenant_id ? ' (tenant ' + x.tenant_id + (x.version ? ', ' + x.version : '') + ')' : '');\n"
         "      HS.wa = 'https://wa.me/' + n + '?text=' + encodeURIComponent(txt);\n"
         "      var el = $('#hcWa'); if (el) { el.hidden = false; el.innerHTML = 'Belum terjawab? <a href=\"' + esc(HS.wa) + '\" target=\"_blank\" rel=\"noopener\">Chat tim DEI lewat WhatsApp</a>'; }\n")
    s = rep(s, a, "      if (c.web_human && c.web_human.enabled) HS.human = c.web_human;" + M + " — tim DEI membalas di panel ini\n"
                  "      else if (c.whatsapp_enabled && n.length >= 8) {\n"
                  "        var x = hsCtx(), txt = 'Halo tim DEI, saya butuh bantuan DEI Chatbot.' + (x.tenant_id ? ' (tenant ' + x.tenant_id + (x.version ? ', ' + x.version : '') + ')' : '');\n"
                  "        HS.wa = 'https://wa.me/' + n + '?text=' + encodeURIComponent(txt);\n"
                  "      }\n      hsFoot();\n", what='hsWa')
    a = ("      var h = '<div class=\"hc-m ' + (m.r === 'u' ? 'u' : 'a') + (m.err ? ' err' : '') + '\"><div class=\"hc-b\">' + esc(m.t).replace(/\\n/g, '<br>') + '</div>';\n")
    s = rep(s, a, "      var h = '<div class=\"hc-m ' + (m.r === 'u' ? 'u' : m.r === 't' ? 'a t' : 'a') + (m.err ? ' err' : '') + '\"><div class=\"hc-b\">' + (m.by ? '<div class=\"hc-by\">' + esc(m.by) + ' · tim DEI</div>' : '') + esc(m.t).replace(/\\n/g, '<br>') + '</div>';" + M + "\n", what='hsRender')
    a = "'Asisten sedang tidak bisa dihubungi. Coba lagi sebentar lagi' + (HS.wa ? ', atau chat tim DEI lewat WhatsApp di bawah.' : '.')"
    s = rep(s, a, "'Asisten sedang tidak bisa dihubungi. Coba lagi sebentar lagi' + (HS.human ? ', atau klik ' + (HS.human.label || 'Bicara dengan tim DEI') + ' di bawah.' : HS.wa ? ', atau chat tim DEI lewat WhatsApp di bawah.' : '.')", what='hs fail')
    a = ("    var conv = HS.conv ? Promise.resolve(HS.conv) : hsPost('web_conv_new', { visitor_id: hsVid() }).then(function (j) {\n"
         "      if (!j || !j.ok || !j.conversation_id) throw new Error((j && j.error) || 'conv');\n"
         "      hsVid(j.visitor_id || ''); HS.conv = j.conversation_id; return HS.conv;\n    });\n")
    s = rep(s, a, "    var conv = hsEnsureConv();" + M + "\n", what='hs conv')
    a = "      if (j && j.ok && j.answer) HS.msgs.push("
    s = rep(s, a, "      if (j && j.ok && j.held) { HS.hold = (j.status || {}).hold || 'req'; HS.agentName = (j.status || {}).agent_name || ''; hsFoot(); }" + M + "\n      else if (j && j.ok && j.answer) HS.msgs.push(", what='hs held')
    a = ("      HS.busy = false; hsRender(false);\n      if ($('#hcSend')) $('#hcSend').disabled = false;\n"
         "      try { $('#hcQ').focus(); } catch (e) {}\n    });\n  }\n")
    s = rep(s, a, a.replace("      try { $('#hcQ').focus(); } catch (e) {}\n", "      try { $('#hcQ').focus(); } catch (e) {}\n      hsPollSchedule();\n") + r'''  /* v1.2.195: web-balas — bicara dengan tim DEI langsung di panel Asisten */
  function hsEnsureConv() {
    if (HS.conv) return Promise.resolve(HS.conv);
    return hsPost('web_conv_new', { visitor_id: hsVid() }).then(function (j) {
      if (!j || !j.ok || !j.conversation_id) throw new Error((j && j.error) || 'conv');
      hsVid(j.visitor_id || ''); HS.conv = j.conversation_id; HS.seen = 1; return HS.conv;
    });
  }
  function hsFoot() {
    var el = $('#hcWa'); if (!el) return;
    if (HS.hold === 'agent') { el.hidden = false; el.innerHTML = '<b style="color:#15803d">Terhubung dengan ' + esc(HS.agentName || 'tim DEI') + '.</b> Balasan tim muncul di percakapan ini.'; return; }
    if (HS.hold === 'req') { el.hidden = false; el.innerHTML = 'Pesan Anda diteruskan ke tim DEI. Mohon tunggu, balasan muncul di sini (panel boleh ditutup).'; return; }
    if (HS.human) { el.hidden = false; el.innerHTML = 'Belum terjawab? <button type="button" class="hc-human" data-hs="human">' + esc(HS.human.label || 'Bicara dengan tim DEI') + '</button>'; return; }
    if (HS.wa) { el.hidden = false; el.innerHTML = 'Belum terjawab? <a href="' + esc(HS.wa) + '" target="_blank" rel="noopener">Chat tim DEI lewat WhatsApp</a>'; return; }
    el.hidden = true;
  }
  function hsHuman() {
    if (!HS.info || !HS.info.enabled) return;
    var el = $('#hcWa'); if (el) el.textContent = 'Menghubungi tim DEI…';
    hsEnsureConv().then(function (cid) {
      return hsPost('web_human', { conversation_id: cid, visitor_id: hsVid(), context: hsCtx() });
    }).then(function (j) {
      if (!j || !j.ok) throw new Error((j && j.error) || 'gagal');
      (j.messages || []).forEach(function (m) { if (m.sys === 'human_req') HS.msgs.push({ r: 'a', t: m.content }); });
      HS.seen = Math.max(HS.seen, j.total || 0);
      HS.hold = (j.status || {}).hold || 'req'; HS.agentName = (j.status || {}).agent_name || '';
      hsRender(); hsFoot(); hsPollSchedule();
    }).catch(function () { HS.msgs.push({ r: 'a', err: true, t: 'Gagal menghubungi tim DEI. Coba lagi sebentar lagi.' }); hsRender(); hsFoot(); });
  }
  function hsPollSchedule() {
    if (HS.timer) { clearTimeout(HS.timer); HS.timer = null; }
    if (!HS.conv || !HS.info) return;
    var isOpen = !!document.querySelector('#helpRoot.on .help-box.chat');
    if (!isOpen && !HS.hold) return;   // panel tertutup: tetap memeriksa hanya selama menunggu / terhubung dengan tim
    HS.timer = setTimeout(hsPoll, isOpen && HS.hold ? 4000 : 15000);
  }
  function hsPoll() {
    if (HS.timer) { clearTimeout(HS.timer); HS.timer = null; }
    if (!HS.conv || !HS.info) return;
    var isOpen = !!document.querySelector('#helpRoot.on .help-box.chat');
    fetch(HS.info.base + '/api/index.php?action=web_poll&conversation_id=' + encodeURIComponent(HS.conv) + '&visitor_id=' + encodeURIComponent(hsVid()) + '&after=' + HS.seen)
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j || !j.ok) return;
        var got = 0;
        (j.messages || []).forEach(function (m) {
          if (m.role === 'agent') { HS.msgs.push({ r: 't', t: m.content, by: m.by || 'Tim' }); got++; }
          else if (m.sys && m.sys !== 'human_req') { HS.msgs.push({ r: 'a', t: m.content }); got++; }
        });
        HS.seen = Math.max(HS.seen, j.total || 0);
        var st = j.status || {}; HS.hold = st.hold || ''; HS.agentName = st.agent_name || '';
        if (got) { if (isOpen && !HS.busy) hsRender(false); else if (!isOpen) toast('Balasan baru dari tim DEI. Klik Panduan untuk membacanya.'); }
        hsFoot();
      }).catch(function () {}).then(hsPollSchedule);
  }
''', what='hsSend end')
    save(JS, s)

# ================================================================== index.html
HT = T + '/dashboard/chatbot-ai/index.html'; s = rd(HT)
if TAG in s: print('sudah:', HT)
else:
    a = "  @media(max-width:860px){ #helpRoot .help-box.chat{height:100%} #helpRoot .hc-in textarea{font-size:16px} }\n"
    s = rep(s, a, a +
        "  /* " + TAG + " */\n"
        "  #helpRoot .hc-m.t .hc-b{background:#ecfdf5;border-color:#a7f3d0}\n"
        "  #helpRoot .hc-by{font-size:11px;font-weight:600;color:#047857;margin-bottom:2px}\n"
        "  #helpRoot .hc-human{border:1px solid var(--brand);background:#fff;color:var(--brand);border-radius:16px;padding:4px 11px;font:inherit;font-size:12.5px;font-weight:600;cursor:pointer;margin-left:4px}\n"
        "  #helpRoot .hc-human:hover{background:var(--brand-tint)}\n"
        "  .web-reply{border-top:1px solid var(--line);background:#fff;padding:8px 12px 10px;flex-shrink:0}\n"
        "  .web-reply[hidden]{display:none}\n"
        "  .web-reply .wr-st{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;font-size:12.5px;color:var(--muted);margin-bottom:6px;line-height:1.45}\n"
        "  .web-reply .wr-btns{display:flex;gap:6px;flex-wrap:wrap}\n"
        "  .web-reply .wr-in{display:flex;gap:8px}\n"
        "  .web-reply textarea{flex:1;resize:none;border:1.5px solid var(--line);border-radius:10px;padding:9px 12px;font:inherit;font-size:14px;height:42px;min-height:42px;max-height:120px;min-width:0}\n"
        "  .web-reply textarea:focus{outline:none;border-color:var(--brand)}\n"
        "  @media(max-width:860px){ .web-reply textarea{font-size:16px} }\n", what='css')
    a = "          <label class=\"switch\"><input type=\"checkbox\" id=\"w_wa_attr\"><span class=\"sl\"></span></label></div><!-- v1.2.175: wa-atribusi -->\n"
    s = rep(s, a, a +
        "        <div class=\"toggle-row\"><div><div class=\"tt\">Pengunjung bisa minta bicara dengan tim</div><div class=\"td\">Widget menampilkan tombol \"Bicara dengan tim kami\". Setelah diklik, asisten berhenti menjawab dan tim membalas dari menu Percakapan Web (balasan muncul di widget).</div></div>\n"
        "          <label class=\"switch\"><input type=\"checkbox\" id=\"w_web_human\"><span class=\"sl\"></span></label></div><!-- " + TAG + " -->\n", what='toggle')
    a = '<script src="app.js?v=1.2.194"></script>'
    s = rep(s, a, '<script src="app.js?v=1.2.195"></script><!-- ' + TAG + ' -->', what='app.js?v')
    save(HT, s)
print('selesai', TAG)
