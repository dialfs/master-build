# v1.2.101: bagian UI (dijalankan dari patch_v12101_percakapan.py; memakai patch(), TEN, HERE)
SV_JS = open(os.path.join(HERE, 'sv.js'), encoding='utf-8').read()

SV_CSS = '''  /* v1.2.101: percakapan — Kinerja Layanan */
  .sv-h{font-size:14px;font-weight:600;margin:4px 0 10px;color:var(--ink)}
  .sv-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:20px}
  .sv-c{background:#fff;border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px;min-width:0}
  .sv-click{cursor:pointer}
  .sv-click:hover{border-color:var(--brand)}
  .sv-l{font-size:12px;color:var(--muted);font-weight:500}
  .sv-v{font-size:24px;font-weight:700;letter-spacing:-.02em;margin-top:4px;font-variant-numeric:tabular-nums}
  .sv-s{font-size:12px;color:var(--muted);margin-top:2px}
  .sv-d{font-size:11.5px;color:var(--muted);margin-top:6px}
  .sv-d.up{color:#15803d}
  .sv-d.down{color:#b91c1c}
  .sv-tbl td.r,.sv-tbl th.r{text-align:right;white-space:nowrap}
  .sv-row{cursor:pointer}
  .sv-row:hover td{background:#fafbfd}
  .sv-pager{display:flex;align-items:center;justify-content:flex-end;gap:8px;margin-top:10px;font-size:12.5px;color:var(--muted)}
  @media(max-width:860px){
    .rep-seg{overflow-x:auto;-webkit-overflow-scrolling:touch}
    .rep-seg button{flex:0 0 auto}
    .sv-grid{grid-template-columns:1fr 1fr;gap:10px}
    .sv-v{font-size:20px}
  }
'''

SV_HTML = '''      <!-- v1.2.101: percakapan — Kinerja Layanan -->
      <div id="repService" style="display:none">
        <div class="card">
          <div class="lg-presets" id="svPresets">
            <button type="button" data-p="month" class="on">Bulan ini</button>
            <button type="button" data-p="last">Bulan lalu</button>
            <button type="button" data-p="7">7 hari</button>
            <button type="button" data-p="30">30 hari</button>
            <button type="button" data-p="90">90 hari</button>
          </div>
          <div class="toolbar">
            <div class="row"><label class="fl">Dari tanggal</label><input type="date" id="svFrom"></div>
            <div class="row"><label class="fl">Sampai tanggal</label><input type="date" id="svTo"></div>
            <div class="row" id="svChWrap" style="display:none"><label class="fl">Nomor WhatsApp</label><select id="svCh"><option value="">Semua nomor</option></select></div>
            <button class="btn" id="svApply">Tampilkan</button>
            <button class="btn ghost" id="svExport">⬇ Unduh CSV</button>
          </div>
          <div class="desc" id="svNote" style="margin:4px 0 0"></div>
        </div>
        <h3 class="sv-h">Ringkasan Percakapan</h3>
        <div class="sv-grid" id="svConv"></div>
        <h3 class="sv-h">Kinerja Waktu</h3>
        <div class="sv-grid" id="svTime"></div>
        <h3 class="sv-h">Bot vs Agent</h3>
        <div class="sv-grid" id="svBot"></div>
        <div class="grid2">
          <div class="card"><h3>Tren Harian</h3><div class="desc">Percakapan per hari: diselesaikan bot vs diserahkan ke agent.</div><div id="svTrend"></div></div>
          <div class="card"><h3>Alasan Diserahkan ke Agent</h3><div class="desc">Mengapa percakapan berpindah dari bot ke manusia.</div><div id="svReasons"></div></div>
        </div>
        <div class="grid2">
          <div class="card"><h3>Percakapan Baru per Jam</h3><div class="desc" id="svHourlyNote"></div><div id="svHourly"></div></div>
          <div class="card"><h3>Rata-rata per Hari dalam Seminggu</h3><div class="desc">Percakapan baru rata-rata per hari.</div><div id="svWeekday"></div></div>
        </div>
        <div class="card">
          <h3>Kinerja per Agent</h3>
          <div class="desc">Dihitung dari percakapan yang di-assign ke agent (agent terakhir yang memegang).</div>
          <div class="scroll"><table class="tbl sv-tbl"><thead><tr><th>Agent</th><th class="r">Di-assign</th><th class="r">Selesai</th><th class="r">Berjalan</th><th class="r">Respon pertama</th><th class="r">Waktu respon</th><th class="r">Waktu selesai</th><th class="r">Pesan</th></tr></thead><tbody id="svAgents"></tbody></table></div>
        </div>
        <div class="card" id="svChCard" style="display:none">
          <h3>Per Nomor WhatsApp</h3>
          <div class="scroll"><table class="tbl sv-tbl"><thead><tr><th>Nomor</th><th class="r">Percakapan</th><th class="r">Selesai bot</th><th class="r">Ke agent</th><th class="r">Belum di-assign</th><th class="r">Selesai</th><th class="r">Respon pertama</th><th class="r">Respon agent</th><th class="r">Waktu selesai</th></tr></thead><tbody id="svChans"></tbody></table></div>
        </div>
        <div class="card" id="svListCard">
          <h3>Daftar Percakapan</h3>
          <div class="lg-chips" id="svChips" style="margin:6px 0 10px">
            <button type="button" class="lg-chip on" data-k="">Semua</button>
            <button type="button" class="lg-chip" data-k="unassigned">Belum di-assign</button>
            <button type="button" class="lg-chip" data-k="in_progress">Berjalan</button>
            <button type="button" class="lg-chip" data-k="resolved">Selesai</button>
            <button type="button" class="lg-chip" data-k="bot_resolved">Selesai oleh bot</button>
            <button type="button" class="lg-chip" data-k="to_agent">Diserahkan ke agent</button>
          </div>
          <div class="scroll"><table class="tbl sv-tbl"><thead><tr><th>Dibuka</th><th>Kontak</th><th>Status</th><th>Agent</th><th class="r">Respon pertama</th><th class="r">Waktu selesai</th><th>Diselesaikan oleh</th></tr></thead><tbody id="svRows"></tbody></table></div>
          <div class="sv-pager"><span id="svPageInfo"></span><button class="btn ghost" id="svPrev" style="padding:5px 10px">‹</button><button class="btn ghost" id="svNext" style="padding:5px 10px">›</button></div>
        </div>
      </div><!-- /repService -->
'''

patch(TEN, 'dashboard/chatbot-ai/index.html', [
    ('        <button type="button" data-v="topics"><span data-ico="sparkles"></span> Topik</button>\n',
     '        <button type="button" data-v="topics"><span data-ico="sparkles"></span> Topik</button>\n'
     '        <button type="button" data-v="service"><span data-ico="headphones"></span> Kinerja Layanan</button><!-- v1.2.101: percakapan -->\n'),
    ('      <div id="repTopics" style="display:none">', SV_HTML + '      <div id="repTopics" style="display:none">'),
    ('  .lg-filters{padding:16px 18px}\n', SV_CSS + '  .lg-filters{padding:16px 18px}\n'),
    ('<script src="app.js?v=1.2.100"></script><!-- v1.2.100: routing -->',
     '<script src="app.js?v=1.2.101"></script><!-- v1.2.101: percakapan -->'),
])

patch(TEN, 'dashboard/chatbot-ai/app.js', [
    ("  function repView(v) {\n    if (['summary', 'logs', 'topics'].indexOf(v) === -1) v = 'summary';\n",
     SV_JS + "\n  function repView(v) {\n    if (['summary', 'logs', 'topics', 'service'].indexOf(v) === -1) v = 'summary';   // v1.2.101: + service\n"),
    ("    $('#repTopics').style.display = v === 'topics' ? '' : 'none';\n",
     "    $('#repTopics').style.display = v === 'topics' ? '' : 'none';\n"
     "    $('#repService').style.display = v === 'service' ? '' : 'none';   // v1.2.101\n"),
    ("    if (v === 'topics') tpInit();   // v1.2.67\n",
     "    if (v === 'topics') tpInit();   // v1.2.67\n"
     "    if (v === 'service') svInit();   // v1.2.101: percakapan\n"),
    ("    // v1.2.58: Supervisor/Admin — serahkan chat ke agent tertentu\n",
     "    // v1.2.101: percakapan — tombol Selesai (pemegang chat, admin/supervisor, atau chat yang belum dipegang)\n"
     "    if (res.conv && ['open', 'handover', 'assigned'].indexOf(res.conv.status) > -1 && (!claim || isMine || waState.isAdmin)) {\n"
     "      actionBtns += ' <button class=\"btn ghost\" id=\"waResolveBtn\" style=\"padding:7px 14px;font-size:13px;margin-left:6px\" title=\"Tandai percakapan ini selesai. Chat dilepas; pesan berikutnya membuka percakapan baru.\">' + ico('check-circle-2',14) + ' Selesai</button>';\n"
     "    }\n"
     "    // v1.2.58: Supervisor/Admin — serahkan chat ke agent tertentu\n"),
    ("        kartu('done', 'done', 'check-circle-2', 'Selesai (customer diam 24 jam)') +",
     "        kartu('done', 'done', 'check-circle-2', 'Selesai (ditandai / diam 24 jam)') +   // v1.2.101"),
    ("    if ($('#waAssignSel')) $('#waAssignSel').onchange = function () { assignNumber(num, this.value, this); };   // v1.2.58\n",
     "    if ($('#waAssignSel')) $('#waAssignSel').onchange = function () { assignNumber(num, this.value, this); };   // v1.2.58\n"
     "    if ($('#waResolveBtn')) $('#waResolveBtn').onclick = function () { resolveConv(num); };   // v1.2.101\n"),
])
