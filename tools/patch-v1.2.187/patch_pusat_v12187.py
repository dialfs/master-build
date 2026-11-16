#!/usr/bin/env python3
"""v1.2.187: mitra — Program Mitra (reseller / referral). Patch KHUSUS PUSAT (dei-pusat), tenant tidak berubah.

  python3 patch_pusat_v12187.py <root dei-pusat>

- menyalin partner-lib.php ke backend/
- backend/index.php: require, signup_config/signup_start (kode mitra), action partner_*
- backend/signup-lib.php: tenant baru membawa partner
- backend/billing-lib.php + billing-callback.php: komisi otomatis saat pesanan Duitku lunas
- daftar/index.html: isian "Kode mitra" (+ ?ref=KODE)
- admin/index.html: kartu "Mitra / Reseller"
Idempoten (penanda "v1.2.187: mitra"); backup *.bak-v12187-<waktu> hanya untuk file yang berubah.
"""
import os, shutil, sys, time

MARK = 'v1.2.187: mitra'
STAMP = time.strftime('%Y%m%d-%H%M%S')
HERE = os.path.dirname(os.path.abspath(__file__))


def die(msg):
    print('GAGAL: ' + msg)
    sys.exit(1)


def rep(s, old, new, path):
    if s.count(old) != 1:
        die('jangkar tidak unik/tidak ada di %s (%d): %r' % (path, s.count(old), old[:90]))
    return s.replace(old, new)


def patch(root, rel, fn):
    path = os.path.join(root, rel)
    if not os.path.isfile(path):
        die('tidak ada: ' + path)
    with open(path, encoding='utf-8') as f:
        s = f.read()
    if MARK in s:
        print('lewati (sudah dipatch): ' + rel)
        return
    out = fn(s, rel)
    shutil.copy2(path, path + '.bak-v12187-' + STAMP)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(out)
    print('dipatch: ' + rel)


# ---------------------------------------------------------------- backend/index.php
PHP_CASES = r'''    /* ========================================================
     * v1.2.187: mitra — Program Mitra / reseller (lihat backend/partner-lib.php)
     * ====================================================== */
    case 'partner_check': {   // publik: dipakai /daftar/ untuk memeriksa kode mitra
        $code = ptCodeNorm((string)($_GET['code'] ?? ''));
        if (empty(ptCfg()['signup_field']) || !ptCodeValid($code)) jsonOut(['ok' => true, 'valid' => false, 'name' => '']);
        if (!suRateOk('pcheck', 60, 3600)) jsonOut(['ok' => false, 'error' => 'Terlalu banyak percobaan. Coba lagi nanti.'], 429);
        $pp = ptFindByCode($code);
        jsonOut(['ok' => true, 'valid' => (bool)$pp, 'name' => $pp ? (string)$pp['name'] : '']);
    }
    case 'partner_list': {
        requireAdmin();
        $tenants = readJson(TENANTS_FILE, []); $free = [];
        foreach ($tenants as $t) {
            if (!is_array($t) || trim((string)($t['partner'] ?? '')) !== '') continue;
            $free[] = ['tenant_id' => tidNorm((string)($t['tenant_id'] ?? '')), 'name' => (string)($t['name'] ?? ''), 'tier' => isTrialTenant($t) ? 'trial' : strtolower((string)($t['tier'] ?? ''))];
        }
        usort($free, function ($a, $b) { return strcasecmp($a['name'], $b['name']); });
        jsonOut(['ok' => true, 'partners' => ptSummary($tenants), 'config' => ptCfg(), 'free_tenants' => $free, 'month' => ptMonth(), 'signup_url' => ptSignupBase()]);
    }
    case 'partner_detail': {
        requireAdmin();
        $d = ptDetail((string)($_GET['id'] ?? ''), readJson(TENANTS_FILE, []));
        if (!$d) jsonOut(['ok' => false, 'error' => 'Mitra tidak ditemukan.'], 404);
        jsonOut(['ok' => true] + $d + ['config' => ptCfg()]);
    }
    case 'partner_save': {
        requireAdmin();
        list($ok, $res) = ptSave(bodyInput());
        if (!$ok) jsonOut(['ok' => false, 'error' => $res], 400);
        jsonOut(['ok' => true, 'partner' => $res]);
    }
    case 'partner_delete': {
        requireAdmin();
        $id = (string)(bodyInput()['id'] ?? '');
        if (!ptFind($id)) jsonOut(['ok' => false, 'error' => 'Mitra tidak ditemukan.'], 404);
        if (ptTenantsOf($id, readJson(TENANTS_FILE, []))) jsonOut(['ok' => false, 'error' => 'Mitra masih punya tenant. Lepaskan tenantnya dulu, atau nonaktifkan mitra ini.'], 400);
        foreach (ptLedger() as $e) if (($e['partner_id'] ?? '') === $id) jsonOut(['ok' => false, 'error' => 'Mitra sudah punya riwayat komisi. Nonaktifkan saja supaya riwayatnya tetap ada.'], 400);
        ptSaveAll(array_filter(ptAll(), function ($p) use ($id) { return ($p['id'] ?? '') !== $id; }));
        jsonOut(['ok' => true]);
    }
    case 'partner_assign': {   // hubungkan / lepas tenant dari mitra (partner_id kosong = lepas)
        requireAdmin();
        $in = bodyInput(); $tid = tidNorm((string)($in['tenant_id'] ?? '')); $pid = trim((string)($in['partner_id'] ?? ''));
        if ($pid !== '' && !ptFind($pid)) jsonOut(['ok' => false, 'error' => 'Mitra tidak ditemukan.'], 404);
        $all = readJson(TENANTS_FILE, []);
        if (!is_array($all) || !count($all)) jsonOut(['ok' => false, 'error' => 'Daftar tenant tidak terbaca.'], 500);
        $hit = false;
        foreach ($all as $i => $t) {
            if (!is_array($t) || !tidEq($t['tenant_id'] ?? '', $tid) || $tid === '') continue;
            $cur = trim((string)($t['partner'] ?? ''));
            if ($pid !== '' && $cur !== '' && $cur !== $pid) jsonOut(['ok' => false, 'error' => 'Tenant ini sudah milik mitra lain. Lepaskan dulu dari mitra tersebut.'], 409);
            if ($pid === '') unset($all[$i]['partner'], $all[$i]['partner_at'], $all[$i]['partner_via']);
            elseif ($cur !== $pid) { $all[$i]['partner'] = $pid; $all[$i]['partner_at'] = gmdate('Y-m-d H:i:s'); $all[$i]['partner_via'] = 'admin'; }
            $hit = true; break;
        }
        if (!$hit) jsonOut(['ok' => false, 'error' => 'Tenant tidak ditemukan.'], 404);
        writeJson(TENANTS_FILE, $all);
        jsonOut(['ok' => true]);
    }
    case 'partner_manual': {   // pembayaran di luar Duitku (transfer/invoice manual) → komisi
        requireAdmin();
        $in = bodyInput(); $pid = (string)($in['partner_id'] ?? ''); $tid = tidNorm((string)($in['tenant_id'] ?? ''));
        $p = ptFind($pid);
        if (!$p) jsonOut(['ok' => false, 'error' => 'Mitra tidak ditemukan.'], 404);
        $tenants = readJson(TENANTS_FILE, []); $t = null;
        foreach ($tenants as $x) if (is_array($x) && tidEq($x['tenant_id'] ?? '', $tid) && (string)($x['partner'] ?? '') === $pid) { $t = $x; break; }
        if (!$t) jsonOut(['ok' => false, 'error' => 'Tenant bukan milik mitra ini.'], 400);
        $date = trim((string)($in['date'] ?? '')) ?: ptToday();
        $pct = trim((string)($in['pct'] ?? '')) === '' ? null : (int)$in['pct'];
        $r = ptCommission($p, $t, $tenants, (int)($in['base'] ?? 0), $date, 'MAN-' . str_replace('-', '', $date) . '-' . strtoupper(bin2hex(random_bytes(3))), 'manual', trim((string)($in['note'] ?? '')), $pct);
        if (empty($r[0])) jsonOut(['ok' => false, 'error' => $r[1]], 400);
        jsonOut(['ok' => true, 'entry' => $r[1]]);
    }
    case 'partner_void': {
        requireAdmin();
        $in = bodyInput();
        list($ok, $res) = ptVoid((string)($in['id'] ?? ''), (string)($in['reason'] ?? ''));
        jsonOut($ok ? ['ok' => true] : ['ok' => false, 'error' => $res], $ok ? 200 : 400);
    }
    case 'partner_payout': {
        requireAdmin();
        $in = bodyInput();
        list($ok, $res) = ptPayout((string)($in['partner_id'] ?? ''), (string)($in['upto'] ?? ''), (string)($in['note'] ?? ''));
        jsonOut($ok ? ['ok' => true] + $res : ['ok' => false, 'error' => $res], $ok ? 200 : 400);
    }
    case 'partner_sync': {
        requireAdmin();
        jsonOut(['ok' => true, 'added' => ptSync(readJson(TENANTS_FILE, []), (string)(bodyInput()['partner_id'] ?? ''))]);
    }
    case 'partner_save_config': {
        requireAdmin();
        jsonOut(['ok' => true, 'config' => ptSaveCfg(bodyInput())]);
    }

'''

PHP_SIGNUP_CODE = r'''        // v1.2.187: mitra — kode mitra (opsional)
        $pid = '';
        $pcode = ptCodeNorm((string)($in['partner_code'] ?? ''));
        if ($pcode !== '' && !empty(ptCfg()['signup_field'])) {
            $pp = ptFindByCode($pcode);
            if (!$pp) jsonOut(['ok' => false, 'error' => 'Kode mitra tidak dikenal. Periksa lagi, atau kosongkan bila tidak punya.', 'field' => 'partner_code'], 400);
            $pid = (string)$pp['id'];
        }
'''


def p_index(s, rel):
    a = "require_once __DIR__ . '/group-lib.php';   // v1.2.185: master-grup\n"
    s = rep(s, a, a + "require_once __DIR__ . '/partner-lib.php';   // v1.2.187: mitra\n", rel)
    a = "'base_url' => rtrim((string)$c['base_url'], '/')]);"
    s = rep(s, a, "'base_url' => rtrim((string)$c['base_url'], '/'), 'partner_field' => !empty(ptCfg()['signup_field'])]);", rel)
    a = "        if (!suTurnstileOk($c, (string)($in['cf_token'] ?? ''))) jsonOut("
    s = rep(s, a, PHP_SIGNUP_CODE + a, rel)
    a = "'pass_hash' => password_hash($pass, PASSWORD_DEFAULT), 'slug' => $slug, 'ip' => suClientIp(),"
    s = rep(s, a, a + " 'partner' => $pid,", rel)
    a = "{$p['name']} · {$p['phone']} · {$p['email']}\\n{$dash}\");"
    s = rep(s, a, "{$p['name']} · {$p['phone']} · {$p['email']}\\n{$dash}\" . ((!empty($res['partner']) && ($pm = ptFind((string)$res['partner']))) ? \"\\nMitra: {$pm['name']} ({$pm['code']})\" : ''));", rel)
    a = "    /* v1.2.138: filter-topik: klasifikasi topik chat WA untuk tenant"
    s = rep(s, a, PHP_CASES + a, rel)
    return s


def p_signup(s, rel):
    a = "        if (!$register($rec)) throw new RuntimeException('Gagal mendaftarkan tenant.');"
    add = ("        if (!empty($p['partner'])) { $rec['partner'] = (string)$p['partner']; $rec['partner_at'] = gmdate('Y-m-d H:i:s', $now); $rec['partner_via'] = 'signup'; }"
           "   // v1.2.187: mitra — tenant milik mitra\n")
    return rep(s, a, add + a, rel)


def p_billing(s, rel):
    a = "    try { $o['pushed'] = blPushLicense($t); } catch"
    add = ("    try { if (function_exists('ptOnPaid')) ptOnPaid($o, $t, $tenants); } catch (\\Throwable $e) { error_log('ptOnPaid: ' . $e->getMessage()); }"
           "   // v1.2.187: mitra — komisi mitra\n")
    return rep(s, a, add + a, rel)


def p_callback(s, rel):
    a = "require_once __DIR__ . '/billing-lib.php';\n"
    return rep(s, a, a + "require_once __DIR__ . '/partner-lib.php';   // v1.2.187: mitra\n", rel)


# ---------------------------------------------------------------- daftar/index.html
DAFTAR_FIELD = r'''          <div id="pcWrap" class="hide"><!-- v1.2.187: mitra -->
            <label for="partner_code">Kode mitra <span style="font-weight:400;color:var(--muted)">(opsional)</span></label>
            <input type="text" id="partner_code" name="partner-code" maxlength="16" autocomplete="off" autocapitalize="characters" spellcheck="false">
            <div class="hint" id="pcHint">Isi bila Anda mendaftar lewat mitra atau reseller DEI.</div>
          </div>
'''

DAFTAR_JS = r'''  // v1.2.187: mitra — kode mitra (opsional); terisi otomatis dari /daftar/?ref=KODE dan diingat 90 hari
  function pcInit() {
    var w = $('#pcWrap'), inp = $('#partner_code'), hint = $('#pcHint'), t = null, code = '';
    if (!w || !inp) return;
    var def = hint.textContent;
    w.classList.remove('hide');
    try {
      var q = new URLSearchParams(location.search);
      code = (q.get('ref') || q.get('mitra') || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 16);
      if (code) localStorage.setItem('dei_ref', JSON.stringify({ c: code, t: Date.now() }));
      else { var s = JSON.parse(localStorage.getItem('dei_ref') || 'null'); if (s && s.c && Date.now() - s.t < 90 * 864e5) code = s.c; }
    } catch (e) {}
    function check() {
      var v = inp.value = inp.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
      inp.classList.remove('bad');
      if (v.length < 4) { hint.textContent = def; hint.style.color = ''; return; }
      fetch(API + '?action=partner_check&code=' + encodeURIComponent(v)).then(function (r) { return r.json(); }).then(function (r) {
        if (inp.value !== v || !r || !r.ok) return;
        hint.textContent = r.valid ? 'Mitra: ' + r.name : 'Kode mitra tidak dikenal. Kosongkan bila tidak punya.';
        hint.style.color = r.valid ? 'var(--ok)' : 'var(--err)';
      }).catch(function () {});
    }
    inp.addEventListener('input', function () { clearTimeout(t); t = setTimeout(check, 500); });
    if (code) { inp.value = code; check(); }
  }

'''


def p_daftar(s, rel):
    a = '          <div class="hp" aria-hidden="true">'
    s = rep(s, a, DAFTAR_FIELD + a, rel)
    a = "  fetch(API + '?action=signup_config')"
    s = rep(s, a, DAFTAR_JS + a, rel)
    a = "    if (!c.otp) $('#b1').textContent = 'Daftar sekarang';\n"
    s = rep(s, a, a + "    if (c.partner_field) pcInit();\n", rel)
    a = "      website: $('#website').value,\n"
    s = rep(s, a, a + "      partner_code: $('#partner_code') ? $('#partner_code').value : '',\n", rel)
    return s


# ---------------------------------------------------------------- admin/index.html
ADMIN_CARD = r'''  <!-- v1.2.187: mitra — Program Mitra (reseller / referral) -->
  <div class="card" id="ptCard">
    <div class="row" style="justify-content:space-between">
      <h2 style="margin:0">Mitra / Reseller <span id="ptBadge"></span></h2>
      <div class="row" style="gap:8px"><button class="ghost" onclick="ptLoad()">Muat ulang</button><button class="ghost" onclick="ptCfgEdit()">Atur tier</button><button onclick="ptEdit('')">+ Mitra baru</button></div>
    </div>
    <div class="hint" id="ptHint" style="margin:6px 0 10px">memuat…</div>
    <div id="ptList" style="overflow:auto"></div>
  </div>

'''

ADMIN_JS = r'''// v1.2.187: mitra — Program Mitra (reseller / referral)
let PT={partners:[],cfg:{tiers:[]},free:[],month:'',cur:null};
const ptTierTxt=c=>(c.tiers||[]).map((t,i,a)=>{ const hi=a[i+1]?a[i+1][0]-1:0; return (hi?(hi===t[0]?t[0]:t[0]+'–'+hi):t[0]+'+')+' tenant '+t[1]+'%'; }).join(' · ');
const ptWide=w=>{ $('#modal').style.maxWidth=w?'920px':''; };
{ const _close=window.closeModal; window.closeModal=()=>{ ptWide(false); _close(); }; }
const ptTgl=d=>{ const m=String(d||'').match(/^(\d{4})-(\d{2})-(\d{2})/); return m?m[3]+'/'+m[2]+'/'+m[1]:'–'; };
function ptLoad(){
  return api('partner_list').then(r=>{
    if(!r.ok){ $('#ptHint').textContent=r.error||'Gagal memuat.'; return; }
    PT.partners=r.partners||[]; PT.cfg=r.config||{tiers:[]}; PT.free=r.free_tenants||[]; PT.month=r.month||'';
    const c=PT.cfg, unpaid=PT.partners.reduce((s,p)=>s+(+p.unpaid||0),0);
    $('#ptBadge').innerHTML=unpaid?`<span class="badge idle">${rp(unpaid)} belum dibayar</span>`:'';
    $('#ptHint').innerHTML=`Tier reseller: <b>${esc(ptTierTxt(c))}</b>, dihitung dari jumlah tenant aktif berbayar dan berlaku untuk semua tenant mitra. Referral: ${c.referral_pct}% selama ${c.referral_months} bulan sejak pembayaran pertama. Komisi tercatat otomatis saat pesanan Duitku lunas; pembayaran transfer/invoice dicatat lewat <b>Detail › Catat pembayaran manual</b>. Tautan pendaftaran: <code>${esc(r.signup_url||'')}?ref=KODE</code>${c.signup_field?'':' · <span style="color:var(--err)">isian kode mitra di /daftar/ sedang dimatikan</span>'}`;
    $('#ptList').innerHTML=PT.partners.length?'<table><thead><tr><th>Mitra</th><th>Kode</th><th>Tipe</th><th>Tenant</th><th>Komisi</th><th>Bulan ini</th><th>Belum dibayar</th><th></th></tr></thead><tbody>'+PT.partners.map(p=>`<tr>
      <td><b>${esc(p.name)}</b>${p.active?'':' <span class="badge off">nonaktif</span>'}<br><span class="hint" style="margin:0">${esc([p.contact,p.phone].filter(Boolean).join(' · '))}</span></td>
      <td class="mono">${esc(p.code)}<br><a href="#" onclick="ptCopy('${esc(p.id)}');return false">salin tautan</a></td>
      <td>${p.type==='referral'?'Referral':'Reseller'}</td>
      <td><b>${p.paying}</b> aktif<br><span class="hint" style="margin:0">${p.tenants} terhubung</span></td>
      <td><b>${p.pct}%</b>${p.next?`<br><span class="hint" style="margin:0">${p.next[0]-p.paying} tenant lagi → ${p.next[1]}%</span>`:''}</td>
      <td style="white-space:nowrap">${rp(p.month)}</td>
      <td style="white-space:nowrap">${p.unpaid?'<b>'+rp(p.unpaid)+'</b>':'–'}</td>
      <td style="white-space:nowrap"><button class="ghost" onclick="ptDetail('${esc(p.id)}')">Detail</button> <button class="ghost" onclick="ptEdit('${esc(p.id)}')">Ubah</button></td></tr>`).join('')+'</tbody></table>'
      :'<div class="hint">Belum ada mitra. Klik <b>+ Mitra baru</b>, lalu bagikan kode atau tautan pendaftarannya.</div>';
  });
}
window.ptCopy=function(id){
  const p=PT.partners.find(x=>x.id===id)||(PT.cur&&PT.cur.partner.id===id?PT.cur.partner:null); if(!p) return;
  (navigator.clipboard?navigator.clipboard.writeText(p.link):Promise.reject()).then(()=>toast('Tautan pendaftaran disalin.'),()=>prompt('Salin tautan ini:',p.link));
};
window.ptEdit=function(id){
  const p=PT.partners.find(x=>x.id===id)||{id:'',name:'',code:'',type:'reseller',contact:'',phone:'',email:'',notes:'',active:true};
  ptWide(false);
  $('#modal').innerHTML=`<h3>${id?'Ubah mitra':'Mitra baru'}</h3><div class="modal-body">
    <label>Nama mitra / perusahaan</label><input id="pt_name" value="${esc(p.name)}" placeholder="CV Mitra Digital">
    <label>Kode mitra (4–16 huruf/angka, kosongkan = dibuat otomatis)</label><input id="pt_code" value="${esc(p.code)}" placeholder="MITRADIGI" maxlength="16" style="text-transform:uppercase">
    ${id&&p.tenants?'<div class="hint">Mengganti kode tidak memutus tenant yang sudah terhubung, tapi tautan lama berhenti berlaku.</div>':''}
    <label>Tipe</label><select id="pt_type"><option value="reseller"${p.type!=='referral'?' selected':''}>Reseller — komisi bertingkat (${esc(ptTierTxt(PT.cfg))}), selama pelanggan aktif</option><option value="referral"${p.type==='referral'?' selected':''}>Referral — ${PT.cfg.referral_pct}% selama ${PT.cfg.referral_months} bulan pertama</option></select>
    <label>Nama kontak (PIC)</label><input id="pt_contact" value="${esc(p.contact)}">
    <label>WhatsApp</label><input id="pt_phone" value="${esc(p.phone)}" placeholder="0812xxxxxxxx">
    <label>Email</label><input id="pt_email" value="${esc(p.email)}">
    <label>Catatan (mis. cara pembayaran komisi)</label><textarea id="pt_notes" rows="2">${esc(p.notes)}</textarea>
    <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="pt_active" style="width:auto" ${p.active?'checked':''}> Aktif (kode bisa dipakai mendaftar dan komisi baru dicatat)</label>
    </div><div class="actions">${id?`<button class="danger" style="margin-right:auto" onclick="ptDel('${esc(p.id)}')">Hapus</button>`:''}<button class="ghost" onclick="closeModal()">Batal</button><button id="pt_save" onclick="ptSave('${esc(p.id)}')">Simpan</button></div>`;
  $('#modalBg').classList.add('show');
};
window.ptSave=function(id){
  const btn=$('#pt_save'); if(btn){ if(btn.disabled) return; btn.disabled=true; }
  const body={id,name:$('#pt_name').value,code:$('#pt_code').value,type:$('#pt_type').value,contact:$('#pt_contact').value,phone:$('#pt_phone').value,email:$('#pt_email').value,notes:$('#pt_notes').value,active:$('#pt_active').checked};
  api('partner_save',{method:'POST',body}).then(r=>{ if(r.ok){ toast('Mitra tersimpan. Kode: '+r.partner.code); closeModal(); ptLoad(); } else { if(btn) btn.disabled=false; toast(r.error||'Gagal.',true); } });
};
window.ptDel=function(id){
  if(!confirm('Hapus mitra ini? Hanya bisa bila belum punya tenant dan riwayat komisi.')) return;
  api('partner_delete',{method:'POST',body:{id}}).then(r=>{ if(r.ok){ toast('Mitra dihapus.'); closeModal(); ptLoad(); } else toast(r.error||'Gagal.',true); });
};
window.ptDetail=function(id){
  api('partner_detail',{qs:'id='+encodeURIComponent(id)}).then(r=>{
    if(!r.ok){ toast(r.error||'Gagal.',true); return; }
    PT.cur=r; const p=r.partner, T=r.tenants||[], L=r.ledger||[], today=new Date(Date.now()+7*36e5).toISOString().slice(0,10);
    const tRows=T.map(t=>`<tr><td><b>${esc(t.name)}</b><br><span class="mono">${esc(t.tenant_id)}</span></td><td>${esc(t.tier||'-')}</td>
      <td>${t.paying?'<span class="badge ok">aktif berbayar</span>':(t.tier==='trial'?'<span class="badge idle">trial</span>':'<span class="badge off">tidak aktif</span>')}</td>
      <td>${t.expires_at?ptTgl(t.expires_at):'–'}</td><td>${ptTgl(t.partner_at)}<span class="hint" style="margin:0"> · ${t.partner_via==='signup'?'daftar':'admin'}</span></td>
      <td><button class="ghost" onclick="ptAssign('${esc(t.tenant_id)}','')">Lepas</button></td></tr>`).join('');
    const lRows=L.map(e=>{ const st=e.void?['batal','off',e.void.reason||'']:(e.paid_out?['dibayar','ok',(ptTgl(e.paid_out.at)+' '+(e.paid_out.note||'')).trim()]:['belum dibayar','idle','']);
      return `<tr${e.void?' style="opacity:.55"':''}><td style="white-space:nowrap">${ptTgl(e.date)}</td><td>${esc(e.tenant_name||e.tenant_id)}<br><span class="hint" style="margin:0">${esc(e.note||'')}</span></td>
      <td class="mono">${esc(e.ref)}</td><td style="white-space:nowrap">${rp(e.base)}</td><td>${e.pct}%<span class="hint" style="margin:0"> · ${e.n} tenant</span></td><td style="white-space:nowrap"><b>${rp(e.amount)}</b></td>
      <td><span class="badge ${st[1]}" title="${esc(st[2])}">${st[0]}</span></td><td>${!e.void&&!e.paid_out?`<button class="ghost" onclick="ptVoid('${esc(e.id)}')">Batalkan</button>`:''}</td></tr>`; }).join('');
    ptWide(true);
    $('#modal').innerHTML=`<h3>${esc(p.name)} <span class="mono" style="font-weight:400">· ${esc(p.code)}</span>${p.active?'':' <span class="badge off">nonaktif</span>'}</h3><div class="modal-body">
      <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr));margin-bottom:10px">
        <div class="stat"><div class="v">${p.pct}%</div><div class="l">${p.type==='referral'?'Referral':'Tier · '+p.paying+' tenant aktif'}</div></div>
        <div class="stat"><div class="v">${rp(p.month)}</div><div class="l">Komisi bulan ini</div></div>
        <div class="stat"><div class="v">${rp(p.unpaid)}</div><div class="l">Belum dibayar</div></div>
        <div class="stat"><div class="v">${rp(p.total)}</div><div class="l">Total komisi</div></div>
      </div>
      <div class="hint" style="margin:0 0 12px">${p.next?`Butuh ${p.next[0]-p.paying} tenant aktif lagi untuk naik ke ${p.next[1]}%. `:''}Tautan pendaftaran: <code>${esc(p.link)}</code> <a href="#" onclick="ptCopy('${esc(p.id)}');return false">salin</a></div>
      <h4 style="margin:0 0 6px">Tenant (${T.length})</h4>
      ${T.length?`<div style="overflow:auto"><table><thead><tr><th>Tenant</th><th>Paket</th><th>Status</th><th>Aktif s/d</th><th>Terhubung</th><th></th></tr></thead><tbody>${tRows}</tbody></table></div>`:'<div class="hint">Belum ada tenant.</div>'}
      <div class="row" style="margin:8px 0 16px"><select id="pt_add" style="max-width:340px"><option value="">— pilih tenant yang belum punya mitra —</option>${PT.free.map(t=>`<option value="${esc(t.tenant_id)}">${esc(t.name)} (${esc(t.tenant_id)} · ${esc(t.tier||'-')})</option>`).join('')}</select><button class="ghost" onclick="ptAssign($('#pt_add').value,'${esc(p.id)}')">Hubungkan tenant</button></div>
      <h4 style="margin:0 0 6px">Buku komisi (${L.length})</h4>
      ${L.length?`<div style="overflow:auto"><table><thead><tr><th>Tanggal</th><th>Tenant</th><th>Pesanan</th><th>Dibayar pelanggan</th><th>Tier</th><th>Komisi</th><th>Status</th><th></th></tr></thead><tbody>${lRows}</tbody></table></div>`:'<div class="hint">Belum ada komisi.</div>'}
      <details style="margin-top:14px"><summary style="cursor:pointer;font-weight:600">Catat pembayaran manual (transfer / invoice di luar Duitku)</summary>
        <div class="row" style="margin-top:8px;align-items:flex-end">
          <div><label>Tenant</label><select id="pm_t">${T.map(t=>`<option value="${esc(t.tenant_id)}">${esc(t.name)}</option>`).join('')}</select></div>
          <div><label>Dibayar pelanggan (Rp)</label><input id="pm_base" type="number" min="0" step="1000" style="width:150px"></div>
          <div><label>Tanggal bayar</label><input id="pm_date" type="date" value="${today}"></div>
          <div><label>% khusus (kosong = ${p.pct}%)</label><input id="pm_pct" type="number" min="0" max="90" style="width:90px"></div>
          <div style="flex:1;min-width:160px"><label>Catatan</label><input id="pm_note" placeholder="Growth · 1 bln · invoice INV-…" style="width:100%"></div>
          <button onclick="ptManual('${esc(p.id)}')">Catat</button>
        </div></details>
      </div><div class="actions"><button class="ghost" style="margin-right:auto" onclick="ptSync('${esc(p.id)}')" title="Mencatat pesanan Duitku lunas yang belum masuk buku komisi">Susulkan dari pesanan lunas</button><button class="ghost" onclick="closeModal()">Tutup</button><button onclick="ptPayout('${esc(p.id)}')"${p.unpaid?'':' disabled style="opacity:.5"'}>Tandai dibayar ${p.unpaid?rp(p.unpaid):''}</button></div>`;
    $('#modalBg').classList.add('show');
  });
};
const ptRefresh=id=>ptLoad().then(()=>ptDetail(id));
window.ptAssign=function(tid,pid){
  if(!tid){ toast('Pilih tenant dulu.',true); return; }
  const cur=PT.cur.partner.id;
  if(!pid&&!confirm('Lepas tenant '+tid+' dari mitra ini? Komisi yang sudah tercatat tetap ada; pembayaran berikutnya tidak lagi menghasilkan komisi.')) return;
  api('partner_assign',{method:'POST',body:{tenant_id:tid,partner_id:pid}}).then(r=>{ if(r.ok){ toast(pid?'Tenant terhubung.':'Tenant dilepas.'); ptRefresh(cur); } else toast(r.error||'Gagal.',true); });
};
window.ptManual=function(pid){
  const base=parseInt($('#pm_base').value,10)||0;
  if(!$('#pm_t').value){ toast('Mitra ini belum punya tenant.',true); return; }
  if(base<=0){ toast('Isi nominal yang dibayar pelanggan.',true); return; }
  api('partner_manual',{method:'POST',body:{partner_id:pid,tenant_id:$('#pm_t').value,base,date:$('#pm_date').value,pct:$('#pm_pct').value,note:$('#pm_note').value}}).then(r=>{
    if(r.ok){ toast('Komisi '+rp(r.entry.amount)+' ('+r.entry.pct+'%) tercatat.'); ptRefresh(pid); } else toast(r.error||'Gagal.',true); });
};
window.ptVoid=function(id){
  const reason=prompt('Batalkan komisi ini? Tulis alasannya (mis. refund):',''); if(reason===null) return;
  api('partner_void',{method:'POST',body:{id,reason}}).then(r=>{ if(r.ok){ toast('Komisi dibatalkan.'); ptRefresh(PT.cur.partner.id); } else toast(r.error||'Gagal.',true); });
};
window.ptPayout=function(pid){
  const p=PT.cur.partner, min=+PT.cfg.min_payout||0;
  if(min&&p.unpaid<min&&!confirm('Komisi belum dibayar '+rp(p.unpaid)+' masih di bawah minimal pencairan '+rp(min)+'. Tetap tandai dibayar?')) return;
  const note=prompt('Tandai '+rp(p.unpaid)+' sebagai SUDAH DIBAYAR ke '+p.name+'?\nCatatan pembayaran (mis. transfer BCA 16/11):',''); if(note===null) return;
  api('partner_payout',{method:'POST',body:{partner_id:pid,note}}).then(r=>{ if(r.ok){ toast(r.count+' komisi ('+rp(r.total)+') ditandai dibayar.'); ptRefresh(pid); } else toast(r.error||'Gagal.',true); });
};
window.ptSync=function(pid){
  api('partner_sync',{method:'POST',body:{partner_id:pid}}).then(r=>{ if(r.ok){ toast(r.added?r.added+' komisi disusulkan.':'Tidak ada pesanan lunas yang belum tercatat.'); if(r.added) ptRefresh(pid); } else toast(r.error||'Gagal.',true); });
};
window.ptCfgEdit=function(){
  const c=PT.cfg, rows=(c.tiers||[]).concat([['','']]);
  ptWide(false);
  $('#modal').innerHTML=`<h3>Atur tier komisi mitra</h3><div class="modal-body">
    <div class="hint" style="margin-top:0">Persentase berlaku untuk pembayaran berikutnya; komisi yang sudah tercatat tidak berubah. Tier pertama selalu mulai dari 1 tenant.</div>
    <table><thead><tr><th>Mulai … tenant aktif</th><th>Komisi (%)</th></tr></thead><tbody id="pc_rows">${rows.map(t=>`<tr><td><input type="number" min="1" class="pc_min" value="${t[0]}"></td><td><input type="number" min="0" max="90" class="pc_pct" value="${t[1]}"></td></tr>`).join('')}</tbody></table>
    <div class="hint">Kosongkan baris untuk menghapus tier. Maksimal 6 tier.</div>
    <label>Komisi referral (%)</label><input id="pc_rpct" type="number" min="0" max="90" value="${c.referral_pct}">
    <label>Masa komisi referral (bulan sejak pembayaran pertama)</label><input id="pc_rmon" type="number" min="1" max="120" value="${c.referral_months}">
    <label>Minimal pencairan komisi (Rp)</label><input id="pc_min" type="number" min="0" step="10000" value="${c.min_payout}">
    <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="pc_field" style="width:auto" ${c.signup_field?'checked':''}> Tampilkan isian "Kode mitra" di halaman /daftar/</label>
    </div><div class="actions"><button class="ghost" onclick="closeModal()">Batal</button><button onclick="ptCfgSave()">Simpan</button></div>`;
  $('#modalBg').classList.add('show');
};
window.ptCfgSave=function(){
  const tiers=$$('#pc_rows tr').map(tr=>[parseInt(tr.querySelector('.pc_min').value,10),parseInt(tr.querySelector('.pc_pct').value,10)]).filter(t=>t[0]>0&&t[1]>=0);
  if(!tiers.length){ toast('Isi minimal satu tier.',true); return; }
  api('partner_save_config',{method:'POST',body:{tiers,referral_pct:parseInt($('#pc_rpct').value,10)||0,referral_months:parseInt($('#pc_rmon').value,10)||12,min_payout:parseInt($('#pc_min').value,10)||0,signup_field:$('#pc_field').checked}}).then(r=>{
    if(r.ok){ toast('Tier tersimpan.'); closeModal(); ptLoad(); } else toast(r.error||'Gagal.',true); });
};
ptLoad();
'''


def p_admin(s, rel):
    a = "  <!-- v1.2.90: Pendaftaran mandiri -->"
    s = rep(s, a, ADMIN_CARD + a, rel)
    a = "grpLoad();\n</script>"
    s = rep(s, a, "grpLoad();\n" + ADMIN_JS + "</script>", rel)
    return s


def main():
    if len(sys.argv) != 2:
        die('pakai: python3 patch_pusat_v12187.py <root dei-pusat>')
    root = os.path.abspath(sys.argv[1])
    if not os.path.isfile(os.path.join(root, 'backend', 'billing-lib.php')):
        die('bukan folder dei-pusat (butuh pusat v1.2.173+): ' + root)
    lib = os.path.join(HERE, 'partner-lib.php')
    if not os.path.isfile(lib):
        die('partner-lib.php tidak ada di samping skrip ini')
    dst = os.path.join(root, 'backend', 'partner-lib.php')
    if not os.path.isfile(dst) or open(dst, 'rb').read() != open(lib, 'rb').read():
        if os.path.isfile(dst):
            shutil.copy2(dst, dst + '.bak-v12187-' + STAMP)
        shutil.copy2(lib, dst)
        print('disalin: backend/partner-lib.php')
    else:
        print('lewati (sama): backend/partner-lib.php')
    patch(root, 'backend/index.php', p_index)
    patch(root, 'backend/signup-lib.php', p_signup)
    patch(root, 'backend/billing-lib.php', p_billing)
    patch(root, 'backend/billing-callback.php', p_callback)
    patch(root, 'daftar/index.html', p_daftar)
    patch(root, 'admin/index.html', p_admin)
    print('SELESAI v1.2.187 mitra')


if __name__ == '__main__':
    main()
