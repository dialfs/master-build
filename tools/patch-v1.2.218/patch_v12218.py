#!/usr/bin/env python3
"""v1.2.218 (sales-di-lead): assign / ganti / lepas Sales langsung dari kartu Leads (Growth+).
- Daftar: dropdown "Sales" di rincian kartu; Kanban: dropdown Sales di kartu; modal Aktivitas & Task: dropdown di kepala.
- Memakai endpoint sales_tag yang sudah ada (tag kontak + pemilik lead ikut berubah, termasuk lead yang sudah Close;
  aturan v1.2.208: lead yang sudah naik dari Baru tidak bisa dikosongkan; lead Baru hasil tag sales hilang bila dilepas -> konfirmasi).
- Tidak tampil untuk peran Sales. Hanya API version bump di backend.
Butuh v1.2.217. Idempoten. Pakai: patch_v12218.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg); T = H + '/dei-tenant'
TAG = 'v1.2.218: sales-di-lead'; NEED = 'v1.2.217: laporan-crm'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old); assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12218-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API)
else:
    assert NEED in s, 'v1.2.217 belum terpasang di ' + API
    s = rep(s, "define('DEI_VERSION', 'v1.2.217');   // v1.2.217:",
            "define('DEI_VERSION', 'v1.2.218');   // " + TAG + " — assign/ganti Sales langsung dari kartu Leads & modal lead; v1.2.217:", what='ver')
    save(API, s)

JSLIB = r'''
  /* ---- v1.2.218: sales-di-lead — assign Sales dari kartu Leads ---- */
  function crmSalesSel218(l, cls) {
    if (!leadCrm215 || user.role === 'sales' || !crmSales215) return '';
    var cur = l.sales_id || '', has = !cur;
    if (!crmSales215.length && !cur) return '';
    var o = '<option value="">— Tanpa sales —</option>' + crmSales215.map(function (x) {
      if (x.id === cur) has = true;
      return '<option value="' + esc(x.id) + '"' + (x.id === cur ? ' selected' : '') + '>' + esc(x.name) + '</option>';
    }).join('');
    if (!has) o += '<option value="' + esc(cur) + '" selected>' + esc(l.sales_name || cur) + '</option>';
    return '<select class="crm-sl218 ' + (cls || '') + '" data-num="' + esc(l.number) + '" data-prev="' + esc(cur) + '" title="Sales yang memegang lead ini" aria-label="Sales">' + o + '</select>';
  }
  function crmSalesSet218(sel) {
    var num = sel.getAttribute('data-num'), prev = sel.getAttribute('data-prev') || '', v = sel.value;
    if (v === prev) return;
    var l = leadAll203.filter(function (x) { return x.number === num; })[0] || {};
    if (!v && l.src === 'sales' && (l.status || 'baru') === 'baru' &&
        !confirm('Lepas sales dari lead ini?\n\nLead ini dibuat otomatis saat chat di-tag sales dan statusnya masih Baru, jadi kartunya akan hilang dari Leads. Kontak & percakapan tetap ada.')) { sel.value = prev; return; }
    sel.disabled = true;
    api('sales_tag', { method: 'POST', body: { number: num, sales: v } }).then(function (r) {
      sel.disabled = false;
      if (!r || !r.ok) { sel.value = prev; toast((r && r.error) || 'Gagal mengatur sales.', true); return; }
      sel.setAttribute('data-prev', v);
      var nm = v ? ((crmSales215 || []).filter(function (x) { return x.id === v; })[0] || {}).name || v : '';
      toast(v ? 'Lead dipegang ' + nm + '.' : (r.lead_removed ? 'Tag sales dilepas — lead Baru ini dihapus dari Leads.' : 'Tag sales dilepas.'));
      fetchLeads();
    });
  }
  document.addEventListener('change', function (e) { var s = e.target; if (s && s.classList && s.classList.contains('crm-sl218')) crmSalesSet218(s); });
  document.addEventListener('mousedown', function (e) { var s = e.target; if (s && s.classList && s.classList.contains('crm-sl218')) e.stopPropagation(); }, true);

'''

j = open(JS, encoding='utf-8').read()
if TAG in j: print('SUDAH', JS)
else:
    assert NEED in j, 'v1.2.217 belum terpasang di app.js'
    j = rep(j, "  // v1.2.147: leads-kanban — pilihan tampilan diingat per browser\n", JSLIB + "  // v1.2.147: leads-kanban — pilihan tampilan diingat per browser\n", what='js-lib')
    # muat daftar sales sekali, lalu gambar ulang
    j = rep(j, "      leadAll203 = res.leads || []; if (res.pipeline) crmPipeApply216(res.pipeline); /* v1.2.216: pipeline-sales */ slLeadSel203();",
            "      if (leadCrm215 && crmSales215 === null && user.role !== 'sales') crmLoadSales215(function () { renderLeads(); });   // " + TAG + "\n"
            "      leadAll203 = res.leads || []; if (res.pipeline) crmPipeApply216(res.pipeline); /* v1.2.216: pipeline-sales */ slLeadSel203();", what='js-fetch')
    # Daftar: baris Sales di rincian
    j = rep(j, "        '<div class=\"row\" style=\"margin-top:8px\"><label class=\"fl\">Status</label>' +",
            "        (crmSalesSel218(l) ? '<div class=\"row\" style=\"margin-top:8px\"><label class=\"fl\">Sales</label>' + crmSalesSel218(l) + '</div>' : '') +   // " + TAG + "\n"
            "        '<div class=\"row\" style=\"margin-top:8px\"><label class=\"fl\">Status</label>' +", what='js-list')
    # Kanban: dropdown Sales di kartu
    j = rep(j, "            '<div class=\"lk-f\"><select class=\"lk-st\" aria-label=\"Status\">' + leadStatusOptionsHtml(l.status || 'baru') + '</select>' +",
            "            (crmSalesSel218(l) ? '<div class=\"lk-slw\">' + ico('briefcase-business', 12) + crmSalesSel218(l, 'lk-sl') + '</div>' : '') +   // " + TAG + "\n"
            "            '<div class=\"lk-f\"><select class=\"lk-st\" aria-label=\"Status\">' + leadStatusOptionsHtml(l.status || 'baru') + '</select>' +", what='js-kanban')
    # Modal lead: dropdown di kepala
    j = rep(j, "' <span class=\"tag\" style=\"background:' + st.bg + ';color:' + st.fg + '\">' + esc(st.label) + '</span>' + slLeadBadge203(l) + crmFuChip215(l) + '</div>' +",
            "' <span class=\"tag\" style=\"background:' + st.bg + ';color:' + st.fg + '\">' + esc(st.label) + '</span>' + (crmSalesSel218(l) ? ' ' + ico('briefcase-business', 12) + crmSalesSel218(l, 'crm-hd-sl') : slLeadBadge203(l)) + crmFuChip215(l) + '</div>' +   /* " + TAG + " */", what='js-modal')
    save(JS, j)

CSS = r'''  /* v1.2.218: sales-di-lead */
  .lk-card .lk-slw{display:flex;align-items:center;gap:5px;margin-top:8px;color:#075985}
  .lk-card .lk-slw select{flex:1;min-width:0;width:auto;padding:4px 6px;font-size:12px;border-radius:7px;background:#f0f9ff;border-color:#bae6fd;color:#075985}
  .crm-hd .crm-hd-sl{width:auto;padding:3px 6px;font-size:12px;border-radius:7px;background:#f0f9ff;border:1px solid #bae6fd;color:#075985}
  .lead-body select.crm-sl218{max-width:320px}
'''
h = open(HT, encoding='utf-8').read()
if TAG in h: print('SUDAH', HT)
else:
    assert NEED in h, 'v1.2.217 belum terpasang di index.html'
    h = rep(h, '  .lk-empty{', CSS + '  .lk-empty{', what='html-css')
    h = rep(h, '<script src="app.js?v=1.2.217"></script>', '<script src="app.js?v=1.2.218"></script><!-- ' + TAG + ' -->', what='html-ver')
    save(HT, h)
print('SELESAI patch', TAG)
