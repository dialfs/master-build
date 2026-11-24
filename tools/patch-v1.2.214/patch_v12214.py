#!/usr/bin/env python3
"""v1.2.214 (task): tiap bubble chat WA bisa dijadikan to-do + menu Task (kanban) + catatan.
- Bubble Percakapan WA: tautan "To-do" -> buat task (judul dari isi pesan); bubble yang sudah jadi task
  menampilkan "Task · <status>" dan membuka task-nya.
- Menu baru "Task" di sidebar: kanban New / On Progress / Pending / Done / Closed (seret kartu atau ganti
  dropdown), filter Semua / Tugas saya / Saya buat, cari, + Task baru (tanpa chat).
- Detail task: judul, status, ditugaskan ke, tenggat, catatan (per penulis), riwayat status,
  Buka di chat (lompat ke bubble asal), hapus (pembuat / Admin / Supervisor).
- Data: data/tasks.json (deiWithLock 'tasks'). Visibilitas mengikuti aturan chat (agent privat / scope SPV);
  task yang saya buat / ditugaskan ke saya selalu terlihat.
Butuh v1.2.213. Idempoten. Pakai: patch_v12214.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.214: task'; NEED = 'v1.2.213: wa-arsip'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12214-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ======================= dashboard: app.js =======================
JSLIB = r'''
  /* ====================================================================== *
   *  v1.2.214: task — to-do dari bubble chat, menu Task (kanban) + catatan
   * ====================================================================== */
  var TK_ST = {
    'new':    { label: 'New',         bg: '#e0e7ff', fg: '#3730a3' },
    progress: { label: 'On Progress', bg: '#dbeafe', fg: '#1d4ed8' },
    pending:  { label: 'Pending',     bg: '#fef3c7', fg: '#92400e' },
    done:     { label: 'Done',        bg: '#dcfce7', fg: '#166534' },
    closed:   { label: 'Closed',      bg: '#e5e7eb', fg: '#374151' }
  };
  var tkS = { list: [], users: [], me: '', idx: {}, filter: 'all', q: '', loaded: false, wired: false };
  try { var _tkf = localStorage.getItem('dei_task_flt'); if (['all', 'mine', 'byme'].indexOf(_tkf) !== -1) tkS.filter = _tkf; } catch (e) {}
  function tkIndex214() {
    tkS.idx = {};
    tkS.list.forEach(function (t) { if (t.src && t.src.num && t.src.k) tkS.idx[t.src.num + '|' + t.src.k] = t; });
    tkBadge214();
  }
  function tkSet214(r) {
    tkS.list = r.tasks || []; tkS.users = r.users || tkS.users; tkS.me = r.me || tkS.me; tkS.loaded = true;
    tkIndex214();
  }
  function tkFetch214(then) {
    api('tasks_list').then(function (r) {
      if (!r || !r.ok) { if (then) toast((r && r.error) || 'Gagal memuat task.', true); return; }
      tkSet214(r);
      if (typeof then === 'function') then();
    });
  }
  function tkUpsert214(t) {
    var i = -1;
    tkS.list.forEach(function (x, j) { if (x.id === t.id) i = j; });
    if (i >= 0) tkS.list[i] = t; else tkS.list.unshift(t);
    tkIndex214(); tkAfter214(t);
  }
  function tkRemove214(id) {
    var t = tkS.list.filter(function (x) { return x.id === id; })[0];
    tkS.list = tkS.list.filter(function (x) { return x.id !== id; });
    tkIndex214(); tkAfter214(t);
  }
  function tkAfter214(t) {   // segarkan tampilan yang memakai task
    var p = $('#panel-tasks'); if (p && p.classList.contains('active')) tkRender214();
    if (t && t.src && waState.current && String(waState.current) === String(t.src.num)) { try { fetchWaThread(waState.current); } catch (e) {} }
  }
  function tkBadge214() {
    var b = document.querySelector('#nav button[data-tab="tasks"]'); if (!b) return;
    var n = tkS.list.filter(function (t) { return t.assignee === tkS.me && ['new', 'progress', 'pending'].indexOf(t.status) !== -1; }).length;
    var s = b.querySelector('.tk-nb');
    if (!s) { s = document.createElement('span'); s.className = 'tk-nb'; b.appendChild(s); }
    s.textContent = n; s.style.display = n ? '' : 'none'; s.title = n + ' task terbuka untuk Anda';
  }
  function tkUserName214(un) {
    if (!un) return '';
    var u = tkS.users.filter(function (x) { return x.username === un; })[0];
    return u ? (u.name || u.username) : un;
  }
  function tkUserOpts214(sel) {
    var has = !sel;
    var h = '<option value="">— Belum ditentukan —</option>' + tkS.users.map(function (u) {
      if (u.username === sel) has = true;
      return '<option value="' + esc(u.username) + '"' + (u.username === sel ? ' selected' : '') + '>' + esc(u.name || u.username) + (u.username === tkS.me ? ' (saya)' : '') + '</option>';
    }).join('');
    if (!has) h += '<option value="' + esc(sel) + '" selected>' + esc(sel) + '</option>';
    return h;
  }
  function tkStatusOpts214(sel) {
    return Object.keys(TK_ST).map(function (k) { return '<option value="' + k + '"' + (k === sel ? ' selected' : '') + '>' + TK_ST[k].label + '</option>'; }).join('');
  }
  function tkSrcName214(src) {
    if (!src || !src.num) return '';
    return src.name ? src.name + ' (+' + src.num + ')' : '+' + src.num;
  }
  function tkSnip214(src) {
    var s = String((src && src.text) || '').replace(/\s+/g, ' ').trim();
    if (!s && src && src.mt) s = '[' + ({ image: 'Gambar', video: 'Video', audio: 'Pesan suara', document: 'Dokumen', sticker: 'Stiker' }[src.mt] || 'Media') + (src.mn ? ' ' + src.mn : '') + ']';
    return s;
  }
  function tkToday214() { var d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  function tkDueHtml214(t) {
    if (!t.due) return '';
    var late = t.due < tkToday214() && t.status !== 'done' && t.status !== 'closed';
    return '<span class="tk-due' + (late ? ' late' : '') + '" title="Tenggat' + (late ? ' — terlewat' : '') + '">' + ico('calendar', 12) + ' ' + esc(t.due.split('-').reverse().join('/')) + '</span>';
  }

  // ---- tautan di bubble Percakapan WA ----
  function waTaskBtn214(rq) {
    var num = waState.current; if (!num || !rq || !rq.k) return '';
    var t = tkS.idx[num + '|' + rq.k];
    if (t) { var d = TK_ST[t.status] || TK_ST['new']; return '<a href="#" class="wa-tk on" data-tk="' + esc(t.id) + '" title="Buka task: ' + esc(t.title) + '">' + ico('list-todo', 12) + ' Task · ' + esc(d.label) + '</a>'; }
    return '<a href="#" class="wa-tk" data-tk-k="' + esc(rq.k) + '" title="Jadikan to-do (menu Task)">' + ico('list-todo', 12) + ' To-do</a>';
  }
  function tk214WaInit() {
    if (waState.tk214) return; waState.tk214 = true;
    tkFetch214(function () { if (waState.current && tkS.list.length) fetchWaThread(waState.current); });
    var body = $('#waThreadBody');
    if (body) body.addEventListener('click', function (e) {
      var a = e.target.closest ? e.target.closest('.wa-tk') : null; if (!a) return;
      e.preventDefault();
      var id = a.getAttribute('data-tk');
      if (id) { tkOpen214(id); return; }
      var k = a.getAttribute('data-tk-k'), b = (waState.bIdx || {})[k], num = waState.current;
      if (!num || !b) return;
      var cv = (waState.convCache || {})[String(num)] || {};
      tkNew214({ number: String(num), k: k, ts: b.ts, kind: b.kind, text: b.text, mt: b.mt, mn: b.mn, name: cv.name || '' });
    });
  }

  // ---- modal ----
  function tkModal214(title, inner, wire) {
    var ov = document.createElement('div'); ov.className = 'thm-ov tk-ov';
    ov.innerHTML = '<div class="thm-box tk-box"><div class="thm-hd"><h3>' + title + '</h3><button type="button" class="thm-x tk-x" aria-label="Tutup">' + ico('x', 18) + '</button></div>' + inner + '</div>';
    document.body.appendChild(ov);
    var onKey = function (e) { if (e.key === 'Escape') close(); };
    function close() { if (ov.parentNode) ov.parentNode.removeChild(ov); document.removeEventListener('keydown', onKey); }
    document.addEventListener('keydown', onKey);
    ov.addEventListener('mousedown', function (e) { if (e.target === ov) close(); });
    Array.prototype.forEach.call(ov.querySelectorAll('.tk-x'), function (b) { b.onclick = close; });
    wire(ov, close);
    return ov;
  }
  function tkSrcBox214(src, withBtn) {
    if (!src || !src.num) return '';
    var who = src.kind === 'in' ? 'Pelanggan' : (src.kind === 'manual' ? 'Admin' : 'Bot');
    return '<div class="tk-src"><div class="tk-src-h">' + ico('message-circle', 13) + ' <b>' + esc(tkSrcName214(src)) + '</b>' +
      '<span>' + who + (src.ts ? ' · ' + esc(String(src.ts).slice(0, 16)) : '') + '</span>' +
      (withBtn ? '<button type="button" class="btn ghost sm tk-go">Buka di chat</button>' : '') + '</div>' +
      '<div class="tk-src-t">' + esc(tkSnip214(src) || '(pesan)') + '</div></div>';
  }
  function tkNew214(src) {
    if (src) {
      var ada = tkS.idx[src.number + '|' + src.k];
      if (ada) { tkOpen214(ada.id); return; }
    }
    var srcView = src ? { num: src.number, k: src.k, ts: src.ts, kind: src.kind, text: src.text, mt: src.mt, mn: src.mn, name: src.name } : null;
    var snip = srcView ? tkSnip214(srcView) : '';
    var judul = snip.length > 120 ? snip.slice(0, 117) + '…' : snip;
    tkModal214('Task baru',
      tkSrcBox214(srcView, false) +
      '<div class="row"><label class="fl">Judul to-do</label><input type="text" class="tk-title" maxlength="300" placeholder="Mis. Kirim penawaran harga ke pelanggan" value="' + esc(judul) + '"></div>' +
      '<div class="tk-grid">' +
        '<div class="row"><label class="fl">Status</label><select class="tk-st">' + tkStatusOpts214('new') + '</select></div>' +
        '<div class="row"><label class="fl">Ditugaskan ke</label><select class="tk-as">' + tkUserOpts214(tkS.me) + '</select></div>' +
        '<div class="row"><label class="fl">Tenggat (opsional)</label><input type="date" class="tk-due-in"></div>' +
      '</div>' +
      '<div class="row"><label class="fl">Catatan (opsional)</label><textarea class="tk-note-in" rows="3" maxlength="2000" placeholder="Detail yang perlu dikerjakan…"></textarea></div>' +
      '<div class="tk-foot"><button type="button" class="btn ghost tk-x">Batal</button><button type="button" class="btn tk-save">' + ico('list-todo', 15) + ' Simpan task</button></div>',
      function (ov, close) {
        var ti = ov.querySelector('.tk-title'); setTimeout(function () { ti.focus(); ti.select(); }, 30);
        var go = function () {
          var title = ti.value.trim();
          if (!title) { toast('Judul to-do wajib diisi.', true); ti.focus(); return; }
          var bt = ov.querySelector('.tk-save'); bt.disabled = true;
          var body = { title: title, status: ov.querySelector('.tk-st').value, assignee: ov.querySelector('.tk-as').value,
                       due: ov.querySelector('.tk-due-in').value, note: ov.querySelector('.tk-note-in').value };
          if (src) body.src = src;
          api('task_save', { method: 'POST', body: body }).then(function (r) {
            bt.disabled = false;
            if (!r || !r.ok) { toast((r && r.error) || 'Gagal menyimpan task.', true); return; }
            close(); tkUpsert214(r.task);
            toast(r.dup ? 'Pesan ini sudah punya task — dibuka.' : 'Task dibuat — lihat di menu Task.');
            if (r.dup) tkOpen214(r.task.id);
          });
        };
        ov.querySelector('.tk-save').onclick = go;
        ti.onkeydown = function (e) { if (e.key === 'Enter') { e.preventDefault(); go(); } };
      });
  }
  function tkNotesHtml214(t) {
    var n = t.notes || [];
    if (!n.length) return '<div class="tk-empty-n">Belum ada catatan.</div>';
    return n.map(function (x) {
      return '<div class="tk-n"><div class="tk-n-h"><b>' + esc(x.by_name || x.by || '') + '</b><span>' + esc(String(x.at || '').slice(0, 16)) + '</span>' +
        (x.can_del ? '<button type="button" class="tk-n-del" data-nid="' + esc(x.id) + '" title="Hapus catatan">' + ico('trash-2', 12) + '</button>' : '') + '</div>' +
        '<div class="tk-n-t">' + esc(x.text || '') + '</div></div>';
    }).join('');
  }
  function tkLogHtml214(t) {
    var l = (t.log || []).slice(-8).reverse();
    if (!l.length) return '';
    return '<details class="tk-log"><summary>Riwayat status (' + (t.log || []).length + ')</summary>' + l.map(function (x) {
      var d = TK_ST[x.s] || { label: x.s };
      return '<div>' + esc(String(x.at || '').slice(0, 16)) + ' — <b>' + esc(d.label) + '</b> oleh ' + esc(x.by_name || x.by || '') + '</div>';
    }).join('') + '</details>';
  }
  function tkOpen214(id) {
    var t = tkS.list.filter(function (x) { return x.id === id; })[0];
    if (!t) { tkFetch214(function () { if (tkS.list.some(function (x) { return x.id === id; })) tkOpen214(id); else toast('Task tidak ditemukan.', true); }); return; }
    tkModal214('Detail task',
      '<div class="row"><label class="fl">Judul to-do</label><input type="text" class="tk-title" maxlength="300" value="' + esc(t.title) + '"></div>' +
      '<div class="tk-grid">' +
        '<div class="row"><label class="fl">Status</label><select class="tk-st">' + tkStatusOpts214(t.status) + '</select></div>' +
        '<div class="row"><label class="fl">Ditugaskan ke</label><select class="tk-as">' + tkUserOpts214(t.assignee) + '</select></div>' +
        '<div class="row"><label class="fl">Tenggat</label><input type="date" class="tk-due-in" value="' + esc(t.due || '') + '"></div>' +
      '</div>' +
      tkSrcBox214(t.src, true) +
      '<div class="tk-sec">' + ico('sticky-note', 14) + ' Catatan <span class="tk-nc">' + (t.notes || []).length + '</span></div>' +
      '<div class="tk-notes">' + tkNotesHtml214(t) + '</div>' +
      '<div class="tk-add"><textarea class="tk-note-in" rows="2" maxlength="2000" placeholder="Tulis catatan… (Ctrl+Enter untuk kirim)"></textarea><button type="button" class="btn ghost sm tk-note-add">' + ico('plus', 14) + ' Tambah</button></div>' +
      tkLogHtml214(t) +
      '<div class="tk-meta">Dibuat ' + esc(String(t.created_at || '').slice(0, 16)) + ' oleh ' + esc(t.by_name || t.by || '') +
        (t.updated_at && t.updated_at !== t.created_at ? ' · diubah ' + esc(String(t.updated_at).slice(0, 16)) + (t.updated_by_name ? ' oleh ' + esc(t.updated_by_name) : '') : '') + '</div>' +
      '<div class="tk-foot">' + (t.can_del ? '<button type="button" class="btn danger sm tk-del" style="margin-right:auto">' + ico('trash-2', 14) + ' Hapus task</button>' : '') +
        '<button type="button" class="btn ghost tk-x">Tutup</button><button type="button" class="btn tk-save">Simpan</button></div>',
      function (ov, close) {
        var cur = t;
        var go = ov.querySelector('.tk-go');
        if (go) go.onclick = function () { close(); tkGoChat214(cur); };
        ov.querySelector('.tk-save').onclick = function () {
          var title = ov.querySelector('.tk-title').value.trim();
          if (!title) { toast('Judul to-do wajib diisi.', true); return; }
          var bt = this; bt.disabled = true;
          api('task_save', { method: 'POST', body: { id: cur.id, title: title, status: ov.querySelector('.tk-st').value,
            assignee: ov.querySelector('.tk-as').value, due: ov.querySelector('.tk-due-in').value } }).then(function (r) {
            bt.disabled = false;
            if (!r || !r.ok) { toast((r && r.error) || 'Gagal menyimpan.', true); return; }
            tkUpsert214(r.task); close(); toast('Task disimpan.');
          });
        };
        var ta = ov.querySelector('.tk-note-in');
        function paintNotes() {
          ov.querySelector('.tk-notes').innerHTML = tkNotesHtml214(cur);
          ov.querySelector('.tk-nc').textContent = (cur.notes || []).length;
        }
        var addNote = function () {
          var v = ta.value.trim(); if (!v) { ta.focus(); return; }
          var bt = ov.querySelector('.tk-note-add'); bt.disabled = true;
          api('task_note', { method: 'POST', body: { id: cur.id, text: v } }).then(function (r) {
            bt.disabled = false;
            if (!r || !r.ok) { toast((r && r.error) || 'Gagal menambah catatan.', true); return; }
            ta.value = ''; cur = r.task; tkUpsert214(cur); paintNotes();
          });
        };
        ov.querySelector('.tk-note-add').onclick = addNote;
        ta.onkeydown = function (e) { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); addNote(); } };
        ov.querySelector('.tk-notes').addEventListener('click', function (e) {
          var b = e.target.closest ? e.target.closest('.tk-n-del') : null; if (!b) return;
          if (!confirm('Hapus catatan ini?')) return;
          api('task_note', { method: 'POST', body: { id: cur.id, note_id: b.getAttribute('data-nid'), remove: 1 } }).then(function (r) {
            if (!r || !r.ok) { toast((r && r.error) || 'Gagal menghapus catatan.', true); return; }
            cur = r.task; tkUpsert214(cur); paintNotes();
          });
        });
        var del = ov.querySelector('.tk-del');
        if (del) del.onclick = function () {
          if (!confirm('Hapus task "' + cur.title + '"?\n\nTask beserta catatannya hilang permanen. Pesan chat-nya tidak terhapus.')) return;
          api('task_delete', { method: 'POST', body: { id: cur.id } }).then(function (r) {
            if (!r || !r.ok) { toast((r && r.error) || 'Gagal menghapus task.', true); return; }
            close(); tkRemove214(cur.id); toast('Task dihapus.');
          });
        };
      });
  }
  function tkGoChat214(t) {
    if (!t || !t.src || !t.src.num) return;
    var wasLoaded = !!loaded.wachat;
    showTab('wachat');
    setTimeout(function () {
      try { if (t.src.ts) waJumpTs164(String(t.src.num), t.src.ts, t.src.k); else selectWaConv(String(t.src.num)); } catch (e) {}
    }, wasLoaded ? 0 : 700);
  }
  function tkSaveQuick214(id, body) {
    body.id = id;
    api('task_save', { method: 'POST', body: body }).then(function (r) {
      if (!r || !r.ok) { toast((r && r.error) || 'Gagal menyimpan.', true); tkFetch214(tkRender214); return; }
      tkUpsert214(r.task);
    });
  }

  // ---- menu Task (kanban) ----
  function loadTasks214() {
    if (!tkS.wired) {
      tkS.wired = true;
      $$('[data-tk-f]').forEach(function (b) {
        b.onclick = function () {
          tkS.filter = b.dataset.tkF;
          try { localStorage.setItem('dei_task_flt', tkS.filter); } catch (e) {}
          tkRender214();
        };
      });
      var qt = null;
      if ($('#tkQ')) $('#tkQ').oninput = function () { var v = this.value; clearTimeout(qt); qt = setTimeout(function () { tkS.q = v.trim().toLowerCase(); tkRender214(); }, 200); };
      if ($('#tkNewBtn')) $('#tkNewBtn').onclick = function () { tkNew214(null); };
      if ($('#tkReload')) $('#tkReload').onclick = function () { tkFetch214(tkRender214); };
    }
    if (!tkS.loaded && $('#taskBoard')) $('#taskBoard').innerHTML = '<div class="card" style="text-align:center;color:var(--muted)">Memuat task…</div>';
    tkFetch214(tkRender214);
  }
  function tkMatch214(t) {
    if (tkS.filter === 'mine' && t.assignee !== tkS.me) return false;
    if (tkS.filter === 'byme' && t.by !== tkS.me) return false;
    if (!tkS.q) return true;
    var hay = [t.title, t.src && t.src.name, t.src && t.src.num, t.src && t.src.text, tkUserName214(t.assignee)]
      .concat((t.notes || []).map(function (n) { return n.text; })).join(' ').toLowerCase();
    return hay.indexOf(tkS.q) !== -1;
  }
  function tkRender214() {
    var box = $('#taskBoard'); if (!box) return;
    $$('[data-tk-f]').forEach(function (b) { b.classList.toggle('active', b.dataset.tkF === tkS.filter); });
    var list = tkS.list.filter(tkMatch214);
    if (!tkS.list.length) {
      box.innerHTML = '<div class="card" style="text-align:center;color:var(--muted);line-height:1.6">Belum ada task.<br>Buka <b>Percakapan WA</b>, lalu klik <b>' + ico('list-todo', 13) + ' To-do</b> di bawah bubble pesan untuk menjadikannya task — atau klik <b>+ Task baru</b>.</div>';
      return;
    }
    var cols = Object.keys(TK_ST), by = {};
    cols.forEach(function (k) { by[k] = []; });
    list.forEach(function (t) { (by[t.status] || by['new']).push(t); });
    cols.forEach(function (k) { by[k].sort(function (a, b) { return String(b.updated_at || '').localeCompare(String(a.updated_at || '')); }); });
    box.innerHTML = (list.length ? '' : '<div class="card" style="text-align:center;color:var(--muted)">Tidak ada task pada filter / pencarian ini.</div>') +
    '<div class="lk-board tk-board">' + cols.map(function (k) {
      var d = TK_ST[k];
      return '<div class="lk-col" data-col="' + k + '">' +
        '<div class="lk-col-h"><span class="tag" style="background:' + d.bg + ';color:' + d.fg + '">' + d.label + '</span><span class="lk-n">' + by[k].length + '</span></div>' +
        '<div class="lk-list">' + (by[k].length ? by[k].map(function (t) {
          var nn = (t.notes || []).length, last = nn ? t.notes[nn - 1] : null;
          return '<div class="lk-card tk-card" draggable="true" data-tk="' + esc(t.id) + '" title="Klik untuk detail · seret ke kolom lain untuk ganti status">' +
            '<div class="lk-t">' + esc(t.title) + '</div>' +
            (t.src && t.src.num ? '<div class="lk-s tk-from">' + ico('message-circle', 12) + ' ' + esc(tkSrcName214(t.src)) + '</div>' : '') +
            '<div class="tk-chips">' +
              '<span class="tk-as-c' + (t.assignee ? '' : ' none') + '">' + ico('user', 12) + ' ' + esc(t.assignee ? tkUserName214(t.assignee) : 'Belum ditentukan') + '</span>' +
              tkDueHtml214(t) +
              (nn ? '<span class="tk-nn" title="' + nn + ' catatan">' + ico('sticky-note', 12) + ' ' + nn + '</span>' : '') +
            '</div>' +
            (last ? '<div class="lk-note">' + esc((last.by_name || last.by || '') + ': ' + last.text) + '</div>' : '') +
            '<div class="lk-f"><select class="lk-st" aria-label="Status">' + tkStatusOpts214(t.status) + '</select>' +
              (t.src && t.src.num ? '<button type="button" class="lk-chat" title="Buka di chat">' + ico('message-circle', 14) + '</button>' : '') + '</div>' +
          '</div>';
        }).join('') : '<div class="lk-empty">Seret kartu ke sini</div>') + '</div></div>';
    }).join('') + '</div>';

    var dragId = null;
    function pindah(id, st) {
      var t = tkS.list.filter(function (x) { return x.id === id; })[0];
      if (!t || t.status === st) return;
      t.status = st; tkRender214(); tkBadge214();   // langsung pindah, server menyusul
      tkSaveQuick214(id, { status: st });
    }
    $$('#taskBoard .tk-card').forEach(function (c) {
      var id = c.dataset.tk;
      c.ondragstart = function (e) { dragId = id; c.classList.add('lk-drag'); try { e.dataTransfer.setData('text/plain', id); e.dataTransfer.effectAllowed = 'move'; } catch (er) {} };
      c.ondragend = function () { c.classList.remove('lk-drag'); $$('#taskBoard .lk-col').forEach(function (x) { x.classList.remove('lk-over'); }); };
      var sel = c.querySelector('.lk-st');
      sel.onchange = function (e) { pindah(id, e.target.value); };
      sel.onmousedown = function (e) { e.stopPropagation(); };
      sel.onclick = function (e) { e.stopPropagation(); };
      var ch = c.querySelector('.lk-chat');
      if (ch) ch.onclick = function (e) { e.stopPropagation(); tkGoChat214(tkS.list.filter(function (x) { return x.id === id; })[0]); };
      c.onclick = function () { tkOpen214(id); };
    });
    $$('#taskBoard .lk-col').forEach(function (col) {
      col.ondragover = function (e) { e.preventDefault(); col.classList.add('lk-over'); };
      col.ondragleave = function (e) { if (!col.contains(e.relatedTarget)) col.classList.remove('lk-over'); };
      col.ondrop = function (e) {
        e.preventDefault(); col.classList.remove('lk-over');
        var id = dragId; try { id = e.dataTransfer.getData('text/plain') || dragId; } catch (er) {}
        dragId = null; if (id) pindah(id, col.dataset.col);
      };
    });
  }
  // badge "task terbuka untuk saya" di menu, dimuat sekali saat dashboard dibuka
  setTimeout(function () { if (!tkS.loaded) tkFetch214(); }, 1500);

'''

ICONS_ADD = (
  "  if (!ICONS['list-todo']) ICONS['list-todo'] = '<rect x=\"3\" y=\"5\" width=\"6\" height=\"6\" rx=\"1\"/><path d=\"m3 17 2 2 4-4\"/><path d=\"M13 6h8\"/><path d=\"M13 12h8\"/><path d=\"M13 18h8\"/>';   // " + TAG + "\n"
  "  if (!ICONS['sticky-note']) ICONS['sticky-note'] = '<path d=\"M16 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V8Z\"/><path d=\"M15 3v4a2 2 0 0 0 2 2h4\"/>';\n"
  "  if (!ICONS.calendar) ICONS.calendar = '<path d=\"M8 2v4\"/><path d=\"M16 2v4\"/><rect width=\"18\" height=\"18\" x=\"3\" y=\"4\" rx=\"2\"/><path d=\"M3 10h18\"/>';\n"
  "  if (!ICONS.plus) ICONS.plus = '<path d=\"M5 12h14\"/><path d=\"M12 5v14\"/>';\n")

HELP_ADD = r'''    { id: 'task', roles: R_ALL, t: 'Membuat to-do (Task) dari bubble chat & kanban Task', k: 'task tugas todo to-do to do kanban pekerjaan catatan notes note bubble pesan new progress pending done closed tenggat deadline',   // v1.2.214: task
      s: ['Di <b>Percakapan WA</b>, klik <b>To-do</b> di bawah bubble pesan. Isi judul, status, ditugaskan ke, tenggat, dan catatan, lalu Simpan.', 'Buka menu <b>Task</b>: kanban New, On Progress, Pending, Done, Closed. Seret kartu (atau ganti dropdown di kartu) untuk mengubah status.', 'Klik kartu untuk detail: tambah catatan, ganti penanggung jawab, atau <b>Buka di chat</b> untuk melompat ke pesan asalnya.'],
      show: [{ tab: 'tasks', el: '#panel-tasks .card', title: 'Task', body: '<p>Saring <b>Tugas saya</b> / <b>Saya buat</b>, cari, atau klik <b>+ Task baru</b>. Papan kanban ada di bawah.</p>' }] },
'''

j = open(JS, encoding='utf-8').read()
if TAG not in j:
    j = rep(j, "  // Expose for inline replacement of static markup\n  window._ico = ico;",
               ICONS_ADD + "  // Expose for inline replacement of static markup\n  window._ico = ico;", what='js-ikon')
    j = rep(j, "    leads: loadLeads,\n", "    leads: loadLeads,\n    tasks: loadTasks214,   // " + TAG + "\n", what='js-loader')
    j = rep(j, "    else if (tab === 'qrtpl' && qrtplRefresh) qrtplRefresh();   // v1.2.199: template-menu\n",
               "    else if (tab === 'qrtpl' && qrtplRefresh) qrtplRefresh();   // v1.2.199: template-menu\n"
               "    else if (tab === 'tasks') tkFetch214(tkRender214);   // " + TAG + "\n", what='js-showtab')
    j = rep(j, "+ rb + sb164 + ma200 + '</div></div>';", "+ rb + sb164 + waTaskBtn214(rq) /* " + TAG + " */ + ma200 + '</div></div>';", what='js-bubble')
    j = rep(j, "    waCs164Init();   // v1.2.164: cari-simpan\n", "    waCs164Init();   // v1.2.164: cari-simpan\n    tk214WaInit();   // " + TAG + "\n", what='js-wainit')
    j = rep(j, "  // v1.2.147: leads-kanban — pilihan tampilan diingat per browser\n", JSLIB + "  // v1.2.147: leads-kanban — pilihan tampilan diingat per browser\n", what='js-lib')
    j = rep(j, "    { id: 'kontak', roles: R_ALL,", HELP_ADD + "    { id: 'kontak', roles: R_ALL,", what='js-help')
    save(JS, j)

# ======================= dashboard: index.html =======================
CSS = r'''
  /* v1.2.214: task */
  .wa-tk{color:inherit;opacity:.8;text-decoration:none;margin-left:8px;display:inline-flex;align-items:center;gap:2px;vertical-align:-2px}
  .wa-tk.on{opacity:1;font-weight:600}
  #nav .tk-nb{margin-left:auto;background:#dc2626;color:#fff;font-size:11px;font-weight:700;border-radius:10px;padding:0 7px;line-height:18px}
  #panel-tasks [data-tk-f].active{background:var(--brand);color:#fff;border-color:var(--brand)}
  #tkQ{border:1px solid var(--line);border-radius:8px;padding:7px 10px;font:inherit;font-size:13px;background:#fff;color:var(--ink)}
  #tkQ:focus{outline:none;border-color:var(--brand)}
  .tk-card{cursor:pointer}
  .tk-card .tk-from{display:flex;align-items:center;gap:4px;margin-top:3px}
  .tk-chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:7px}
  .tk-chips>span{display:inline-flex;align-items:center;gap:3px;font-size:11.5px;background:#f3f4f8;border-radius:6px;padding:2px 7px;color:#3b3b55}
  .tk-chips .tk-as-c.none{color:var(--muted)}
  .tk-chips .tk-due.late{background:#fee2e2;color:#b91c1c;font-weight:600}
  .tk-box{max-width:620px}
  .tk-box .row{margin-bottom:10px}
  .tk-box input[type=text],.tk-box textarea,.tk-box select,.tk-box input[type=date]{width:100%}
  .tk-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
  @media(max-width:640px){.tk-grid{grid-template-columns:1fr}}
  .tk-src{background:var(--brand-soft);border-radius:10px;padding:9px 11px;margin:4px 0 12px;font-size:13px}
  .tk-src-h{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
  .tk-src-h span{color:var(--muted);font-size:12px}
  .tk-src-h .tk-go{margin-left:auto}
  .tk-src-t{margin-top:5px;white-space:pre-wrap;max-height:120px;overflow:auto;line-height:1.45}
  .tk-sec{display:flex;align-items:center;gap:6px;font-weight:700;font-size:13.5px;margin:6px 0}
  .tk-sec .tk-nc{font-weight:600;color:var(--muted);font-size:12px;background:#f3f4f8;border-radius:10px;padding:0 7px}
  .tk-notes{display:flex;flex-direction:column;gap:6px;max-height:240px;overflow:auto}
  .tk-n{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:7px 9px;font-size:13px}
  .tk-n-h{display:flex;align-items:center;gap:8px;font-size:12px}
  .tk-n-h span{color:var(--muted)}
  .tk-n-del{margin-left:auto;border:0;background:transparent;color:#b91c1c;cursor:pointer;display:inline-flex;padding:2px}
  .tk-n-t{white-space:pre-wrap;margin-top:3px;line-height:1.45}
  .tk-empty-n{color:var(--muted);font-size:12.5px;padding:4px 2px}
  .tk-add{display:flex;gap:8px;align-items:flex-end;margin-top:8px}
  .tk-add textarea{flex:1}
  .tk-log{margin-top:10px;font-size:12px;color:var(--muted)}
  .tk-log summary{cursor:pointer}
  .tk-log div{padding:2px 0}
  .tk-meta{margin-top:10px;font-size:11.5px;color:var(--muted)}
  .tk-foot{display:flex;justify-content:flex-end;gap:8px;margin-top:14px;flex-wrap:wrap}
'''
NAV = '      <button data-tab="tasks"    data-role="super_admin,admin,supervisor,wa_agent" data-icon="list-todo"><span class="ic"></span> Task</button><!-- ' + TAG + ' -->\n'
PANEL = '''    <!-- TASK (''' + TAG + ''') -->
    <section class="panel" id="panel-tasks">
      <div class="ph"><h2>Task</h2><p>To-do tim dari bubble chat WhatsApp atau dibuat manual. Seret kartu untuk mengubah status, klik kartu untuk catatan &amp; detail.</p></div>
      <div class="card">
        <div class="toolbar" style="margin-bottom:0;flex-wrap:wrap">
          <button class="btn ghost sm" data-tk-f="all">Semua</button>
          <button class="btn ghost sm" data-tk-f="mine">Tugas saya</button>
          <button class="btn ghost sm" data-tk-f="byme">Saya buat</button>
          <input type="search" id="tkQ" placeholder="Cari task, pelanggan, catatan…" autocomplete="off" style="width:auto;flex:1;min-width:160px;max-width:320px">
          <button class="btn ghost sm" id="tkReload" style="margin-left:auto">&#8635; Muat ulang</button>
          <button class="btn sm" id="tkNewBtn">+ Task baru</button>
        </div>
      </div>
      <div id="taskBoard"></div>
    </section>

'''
h = open(HT, encoding='utf-8').read()
if TAG not in h:
    h = rep(h, '  .lk-empty{', CSS + '  .lk-empty{', what='html-css')
    h = rep(h, '      <button data-tab="kontak"   data-role="super_admin,admin,supervisor,wa_agent" data-icon="users">', NAV + '      <button data-tab="kontak"   data-role="super_admin,admin,supervisor,wa_agent" data-icon="users">', what='html-nav')
    h = rep(h, '    <!-- KONTAK (v1.2.39) -->\n', PANEL + '    <!-- KONTAK (v1.2.39) -->\n', what='html-panel')
    h = rep(h, '<script src="app.js?v=1.2.213"></script>', '<script src="app.js?v=1.2.214"></script><!-- ' + TAG + ' -->', what='html-ver')
    save(HT, h)

# ======================= api =======================
LIB = r'''
/* v1.2.214: task — to-do dari bubble chat + menu Task (kanban) + catatan.
 * data/tasks.json = {id: {id, title, status, assignee, due, src:{num,k,ts,kind,text,mt,mn}|null,
 *                         notes:[{id,by,by_name,at,text}], log:[{at,by,by_name,s}], by, by_name,
 *                         created_at, updated_at, updated_by, updated_by_name}} */
if (!defined('TASKS_FILE')) define('TASKS_FILE', DATA_DIR . '/tasks.json');
if (!defined('TASKS_MAX')) define('TASKS_MAX', 5000);
if (!defined('TASK_NOTES_MAX')) define('TASK_NOTES_MAX', 300);
function tkStatuses214() { return ['new', 'progress', 'pending', 'done', 'closed']; }
function tkAll214() { $a = readJson(TASKS_FILE, []); return is_array($a) ? $a : []; }
function tkClean214($s, $max) { return mb_substr(trim((string)preg_replace('/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/u', '', (string)$s)), 0, $max); }
function tkCanSee214($u, $t) {
    $me = (string)($u['username'] ?? '');
    if (($t['by'] ?? '') === $me || ($t['assignee'] ?? '') === $me) return true;
    $n = (string)($t['src']['num'] ?? '');
    return $n === '' || deiCanSeeNum164($u, $n);
}
function tkCanDel214($u, $t) { return deiIsLead($u['role'] ?? '') || ($t['by'] ?? '') === ($u['username'] ?? ''); }
function tkUserNames214() {
    static $m = null;
    if ($m === null) { $m = []; foreach ((array)readJson(USERS_FILE, []) as $x) { if (is_array($x) && !empty($x['username'])) $m[$x['username']] = (string)($x['name'] ?? $x['username']); } }
    return $m;
}
function tkPublic214($u, $t) {
    static $names = [];
    $n = (string)($t['src']['num'] ?? '');
    if ($n !== '') {
        if (!isset($names[$n])) { try { $names[$n] = (string)waContactName($n); } catch (\Throwable $e) { $names[$n] = ''; } }
        $t['src']['name'] = $names[$n];
    } else $t['src'] = null;
    $me = (string)($u['username'] ?? ''); $lead = deiIsLead($u['role'] ?? '');
    $t['notes'] = array_map(function ($x) use ($me, $lead) { $x['can_del'] = $lead || ($x['by'] ?? '') === $me; return $x; }, array_values((array)($t['notes'] ?? [])));
    $t['log'] = array_values((array)($t['log'] ?? []));
    $t['can_del'] = tkCanDel214($u, $t);
    return $t;
}
function tkList214($u) {
    $out = [];
    foreach (tkAll214() as $t) { if (is_array($t) && tkCanSee214($u, $t)) $out[] = tkPublic214($u, $t); }
    usort($out, function ($a, $b) { return strcmp((string)($b['updated_at'] ?? ''), (string)($a['updated_at'] ?? '')); });
    return $out;
}
function tkMe214($u) { $m = tkUserNames214(); $un = (string)($u['username'] ?? ''); return [$un, $m[$un] ?? (string)($u['name'] ?? $un)]; }
'''

CASES = r'''    /* ---------- v1.2.214: task ---------- */
    case 'tasks_list': {
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        $users = array_map(function ($x) { return ['username' => $x['username'], 'name' => $x['name'], 'role' => $x['role']]; }, deiAssignableUsers(null));
        jsonOut(['ok' => true, 'tasks' => tkList214($u), 'users' => $users, 'me' => (string)($u['username'] ?? ''), 'statuses' => tkStatuses214()]);
        break;
    }
    case 'task_save': {   // body: id? (kosong = baru), title, status, assignee, due (Y-m-d), note (baru saja), src {number,k,ts,kind,text,mt,mn} (baru saja)
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        $in = bodyInput();
        $id = preg_replace('/[^a-z0-9]/', '', (string)($in['id'] ?? ''));
        $src = null;
        if ($id === '' && is_array($in['src'] ?? null)) {
            $sn = waNormNum($in['src']['number'] ?? '');
            $sk = mb_substr(preg_replace('/[\x00-\x1f]/', '', (string)($in['src']['k'] ?? '')), 0, 200);
            if ($sn !== '' && $sk !== '') {
                deiGuardAgentPrivate($u, $sn);
                $kind = in_array(($in['src']['kind'] ?? ''), ['in', 'bot', 'manual'], true) ? $in['src']['kind'] : 'in';
                $src = ['num' => $sn, 'k' => $sk, 'ts' => mb_substr((string)($in['src']['ts'] ?? ''), 0, 19), 'kind' => $kind,
                        'text' => tkClean214($in['src']['text'] ?? '', 2000),
                        'mt' => mb_substr(preg_replace('/[^a-z]/', '', (string)($in['src']['mt'] ?? '')), 0, 12),
                        'mn' => tkClean214($in['src']['mn'] ?? '', 120)];
            }
        }
        $validUsers = tkUserNames214();
        [$me, $meName] = tkMe214($u);
        $r = deiWithLock('tasks', function () use ($u, $in, $id, $src, $validUsers, $me, $meName) {
            $all = tkAll214();
            $now = date('Y-m-d H:i:s');
            $isNew = $id === '';
            if (!$isNew) {
                if (!isset($all[$id]) || !is_array($all[$id])) return 'Task tidak ditemukan.';
                $t = $all[$id];
                if (!tkCanSee214($u, $t)) return 'Anda tidak bisa mengubah task ini.';
            } else {
                if ($src) foreach ($all as $x) {
                    if (is_array($x) && ($x['src']['num'] ?? '') === $src['num'] && ($x['src']['k'] ?? '') === $src['k']) return ['task' => $x, 'dup' => true];
                }
                if (count($all) >= TASKS_MAX) return 'Batas ' . TASKS_MAX . ' task tercapai. Hapus task lama yang sudah Closed dulu.';
                do { $nid = 't' . bin2hex(random_bytes(6)); } while (isset($all[$nid]));
                $t = ['id' => $nid, 'title' => '', 'status' => 'new', 'assignee' => '', 'due' => '', 'src' => $src, 'notes' => [], 'log' => [],
                      'by' => $me, 'by_name' => $meName, 'created_at' => $now];
            }
            if ($isNew || array_key_exists('title', $in)) {
                $ti = tkClean214(preg_replace('/\s+/u', ' ', (string)($in['title'] ?? '')), 300);
                if ($ti === '') return 'Judul to-do wajib diisi.';
                $t['title'] = $ti;
            }
            $prev = $isNew ? '' : (string)($t['status'] ?? 'new');
            if (array_key_exists('status', $in) || $isNew) {
                $st = (string)($in['status'] ?? 'new');
                if (!in_array($st, tkStatuses214(), true)) return 'Status tidak dikenal.';
                $t['status'] = $st;
            }
            if ($t['status'] !== $prev) {
                $t['status_at'] = $now;
                $t['log'] = array_slice(array_merge((array)($t['log'] ?? []), [['at' => $now, 'by' => $me, 'by_name' => $meName, 's' => $t['status']]]), -50);
            }
            if (array_key_exists('assignee', $in)) {
                $as = (string)$in['assignee'];
                if ($as !== '' && !isset($validUsers[$as]) && $as !== ($t['assignee'] ?? '')) return 'Pengguna yang ditugaskan tidak ditemukan.';
                $t['assignee'] = $as;
            }
            if (array_key_exists('due', $in)) {
                $du = (string)$in['due'];
                if ($du !== '' && !preg_match('/^\d{4}-\d{2}-\d{2}$/', $du)) return 'Format tenggat tidak valid.';
                $t['due'] = $du;
            }
            if ($isNew) {
                $nt = tkClean214($in['note'] ?? '', 2000);
                if ($nt !== '') $t['notes'][] = ['id' => 'n' . bin2hex(random_bytes(4)), 'by' => $me, 'by_name' => $meName, 'at' => $now, 'text' => $nt];
            }
            $t['updated_at'] = $now; $t['updated_by'] = $me; $t['updated_by_name'] = $meName;
            $all[$t['id']] = $t;
            writeJson(TASKS_FILE, $all);
            return ['task' => $t, 'dup' => false];
        });
        if (!is_array($r)) jsonOut(['ok' => false, 'error' => (string)$r], 400);
        jsonOut(['ok' => true, 'task' => tkPublic214($u, $r['task']), 'dup' => $r['dup']]);
        break;
    }
    case 'task_note': {   // body: id, text  |  id, note_id, remove=1
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        $in = bodyInput();
        $id = preg_replace('/[^a-z0-9]/', '', (string)($in['id'] ?? ''));
        $rm = !empty($in['remove']); $nid = preg_replace('/[^a-z0-9]/', '', (string)($in['note_id'] ?? ''));
        $text = tkClean214($in['text'] ?? '', 2000);
        if ($id === '' || ($rm ? $nid === '' : $text === '')) jsonOut(['ok' => false, 'error' => $rm ? 'note_id wajib' : 'Catatan kosong.'], 400);
        [$me, $meName] = tkMe214($u);
        $r = deiWithLock('tasks', function () use ($u, $id, $rm, $nid, $text, $me, $meName) {
            $all = tkAll214();
            if (!isset($all[$id]) || !is_array($all[$id])) return 'Task tidak ditemukan.';
            $t = $all[$id];
            if (!tkCanSee214($u, $t)) return 'Anda tidak bisa mengubah task ini.';
            $notes = array_values((array)($t['notes'] ?? []));
            $now = date('Y-m-d H:i:s');
            if ($rm) {
                $hit = false;
                foreach ($notes as $i => $x) {
                    if (($x['id'] ?? '') !== $nid) continue;
                    if (($x['by'] ?? '') !== $me && !deiIsLead($u['role'] ?? '')) return 'Hanya penulis atau Admin/Supervisor yang bisa menghapus catatan ini.';
                    unset($notes[$i]); $hit = true;
                }
                if (!$hit) return 'Catatan tidak ditemukan.';
            } else {
                if (count($notes) >= TASK_NOTES_MAX) return 'Batas ' . TASK_NOTES_MAX . ' catatan per task tercapai.';
                $notes[] = ['id' => 'n' . bin2hex(random_bytes(4)), 'by' => $me, 'by_name' => $meName, 'at' => $now, 'text' => $text];
            }
            $t['notes'] = array_values($notes);
            $t['updated_at'] = $now; $t['updated_by'] = $me; $t['updated_by_name'] = $meName;
            $all[$id] = $t;
            writeJson(TASKS_FILE, $all);
            return ['task' => $t];
        });
        if (!is_array($r)) jsonOut(['ok' => false, 'error' => (string)$r], 400);
        jsonOut(['ok' => true, 'task' => tkPublic214($u, $r['task'])]);
        break;
    }
    case 'task_delete': {   // pembuat task, Admin, atau Supervisor
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        $id = preg_replace('/[^a-z0-9]/', '', (string)(bodyInput()['id'] ?? ''));
        if ($id === '') jsonOut(['ok' => false, 'error' => 'id wajib'], 400);
        $r = deiWithLock('tasks', function () use ($u, $id) {
            $all = tkAll214();
            if (!isset($all[$id]) || !is_array($all[$id])) return 'Task tidak ditemukan.';
            if (!tkCanSee214($u, $all[$id]) || !tkCanDel214($u, $all[$id])) return 'Hanya pembuat task atau Admin/Supervisor yang bisa menghapus.';
            unset($all[$id]);
            writeJson(TASKS_FILE, $all ?: new \stdClass());
            return true;
        });
        if ($r !== true) jsonOut(['ok' => false, 'error' => (string)$r], 400);
        jsonOut(['ok' => true]);
        break;
    }

'''

s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API); sys.exit(0)
assert NEED in s, 'butuh v1.2.213 dulu'
s = rep(s, "define('DEI_VERSION', 'v1.2.213');   // v1.2.213:",
        "define('DEI_VERSION', 'v1.2.214');   // " + TAG + " — bubble chat jadi to-do, menu Task kanban (New/On Progress/Pending/Done/Closed) + catatan; v1.2.213:", what='versi')
s = rep(s, "\nfunction deiGuardAgentPrivate($u, $num) {", LIB + "function deiGuardAgentPrivate($u, $num) {", what='lib')
s = rep(s, "    /* ---------- ADMIN: take over / return to bot ---------- */", CASES + "    /* ---------- ADMIN: take over / return to bot ---------- */", what='cases')
save(API, s)
