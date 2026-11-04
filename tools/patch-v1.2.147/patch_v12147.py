# v1.2.147: leads-kanban — tampilan Leads bisa Daftar atau Kanban (kolom per status, seret kartu = ganti status)
import sys, os, shutil, time
T = os.path.expanduser(sys.argv[1])
J = os.path.join(T, 'dashboard/chatbot-ai/app.js'); H = os.path.join(T, 'dashboard/chatbot-ai/index.html'); A = os.path.join(T, 'api/index.php')
ts = time.strftime('%Y%m%d-%H%M%S')
for f in (H, J, A): shutil.copy2(f, f + '.bak-v12147k-' + ts)
def rep(path, old, new):
    s = open(path, encoding='utf-8').read()
    if new in s and old not in s: print('skip'); return
    assert s.count(old) == 1, (path, old[:60]); open(path, 'w', encoding='utf-8').write(s.replace(old, new))

# ---- HTML: tombol tampilan + CSS
rep(H, """          <button class="btn ghost sm" id="btnReloadLeads" style="margin-left:auto">&#8635; Muat ulang</button>""",
"""          <span class="lk-view" style="margin-left:auto"><!-- v1.2.147: leads-kanban -->
            <button type="button" class="btn ghost sm" data-lead-view="list">Daftar</button><button type="button" class="btn ghost sm" data-lead-view="kanban">Kanban</button>
          </span>
          <button class="btn ghost sm" id="btnReloadLeads">&#8635; Muat ulang</button>""")
s = open(H, encoding='utf-8').read()
CSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kanban.css'), encoding='utf-8').read()
if 'v1.2.147: leads-kanban */' not in s:
    i = s.index('</style>'); s = s[:i] + CSS + s[i:]; open(H, 'w', encoding='utf-8').write(s)
rep(H, '<script src="app.js?v=1.2.146"></script><!-- v1.2.146: label-nomor-utama -->',
       '<script src="app.js?v=1.2.147"></script><!-- v1.2.147: leads-kanban -->')

# ---- JS
rep(J, """  function loadLeads() {
    fetchLeads();
    $('#btnReloadLeads').onclick = fetchLeads;""",
"""  // v1.2.147: leads-kanban — pilihan tampilan diingat per browser
  var leadView = 'list';
  try { leadView = localStorage.getItem('dei_lead_view') === 'kanban' ? 'kanban' : 'list'; } catch (e) {}
  function leadViewApply() {
    var p = $('#panel-leads'); if (p) p.classList.toggle('lk-on', leadView === 'kanban');
    $$('[data-lead-view]').forEach(function (b) { b.classList.toggle('on', b.dataset.leadView === leadView); });
  }
  function loadLeads() {
    fetchLeads();
    $('#btnReloadLeads').onclick = fetchLeads;
    $$('[data-lead-view]').forEach(function (b) {   // v1.2.147: leads-kanban
      b.onclick = function () {
        leadView = b.dataset.leadView;
        try { localStorage.setItem('dei_lead_view', leadView); } catch (e) {}
        leadViewApply(); renderLeads();
      };
    });
    leadViewApply();""")
rep(J, """  function renderLeads() {
    leadFilterLegacyBtn();   // v1.2.118
""", """  function renderLeads() {
    leadFilterLegacyBtn();   // v1.2.118
    if (leadView === 'kanban') { renderLeadsKanban(); return; }   // v1.2.147: leads-kanban
""")
rep(J, """  function saveLead(num, body) {""", r"""  // v1.2.147: leads-kanban — satu kolom per status; seret kartu (desktop) atau ganti dropdown (HP)
  function renderLeadsKanban() {
    var box = $('#leadList');
    if (!leadData.length) {
      box.innerHTML = '<div class="card" style="text-align:center;color:var(--muted)">Belum ada lead. Kartu dibuat otomatis saat percakapan WhatsApp mencapai 8 pesan.</div>';
      return;
    }
    var cols = Object.keys(LEAD_STATUS).filter(function (k) {
      return !LEAD_STATUS[k].legacy || leadData.some(function (l) { return l.status === k; });
    });
    var byCol = {}; cols.forEach(function (k) { byCol[k] = []; });
    leadData.forEach(function (l) { var k = l.status || 'baru'; (byCol[k] || byCol.baru).push(l); });
    cols.forEach(function (k) {   // terbaru di atas
      byCol[k].sort(function (a, b) { return String(b.updated_at || b.analyzed_at || '').localeCompare(String(a.updated_at || a.analyzed_at || '')); });
    });
    box.innerHTML = '<div class="lk-board">' + cols.map(function (k) {
      var d = LEAD_STATUS[k];
      return '<div class="lk-col" data-col="' + k + '">' +
        '<div class="lk-col-h"><span class="tag" style="background:' + d.bg + ';color:' + d.fg + '">' + esc(d.label) + '</span>' +
          '<span class="lk-n">' + byCol[k].length + '</span></div>' +
        '<div class="lk-list">' + (byCol[k].length ? byCol[k].map(function (l) {
          var ex = l.extracted || {};
          var judul = l.name ? esc(l.name) : ('+' + esc(l.number));
          return '<div class="lk-card" draggable="true" data-lead="' + esc(l.number) + '" title="Seret ke kolom lain untuk mengganti status">' +
            '<div class="lk-t">' + judul + '</div>' +
            '<div class="lk-s">' + (l.name ? '+' + esc(l.number) + ' &middot; ' : '') + esc((l.analyzed_at || '').slice(0, 16)) + '</div>' +
            '<div style="margin-top:6px">' + contactStageBadgeHtml(l.contact_stage, l.contact_vip) + '</div>' +
            (ex.ringkasan ? '<div class="lk-r">' + esc(ex.ringkasan) + '</div>' : '') +
            (ex.kebutuhan ? '<div class="lk-s" style="margin-top:5px"><strong>Kebutuhan:</strong> ' + esc(ex.kebutuhan) + '</div>' : '') +
            (l.note ? '<div class="lk-note">' + esc(l.note) + '</div>' : '') +
            '<div class="lk-f"><select class="lk-st" aria-label="Status">' + leadStatusOptionsHtml(l.status || 'baru') + '</select>' +
              '<button type="button" class="lk-chat" title="Lihat percakapan">' + ico('message-circle', 14) + '</button></div>' +
          '</div>';
        }).join('') : '<div class="lk-empty">Seret kartu ke sini</div>') + '</div>' +
      '</div>';
    }).join('') + '</div>';

    var dragNum = null;
    function pindah(num, st) {
      var l = leadData.filter(function (x) { return x.number === num; })[0];
      if (!l || (l.status || 'baru') === st) return;
      l.status = st; renderLeadsKanban();   // langsung pindah, server menyusul
      saveLead(num, { status: st });
    }
    $$('#leadList .lk-card').forEach(function (c) {
      var num = c.dataset.lead;
      c.ondragstart = function (e) { dragNum = num; c.classList.add('lk-drag'); try { e.dataTransfer.setData('text/plain', num); e.dataTransfer.effectAllowed = 'move'; } catch (er) {} };
      c.ondragend = function () { c.classList.remove('lk-drag'); $$('#leadList .lk-col').forEach(function (x) { x.classList.remove('lk-over'); }); };
      c.querySelector('.lk-st').onchange = function (e) { pindah(num, e.target.value); };
      c.querySelector('.lk-st').onmousedown = function (e) { e.stopPropagation(); };
      c.querySelector('.lk-chat').onclick = function () { openLeadConv(num); };
    });
    $$('#leadList .lk-col').forEach(function (col) {
      col.ondragover = function (e) { e.preventDefault(); col.classList.add('lk-over'); };
      col.ondragleave = function (e) { if (!col.contains(e.relatedTarget)) col.classList.remove('lk-over'); };
      col.ondrop = function (e) {
        e.preventDefault(); col.classList.remove('lk-over');
        var num = dragNum; try { num = e.dataTransfer.getData('text/plain') || dragNum; } catch (er) {}
        dragNum = null; if (num) pindah(num, col.dataset.col);
      };
    });
  }

  function saveLead(num, body) {""")
rep(A, "define('DEI_VERSION', 'v1.2.146');   // v1.2.146: label-nomor-utama",
       "define('DEI_VERSION', 'v1.2.147');   // v1.2.147: leads-kanban")
print('OK')
