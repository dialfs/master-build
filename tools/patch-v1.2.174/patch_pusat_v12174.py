#!/usr/bin/env python3
"""v1.2.174 update-dari-pusat (PUSAT): backend/update-push-lib.php + update-push.php (CLI), action=push_update,
Admin › Daftar Tenant: tombol Update per tenant + Update semua tenant. Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
P = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-pusat')
HERE = os.path.dirname(os.path.abspath(__file__))
IDX = P + '/backend/index.php'; ADM = P + '/admin/index.html'
TAG = 'v1.2.174: update-dari-pusat'; stamp = time.strftime('%Y%m%d-%H%M%S')
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    shutil.copy2(p, p + '.bak-v12174-' + stamp); wr(p, fn(s)); print('OK', p)

for f in ['update-push-lib.php', 'update-push.php']:
    shutil.copy2(HERE + '/files/backend/' + f, P + '/backend/' + f); print('salin', f)

def idx(s):
    s = rep(s, "require_once __DIR__ . '/billing-lib.php';   // v1.2.173: bayar-mandiri (Duitku)\n",
               "require_once __DIR__ . '/billing-lib.php';   // v1.2.173: bayar-mandiri (Duitku)\n"
               "require_once __DIR__ . '/update-push-lib.php';   // " + TAG + "\n"
               "if (defined('DEI_PUSAT_CLI_LIB')) return;   // " + TAG + " — dimuat sebagai pustaka oleh backend/update-push.php\n", 'require')
    s = rep(s, "    case 'list_releases': {\n",
        "    /* " + TAG + " — pasang rilis terbaru ke satu tenant (UI memanggil per tenant, maks. 3 paralel) */\n"
        "    case 'push_update': {\n"
        "        $adm = requireAdmin();\n"
        "        $id = tidNorm((string)(bodyInput()['tenant_id'] ?? ''));\n"
        "        $latest = latestVersion();\n"
        "        if (!$latest) jsonOut(['ok' => false, 'error' => 'Belum ada rilis.'], 400);\n"
        "        @ignore_user_abort(true); @set_time_limit(200);\n"
        "        foreach (readJson(TENANTS_FILE, []) as $t) {\n"
        "            if (!tidEq($t['tenant_id'] ?? '', $id)) continue;\n"
        "            $r = puPushOne($t, $latest, readJson(DATA_DIR . '/cron-status.json', []), (string)($adm['username'] ?? 'admin'));\n"
        "            jsonOut($r + ['latest' => $latest]);\n"
        "        }\n"
        "        jsonOut(['ok' => false, 'error' => 'Tenant tidak ditemukan.'], 404);\n"
        "    }\n\n"
        "    case 'list_releases': {\n", 'push_update')
    s = rep(s, " *   - tenant_reports    histori report-back per tenant\n",
               " *   - tenant_reports    histori report-back per tenant\n"
               " *   - push_update       pasang rilis terbaru ke tenant dari pusat (" + TAG + ")\n", 'doc')
    return s

def adm(s):
    s = rep(s, '      <button id="btnAdd">+ Daftarkan Tenant Baru</button>\n',
               '      <div class="row" style="gap:8px"><!-- ' + TAG + ' -->\n'
               '        <button class="ghost" id="btnUpdAll" onclick="pushUpdateAll()" style="display:none" title="Pasang versi terbaru ke semua tenant aktif yang tertinggal (3 sekaligus)"></button>\n'
               '        <button id="btnAdd">+ Daftarkan Tenant Baru</button>\n'
               '      </div>\n', 'btn all')
    s = rep(s, "<td><span class=\"badge ${verBadge}\">${esc(t.current_version||'belum')}</span></td>",
               "<td data-upd=\"${esc(t.tenant_id)}\" style=\"white-space:nowrap\">${verCell(t, latest)}</td><!-- " + TAG + " -->", 'ver cell')
    s = rep(s, "    $('#kVer').textContent=latest;\n",
               "    $('#kVer').textContent=latest;\n"
               "    window._outdated=outdatedIds(ts, latest);   // " + TAG + "\n"
               "    { const b=$('#btnUpdAll'); if(b && !b.disabled){ b.style.display=window._outdated.length?'':'none'; b.textContent='Update semua tenant ('+window._outdated.length+')'; } }\n", 'load')
    s = rep(s, "window.ssoAsSa = function(id){\n",
        "/* " + TAG + " — tombol Update per tenant & Update semua tenant */\n"
        "function verCmp(a,b){ const p=s=>String(s||'').replace(/^v/,'').split('.').map(n=>parseInt(n,10)||0); const x=p(a),y=p(b); for(let i=0;i<3;i++){ if((x[i]||0)!==(y[i]||0)) return (x[i]||0)<(y[i]||0)?-1:1; } return 0; }\n"
        "function canPush(t, latest){ const v=t.current_version||''; return !!t.active && !!v && latest!=='–' && verCmp(v,latest)<0 && verCmp(v,'v1.2.90')>=0; }\n"
        "function outdatedIds(ts, latest){ return ts.filter(t=>canPush(t,latest)).map(t=>t.tenant_id); }\n"
        "function verCell(t, latest){\n"
        "  const v=t.current_version||''; const lp=t.last_update_push||null;\n"
        "  let h=`<span class=\"badge ${v===latest?'ok':(v?'idle':'off')}\">${esc(v||'belum')}</span>`;\n"
        "  if(canPush(t,latest)) h+=` <button class=\"ghost\" style=\"padding:2px 8px;font-size:11px\" title=\"Pasang ${esc(latest)} sekarang dari pusat\" onclick=\"pushUpdate('${esc(t.tenant_id)}')\">Update</button>`;\n"
        "  else if(t.active && v && latest!=='–' && verCmp(v,latest)<0) h+=` <span class=\"badge off\" title=\"Versi di bawah v1.2.90 — update pertama manual dari dashboard tenant\">manual</span>`;\n"
        "  if(lp && !lp.ok && v && verCmp(v,latest)<0) h+=` <span class=\"badge off\" title=\"${esc((lp.at_wib||'')+' WIB — '+(lp.error||''))}\">gagal</span>`;\n"
        "  return h;\n"
        "}\n"
        "window.pushUpdate = function(id, quiet){\n"
        "  if(!quiet && !confirm('Pasang versi terbaru ke tenant '+id+' sekarang?')) return Promise.resolve({ok:false});\n"
        "  const c=document.querySelector('[data-upd=\"'+id+'\"]'); if(c) c.innerHTML='<span class=\"badge idle\">memperbarui…</span>';\n"
        "  return api('push_update',{method:'POST',body:{tenant_id:id}}).catch(()=>({ok:false,error:'Koneksi terputus.'})).then(res=>{\n"
        "    if(!res.ok && res.error==='Respons tidak valid.') res.error='Tidak ada jawaban (kemungkinan timeout) — update bisa tetap berjalan, cek lagi 1–2 menit.';\n"
        "    if(c) c.innerHTML = res.ok ? `<span class=\"badge ok\">${esc(res.version||'ok')}</span>` : `<span class=\"badge off\" title=\"${esc(res.error||'')}\">gagal</span>`;\n"
        "    if(!quiet){ toast(res.ok?(res.message||'Selesai.'):(res.error||'Gagal.'), !res.ok); if(res.ok) setTimeout(load, 800); }\n"
        "    return res;\n"
        "  });\n"
        "};\n"
        "window.pushUpdateAll = function(){\n"
        "  const ids=(window._outdated||[]).slice(); const latest=$('#kVer').textContent;\n"
        "  if(!ids.length){ toast('Semua tenant aktif sudah versi terbaru.'); return; }\n"
        "  if(!confirm('Pasang '+latest+' ke '+ids.length+' tenant sekarang?\\n\\n'+ids.join(', '))) return;\n"
        "  const btn=$('#btnUpdAll'); btn.disabled=true; let i=0, n=0; const ok=[], fail=[];\n"
        "  btn.textContent='Memperbarui… 0/'+ids.length;\n"
        "  const worker=()=>{ if(i>=ids.length) return Promise.resolve(); const id=ids[i++];\n"
        "    return pushUpdate(id,true).then(r=>{ if(r.ok) ok.push(id); else fail.push(id+': '+(r.error||'gagal')); btn.textContent='Memperbarui… '+(++n)+'/'+ids.length; }).then(worker); };\n"
        "  Promise.all([worker(),worker(),worker()]).then(()=>{\n"
        "    btn.disabled=false; toast(ok.length+' tenant diperbarui'+(fail.length?', '+fail.length+' gagal':'')+'.', fail.length>0);\n"
        "    if(fail.length) alert('Gagal diperbarui:\\n\\n'+fail.join('\\n'));\n"
        "    load();\n"
        "  });\n"
        "};\n"
        "window.ssoAsSa = function(id){\n", 'fns')
    s = rep(s, '<div class="hint">Upload versi baru manual ke <code>releases/v1.x.x/</code> di server. Symlink <code>latest</code> opsional.</div>',
               '<div class="hint">Upload versi baru manual ke <code>releases/v1.x.x/</code> di server. Setelah rilis, pasang ke tenant lewat tombol <b>Update</b> di Daftar Tenant (atau <b>Update semua tenant</b>).</div><!-- ' + TAG + ' -->', 'hint')
    return s

patch(IDX, idx)
patch(ADM, adm)
