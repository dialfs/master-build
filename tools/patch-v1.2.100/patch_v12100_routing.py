#!/usr/bin/env python3
"""v1.2.100 — Routing chat otomatis ke agent.
settings.routing = {enabled, method: 'load'|'rr', by_number, online_only, max_active}
- Kapan: chat butuh agent = mode manusia & belum diklaim (Mode AI: handoff kata kunci, batas balasan AI, chat yang
  sudah di mode manusia; Mode Manual: setiap pesan masuk). Juga antrean: saat agent online/Tersedia (heartbeat) dan
  tiap cron_tick pusat, chat yang menunggu (<= 24 jam) dibagikan.
- Siapa: WA Agent dalam batas kursi (Supervisor hanya cadangan bila tidak ada agent yang memenuhi).
  by_number: nomor bisnis pelanggan (kontak.wa_ch) -> tim (username supervisor) di whatsapp_api.team / wa_numbers[].team;
  tim = supervisor + WA Agent di bawahnya. online_only: dashboard aktif <= 2 menit. Status "Istirahat" selalu dilewati.
  max_active: chat yang sedang dipegang < batas (0 = tanpa batas).
- Pilih: load = chat dipegang paling sedikit (seri -> paling lama tidak mendapat chat); rr = paling lama tidak mendapat chat.
- Hasil: claim biasa (assigned_by '(otomatis)'), audit 'auto_assign', laporan agent 'assign', push ke agent.
UI: Tim & Agent › Routing Chat Otomatis (+ daftar agent tersedia), tombol status Tersedia/Istirahat di sidebar
(WA Agent & Supervisor, heartbeat 60 dtk), kolom Tim di kartu Nomor WhatsApp.
Pemakaian: python3 patch_v12100_routing.py <root dei-tenant>   (idempoten; backup *.bak-v12100-*)  Butuh v1.2.99."""
import sys, os, time, shutil
TEN = sys.argv[1]
STAMP = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.100: routing'

def patch(root, rel, pairs):
    p = os.path.join(root, rel)
    s = open(p, encoding='utf-8').read()
    if MARK in s: print('sudah dipatch:', rel); return
    if 'v1.2.99: lisensi-nomor' not in s: sys.exit('GAGAL: v1.2.99 belum terpasang di ' + rel)
    for old, new in pairs:
        n = s.count(old)
        if n != 1: sys.exit(f'GAGAL {rel}: anchor {n}x:\n{old[:300]}')
        s = s.replace(old, new)
    shutil.copy2(p, p + '.bak-v12100-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

PHP_FUNCS = r'''
/* v1.2.100: routing — bagi chat otomatis ke agent (lihat docstring patch v1.2.100). */
if (!defined('AGENT_PRESENCE_FILE')) define('AGENT_PRESENCE_FILE', DATA_DIR . '/agent-presence.json');
if (!defined('ROUTING_STATE_FILE')) define('ROUTING_STATE_FILE', DATA_DIR . '/routing-state.json');
if (!defined('PRESENCE_ONLINE_SEC')) define('PRESENCE_ONLINE_SEC', 120);
function deiRoutingConf($s = null) {
    if ($s === null) $s = getSettings();
    $r = is_array($s['routing'] ?? null) ? $s['routing'] : [];
    return [
        'enabled'     => !empty($r['enabled']),
        'method'      => (($r['method'] ?? 'load') === 'rr') ? 'rr' : 'load',
        'by_number'   => !empty($r['by_number']),
        'online_only' => !array_key_exists('online_only', $r) || !empty($r['online_only']),
        'max_active'  => max(0, min(500, (int)($r['max_active'] ?? 0))),
    ];
}
function deiPresenceAll() { $p = readJson(AGENT_PRESENCE_FILE, []); return is_array($p) ? $p : []; }
function deiPresenceOnline($row) {
    return is_array($row) && ($row['status'] ?? 'available') !== 'away' && (time() - (int)($row['seen'] ?? 0)) <= PRESENCE_ONLINE_SEC;
}
// Catat heartbeat (+ ubah status). Hasil: [online sebelum, online sesudah].
function deiPresenceTouch($username, $status = null) {
    return deiWithLock('agent-presence', function () use ($username, $status) {
        $all = deiPresenceAll();
        $row = is_array($all[$username] ?? null) ? $all[$username] : ['status' => 'available'];
        $was = deiPresenceOnline($row);
        $row['seen'] = time();
        if ($status !== null) $row['status'] = ($status === 'away') ? 'away' : 'available';
        $all[$username] = $row;
        writeJson(AGENT_PRESENCE_FILE, $all);
        return [$was, deiPresenceOnline($row)];
    });
}
// Daftar tim = supervisor yang ada.
function deiTeamsList($users = null) {
    if ($users === null) $users = readJson(USERS_FILE, []);
    $out = [];
    foreach ((array)$users as $u) {
        if (($u['role'] ?? '') === 'supervisor') $out[] = ['username' => (string)($u['username'] ?? ''), 'name' => (string)($u['name'] ?? ($u['username'] ?? ''))];
    }
    return $out;
}
// Tim yang menangani nomor bisnis $ch ('' = semua agent).
function deiChanTeam($ch, $s = null) {
    if ($s === null) $s = getSettings();
    $ch = (string)$ch;
    if ($ch !== '' && $ch !== 'utama') {
        foreach (waNumbersRaw($s) as $x) { if ((string)$x['id'] === $ch) return trim((string)($x['team'] ?? '')); }
    }
    return trim((string)($s['whatsapp_api']['team'] ?? ''));
}
function deiRouteCandidates($conf, $team, $users, $claims, $pres, $role) {
    $active = [];
    foreach ((array)$claims as $c) { $a = (string)($c['agent_username'] ?? ''); if ($a !== '') $active[$a] = ($active[$a] ?? 0) + 1; }
    $out = [];
    foreach ((array)$users as $u) {
        $un = (string)($u['username'] ?? ''); $r = (string)($u['role'] ?? '');
        if ($un === '' || $r !== $role) continue;
        if (!deiSeatAllowed($un, $r, $users)) continue;
        if ($team !== '' && ($r === 'supervisor' ? $un !== $team : deiAgentSpv($u, $users) !== $team)) continue;
        $p = $pres[$un] ?? null;
        if (is_array($p) && ($p['status'] ?? '') === 'away') continue;      // Istirahat: selalu dilewati
        if ($conf['online_only'] && !deiPresenceOnline($p)) continue;
        $n = $active[$un] ?? 0;
        if ($conf['max_active'] > 0 && $n >= $conf['max_active']) continue;
        $out[$un] = $n;
    }
    return $out;
}
// Serahkan chat $num ke agent secara otomatis. Hasil: username, atau '' bila tidak dibagikan.
// $ch = nomor bisnis yang dihubungi (null = dari kontak).
function deiRouteAssign($num, $ch = null, $s = null) {
    try {
        if ($s === null) $s = getSettings();
        $conf = deiRoutingConf($s);
        if (!$conf['enabled']) return '';
        $num = waNormNum($num);
        if ($num === '') return '';
        if ($ch === null || $ch === '') { $c = waContactGet($num); $ch = (string)(is_array($c) ? ($c['wa_ch'] ?? '') : ''); }
        $team = $conf['by_number'] ? deiChanTeam($ch, $s) : '';
        $pick = (string)deiWithLock('wa-routing', function () use ($num, $conf, $team) {
            $claims = waClaimGetAll();
            if (!empty($claims[$num])) return '';
            $users = readJson(USERS_FILE, []);
            $pres = deiPresenceAll();
            $cand = deiRouteCandidates($conf, $team, $users, $claims, $pres, 'wa_agent');
            if (!$cand) $cand = deiRouteCandidates($conf, $team, $users, $claims, $pres, 'supervisor');   // cadangan
            if (!$cand) return '';
            $st = readJson(ROUTING_STATE_FILE, []);
            $last = is_array($st['last'] ?? null) ? $st['last'] : [];
            $best = null; $bestKey = null;
            foreach ($cand as $un => $n) {
                $k = [$conf['method'] === 'load' ? $n : 0, (int)($last[$un] ?? 0), $un];
                if ($bestKey === null || $k < $bestKey) { $bestKey = $k; $best = $un; }
            }
            $now = time();
            $seq = (int)($st['seq'] ?? 0) + 1;   // urutan, bukan detik: beberapa chat bisa dibagikan di detik yang sama
            $st['seq'] = $seq;
            $last[$best] = $seq;
            $st['last'] = $last;
            writeJson(ROUTING_STATE_FILE, $st);
            waClaimSet($num, ['agent_username' => $best, 'claimed_at' => $now, 'last_agent_activity' => $now,
                              'assigned_by' => '(otomatis)', 'auto' => true]);
            return $best;
        });
        if ($pick === '') return '';
        try { waAuditLog('auto_assign', '(otomatis)', $num, ['to_agent' => $pick, 'team' => $team, 'method' => $conf['method']]); } catch (\Throwable $e) {}
        agentEvent('assign', $pick, $num, ['by' => '(otomatis)', 'from' => '']);
        try {
            $nm = waContactName($num);
            sendPushToUsers([$pick], 'Chat baru untuk Anda', '+' . $num . ($nm ? ' (' . $nm . ')' : '') . ' — dibagikan otomatis', deiDashboardUrl());
        } catch (\Throwable $e) { error_log('routing push: ' . $e->getMessage()); }
        return $pick;
    } catch (\Throwable $e) { error_log('deiRouteAssign: ' . $e->getMessage()); return ''; }
}
// Bagikan chat yang menunggu agent (belum diklaim, <= 24 jam, mode manusia). Hasil: jumlah dibagikan.
function deiRouteDrain($max = 10, $s = null) {
    try {
        if ($s === null) $s = getSettings();
        if (!deiRoutingConf($s)['enabled']) return 0;
        $cs = convStateReadAll();
        if (!is_array($cs) || !$cs) return 0;
        $claims = waClaimGetAll();
        $manual = deiIsManual($s);
        $now = time();
        $wait = [];
        foreach ($cs as $num => $st) {
            $since = (int)(is_array($st) ? ($st['guest_waiting_since'] ?? 0) : 0);
            $num = (string)$num;
            if ($since <= 0 || $now - $since > 86400 || !empty($claims[$num])) continue;
            if (!$manual && waGetMode($num) !== 'human') continue;
            $wait[$num] = $since;
        }
        asort($wait);
        $n = 0; $tries = 0;
        foreach (array_keys($wait) as $num) {
            if ($n >= $max || ++$tries > 40) break;
            if (deiRouteAssign($num, null, $s) !== '') $n++;
        }
        return $n;
    } catch (\Throwable $e) { error_log('deiRouteDrain: ' . $e->getMessage()); return 0; }
}
'''

PHP_ENDPOINT = r'''    /* ---------- v1.2.100: routing — status agent (heartbeat Tersedia/Istirahat) ---------- */
    case 'agent_presence': {
        $u  = requireAuth(['super_admin', 'admin', 'supervisor', 'wa_agent']);
        $in = bodyInput();
        $op = (string)($in['op'] ?? 'ping');
        if ($op === 'list') {
            if (!deiIsLead($u['role'] ?? '')) jsonOut(['ok' => false, 'error' => 'Tidak diizinkan.'], 403);
            $users = readJson(USERS_FILE, []);
            $pres = deiPresenceAll();
            $scope = deiSpvScope($u, $users);
            $act = [];
            foreach (waClaimGetAll() as $c) { $a = (string)($c['agent_username'] ?? ''); if ($a !== '') $act[$a] = ($act[$a] ?? 0) + 1; }
            $rows = [];
            foreach ((array)$users as $x) {
                $r = (string)($x['role'] ?? ''); $un = (string)($x['username'] ?? '');
                if (!in_array($r, ['wa_agent', 'supervisor'], true)) continue;
                if ($scope !== null && !isset($scope[$un])) continue;
                $p = $pres[$un] ?? null;
                $rows[] = ['username' => $un, 'name' => (string)($x['name'] ?? $un), 'role' => $r,
                           'team' => $r === 'supervisor' ? $un : deiAgentSpv($x, $users),
                           'online' => deiPresenceOnline($p), 'status' => is_array($p) ? (string)($p['status'] ?? 'available') : 'available',
                           'seen' => is_array($p) ? (int)($p['seen'] ?? 0) : 0, 'active' => (int)($act[$un] ?? 0),
                           'seat_ok' => deiSeatAllowed($un, $r, $users)];
            }
            jsonOut(['ok' => true, 'agents' => $rows, 'routing' => deiRoutingConf(), 'now' => time()]);
        }
        $status = ($op === 'set') ? ((($in['status'] ?? '') === 'away') ? 'away' : 'available') : null;
        list($was, $isOn) = deiPresenceTouch((string)$u['username'], $status);
        $assigned = 0;
        if ($isOn && in_array($u['role'] ?? '', ['wa_agent', 'supervisor'], true)) $assigned = deiRouteDrain(5);
        $row = deiPresenceAll()[(string)$u['username']] ?? [];
        jsonOut(['ok' => true, 'status' => (string)($row['status'] ?? 'available'), 'online' => $isOn, 'assigned' => $assigned]);
        break;
    }

'''

php = [
    ("define('DEI_VERSION', 'v1.2.99');", "define('DEI_VERSION', 'v1.2.100');"),
    ("// === /v1.2.0 WA Claim System Helpers ========================================\n",
     PHP_FUNCS + "\n// === /v1.2.0 WA Claim System Helpers ========================================\n"),
    # pemicu: chat butuh agent
    ("    if ($mode === 'human') {\n        // Admin is handling this number — record, notify, do NOT auto-reply.\n",
     "    if ($mode === 'human') {\n        // Admin is handling this number — record, notify, do NOT auto-reply.\n"
     "        deiRouteAssign($from, (string)($wa['_ch'] ?? ''), $s);   // v1.2.100: routing (lewati bila sudah diklaim / routing mati)\n"),
    # antrean di cron pusat
    ("        try { $r['media_purged'] = deiWaMediaSweep(); } catch (\\Throwable $e) { $r['err_media'] = $e->getMessage(); }   // v1.2.94: wa-media\n",
     "        try { $r['media_purged'] = deiWaMediaSweep(); } catch (\\Throwable $e) { $r['err_media'] = $e->getMessage(); }   // v1.2.94: wa-media\n"
     "        try { $r['routed'] = deiRouteDrain(20, $s); } catch (\\Throwable $e) { $r['err_routing'] = $e->getMessage(); }   // v1.2.100: routing\n"),
    # endpoint status
    ("    /* ---------- v1.2.98: multi-nomor — kelola nomor WhatsApp tambahan ---------- */\n",
     PHP_ENDPOINT + "    /* ---------- v1.2.98: multi-nomor — kelola nomor WhatsApp tambahan ---------- */\n"),
    # team_info membawa routing
    ("            'team'        => deiTeamConf($s),\n",
     "            'team'        => deiTeamConf($s),\n"
     "            'routing'     => deiRoutingConf($s),   // v1.2.100\n"
     "            'teams'       => deiTeamsList($users),\n"),
    # simpan pengaturan (Super Admin lewat merge; Admin eksplisit) + rapikan
    ("            if (isset($incoming['ai_limit']) && is_array($incoming['ai_limit'])) {   // v1.2.97: batas-ai\n",
     "            if (isset($incoming['routing']) && is_array($incoming['routing'])) {   // v1.2.100: routing\n"
     "                $merged['routing'] = deiMergeSettings($current['routing'] ?? [], $incoming['routing']);\n"
     "            }\n"
     "            if (isset($incoming['ai_limit']) && is_array($incoming['ai_limit'])) {   // v1.2.97: batas-ai\n"),
    ("        if (isset($merged['ai_limit']) && is_array($merged['ai_limit'])) $merged['ai_limit'] = deiAiLimitConf($merged);   // v1.2.97: batas-ai\n",
     "        if (isset($merged['ai_limit']) && is_array($merged['ai_limit'])) $merged['ai_limit'] = deiAiLimitConf($merged);   // v1.2.97: batas-ai\n"
     "        if (isset($merged['routing']) && is_array($merged['routing'])) $merged['routing'] = deiRoutingConf($merged);   // v1.2.100: routing\n"),
    # nomor -> tim
    ("            if ($isSa) $p['phone_number_id'] = (string)($wa['phone_number_id'] ?? '');\n",
     "            if ($isSa) $p['phone_number_id'] = (string)($wa['phone_number_id'] ?? '');\n"
     "            $p['team'] = (string)($wa['team'] ?? '');   // v1.2.100: routing\n"),
    ("                          'waha_session' => (string)($x['waha_session'] ?? '')];\n",
     "                          'waha_session' => (string)($x['waha_session'] ?? ''), 'team' => (string)($x['team'] ?? '')];   // v1.2.100\n"),
    ("                     'limit' => $lim, 'vendor' => deiBrandVendor(),   // v1.2.99: lisensi-nomor\n",
     "                     'limit' => $lim, 'vendor' => deiBrandVendor(),   // v1.2.99: lisensi-nomor\n"
     "                     'teams' => deiTeamsList(), 'routing_by_number' => deiRoutingConf($s)['by_number'],   // v1.2.100\n"),
    ("            $label = mb_substr(trim((string)($in['label'] ?? '')), 0, 40);\n            if ($id === 'utama') {\n                $s['whatsapp_api']['label'] = $label;\n",
     "            $label = mb_substr(trim((string)($in['label'] ?? '')), 0, 40);\n"
     "            $teamIn = array_key_exists('team', $in) ? trim((string)$in['team']) : null;   // v1.2.100: routing\n"
     "            if ($teamIn !== null && $teamIn !== '' && !in_array($teamIn, array_column(deiTeamsList(), 'username'), true)) jsonOut(['ok' => false, 'error' => 'Tim (supervisor) tidak ditemukan.'], 400);\n"
     "            if ($id === 'utama') {\n                $s['whatsapp_api']['label'] = $label;\n"
     "                if ($teamIn !== null) $s['whatsapp_api']['team'] = $teamIn;\n"),
    ("            $row['label'] = $label;\n",
     "            $row['label'] = $label;\n            if ($teamIn !== null) $row['team'] = $teamIn;   // v1.2.100\n"),
]
patch(TEN, 'api/index.php', php)

HTML_CARD = '''      <!-- v1.2.100: routing -->
      <div class="card" data-role-card="super_admin,admin" id="timRouteCard"><h3>Routing Chat Otomatis</h3>
        <div class="desc">Chat yang butuh agent langsung diserahkan ke satu agent — tidak perlu rebutan Claim. Mode AI: saat bot menyerahkan ke manusia (kata kunci handoff, batas balasan AI). Mode Manual: setiap chat baru. Chat yang belum kebagian menunggu di Unclaimed dan dibagikan begitu ada agent tersedia.</div>
        <div class="toggle-row"><div><div class="tt">Bagi chat otomatis ke agent</div><div class="td">Saklar utama. Mati = seperti sebelumnya (Claim manual &amp; Serahkan ke…).</div></div>
          <label class="switch"><input type="checkbox" id="rt_enabled"><span class="sl"></span></label></div>
        <div class="row"><label class="fl">Cara memilih agent</label><select id="rt_method">
          <option value="load">Beban teringan — agent dengan chat dipegang paling sedikit (seri: bergiliran)</option>
          <option value="rr">Bergiliran — bergantian rata ke semua agent</option></select></div>
        <div class="toggle-row"><div><div class="tt">Routing per nomor / cabang</div><div class="td">Chat ke nomor tertentu hanya untuk tim nomor itu (tim = Supervisor + WA Agent di bawahnya). Atur tim tiap nomor di Widget &amp; API › Nomor WhatsApp.</div></div>
          <label class="switch"><input type="checkbox" id="rt_bynum"><span class="sl"></span></label></div>
        <div class="toggle-row"><div><div class="tt">Hanya agent yang online</div><div class="td">Agent dihitung online bila dashboard-nya terbuka (2 menit terakhir). Agent berstatus Istirahat selalu dilewati.</div></div>
          <label class="switch"><input type="checkbox" id="rt_online"><span class="sl"></span></label></div>
        <div class="grid2"><div class="row"><label class="fl">Maks. chat dipegang per agent</label><input type="number" id="rt_max" min="0" max="500" step="1" value="0"><div class="help">0 = tanpa batas. Agent yang penuh dilewati sampai ada chat yang dilepas.</div></div></div>
        <div class="help">WA Agent didahulukan; Supervisor hanya menerima bila tidak ada agent yang memenuhi syarat.</div>
        <button class="btn" id="btnSaveRoute" type="button"><span data-ico="save" data-ico-size="15"></span> Simpan Routing</button>
        <div style="margin-top:14px"><div class="fl" style="font-weight:600;margin-bottom:6px">Status agent sekarang</div><div id="rtAgents" class="help">Memuat…</div></div>
      </div>

'''
patch(TEN, 'dashboard/chatbot-ai/index.html', [
    ('      <div class="card"><h3>Kursi Tim</h3>\n', HTML_CARD + '      <div class="card"><h3>Kursi Tim</h3>\n'),
    ('<button id="btnTour" type="button" title="Cari panduan &amp; tur (tekan /)">',
     '<button id="btnAvail" type="button" style="display:none" title="Status menerima chat otomatis"></button><!-- v1.2.100: routing --><button id="btnTour" type="button" title="Cari panduan &amp; tur (tekan /)">'),
    ('          <div class="row"><label class="fl">Label</label><input type="text" id="wn_label" maxlength="40"',
     '          <div class="row" id="wn_team_row"><label class="fl">Tim penanganan (routing)</label><select id="wn_team"></select><div class="help">Dipakai bila Routing per nomor aktif (Tim &amp; Agent). Tim = Supervisor + WA Agent di bawahnya.</div></div><!-- v1.2.100: routing -->\n'
     '          <div class="row"><label class="fl">Label</label><input type="text" id="wn_label" maxlength="40"'),
    ('<script src="app.js?v=1.2.99"></script><!-- v1.2.99: lisensi-nomor -->',
     '<script src="app.js?v=1.2.100"></script><!-- v1.2.100: routing -->'),
])

JS_ROUTE = r'''
  /* v1.2.100: routing — pengaturan + status agent */
  function rtLoad(r) {
    var c = (r && r.routing) || {};
    if (!$('#rt_enabled')) return;
    $('#rt_enabled').checked = !!c.enabled;
    $('#rt_method').value = c.method === 'rr' ? 'rr' : 'load';
    $('#rt_bynum').checked = !!c.by_number;
    $('#rt_online').checked = c.online_only !== false;
    $('#rt_max').value = c.max_active || 0;
    $('#btnSaveRoute').onclick = function () {
      var b = this; b.disabled = true;
      api('save_settings', { method: 'POST', body: { settings: { routing: {
        enabled: $('#rt_enabled').checked, method: $('#rt_method').value, by_number: $('#rt_bynum').checked,
        online_only: $('#rt_online').checked, max_active: Math.max(0, Math.min(500, Math.round(+$('#rt_max').value || 0)))
      } } } }).then(function (res) {
        b.disabled = false;
        toast(res && res.ok ? 'Routing tersimpan.' : ((res && res.error) || 'Gagal menyimpan.'), !(res && res.ok));
        rtAgents();
      }).catch(function () { b.disabled = false; });
    };
    rtAgents();
  }
  function rtAgents() {
    var box = $('#rtAgents'); if (!box) return;
    api('agent_presence', { method: 'POST', body: { op: 'list' } }).then(function (r) {
      if (!r || !r.ok) { box.textContent = (r && r.error) || 'Gagal memuat.'; return; }
      var a = r.agents || [];
      if (!a.length) { box.textContent = 'Belum ada WA Agent / Supervisor.'; return; }
      box.innerHTML = '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Agent</th><th>Tim</th><th>Status</th><th style="text-align:right">Dipegang</th></tr></thead><tbody>' +
        a.map(function (x) {
          var st = !x.seat_ok ? '<span class="tag" style="background:#fee2e2;color:#991b1b">Di luar kursi</span>'
            : x.status === 'away' ? '<span class="tag" style="background:#fef3c7;color:#92400e">Istirahat</span>'
            : x.online ? '<span class="tag" style="background:#d1fae5;color:#065f46">Online</span>'
            : '<span class="tag">Offline</span>';
          return '<tr><td>' + esc(x.name || x.username) + ' <span style="color:var(--muted);font-size:11px">' + esc(ROLE_LABEL[x.role] || x.role) + '</span></td><td>' + esc(x.team || '—') + '</td><td>' + st + '</td><td style="text-align:right">' + (x.active || 0) + '</td></tr>';
        }).join('') + '</tbody></table></div>';
    });
  }
  // Tombol status di sidebar + heartbeat (WA Agent & Supervisor)
  var _avail = { status: 'available', t: null };
  function availPaint() {
    var b = $('#btnAvail'); if (!b) return;
    var on = _avail.status !== 'away';
    b.innerHTML = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;background:' + (on ? '#16a34a' : '#d97706') + '"></span>' + (on ? 'Tersedia' : 'Istirahat');
    b.title = on ? 'Anda menerima chat otomatis. Klik untuk Istirahat.' : 'Anda tidak menerima chat otomatis. Klik untuk kembali Tersedia.';
  }
  function availPing(set) {
    var body = set ? { op: 'set', status: set } : { op: 'ping' };
    return api('agent_presence', { method: 'POST', body: body }).then(function (r) {
      if (!r || !r.ok) return;
      _avail.status = r.status || 'available'; availPaint();
      if (r.assigned > 0) { toast(r.assigned + ' chat menunggu dibagikan ke tim.'); if (typeof fetchWaConvs === 'function' && $('#waConvList')) fetchWaConvs(true); }
    }).catch(function () {});
  }
  function availInit() {
    var b = $('#btnAvail');
    if (!b || (role !== 'wa_agent' && role !== 'supervisor')) return;
    b.style.display = '';
    availPaint();
    b.onclick = function () { availPing(_avail.status === 'away' ? 'available' : 'away'); };
    availPing();
    clearInterval(_avail.t);
    _avail.t = setInterval(function () { if (!document.hidden) availPing(); }, 60000);
    document.addEventListener('visibilitychange', function () { if (!document.hidden) availPing(); });
  }
  availInit();
'''

js = [
    ("  function saveTim() {\n", JS_ROUTE + "\n  function saveTim() {\n"),
    ("      if ($('#tim_private')) $('#tim_private').checked = !!(r.team && r.team.agent_private);\n",
     "      if ($('#tim_private')) $('#tim_private').checked = !!(r.team && r.team.agent_private);\n"
     "      rtLoad(r);   // v1.2.100: routing\n"),
    # kartu Nomor WhatsApp: kolom & pilihan tim
    ("      _wn.rows = r.numbers || []; _wn.max = (r.limit != null) ? r.limit : (r.max || 0);   // v1.2.99: lisensi-nomor (batas paket)\n",
     "      _wn.rows = r.numbers || []; _wn.max = (r.limit != null) ? r.limit : (r.max || 0);   // v1.2.99: lisensi-nomor (batas paket)\n"
     "      _wn.teams = r.teams || [];   // v1.2.100: routing\n"
     "      var _tn = {}; _wn.teams.forEach(function (t) { _tn[t.username] = t.name || t.username; });\n"),
    ("'</th><th></th></tr></thead><tbody>' +\n",
     "'</th><th>Tim</th><th></th></tr></thead><tbody>' +   // v1.2.100: routing\n"),
    ("            '<td class=\"mono\" style=\"font-size:12px\">' + esc(idc) + '</td><td style=\"white-space:nowrap;text-align:right\">' + acts + '</td></tr>';\n",
     "            '<td class=\"mono\" style=\"font-size:12px\">' + esc(idc) + '</td><td style=\"font-size:12px\">' + (x.team ? esc(_tn[x.team] || x.team) : '<span style=\"color:var(--muted)\">Semua</span>') + '</td><td style=\"white-space:nowrap;text-align:right\">' + acts + '</td></tr>';\n"),
    ("    $('#wn_label').value = row ? (row.label || '') : '';\n",
     "    $('#wn_label').value = row ? (row.label || '') : '';\n"
     "    $('#wn_team').innerHTML = '<option value=\"\">Semua agent</option>' + (_wn.teams || []).map(function (t) { return '<option value=\"' + esc(t.username) + '\">Tim ' + esc(t.name || t.username) + '</option>'; }).join('');   // v1.2.100\n"
     "    $('#wn_team').value = row ? (row.team || '') : '';\n"),
    ("    var body = { op: 'save', id: id, label: $('#wn_label').value.trim() };\n",
     "    var body = { op: 'save', id: id, label: $('#wn_label').value.trim(), team: $('#wn_team').value };   // v1.2.100: team\n"),
]
patch(TEN, 'dashboard/chatbot-ai/app.js', js)
print('selesai')
