#!/usr/bin/env python3
"""v1.2.164 cari-simpan: cari pesan (di dalam chat & di semua chat) + simpan pesan per bubble. Idempoten.
Pakai: python3 patch_v12164.py [~/Herd/dei-tenant]"""
import sys, os, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.164: cari-simpan'
stamp = time.strftime('%Y%m%d-%H%M%S')

def patch(rel, reps):
    p = T + '/' + rel
    s = open(p, encoding='utf-8').read()
    if TAG in s:
        print('sudah:', rel); return
    for a, b in reps:
        n = s.count(a)
        assert n == 1, (rel, n, a[:90])
        s = s.replace(a, b)
    shutil.copy2(p, p + '.bak-v12164-' + stamp)
    open(p, 'w', encoding='utf-8').write(s)
    print('patched:', rel)

# ---------------- API ----------------
PHP_FN = r'''/* ---------- v1.2.164: cari-simpan — cari pesan & simpan bubble ---------- */
define('WA_SAVED_FILE', DATA_DIR . '/wa-saved.json');
define('WA_SAVED_MAX', 500);
function deiCanSeeNum164($u, $num) {   // aturan sama dengan deiGuardAgentPrivate/deiGuardSpvScope, tapi mengembalikan bool
    $r = $u['role'] ?? '';
    if ($r === 'supervisor') {
        $cl = waClaimGet($num);
        return deiSpvSeesOwner(deiSpvScope($u), (string)($cl['agent_username'] ?? ''));
    }
    if ($r !== 'wa_agent') return true;
    static $priv = null;
    if ($priv === null) $priv = !empty(deiTeamConf(getSettings())['agent_private']);
    if (!$priv) return true;
    $cl = waClaimGet($num);
    if (!$cl) return true;
    $me = (string)($u['username'] ?? '');
    return ($cl['agent_username'] ?? '') === $me || ($cl['takeover_request']['requester'] ?? '') === $me;
}
function waSnip164($t, $q) {
    $t = trim(preg_replace('/\s+/u', ' ', (string)$t));
    $i = $q !== '' ? mb_stripos($t, $q) : false;
    if ($i === false || $i < 50) return mb_strlen($t) > 160 ? mb_substr($t, 0, 157) . '…' : $t;
    $st = $i - 40;
    return '…' . mb_substr($t, $st, 150) . (mb_strlen($t) > $st + 150 ? '…' : '');
}
/* $num kosong = semua chat (maks 60 hasil terbaru); $ts diisi = cari posisi entri itu saja */
function waMsgSearch164($u, $num, $q, $ts) {
    $logs = logReadAll();
    $hits = []; $pos = []; $ok = []; $names = []; $cut = false;
    $max = $num !== '' ? 300 : 60;
    foreach ($logs as $e) {   // log: terbaru dulu — urutan & posisi sama dengan wa_thread
        if (($e['channel'] ?? '') !== 'whatsapp') continue;
        $n = waNormNum($e['ip'] ?? '');
        if ($n === '' || ($num !== '' && $n !== $num)) continue;
        $p = $pos[$n] = isset($pos[$n]) ? $pos[$n] + 1 : 0;
        $ets = (string)($e['ts'] ?? '');
        if ($ts !== '') { if ($ets === $ts) return ['pos' => $p]; continue; }
        if (!isset($ok[$n])) $ok[$n] = deiCanSeeNum164($u, $n);
        if (!$ok[$n]) continue;
        foreach (['q', 'a'] as $kd) {
            $t = (string)($e[$kd] ?? '');
            if ($t === '' || mb_stripos($t, $q) === false) continue;
            if ($kd === 'a' && !empty($e['media_out']) && preg_match('/^\[Foto/', $t)) continue;   // bubble ini tidak ditampilkan di thread
            $oid = (string)(($e['out_id'] ?? '') ?: (($e['a_wamid'] ?? '') ?: ($e['echo_id'] ?? '')));
            $h = ['num' => $n, 'pos' => $p, 'ts' => $ets,
                  'kind' => $kd === 'q' ? 'in' : ((($e['dir'] ?? '') === 'manual') ? 'manual' : 'bot'),
                  'k' => $kd === 'q' ? 'q' . $ets . (string)($e['wamid'] ?? '') : 'a' . $ets . $oid,
                  'snip' => waSnip164($t, $q)];
            if ($num === '') { if (!isset($names[$n])) $names[$n] = waContactName($n); $h['name'] = $names[$n]; }
            $hits[] = $h;
            if (count($hits) >= $max) { $cut = true; break 2; }
        }
    }
    if ($ts !== '') return ['pos' => -1];
    if ($num !== '') $hits = array_reverse($hits);   // di dalam chat: lama → baru
    return ['hits' => $hits, 'more' => $cut];
}
function waSavedItems164($u) {
    $all = readJson(WA_SAVED_FILE, []);
    $me = (string)($u['username'] ?? '');
    $l = (is_array($all) && is_array($all[$me] ?? null)) ? $all[$me] : [];
    $out = []; $names = [];
    foreach ($l as $x) {
        $n = (string)($x['num'] ?? '');
        if ($n === '' || !deiCanSeeNum164($u, $n)) continue;
        if (!isset($names[$n])) $names[$n] = waContactName($n);
        $x['name'] = $names[$n];
        $out[] = $x;
    }
    usort($out, function ($a, $b) { return strcmp((string)($b['at'] ?? ''), (string)($a['at'] ?? '')); });
    return $out;
}
'''
PHP_CASE = r'''    /* ---------- v1.2.164: cari-simpan ---------- */
    case 'wa_msg_search': {
        $u = requireAuth(['super_admin','admin','wa_agent']);
        $num = waNormNum($_GET['number'] ?? '');
        $q = trim(preg_replace('/\s+/u', ' ', (string)($_GET['q'] ?? '')));
        $ts = trim((string)($_GET['ts'] ?? ''));
        if ($num !== '') deiGuardAgentPrivate($u, $num);
        if ($ts !== '' && $num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        if ($ts === '' && mb_strlen($q) < ($num !== '' ? 2 : 3)) jsonOut(['ok' => true, 'hits' => [], 'more' => false]);
        jsonOut(['ok' => true] + waMsgSearch164($u, $num, mb_substr($q, 0, 100), $ts));
        break;
    }
    case 'wa_saved_list': {
        $u = requireAuth(['super_admin','admin','wa_agent']);
        jsonOut(['ok' => true, 'items' => waSavedItems164($u), 'max' => WA_SAVED_MAX]);
        break;
    }
    case 'wa_saved_toggle': {   // simpan pesan per bubble — per pengguna; body: number, k, ts, kind, text, mt, mn | remove=1
        $u = requireAuth(['super_admin','admin','wa_agent']);
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        $k = mb_substr(preg_replace('/[\x00-\x1f]/', '', (string)($in['k'] ?? '')), 0, 200);
        if ($num === '' || $k === '') jsonOut(['ok' => false, 'error' => 'number & k wajib'], 400);
        $rm = !empty($in['remove']);
        if (!$rm) deiGuardAgentPrivate($u, $num);
        $me = (string)($u['username'] ?? '');
        $id = substr(sha1($num . '|' . $k), 0, 16);
        $r = deiWithLock('wa-saved', function () use ($me, $id, $num, $k, $in, $rm) {
            $all = readJson(WA_SAVED_FILE, []);
            if (!is_array($all)) $all = [];
            $l = is_array($all[$me] ?? null) ? $all[$me] : [];
            $had = false;
            foreach ($l as $i => $x) { if (($x['id'] ?? '') === $id) { unset($l[$i]); $had = true; } }
            $saved = false;
            if (!$had && !$rm) {
                if (count($l) >= WA_SAVED_MAX) return 'Batas ' . WA_SAVED_MAX . ' pesan tersimpan tercapai. Hapus yang tidak perlu dulu.';
                $kind = in_array(($in['kind'] ?? ''), ['in', 'bot', 'manual'], true) ? $in['kind'] : 'in';
                $l[] = ['id' => $id, 'num' => $num, 'k' => $k, 'ts' => mb_substr((string)($in['ts'] ?? ''), 0, 19), 'kind' => $kind,
                        'text' => mb_substr((string)($in['text'] ?? ''), 0, 2000),
                        'mt' => mb_substr(preg_replace('/[^a-z]/', '', (string)($in['mt'] ?? '')), 0, 12),
                        'mn' => mb_substr((string)($in['mn'] ?? ''), 0, 120),
                        'at' => date('Y-m-d H:i:s')];
                $saved = true;
            }
            $all[$me] = array_values($l);
            if (!$all[$me]) unset($all[$me]);
            writeJson(WA_SAVED_FILE, $all);
            return ['saved' => $saved];
        });
        if (!is_array($r)) jsonOut(['ok' => false, 'error' => (string)$r], 400);
        jsonOut(['ok' => true, 'saved' => $r['saved'], 'items' => waSavedItems164($u)]);
        break;
    }

    /* ---------- ADMIN: take over / return to bot ---------- */
    case 'wa_set_mode': {'''

patch('api/index.php', [
    ("define('DEI_VERSION', 'v1.2.163');   // v1.2.163: thread-lengkap",
     "define('DEI_VERSION', 'v1.2.164');   // " + TAG + " — cari pesan & simpan bubble; v1.2.163: thread-lengkap"),
    ("function deiGuardAgentPrivate($u, $num) {", PHP_FN + "function deiGuardAgentPrivate($u, $num) {"),
    ("    /* ---------- ADMIN: take over / return to bot ---------- */\n    case 'wa_set_mode': {", PHP_CASE),
])

# ---------------- index.html ----------------
CSS = '/* ' + TAG + ''' */
.wa-search-row{display:flex;align-items:center;gap:6px;padding:10px 12px;border-bottom:1px solid var(--line)}
.wa-search-row .wa-search{flex:1;min-width:0;padding:0;border-bottom:0}
.wa-search-row .wa-search .ic-s{left:11px}
.wa-ibtn{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:9px;border:1px solid var(--line);background:#fff;color:var(--ink);cursor:pointer;flex:none;padding:0}
.wa-ibtn:hover{border-color:var(--brand);color:var(--brand)}
.wa-ibtn.on{background:var(--brand-soft);color:var(--brand);border-color:var(--brand)}
.wa-ibtn:disabled{opacity:.4;cursor:default}
.wa-find{display:flex;align-items:center;gap:6px;padding:8px 12px;border-bottom:1px solid var(--line);background:#fff}
.wa-find input{flex:1;min-width:0;padding:7px 10px;border:1px solid var(--line);border-radius:8px;font:inherit;font-size:13.5px;outline:none}
.wa-find input:focus{border-color:var(--brand)}
.wa-find .cnt{font-size:12px;color:var(--muted);min-width:48px;text-align:center;white-space:nowrap}
mark.wa-hl{background:#fde047;color:#111;border-radius:2px;padding:0 1px}
.wa-sv{color:inherit;opacity:.8;text-decoration:none;margin-left:8px;display:inline-flex;align-items:center;gap:2px;vertical-align:-2px}
.wa-sv.on{opacity:1;font-weight:600}
.wa-sv.on svg{fill:currentColor}
.wa-gh{padding:7px 14px;font-size:11.5px;font-weight:600;color:var(--muted);background:var(--bg);border-bottom:1px solid var(--line);letter-spacing:.03em}
.wa-gmsg,.wa-svi{padding:10px 14px;border-bottom:1px solid var(--line);cursor:pointer}
.wa-gmsg:hover,.wa-svi:hover{background:var(--brand-soft)}
.wa-gm-top{display:flex;justify-content:space-between;align-items:baseline;gap:8px;font-size:13px}
.wa-gm-top b{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.wa-gm-top span{font-size:11.5px;color:var(--muted);white-space:nowrap;display:inline-flex;align-items:center;gap:4px}
.wa-gm-who{font-size:11px;color:var(--muted);margin-top:2px}
.wa-gm-tx{font-size:13px;color:var(--ink);margin-top:2px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;white-space:pre-wrap;word-break:break-word}
.wa-sv-hd{display:flex;align-items:center;gap:8px;padding:10px 14px;border-bottom:1px solid var(--line);font-size:14px}
.wa-sv-hd b{flex:1}
.wa-svx{border:0;background:transparent;color:var(--muted);cursor:pointer;padding:2px;display:inline-flex;flex:none}
.wa-svx:hover{color:#b91c1c}
@media(max-width:860px){.wa-find input{font-size:16px}}
'''
patch('dashboard/chatbot-ai/index.html', [
    ('#panel-wachat .wa-conv{display:flex;gap:10px;align-items:flex-start}',
     CSS + '#panel-wachat .wa-conv{display:flex;gap:10px;align-items:flex-start}'),
    ('<div class="wa-search"><span class="ic-s" data-ico="search" data-ico-size="16"></span><input type="search" id="waSearch" placeholder="Cari nama / nomor / pesan…" autocomplete="off"></div>',
     '<div class="wa-search-row"><div class="wa-search"><span class="ic-s" data-ico="search" data-ico-size="16"></span><input type="search" id="waSearch" placeholder="Cari nama / nomor / isi pesan…" autocomplete="off"></div>'
     '<button type="button" class="wa-ibtn" id="waSavedBtn" title="Pesan tersimpan"><span data-ico="bookmark" data-ico-size="16"></span></button></div><!-- ' + TAG + ' -->'),
    ('<div class="wachat-body" id="waThreadBody"></div>',
     '<div class="wa-find" id="waFindBar" style="display:none"></div><!-- ' + TAG + ' -->\n            <div class="wachat-body" id="waThreadBody"></div>'),
    ('<script src="app.js?v=1.2.163"></script><!-- v1.2.163: thread-lengkap -->',
     '<script src="app.js?v=1.2.164"></script><!-- ' + TAG + ' --><!-- v1.2.163: thread-lengkap -->'),
])

# ---------------- app.js ----------------
JS_FN = r'''
  /* ---- v1.2.164: cari-simpan — cari pesan (di chat ini & semua chat) + simpan pesan per bubble ---- */
  function waHlSnip164(s, q) {
    s = String(s == null ? '' : s); q = String(q || '').trim();
    if (q.length < 2) return esc(s);
    var lo = s.toLowerCase(), ql = q.toLowerCase(), out = '', i = 0, j;
    if (lo.length !== s.length) return esc(s);   // huruf yang panjangnya berubah saat lowercase: tanpa sorotan
    while ((j = lo.indexOf(ql, i)) > -1) { out += esc(s.slice(i, j)) + '<mark class="wa-hl">' + esc(s.slice(j, j + ql.length)) + '</mark>'; i = j + ql.length; }
    return out + esc(s.slice(i));
  }
  function waHl164(text, on) {
    if (!on || String(waState.findNum) !== String(waState.current)) return esc(text);
    return waHlSnip164(text, waState.findQ);
  }
  function waTsLbl164(ts) {
    ts = String(ts || ''); var dk = waDateKey(ts);
    return (dk ? waDateLabel(dk) : '') + (ts.length >= 16 ? ' ' + ts.slice(11, 16) : '');
  }
  var WA_WHO164 = { 'in': 'Pelanggan', bot: 'Bot', manual: 'Admin' };
  var WA_MT164 = { image: 'Gambar', video: 'Video', audio: 'Pesan suara', document: 'Dokumen', sticker: 'Stiker' };
  // tombol Simpan di baris waktu bubble
  function waSaveBtn164(k, kind, ts, text, media) {
    var num = waState.current; if (!num || !k) return '';
    waState.bIdx = waState.bIdx || {};
    waState.bIdx[k] = { kind: kind === 'in' ? 'in' : (kind === 'manual' ? 'manual' : 'bot'), ts: ts || '', text: String(text || '').slice(0, 2000), mt: (media && media.type) || '', mn: (media && media.name) || '' };
    var on = !!(waState.saved || {})[num + '|' + k];
    return '<a href="#" class="wa-sv' + (on ? ' on' : '') + '" data-sk="' + esc(k) + '" title="' + (on ? 'Hapus dari Pesan tersimpan' : 'Simpan pesan ini') + '">' + ico('bookmark', 12) + (on ? ' Tersimpan' : ' Simpan') + '</a>';
  }
  function waSavedSet164(items) {
    waState.savedList = items || []; waState.saved = {};
    waState.savedList.forEach(function (x) { waState.saved[x.num + '|' + x.k] = x; });
    var b = $('#waSavedBtn'); if (b) b.title = 'Pesan tersimpan (' + waState.savedList.length + ')';
  }
  function waSavedLoad164(then) {
    api('wa_saved_list').then(function (r) { if (r && r.ok) { waSavedSet164(r.items); if (then) then(); } });
  }
  function waSavedToggle164(body) {
    api('wa_saved_toggle', { method: 'POST', body: body }).then(function (r) {
      if (!r || !r.ok) { toast((r && r.error) || 'Gagal menyimpan.', true); return; }
      waSavedSet164(r.items);
      toast(r.saved ? 'Pesan disimpan — buka lewat ikon Tersimpan di atas daftar chat.' : 'Dihapus dari Pesan tersimpan.');
      if (waState.current) fetchWaThread(waState.current);
      if (waState.savedView) renderWaConvs();
    });
  }
  // lompat ke pesan: muat thread sampai entri ke-pos, gulir ke bubble k & beri sorotan
  function waJump164(num, pos, k) {
    num = String(num);
    waState.thLim = waState.thLim || {};
    if (pos >= 0 && (waState.thLim[num] || 60) < pos + 11) waState.thLim[num] = pos + 11;
    waState.jumpK = { num: num, k: k || '' };
    if (String(waState.current) !== num) selectWaConv(num); else fetchWaThread(num);
  }
  function waJumpApply164(num) {
    var j = waState.jumpK; if (!j || String(j.num) !== String(num)) return;
    waState.jumpK = null;
    var el = null;
    $$('#waThreadBody [data-k]').forEach(function (x) { if (!el && x.getAttribute('data-k') === j.k) el = x; });
    if (!el) { toast('Pesan tidak ditemukan di tampilan ini.'); return; }
    waState.waStick = false;
    el.scrollIntoView({ block: 'center' });
    el.style.boxShadow = '0 0 0 3px #fbbf24'; setTimeout(function () { el.style.boxShadow = ''; }, 1800);
  }
  function waJumpTs164(num, ts, k) {   // dari Pesan tersimpan: posisi dicari lewat ts
    api('wa_msg_search', { query: '&number=' + encodeURIComponent(num) + '&ts=' + encodeURIComponent(ts) }).then(function (r) {
      if (!r || !r.ok) { toast((r && r.error) || 'Chat tidak bisa dibuka.', true); return; }
      if (r.pos < 0) { toast('Pesan ini sudah tidak ada di log chat (isinya tetap ada di Pesan tersimpan).'); if (String(waState.current) !== String(num)) selectWaConv(String(num)); return; }
      waJump164(num, r.pos, k);
    });
  }
  // --- cari di dalam chat yang terbuka ---
  function waFindOpen164() {
    var b = $('#waFindBar'); if (!b || !waState.current) return;
    if (!b.innerHTML) {
      b.innerHTML = ico('search', 16, 'style="color:var(--muted);flex:none"') +
        '<input type="search" id="waFindQ" placeholder="Cari di chat ini…" autocomplete="off" enterkeyhint="search">' +
        '<span class="cnt" id="waFindCnt"></span>' +
        '<button type="button" class="wa-ibtn" id="waFindUp" title="Lebih lama (Enter)">' + ico('chevron-down', 16, 'style="transform:rotate(180deg)"') + '</button>' +
        '<button type="button" class="wa-ibtn" id="waFindDn" title="Lebih baru (Shift+Enter)">' + ico('chevron-down', 16) + '</button>' +
        '<button type="button" class="wa-ibtn" id="waFindX" title="Tutup (Esc)">' + ico('x', 16) + '</button>';
      var t = null;
      $('#waFindQ').oninput = function () { var v = this.value; clearTimeout(t); t = setTimeout(function () { waFindRun164(v); }, 300); };
      $('#waFindQ').onkeydown = function (e) {
        if (e.key === 'Enter') { e.preventDefault(); waFindStep164(e.shiftKey ? 1 : -1); }
        else if (e.key === 'Escape') { e.preventDefault(); waFindClose164(); }
      };
      $('#waFindUp').onclick = function () { waFindStep164(-1); };
      $('#waFindDn').onclick = function () { waFindStep164(1); };
      $('#waFindX').onclick = function () { waFindClose164(); };
    }
    b.style.display = 'flex'; waState.findOpen = true; waState.findNum = String(waState.current);
    if ($('#waFindBtn')) $('#waFindBtn').classList.add('on');
    waFindCnt164();
    $('#waFindQ').focus(); $('#waFindQ').select();
  }
  function waFindClose164(noFetch) {
    var b = $('#waFindBar'); if (b) b.style.display = 'none';
    var had = !!waState.findQ;
    waState.findOpen = false; waState.findQ = ''; waState.fHits = []; waState.fIdx = -1; waState.findSeq = (waState.findSeq || 0) + 1;
    if ($('#waFindQ')) $('#waFindQ').value = '';
    if ($('#waFindCnt')) $('#waFindCnt').textContent = '';
    if ($('#waFindBtn')) $('#waFindBtn').classList.remove('on');
    if (had && !noFetch && waState.current) fetchWaThread(waState.current);
  }
  function waFindCnt164(busy) {
    var c = $('#waFindCnt'); if (!c) return;
    var h = waState.fHits || [], q = String(waState.findQ || '');
    if ($('#waFindUp')) $('#waFindUp').disabled = !h.length || waState.fIdx <= 0;
    if ($('#waFindDn')) $('#waFindDn').disabled = !h.length || waState.fIdx >= h.length - 1;
    c.textContent = busy ? 'Mencari…' : (q.length < 2 ? '' : (h.length ? (waState.fIdx + 1) + '/' + h.length + (waState.fMore ? '+' : '') : 'Tidak ada'));
  }
  function waFindRun164(v) {
    var num = String(waState.current || ''), q = String(v || '').trim();
    var seq = waState.findSeq = (waState.findSeq || 0) + 1;
    waState.findNum = num; waState.findQ = q.length >= 2 ? q : '';
    if (q.length < 2) { waState.fHits = []; waState.fIdx = -1; waFindCnt164(); fetchWaThread(num); return; }
    waFindCnt164(true);
    api('wa_msg_search', { query: '&number=' + encodeURIComponent(num) + '&q=' + encodeURIComponent(q) }).then(function (r) {
      if (seq !== waState.findSeq || String(waState.current) !== num) return;
      waState.fHits = (r && r.ok && r.hits) || []; waState.fMore = !!(r && r.more);
      waState.fIdx = waState.fHits.length - 1;   // mulai dari yang terbaru
      waFindCnt164();
      if (waState.fIdx >= 0) { var h = waState.fHits[waState.fIdx]; waJump164(num, h.pos, h.k); }
      else fetchWaThread(num);
    });
  }
  function waFindStep164(d) {
    var h = waState.fHits || []; if (!h.length) return;
    var i = Math.max(0, Math.min(h.length - 1, waState.fIdx + d));
    if (i === waState.fIdx) return;
    waState.fIdx = i; waFindCnt164();
    waJump164(waState.current, h[i].pos, h[i].k);
  }
  // --- cari isi pesan di semua chat (kotak cari daftar chat, >= 3 huruf) ---
  function waGlobFetch164(v) {
    var q = String(v || '').trim();
    clearTimeout(waState.gT);
    if (q.length < 3) { waState.gHits = null; return; }
    waState.gT = setTimeout(function () {
      api('wa_msg_search', { query: '&q=' + encodeURIComponent(q) }).then(function (r) {
        if (String(waState.q || '').trim() !== q) return;
        waState.gHits = { q: q, hits: (r && r.ok && r.hits) || [], more: !!(r && r.more) };
        renderWaConvs();
      });
    }, 350);
  }
  function waGlobHtml164() {
    var q = String(waState.q || '').trim(); if (q.length < 3) return '';
    var g = waState.gHits;
    if (!g || g.q !== q) return '<div class="wa-gh">PESAN</div><div style="padding:12px 14px;color:var(--muted);font-size:13px">Mencari di isi pesan…</div>';
    if (!g.hits.length) return '<div class="wa-gh">PESAN</div><div style="padding:12px 14px;color:var(--muted);font-size:13px">Tidak ada pesan berisi "' + esc(q) + '"</div>';
    return '<div class="wa-gh">PESAN (' + g.hits.length + (g.more ? '+' : '') + ')</div>' + g.hits.map(function (h, i) {
      return '<div class="wa-gmsg" data-gi="' + i + '"><div class="wa-gm-top"><b>' + esc(h.name || ('+' + h.num)) + '</b><span>' + esc(waTsLbl164(h.ts)) + '</span></div>' +
        '<div class="wa-gm-tx"><span style="color:var(--muted)">' + esc(WA_WHO164[h.kind] || '') + ': </span>' + waHlSnip164(h.snip, q) + '</div></div>';
    }).join('');
  }
  function waGlobBind164() {
    $$('#waConvList .wa-gmsg').forEach(function (el) {
      el.onclick = function () {
        var h = ((waState.gHits || {}).hits || [])[+el.getAttribute('data-gi')]; if (!h) return;
        waJump164(h.num, h.pos, h.k);
      };
    });
  }
  // --- daftar Pesan tersimpan (menggantikan daftar chat selama dibuka) ---
  function waSavedRender164() {
    var L = waState.savedList || [], q = String(waState.q || '').trim().toLowerCase();
    if (q) L = L.filter(function (x) { return (String(x.text || '') + ' ' + (x.mn || '') + ' ' + (x.name || '') + ' ' + x.num).toLowerCase().indexOf(q) > -1; });
    var h = '<div class="wa-sv-hd">' + ico('bookmark', 15) + '<b>Pesan tersimpan</b><span style="color:var(--muted);font-size:12px">' + (waState.savedList || []).length + '</span>' +
      '<button type="button" class="wa-svx" id="waSavedClose" title="Kembali ke daftar chat">' + ico('x', 18) + '</button></div>';
    if (!L.length) h += '<div style="padding:16px;color:var(--muted);font-size:13px">' + (q ? 'Tidak ada pesan tersimpan yang cocok.' : 'Belum ada pesan tersimpan. Klik <b>Simpan</b> di bawah bubble chat untuk menyimpannya di sini.') + '</div>';
    h += L.map(function (x) {
      var tx = String(x.text || '');
      if (x.mt) tx = '[' + (WA_MT164[x.mt] || 'Media') + (x.mn ? ': ' + x.mn : '') + ']' + (tx ? '\n' + tx : '');
      return '<div class="wa-svi" data-id="' + esc(x.id) + '"><div class="wa-gm-top"><b>' + esc(x.name || ('+' + x.num)) + '</b><span>' + esc(waTsLbl164(x.ts)) +
        ' <button type="button" class="wa-svx" data-rm="1" title="Hapus dari Pesan tersimpan">' + ico('trash-2', 14) + '</button></span></div>' +
        '<div class="wa-gm-who">' + esc(WA_WHO164[x.kind] || '') + '</div><div class="wa-gm-tx">' + waHlSnip164(tx, q) + '</div></div>';
    }).join('');
    $('#waConvList').innerHTML = h;
    $('#waSavedClose').onclick = function () { waSavedView164(false); };
    $$('#waConvList .wa-svi').forEach(function (el) {
      el.onclick = function (e) {
        var id = el.getAttribute('data-id'), x = (waState.savedList || []).filter(function (y) { return y.id === id; })[0]; if (!x) return;
        if (e.target.closest && e.target.closest('[data-rm]')) { e.stopPropagation(); if (confirm('Hapus pesan ini dari Pesan tersimpan?')) waSavedToggle164({ number: x.num, k: x.k, remove: 1 }); return; }
        waJumpTs164(x.num, x.ts, x.k);
      };
    });
  }
  function waSavedView164(on) {
    waState.savedView = !!on;
    if ($('#waSavedBtn')) $('#waSavedBtn').classList.toggle('on', !!on);
    if (on) waSavedLoad164(renderWaConvs);
    renderWaConvs();
  }
  function waCs164Init() {
    if (waState.cs164) return; waState.cs164 = true;
    waSavedLoad164(function () { if (waState.current) fetchWaThread(waState.current); });
    if ($('#waSavedBtn')) $('#waSavedBtn').onclick = function () { waSavedView164(!waState.savedView); };
    var body = $('#waThreadBody');
    if (body) body.addEventListener('click', function (e) {
      var a = e.target.closest ? e.target.closest('.wa-sv') : null; if (!a) return;
      e.preventDefault();
      var k = a.getAttribute('data-sk'), b = (waState.bIdx || {})[k], num = waState.current; if (!num || !b) return;
      waSavedToggle164({ number: num, k: k, ts: b.ts, kind: b.kind, text: b.text, mt: b.mt, mn: b.mn });
    });
    document.addEventListener('keydown', function (e) {   // Ctrl/Cmd+F di Percakapan WA = cari di chat ini
      if (!(e.ctrlKey || e.metaKey) || String(e.key).toLowerCase() !== 'f' || !waState.current) return;
      var p = $('#panel-wachat'); if (!p || !p.classList.contains('active')) return;
      e.preventDefault(); waFindOpen164();
    });
  }

  function waBubble(text, kind, ts, media, via, rq) {'''

A = 'dashboard/chatbot-ai/app.js'
patch(A, [
    ("  var ICONS_EXTRA = {\n",
     "  var ICONS_EXTRA = {\n    'bookmark':          '<path d=\"m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z\"/>',   // " + TAG + "\n"),
    ("\n  function waBubble(text, kind, ts, media, via, rq) {", JS_FN),
    ("    if (rq && rq.reply_to) qh = waQuoteHtml(rq.reply_to, kind === 'bot');\n",
     "    if (rq && rq.reply_to) qh = waQuoteHtml(rq.reply_to, kind === 'bot');\n    var sb164 = (rq && rq.k) ? waSaveBtn164(rq.k, kind, ts, text, media) : '';   // " + TAG + "\n"),
    ("qh + waMediaHtml(media) + esc(text) + '<div style=\"font-size:10px;opacity:.65;margin-top:4px\">' + esc((ts || '').slice(11, 16)) + who + (via ? ' · ke ' + esc(via) : '') + rb + '</div></div>';",
     "qh + waMediaHtml(media) + waHl164(text, !!(rq && rq.k)) + '<div style=\"font-size:10px;opacity:.65;margin-top:4px\">' + esc((ts || '').slice(11, 16)) + who + (via ? ' · ke ' + esc(via) : '') + rb + sb164 + '</div></div>';   // " + TAG),
    ("    waState.qIdx = {};\n", "    waState.qIdx = {}; waState.bIdx = {};   // " + TAG + "\n"),
    ("    var _wide151 = waCtlWide();\n",
     "    var _wide151 = waCtlWide();\n    var _fb164 = '<button type=\"button\" class=\"wa-ibtn' + (waState.findOpen ? ' on' : '') + '\" id=\"waFindBtn\" title=\"Cari di chat ini (Ctrl+F)\">' + ico('search', 16) + '</button>';   // " + TAG + "\n"),
    ("'</div></div>' + _mine151 +", "'</div></div>' + _mine151 + _fb164 +"),
    ("_metaRow + toolBtns + _vipHtml + _leadLink", "_metaRow + toolBtns + ' <a href=\"#\" id=\"waFindBtn\" style=\"font-size:12px\">' + ico('search', 13) + ' Cari di chat ini</a>' + _vipHtml + _leadLink"),   # tata letak sempit/HP: di lembar Alat chat
    ("    waCtlBind151();\n",
     "    waCtlBind151();\n    if ($('#waFindBtn')) $('#waFindBtn').onclick = function (ev) { if (ev) ev.preventDefault(); waState.thTools = false; if ($('#waThreadHead')) $('#waThreadHead').classList.remove('tools-open'); if (waState.findOpen) waFindClose164(); else waFindOpen164(); };   // " + TAG + "\n"),
    ("    wiThreadBind(res);   // v1.2.105\n", "    wiThreadBind(res);   // v1.2.105\n    waJumpApply164(num);   // " + TAG + "\n"),
    ("    waQuoteInit();   // v1.2.121: wa-balas-kutip\n", "    waQuoteInit();   // v1.2.121: wa-balas-kutip\n    waCs164Init();   // " + TAG + "\n"),
    ("if ($('#waSearch')) $('#waSearch').oninput = function () { waState.q = this.value; renderWaConvs(); };",
     "if ($('#waSearch')) $('#waSearch').oninput = function () { waState.q = this.value; waGlobFetch164(this.value); renderWaConvs(); };   // " + TAG),
    ("  function renderWaConvs() {\n", "  function renderWaConvs() {\n    if (waState.savedView && $('#waConvList')) { waSavedRender164(); return; }   // " + TAG + "\n"),
    ("      if (!_list125.length) { $('#waConvList').innerHTML = '<div style=\"padding:16px;color:var(--muted)\">Tidak ada yang cocok dengan \"' + esc(waState.q.trim()) + '\"</div>'; return; }",
     "      if (!_list125.length) { $('#waConvList').innerHTML = '<div style=\"padding:16px;color:var(--muted)\">Tidak ada kontak yang cocok dengan \"' + esc(waState.q.trim()) + '\"</div>' + waGlobHtml164(); waGlobBind164(); return; }   // " + TAG),
    ("    }).join('');\n    $$('#waConvList .wa-conv').forEach(function (el) {\n",
     "    }).join('');\n    if (_q125) { $('#waConvList').insertAdjacentHTML('beforeend', waGlobHtml164()); waGlobBind164(); }   // " + TAG + "\n    $$('#waConvList .wa-conv').forEach(function (el) {\n"),
    ("  function selectWaConv(num) {\n", "  function selectWaConv(num) {\n    if (waState.findOpen && String(waState.findNum) !== String(num)) waFindClose164(true);   // " + TAG + "\n"),
])
print('OK')
