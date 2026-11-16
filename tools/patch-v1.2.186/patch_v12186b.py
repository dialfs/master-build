import sys
TAG='v1.2.186b: grup-paket'
def edit(p, pairs):
    s=open(p).read()
    if TAG in s: print('sudah', p); return
    for a,b in pairs:
        assert s.count(a)==1, (p, a[:70], s.count(a)); s=s.replace(a,b)
    open(p,'w').write(s); print('OK',p)
D=sys.argv[1]
GL=D+'/backend/group-lib.php'
s=open(GL).read()
if TAG not in s:
    s+='''
/* ---------- v1.2.186b: grup-paket — Dashboard Grup mulai paket Business ----------
 * Trial, Starter & Growth tidak termasuk. Pengecualian manual: tenants.json › group_ok = true. */
function grpTierOk(array $t): bool {
    if (!empty($t['group_ok'])) return true;
    $ft = function_exists('featTier') ? featTier($t) : strtolower((string)($t['tier'] ?? ''));
    return in_array($ft, ['business', 'pro', 'custom', 'enterprise'], true);
}
function grpTierMsg(array $t): string {
    $ft = function_exists('featTier') ? featTier($t) : strtolower((string)($t['tier'] ?? ''));
    $nm = ['starter' => 'Starter', 'growth' => 'Growth'][$ft] ?? ($ft !== '' ? ucfirst($ft) : '-');
    return 'Paket tenant ini (' . (function_exists('isTrialTenant') && isTrialTenant($t) ? 'trial ' : '') . $nm . ') belum termasuk Dashboard Grup — tersedia mulai paket Business.';
}
'''
    a="""    foreach (grpUserTenantIds($g, $u) as $tid) if (isset($tn[$tid]) && ($map[$tid] ?? '') !== '') $o[$tid] = [$tn[$tid], (string)$map[$tid]];"""
    b="""    foreach (grpUserTenantIds($g, $u) as $tid) if (isset($tn[$tid]) && ($map[$tid] ?? '') !== '' && grpTierOk($tn[$tid])) $o[$tid] = [$tn[$tid], (string)$map[$tid]];   // """+TAG
    assert s.count(a)==1; s=s.replace(a,b); open(GL,'w').write(s); print('OK',GL)
else: print('sudah',GL)

edit(D+'/backend/index.php', [
 ("""                          return ['tenant_id' => $id, 'name' => $t['name'] ?? $id, 'exists' => (bool)$t, 'version' => $t['current_version'] ?? '', 'api_url' => (bool)trim((string)($t['api_url'] ?? ''))]; }, (array)($g['tenant_ids'] ?? [])),""",
  """                          return ['tenant_id' => $id, 'name' => $t['name'] ?? $id, 'exists' => (bool)$t, 'version' => $t['current_version'] ?? '', 'api_url' => (bool)trim((string)($t['api_url'] ?? '')),
                                  'plan_ok' => $t ? grpTierOk($t) : false, 'plan_msg' => $t && !grpTierOk($t) ? grpTierMsg($t) : '']; }, (array)($g['tenant_ids'] ?? [])),   // """+TAG),
 ("""            $list[] = ['tenant_id' => $tid, 'name' => (string)($t['name'] ?? $tid), 'active' => !empty($t['active']),
                       'version' => (string)($t['current_version'] ?? ''),
                       'can_open' => ($u['role'] ?? 'manager') === 'manager' && !empty(((array)($u['map'] ?? []))[$tid])];""",
  """            $pok = grpTierOk($t);   // """+TAG+"""
            $list[] = ['tenant_id' => $tid, 'name' => (string)($t['name'] ?? $tid), 'active' => !empty($t['active']),
                       'version' => (string)($t['current_version'] ?? ''), 'plan_ok' => $pok, 'plan_msg' => $pok ? '' : grpTierMsg($t),
                       'can_open' => $pok && ($u['role'] ?? 'manager') === 'manager' && !empty(((array)($u['map'] ?? []))[$tid])];"""),
 ("""        foreach (grpUserTenantIds($g, $u) as $tid) if (isset($tn[$tid])) $jobs[$tid] = [$tn[$tid], 'grp_report', ['from' => $from, 'to' => $to]];
        $out = [];""",
  """        $out = [];
        foreach (grpUserTenantIds($g, $u) as $tid) if (isset($tn[$tid])) {
            if (!grpTierOk($tn[$tid])) { $out[] = ['tenant_id' => $tid, 'name' => (string)($tn[$tid]['name'] ?? $tid), 'ok' => false, 'error' => grpTierMsg($tn[$tid])]; continue; }   // """+TAG+"""
            $jobs[$tid] = [$tn[$tid], 'grp_report', ['from' => $from, 'to' => $to]];
        }"""),
 ("""        $t = grpTenantsById()[$tid] ?? null;
        $dash = $t ? suTenantDashUrl($t) : '';""",
  """        $t = grpTenantsById()[$tid] ?? null;
        if ($t && !grpTierOk($t)) jsonOut(['ok' => false, 'error' => grpTierMsg($t)], 403);   // """+TAG+"""
        $dash = $t ? suTenantDashUrl($t) : '';"""),
 ("""        $tt = grpInboxTenants($g, $u);
        if (!$tt) jsonOut(['ok' => true, 'tenants' => [], 'conversations' => [], 'note' =>""",
  """        $tt = grpInboxTenants($g, $u);
        $tnAll = grpTenantsById(); $planBad = [];   // """+TAG+"""
        foreach (grpUserTenantIds($g, $u) as $tid) if (isset($tnAll[$tid]) && !grpTierOk($tnAll[$tid])) $planBad[] = ['tenant_id' => $tid, 'name' => (string)($tnAll[$tid]['name'] ?? $tid), 'ok' => false, 'error' => grpTierMsg($tnAll[$tid])];
        if (!$tt) jsonOut(['ok' => true, 'tenants' => $planBad, 'conversations' => [], 'note' =>"""),
 ("""        usort($conv, function ($a, $b) { return strcmp($b['last_ts'], $a['last_ts']); });
        jsonOut(['ok' => true, 'tenants' => $st, 'conversations' => $conv]);""",
  """        usort($conv, function ($a, $b) { return strcmp($b['last_ts'], $a['last_ts']); });
        jsonOut(['ok' => true, 'tenants' => array_merge($st, $planBad), 'conversations' => $conv]);"""),
])

edit(D+'/grup/index.html', [
 ("<!-- v1.2.186: grup-inbox -->","<!-- v1.2.186: grup-inbox --><!-- "+TAG+" -->"),
 ("""    <div class="nm" title="${esc(t.name)}">${esc(t.name)}<div class="sub">${esc(t.tenant_id)}${t.active?'':' · nonaktif'}</div></div>""",
  """    <div class="nm" title="${esc(t.plan_msg||t.name)}">${esc(t.name)}<div class="sub">${esc(t.tenant_id)}${t.active?'':' · nonaktif'}${t.plan_ok===false?' · <span style="color:var(--warn)">butuh paket Business</span>':''}</div></div>"""),
 ("""  $('#tHint').textContent=me.user.role==='viewer'?'Akun Anda hanya untuk melihat laporan.':(ts.some(t=>!t.can_open)?'Tenant tanpa tombol Buka: akun Anda belum dihubungkan, hubungi DEI.':'');""",
  """  $('#tHint').textContent=me.user.role==='viewer'?'Akun Anda hanya untuk melihat laporan.':(ts.some(t=>t.plan_ok===false)?'Dashboard Grup tersedia untuk tenant paket Business ke atas. ':'')+(me.user.role!=='viewer'&&ts.some(t=>t.plan_ok!==false&&!t.can_open)?'Tenant tanpa tombol Buka: akun Anda belum dihubungkan, hubungi DEI.':'');"""),
])

edit(D+'/admin/index.html', [
 ("""Laporan butuh tenant <span id="grpMinVer">v1.2.185</span>+.</div>""",
  """Laporan butuh tenant <span id="grpMinVer">v1.2.185</span>+, inbox v1.2.186+. <b>Hanya untuk tenant paket Business ke atas</b> (trial, Starter &amp; Growth tidak ikut; pengecualian manual: <code>group_ok: true</code> di tenants.json).</div><!-- """+TAG+""" -->"""),
 ("""      const tl=g.tenants.map(t=>`<span class="badge ${t.exists?(t.version&&vlt(t.version)?'idle':'ok'):'off'}" title="${t.exists?(t.version?('Versi '+esc(t.version)+(vlt(t.version)?' — perlu update untuk laporan grup':'')):'Versi belum diketahui'):'Tenant sudah dihapus'}">${esc(t.name)}</span>`).join(' ')||'<span class="hint">belum ada tenant</span>';""",
  """      const tl=g.tenants.map(t=>`<span class="badge ${!t.exists||t.plan_ok===false?'off':(t.version&&vlt(t.version)?'idle':'ok')}" title="${!t.exists?'Tenant sudah dihapus':(t.plan_ok===false?esc(t.plan_msg):(t.version?('Versi '+esc(t.version)+(vlt(t.version)?' — perlu update untuk laporan grup':'')):'Versi belum diketahui'))}">${esc(t.name)}${t.plan_ok===false?' · paket kurang':''}</span>`).join(' ')||'<span class="hint">belum ada tenant</span>';"""),
 ("""    GRP.tenants=(t.ok?t.tenants:[]).map(x=>({id:String(x.tenant_id||'').toLowerCase(),name:x.name||x.tenant_id})).sort((a,b)=>a.name.localeCompare(b.name));""",
  """    GRP.tenants=(t.ok?t.tenants:[]).map(x=>({id:String(x.tenant_id||'').toLowerCase(),name:x.name||x.tenant_id,trial:!!(x.trial&&typeof x.trial==='object')||String(x.tier||'').toLowerCase()==='trial',tier:String(x.tier||'').toLowerCase(),gok:!!x.group_ok})).sort((a,b)=>a.name.localeCompare(b.name));"""),
 ("""<input type="checkbox" value="${esc(t.id)}" style="width:auto" ${g.tenant_ids.includes(t.id)?'checked':''}> ${esc(t.name)} <span class="mono hint" style="margin:0">${esc(t.id)}</span></label>`).join('')}</div>""",
  """<input type="checkbox" value="${esc(t.id)}" style="width:auto" ${g.tenant_ids.includes(t.id)?'checked':''}> ${esc(t.name)} <span class="mono hint" style="margin:0">${esc(t.id)}</span>${(t.gok||(!t.trial&&['business','pro','custom','enterprise'].includes(t.tier)))?'':` <span class="badge off" title="Dashboard Grup mulai paket Business">${t.trial?'trial':esc(t.tier||'-')} · belum termasuk</span>`}</label>`).join('')}</div>
    <div class="hint">Tenant di bawah paket Business boleh dimasukkan, tapi baru tampil di Dashboard Grup setelah naik ke Business.</div>"""),
])
