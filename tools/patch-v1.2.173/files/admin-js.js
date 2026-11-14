// v1.2.173: bayar-mandiri — pembayaran online Duitku
const BL_FIELDS=['price_starter','price_growth','price_business','price_pro','disc_3','disc_12','duitku_env','duitku_file','pay_base','admin_email','refund_url','expiry_minutes'];
const rp=n=>'Rp'+Number(n||0).toLocaleString('id-ID');
function loadBlCfg(){
  api('get_billing_config').then(res=>{
    if(!res.ok) return;
    const c=res.billing;
    BL_FIELDS.forEach(k=>{ const el=$('#bl_'+k); if(el) el.value = c[k] ?? ''; });
    $('#bl_enabled').checked=!!c.enabled; $('#bl_reminders').checked=!!c.reminders;
    const warn=[];
    if(!c.duitku_ok) warn.push('kredensial Duitku tidak terbaca');
    if(!c.waha_ok) warn.push('WAHA pendaftaran belum diatur (notifikasi WA mati)');
    $('#blState').innerHTML=(c.enabled?'<span class="badge ok">DIBUKA</span> ':'<span class="badge off">DITUTUP</span> ')
      +(c.duitku_ok?'Duitku <b>'+esc(c.duitku_env_eff)+'</b> · merchant '+esc(c.duitku_merchant)+' · ':'')
      +(warn.length?'<span style="color:var(--err)">Perlu dicek: '+esc(warn.join(' · '))+'</span>':'Siap.')
      +'<br>Callback: <code>'+esc(c.callback_url)+'</code> · Halaman: <code>'+esc(c.pay_base_eff)+'/bayar/</code>';
  });
}
window.saveBlCfg=function(){
  const body={enabled:$('#bl_enabled').checked, reminders:$('#bl_reminders').checked};
  BL_FIELDS.forEach(k=>{ const el=$('#bl_'+k); if(el) body[k]=el.type==='number'?(parseInt(el.value,10)||0):el.value.trim(); });
  if(body.enabled && body.duitku_env==='sandbox' && !confirm('Mode SANDBOX: tenant tidak benar-benar membayar tapi paket tetap aktif saat simulasi lunas. Lanjutkan (hanya untuk uji)?')) return;
  api('save_billing_config',{method:'POST',body}).then(res=>{ if(res.ok){ toast('Pengaturan pembayaran tersimpan.'); loadBlCfg(); load(); } else toast(res.error||'Gagal.',true); });
};
const BL_ST={paid:['Lunas','ok'],pending:['Menunggu','idle'],failed:['Gagal/Batal','off']};
const BL_MODE={trial:'trial → berbayar',new:'baru',renew:'perpanjang',upgrade:'naik paket',downgrade:'turun paket'};
function loadBlOrders(){
  api('billing_orders').then(res=>{
    if(!res.ok) return;
    const os=res.orders||[], paid=os.filter(o=>o.status==='paid'), m=new Date().toISOString().slice(0,7);
    const bulan=paid.filter(o=>String(o.paid_at||'').slice(0,7)===m).reduce((s,o)=>s+(+o.amount||0),0);
    $('#blBadge').innerHTML=paid.length?`<span class="badge ok">${rp(bulan)} bulan ini</span>`:'';
    $('#blOrders').innerHTML=os.length?'<table><thead><tr><th>Waktu</th><th>Pesanan</th><th>Tenant</th><th>Paket</th><th>Total</th><th>Status</th><th></th></tr></thead><tbody>'+os.map(o=>{
      const s=BL_ST[o.status]||[o.status,'idle'], a=o.applied||{};
      return `<tr><td style="white-space:nowrap">${esc(new Date(o.created_at).toLocaleString('id-ID'))}</td>
        <td class="mono">${esc(o.id)}${o.env==='sandbox'?' <span class="badge idle">sandbox</span>':''}</td>
        <td><b>${esc(o.tenant_name||'')}</b><br><span class="mono">${esc(o.tenant_id)}</span></td>
        <td>${esc(o.tier)} · ${o.months} bln<br><span class="hint" style="margin:0">${esc(BL_MODE[o.mode]||o.mode)}${a.ends?' · s/d '+esc(a.ends):''}</span></td>
        <td style="white-space:nowrap">${rp(o.amount)}${o.quote&&o.quote.credit?`<br><span class="hint" style="margin:0">kredit ${rp(o.quote.credit)}</span>`:''}</td>
        <td><span class="badge ${s[1]}">${s[0]}</span>${o.payment&&o.payment.paymentCode?`<br><span class="hint" style="margin:0">${esc(o.payment.paymentCode)}</span>`:''}${o.apply_error?`<div style="color:var(--err);font-size:12px">${esc(o.apply_error)}</div>`:''}
          <div class="hint" style="margin:0">${esc(o.customer?.name||'')} · ${esc(o.customer?.phone||'')}</div></td>
        <td>${o.status!=='paid'?`<button class="ghost" onclick="blRecheck('${esc(o.id)}')">Cek Duitku</button>`:''}</td></tr>`;
    }).join('')+'</tbody></table>':'<div style="color:var(--muted)">Belum ada pesanan.</div>';
  });
}
window.loadBlOrders=loadBlOrders;
window.blRecheck=function(id){ api('billing_recheck',{method:'POST',body:{order:id}}).then(r=>{ toast(r.message||r.error||'?',!r.ok); loadBlOrders(); load(); }); };
window.billingLink=function(id){
  api('billing_link',{method:'POST',body:{tenant_id:id}}).then(r=>{
    if(!r.ok){ toast(r.error||'Gagal.',true); return; }
    const el=$('#m_bill');
    const note=!r.enabled?'Pembayaran online masih DITUTUP. ':(!r.eligible?r.reason+' ':'');
    if(navigator.clipboard) navigator.clipboard.writeText(r.url).then(()=>toast('Link bayar disalin.'),()=>{});
    if(el) el.innerHTML=(note?'<span style="color:var(--err)">'+esc(note)+'</span>':'')+'<a href="'+esc(r.url)+'" target="_blank" rel="noopener" class="mono">'+esc(r.url)+'</a>';
  });
};
loadBlCfg(); loadBlOrders(); setInterval(loadBlOrders, 60000);
