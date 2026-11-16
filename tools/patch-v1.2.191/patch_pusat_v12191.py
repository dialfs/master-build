#!/usr/bin/env python3
"""v1.2.191: mitra-skema — skema komisi per mitra (default / persentase tetap / tier khusus). KHUSUS PUSAT, di atas v1.2.190.

  python3 patch_pusat_v12191.py <root dei-pusat>

- backend/partner-lib.php, backend/partner-portal-lib.php, mitra/index.html diperbarui
- backend/index.php: partner_save mencatat admin yang mengubah skema
- admin/index.html: pilihan "Skema komisi" di modal mitra, tanda "khusus" di daftar
Idempoten (penanda "v1.2.191: mitra-skema"); backup *.bak-v12191-<waktu>.
"""
import os, shutil, sys, time

MARK = 'v1.2.191: mitra-skema'
STAMP = time.strftime('%Y%m%d-%H%M%S')
HERE = os.path.dirname(os.path.abspath(__file__))


def die(msg):
    print('GAGAL: ' + msg)
    sys.exit(1)


def rep(s, old, new, path):
    if s.count(old) != 1:
        die('jangkar tidak cocok di %s (%d): %r' % (path, s.count(old), old[:90]))
    return s.replace(old, new)


def patch(root, rel, fn, need):
    path = os.path.join(root, rel)
    with open(path, encoding='utf-8') as f:
        s = f.read()
    if MARK in s:
        print('lewati (sudah dipatch): ' + rel)
        return
    if need not in s:
        die(rel + ' belum dipatch ' + need)
    out = fn(s, rel)
    shutil.copy2(path, path + '.bak-v12191-' + STAMP)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(out)
    print('dipatch: ' + rel)


def put(root, src, rel):
    a = os.path.join(HERE, src); b = os.path.join(root, rel)
    if not os.path.isfile(a) or not os.path.isfile(b):
        die('tidak ada: ' + src + ' atau ' + rel)
    if open(a, 'rb').read() == open(b, 'rb').read():
        print('lewati (sama): ' + rel)
        return
    shutil.copy2(b, b + '.bak-v12191-' + STAMP)
    shutil.copy2(a, b)
    print('disalin: ' + rel)


def p_index(s, rel):
    a = "        list($ok, $res) = ptSave(bodyInput());"
    return rep(s, a, "        list($ok, $res) = ptSave(['_by' => (string)(requireAdmin()['username'] ?? '')] + bodyInput());   // " + MARK + " — siapa yang mengubah skema", rel)


JS_FORM = r'''    <label>Skema komisi</label><select id="pt_scheme" onchange="ptSchemeUI()"><option value="default"${!p.scheme||p.scheme==='default'?' selected':''}>Default — ikut aturan umum tipe di atas</option><option value="fixed"${p.scheme==='fixed'?' selected':''}>Persentase tetap — satu angka khusus mitra ini</option><option value="tiers"${p.scheme==='tiers'?' selected':''}>Tier khusus — tabel tier sendiri untuk mitra ini</option></select>
    <div id="pt_sfix" style="display:none"><label>Komisi tetap (%)</label><input id="pt_spct" type="number" min="0" max="90" value="${p.scheme==='fixed'?p.scheme_pct:''}" oninput="ptSchemeUI()" placeholder="mis. 40"></div>
    <div id="pt_stier" style="display:none"><table style="margin-top:6px"><thead><tr><th>Mulai … tenant aktif</th><th>Komisi (%)</th></tr></thead><tbody id="ps_rows">${((p.scheme==='tiers'&&p.scheme_tiers&&p.scheme_tiers.length?p.scheme_tiers:(PT.cfg.tiers||[])).concat([['','']])).map(t=>`<tr><td><input type="number" min="1" class="ps_min" value="${t[0]}" oninput="ptSchemeUI()"></td><td><input type="number" min="0" max="90" class="ps_pct" value="${t[1]}" oninput="ptSchemeUI()"></td></tr>`).join('')}</tbody></table><div class="hint">Tier pertama selalu mulai dari 1 tenant. Kosongkan baris untuk menghapusnya. Maksimal 6 tier.</div></div>
    <div class="hint" id="pt_swarn" style="display:none"></div>
    ${id&&p.scheme_at&&p.scheme&&p.scheme!=='default'?`<div class="hint">Skema khusus diatur ${esc(p.scheme_at)} UTC${p.scheme_by?' oleh '+esc(p.scheme_by):''}.</div>`:''}
'''

JS_FN = r'''// v1.2.191: mitra-skema — skema komisi per mitra di modal Ubah mitra
window.ptSchemeTiers=function(){
  return $$('#ps_rows tr').map(tr=>[parseInt(tr.querySelector('.ps_min').value,10),parseInt(tr.querySelector('.ps_pct').value,10)]).filter(t=>t[0]>0&&t[1]>=0);
};
window.ptSchemeUI=function(){
  const sc=$('#pt_scheme'); if(!sc) return;
  const m=sc.value, ref=$('#pt_type').value==='referral';
  $('#pt_sfix').style.display=m==='fixed'?'':'none'; $('#pt_stier').style.display=m==='tiers'?'':'none';
  const max=m==='fixed'?(parseInt($('#pt_spct').value,10)||0):(m==='tiers'?Math.max(0,...ptSchemeTiers().map(t=>t[1])):0), w=$('#pt_swarn'), msg=[];
  if(m!=='default') msg.push('Berlaku untuk pembayaran berikutnya; komisi yang sudah tercatat tidak berubah.');
  if(m==='tiers'&&ref) msg.push('<span style="color:var(--err)">Tier khusus hanya untuk tipe Reseller. Untuk Referral pakai Persentase tetap.</span>');
  if(max>50) msg.push('<span style="color:var(--err)"><b>Di atas 50%:</b> pada paket Pro dengan pemakaian maksimal, sisa untuk DEI di bawah 20% dan bisa rugi bila ada diskon tahunan.</span>');
  else if(max>40) msg.push('<span style="color:var(--warn)"><b>Di atas 40%:</b> pada paket Pro dengan pemakaian maksimal, sisa untuk DEI di bawah 30% dari harga.</span>');
  w.innerHTML=msg.join('<br>'); w.style.display=msg.length?'':'none';
};
'''


def p_admin(s, rel):
    a = '    <label>Nama kontak (PIC)</label><input id="pt_contact"'
    s = rep(s, a, JS_FORM + a, rel)
    a = '<label>Tipe</label><select id="pt_type">'
    s = rep(s, a, '<label>Tipe</label><select id="pt_type" onchange="ptSchemeUI()">', rel)
    a = "type:$('#pt_type').value,contact:"
    s = rep(s, a, "type:$('#pt_type').value,scheme:$('#pt_scheme').value,scheme_pct:$('#pt_spct').value,scheme_tiers:ptSchemeTiers(),contact:", rel)
    a = "  $('#modalBg').classList.add('show');\n};\nwindow.ptSave=function(id){"
    s = rep(s, a, "  $('#modalBg').classList.add('show');\n  ptSchemeUI();\n};\nwindow.ptSave=function(id){", rel)
    a = "<td><b>${p.pct}%</b>${p.next?"
    s = rep(s, a, "<td><b>${p.pct}%</b>${p.scheme&&p.scheme!=='default'?` <span class=\"badge idle\" title=\"Skema komisi khusus mitra ini: ${p.scheme==='fixed'?'persentase tetap':'tier khusus'}\">khusus</span>`:''}${p.next?", rel)
    a = "${p.type==='referral'?'Referral':'Tier · '+p.paying+' tenant aktif'}"
    s = rep(s, a, "${p.scheme==='fixed'?'Persentase tetap (khusus)':(p.type==='referral'?'Referral':(p.scheme==='tiers'?'Tier khusus':'Tier')+' · '+p.paying+' tenant aktif')}", rel)
    a = "window.ptCfgEdit=function(){"
    s = rep(s, a, JS_FN + a, rel)
    return s


def main():
    if len(sys.argv) != 2:
        die('pakai: python3 patch_pusat_v12191.py <root dei-pusat>')
    root = os.path.abspath(sys.argv[1])
    put(root, 'partner-lib.php', 'backend/partner-lib.php')
    put(root, 'partner-portal-lib.php', 'backend/partner-portal-lib.php')
    put(root, 'mitra-index.html', 'mitra/index.html')
    patch(root, 'backend/index.php', p_index, 'v1.2.189: mitra-masuk')
    patch(root, 'admin/index.html', p_admin, 'v1.2.190: admin-tampilan')
    print('SELESAI v1.2.191 mitra-skema')


if __name__ == '__main__':
    main()
