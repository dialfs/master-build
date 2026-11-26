#!/usr/bin/env python3
"""v1.2.222 (notif-wa): notifikasi tim lewat WhatsApp dari salah satu nomor bisnis tenant.
- Widget & API > kartu "Notifikasi Tim via WhatsApp" (Super Admin/Admin): aktif, nomor pengirim (WAHA; nomor Meta tidak bisa),
  mode per jenis (pengingat jatuh tempo & laporan mingguan: email / WhatsApp / keduanya; task baru, lead untuk Sales,
  chat diserahkan: mati / WhatsApp), nomor WA tiap anggota tim, kirim uji, riwayat 300 kiriman (data/notif-wa-log.json).
- Profil Saya > "WhatsApp untuk Notifikasi" (isi nomor sendiri + kirim uji).
- Pesan dari nomor tim ke nomor bisnis tidak dijawab bot (waGetMode -> human) selama fitur aktif.
- API: ntf_get, ntf_save, ntf_me, update_own_wa, ntf_test. Batas 20 notifikasi/jam per nomor.
Butuh v1.2.221. Idempoten. Pakai: patch_v12222.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H + '/dei-tenant'
TD = os.path.dirname(os.path.abspath(__file__))
TAG = 'v1.2.222: notif-wa'; NEED = 'v1.2.221: laporan-sales'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12222-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
rd = lambda f: open(os.path.join(TD, 'src', f), encoding='utf-8').read()
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'
C = '   // ' + TAG

# ======================= api =======================
s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API)
else:
    assert NEED in s, 'v1.2.221 belum terpasang di ' + API
    s = rep(s, "define('DEI_VERSION', 'v1.2.221');   // v1.2.221:",
            "define('DEI_VERSION', 'v1.2.222');   // " + TAG + " — notifikasi tim (pengingat, laporan mingguan, task, lead, transfer chat) lewat WhatsApp dari nomor bisnis pilihan; v1.2.221:", what='ver')
    s = rep(s, "\nfunction deiGuardAgentPrivate($u, $num) {", "\n" + rd('lib222.php') + "function deiGuardAgentPrivate($u, $num) {", what='lib')
    s = rep(s, "    case 'crm_weekly_get': {", rd('cases222.php') + "    case 'crm_weekly_get': {", what='cases')
    s = rep(s, "'crm_badge', 'crm_remind_test', 'crm_sales_perf', 'sales_rep',", "'crm_badge', 'crm_remind_test', 'crm_sales_perf', 'sales_rep', 'ntf_me', 'update_own_wa', 'ntf_test',", what='sales-actions')
    # bot tidak menjawab nomor tim
    s = rep(s, "    if (waIsGroup($from)) return 'human';   // v1.2.170: grup-wa\n    $modes = readJson(WA_MODES_FILE, []);",
            "    if (waIsGroup($from)) return 'human';   // v1.2.170: grup-wa\n    if (ntfIsTeamNum222($from)) return 'human';" + C + " — nomor tim (penerima notifikasi) tidak dijawab bot\n    $modes = readJson(WA_MODES_FILE, []);", what='mode')
    # pengingat jatuh tempo
    s = rep(s, "        $cnt = count((array)($it['tasks'] ?? [])) + count((array)($it['fu'] ?? []));\n        if ($to !== '') {",
            "        $cnt = count((array)($it['tasks'] ?? [])) + count((array)($it['fu'] ?? []));\n"
            "        $first = '';\n"
            "        if (ntfWantWa222('crm_remind') && ntfUserWa222($users[$un]) !== '') {" + C + "\n"
            "            [$wt222, $first] = ntfRemindText222($users[$un], $it, $today);\n"
            "            $rw222 = ntfWaSend222(ntfUserWa222($users[$un]), $wt222, 'crm_remind', (string)($users[$un]['name'] ?? $un));\n"
            "            if (!empty($rw222['ok'])) { $res['wa'] = ($res['wa'] ?? 0) + 1; if (ntfSkipMail222('crm_remind', $users[$un])) $to = ''; }\n"
            "            else { $res['wa_fail'] = ($res['wa_fail'] ?? 0) + 1; error_log('[crm-remind] wa: ' . ($rw222['error'] ?? '')); }\n"
            "        }\n"
            "        if ($to !== '') {", what='remind')
    s = rep(s, "            $first = $r['first'];\n        } else $first = '';\n", "            $first = $r['first'];\n        }\n", what='remind-first')
    # laporan mingguan
    s = rep(s, "        if ($em === '' || isset($seen[$em])) continue;\n        $nm = trim((string)($x['name'] ?? '')) ?: (string)$x['username'];\n        if (in_array($r, ['super_admin', 'admin'], true) && ($cf['admins'] || $onlyUser !== ''))",
            "        if ($em === '' || isset($seen[$em])) continue;\n        if ($onlyUser === '' && ntfSkipMail222('crm_weekly', $x)) continue;" + C + "\n        $nm = trim((string)($x['name'] ?? '')) ?: (string)$x['username'];\n        if (in_array($r, ['super_admin', 'admin'], true) && ($cf['admins'] || $onlyUser !== ''))", what='weekly-skip')
    s = rep(s, "    $st['done'] = !$left; $st['period'] = [$from, $to];\n    if (empty($GLOBALS['dei_dry'])) writeJson(CRM_WEEKLY_FILE, $st);\n    return ($res['mail'] || $res['fail']) ? $res : null;",
            "    if (!$left && ntfWantWa222('crm_weekly')) foreach (crmWeeklyWaRecipients222($cf) as [$wa222, $nm222, $sid222]) {" + C + "\n"
            "        $k = 'w' . md5($wa222); if (!empty($st['sent'][$k])) continue;\n"
            "        if ($n >= 15) { $left = true; break; }\n"
            "        $n++;\n"
            "        $rep = $sid222 === null ? $full : crmPerf217($from, $to, $sid222);\n"
            "        $rw = ntfWaSend222($wa222, ntfWeeklyText222($nm222, $rep, $sid222 !== null && count((array)$sid222) === 1), 'crm_weekly', $nm222);\n"
            "        if (!empty($rw['ok'])) $res['wa'] = ($res['wa'] ?? 0) + 1; else $res['wa_fail'] = ($res['wa_fail'] ?? 0) + 1;\n"
            "        $st['sent'][$k] = 1;\n"
            "    }\n"
            "    $st['done'] = !$left; $st['period'] = [$from, $to];\n    if (empty($GLOBALS['dei_dry'])) writeJson(CRM_WEEKLY_FILE, $st);\n"
            "    return ($res['mail'] || $res['fail'] || !empty($res['wa']) || !empty($res['wa_fail'])) ? $res : null;", what='weekly-wa')
    # task ditugaskan
    s = rep(s, "                if ($as !== '' && !isset($validUsers[$as]) && $as !== ($t['assignee'] ?? '')) return 'Pengguna yang ditugaskan tidak ditemukan.';\n                $t['assignee'] = $as;",
            "                if ($as !== '' && !isset($validUsers[$as]) && $as !== ($t['assignee'] ?? '')) return 'Pengguna yang ditugaskan tidak ditemukan.';\n                $GLOBALS['ntf_prev_as222'] = (string)($t['assignee'] ?? '');" + C + "\n                $t['assignee'] = $as;", what='task-prev')
    s = rep(s, "        if ($ld215 !== '' && empty($r['dup'])) crmLog215($ld215, 'Task dibuat: ' . $r['task']['title'], $u);   // v1.2.215: crm-aktivitas\n",
            "        if ($ld215 !== '' && empty($r['dup'])) crmLog215($ld215, 'Task dibuat: ' . $r['task']['title'], $u);   // v1.2.215: crm-aktivitas\n"
            "        if (empty($r['dup'])) { try { ntfTaskAssigned222($r['task'], $GLOBALS['ntf_prev_as222'] ?? null, $me, $meName); } catch (\\Throwable $e) {} }" + C + "\n", what='task-ntf')
    # lead untuk sales
    s = rep(s, "        $slDel208 = false;   // v1.2.208: sales-untag\n",
            "        if ($sid !== '' && $sid !== $prevId) ntfLeadAssigned222($num, $sid, $u);" + C + "\n        $slDel208 = false;   // v1.2.208: sales-untag\n", what='lead-tag')
    # transfer chat
    s = rep(s, "            sendPushToUsers([$to], 'Chat diserahkan ke Anda', '+' . $num . ($nm ? ' (' . $nm . ')' : '') . ' — dari ' . $u['username'], deiDashboardUrl());\n",
            "            sendPushToUsers([$to], 'Chat diserahkan ke Anda', '+' . $num . ($nm ? ' (' . $nm . ')' : '') . ' — dari ' . $u['username'], deiDashboardUrl());\n"
            "            ntfUserEvent222($to, 'chat_assign', 'Chat diserahkan ke Anda', 'Chat WhatsApp +' . $num . ($nm ? ' (' . $nm . ')' : '') . ' diserahkan ke Anda oleh ' . (string)($u['name'] ?? $u['username']) . '. Buka Percakapan WA untuk membalas.', (string)$u['username']);" + C + "\n", what='chat-assign')
    save(API, s)

# ======================= app.js =======================
s = open(JS, encoding='utf-8').read()
if TAG in s: print('SUDAH', JS)
else:
    assert NEED in s, 'v1.2.221 belum terpasang di ' + JS
    s = rep(s, "  /* ---- v1.2.218: sales-di-lead — assign Sales dari kartu Leads ---- */",
            rd('js222.js').replace('  /* ====', '  /* ' + TAG + ' */\n  /* ====', 1) + "\n\n  /* ---- v1.2.218: sales-di-lead — assign Sales dari kartu Leads ---- */", what='js')
    s = rep(s, "    widget: function () { loadWidget(); loadCentral(); wireCentralButtons(); },",
            "    widget: function () { loadWidget(); loadCentral(); wireCentralButtons(); ntfLoad222(); },   // " + TAG, what='loader-widget')
    s = rep(s, "    profile: loadProfile,", "    profile: function () { loadProfile(); ntfProfile222(); },   // " + TAG, what='loader-profile')
    s = rep(s, "    { id: 'laporan-sales', roles:",
            "    { id: 'notif-wa', roles: 'super_admin,admin,supervisor,wa_agent', t: 'Notifikasi tim lewat WhatsApp (pengingat, laporan, task, lead)', k: 'notifikasi whatsapp wa pengingat reminder jatuh tempo laporan mingguan task baru lead sales transfer chat nomor pengirim notif tim',   // " + TAG + "\n"
            "      s: ['Admin: buka <b>Widget &amp; API</b> &gt; <b>Notifikasi Tim via WhatsApp</b>. Nyalakan, lalu pilih <b>Nomor pengirim</b> dari nomor WhatsApp bisnis yang sudah terhubung (WAHA).', "
            "'Atur tiap jenis: pengingat jatuh tempo &amp; laporan mingguan bisa Email saja, WhatsApp saja, atau keduanya; task baru, lead untuk Sales, dan chat yang diserahkan bisa Mati atau WhatsApp.', "
            "'Isi nomor WhatsApp tiap anggota tim di kartu itu (atau masing-masing lewat <b>Profil Saya</b>), lalu klik <b>Uji</b>. Pesan dari nomor tim ke nomor bisnis tidak dijawab bot.'],\n"
            "      show: [{ tab: 'widget', el: '#ntfCard', title: 'Notifikasi Tim via WhatsApp', body: '<p>Pilih nomor pengirim, jenis notifikasi, dan nomor WhatsApp tim.</p>' }] },\n"
            "    { id: 'laporan-sales', roles:", what='help')
    save(JS, s)

# ======================= index.html =======================
CSS = '''  /* v1.2.222: notif-wa */
  .ntf-h{font-size:13.5px;margin:16px 0 6px}
  .ntf-t td{padding:7px 8px;vertical-align:middle}
'''
CARD = '''      <div class="card" data-role-card="super_admin,admin" id="ntfCard"><h3>Notifikasi Tim via WhatsApp</h3><!-- v1.2.222: notif-wa -->
        <div class="desc">Kirim pengingat &amp; notifikasi ke anggota tim lewat WhatsApp dari salah satu nomor bisnis di atas.</div>
        <div id="ntfBody"><div class="help">Memuat…</div></div>
      </div>
'''
ME = '''      <!-- v1.2.222: notif-wa -->
      <div class="card" id="ntfMeCard" style="margin-bottom:16px;display:none">
        <h3 style="margin:0 0 6px 0;font-size:15px">WhatsApp untuk Notifikasi</h3>
        <p class="hint" style="font-size:12px;color:var(--muted);margin:0 0 10px">Pengingat jatuh tempo, task baru, dan notifikasi tim lain dikirim ke nomor ini. <span id="ntfMeNote"></span></p>
        <div style="margin-bottom:10px"><label style="display:block;font-size:13px;color:var(--muted);margin-bottom:4px">Nomor WhatsApp</label><input type="text" inputmode="tel" id="ntfMeWa" class="input" placeholder="08xxxxxxxxxx" autocomplete="tel"></div>
        <button class="btn" id="ntfMeSave" type="button">Simpan Nomor</button> <button class="btn ghost" id="ntfMeTest" type="button">Kirim uji</button>
      </div>
'''
s = open(HT, encoding='utf-8').read()
if TAG in s: print('SUDAH', HT)
else:
    assert NEED in s, 'v1.2.221 belum terpasang di ' + HT
    s = rep(s, "  /* v1.2.221: laporan-sales */\n", CSS + "  /* v1.2.221: laporan-sales */\n", what='css')
    s = rep(s, '      <div class="card" data-role-card="super_admin"><h3>WhatsApp Bot</h3>', CARD + '      <div class="card" data-role-card="super_admin"><h3>WhatsApp Bot</h3>', what='card')
    s = rep(s, '      <!-- v1.2.112: login-log -->\n      <div class="card" id="myLlCard"', ME + '      <!-- v1.2.112: login-log -->\n      <div class="card" id="myLlCard"', what='profile')
    s = rep(s, '<script src="app.js?v=1.2.221"></script>', '<script src="app.js?v=1.2.222"></script><!-- ' + TAG + ' -->', what='cache')
    save(HT, s)
print('selesai')
