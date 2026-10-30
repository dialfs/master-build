#!/usr/bin/env python3
"""v1.2.117 filter-lead-rating: saring Percakapan WA (dropdown) & Percakapan Web (chip) per Lead Rating.
Web: Lead Rating diambil dari kontak bernomor sama dengan nomor HP form pengunjung, bisa diubah dari kepala thread.
Pakai: python3 patch_v12117_filter_lead_rating.py [~/Herd/dei-tenant] (idempoten)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.117: filter-lead-rating'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def patch(rel, edits):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    shutil.copy2(p, p + '.bak-v12117-' + STAMP)
    for old, new in edits:
        n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:80]); s = s.replace(old, new)
    assert TAG in s, rel; open(p, 'w', encoding='utf-8').write(s); print('OK', rel)

patch('api/index.php', [
 ("define('DEI_VERSION', 'v1.2.116');   // v1.2.116: pindah-nomor",
  "define('DEI_VERSION', 'v1.2.117');   // v1.2.117: filter-lead-rating"),
 ("""function waContactStage($number, $contacts = null) {""",
  """// v1.2.117: filter-lead-rating — nilai filter: '' (semua) | stage | 'vip' (| 'nonum' untuk web)
function deiStageFilterVal($v, $allowNonum = false) {
    $v = (string)$v;
    if ($v === 'vip' || ($allowNonum && $v === 'nonum') || contactStageValid($v)) return $v;
    return '';
}
function deiStageMatch($f, $stage, $vip) {
    if ($f === '') return true;
    if ($f === 'vip') return (bool)$vip;
    return $stage === $f;
}
function deiStageCountsInit($withNonum = false) {
    $c = ['all' => 0, 'new' => 0, 'cold' => 0, 'warm' => 0, 'hot_prospect' => 0, 'lost' => 0, 'active_customer' => 0, 'churned' => 0, 'vip' => 0];
    if ($withNonum) $c['nonum'] = 0;
    return $c;
}
function deiStageCountAdd(&$c, $stage, $vip) {
    $c['all']++;
    if (isset($c[$stage])) $c[$stage]++;
    if ($vip) $c['vip']++;
}
// Lead Rating percakapan web = kontak dengan nomor HP dari form pengunjung ('' = tanpa nomor).
function deiWebConvStage($cv, $contacts) {
    $ln = contactImportNormNum($cv['lead_phone'] ?? '');
    $cv['lead_number'] = $ln;
    $cv['stage'] = $ln !== '' ? waContactStage($ln, $contacts) : '';
    $cv['vip'] = $ln !== '' ? waContactVip($ln, $contacts) : false;
    return $cv;
}
function waContactStage($number, $contacts = null) {"""),
 # wa_conversations_v2
 ("""        if (!isset($chMap[$chF])) $chF = '';
        $allLeads = leadsGetAll();""",
  """        if (!isset($chMap[$chF])) $chF = '';
        $stF = deiStageFilterVal($_GET['stage'] ?? '');   // v1.2.117: filter-lead-rating
        $stCounts = deiStageCountsInit();
        $allLeads = leadsGetAll();"""),
 ("""            if ($show) $result[] = $item;""",
  """            if ($show) {   // v1.2.117: jumlah per Lead Rating dihitung dalam filter status aktif
                deiStageCountAdd($stCounts, $item['stage'], $item['vip']);
                if (deiStageMatch($stF, $item['stage'], $item['vip'])) $result[] = $item;
            }"""),
 ("""            'channels' => $chList, 'ch' => $chF,   // v1.2.98: multi-nomor""",
  """            'channels' => $chList, 'ch' => $chF,   // v1.2.98: multi-nomor
            'stage_counts' => $stCounts, 'stage' => $stF,   // v1.2.117: filter-lead-rating"""),
 # web_conversations_admin
 ("""        usort($convs, function ($a, $b) {
            return strcmp($b['last_ts'] ?? '', $a['last_ts'] ?? '');
        });

        // Pagination""",
  """        usort($convs, function ($a, $b) {
            return strcmp($b['last_ts'] ?? '', $a['last_ts'] ?? '');
        });

        // v1.2.117: filter-lead-rating
        $stF = deiStageFilterVal($_GET['stage'] ?? '', true);
        $stCounts = deiStageCountsInit(true);
        $cts117 = []; try { $cts117 = waGetContacts(); } catch (\\Throwable $e) { error_log('web stage: ' . $e->getMessage()); }
        $flt117 = [];
        foreach ($convs as $cv) {
            $cv = deiWebConvStage($cv, $cts117);
            if ($cv['lead_number'] === '') { $stCounts['all']++; $stCounts['nonum']++; $ok = ($stF === '' || $stF === 'nonum'); }
            else { deiStageCountAdd($stCounts, $cv['stage'], $cv['vip']); $ok = ($stF !== 'nonum' && deiStageMatch($stF, $cv['stage'], $cv['vip'])); }
            if ($ok) $flt117[] = $cv;
        }
        $convs = $flt117;

        // Pagination"""),
 ("""            'total_pages'   => (int)ceil($total / $perPage),
        ]);""",
  """            'total_pages'   => (int)ceil($total / $perPage),
            'stage_counts'  => $stCounts,   // v1.2.117
            'stage'         => $stF,
        ]);"""),
 ("""        $messages = webConvLoadMessages($convId);
        jsonOut([
            'ok'           => true,
            'conversation' => $convs[$idx],""",
  """        $messages = webConvLoadMessages($convId);
        $cts117 = []; try { $cts117 = waGetContacts(); } catch (\\Throwable $e) {}
        jsonOut([
            'ok'           => true,
            'conversation' => deiWebConvStage($convs[$idx], $cts117),   // v1.2.117: filter-lead-rating"""),
])

patch('dashboard/chatbot-ai/app.js', [
 ("""  var webState = { convs: [], current: null, timer: null };""",
  """  var webState = { convs: [], current: null, timer: null, stage: '', stageCounts: null };   // v1.2.117: filter-lead-rating"""),
 # helper
 ("""  function contactStageBadgeHtml(stage, vip, extraStyle) {""",
  """  // v1.2.117: filter-lead-rating — pilihan filter Lead Rating (Percakapan WA & Web)
  var STAGE_FLT_EXTRA = { vip: 'VIP', nonum: 'Tanpa nomor HP' };
  function stageFltLabel(k) {
    if (!k) return 'Semua Lead Rating';
    return CONTACT_STAGE[k] ? CONTACT_STAGE[k].label : (STAGE_FLT_EXTRA[k] || k);
  }
  function stageFltKeys(withNonum) {
    var ks = [''];
    CONTACT_STAGE_ORDER.forEach(function (k) { if (k !== '__sep__') ks.push(k); });
    ks.push('vip');
    if (withNonum) ks.push('nonum');
    return ks;
  }
  function stageFltOptionsHtml(sel, counts) {
    return stageFltKeys(false).map(function (k) {
      var n = counts ? counts[k || 'all'] : null;
      return '<option value="' + k + '"' + (sel === k ? ' selected' : '') + '>' + esc(stageFltLabel(k)) +
        (n != null ? ' (' + Number(n).toLocaleString('id-ID') + ')' : '') + '</option>';
    }).join('');
  }
  function contactStageBadgeHtml(stage, vip, extraStyle) {"""),
 ("""        fetchWaConvs().then(function () { if (waState.current === num) fetchWaThread(num); });""",
  """        fetchWaConvs().then(function () { if (waState.current === num) fetchWaThread(num); });
        if ($('#panel-webchat') && $('#panel-webchat').classList.contains('active')) {   // v1.2.117: filter-lead-rating
          fetchWebConvs(true).then(function () { if (webState.current) fetchWebThread(webState.current, true); });
        }"""),
 # WA dropdown
 ("""      (waState.isAdmin === false ? '' : '<button class="wa-filter-btn wa-export-contacts\"""",
  """      '<select class="wa-stage-filter' + (waState.stage ? ' is-active' : '') + '" title="Saring per Lead Rating" style="width:auto;max-width:230px;flex:0 0 auto;padding:5px 10px;border-radius:999px;font-size:12px">' +   // v1.2.117: filter-lead-rating
        stageFltOptionsHtml(waState.stage || '', waState.stageCounts) + '</select>' +
      (waState.isAdmin === false ? '' : '<button class="wa-filter-btn wa-export-contacts\""""),
 ("""    if (_chSel) _chSel.onchange = function () { waState.ch = this.value; fetchWaConvs(); };""",
  """    if (_chSel) _chSel.onchange = function () { waState.ch = this.value; fetchWaConvs(); };
    var _stSel = $('#waFilterBar .wa-stage-filter');   // v1.2.117: filter-lead-rating
    if (_stSel) _stSel.onchange = function () { waState.stage = this.value; fetchWaConvs(); };"""),
 ("""    if (waState.ch) query += '&ch=' + encodeURIComponent(waState.ch);   // v1.2.98: multi-nomor""",
  """    if (waState.ch) query += '&ch=' + encodeURIComponent(waState.ch);   // v1.2.98: multi-nomor
    if (waState.stage) query += '&stage=' + encodeURIComponent(waState.stage);   // v1.2.117: filter-lead-rating"""),
 ("""      if (waState.ch && !waState.channels.some(function (c) { return c.id === waState.ch; })) waState.ch = '';
      // Rebuild filter bar setelah tahu role user (hide Audit btn untuk non-admin)
      var oldBar = document.getElementById('waFilterBar');
      if (oldBar) oldBar.remove();
      var oldCards = document.getElementById('waFlagCards');   // v1.2.58
      if (oldCards) oldCards.remove();
      var oldAuditBox = document.getElementById('waAuditBox');
      if (oldAuditBox) oldAuditBox.remove();
      ensureFilterBar();""",
  """      if (waState.ch && !waState.channels.some(function (c) { return c.id === waState.ch; })) waState.ch = '';
      waState.stageCounts = res.stage_counts || null;   // v1.2.117: filter-lead-rating
      if (res.stage !== undefined) waState.stage = res.stage || '';
      // v1.2.117: jangan bangun ulang bar saat dropdown di dalamnya sedang dibuka (polling 6 dtk)
      var _ae117 = document.activeElement;
      var _selOpen117 = !!(_ae117 && _ae117.tagName === 'SELECT' && _ae117.closest && _ae117.closest('#waFilterBar'));
      if (!_selOpen117) {
      // Rebuild filter bar setelah tahu role user (hide Audit btn untuk non-admin)
      var oldBar = document.getElementById('waFilterBar');
      if (oldBar) oldBar.remove();
      var oldCards = document.getElementById('waFlagCards');   // v1.2.58
      if (oldCards) oldCards.remove();
      var oldAuditBox = document.getElementById('waAuditBox');
      if (oldAuditBox) oldAuditBox.remove();
      ensureFilterBar();
      }"""),
 ("""      $('#waConvList').innerHTML = '<div style="padding:16px;color:var(--muted)">' + msg + '</div>';""",
  """      if (waState.stage) msg = ((waState.filter && waState.filter !== 'all') ? msg : 'Tidak ada percakapan') + ' dengan Lead Rating "' + stageFltLabel(waState.stage) + '"';   // v1.2.117
      $('#waConvList').innerHTML = '<div style="padding:16px;color:var(--muted)">' + msg + '</div>';"""),
 # Web
 ("""    if (window.scrollTo) window.scrollTo(0, 0);
    fetchWebConvs();""",
  """    if (window.scrollTo) window.scrollTo(0, 0);
    webEnsureStageBar();   // v1.2.117: filter-lead-rating
    fetchWebConvs();"""),
 ("""  function fetchWebConvs(silent) {
    var list = $('#webConvList');
    if (!silent && list) list.innerHTML = '<div style="padding:16px;color:var(--muted)">Memuat…</div>';
    return api('web_conversations_admin')
      .then(function (res) {
        if (!res.ok) return;
        webState.convs = res.conversations || [];""",
  """  // v1.2.117: filter-lead-rating — chip Lead Rating di atas daftar Percakapan Web
  function webEnsureStageBar() {
    var panel = $('#panel-webchat');
    if (!panel) return;
    if (!$('#webStageBar')) {
      var card = panel.querySelector('.card');
      if (!card) return;
      var bar = document.createElement('div');
      bar.id = 'webStageBar';
      bar.className = 'wa-filter-bar';
      bar.style.cssText = 'border:1px solid var(--line);border-radius:12px;margin-bottom:12px';
      bar.innerHTML = '<span style="font-size:12px;color:var(--muted);font-weight:600">Lead Rating:</span>' +
        stageFltKeys(true).map(function (k) {
          return '<button type="button" class="wa-filter-btn" data-wstage="' + k + '">' + esc(k ? stageFltLabel(k) : 'Semua') +
            ' <span class="wa-filter-count" data-wcount="' + (k || 'all') + '">0</span></button>';
        }).join('');
      card.parentNode.insertBefore(bar, card);
      $$('#webStageBar .wa-filter-btn').forEach(function (b) {
        b.onclick = function () { webState.stage = b.dataset.wstage; webStageBarSync(); fetchWebConvs(); };
      });
    }
    webStageBarSync();
  }
  function webStageBarSync() {
    var c = webState.stageCounts || {};
    $$('#webStageBar .wa-filter-btn').forEach(function (b) { b.classList.toggle('active', b.dataset.wstage === (webState.stage || '')); });
    $$('#webStageBar .wa-filter-count').forEach(function (el) {
      var k = el.dataset.wcount, n = c[k] || 0;
      el.textContent = Number(n).toLocaleString('id-ID');
      el.style.display = (n > 0 || k === 'all') ? 'inline-block' : 'none';
    });
  }

  function fetchWebConvs(silent) {
    var list = $('#webConvList');
    if (!silent && list) list.innerHTML = '<div style="padding:16px;color:var(--muted)">Memuat…</div>';
    var q117 = '&per_page=50' + (webState.stage ? '&stage=' + encodeURIComponent(webState.stage) : '');   // v1.2.117
    return api('web_conversations_admin', { query: q117 })
      .then(function (res) {
        if (!res.ok) return;
        webState.convs = res.conversations || [];
        webState.stageCounts = res.stage_counts || null;   // v1.2.117
        if (res.stage !== undefined) webState.stage = res.stage || '';
        webEnsureStageBar();"""),
 ("""      list.innerHTML = '<div style="padding:24px;color:var(--muted);text-align:center">Belum ada percakapan web.</div>';""",
  """      list.innerHTML = '<div style="padding:24px;color:var(--muted);text-align:center">' +
        (webState.stage ? 'Tidak ada percakapan dengan Lead Rating "' + esc(stageFltLabel(webState.stage)) + '".' : 'Belum ada percakapan web.') + '</div>';   // v1.2.117"""),
 ("""        '<div style="margin-top:6px">' + badge + mig + '</div>' +""",
  """        '<div style="margin-top:6px">' + badge + mig + (c.lead_number ? ' ' + contactStageBadgeHtml(c.stage, c.vip, '') : '') + '</div>' +   // v1.2.117"""),
 ("""        if (head) {
          head.innerHTML =
            '<div style="display:flex;align-items:center;gap:10px;width:100%">' +
              '<div style="width:38px;height:38px;border-radius:50%;background:var(--brand-soft);display:flex;align-items:center;justify-content:center;flex-shrink:0;color:var(--brand)">' + ico('monitor-smartphone', 20) + '</div>' +""",
  """        var _ae117 = document.activeElement;   // v1.2.117: jangan gambar ulang saat dropdown Lead Rating dibuka
        if (head && !(silent && _ae117 && _ae117.id === 'webStageSelect')) {
          head.innerHTML =
            '<div style="display:flex;align-items:center;gap:10px;width:100%">' +
              '<div style="width:38px;height:38px;border-radius:50%;background:var(--brand-soft);display:flex;align-items:center;justify-content:center;flex-shrink:0;color:var(--brand)">' + ico('monitor-smartphone', 20) + '</div>' +"""),
 ("""                '<div style="font-size:12px;color:var(--muted)">Pengunjung web &middot; ' + count + ' pesan' + (conv.migrated ? ' &middot; arsip' : '') + '</div>' +
              '</div>' +
            '</div>';""",
  """                '<div style="font-size:12px;color:var(--muted)">Pengunjung web &middot; ' + count + ' pesan' + (conv.migrated ? ' &middot; arsip' : '') + '</div>' +
              '</div>' +
              (conv.lead_number   // v1.2.117: Lead Rating = kontak bernomor sama (sinkron dengan Kontak & Percakapan WA)
                ? '<div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px;flex-shrink:0"><span style="font-size:11px;color:var(--muted)">Lead Rating</span>' +
                  '<select id="webStageSelect" style="border-radius:6px;padding:2px 4px;font-size:11px;border:1px solid var(--line);width:118px">' + contactStageOptionsHtml(conv.stage || 'new') + '</select></div>'
                : '<span style="font-size:11px;color:var(--muted);flex-shrink:0;max-width:120px;text-align:right">Lead Rating butuh nomor HP pengunjung</span>') +
            '</div>';
          var _wss = $('#webStageSelect');
          if (_wss) _wss.onchange = function () {
            var st = this.value;
            saveContactStage(conv.lead_number, st, st === 'active_customer' ? !!conv.vip : false);
          };"""),
])

patch('dashboard/chatbot-ai/index.html', [
 ('app.js?v=1.2.116"></script><!-- v1.2.116: pindah-nomor -->',
  'app.js?v=1.2.117"></script><!-- v1.2.117: filter-lead-rating -->'),
 (""".wa-filter-bar {
  display: flex;""",
  """/* v1.2.117: filter-lead-rating */
.wa-stage-filter.is-active { border-color: var(--brand); background: var(--brand-soft); color: var(--brand); font-weight: 600; }
.wa-filter-bar {
  display: flex;"""),
])
