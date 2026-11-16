// v1.2.185: master-grup — kelola Dashboard Grup
let GRP={groups:[],tenants:[],max:10,minv:'v1.2.185'};
function grpLoad(){
  Promise.all([api('group_list'),api('list_tenants')]).then(([g,t])=>{
    if(!g.ok){ $('#grpList').innerHTML='<div class="hint">'+esc(g.error||'Gagal memuat.')+'</div>'; return; }
    GRP.groups=g.groups||[]; GRP.max=g.max_tenants||10; GRP.minv=g.min_version||GRP.minv;
    GRP.tenants=(t.ok?t.tenants:[]).map(x=>({id:String(x.tenant_id||'').toLowerCase(),name:x.name||x.tenant_id})).sort((a,b)=>a.name.localeCompare(b.name));
    if(g.url){ $('#grpUrl').href=g.url; $('#grpUrl').textContent=g.url; }
    $('#grpMinVer').textContent=GRP.minv;
    const vlt=v=>{ const p=s=>String(s||'').replace(/^v/,'').split('.').map(Number); const a=p(v),b=p(GRP.minv); for(let i=0;i<3;i++){ if((a[i]||0)!==(b[i]||0)) return (a[i]||0)<(b[i]||0); } return false; };
    $('#grpList').innerHTML=GRP.groups.length?GRP.groups.map(g=>{
      const tl=g.tenants.map(t=>`<span class="badge ${t.exists?(t.version&&vlt(t.version)?'idle':'ok'):'off'}" title="${t.exists?(t.version?('Versi '+esc(t.version)+(vlt(t.version)?' — perlu update untuk laporan grup':'')):'Versi belum diketahui'):'Tenant sudah dihapus'}">${esc(t.name)}</span>`).join(' ')||'<span class="hint">belum ada tenant</span>';
      const ul=g.users.length?'<table style="margin-top:8px"><thead><tr><th>User</th><th>Peran</th><th>Akses tenant</th><th>Akun di tenant</th><th>Login terakhir</th><th></th></tr></thead><tbody>'+g.users.map(u=>{
        const mp=Object.keys(u.map||{}); const acc=u.tenants&&u.tenants.length?u.tenants.length+' dari '+g.tenant_ids.length:'Semua';
        return `<tr><td><b>${esc(u.name||'-')}</b><br><span class="mono">${esc(u.email)}</span>${u.disabled?' <span class="badge off">nonaktif</span>':''}${u.has_password?'':' <span class="badge idle">belum buat password</span>'}</td>
          <td>${u.role==='viewer'?'Lihat laporan':'Manager'}</td><td>${acc}</td><td>${mp.length?mp.length+' terhubung':'<span class="hint" style="margin:0">belum</span>'}</td><td>${esc(u.last_login||'–')}</td>
          <td style="white-space:nowrap"><button class="ghost" onclick="grpUser('${esc(g.id)}','${esc(u.id)}')">Ubah</button>
          <button class="ghost" onclick="grpLink('${esc(g.id)}','${esc(u.id)}',1)" title="Kirim email tautan buat/atur password">Kirim tautan</button>
          <button class="ghost" onclick="grpLink('${esc(g.id)}','${esc(u.id)}',0)" title="Salin tautan buat password (berlaku 3 hari)">Salin</button>
          <button class="danger" onclick="grpUserDel('${esc(g.id)}','${esc(u.id)}')">Hapus</button></td></tr>`; }).join('')+'</tbody></table>':'<div class="hint">Belum ada user grup.</div>';
      return `<div style="border:1px solid var(--line);border-radius:10px;padding:12px;margin-bottom:10px">
        <div class="row" style="justify-content:space-between"><div><b style="font-size:15px">${esc(g.name)}</b> <span class="hint" style="margin:0">${g.tenant_ids.length} tenant · ${g.users.length} user</span></div>
        <div class="row" style="gap:6px"><button class="ghost" onclick="grpEdit('${esc(g.id)}')">Ubah grup</button><button onclick="grpUser('${esc(g.id)}','')">+ User</button><button class="danger" onclick="grpDel('${esc(g.id)}')">Hapus</button></div></div>
        <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">${tl}</div>${ul}</div>`;
    }).join(''):'<div class="hint">Belum ada grup.</div>';
  });
}
window.grpLoad=grpLoad;
window.grpEdit=function(id){
  const g=GRP.groups.find(x=>x.id===id)||{id:'',name:'',tenant_ids:[]};
  $('#modal').innerHTML=`<h3>${id?'Ubah grup':'Grup baru'}</h3><div class="modal-body">
    <label>Nama grup (tampil di Dashboard Grup)</label><input id="g_name" value="${esc(g.name)}" placeholder="Grup Bagong">
    <label>Tenant anggota (maks. ${GRP.max})</label>
    <input id="g_q" placeholder="Cari tenant…" oninput="grpFilt()" style="margin-bottom:6px">
    <div id="g_tl" style="max-height:260px;overflow:auto;border:1px solid var(--line);border-radius:7px;padding:6px 10px">${GRP.tenants.map(t=>`<label data-q="${esc((t.name+' '+t.id).toLowerCase())}" style="display:flex;gap:8px;align-items:center;margin:4px 0;font-size:13px"><input type="checkbox" value="${esc(t.id)}" style="width:auto" ${g.tenant_ids.includes(t.id)?'checked':''}> ${esc(t.name)} <span class="mono hint" style="margin:0">${esc(t.id)}</span></label>`).join('')}</div>
    </div><div class="actions"><button class="ghost" onclick="closeModal()">Batal</button><button onclick="grpSave('${esc(g.id)}')">Simpan</button></div>`;
  $('#modalBg').classList.add('show');
};
window.grpFilt=function(){ const q=$('#g_q').value.toLowerCase(); $$('#g_tl label').forEach(l=>l.style.display=l.dataset.q.includes(q)?'flex':'none'); };
window.grpSave=function(id){
  const ids=$$('#g_tl input:checked').map(i=>i.value);
  if(ids.length>GRP.max){ toast('Maksimal '+GRP.max+' tenant per grup.',true); return; }
  api('group_save',{method:'POST',body:{id,name:$('#g_name').value,tenant_ids:ids}}).then(r=>{ if(r.ok){ toast('Grup tersimpan.'); closeModal(); grpLoad(); } else toast(r.error||'Gagal.',true); });
};
window.grpDel=function(id){
  const g=GRP.groups.find(x=>x.id===id); if(!g||!confirm('Hapus grup "'+g.name+'" beserta '+g.users.length+' user grupnya? Tenant & data tenant tidak tersentuh.')) return;
  api('group_delete',{method:'POST',body:{id}}).then(r=>{ if(r.ok){ toast('Grup dihapus.'); grpLoad(); } else toast(r.error||'Gagal.',true); });
};
window.grpUser=function(gid,uid){
  const g=GRP.groups.find(x=>x.id===gid); if(!g) return;
  const u=g.users.find(x=>x.id===uid)||{id:'',email:'',name:'',role:'manager',tenants:[],map:{},disabled:false,has_password:false};
  $('#modal').innerHTML=`<h3>${uid?'Ubah user grup':'User grup baru'} — ${esc(g.name)}</h3><div class="modal-body">
    <label>Email (dipakai login)</label><input id="u_email" type="email" value="${esc(u.email)}">
    <label>Nama</label><input id="u_name" value="${esc(u.name)}">
    <label>Peran</label><select id="u_role"><option value="manager" ${u.role!=='viewer'?'selected':''}>Manager — laporan + buka dashboard tenant</option><option value="viewer" ${u.role==='viewer'?'selected':''}>Lihat laporan saja</option></select>
    <label>Akses tenant &amp; akun di tiap tenant</label>
    <div class="hint" style="margin:0 0 6px">Centang tenant yang boleh dilihat (kosongkan semua = semua tenant grup). Pilih akun tenant yang dipakai saat menekan <b>Buka</b>; hak aksesnya mengikuti peran akun itu di tenant.</div>
    <table><tbody>${g.tenants.map(t=>`<tr><td style="padding:5px 4px"><label style="display:flex;gap:6px;align-items:center;margin:0;font-size:13px"><input type="checkbox" class="u_t" value="${esc(t.tenant_id)}" style="width:auto" ${(u.tenants||[]).includes(t.tenant_id)?'checked':''}> ${esc(t.name)}</label></td>
      <td style="padding:5px 4px;width:55%"><select class="u_m" data-t="${esc(t.tenant_id)}"><option value="">— memuat akun… —</option></select></td></tr>`).join('')||'<tr><td class="hint">Grup belum punya tenant.</td></tr>'}</tbody></table>
    <label>Password (opsional)</label><input id="u_pw" type="password" autocomplete="new-password" placeholder="${u.has_password?'Kosongkan = tidak diubah':'Kosongkan = user buat sendiri lewat email'}">
    <label style="display:flex;gap:6px;align-items:center"><input type="checkbox" id="u_inv" style="width:auto" ${uid?'':'checked'}> Kirim email ${u.has_password?'tautan atur password':'undangan (tautan buat password, berlaku 3 hari)'}</label>
    <label style="display:flex;gap:6px;align-items:center"><input type="checkbox" id="u_dis" style="width:auto" ${u.disabled?'checked':''}> Nonaktifkan user</label>
    </div><div class="actions"><button class="ghost" onclick="closeModal()">Batal</button><button onclick="grpUserSave('${esc(gid)}','${esc(uid)}')">Simpan</button></div>`;
  $('#modalBg').classList.add('show');
  $$('.u_m').forEach(sel=>{
    const tid=sel.dataset.t, cur=(u.map||{})[tid]||'';
    api('group_tenant_users',{qs:'tenant_id='+encodeURIComponent(tid)}).then(r=>{
      if(!r.ok){   // tenant belum v1.2.185 / tidak terjangkau: username diketik manual
        sel.outerHTML=`<input class="u_m" data-t="${esc(tid)}" value="${esc(cur)}" placeholder="username di tenant (kosong = tidak dihubungkan)"><div class="hint" style="margin:2px 0 0;color:var(--warn)">${esc(r.error||'Gagal memuat akun.')} Ketik username manual; sebelum tenant diupdate, Buka hanya jalan untuk akun Admin.</div>`; return; }
      const RL={super_admin:'Super Admin',admin:'Admin',supervisor:'Supervisor',wa_agent:'Agent'};
      sel.innerHTML='<option value="">— tidak dihubungkan —</option>'+(r.users||[]).map(x=>`<option value="${esc(x.username)}" ${x.username===cur?'selected':''}>${esc(x.name||x.username)} (${esc(x.username)} · ${esc(RL[x.role]||x.role)})</option>`).join('')
        +(cur&&!(r.users||[]).some(x=>x.username===cur)?`<option value="${esc(cur)}" selected>${esc(cur)} (tidak ada lagi di tenant)</option>`:'');
    });
  });
};
window.grpUserSave=function(gid,uid){
  const map={}; $$('.u_m').forEach(s=>{ if(s.value) map[s.dataset.t]=s.value; });
  const body={group_id:gid,id:uid,email:$('#u_email').value,name:$('#u_name').value,role:$('#u_role').value,
    tenants:$$('.u_t:checked').map(i=>i.value),map,password:$('#u_pw').value,send_invite:$('#u_inv').checked,disabled:$('#u_dis').checked};
  api('group_user_save',{method:'POST',body}).then(r=>{
    if(!r.ok){ toast(r.error||'Gagal.',true); return; }
    toast(r.invite_sent===false?'Tersimpan, tapi email gagal terkirim — pakai tombol Salin.':(r.invite_sent?'Tersimpan, email terkirim.':'Tersimpan.'),r.invite_sent===false);
    closeModal(); grpLoad();
  });
};
window.grpUserDel=function(gid,uid){
  if(!confirm('Hapus user grup ini? Akun mereka di tiap tenant tidak ikut terhapus.')) return;
  api('group_user_delete',{method:'POST',body:{group_id:gid,id:uid}}).then(r=>{ if(r.ok){ toast('User dihapus.'); grpLoad(); } else toast(r.error||'Gagal.',true); });
};
window.grpLink=function(gid,uid,email){
  api('group_user_link',{method:'POST',body:{group_id:gid,id:uid,email:email?1:0}}).then(r=>{
    if(!r.ok){ toast(r.error||'Gagal.',true); return; }
    if(email){ toast(r.sent?'Email tautan terkirim.':'Email gagal terkirim — pakai tombol Salin.',!r.sent); return; }
    (navigator.clipboard?navigator.clipboard.writeText(r.url):Promise.reject()).then(()=>toast('Tautan disalin (berlaku 3 hari, sekali pakai).'),()=>prompt('Salin tautan ini:',r.url));
  });
};
grpLoad();
