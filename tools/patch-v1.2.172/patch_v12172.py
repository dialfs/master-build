#!/usr/bin/env python3
"""v1.2.172 trial-paket (TENANT): trial paket Growth membuka fitur Growth (Filter Topik, Customer Feedback;
nomor WA & unit bisnis sudah dari pusat). Beda Starter vs Growth dibuat jelas: label "Growth" di menu,
kartu perbandingan paket di Laporan, tombol "Lihat beda Starter & Growth" di fitur terkunci, banner trial menyebut paketnya.
Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HTML = T + '/dashboard/chatbot-ai/index.html'
TAG = 'v1.2.172: trial-paket'; stamp = time.strftime('%Y%m%d-%H%M%S')
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    shutil.copy2(p, p + '.bak-v12172-' + stamp); wr(p, fn(s)); print('OK', p)
C = '   // ' + TAG

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.171');   // v1.2.171:",
               "define('DEI_VERSION', 'v1.2.172');   // " + TAG + " — trial bisa paket Growth (fitur Growth terbuka), beda Starter vs Growth tampil jelas; v1.2.171:", 'versi')
    s = rep(s, "            'upgrade_url' => substr((string)($t['upgrade_url'] ?? ''), 0, 300)];\n}",
               "            'upgrade_url' => substr((string)($t['upgrade_url'] ?? ''), 0, 300),\n"
               "            'tier' => strtolower((string)($t['tier'] ?? '')) === 'growth' ? 'growth' : 'starter'];" + C + " — paket yang dicoba (maks Growth)\n}", 'norm')
    for name, const in [('gc', 'GC_TIERS'), ('tp', 'TP_TIERS')]:
        s = rep(s, "    $ok = !$trial && in_array($tier, explode(',', " + const + "), true);\n",
                   "    $tt = $trial ? ((is_array($cap['trial'] ?? null) ? ($cap['trial']['tier'] ?? '') : '') === 'growth' ? 'growth' : 'starter') : '';" + C + "\n"
                   "    $ok = $trial ? ($tt === 'growth') : in_array($tier, explode(',', " + const + "), true);\n", name + ' plan')
    s = rep(s, "    return $GLOBALS['dei_gc_plan'] = ['ok' => $ok, 'tier' => $trial ? 'trial' : $tier, 'trial' => $trial];\n",
               "    return $GLOBALS['dei_gc_plan'] = ['ok' => $ok, 'tier' => $trial ? 'trial' : $tier, 'trial' => $trial, 'trial_tier' => $tt];\n", 'gc ret')
    s = rep(s, "    return $GLOBALS['dei_tp_plan'] = ['ok' => $ok, 'tier' => $trial ? 'trial' : $tier, 'trial' => $trial, 'central' => true];\n",
               "    return $GLOBALS['dei_tp_plan'] = ['ok' => $ok, 'tier' => $trial ? 'trial' : $tier, 'trial' => $trial, 'trial_tier' => $tt, 'central' => true];\n", 'tp ret')
    s = rep(s, "    case 'team_info': {\n",
        "    case 'plan_info': {" + C + " — paket efektif untuk tampilan beda Starter vs Growth\n"
        "        requireAuth(['super_admin', 'admin', 'supervisor', 'wa_agent']);\n"
        "        $s = getSettings();\n"
        "        $cs = $s['central_server'] ?? [];\n"
        "        if (empty($cs['url']) || empty($cs['tenant_id']) || empty($cs['license_key'])) jsonOut(['ok' => true, 'central' => false, 'tier' => 'custom', 'growth' => true, 'trial' => false]);\n"
        "        $cap = [];\n"
        "        try { $cap = getCapStatus($s); } catch (\\Throwable $e) { error_log('plan_info: ' . $e->getMessage()); }\n"
        "        $tr = is_array($cap['trial'] ?? null) ? $cap['trial'] : null;\n"
        "        $tier = strtolower(trim((string)($cap['tier'] ?? '')));\n"
        "        $eff = $tr ? (($tr['tier'] ?? '') === 'growth' ? 'growth' : 'starter') : ($tier !== '' && $tier !== 'trial' ? $tier : 'starter');\n"
        "        jsonOut(['ok' => true, 'central' => true, 'tier' => $eff, 'growth' => $eff !== 'starter', 'trial' => (bool)$tr,\n"
        "                 'days_left' => $tr ? (int)($tr['days_left'] ?? 0) : null, 'upgrade_url' => $tr ? (string)($tr['upgrade_url'] ?? '') : '']);\n"
        "        break;\n"
        "    }\n"
        "    case 'team_info': {\n", 'plan_info')
    return s

JS_BLOCK = r"""
  /* ====================================================================== *
   *  v1.2.172: trial-paket — beda paket Starter vs Growth dibuat jelas
   *  (label "Growth" di menu, kartu perbandingan, tombol bandingkan di fitur terkunci)
   * ====================================================================== */
  var PLAN = null, planCbs = null;
  function planGet(cb) {
    if (PLAN) { cb(PLAN); return; }
    if (planCbs) { planCbs.push(cb); return; }
    planCbs = [cb];
    api('plan_info').then(function (r) {
      PLAN = (r && r.ok) ? r : { ok: false, tier: 'custom', growth: true, trial: false };
      var l = planCbs; planCbs = null; l.forEach(function (f) { try { f(PLAN); } catch (e) {} });
    });
  }
  var PLAN_ROWS = [
    ['Balasan AI per bulan', '1.000', '2.000'],
    ['Chatbot WhatsApp + widget web', true, true],
    ['Knowledge Base, Produk & Leads', true, true],
    ['Tim & agent, Kontak, Blast WA', true, true],
    ['Nomor WhatsApp tambahan', false, '+2 nomor'],
    ['Unit Bisnis (cabang / brand / divisi)', false, '3 unit'],
    ['Filter Topik & Divisi — chat WA dipilah AI otomatis', false, '5.000 chat/bulan'],
    ['Customer Feedback — survei kepuasan WA & web', false, true]
  ];
  (function () {
    var st = document.createElement('style');
    st.textContent =
      '.plan-tag{margin-left:auto;font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;padding:2px 7px;border-radius:9px;background:#fef3c7;color:#92400e;line-height:1.4;flex-shrink:0}' +
      '.plan-tag.on{background:#cffafe;color:#0e7490}' +
      '.pc-tbl{width:100%;border-collapse:separate;border-spacing:0;font-size:13px;margin-top:14px}' +
      '.pc-tbl th,.pc-tbl td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:center;vertical-align:middle}' +
      '.pc-tbl td:first-child,.pc-tbl th:first-child{text-align:left}' +
      '.pc-tbl th{font-size:13.5px}.pc-tbl th small{display:block;font-weight:500;font-size:10.5px;opacity:.8;margin-top:2px}' +
      '.pc-tbl .pc-g{background:#ecfeff;width:30%}.pc-tbl th.pc-g{background:linear-gradient(135deg,#0891b2,#0e7490);color:#fff;border-radius:10px 10px 0 0}' +
      '.pc-tbl td.pc-s,.pc-tbl th.pc-s{width:24%;color:var(--muted)}' +
      '.pc-tbl tr.pc-x td{font-weight:600}.pc-tbl tr.pc-x td.pc-g{color:#0e7490}' +
      '.pc-y{color:#16a34a;display:inline-flex}.pc-n{color:#cbd5e1;font-weight:700}' +
      '.pc-head{display:flex;gap:12px;align-items:flex-start}.pc-head>svg{flex-shrink:0;color:#0e7490;margin-top:2px}' +
      '.pc-head p{margin:4px 0 0;color:var(--muted);font-size:13px;line-height:1.5}' +
      '.pc-foot{margin-top:14px;display:flex;justify-content:flex-end;align-items:center;gap:10px;flex-wrap:wrap}' +
      '.pc-cta{background:linear-gradient(135deg,#0891b2,#0e7490)!important;color:#fff!important;text-decoration:none;display:inline-flex;gap:6px;align-items:center;border:0}' +
      '.pc-ctx{font-size:13px;color:#0e7490;font-weight:600}' +
      '.pc-more{font-size:12px;color:var(--muted);margin-top:8px}' +
      '.pc-ov{position:fixed;inset:0;background:rgba(15,23,42,.55);z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px}' +
      '.pc-box{background:#fff;color:var(--ink);border-radius:14px;max-width:640px;width:100%;max-height:90vh;overflow:auto;padding:22px;position:relative;box-shadow:0 20px 50px rgba(0,0,0,.25)}' +
      '.pc-box h3{margin:0;display:flex;gap:8px;align-items:center;color:#0e7490}' +
      '.pc-close{position:absolute;right:12px;top:8px;border:0;background:none;font-size:24px;cursor:pointer;color:var(--muted)}' +
      '@media(max-width:600px){.pc-tbl{font-size:12px}.pc-tbl th,.pc-tbl td{padding:7px 6px}}';
    document.head.appendChild(st);
  })();
  function planCell(v) {
    if (v === true) return '<span class="pc-y">' + ico('check-circle-2', 16) + '</span>';
    if (v === false) return '<span class="pc-n">&ndash;</span>';
    return esc(v);
  }
  function planCta(p) {
    var u = p && p.upgrade_url;
    return u ? '<a class="btn pc-cta" href="' + esc(u) + '" target="_blank" rel="noopener">' + ico('crown', 15) + ' Berlangganan Growth</a>'
             : '<span class="pc-ctx">' + ico('crown', 14, 'style="vertical-align:-2px"') + ' Hubungi ' + esc(BRAND_VENDOR) + ' untuk upgrade ke Growth.</span>';
  }
  function planCompareHtml(p) {
    var g = !!(p && p.growth);
    var h = '<table class="pc-tbl"><thead><tr><th>Fitur</th>' +
      '<th class="pc-s">Starter' + (!g ? '<small>' + (p && p.trial ? 'Trial Anda' : 'Paket Anda') + '</small>' : '') + '</th>' +
      '<th class="pc-g">' + ico('crown', 14, 'style="vertical-align:-2px"') + ' Growth<small>' + (g ? (p.trial ? 'Sedang Anda coba' : 'Paket Anda') : 'Direkomendasikan') + '</small></th></tr></thead><tbody>';
    PLAN_ROWS.forEach(function (r) {
      h += '<tr' + (r[1] === false ? ' class="pc-x"' : '') + '><td>' + esc(r[0]) + '</td><td class="pc-s">' + planCell(r[1]) + '</td><td class="pc-g">' + planCell(r[2]) + '</td></tr>';
    });
    return h + '</tbody></table><div class="pc-more">Butuh lebih besar? <b>Business</b> (5.000 balasan, +4 nomor, 5 unit) dan <b>Pro</b> (15.000 balasan, +9 nomor, 10 unit).</div>';
  }
  window.showPlanCompare = function () {
    planGet(function (p) {
      var ov = document.createElement('div'); ov.className = 'pc-ov';
      ov.innerHTML = '<div class="pc-box"><button type="button" class="pc-close" aria-label="Tutup">&times;</button>' +
        '<h3>' + ico('crown', 20) + ' Beda paket Starter &amp; Growth</h3>' + planCompareHtml(p) +
        '<div class="pc-foot">' + (p.growth && !p.trial ? '' : planCta(p)) + '</div></div>';
      ov.onclick = function (e) { if (e.target === ov || (e.target.closest && e.target.closest('.pc-close'))) ov.remove(); };
      document.body.appendChild(ov);
    });
  };
  function planBtn() {
    return '<div style="margin-top:10px"><button type="button" class="btn sm pc-cta" onclick="showPlanCompare()">' + ico('crown', 14) + ' Lihat beda Starter &amp; Growth</button></div>';
  }
  function renderPlanCard() {
    var uc = document.getElementById('usageCard'); if (!uc) return;
    planGet(function (p) {
      var el = document.getElementById('planCard');
      if (!p.ok || (p.growth && !p.trial)) { if (el) el.style.display = 'none'; return; }
      if (!el) { el = document.createElement('div'); el.id = 'planCard'; el.className = 'card'; uc.parentNode.insertBefore(el, uc.nextSibling); }
      el.style.display = '';
      var head = p.growth
        ? '<div class="pc-head">' + ico('crown', 22) + '<div><b>Anda sedang mencoba paket Growth</b><p>Semua fitur Growth aktif selama trial' + (p.days_left != null ? ' (' + p.days_left + ' hari lagi)' : '') +
          ': Filter Topik &amp; Divisi, Customer Feedback, nomor WA tambahan, dan Unit Bisnis. Berlangganan Growth supaya fitur ini tetap jalan setelah trial berakhir.</p></div></div>'
        : '<div class="pc-head">' + ico('rocket', 22) + '<div><b>Naik ke Growth, layani pelanggan lebih rapi</b><p>Paket Anda ' + (p.trial ? 'trial Starter' : 'Starter') +
          '. Dengan Growth, chat WA otomatis dipilah per topik/divisi, kepuasan pelanggan terukur lewat survei, bisa pakai nomor WA tambahan dan beberapa unit bisnis, dengan kuota balasan AI dua kali lipat.</p></div></div>';
      el.innerHTML = head + planCompareHtml(p) + '<div class="pc-foot">' + planCta(p) + '</div>';
    });
  }
  function planNav() {
    planGet(function (p) {
      if (!p.ok || (p.growth && !p.trial)) return;
      ['topik', 'gc'].forEach(function (k) {
        var b = document.querySelector('#nav button[data-tab="' + k + '"]');
        if (!b || b.querySelector('.plan-tag')) return;
        b.insertAdjacentHTML('beforeend', '<span class="plan-tag' + (p.growth ? ' on' : '') + '" title="' + (p.growth ? 'Fitur paket Growth — aktif selama trial' : 'Fitur paket Growth — klik untuk melihat') + '">Growth</span>');
      });
    });
  }

"""

def js(s):
    s = rep(s, "  function renderCapBanner() {\n", JS_BLOCK + "  function renderCapBanner() {\n", 'block')
    s = rep(s, "<b>Masa trial: ' + t.days_left + ' hari lagi</b>",
               "<b>Masa trial' + (t.tier === 'growth' ? ' paket Growth' : '') + ': ' + t.days_left + ' hari lagi</b>", 'banner')
    s = rep(s, "                       + '<span class=\"uc-label\">Paket</span>'\n                       + (tierLabels[tier] || tier);\n",
               "                       + '<span class=\"uc-label\">Paket</span>'\n                       + (tierLabels[tier] || tier) + (res.trial && res.trial.tier === 'growth' ? ' · Growth' : '');" + C + "\n", 'badge')
    s = rep(s, "      if (res.trial) {   // v1.2.90: kartu pemakaian untuk masa trial\n",
               "      renderPlanCard();" + C + "\n      if (res.trial) {   // v1.2.90: kartu pemakaian untuk masa trial\n", 'plan card')
    s = rep(s, "'</b>.' : '') + '</p></div>';\n    var st = $('#tfStatus');",
               "'</b>.' : '') + '</p>' + planBtn() + '</div>';" + C + "\n    var st = $('#tfStatus');", 'tf lock')
    s = rep(s, "' Data feedback yang sudah masuk tetap bisa dilihat & diekspor.' : '') + '</p></div>';",
               "' Data feedback yang sudah masuk tetap bisa dilihat & diekspor.' : '') + '</p>' + planBtn() + '</div>';" + C, 'gc lock')
    s = rep(s, "Hubungi tim DEI untuk upgrade.</div>';",
               "Hubungi tim DEI untuk upgrade.' + planBtn() + '</div>';" + C, 'bu lock')
    s = rep(s, "  renderCapBanner();\n  renderOnboarding();",
               "  renderCapBanner();\n  planNav();" + C + "\n  renderOnboarding();", 'nav')
    return s

def html(s):
    return rep(s, '<script src="app.js?v=1.2.171"></script>', '<script src="app.js?v=1.2.172"></script><!-- ' + TAG + ' -->', 'cache bust')

for p, fn in [(API, api), (JS, js), (HTML, html)]:
    patch(p, fn)
