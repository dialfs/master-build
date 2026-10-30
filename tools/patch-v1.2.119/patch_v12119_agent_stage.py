#!/usr/bin/env python3
r"""v1.2.119 agent-stage: WA Agent hanya boleh claim/membalas chat dari kontak dengan Lead Rating tertentu.
Dipilih saat membuat user, bisa diubah di Pengguna > Edit. Kosong = semua status.
Pakai: python3 patch_v12119_agent_stage.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.118)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.119: agent-stage'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def patch(rel, edits):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    shutil.copy2(p, p + '.bak-v12119-' + STAMP)
    for old, new in edits:
        n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:90]); s = s.replace(old, new)
    assert TAG in s, rel; open(p, 'w', encoding='utf-8').write(s); print('OK', rel)

patch('api/index.php', [
 (r"""define('DEI_VERSION', 'v1.2.118');   // v1.2.118: close-deal-lose""",
  r"""define('DEI_VERSION', 'v1.2.119');   // v1.2.119: agent-stage"""),
 # helper
 (r"""function waContactStage($number, $contacts = null) {""",
  r"""// v1.2.119: agent-stage — WA Agent hanya membalas kontak dengan Lead Rating tertentu ([] = semua)
function deiReplyStagesClean($arr) {
    $o = [];
    foreach ((array)$arr as $v) { $v = (string)$v; if (($v === 'vip' || contactStageValid($v)) && !in_array($v, $o, true)) $o[] = $v; }
    return $o;
}
function deiUserReplyStages($u) {
    if (($u['role'] ?? '') !== 'wa_agent') return [];
    if (!is_array($u) || !array_key_exists('reply_stages', $u)) {
        foreach ((array)readJson(USERS_FILE, []) as $x) { if (($x['username'] ?? '') === ($u['username'] ?? '')) { $u = $x; break; } }
    }
    return deiReplyStagesClean($u['reply_stages'] ?? []);
}
function deiStageAllowed($allowed, $stage, $vip) {
    if (!$allowed) return true;
    return in_array((string)$stage, $allowed, true) || ($vip && in_array('vip', $allowed, true));
}
function deiNumStageVip($num) {
    $num = preg_replace('/\D/', '', (string)$num);
    $all = waContactsFor($num);
    return [waContactStage($num, $all), waContactVip($num, $all)];
}
function deiAgentCanReplyNum($u, $num) {
    $al = deiUserReplyStages($u);
    if (!$al) return true;
    list($st, $vip) = deiNumStageVip($num);
    return deiStageAllowed($al, $st, $vip);
}
function deiReplyStagesLabel($al) {
    $lb = ['new' => 'Unrated', 'cold' => 'Cold', 'warm' => 'Warm', 'hot_prospect' => 'Hot Prospect', 'lost' => 'Unqualified',
           'active_customer' => 'Active Customer', 'churned' => 'Churned', 'vip' => 'VIP'];
    return implode(', ', array_map(function ($k) use ($lb) { return $lb[$k] ?? $k; }, (array)$al));
}
function deiGuardAgentStage($u, $num) {
    if (deiAgentCanReplyNum($u, $num)) return;
    jsonOut(['ok' => false, 'error' => 'Akun Anda hanya boleh membalas kontak dengan Lead Rating: ' . deiReplyStagesLabel(deiUserReplyStages($u)) . '. Minta Supervisor/Admin menyerahkan chat ini ke agent lain.'], 403);
}
function waContactStage($number, $contacts = null) {"""),
 # wa_send_manual
 (r"""        deiGuardSpvScope($u, $num);   // v1.2.59
        // v1.2.58: agent tidak boleh membalas chat yang dipegang agent lain""",
  r"""        deiGuardSpvScope($u, $num);   // v1.2.59
        deiGuardAgentStage($u, $num);   // v1.2.119: agent-stage
        // v1.2.58: agent tidak boleh membalas chat yang dipegang agent lain"""),
 # wa_claim
 (r"""        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);

        // Run auto-process dulu supaya state fresh""",
  r"""        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        deiGuardAgentStage($u, $num);   // v1.2.119: agent-stage

        // Run auto-process dulu supaya state fresh"""),
 # wa_takeover_request
 (r"""            jsonOut(['ok' => false, 'error' => 'Chat tidak claimed. Silakan claim langsung dengan wa_claim.'], 400);
        }""",
  r"""            jsonOut(['ok' => false, 'error' => 'Chat tidak claimed. Silakan claim langsung dengan wa_claim.'], 400);
        }
        deiGuardAgentStage($u, $num);   // v1.2.119: agent-stage"""),
 # wa_assign
 (r"""        foreach (deiAssignableUsers($u) as $au) { if ($au['username'] === $to) { $target = $au; break; } }
        if (!$target) jsonOut(['ok' => false, 'error' => 'Agent tidak ditemukan, di luar tim Anda, atau di luar batas paket.'], 404);""",
  r"""        foreach (deiAssignableUsers($u) as $au) { if ($au['username'] === $to) { $target = $au; break; } }
        if (!$target) jsonOut(['ok' => false, 'error' => 'Agent tidak ditemukan, di luar tim Anda, atau di luar batas paket.'], 404);
        if (($target['reply_stages'] ?? []) && $target['role'] === 'wa_agent') {   // v1.2.119: agent-stage
            list($stA, $vipA) = deiNumStageVip($num);
            if (!deiStageAllowed($target['reply_stages'], $stA, $vipA)) {
                jsonOut(['ok' => false, 'error' => $to . ' hanya menangani kontak dengan Lead Rating: ' . deiReplyStagesLabel($target['reply_stages']) . '.'], 403);
            }
        }"""),
 # deiAssignableUsers
 (r"""        $out[] = ['username' => $u['username'] ?? '', 'name' => $u['name'] ?? ($u['username'] ?? ''), 'role' => $r];""",
  r"""        $out[] = ['username' => $u['username'] ?? '', 'name' => $u['name'] ?? ($u['username'] ?? ''), 'role' => $r,
                  'reply_stages' => $r === 'wa_agent' ? deiReplyStagesClean($u['reply_stages'] ?? []) : []];   // v1.2.119: agent-stage"""),
 # routing
 (r"""function deiRouteCandidates($conf, $team, $users, $claims, $pres, $role) {""",
  r"""function deiRouteCandidates($conf, $team, $users, $claims, $pres, $role, $stInfo = null) {   // v1.2.119: agent-stage"""),
 (r"""        if (!deiSeatAllowed($un, $r, $users)) continue;
        if ($team !== '' && ($r === 'supervisor'""",
  r"""        if (!deiSeatAllowed($un, $r, $users)) continue;
        if ($r === 'wa_agent' && $stInfo && !deiStageAllowed(deiReplyStagesClean($u['reply_stages'] ?? []), $stInfo[0], $stInfo[1])) continue;   // v1.2.119
        if ($team !== '' && ($r === 'supervisor'"""),
 (r"""        $pick = (string)deiWithLock('wa-routing', function () use ($num, $conf, $team) {""",
  r"""        $stInfo = deiNumStageVip($num);   // v1.2.119: agent-stage
        $pick = (string)deiWithLock('wa-routing', function () use ($num, $conf, $team, $stInfo) {"""),
 (r"""            $cand = deiRouteCandidates($conf, $team, $users, $claims, $pres, 'wa_agent');""",
  r"""            $cand = deiRouteCandidates($conf, $team, $users, $claims, $pres, 'wa_agent', $stInfo);"""),
 # save_contact_stage
 (r"""    case 'save_contact_stage': {
        requireAuth(['super_admin', 'admin', 'wa_agent']);""",
  r"""    case 'save_contact_stage': {
        $uSt = requireAuth(['super_admin', 'admin', 'wa_agent']);"""),
 (r"""        $vip = !empty($in['vip']);
        waSetContactStage($num, $stage, $vip);""",
  r"""        $vip = !empty($in['vip']);
        // v1.2.119: agent-stage — agent terbatas hanya boleh mengubah kontak yang memang ia tangani
        if (deiUserReplyStages($uSt) && !deiAgentCanReplyNum($uSt, $num)) {
            jsonOut(['ok' => false, 'error' => 'Akun Anda hanya menangani kontak dengan Lead Rating: ' . deiReplyStagesLabel(deiUserReplyStages($uSt)) . '. Lead Rating kontak ini tidak bisa Anda ubah.'], 403);
        }
        waSetContactStage($num, $stage, $vip);"""),
 # wa_thread
 (r"""            'wa_prov' => (string)(waConf($s116)['provider'] ?? 'meta'),""",
  r"""            'wa_prov' => (string)(waConf($s116)['provider'] ?? 'meta'),
            'reply_ok' => deiAgentCanReplyNum($u, $num), 'reply_stages' => deiUserReplyStages($u),   // v1.2.119: agent-stage
            'stage' => deiNumStageVip($num)[0], 'vip' => deiNumStageVip($num)[1],"""),
 # get_users
 (r"""                'categories' => $u['categories'] ?? [],  // v1.2.12 Fase 2: categories
            ];""",
  r"""                'categories' => $u['categories'] ?? [],  // v1.2.12 Fase 2: categories
                'reply_stages' => ($u['role'] ?? '') === 'wa_agent' ? deiReplyStagesClean($u['reply_stages'] ?? []) : [],   // v1.2.119: agent-stage
            ];"""),
 # save_user
 (r"""        if ($username === '') jsonOut(['ok' => false, 'error' => 'Username wajib diisi.'], 400);

        // === v1.2.6""",
  r"""        if ($username === '') jsonOut(['ok' => false, 'error' => 'Username wajib diisi.'], 400);
        // v1.2.119: agent-stage — null = pertahankan nilai lama
        $rsSet = (isset($in['reply_stages']) && is_array($in['reply_stages'])) ? deiReplyStagesClean($in['reply_stages']) : null;

        // === v1.2.6"""),
 (r"""                if ($role !== 'wa_agent') unset($users[$i]['supervisor']);            // v1.2.59""",
  r"""                if ($role !== 'wa_agent') unset($users[$i]['reply_stages']);          // v1.2.119
                elseif ($rsSet !== null) $users[$i]['reply_stages'] = $rsSet;
                if ($role !== 'wa_agent') unset($users[$i]['supervisor']);            // v1.2.59"""),
 (r"""            if ($role === 'wa_agent' && $spvSet !== null && $spvSet !== '') $users[count($users) - 1]['supervisor'] = $spvSet;   // v1.2.59""",
  r"""            if ($role === 'wa_agent' && $spvSet !== null && $spvSet !== '') $users[count($users) - 1]['supervisor'] = $spvSet;   // v1.2.59
            if ($role === 'wa_agent' && $rsSet) $users[count($users) - 1]['reply_stages'] = $rsSet;   // v1.2.119"""),
])

patch('dashboard/chatbot-ai/index.html', [
 (r"""          <div class="row" id="u_spv_row" style="display:none"><label class="fl">Supervisor</label><select id="u_supervisor"><option value="">— Tanpa supervisor (terlihat semua SPV) —</option></select></div>""",
  r"""          <div class="row" id="u_spv_row" style="display:none"><label class="fl">Supervisor</label><select id="u_supervisor"><option value="">— Tanpa supervisor (terlihat semua SPV) —</option></select></div>
          <!-- v1.2.119: agent-stage -->
          <div class="row" id="u_rs_row" style="display:none"><label class="fl">Boleh balas Lead Rating</label>
            <div id="u_reply_stages" style="flex:1;display:flex;flex-wrap:wrap;gap:10px"></div>
          </div>
          <div class="help" id="u_rs_help" style="display:none;grid-column:1/-1;margin-top:-6px">Agent hanya bisa claim &amp; membalas chat dari kontak dengan Lead Rating yang dicentang (juga untuk pembagian otomatis). Kosongkan = semua status.</div>"""),
])

patch('dashboard/chatbot-ai/app.js', [
 # helper render + toggle
 (r"""  function toggleSpvRow() {
    var row = document.getElementById('u_spv_row');
    if (!row) return;
    var show = (user.role === 'super_admin' || user.role === 'admin') && $('#u_role').value === 'wa_agent';
    row.style.display = show ? '' : 'none';
  }""",
  r"""  function toggleSpvRow() {
    // v1.2.119: agent-stage — baris Lead Rating untuk WA Agent
    var isAg = $('#u_role') && $('#u_role').value === 'wa_agent';
    if (document.getElementById('u_rs_row')) { document.getElementById('u_rs_row').style.display = isAg ? '' : 'none'; document.getElementById('u_rs_help').style.display = isAg ? '' : 'none'; }
    var row = document.getElementById('u_spv_row');
    if (!row) return;
    var show = (user.role === 'super_admin' || user.role === 'admin') && $('#u_role').value === 'wa_agent';
    row.style.display = show ? '' : 'none';
  }
  var RS_EXTRA = { vip: 'VIP' };
  function rsLabel(k) { return CONTACT_STAGE[k] ? CONTACT_STAGE[k].label : (RS_EXTRA[k] || k); }
  function rsKeys() { var ks = []; CONTACT_STAGE_ORDER.forEach(function (k) { if (k !== '__sep__') ks.push(k); }); ks.push('vip'); return ks; }
  function rsAllowed(al, stage, vip) { return !al || !al.length || al.indexOf(stage || 'new') > -1 || (!!vip && al.indexOf('vip') > -1); }
  function renderUserReplyStages(sel) {
    var box = document.getElementById('u_reply_stages');
    if (!box) return;
    sel = sel || [];
    box.innerHTML = rsKeys().map(function (k) {
      return '<label style="display:flex;gap:5px;align-items:center;font-size:13px;cursor:pointer">' +
        '<input type="checkbox" class="u_rs" value="' + k + '"' + (sel.indexOf(k) > -1 ? ' checked' : '') + '> ' + esc(rsLabel(k)) + '</label>';
    }).join('');
  }"""),
 (r"""    ensureCategories(function () { renderUserCategories([]); renderUsers(); });  // v1.2.13""",
  r"""    ensureCategories(function () { renderUserCategories([]); renderUsers(); });  // v1.2.13
    renderUserReplyStages([]);   // v1.2.119: agent-stage"""),
 # table + edit
 (r"""            (u.seat_locked ? ' <span class="tag" style="background:#fee2e2;color:#b91c1c" title="Di luar batas kursi paket — tidak bisa login">' + ico('ban',12) + ' terkunci</span>' : '') + '</td>' +""",
  r"""            (u.seat_locked ? ' <span class="tag" style="background:#fee2e2;color:#b91c1c" title="Di luar batas kursi paket — tidak bisa login">' + ico('ban',12) + ' terkunci</span>' : '') +
            ((u.role === 'wa_agent' && (u.reply_stages || []).length) ? '<div style="font-size:11px;color:var(--muted);margin-top:3px" title="Hanya boleh membalas Lead Rating ini">Balas: ' + esc(u.reply_stages.map(rsLabel).join(', ')) + '</div>' : '') + '</td>' +   // v1.2.119"""),
 (r"""'" data-cats="' + esc(JSON.stringify(u.categories || [])) + '">Edit</button> ' +""",
  r"""'" data-cats="' + esc(JSON.stringify(u.categories || [])) + '" data-rs="' + esc(JSON.stringify(u.reply_stages || [])) + '">Edit</button> ' +"""),
 (r"""        renderUserCategories(editCats);   // v1.2.13: rebuild dari daftar dinamis""",
  r"""        renderUserCategories(editCats);   // v1.2.13: rebuild dari daftar dinamis
        var editRs = []; try { editRs = JSON.parse(b.dataset.rs || '[]'); } catch (e) { editRs = []; }
        renderUserReplyStages(editRs);   // v1.2.119: agent-stage"""),
 (r"""    renderUserCategories([]);  // v1.2.13: rebuild kosong""",
  r"""    renderUserCategories([]);  // v1.2.13: rebuild kosong
    renderUserReplyStages([]);   // v1.2.119: agent-stage"""),
 (r"""    if ($('#u_spv_row') && $('#u_spv_row').style.display !== 'none') body.supervisor = $('#u_supervisor').value;   // v1.2.59""",
  r"""    if ($('#u_spv_row') && $('#u_spv_row').style.display !== 'none') body.supervisor = $('#u_supervisor').value;   // v1.2.59
    if (body.role === 'wa_agent') body.reply_stages = Array.prototype.slice.call(document.querySelectorAll('.u_rs:checked')).map(function (c) { return c.value; });   // v1.2.119"""),
 # assign dropdown
 (r"""          if (claim && a.username === claim.agent_username) return '';
          return '<option value="' + esc(a.username) + '">' + esc(a.name || a.username) + ' (' + esc(ROLE_LABEL[a.role] || a.role) + ')</option>';""",
  r"""          if (claim && a.username === claim.agent_username) return '';
          var _rsNo = a.role === 'wa_agent' && !rsAllowed(a.reply_stages, res.stage, res.vip);   // v1.2.119: agent-stage
          return '<option value="' + esc(a.username) + '"' + (_rsNo ? ' disabled' : '') + '>' + esc(a.name || a.username) + ' (' + esc(ROLE_LABEL[a.role] || a.role) + ')' + (_rsNo ? ' — Lead Rating tidak sesuai' : '') + '</option>';"""),
 # thread reply guard
 (r"""    var canReply = open && (isMine || waState.isAdmin);
    $('#waReplyInput').disabled = !canReply;""",
  r"""    var canReply = open && (isMine || waState.isAdmin);
    var _rsBlock = res.reply_ok === false;   // v1.2.119: agent-stage
    if (_rsBlock) {
      canReply = false;
      ['#waClaimBtn', '#waRequestTakeoverBtn'].forEach(function (id) { if ($(id)) $(id).style.display = 'none'; });
      if ($('#waStageSelect')) $('#waStageSelect').disabled = true;
      if ($('#waVipToggle')) $('#waVipToggle').disabled = true;
    }
    $('#waReplyInput').disabled = !canReply;"""),
 (r"""    $('#waWindowNote').innerHTML = open
      ? (isMine ?""",
  r"""    $('#waWindowNote').innerHTML = _rsBlock
      ? '<span style="color:#b45309">' + ico('ban',13) + ' Akun Anda hanya membalas kontak dengan Lead Rating <strong>' + esc((res.reply_stages || []).map(rsLabel).join(', ')) + '</strong>. Chat ini: ' + esc(rsLabel(res.stage || 'new')) + (res.vip ? ' + VIP' : '') + ' — minta Supervisor/Admin menyerahkan ke agent lain.</span>'
      : open
      ? (isMine ?"""),
])
