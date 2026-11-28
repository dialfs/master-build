  /* ---- v1.2.226: buat-template -- buat message template WhatsApp dari dashboard ---- */
  function tplVarCount(t) { var m = String(t || '').match(/\{\{\s*(\d+)\s*\}\}/g) || [], n = 0; m.forEach(function (x) { n = Math.max(n, +x.replace(/\D/g, '')); }); return n; }
  function tplRenderEx() {
    var box = $('#tplEx'); if (!box) return;
    var n = tplVarCount($('#tplBody').value), old = {};
    $$('#tplEx input').forEach(function (el) { old[el.dataset.k] = el.value; });
    var h = '';
    for (var k = 1; k <= n; k++) h += '<div class="row"><label class="fl">Contoh isi {{' + k + '}}</label><input type="text" data-k="' + k + '" value="' + esc(old[k] || '') + '" placeholder="' + (k === 1 ? 'mis. Budi' : 'contoh nilai') + '"></div>';
    box.innerHTML = h;
  }
  function tplLoadList() {
    var box = $('#tplList'); if (!box) return;
    box.textContent = 'Memuat…';
    var _bch = $('#blastCh') ? $('#blastCh').value : '';
    api('wa_templates', { query: _bch ? '&ch=' + encodeURIComponent(_bch) : '' }).then(function (r) {
      if (!r || !r.ok) { box.textContent = (r && r.error) || 'Gagal memuat template.'; return; }
      var ts = r.templates || [];
      if (!ts.length) { box.textContent = 'Belum ada template.'; return; }
      var col = { APPROVED: '#1a7f37', PENDING: '#b54708', REJECTED: '#b42318', PAUSED: '#b54708', DISABLED: '#b42318' };
      box.innerHTML = '<div class="tbl-wrap"><table class="tbl" style="width:100%"><thead><tr><th>Nama</th><th>Kategori</th><th>Bahasa</th><th>Status</th></tr></thead><tbody>' +
        ts.map(function (t) { var st = String(t.status || '').toUpperCase();
          return '<tr><td class="mono" title="' + esc(t.body || '') + '">' + esc(t.name) + '</td><td>' + esc(t.category || '') + '</td><td>' + esc(t.language || '') + '</td><td><b style="color:' + (col[st] || 'inherit') + '">' + esc(st) + '</b></td></tr>'; }).join('') +
        '</tbody></table></div>';
    }).catch(function () { box.textContent = 'Gagal memuat template.'; });
  }
  function tplInit() {
    var card = $('#tplCard'); if (!card) return;
    var ok = role === 'super_admin' || role === 'admin';
    card.style.display = ok ? '' : 'none';
    if (!ok) return;
    if (card.dataset.wired) { tplLoadList(); return; }
    card.dataset.wired = '1';
    $('#tplBody').oninput = tplRenderEx;
    $('#tplReload').onclick = tplLoadList;
    $('#tplName').onblur = function () { this.value = this.value.toLowerCase().replace(/[^a-z0-9_]+/g, '_').replace(/^_+|_+$/g, ''); };
    $('#tplSubmit').onclick = function () {
      var st = $('#tplStatus'), btn = this;
      var ex = []; $$('#tplEx input').forEach(function (el) { ex[+el.dataset.k - 1] = el.value.trim(); });
      var body = { name: $('#tplName').value.trim(), category: $('#tplCat').value, language: $('#tplLang').value,
        header: $('#tplHead').value.trim(), body: $('#tplBody').value.trim(), footer: $('#tplFoot').value.trim(), examples: ex,
        ch: $('#blastCh') ? $('#blastCh').value : '' };
      if (!body.name || !body.body) { toast('Isi nama dan isi pesan template.', true); return; }
      btn.disabled = true; st.textContent = 'Mengirim ke Meta…'; st.style.color = '';
      api('wa_template_create', { method: 'POST', body: body }).then(function (r) {
        btn.disabled = false;
        if (!r || !r.ok) { st.textContent = (r && r.error) || 'Gagal.'; st.style.color = '#b42318'; return; }
        st.textContent = 'Terkirim: ' + r.name + ' — status ' + r.status + ' (' + r.category + ')'; st.style.color = '#1a7f37';
        toast('Template ' + r.name + ' dikirim ke Meta.');
        tplLoadList();
      }).catch(function () { btn.disabled = false; st.textContent = 'Gagal.'; st.style.color = '#b42318'; });
    };
    tplRenderEx(); tplLoadList();
  }
