#!/usr/bin/env python3
"""v1.2.118 close-deal-lose: status lead "Closed" dipecah jadi Close Deal & Close Lose.
Status lama 'closed' tetap sah (data lama), tampil "Closed (lama)" sampai diganti agent.
Pakai: python3 patch_v12118_close_deal_lose.py [~/Herd/dei-tenant] (idempoten)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.118: close-deal-lose'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def patch(rel, edits):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    shutil.copy2(p, p + '.bak-v12118-' + STAMP)
    for old, new in edits:
        n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:80]); s = s.replace(old, new)
    assert TAG in s, rel; open(p, 'w', encoding='utf-8').write(s); print('OK', rel)

patch('api/index.php', [
 ("define('DEI_VERSION', 'v1.2.117');   // v1.2.117: filter-lead-rating",
  "define('DEI_VERSION', 'v1.2.118');   // v1.2.118: close-deal-lose"),
 ("""    return in_array($s, ['baru', 'qualified', 'follow_up', 'closed'], true);""",
  """    // v1.2.118: close-deal-lose — 'closed' lama tetap sah untuk data yang sudah ada
    return in_array($s, ['baru', 'qualified', 'follow_up', 'closed_deal', 'closed_lost', 'closed'], true);"""),
])

patch('dashboard/chatbot-ai/app.js', [
 ("""    closed:    { label: 'Closed',    bg: '#e0e7ff', fg: '#3730a3' }
  };""",
  """    // v1.2.118: close-deal-lose — Closed dipecah dua; 'closed' = data lama
    closed_deal: { label: 'Close Deal', bg: '#bbf7d0', fg: '#166534', grp: 'Close' },
    closed_lost: { label: 'Close Lose', bg: '#fecaca', fg: '#991b1b', grp: 'Close' },
    closed:      { label: 'Closed (lama)', bg: '#e0e7ff', fg: '#3730a3', legacy: true }
  };
  function leadStatusOptionsHtml(cur) {
    var h = '', grp = '';
    Object.keys(LEAD_STATUS).forEach(function (k) {
      var d = LEAD_STATUS[k];
      if (d.legacy && cur !== k) return;   // pilihan lama hanya tampil bila masih dipakai
      var g = d.grp || '';
      if (g !== grp) { if (grp) h += '</optgroup>'; if (g) h += '<optgroup label="' + g + '">'; grp = g; }
      h += '<option value="' + k + '"' + (cur === k ? ' selected' : '') + '>' + d.label + (d.legacy ? ' \\u2014 pilih Deal/Lose' : '') + '</option>';
    });
    if (grp) h += '</optgroup>';
    return h;
  }
  function leadFilterLegacyBtn() {
    var ada = leadData.some(function (l) { return l.status === 'closed'; });
    var b = $('#leadFltLegacy');
    if (b) b.style.display = ada ? '' : 'none';
    if (!ada && leadFilter === 'closed') {
      leadFilter = 'all';
      $$('.lead-filter').forEach(function (x) { x.classList.toggle('active', x.dataset.leadStatus === 'all'); });
    }
  }"""),
 ("""  function renderLeads() {
    var list = leadData.filter(function (l) {""",
  """  function renderLeads() {
    leadFilterLegacyBtn();   // v1.2.118
    var list = leadData.filter(function (l) {"""),
 ("""      var opsi = Object.keys(LEAD_STATUS).map(function (k) {
        return '<option value="' + k + '"' + ((l.status || 'baru') === k ? ' selected' : '') + '>' + LEAD_STATUS[k].label + '</option>';
      }).join('');""",
  """      var opsi = leadStatusOptionsHtml(l.status || 'baru');   // v1.2.118"""),
])

patch('dashboard/chatbot-ai/index.html', [
 ("""          <button class="btn ghost sm lead-filter" data-lead-status="closed">Closed</button>""",
  """          <button class="btn ghost sm lead-filter" data-lead-status="closed_deal">Close Deal</button><!-- v1.2.118: close-deal-lose -->
          <button class="btn ghost sm lead-filter" data-lead-status="closed_lost">Close Lose</button>
          <button class="btn ghost sm lead-filter" data-lead-status="closed" id="leadFltLegacy" style="display:none" title="Lead lama berstatus Closed — ubah ke Close Deal atau Close Lose">Closed (lama)</button>"""),
])
