#!/usr/bin/env python3
"""v1.2.192: asisten-support — umpan KB & pengaturan tenant Support. KHUSUS PUSAT, di atas v1.2.191.

  python3 patch_pusat_v12192.py <root dei-pusat>

- backend/support-lib.php (baru): pengaturan Support, umpan KB dari blok `guide` rilis + entri paket & harga
- backend/index.php: require lib; check_update mengirim `support_widget`; action support_kb_feed,
  get_support_config, save_support_config
- admin/index.html: kartu "Asisten Support" di menu Pengaturan
- dev/preflight.sh: validasi blok `guide` (manifest rilis & releases/guide.json)
Idempoten (penanda "v1.2.192: asisten-support"); backup *.bak-v12192-<waktu>.
"""
import os, shutil, sys, time

MARK = 'v1.2.192: asisten-support'
NEED = 'v1.2.191: mitra-skema'
STAMP = time.strftime('%Y%m%d-%H%M%S')
HERE = os.path.dirname(os.path.abspath(__file__))


def die(msg):
    print('GAGAL: ' + msg)
    sys.exit(1)


def rep(s, old, new, path):
    if s.count(old) != 1:
        die('jangkar tidak cocok di %s (%d): %r' % (path, s.count(old), old[:90]))
    return s.replace(old, new)


def patch(root, rel, fn, need=None):
    path = os.path.join(root, rel)
    with open(path, encoding='utf-8') as f:
        s = f.read()
    if MARK in s:
        print('lewati (sudah dipatch): ' + rel)
        return
    if need and need not in s:
        die(rel + ' belum dipatch ' + need)
    out = fn(s, rel)
    shutil.copy2(path, path + '.bak-v12192-' + STAMP)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(out)
    print('dipatch: ' + rel)


def put_new(root, src, rel):
    a = os.path.join(HERE, src); b = os.path.join(root, rel)
    if not os.path.isfile(a):
        die('tidak ada: ' + src)
    if os.path.isfile(b):
        if open(a, 'rb').read() == open(b, 'rb').read():
            print('lewati (sama): ' + rel)
            return
        shutil.copy2(b, b + '.bak-v12192-' + STAMP)
    shutil.copy2(a, b)
    print('disalin: ' + rel)


# ---------------------------------------------------------------- backend/index.php
PHP_CASES = r'''    /* v1.2.192: asisten-support — umpan KB untuk tenant Support (panduan per fitur + paket & harga).
     * Wajib tenant_id + license_key yang cocok DAN tenant itu yang ditunjuk sebagai tenant Support. */
    case 'support_kb_feed': {
        $body = bodyInput();
        $tenantId   = trim((string)($body['tenant_id']   ?? ($_SERVER['HTTP_X_TENANT_ID']   ?? '')));
        $licenseKey = trim((string)($body['license_key'] ?? ($_SERVER['HTTP_X_LICENSE_KEY'] ?? '')));
        if ($tenantId === '' || $licenseKey === '') jsonOut(['ok' => false, 'error' => 'tenant_id & license_key wajib.'], 400);
        $tenant = null;
        foreach (readJson(TENANTS_FILE, []) as $t) {
            if (tidEq($t['tenant_id'] ?? '', $tenantId)) { $tenant = $t; break; }
        }
        if (!$tenant) jsonOut(['ok' => false, 'error' => 'Tenant tidak terdaftar di server pusat.'], 404);
        if (!hash_equals((string)($tenant['license_key'] ?? ''), $licenseKey)) jsonOut(['ok' => false, 'error' => 'License key tidak cocok.'], 403);
        $spc = spCfg();
        if ($spc['tenant_id'] === '' || !tidEq($tenant['tenant_id'] ?? '', $spc['tenant_id'])) jsonOut(['ok' => false, 'error' => 'Umpan ini hanya untuk tenant Support.'], 403);
        $feed = spFeed(true);
        if ((string)($body['rev'] ?? '') === $feed['rev']) jsonOut(['ok' => true, 'rev' => $feed['rev'], 'unchanged' => true]);
        jsonOut(['ok' => true, 'rev' => $feed['rev'], 'entries' => $feed['entries']]);
    }
    case 'get_support_config': {
        requireAdmin();
        jsonOut(['ok' => true, 'support' => spCfgAdmin()]);
    }
    case 'save_support_config': {
        requireAdmin();
        list($spOk, $spErr) = spSaveCfg(bodyInput());
        if (!$spOk) jsonOut(['ok' => false, 'error' => $spErr], 400);
        jsonOut(['ok' => true, 'support' => spCfgAdmin()]);
    }

'''


def p_index(s, rel):
    a = "require_once __DIR__ . '/partner-portal-lib.php';   // v1.2.188: mitra-portal\n"
    s = rep(s, a, a + "require_once __DIR__ . '/support-lib.php';   // " + MARK + "\n", rel)
    a = "            'pay_url'          => $tenant ? blPayUrl($tenant) : '',   // v1.2.173: bayar-mandiri — tautan bayar/perpanjang mandiri\n"
    s = rep(s, a, a + "            'support_widget'   => spWidgetPayload($tenant),   // " + MARK + " — tombol Bantuan di dashboard tenant\n", rel)
    a = "    /* v1.2.65: catatan rilis untuk halaman \"Pembaruan\" di dashboard tenant.\n"
    s = rep(s, a, PHP_CASES + a, rel)
    return s


# ---------------------------------------------------------------- admin/index.html
HTML_CARD = r'''  <div class="card"><!-- v1.2.192: asisten-support -->
    <h2>Asisten Support (bantuan di dashboard tenant)</h2>
    <div class="hint" style="margin-bottom:10px">Tenant Support menjawab pertanyaan pengguna dashboard: cara setting, letak menu, paket. KB-nya terisi otomatis dari blok <span class="mono">guide</span> di manifest rilis dan <span class="mono">releases/guide.json</span>, ditambah entri paket &amp; harga dari Pengaturan Pembayaran. Perubahan <b>langsung tayang</b> saat tenant Support menarik umpan.</div>
    <div class="row" style="gap:10px">
      <div style="flex:1;min-width:220px"><label>Tenant Support (tenant_id)</label><input id="sp_tid" style="width:100%" placeholder="dei-support"></div>
      <div style="flex:1;min-width:260px"><label>Alamat tenant Support</label><input id="sp_base" style="width:100%" placeholder="https://chatbot.deintegra.com/support"></div>
    </div>
    <label style="font-size:13px;margin-top:8px;display:block"><input type="checkbox" id="sp_enabled"> Tampilkan tombol Bantuan di dashboard tenant (tenant v1.2.194 ke atas)</label>
    <label style="font-size:13px;margin-top:4px;display:block"><input type="checkbox" id="sp_notify"> Kirim ringkasan ke Telegram setiap KB berubah</label>
    <div class="hint" id="spState" style="margin-top:6px"></div>
    <div id="spList" style="display:none;margin-top:8px;max-height:260px;overflow:auto"></div>
    <button onclick="saveSpCfg()" style="margin-top:10px">Simpan Asisten Support</button>
  </div>

'''

JS_FN = r'''// v1.2.192: asisten-support
function spRender(c){
  $('#sp_tid').value=c.tenant_id||''; $('#sp_base').value=c.base||''; $('#sp_enabled').checked=!!c.enabled; $('#sp_notify').checked=!!c.notify;
  const f=c.feed||{count:0,entries:[],invalid:[]};
  let h='Umpan KB: <b>'+f.count+'</b> entri'+(f.entries.length?' — <a href="#" onclick="spToggleList();return false">lihat daftar</a>':'')+'. ';
  if(!c.tenant_id) h+='Tenant Support belum diatur, jadi umpan belum ditarik siapa pun.';
  else if(!f.pulled_at) h+='Belum pernah ditarik tenant Support.';
  else h+='Terakhir ditarik '+esc(f.pulled_at)+' UTC'+(f.in_sync?' (sudah sama dengan isi terbaru).':' — <span style="color:var(--err)">ada perubahan yang belum ditarik.</span>');
  if(f.invalid&&f.invalid.length) h+='<br><span style="color:var(--err)">Dilewati karena tidak sah: '+f.invalid.map(esc).join(' · ')+'</span>';
  $('#spState').innerHTML=h;
  $('#spList').innerHTML=f.entries.length?'<table><thead><tr><th>Kunci</th><th>Judul</th><th>Menu</th><th>Paket min.</th><th>Sejak</th><th>Diubah</th></tr></thead><tbody>'
    +f.entries.map(e=>'<tr><td class="mono">'+esc(e.key)+'</td><td>'+esc(e.title)+'</td><td>'+esc(e.menu||'-')+'</td><td>'+esc(e.min_tier||'-')+'</td><td>'+esc(e.since||'-')+'</td><td>'+esc(e.updated||'-')+'</td></tr>').join('')+'</tbody></table>':'';
}
window.spToggleList=function(){ const l=$('#spList'); l.style.display=l.style.display==='none'?'':'none'; };
function loadSpCfg(){ api('get_support_config').then(res=>{ if(res.ok) spRender(res.support); }); }
window.saveSpCfg=function(){
  api('save_support_config',{method:'POST',body:{tenant_id:$('#sp_tid').value.trim(),base:$('#sp_base').value.trim(),enabled:$('#sp_enabled').checked,notify:$('#sp_notify').checked}})
    .then(res=>{ if(res.ok){ toast('Pengaturan Asisten Support tersimpan.'); spRender(res.support); } else toast(res.error||'Gagal.',true); });
};
loadSpCfg();
'''


def p_admin(s, rel):
    a = ' <section class="view" data-view="cfg">\n'
    s = rep(s, a, a + HTML_CARD, rel)
    a = "};\nloadClsCfg();\n"
    s = rep(s, a, a + JS_FN, rel)
    return s


# ---------------------------------------------------------------- dev/preflight.sh
PY_GUIDE = r'''# v1.2.192: asisten-support — blok guide langsung tayang di KB tenant Support, jadi wajib sah sebelum deploy
def guide_bad(g):
    if not isinstance(g,dict): return 'item bukan objek'
    k=str(g.get('key',''))
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,39}',k): return 'key tidak sah: %r'%k
    if k=='paket-harga': return 'paket-harga dibangkitkan otomatis, jangan ditulis'
    if g.get('remove'): return ''
    t=' '.join(str(g.get('title','')).split()); c=str(g.get('content','')).strip()
    if not 3<=len(t)<=120: return k+': title harus 3-120 karakter'
    if not 20<=len(c)<=4000: return k+': content harus 20-4000 karakter'
    if not re.fullmatch(r'[a-z0-9_-]{0,24}',str(g.get('menu',''))): return k+': menu tidak sah'
    if str(g.get('min_tier','')) not in ('','starter','growth','business','pro'): return k+': min_tier tidak dikenal'
    for f in ('since','updated'):
        if g.get(f) and not re.fullmatch(r'v\d+\.\d+\.\d+',str(g[f])): return k+': '+f+' harus vX.Y.Z'
    if re.search(r'sk-[a-z]+-|license_key|\.secret|public_html|/home/|api[_ ]?key\s*[:=]|password\s*[:=]|token\s*[:=]',t+' '+c,re.I): return k+': isi tampak memuat data internal (kunci/path server)'
    return ''
gsrc=[m for m in sorted(glob.glob('releases/v*/manifest.json'))]+(['releases/guide.json'] if os.path.isfile('releases/guide.json') else [])
for m in gsrc:
    try: j=json.load(open(m,encoding='utf-8'))
    except Exception:
        if m.endswith('guide.json'): bad.append(m+' (JSON rusak)')
        continue
    if not isinstance(j,dict) or 'guide' not in j:
        if m.endswith('guide.json'): bad.append(m+' (wajib punya "guide")')
        continue
    if not isinstance(j['guide'],list): bad.append(m+' (guide bukan daftar)'); continue
    seen=set()
    for g in j['guide']:
        e=guide_bad(g)
        if e: bad.append(m+' (guide: '+e+')')
        elif g['key'] in seen: bad.append(m+' (guide: key ganda '+g['key']+')')
        else: seen.add(g['key'])
'''


def p_preflight(s, rel):
    a = "for b in bad: print('   RUSAK:',b)\n"
    return rep(s, a, PY_GUIDE + a, rel)


def main():
    if len(sys.argv) != 2 or not os.path.isfile(os.path.join(sys.argv[1], 'backend', 'index.php')):
        die('pakai: python3 patch_pusat_v12192.py <root dei-pusat>')
    root = sys.argv[1]
    adm = open(os.path.join(root, 'admin', 'index.html'), encoding='utf-8').read()
    if NEED not in adm:
        die('admin/index.html belum v1.2.191')
    put_new(root, 'support-lib.php', 'backend/support-lib.php')
    patch(root, 'backend/index.php', p_index)
    patch(root, 'admin/index.html', p_admin, NEED)
    patch(root, 'dev/preflight.sh', p_preflight)
    print('SELESAI ' + MARK)


if __name__ == '__main__':
    main()
