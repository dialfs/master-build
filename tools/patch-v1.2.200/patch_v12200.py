#!/usr/bin/env python3
"""v1.2.200 (edit-hapus-pesan): edit & hapus pesan keluar per bubble di Percakapan WA.
- api/index.php: wa_msg_edit (PUT WAHA, maks 15 menit, teks saja) & wa_msg_delete (DELETE WAHA = hapus untuk semua
  orang, maks 48 jam). Hanya nomor WAHA (Meta Cloud API tidak punya fitur ini). Super Admin/Admin/Supervisor: semua
  pesan keluar; WA Agent: hanya pesan yang ia kirim sendiri (entri log baru menyimpan 'by').
  Log: a_orig + edited {at,by} / deleted {at,by}; riwayat konteks AI ikut disesuaikan; audit msg_edit / msg_delete.
  wa_thread mengirim act {e,d,why}, edited, deleted per pesan.
- app.js: tautan Edit / Hapus di bubble (muncul saat kursor di atas bubble; di HP selalu tampil), modal edit,
  bubble terhapus tampil "Pesan ini dihapus" (isi lama dicoret untuk tim), label "diedit".
- index.html: gaya .wa-mact, app.js?v=1.2.200.
Butuh v1.2.199. Idempoten.  Pakai: patch_v12200.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.200: edit-hapus-pesan'; NEED = 'v1.2.199: template-menu'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12200-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)

API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ---------------------------------------------------------------- api/index.php
s = rd(API)
if TAG not in s:
    assert 'v1.2.199: template-media' in s, 'butuh v1.2.199 dulu'
    s = rep(s, "define('DEI_VERSION', 'v1.2.199');   // v1.2.199:",
            "define('DEI_VERSION', 'v1.2.200');   // " + TAG + " — edit & hapus pesan keluar per bubble (WAHA); v1.2.199:", what='DEI_VERSION')
    LIB = r'''/* ---------- v1.2.200: edit-hapus-pesan — edit & hapus pesan keluar per bubble (hanya WAHA) ---------- */
define('WA_EDIT_SEC', 15 * 60);    // batas WhatsApp untuk mengedit pesan
define('WA_DEL_SEC', 48 * 3600);   // batas aman "hapus untuk semua orang"
function deiMsgOutId($e) { return (string)(($e['out_id'] ?? '') ?: (($e['a_wamid'] ?? '') ?: ($e['echo_id'] ?? ''))); }
function deiMsgCh($e, $num, $s) { $c = (string)($e['out_ch'] ?? ''); return $c !== '' ? $c : waCurCh($num, $s); }
// Hak edit/hapus satu entri keluar: ['e' => bool, 'd' => bool, 'why' => alasan bila keduanya tidak bisa]
function deiMsgActs($u, $e, $num, $s, $claim = false) {
    $no = function ($why) { return ['e' => false, 'd' => false, 'why' => $why]; };
    $isMedOut = ($e['q'] ?? '') === '' && is_array($e['media'] ?? null);
    if (deiMsgOutId($e) === '' || (($e['a'] ?? '') === '' && !$isMedOut)) return $no('');
    if (!empty($e['deleted'])) return $no('Pesan sudah dihapus.');
    if (waChanProv(deiMsgCh($e, $num, $s), $s) !== 'waha') return $no('WhatsApp API resmi (Meta) tidak mendukung edit atau hapus pesan yang sudah terkirim.');
    if (!deiIsLead((string)($u['role'] ?? ''))) {
        $by = (string)(($e['by'] ?? '') ?: ($e['sched_by'] ?? ''));
        if ($by === '' || $by !== (string)($u['username'] ?? '')) return $no('Hanya pengirim pesan atau Supervisor/Admin yang boleh mengubah pesan ini.');
        if ($claim === false) $claim = waClaimGet($num);
        if ($claim && (string)($claim['agent_username'] ?? '') !== (string)$u['username']) return $no('Chat ini sedang dipegang agent lain.');
    }
    $age = time() - (int)strtotime((string)($e['ts'] ?? ''));
    $ed = !$isMedOut && ($e['a'] ?? '') !== '' && $age <= WA_EDIT_SEC;
    $dl = $age <= WA_DEL_SEC;
    return ['e' => $ed, 'd' => $dl, 'why' => ($ed || $dl) ? '' : 'Batas waktu WhatsApp sudah lewat (edit 15 menit, hapus 48 jam).'];
}
// Path WAHA pesan: chatId diambil dari id serialized ("true_<jid>_<id>") bila ada (bisa @lid / grup).
function deiMsgWahaPath($wa, $num, $oid) {
    $jid = preg_match('/^(?:true|false)_(.+@[^_]+)_[^_]+$/', $oid, $m) ? $m[1] : waChatId($num);
    return '/api/' . rawurlencode(wahaSession($wa)) . '/chats/' . rawurlencode($jid) . '/messages/' . rawurlencode($oid);
}
'''
    s = rep(s, "/* ---------- v1.2.122: template-balasan — template balasan cepat Percakapan WA ---------- */\n",
            LIB + "/* ---------- v1.2.122: template-balasan — template balasan cepat Percakapan WA ---------- */\n", what='lib')
    # endpoint
    EP = r'''    case 'wa_msg_edit':
    case 'wa_msg_delete': {   // v1.2.200: edit-hapus-pesan
        $u = requireAuth(['super_admin','admin','wa_agent']);
        $s = getSettings();
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        $oid = trim((string)($in['id'] ?? ''));
        if ($num === '' || $oid === '' || strlen($oid) > 200) jsonOut(['ok' => false, 'error' => 'number & id wajib'], 400);
        deiGuardAgentPrivate($u, $num);
        deiGuardSpvScope($u, $num);
        $e = null;
        foreach (logReadByNumber($num, 2000) as $x) { if (deiMsgOutId($x) === $oid) { $e = $x; break; } }
        if (!$e) jsonOut(['ok' => false, 'error' => 'Pesan tidak ditemukan (mungkin sudah terlalu lama).'], 404);
        $isEd = $action === 'wa_msg_edit';
        $act = deiMsgActs($u, $e, $num, $s);
        if (!$act[$isEd ? 'e' : 'd']) {
            jsonOut(['ok' => false, 'error' => $act['why'] !== '' ? $act['why'] : ($isEd ? 'Pesan ini tidak bisa diedit — hanya pesan teks, paling lama 15 menit setelah dikirim.' : 'Pesan ini tidak bisa dihapus.')], 409);
        }
        $text = '';
        $old = (string)($e['a'] ?? '');
        if ($isEd) {
            $text = trim(str_replace(["\r\n", "\r"], "\n", (string)($in['text'] ?? '')));
            if ($text === '') jsonOut(['ok' => false, 'error' => 'Isi pesan tidak boleh kosong. Pakai Hapus untuk menarik pesan.'], 400);
            if (mb_strlen($text) > 4000) jsonOut(['ok' => false, 'error' => 'Isi pesan maksimal 4.000 karakter.'], 400);
            if ($text === trim($old)) jsonOut(['ok' => true, 'same' => 1]);
        }
        $wac = waChanConf(waConf($s), deiMsgCh($e, $num, $s), $s);
        list($c, $d) = wahaApi($wac, $isEd ? 'PUT' : 'DELETE', deiMsgWahaPath($wac, $num, $oid), $isEd ? ['text' => $text] : null);
        if ($c < 200 || $c >= 300) {
            error_log('wa_msg ' . ($isEd ? 'edit' : 'delete') . ' HTTP ' . $c . ': ' . json_encode($d));
            jsonOut(['ok' => false, 'error' => 'WhatsApp menolak: ' . wahaErr($c, $d, $isEd ? 'Edit pesan gagal.' : 'Hapus pesan gagal.')], 502);
        }
        $who = ['at' => date('Y-m-d H:i:s'), 'by' => (string)($u['name'] ?? $u['username']), 'u' => (string)$u['username']];
        logMutate(function (&$logs) use ($num, $oid, $isEd, $text, $who) {
            foreach ($logs as $i => $x) {
                if (($x['channel'] ?? '') !== 'whatsapp' || waNormNum($x['ip'] ?? '') !== $num || deiMsgOutId($x) !== $oid) continue;
                if ($isEd) {
                    if (!isset($x['a_orig'])) $logs[$i]['a_orig'] = (string)($x['a'] ?? '');
                    $logs[$i]['a'] = $text; $logs[$i]['edited'] = $who;
                } else $logs[$i]['deleted'] = $who;
                return true;
            }
            return false;
        });
        try {   // konteks AI ikut: isi lama diganti / dibuang
            $h = waLoadHistory($num);
            for ($i = count($h) - 1; $i >= 0; $i--) {
                if (($h[$i]['role'] ?? '') !== 'assistant' || trim((string)($h[$i]['content'] ?? '')) !== trim($old)) continue;
                if ($isEd) $h[$i]['content'] = $text; else array_splice($h, $i, 1);
                waSaveHistory($num, $h);
                break;
            }
        } catch (\Throwable $ex) {}
        waAuditLog($isEd ? 'msg_edit' : 'msg_delete', $u['username'], $num, ['id' => $oid, 'old' => mb_substr($old, 0, 300)] + ($isEd ? ['new' => mb_substr($text, 0, 300)] : []));
        jsonOut(['ok' => true]);
        break;
    }

'''
    s = rep(s, "    case 'wa_send_media': {   // v1.2.120: wa-lampiran", EP + "    case 'wa_send_media': {   // v1.2.120: wa-lampiran", what='endpoint')
    # catat pengirim & nomor bisnis di entri log baru
    s = rep(s, "        ] + array_filter(['out_id' => $oid121, 'reply_to' => $rq121]), (int)($s['api']['log_limit'] ?? 500));   // v1.2.121\n",
               "        ] + array_filter(['out_id' => $oid121, 'reply_to' => $rq121, 'by' => (string)$u['username'], 'out_ch' => (string)($GLOBALS['wa_out_ch'] ?? '')]), (int)($s['api']['log_limit'] ?? 500));   // v1.2.121; " + TAG + "\n", what='log manual')
    s = rep(s, "        ] + array_filter(['out_id' => $oidM, 'reply_to' => $rqM]), (int)($s['api']['log_limit'] ?? 500));   // v1.2.121\n",
               "        ] + array_filter(['out_id' => $oidM, 'reply_to' => $rqM, 'by' => (string)$u['username'], 'out_ch' => (string)($GLOBALS['wa_out_ch'] ?? '')]), (int)($s['api']['log_limit'] ?? 500));   // v1.2.121; " + TAG + "\n", what='log media')
    s = rep(s, "    ] + array_filter(['out_id' => $oid, 'media' => $logM]), (int)($s['api']['log_limit'] ?? 500));\n",
               "    ] + array_filter(['out_id' => $oid, 'media' => $logM, 'out_ch' => (string)($GLOBALS['wa_out_ch'] ?? '')]), (int)($s['api']['log_limit'] ?? 500));   // " + TAG + "\n", what='log jadwal')
    # wa_thread: act/edited/deleted
    s = rep(s, "        $s116 = getSettings(); $curCh116 = waCurCh($num, $s116); $winCh116 = waWinCh($num, $s116);   // v1.2.116: pindah-nomor\n",
               "        $s116 = getSettings(); $curCh116 = waCurCh($num, $s116); $winCh116 = waWinCh($num, $s116);   // v1.2.116: pindah-nomor\n"
               "        $cl200 = waClaimGet($num);   // " + TAG + "\n", what='thread claim')
    s = rep(s, "                       'reply_to' => is_array($e['reply_to'] ?? null) ? $e['reply_to'] : null];\n",
               "                       'reply_to' => is_array($e['reply_to'] ?? null) ? $e['reply_to'] : null,\n"
               "                       // " + TAG + "\n"
               "                       'edited' => is_array($e['edited'] ?? null) ? ['at' => (string)($e['edited']['at'] ?? ''), 'by' => (string)($e['edited']['by'] ?? '')] : null,\n"
               "                       'deleted' => is_array($e['deleted'] ?? null) ? ['at' => (string)($e['deleted']['at'] ?? ''), 'by' => (string)($e['deleted']['by'] ?? '')] : null,\n"
               "                       'act' => deiMsgOutId($e) !== '' ? deiMsgActs($u, $e, $num, $s116, $cl200) : null];\n", what='thread msg')
    save(API, s)
else: print('sudah', API)

# ---------------------------------------------------------------- app.js
s = rd(JS)
if TAG not in s:
    assert NEED in s, 'butuh v1.2.199 dulu'
    s = rep(s, "    'pen-tool':",
            "    'pencil':            '<path d=\"M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z\"/><path d=\"m15 5 4 4\"/>',   // " + TAG + "\n"
            "    'pen-tool':", what='ikon pencil')
    # waBubble
    s = rep(s, "    if (rq && rq.reply_to) qh = waQuoteHtml(rq.reply_to, kind === 'bot');\n",
               "    if (rq && rq.reply_to) qh = waQuoteHtml(rq.reply_to, kind === 'bot');\n"
               "    // " + TAG + ": label diedit / dihapus + tautan Edit & Hapus\n"
               "    var del200 = rq && rq.del, edt200 = rq && rq.edt, mk200 = '', ma200 = '';\n"
               "    if (del200) { rb = ''; mk200 = ' · dihapus' + (del200.by ? ' oleh ' + esc(del200.by) : ''); }\n"
               "    else if (edt200) mk200 = ' · <span title=\"Diedit' + (edt200.by ? ' oleh ' + esc(edt200.by) : '') + (edt200.at ? ' pukul ' + esc(String(edt200.at).slice(11, 16)) : '') + '\">diedit</span>';\n"
               "    if (!del200 && rid && rq.act && (rq.act.e || rq.act.d)) {\n"
               "      waState.mIdx = waState.mIdx || {}; waState.mIdx[rid] = { text: String(text || '') };\n"
               "      if (rq.act.e) ma200 += '<a href=\"#\" class=\"wa-mact\" data-act=\"edit\" data-oid=\"' + esc(rid) + '\" title=\"Edit pesan ini (maks 15 menit setelah dikirim)\">' + ico('pencil', 12) + ' Edit</a>';\n"
               "      if (rq.act.d) ma200 += '<a href=\"#\" class=\"wa-mact\" data-act=\"del\" data-oid=\"' + esc(rid) + '\" title=\"Hapus untuk semua orang (maks 48 jam setelah dikirim)\">' + ico('trash-2', 12) + ' Hapus</a>';\n"
               "    }\n", what='bubble prep')
    s = rep(s, "qh + waMediaHtml(media) + waHl164(text, !!(rq && rq.k)) + '<div style=\"font-size:10px;opacity:.65;margin-top:4px\">' + esc((ts || '').slice(11, 16)) + who + (via ? ' · ke ' + esc(via) : '') + rb + sb164 + '</div></div>';",
               "qh + (del200 ? '<div style=\"font-style:italic;display:flex;align-items:center;gap:5px\">' + ico('ban', 13) + ' Pesan ini dihapus</div>' + ((text || (media && media.name)) ? '<div style=\"opacity:.55;text-decoration:line-through;font-size:12.5px;margin-top:2px\" title=\"Isi sebelum dihapus (hanya terlihat oleh tim)\">' + esc(String(text || '') || ('[' + (media.name || 'lampiran') + ']')) + '</div>' : '') : waMediaHtml(media) + waHl164(text, !!(rq && rq.k))) + '<div style=\"font-size:10px;opacity:.65;margin-top:4px\">' + esc((ts || '').slice(11, 16)) + who + (via ? ' · ke ' + esc(via) : '') + mk200 + rb + sb164 + ma200 + '</div></div>';   // " + TAG,
               what='bubble return')
    s = rep(s, "{ id: m.out_id, reply_to: m.q ? null : m.reply_to, k: 'a' + m.ts + (m.out_id || '') });   // v1.2.121\n",
               "{ id: m.out_id, reply_to: m.q ? null : m.reply_to, k: 'a' + m.ts + (m.out_id || ''), act: m.act, edt: m.edited, del: m.deleted });   // v1.2.121; " + TAG + "\n", what='render a')
    s = rep(s, "    waState.qIdx = {}; waState.bIdx = {};   // v1.2.164: cari-simpan\n",
               "    waState.qIdx = {}; waState.bIdx = {}; waState.mIdx = {};   // v1.2.164: cari-simpan; " + TAG + "\n", what='reset idx')
    # klik Edit / Hapus
    s = rep(s, "      if (a) { e.preventDefault(); waQuoteSet(a.getAttribute('data-rid')); return; }\n",
               "      if (a) { e.preventDefault(); waQuoteSet(a.getAttribute('data-rid')); return; }\n"
               "      var ma = e.target.closest ? e.target.closest('.wa-mact') : null;   // " + TAG + "\n"
               "      if (ma) { e.preventDefault(); waMsgAct(ma.getAttribute('data-act'), ma.getAttribute('data-oid')); return; }\n", what='klik')
    FN = r'''  /* ---- v1.2.200: edit-hapus-pesan — edit & hapus pesan keluar (WAHA) ---- */
  function waMsgAct(act, oid) {
    var num = waState.current, m = (waState.mIdx || {})[oid];
    if (!num || !m) return;
    if (act === 'del') {
      if (!confirm('Hapus pesan ini untuk semua orang?\n\nPesan ditarik dari WhatsApp pelanggan (di sana tampil "Pesan ini telah dihapus"). Tindakan ini tidak bisa dibatalkan.')) return;
      api('wa_msg_delete', { method: 'POST', body: { number: num, id: oid } }).then(function (r) {
        if (r && r.ok) { toast('Pesan dihapus untuk semua orang.'); fetchWaThread(num); }
        else toast((r && r.error) || 'Gagal menghapus pesan.', true);
      });
      return;
    }
    var ov = document.createElement('div');
    ov.id = 'waMsgEd';
    ov.style.cssText = 'position:fixed;inset:0;background:rgba(15,23,42,.45);z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px';
    ov.innerHTML = '<div class="card" style="width:100%;max-width:540px;margin:0">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:10px"><h3 style="margin:0">Edit pesan</h3>' +
      '<button type="button" class="btn ghost sm" id="wmeX" title="Tutup">' + ico('x', 16) + '</button></div>' +
      '<textarea id="wmeT" rows="6" maxlength="4000" style="width:100%"></textarea>' +
      '<p class="help" style="margin:6px 0 12px">Pesan di WhatsApp pelanggan ikut berubah dan diberi label <b>Diedit</b>. Hanya bisa sampai 15 menit setelah dikirim. Ctrl/⌘ + Enter untuk menyimpan.</p>' +
      '<div style="display:flex;gap:8px;justify-content:flex-end"><button type="button" class="btn ghost" id="wmeC">Batal</button>' +
      '<button type="button" class="btn" id="wmeS">' + ico('save', 14) + ' Simpan</button></div></div>';
    document.body.appendChild(ov);
    var tutup = function () { ov.remove(); document.removeEventListener('keydown', esck); };
    var esck = function (e) { if (e.key === 'Escape') tutup(); };
    document.addEventListener('keydown', esck);
    ov.onclick = function (e) { if (e.target === ov) tutup(); };
    $('#wmeX').onclick = tutup; $('#wmeC').onclick = tutup;
    var t = $('#wmeT');
    t.value = m.text; t.focus();
    try { t.setSelectionRange(t.value.length, t.value.length); } catch (e) {}
    var simpan = function () {
      var v = t.value.trim(), b = $('#wmeS');
      if (!v) { toast('Isi pesan tidak boleh kosong. Pakai Hapus untuk menarik pesan.', true); return; }
      if (v === String(m.text).trim()) { tutup(); return; }
      b.disabled = true;
      api('wa_msg_edit', { method: 'POST', body: { number: num, id: oid, text: v } }).then(function (r) {
        b.disabled = false;
        if (r && r.ok) { tutup(); toast('Pesan diperbarui.'); fetchWaThread(num); }
        else toast((r && r.error) || 'Gagal mengedit pesan.', true);
      });
    };
    $('#wmeS').onclick = simpan;
    t.addEventListener('keydown', function (e) { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); simpan(); } });
  }
'''
    s = rep(s, "  /* ---- v1.2.15: pemisah tanggal di thread WA ------------------------- */\n", FN + "\n  /* ---- v1.2.15: pemisah tanggal di thread WA ------------------------- */\n", what='fn')
    # Pusat Bantuan
    s = rep(s, "    { id: 'release', roles: R_ALL, t: 'Mengembalikan chat ke bot / antrean'",
               "    { id: 'edit-hapus', roles: R_ALL, t: 'Mengedit atau menghapus pesan yang sudah terkirim', k: 'edit ubah ralat salah ketik typo hapus tarik unsend delete batal kirim pesan terkirim bubble',\n"
               "      s: ['Di <b>Percakapan WA</b>, arahkan kursor ke bubble pesan keluar (di HP tautan selalu tampil), lalu klik <b>Edit</b> atau <b>Hapus</b> di baris jam pesan.',\n"
               "          '<b>Edit</b>: ubah isi lalu <b>Simpan</b>. Pesan di WhatsApp pelanggan ikut berubah dengan label Diedit. Hanya pesan teks, paling lama 15 menit setelah dikirim.',\n"
               "          '<b>Hapus</b>: menarik pesan untuk semua orang (pelanggan melihat Pesan ini telah dihapus), paling lama 48 jam setelah dikirim. Di dashboard isinya tetap terlihat dicoret untuk tim.',\n"
               "          'Hanya untuk nomor WhatsApp lewat WAHA. WhatsApp API resmi (Meta) tidak menyediakan edit/hapus. WA Agent hanya bisa mengubah pesan yang ia kirim sendiri; Supervisor/Admin semua pesan keluar.'] },   // " + TAG + "\n"
               "    { id: 'release', roles: R_ALL, t: 'Mengembalikan chat ke bot / antrean'", what='artikel')
    save(JS, s)
else: print('sudah', JS)

# ---------------------------------------------------------------- index.html
s = rd(HT)
if TAG not in s:
    s = rep(s, '<script src="app.js?v=1.2.199"></script><!-- v1.2.199: template-media -->',
            '<script src="app.js?v=1.2.200"></script><!-- ' + TAG + ' --><!-- v1.2.199: template-media -->', what='app.js?v')
    s = rep(s, ".wa-sv{color:inherit;opacity:.8;text-decoration:none;margin-left:8px;display:inline-flex;align-items:center;gap:2px;vertical-align:-2px}\n",
            ".wa-sv{color:inherit;opacity:.8;text-decoration:none;margin-left:8px;display:inline-flex;align-items:center;gap:2px;vertical-align:-2px}\n"
            "/* " + TAG + " */\n"
            ".wa-mact{color:inherit;opacity:.8;text-decoration:none;margin-left:8px;display:none;align-items:center;gap:2px;vertical-align:-2px}\n"
            ".wa-mact:hover{opacity:1;text-decoration:underline}\n"
            "#waThreadBody [data-mid]:hover .wa-mact,#waThreadBody [data-mid]:focus-within .wa-mact{display:inline-flex}\n"
            "@media (hover:none){.wa-mact{display:inline-flex}}\n", what='css')
    save(HT, s)
else: print('sudah', HT)
print('patch v1.2.200 selesai')
