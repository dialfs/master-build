#!/usr/bin/env python3
"""v1.2.209 (autoreply-hp): auto reply WhatsApp Business dari HP (Away/Greeting message) tidak lagi mengambil alih bot.
Daftar teks auto reply (data/wa-autoreply.json). Pesan keluar dari HP (echo Meta coexistence / WAHA fromMe) yang
teksnya sama (abaikan huruf besar & spasi) tetap tercatat (src=hp_auto) tetapi: tidak memindah chat ke mode manusia,
tidak dihitung balasan agent, tidak menandai chat terbalas, tidak masuk riwayat AI.
Setelan di Widget & API (Super Admin/Admin) + tombol "Tandai auto reply" di bubble pesan dari HP (Supervisor+).
Saat menyimpan/menandai: chat yang terlanjur di mode manusia (tanpa claim) karena auto reply itu dikembalikan ke bot.
Butuh v1.2.208. Idempoten.  Pakai: patch_v12209.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.209: autoreply-hp'; NEED = 'v1.2.208: sales-untag'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12209-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

LIB = r'''/* ---- v1.2.209: autoreply-hp — auto reply WhatsApp Business dari HP tidak mengambil alih bot ---- */
define('WA_AUTOREPLY_FILE', DATA_DIR . '/wa-autoreply.json');
define('WA_AUTOREPLY_MAX', 10);
function warNorm209($t) { return mb_strtolower(trim(preg_replace('/\s+/u', ' ', (string)$t))); }
function warConf209() { $d = readJson(WA_AUTOREPLY_FILE, []); return is_array($d) ? $d : []; }
function warTexts209() {
    $d = warConf209();
    return is_array($d['texts'] ?? null) ? array_values(array_filter($d['texts'], function ($x) { return is_string($x) && trim($x) !== ''; })) : [];
}
function warIsAuto209($text) {
    $n = warNorm209($text);
    if ($n === '') return false;
    foreach (warTexts209() as $x) if (warNorm209($x) === $n) return true;
    return false;
}
function warClean209($list) {
    $out = []; $seen = [];
    foreach ((array)$list as $x) {
        $t = trim(str_replace(["\r\n", "\r"], "\n", (string)$x));
        if ($t === '') continue;
        $t = mb_substr($t, 0, 1500);
        $k = warNorm209($t);
        if (isset($seen[$k])) continue;
        $seen[$k] = 1; $out[] = $t;
        if (count($out) >= WA_AUTOREPLY_MAX) break;
    }
    return $out;
}
function warSave209($texts, $by) {
    writeJson(WA_AUTOREPLY_FILE, ['texts' => array_values($texts), 'updated_at' => wibDate('Y-m-d H:i:s'), 'by' => (string)$by]);
}
// Chat mode manusia tanpa claim yang pesan keluar terakhirnya auto reply dari HP -> kembali ke bot. Return daftar nomor.
function warRestore209($by) {
    if (deiIsManual()) return [];
    $modes = readJson(WA_MODES_FILE, []);
    if (!is_array($modes) || !warTexts209()) return [];
    $claims = waClaimGetAll();
    $done = []; $n = 0;
    foreach ($modes as $num => $m) {
        if (!is_array($m) || ($m['mode'] ?? '') !== 'human') continue;
        $num = (string)$num;
        if (!empty($claims[$num]) || waIsGroup($num)) continue;
        if (++$n > 500) break;
        $last = null;
        foreach (logReadByNumber($num, 40) as $e) {   // terbaru dulu
            if ((string)($e['a'] ?? '') !== '') { $last = $e; break; }
        }
        if (!$last || ($last['dir'] ?? '') !== 'manual' || !in_array((string)($last['src'] ?? ''), ['hp', 'hp_auto'], true)) continue;
        if (!warIsAuto209($last['a'])) continue;
        waSetMode($num, 'bot');
        try { waAuditLog('autoreply_restore', (string)$by, $num, []); } catch (\Throwable $e) {}
        $done[] = $num;
    }
    return $done;
}
'''

CASES = r'''    /* ---------- v1.2.209: autoreply-hp ---------- */
    case 'wa_autoreply_get': {
        requireAuth(['super_admin', 'admin', 'supervisor']);
        $d = warConf209();
        jsonOut(['ok' => true, 'texts' => warTexts209(), 'max' => WA_AUTOREPLY_MAX, 'updated_at' => (string)($d['updated_at'] ?? ''), 'by' => (string)($d['by'] ?? '')]);
        break;
    }
    case 'wa_autoreply_save': {
        $u = requireAuth(['super_admin', 'admin']);
        $in = bodyInput();
        $texts = warClean209($in['texts'] ?? []);
        warSave209($texts, $u['username']);
        try { waAuditLog('autoreply_save', $u['username'], '', ['n' => count($texts)]); } catch (\Throwable $e) {}
        $back = !empty($in['restore']) ? warRestore209($u['username']) : [];
        jsonOut(['ok' => true, 'texts' => $texts, 'restored' => count($back), 'restored_numbers' => $back]);
        break;
    }
    case 'wa_autoreply_mark': {   // tandai bubble pesan dari HP sebagai auto reply
        $u = requireAuth(['super_admin', 'admin', 'supervisor']);
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        $ts = (string)($in['ts'] ?? '');
        if ($num === '' || $ts === '') jsonOut(['ok' => false, 'error' => 'number & ts wajib'], 400);
        deiGuardSpvScope($u, $num);
        $text = '';
        foreach (logReadByNumber($num, 400) as $e) {
            if ((string)($e['ts'] ?? '') === $ts && ($e['dir'] ?? '') === 'manual' && in_array((string)($e['src'] ?? ''), ['hp', 'hp_auto'], true) && (string)($e['a'] ?? '') !== '') { $text = (string)$e['a']; break; }
        }
        if ($text === '') jsonOut(['ok' => false, 'error' => 'Pesan dari HP tidak ditemukan.'], 404);
        $list = warTexts209();
        $had = warIsAuto209($text);
        if (!$had) {
            if (count($list) >= WA_AUTOREPLY_MAX) jsonOut(['ok' => false, 'error' => 'Daftar auto reply sudah penuh (' . WA_AUTOREPLY_MAX . '). Hapus yang tidak dipakai di Widget & API.'], 400);
            $list[] = $text;
            warSave209(warClean209($list), $u['username']);
        }
        try { waAuditLog('autoreply_mark', $u['username'], $num, ['added' => $had ? 0 : 1]); } catch (\Throwable $e) {}
        $back = warRestore209($u['username']);
        jsonOut(['ok' => true, 'added' => !$had, 'texts' => warTexts209(), 'restored' => count($back), 'restored_numbers' => $back]);
        break;
    }

'''

s = rd(API)
if TAG not in s:
    assert NEED in s, 'butuh v1.2.208 dulu'
    s = rep(s, "define('DEI_VERSION', 'v1.2.208');   // v1.2.208:",
            "define('DEI_VERSION', 'v1.2.209');   // " + TAG + " — auto reply WA Business dari HP tidak mengambil alih bot; v1.2.208:", what='DEI_VERSION')
    s = rep(s, "function waSetMode($from, $mode, $reason = '') {", LIB + "function waSetMode($from, $mode, $reason = '') {", what='lib')
    s = rep(s, "    case 'wa_set_mode': {", CASES + "    case 'wa_set_mode': {", what='cases')
    # echo handler
    s = rep(s, "                if ($etext === '') continue;\n                try {\n                    $eid = (string)($echo['id'] ?? '');",
            "                if ($etext === '') continue;\n"
            "                $eauto = false; try { $eauto = warIsAuto209($etext); } catch (\\Throwable $e) {}   // " + TAG + "\n"
            "                try {\n                    $eid = (string)($echo['id'] ?? '');", what='echo auto')
    s = rep(s, "logMutate(function (&$elogs) use ($eid, $etext, $eto, &$dup, $emedia) {",
            "logMutate(function (&$elogs) use ($eid, $etext, $eto, &$dup, $emedia, $eauto) {", what='echo use')
    s = rep(s, "'channel' => 'whatsapp', 'dir' => 'manual', 'src' => 'hp', 'echo_id' => $eid,",
            "'channel' => 'whatsapp', 'dir' => 'manual', 'src' => $eauto ? 'hp_auto' : 'hp', 'echo_id' => $eid,", what='echo src')
    s = rep(s, "                        waSetMode($eto, 'human', 'agent_reply'); // agent balas dari HP = ambil alih -> bot mundur\n"
               "                        $ecl = waClaimGet($eto);   // v1.2.58: atribusikan ke pemegang claim bila ada\n"
               "                        deiRecordAgentReply($eto, $ecl ? ($ecl['agent_username'] ?? '(HP)') : '(HP)', 'hp');\n"
               "                        convReply($eto, 'agent');   // v1.2.56\n"
               "                        if ($keepCtx) { $eh = waLoadHistory($eto); $eh[] = ['role' => 'assistant', 'content' => $etext]; waSaveHistory($eto, $eh); }\n",
            "                        if (!$eauto) {   // " + TAG + ": auto reply WA Business tidak mengambil alih bot\n"
            "                        waSetMode($eto, 'human', 'agent_reply'); // agent balas dari HP = ambil alih -> bot mundur\n"
            "                        $ecl = waClaimGet($eto);   // v1.2.58: atribusikan ke pemegang claim bila ada\n"
            "                        deiRecordAgentReply($eto, $ecl ? ($ecl['agent_username'] ?? '(HP)') : '(HP)', 'hp');\n"
            "                        convReply($eto, 'agent');   // v1.2.56\n"
            "                        if ($keepCtx) { $eh = waLoadHistory($eto); $eh[] = ['role' => 'assistant', 'content' => $etext]; waSaveHistory($eto, $eh); }\n"
            "                        }\n", what='echo takeover')
    # wa_thread: src pesan
    s = rep(s, "                       'ch' => (string)($e['wa_ch'] ?? ''),   // v1.2.98: multi-nomor\n",
            "                       'ch' => (string)($e['wa_ch'] ?? ''),   // v1.2.98: multi-nomor\n"
            "                       'src' => in_array((string)($e['src'] ?? ''), ['hp', 'hp_auto'], true) ? (string)$e['src'] : '',   // " + TAG + "\n", what='thread src')
    save(API, s)
else: print('sudah', API)

JS_LIB = r'''  /* ---- v1.2.209: autoreply-hp — auto reply WA Business dari HP ---- */
  function warNote209(m) {
    if (!m || m.dir !== 'manual' || !m.a) return '';
    if (m.src === 'hp_auto') return '<div class="war-note" title="Pesan ini sama dengan teks auto reply di Widget & API, jadi bot tetap aktif">' + ico('bot', 11) + ' Auto reply WhatsApp Business (HP) — bot tetap aktif</div>';
    if (m.src === 'hp' && waState.isAdmin) return '<div class="war-note"><a href="#" class="war-mark" data-ts="' + esc(m.ts) + '" title="Pesan ini otomatis dari aplikasi WhatsApp Business? Tandai supaya pesan yang sama tidak menghentikan bot">Dari HP · tandai sebagai auto reply</a></div>';
    return '';
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('.war-mark'); if (!a) return;
    e.preventDefault();
    var num = waState.current; if (!num) return;
    if (!confirm('Tandai pesan ini sebagai auto reply WhatsApp Business?\n\nPesan dari HP dengan teks yang sama tidak akan lagi menghentikan bot. Chat yang terlanjur pindah ke mode manusia karena pesan ini dikembalikan ke bot.')) return;
    api('wa_autoreply_mark', { method: 'POST', body: { number: num, ts: a.dataset.ts } }).then(function (r) {
      if (r && r.ok) { toast((r.added ? 'Ditambahkan ke daftar auto reply. ' : 'Sudah ada di daftar auto reply. ') + (r.restored ? r.restored + ' chat dikembalikan ke bot.' : '')); fetchWaConvs(); fetchWaThread(num, true); }
      else toast((r && r.error) || 'Gagal menandai.', true);
    });
  });
  function warLoad209() {
    var box = $('#warList'); if (!box) return;
    var draw = function (texts) {
      box.innerHTML = (texts.length ? texts : ['']).map(function (t) {
        return '<div class="war-row" style="display:flex;gap:6px;align-items:flex-start;margin-bottom:6px"><textarea class="war-t" rows="2" maxlength="1500" placeholder="Tempel teks Away message / Greeting message persis seperti di HP" style="flex:1">' + esc(t) + '</textarea>' +
          '<button type="button" class="btn ghost sm war-del" title="Hapus">' + ico('trash-2', 13) + '</button></div>';
      }).join('');
      $$('#warList .war-del').forEach(function (b) { b.onclick = function () { var r = b.closest('.war-row'); if ($$('#warList .war-row').length > 1) r.remove(); else r.querySelector('textarea').value = ''; }; });
    };
    api('wa_autoreply_get').then(function (r) {
      if (!r || !r.ok) return;
      draw(r.texts || []);
      $('#warInfo').textContent = r.updated_at ? 'Terakhir diubah ' + r.updated_at + (r.by ? ' oleh ' + r.by : '') : '';
      $('#btnWarAdd').onclick = function () { if ($$('#warList .war-row').length >= (r.max || 10)) { toast('Maksimal ' + (r.max || 10) + ' teks.', true); return; } var cur = $$('#warList .war-t').map(function (x) { return x.value; }); cur.push(''); draw(cur); };
      $('#btnWarSave').onclick = function () {
        var btn = this; btn.disabled = true;
        var texts = $$('#warList .war-t').map(function (x) { return x.value.trim(); }).filter(Boolean);
        api('wa_autoreply_save', { method: 'POST', body: { texts: texts, restore: $('#war_restore').checked } }).then(function (x) {
          btn.disabled = false;
          if (x && x.ok) { toast('Daftar auto reply tersimpan.' + (x.restored ? ' ' + x.restored + ' chat dikembalikan ke bot.' : '')); warLoad209(); loaded.wachat = false; }
          else toast((x && x.error) || 'Gagal menyimpan.', true);
        });
      };
    });
  }
'''

s = rd(JS)
if TAG not in s:
    s = rep(s, "  function tfBadgeHtml(tp) {", JS_LIB + "  function tfBadgeHtml(tp) {", what='js lib')
    s = rep(s, "edt: m.edited, del: m.deleted });   // v1.2.121; v1.2.200: edit-hapus-pesan\n",
            "edt: m.edited, del: m.deleted });   // v1.2.121; v1.2.200: edit-hapus-pesan\n"
            "      if (m.a && !_fotoOnly) h += warNote209(m);   // " + TAG + "\n", what='bubble note')
    s = rep(s, "      if ($('#wa_alert_phone')) $('#wa_alert_phone').value = (s.wa_alert && s.wa_alert.phone) || '';   // v1.2.179: notif-putus-wa\n",
            "      if ($('#wa_alert_phone')) $('#wa_alert_phone').value = (s.wa_alert && s.wa_alert.phone) || '';   // v1.2.179: notif-putus-wa\n"
            "      warLoad209();   // " + TAG + "\n", what='widget load')
    save(JS, s)
else: print('sudah', JS)

HT_CARD = '''      <!-- v1.2.209: autoreply-hp -->
      <div class="card" data-role-card="super_admin,admin" id="warCard"><h3>Auto reply WhatsApp Business di HP</h3>
        <div class="desc">Pesan yang dikirim dari HP biasanya dianggap balasan agent, sehingga bot berhenti membalas chat itu. Akibatnya <b>Away message</b> atau <b>Greeting message</b> otomatis dari aplikasi WhatsApp Business ikut menghentikan bot. Tempel teks auto reply tersebut di sini (persis seperti di HP; huruf besar/kecil dan spasi diabaikan). Pesan dari HP dengan teks yang sama tetap tercatat di chat, tetapi bot tetap aktif. Lebih rapi lagi bila auto reply di HP dimatikan saat Jam Aktif AI sudah menangani jam di luar kerja.</div>
        <div id="warList"></div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:4px">
          <button class="btn ghost sm" id="btnWarAdd" type="button">+ Tambah teks</button>
          <label style="display:inline-flex;gap:6px;align-items:center;font-size:13px"><input type="checkbox" id="war_restore" checked> Kembalikan ke bot chat yang terlanjur pindah ke mode manusia karena auto reply ini</label>
        </div>
        <button class="btn" id="btnWarSave" type="button" style="margin-top:10px"><span data-ico="save" data-ico-size="15"></span> Simpan Daftar Auto Reply</button>
        <div class="help" id="warInfo" style="margin-top:6px"></div>
        <div class="help">Bisa juga dari chat: pada pesan dari HP, klik <b>tandai sebagai auto reply</b>. Teks yang diubah di HP harus diubah juga di sini.</div>
      </div>
'''
HT_CSS = '  .war-note{font-size:11px;color:var(--muted);text-align:right;margin:-2px 8px 8px}.war-note a{color:var(--muted)}\n'

s = rd(HT)
if TAG not in s:
    s = rep(s, '<script src="app.js?v=1.2.208"></script><!-- v1.2.208: sales-untag -->',
            '<script src="app.js?v=1.2.209"></script><!-- ' + TAG + ' --><!-- v1.2.208: sales-untag -->', what='app.js?v')
    s = rep(s, '      <!-- v1.2.91: wa-api — WhatsApp API resmi dengan bantuan tim DEI -->', HT_CARD + '      <!-- v1.2.91: wa-api — WhatsApp API resmi dengan bantuan tim DEI -->', what='card')
    s = rep(s, '</style>', HT_CSS + '</style>', n=s.count('</style>') and 1, what='css') if s.count('</style>') == 1 else s.replace('</style>', HT_CSS + '</style>', 1)
    save(HT, s)
else: print('sudah', HT)
print('patch v1.2.209 selesai')
