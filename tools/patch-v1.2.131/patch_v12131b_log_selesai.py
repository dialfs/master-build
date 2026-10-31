#!/usr/bin/env python3
r"""v1.2.131 (lanjutan) log-selesai: log khusus chat yang ditandai Selesai manual.
- data/wa-resolve-log.json (maks 5000 baris, terbaru di atas): waktu, nomor, nama, oleh, peran, pemegang chat,
  status sebelumnya (Belum dibalas/Aktif) + lama menunggu, status percakapan, nomor bisnis, pesan terakhir.
- Aksi API wa_resolve_log (Supervisor: hanya entri miliknya / chat timnya); ?format=csv&from=&to= untuk unduh.
- Tombol "Log Selesai" di bar filter Percakapan WA (Supervisor/Admin) + Unduh CSV.
Pakai: python3 patch_v12131b_log_selesai.py [~/Herd/dei-tenant] (idempoten; butuh patch_v12131_selesai_spv)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.131: log-selesai'
NEED = 'v1.2.131: selesai-spv'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def rep(s, old, new, rel):
    n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:100]); return s.replace(old, new)
def patch(rel, fn):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    assert NEED in s, rel + ': butuh ' + NEED
    s2 = fn(s, rel); assert TAG in s2, rel
    shutil.copy2(p, p + '.bak-v12131b-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s2); print('OK', rel)

def f_api(s, rel):
    s = rep(s, "function waAuditLog($action, $agent, $number, $extra = []) {",
        "// " + TAG + " — log khusus chat yang ditandai Selesai manual (permanen, maks 5000 baris)\n"
        "function waResolveLogFile() { return DATA_DIR . '/wa-resolve-log.json'; }\n"
        "function waResolveLog($row) {\n"
        "    try { deiWithLock('wa-resolve-log', function () use ($row) {\n"
        "        $all = readJson(waResolveLogFile(), []);\n"
        "        if (!is_array($all)) $all = [];\n"
        "        array_unshift($all, $row);\n"
        "        writeJson(waResolveLogFile(), array_slice($all, 0, 5000));\n"
        "    }); } catch (\\Throwable $e) { error_log('waResolveLog: ' . $e->getMessage()); }\n"
        "}\n"
        "function waAuditLog($action, $agent, $number, $extra = []) {", rel)
    s = rep(s, "        $owner = $cl ? (string)($cl['agent_username'] ?? '') : '';\n        $ok = convTrack($num, 'resolve', ['agent' => $u['username']]);",
        "        $owner = $cl ? (string)($cl['agent_username'] ?? '') : '';\n"
        "        $cPrev131 = convStoreGet($num);   // " + TAG + "\n"
        "        $convPrev131 = is_array($cPrev131) ? (string)($cPrev131['status'] ?? '') : '';\n"
        "        $ok = convTrack($num, 'resolve', ['agent' => $u['username']]);", rel)
    s = rep(s, "        waAuditLog('resolve', $u['username'], $num, ['from_agent' => $owner]);\n        jsonOut(['ok' => true, 'number' => $num, 'conv' => convPublic($c)]);",
        "        waAuditLog('resolve', $u['username'], $num, ['from_agent' => $owner]);\n"
        "        try {   // " + TAG + "\n"
        "            $ct131 = waContactGet($num) ?: [];\n"
        "            $chId131 = (string)($ct131['wa_ch'] ?? ''); $chL131 = '';\n"
        "            if ($chId131 !== '') foreach (waChannels(getSettings()) as $cx) { if (($cx['id'] ?? '') === $chId131) $chL131 = (string)($cx['label'] ?? ''); }\n"
        "            $pf131 = (string)($in['prev_flag'] ?? '');\n"
        "            waResolveLog([\n"
        "                'ts' => wibDate('Y-m-d H:i:s'), 'at' => time(),\n"
        "                'number' => $num, 'name' => waContactName($num, [$num => $ct131]),\n"
        "                'by' => (string)$u['username'], 'role' => (string)$u['role'], 'owner' => $owner,\n"
        "                'prev_flag' => in_array($pf131, ['unreplied', 'active', 'done'], true) ? $pf131 : '',\n"
        "                'waiting_sec' => max(0, (int)($in['waiting_sec'] ?? 0)),\n"
        "                'conv' => $convPrev131, 'ch' => $chL131,\n"
        "                'last_msg' => mb_substr(trim((string)($in['last_msg'] ?? '')), 0, 200),\n"
        "            ]);\n"
        "        } catch (\\Throwable $e) { error_log('wa_resolve log: ' . $e->getMessage()); }\n"
        "        jsonOut(['ok' => true, 'number' => $num, 'conv' => convPublic($c)]);", rel)
    s = rep(s, "    case 'wa_audit_log': {",
        "    case 'wa_resolve_log': {   // " + TAG + "\n"
        "        $u = requireAuth(['super_admin', 'admin', 'supervisor']);\n"
        "        $all = readJson(waResolveLogFile(), []);\n"
        "        if (!is_array($all)) $all = [];\n"
        "        $sc = deiSpvScope($u);\n"
        "        if ($sc !== null) $all = array_values(array_filter($all, function ($r) use ($sc, $u) {\n"
        "            $ow = (string)($r['owner'] ?? '');\n"
        "            return (string)($r['by'] ?? '') === (string)$u['username'] || ($ow !== '' && isset($sc[$ow]));\n"
        "        }));\n"
        "        $from = preg_match('/^\\d{4}-\\d{2}-\\d{2}$/', (string)($_GET['from'] ?? '')) ? (string)$_GET['from'] : '';\n"
        "        $to   = preg_match('/^\\d{4}-\\d{2}-\\d{2}$/', (string)($_GET['to'] ?? '')) ? (string)$_GET['to'] : '';\n"
        "        if ($from !== '' || $to !== '') $all = array_values(array_filter($all, function ($r) use ($from, $to) {\n"
        "            $d = substr((string)($r['ts'] ?? ''), 0, 10); return ($from === '' || $d >= $from) && ($to === '' || $d <= $to);\n"
        "        }));\n"
        "        if (($_GET['format'] ?? '') === 'csv') {\n"
        "            $FL = ['unreplied' => 'Belum dibalas', 'active' => 'Aktif', 'done' => 'Selesai'];\n"
        "            $fn = 'log-selesai-manual' . (($from !== '' || $to !== '') ? '_' . ($from ?: 'awal') . '_to_' . ($to ?: 'akhir') : '') . '.csv';\n"
        "            header('Content-Type: text/csv; charset=utf-8');\n"
        "            header('Content-Disposition: attachment; filename=\"' . $fn . '\"');\n"
        "            $out = fopen('php://output', 'w');\n"
        "            fwrite($out, \"\\xEF\\xBB\\xBF\");\n"
        "            fputcsv($out, ['Waktu', 'Nomor', 'Nama', 'Ditandai oleh', 'Peran', 'Pemegang chat', 'Status sebelumnya', 'Lama menunggu (jam)', 'Status percakapan', 'Nomor bisnis', 'Pesan terakhir']);\n"
        "            foreach ($all as $r) {\n"
        "                fputcsv($out, [$r['ts'] ?? '', '+' . ($r['number'] ?? ''), $r['name'] ?? '', $r['by'] ?? '', $r['role'] ?? '', $r['owner'] ?? '',\n"
        "                    $FL[$r['prev_flag'] ?? ''] ?? '', !empty($r['waiting_sec']) ? round($r['waiting_sec'] / 3600, 1) : '',\n"
        "                    $r['conv'] ?? '', $r['ch'] ?? '', $r['last_msg'] ?? '']);\n"
        "            }\n"
        "            fclose($out);\n"
        "            exit;\n"
        "        }\n"
        "        jsonOut(['ok' => true, 'entries' => array_slice($all, 0, 300), 'total' => count($all)]);\n"
        "        break;\n"
        "    }\n\n"
        "    case 'wa_audit_log': {", rel)
    return s

def f_js(s, rel):
    s = rep(s, "      (waState.isAdmin === false ? '' : '<button class=\"wa-filter-btn wa-audit-toggle\"",
        "      (waState.isAdmin ? '<button class=\"wa-filter-btn wa-reslog-toggle\" title=\"Log chat yang ditandai Selesai manual\">' + ico('check-circle-2',14) + '<span class=\"wa-lbl-t\"> Log Selesai</span></button>' : '') +   // " + TAG + "\n"
        "      (waState.isAdmin === false ? '' : '<button class=\"wa-filter-btn wa-audit-toggle\"", rel)
    s = rep(s, "    wrap.parentNode.insertBefore(auditBox, wrap);\n",
        "    wrap.parentNode.insertBefore(auditBox, wrap);\n"
        "    // " + TAG + ": kotak Log Selesai — dipakai ulang saat bar dibangun ulang (isi & status buka tetap)\n"
        "    var resLogBox = document.getElementById('waResLogBox');\n"
        "    if (!resLogBox) { resLogBox = document.createElement('div'); resLogBox.id = 'waResLogBox'; resLogBox.className = 'wa-audit-box wa-reslog-box'; resLogBox.style.display = 'none'; }\n"
        "    wrap.parentNode.insertBefore(resLogBox, wrap);\n", rel)
    s = rep(s, "      if (btn.classList.contains('wa-audit-toggle')) {\n        btn.onclick = toggleAuditLog;\n      }",
        "      if (btn.classList.contains('wa-audit-toggle')) {\n        btn.onclick = toggleAuditLog;\n"
        "      } else if (btn.classList.contains('wa-reslog-toggle')) {   // " + TAG + "\n        btn.onclick = toggleResLog;\n      }", rel)
    s = rep(s, "  function toggleAuditLog() {",
        "  // " + TAG + "\n"
        "  function toggleResLog() {\n"
        "    var box = $('#waResLogBox'); if (!box) return;\n"
        "    if (box.style.display === 'none') { box.style.display = 'block'; refreshResLog(); } else { box.style.display = 'none'; }\n"
        "  }\n"
        "  function refreshResLog() {\n"
        "    var box = $('#waResLogBox'); if (!box) return;\n"
        "    if (!box.innerHTML) box.innerHTML = '<div style=\"padding:8px 0;color:var(--muted);font-size:13px\">Memuat…</div>';\n"
        "    api('wa_resolve_log').then(function (res) {\n"
        "      if (!res || !res.ok) { box.innerHTML = '<div style=\"padding:8px 0;color:#b91c1c;font-size:13px\">' + esc((res && res.error) || 'Gagal memuat log selesai') + '</div>'; return; }\n"
        "      var FL = { unreplied: 'Belum dibalas', active: 'Aktif', done: 'Selesai' };\n"
        "      var h = '<div class=\"wa-audit-header\" style=\"display:flex;align-items:center;gap:8px;flex-wrap:wrap\"><strong>' + ico('check-circle-2',14) + ' Log Selesai Manual</strong>' +\n"
        "        ' <span style=\"color:var(--muted);font-size:12px\">(' + res.entries.length + ' dari ' + res.total + ')</span><span style=\"flex:1\"></span>' +\n"
        "        '<button type=\"button\" class=\"btn ghost\" id=\"waResLogCsv\" style=\"padding:4px 10px;font-size:12px\">' + ico('download',12) + ' Unduh CSV</button></div>';\n"
        "      if (!res.entries.length) h += '<div style=\"padding:6px 0;color:var(--muted);font-size:13px\">Belum ada chat yang ditandai selesai manual.</div>';\n"
        "      else {\n"
        "        h += '<div class=\"wa-audit-list\">';\n"
        "        res.entries.forEach(function (e) {\n"
        "          h += '<div class=\"wa-audit-row wa-reslog-row\">' +\n"
        "            '<span class=\"wa-audit-ts\">' + esc(e.ts) + '</span>' +\n"
        "            '<span class=\"wa-audit-agent\">' + esc(e.by) + '</span>' +\n"
        "            '<span class=\"wa-audit-num\">+' + esc(e.number) + (e.name ? ' · ' + esc(e.name) : '') + '</span>' +\n"
        "            '<span>' + esc(FL[e.prev_flag] || '-') + (e.waiting_sec ? ' · ' + waDurasi(e.waiting_sec) : '') + (e.owner ? ' · dipegang ' + esc(e.owner) : '') + (e.ch ? ' · ' + esc(e.ch) : '') + '</span>' +\n"
        "          '</div>';\n"
        "        });\n"
        "        h += '</div>';\n"
        "      }\n"
        "      box.innerHTML = h;\n"
        "      var b = $('#waResLogCsv');\n"
        "      if (b) b.onclick = function () { window.location.href = API + '?action=wa_resolve_log&format=csv&token=' + encodeURIComponent(token); };\n"
        "    });\n"
        "  }\n\n"
        "  function toggleAuditLog() {", rel)
    s = rep(s, "    api('wa_resolve', { method: 'POST', body: { number: num } }).then(function (res) {\n"
               "      if (res && res.ok) { toast('Percakapan ditandai selesai.'); fetchWaThread(num); fetchWaConvs(); }",
        "    var li = (waState.convs || []).filter(function (c) { return String(c.number) === String(num); })[0] || {};   // " + TAG + "\n"
        "    api('wa_resolve', { method: 'POST', body: { number: num, prev_flag: li.flag || '', waiting_sec: li.waiting_sec || 0, last_msg: li.last_q || '' } }).then(function (res) {\n"
        "      if (res && res.ok) { toast('Percakapan ditandai selesai.'); fetchWaThread(num); fetchWaConvs(); if ($('#waResLogBox') && $('#waResLogBox').style.display !== 'none') refreshResLog(); }", rel)
    return s

def f_html(s, rel):
    return rep(s, ".wa-audit-extra { cursor: help; opacity: 0.6; }\n",
        ".wa-audit-extra { cursor: help; opacity: 0.6; }\n"
        "/* " + TAG + " */\n"
        ".wa-reslog-box { background: #f0fdf4; }\n"
        ".wa-reslog-row { grid-template-columns: 130px 110px minmax(0,1.2fr) minmax(0,1.5fr); border-color: #dcfce7; }\n"
        ".wa-reslog-row span { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n"
        "@media (max-width: 640px) { .wa-reslog-row { grid-template-columns: 1fr 1fr; } }\n", rel)

patch('api/index.php', f_api)
patch('dashboard/chatbot-ai/app.js', f_js)
patch('dashboard/chatbot-ai/index.html', f_html)
