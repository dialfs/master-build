#!/usr/bin/env python3
"""v1.2.203 (sales-tag): tag Sales per chat WA, catat PO, jadikan lead Close Deal, laporan per Sales.
Paket Growth ke atas (pakai tpPlan()). Data: data/sales.json, data/sales-po.json, data/sales-events/YYYY-MM.jsonl,
kontak.sales = {id, at, by}, lead.sales + lead.closed_ts (dicap saat status jadi Close Deal/Lose).
Butuh v1.2.202. Idempoten.  Pakai: patch_v12203.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.203: sales-tag'; NEED = 'v1.2.202: id-noweb'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12203-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ============================== API ==============================
PHP_LIB = r'''/* ---- v1.2.203: sales-tag — tag Sales per chat, catatan PO, laporan per Sales (paket Growth+) ---- */
define('SALES_FILE', DATA_DIR . '/sales.json');
define('SALES_PO_FILE', DATA_DIR . '/sales-po.json');
define('SALES_EV_DIR', DATA_DIR . '/sales-events');
function slPlanOk() { return (bool)tpPlan()['ok']; }
function slLockedMsg() { return 'Tag Sales & Laporan per Sales tersedia mulai paket Growth. Hubungi ' . deiBrandVendor() . ' untuk upgrade paket.'; }
function slGuard() { if (!slPlanOk()) jsonOut(['ok' => false, 'locked' => true, 'error' => slLockedMsg()], 403); }
function slAll() {
    $d = readJson(SALES_FILE, []);
    return (is_array($d) && is_array($d['items'] ?? null)) ? array_values(array_filter($d['items'], 'is_array')) : [];
}
function slMap() { $m = []; foreach (slAll() as $x) $m[(string)($x['id'] ?? '')] = $x; return $m; }
function slNumSales($num) {
    $c = waContactGet($num);
    $s = is_array($c['sales'] ?? null) ? $c['sales'] : null;
    return ($s && (string)($s['id'] ?? '') !== '') ? $s : null;
}
function slEvent($ev, $sales, $num, $extra = []) {
    try {
        if (!is_dir(SALES_EV_DIR)) @mkdir(SALES_EV_DIR, 0755, true);
        $row = array_merge(['t' => time(), 'ev' => (string)$ev, 'sales' => (string)$sales, 'num' => waNormNum($num)], $extra);
        @file_put_contents(SALES_EV_DIR . '/' . wibDate('Y-m') . '.jsonl',
            json_encode($row, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n", FILE_APPEND | LOCK_EX);
    } catch (\Throwable $e) { error_log('slEvent: ' . $e->getMessage()); }
}
function slEventsRead($fromTs, $toTs) {
    $out = [];
    $y = (int)wibDate('Y', $fromTs); $mo = (int)wibDate('n', $fromTs);
    $endKey = wibDate('Y-m', $toTs);
    for ($i = 0; $i < 14; $i++) {
        $key = sprintf('%04d-%02d', $y, $mo);
        $mo++; if ($mo > 12) { $mo = 1; $y++; }
        $f = SALES_EV_DIR . '/' . $key . '.jsonl';
        if (is_file($f) && ($fh = @fopen($f, 'r'))) {
            while (($line = fgets($fh)) !== false) {
                $r = json_decode($line, true);
                if (!is_array($r)) continue;
                $t = (int)($r['t'] ?? 0);
                if ($t >= $fromTs && $t <= $toTs) $out[] = $r;
            }
            fclose($fh);
        }
        if ($key >= $endKey) break;
    }
    return $out;
}
function slPoAll() { $d = readJson(SALES_PO_FILE, []); return is_array($d) ? array_values(array_filter($d, 'is_array')) : []; }
function slPoFor($num) {
    $o = [];
    foreach (slPoAll() as $p) if ((string)($p['num'] ?? '') === (string)$num) $o[] = $p;
    usort($o, function ($a, $b) { return strcmp((string)($b['date'] ?? ''), (string)($a['date'] ?? '')) ?: ((int)($b['at'] ?? 0) <=> (int)($a['at'] ?? 0)); });
    return $o;
}
// Cap waktu Close Deal / Close Lose di kartu lead + sales yang memegang chat saat itu
function slLeadStamp(&$l, $prevSt, $st, $num) {
    if (!in_array($st, ['closed_deal', 'closed_lost'], true)) { unset($l['closed_ts']); return; }
    if ($prevSt === $st && !empty($l['closed_ts'])) return;
    $l['closed_ts'] = time();
    $s = slNumSales($num);
    if ($s) $l['sales'] = (string)$s['id'];
}
// Sales sebuah lead: yang sudah ditutup memakai sales saat ditutup; selain itu sales chat saat ini
function slLeadSalesId($l, $num, $contacts) {
    if (in_array((string)($l['status'] ?? ''), ['closed_deal', 'closed_lost'], true) && (string)($l['sales'] ?? '') !== '') return (string)$l['sales'];
    $c = $contacts[$num] ?? null;
    return is_array($c) && is_array($c['sales'] ?? null) ? (string)($c['sales']['id'] ?? '') : '';
}
function slLeadStatus($num) { $all = leadsGetAll(); return (isset($all[$num]) && is_array($all[$num])) ? (string)($all[$num]['status'] ?? 'baru') : ''; }
function slThreadInfo($num) {
    if (!slPlanOk()) return null;
    $map = slMap(); $cur = slNumSales($num);
    $list = [];
    foreach ($map as $id => $x) if (!empty($x['active'])) $list[] = ['id' => (string)$id, 'name' => (string)($x['name'] ?? '')];
    return [
        'list' => $list,
        'cur'  => $cur ? ['id' => (string)$cur['id'], 'name' => (string)($map[$cur['id']]['name'] ?? '(sales dihapus)'), 'at' => (int)($cur['at'] ?? 0), 'by' => (string)($cur['by'] ?? '')] : null,
        'po_n' => count(slPoFor($num)),
        'lead' => slLeadStatus($num),
    ];
}
'''

PHP_CASES = r'''    /* ---------- v1.2.203: sales-tag ---------- */
    case 'sales_list': {
        $u = requireAuth(['super_admin', 'admin', 'supervisor', 'wa_agent']);
        if (!slPlanOk()) jsonOut(['ok' => true, 'locked' => true, 'locked_msg' => slLockedMsg(), 'items' => []]);
        $mgr = in_array($u['role'], ['super_admin', 'admin', 'supervisor'], true);
        $items = [];
        foreach (slAll() as $x) {
            if (!$mgr && empty($x['active'])) continue;
            $items[] = ['id' => (string)$x['id'], 'name' => (string)($x['name'] ?? ''), 'phone' => (string)($x['phone'] ?? ''), 'active' => !empty($x['active'])];
        }
        jsonOut(['ok' => true, 'locked' => false, 'items' => $items, 'manage' => $mgr]);
        break;
    }
    case 'sales_save': {
        $u = requireAuth(['super_admin', 'admin', 'supervisor']);
        slGuard();
        $in = bodyInput();
        $name = mb_substr(trim(preg_replace('/\s+/u', ' ', (string)($in['name'] ?? ''))), 0, 60);
        if ($name === '') jsonOut(['ok' => false, 'error' => 'Nama sales wajib diisi.'], 400);
        $phone = waNormNum($in['phone'] ?? '');
        if (strpos($phone, '0') === 0) $phone = '62' . substr($phone, 1);
        $phone = substr($phone, 0, 20);
        $id = preg_replace('/[^a-z0-9_]/', '', (string)($in['id'] ?? ''));
        $act = array_key_exists('active', $in) ? !empty($in['active']) : null;
        $by = (string)$u['username'];
        $res = deiWithLock('sales', function () use ($id, $name, $phone, $act, $by) {
            $items = slAll();
            foreach ($items as $x) if (mb_strtolower((string)($x['name'] ?? '')) === mb_strtolower($name) && (string)$x['id'] !== $id) return ['e' => 'Nama sales sudah ada.'];
            $found = false;
            foreach ($items as &$x) {
                if ($id === '' || (string)$x['id'] !== $id) continue;
                $x['name'] = $name; $x['phone'] = $phone;
                if ($act !== null) $x['active'] = $act;
                $x['updated_at'] = wibDate('Y-m-d H:i:s'); $x['updated_by'] = $by;
                $found = true;
            }
            unset($x);
            if (!$found) {
                if ($id !== '') return ['e' => 'Sales tidak ditemukan.'];
                if (count($items) >= 200) return ['e' => 'Maksimal 200 sales.'];
                $id = 'sl_' . substr(md5(uniqid('', true)), 0, 8);
                $items[] = ['id' => $id, 'name' => $name, 'phone' => $phone, 'active' => true, 'created_at' => wibDate('Y-m-d H:i:s'), 'by' => $by];
            }
            writeJson(SALES_FILE, ['items' => $items]);
            return ['id' => $id];
        });
        if (isset($res['e'])) jsonOut(['ok' => false, 'error' => $res['e']], 400);
        jsonOut(['ok' => true, 'id' => $res['id']]);
        break;
    }
    case 'sales_delete': {
        requireAuth(['super_admin', 'admin', 'supervisor']);
        slGuard();
        $id = preg_replace('/[^a-z0-9_]/', '', (string)(bodyInput()['id'] ?? ''));
        if ($id === '') jsonOut(['ok' => false, 'error' => 'id wajib'], 400);
        deiWithLock('sales', function () use ($id) {
            writeJson(SALES_FILE, ['items' => array_values(array_filter(slAll(), function ($x) use ($id) { return (string)$x['id'] !== $id; }))]);
        });
        jsonOut(['ok' => true]);
        break;
    }
    case 'sales_tag': {
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        slGuard();
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        deiGuardAgentPrivate($u, $num);
        $sid = preg_replace('/[^a-z0-9_]/', '', (string)($in['sales'] ?? ''));
        $map = slMap();
        if ($sid !== '' && (!isset($map[$sid]) || empty($map[$sid]['active']))) jsonOut(['ok' => false, 'error' => 'Sales tidak ditemukan atau nonaktif.'], 404);
        $prev = slNumSales($num); $prevId = $prev ? (string)$prev['id'] : '';
        if ($prevId === $sid) jsonOut(['ok' => true, 'sales' => slThreadInfo($num)]);
        $by = (string)$u['username'];
        waContactUpdate($num, function (&$c) use ($sid, $by) {
            if ($sid === '') unset($c['sales']);
            else $c['sales'] = ['id' => $sid, 'at' => time(), 'by' => $by];
        });
        slEvent($sid === '' ? 'untag' : 'tag', $sid !== '' ? $sid : $prevId, $num, ['by' => $by, 'prev' => $prevId]);
        try { waAuditLog('sales_tag', $by, $num, ['from' => $prevId, 'to' => $sid]); } catch (\Throwable $e) {}
        jsonOut(['ok' => true, 'sales' => slThreadInfo($num)]);
        break;
    }
    case 'sales_po_list': {
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        slGuard();
        $num = waNormNum($_GET['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        deiGuardAgentPrivate($u, $num);
        $map = slMap();
        $items = array_map(function ($p) use ($map) {
            $sid = (string)($p['sales'] ?? '');
            return ['id' => (string)$p['id'], 'date' => (string)($p['date'] ?? ''), 'no' => (string)($p['no'] ?? ''), 'note' => (string)($p['note'] ?? ''),
                    'sales' => $sid, 'sales_name' => (string)($map[$sid]['name'] ?? '(sales dihapus)'), 'by' => (string)($p['by'] ?? '')];
        }, slPoFor($num));
        jsonOut(['ok' => true, 'items' => $items, 'info' => slThreadInfo($num), 'can_delete' => in_array($u['role'], ['super_admin', 'admin', 'supervisor'], true)]);
        break;
    }
    case 'sales_po_add': {
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        slGuard();
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        deiGuardAgentPrivate($u, $num);
        $cur = slNumSales($num);
        if (!$cur) jsonOut(['ok' => false, 'error' => 'Pilih Sales untuk chat ini dulu.'], 400);
        $date = (string)($in['date'] ?? '');
        if (wibDayStart($date) === null) $date = wibToday();
        $po = ['id' => 'po_' . substr(md5(uniqid('', true)), 0, 10), 'num' => $num, 'sales' => (string)$cur['id'], 'date' => $date,
               'no' => mb_substr(trim((string)($in['no'] ?? '')), 0, 60), 'note' => mb_substr(trim((string)($in['note'] ?? '')), 0, 300),
               'by' => (string)$u['username'], 'at' => time()];
        deiWithLock('sales-po', function () use ($po) { $all = slPoAll(); $all[] = $po; writeJson(SALES_PO_FILE, $all); });
        slEvent('po', $po['sales'], $num, ['by' => $po['by'], 'po' => $po['id']]);
        try { waAuditLog('sales_po', $po['by'], $num, ['po' => $po['id'], 'sales' => $po['sales'], 'no' => $po['no']]); } catch (\Throwable $e) {}
        jsonOut(['ok' => true, 'po' => $po, 'sales' => slThreadInfo($num)]);
        break;
    }
    case 'sales_po_del': {
        $u = requireAuth(['super_admin', 'admin', 'supervisor']);
        slGuard();
        $id = preg_replace('/[^a-z0-9_]/', '', (string)(bodyInput()['id'] ?? ''));
        if ($id === '') jsonOut(['ok' => false, 'error' => 'id wajib'], 400);
        $gone = deiWithLock('sales-po', function () use ($id) {
            $keep = []; $g = null;
            foreach (slPoAll() as $p) { if ((string)($p['id'] ?? '') === $id) $g = $p; else $keep[] = $p; }
            if ($g) writeJson(SALES_PO_FILE, $keep);
            return $g;
        });
        if (!$gone) jsonOut(['ok' => false, 'error' => 'PO tidak ditemukan.'], 404);
        slEvent('po_del', (string)($gone['sales'] ?? ''), (string)($gone['num'] ?? ''), ['by' => (string)$u['username'], 'po' => $id]);
        try { waAuditLog('sales_po_del', $u['username'], (string)($gone['num'] ?? ''), ['po' => $id]); } catch (\Throwable $e) {}
        jsonOut(['ok' => true]);
        break;
    }
    case 'sales_deal': {
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        slGuard();
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        deiGuardAgentPrivate($u, $num);
        $cur = slNumSales($num);
        if (!$cur) jsonOut(['ok' => false, 'error' => 'Pilih Sales untuk chat ini dulu.'], 400);
        $all = leadsGetAll();
        $now = date('Y-m-d H:i:s');
        if (!isset($all[$num]) || !is_array($all[$num])) {
            $all[$num] = ['number' => $num, 'name' => waContactName($num), 'status' => 'baru', 'note' => '', 'extracted' => [],
                          'analyzed_at' => '', 'created_at' => $now, 'updated_at' => $now, 'src' => 'po'];
        }
        $prevSt = (string)($all[$num]['status'] ?? 'baru');
        $all[$num]['status'] = 'closed_deal';
        slLeadStamp($all[$num], $prevSt, 'closed_deal', $num);
        $all[$num]['updated_at'] = $now;
        writeJson(LEADS_FILE, $all);
        slEvent('deal', (string)$cur['id'], $num, ['by' => (string)$u['username']]);
        try { waAuditLog('sales_deal', $u['username'], $num, ['sales' => (string)$cur['id']]); } catch (\Throwable $e) {}
        jsonOut(['ok' => true, 'sales' => slThreadInfo($num)]);
        break;
    }
    case 'sales_report': {
        requireAuth(['super_admin', 'admin', 'supervisor']);
        slGuard();
        $fromD = (string)($_GET['from'] ?? wibDate('Y-m-01'));
        $toD   = (string)($_GET['to'] ?? wibToday());
        $fromTs = wibDayStart($fromD); $toTs = wibDayStart($toD);
        if ($fromTs === null || $toTs === null || $toTs < $fromTs) jsonOut(['ok' => false, 'error' => 'Rentang tanggal tidak valid (YYYY-MM-DD).'], 400);
        if ($toTs - $fromTs > 370 * 86400) jsonOut(['ok' => false, 'error' => 'Rentang maksimal 1 tahun.'], 400);
        $toTs += 86399;
        $map = slMap();
        $mk = function ($id) use ($map) {
            return ['id' => $id, 'name' => $id === '' ? 'Tanpa sales' : (string)($map[$id]['name'] ?? '(sales dihapus)'),
                    'active' => $id !== '' && !empty($map[$id]['active']), 'chats' => 0, 'po' => 0, 'deal' => 0, 'lost' => 0, '_n' => []];
        };
        $rows = [];
        foreach ($map as $id => $x) if (!empty($x['active'])) $rows[(string)$id] = $mk((string)$id);
        foreach (slEventsRead($fromTs, $toTs) as $ev) {
            if (($ev['ev'] ?? '') !== 'tag') continue;
            $id = (string)($ev['sales'] ?? ''); $n = (string)($ev['num'] ?? '');
            if ($id === '' || $n === '') continue;
            if (!isset($rows[$id])) $rows[$id] = $mk($id);
            $rows[$id]['_n'][$n]['tag'] = 1;
        }
        foreach (slPoAll() as $p) {
            $t = wibDayStart((string)($p['date'] ?? ''));
            if ($t === null || $t < $fromTs || $t > $toTs) continue;
            $id = (string)($p['sales'] ?? ''); $n = (string)($p['num'] ?? '');
            if (!isset($rows[$id])) $rows[$id] = $mk($id);
            $rows[$id]['po']++;
            $rows[$id]['_n'][$n]['po'] = ($rows[$id]['_n'][$n]['po'] ?? 0) + 1;
        }
        foreach (leadsGetAll() as $n => $l) {
            if (!is_array($l)) continue;
            $st = (string)($l['status'] ?? '');
            if ($st !== 'closed_deal' && $st !== 'closed_lost') continue;
            $t = (int)($l['closed_ts'] ?? 0);
            if ($t < $fromTs || $t > $toTs) continue;
            $id = (string)($l['sales'] ?? '');
            if (!isset($rows[$id])) $rows[$id] = $mk($id);
            $rows[$id][$st === 'closed_deal' ? 'deal' : 'lost']++;
            $rows[$id]['_n'][(string)$n]['st'] = $st;
        }
        $contacts = waGetContacts();
        $out = []; $tot = ['chats' => 0, 'po' => 0, 'deal' => 0, 'lost' => 0];
        foreach ($rows as $R) {
            $items = []; $chats = 0;
            foreach ($R['_n'] as $n => $x) {
                if (!empty($x['tag'])) $chats++;
                $items[] = ['number' => (string)$n, 'name' => waContactName((string)$n, $contacts), 'tagged' => !empty($x['tag']),
                            'po' => (int)($x['po'] ?? 0), 'status' => (string)($x['st'] ?? '')];
            }
            usort($items, function ($a, $b) { return ($b['status'] === 'closed_deal') <=> ($a['status'] === 'closed_deal') ?: $b['po'] <=> $a['po'] ?: strcmp($a['number'], $b['number']); });
            $R['chats'] = $chats;
            $R['conv'] = $chats > 0 ? round($R['deal'] / $chats * 100, 1) : null;
            $R['items'] = array_slice($items, 0, 300);
            $R['items_total'] = count($items);
            unset($R['_n']);
            foreach ($tot as $k => $_) $tot[$k] += $R[$k];
            $out[] = $R;
        }
        usort($out, function ($a, $b) { return $b['deal'] <=> $a['deal'] ?: $b['po'] <=> $a['po'] ?: $b['chats'] <=> $a['chats'] ?: strcmp($a['name'], $b['name']); });
        $tot['conv'] = $tot['chats'] > 0 ? round($tot['deal'] / $tot['chats'] * 100, 1) : null;
        jsonOut(['ok' => true, 'from' => $fromD, 'to' => $toD, 'rows' => $out, 'totals' => $tot]);
        break;
    }

'''

s = rd(API)
if TAG not in s:
    assert NEED in s, 'butuh v1.2.202 dulu'
    s = rep(s, "define('DEI_VERSION', 'v1.2.202');   // v1.2.202:",
            "define('DEI_VERSION', 'v1.2.203');   // " + TAG + " — tag Sales per chat, catat PO, Close Deal & laporan per Sales (Growth+); v1.2.202:", what='DEI_VERSION')
    s = rep(s, "function agentEvent($ev, $agent, $num, $extra = []) {", PHP_LIB + "function agentEvent($ev, $agent, $num, $extra = []) {", what='lib')
    s = rep(s, "    case 'agent_report': {", PHP_CASES + "    case 'agent_report': {", what='cases')
    # save_lead: cap waktu Close Deal/Lose + sales
    s = rep(s, "            if (!leadStatusValid($st)) jsonOut(['ok' => false, 'error' => 'Status tidak dikenal.'], 400);\n            $all[$num]['status'] = $st;",
            "            if (!leadStatusValid($st)) jsonOut(['ok' => false, 'error' => 'Status tidak dikenal.'], 400);\n"
            "            $slPrev203 = (string)($all[$num]['status'] ?? 'baru');   // " + TAG + "\n"
            "            $all[$num]['status'] = $st;\n"
            "            slLeadStamp($all[$num], $slPrev203, $st, $num);", what='save_lead')
    # analisa ulang lead tidak menghapus sales / closed_ts
    s = rep(s, "        'updated_at'  => $now,\n    ];\n    writeJson(LEADS_FILE, $all);\n    return true;",
            "        'updated_at'  => $now,\n    ];\n"
            "    foreach (['sales', 'closed_ts', 'src'] as $slK203) if (isset($lama[$slK203])) $all[$number][$slK203] = $lama[$slK203];   // " + TAG + "\n"
            "    writeJson(LEADS_FILE, $all);\n    return true;", what='leadAnalyze')
    # get_leads: sales per lead
    s = rep(s, "        $contacts = waGetContacts();\n        $out = [];\n        foreach ($all as $num => $l) {",
            "        $contacts = waGetContacts();\n        $slMap203 = slPlanOk() ? slMap() : null;   // " + TAG + "\n        $out = [];\n        foreach ($all as $num => $l) {", what='get_leads map')
    s = rep(s, "                'contact_vip'   => waContactVip($num, $contacts),     // v1.2.39\n            ];",
            "                'contact_vip'   => waContactVip($num, $contacts),     // v1.2.39\n"
            "                'sales_id'      => $slId203 = ($slMap203 === null ? '' : slLeadSalesId($l, $num, $contacts)),   // " + TAG + "\n"
            "                'sales_name'    => $slId203 !== '' ? (string)($slMap203[$slId203]['name'] ?? '(sales dihapus)') : '',\n            ];", what='get_leads item')
    # wa_thread: info sales
    s = rep(s, "            'tp' => tpActive() ? tpPublic(waContactGet($num) ?: []) : null,   // v1.2.138: filter-topik\n",
            "            'tp' => tpActive() ? tpPublic(waContactGet($num) ?: []) : null,   // v1.2.138: filter-topik\n"
            "            'sales' => (function () use ($num) { try { return wgPublic($num) ? null : slThreadInfo($num); } catch (\\Throwable $e) { return null; } })(),   // " + TAG + "\n", what='wa_thread')
    save(API, s)
else: print('sudah', API)

# ============================== JS ==============================
JS_LIB = r'''  /* ---- v1.2.203: sales-tag — tag Sales per chat, PO, Close Deal, laporan per Sales ---- */
  function slYmd203(d) { var p = function (n) { return String(n).padStart(2, '0'); }; d = d || new Date(); return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()); }
  function slThreadTools203(res) {
    var S = res && res.sales; if (!S || res.group) return '';
    var cur = S.cur ? S.cur.id : '', list = S.list || [];
    var opts = '<option value="">' + (list.length ? 'Sales: —' : 'Sales: belum ada (atur di Tim & Agent)') + '</option>' + list.map(function (o) {
      return '<option value="' + esc(o.id) + '"' + (o.id === cur ? ' selected' : '') + '>Sales: ' + esc(o.name) + '</option>';
    }).join('');
    if (S.cur && !list.some(function (o) { return o.id === cur; })) opts += '<option value="' + esc(cur) + '" selected>Sales: ' + esc(S.cur.name) + ' (nonaktif)</option>';
    return '<span class="wa-assign" title="Sales yang menangani chat ini' + (S.cur && S.cur.by ? ' (dipilih ' + esc(S.cur.by) + ')' : '') + '">' + ico('briefcase-business', 13) + '<select id="slTagSel">' + opts + '</select></span>' +
      ' <a href="#" id="slPoBtn" style="font-size:12px" title="Catat PO & jadikan lead Close Deal">' + ico('file-text', 13) + ' PO' + (S.po_n ? ' (' + S.po_n + ')' : '') + (S.lead === 'closed_deal' ? ' · Close Deal' : '') + '</a>';
  }
  function slBindThread203(num, res) {
    var sel = $('#slTagSel');
    if (sel) sel.onchange = function () {
      var v = this.value; sel.disabled = true;
      api('sales_tag', { method: 'POST', body: { number: num, sales: v } }).then(function (r) {
        sel.disabled = false;
        if (r && r.ok) toast(v ? 'Sales dipilih.' : 'Tag sales dihapus.');
        else toast((r && r.error) || 'Gagal menyimpan sales.', true);
        if (String(waState.current) === String(num)) fetchWaThread(num, true);
      });
    };
    var b = $('#slPoBtn');
    if (b) b.onclick = function (ev) { ev.preventDefault(); slPoModal203(num); };
  }
  function slPoModal203(num) {
    var old = $('#slPoModal'); if (old) old.remove();
    var m = document.createElement('div'); m.id = 'slPoModal'; m.className = 'tf-modal';
    m.innerHTML = '<div class="tf-modal-box"><div style="color:var(--muted)">Memuat…</div></div>';
    document.body.appendChild(m);
    var box = m.querySelector('.tf-modal-box');
    var close = function () { m.remove(); };
    m.onclick = function (e) { if (e.target === m) close(); };
    var refresh = function () { if (String(waState.current) === String(num)) fetchWaThread(num, true); };
    var draw = function () {
      api('sales_po_list', { query: '&number=' + encodeURIComponent(num) }).then(function (r) {
        if (!document.body.contains(m)) return;
        if (!r || !r.ok) { box.innerHTML = '<div style="color:#b91c1c">' + esc((r && r.error) || 'Gagal memuat.') + '</div>'; return; }
        var info = r.info || {}, cur = info.cur, items = r.items || [], leadSt = info.lead || '', ls = LEAD_STATUS[leadSt];
        var rows = items.length ? items.map(function (p) {
          return '<tr><td style="white-space:nowrap">' + esc(p.date) + '</td><td>' + esc(p.no || '—') + (p.note ? '<div style="color:var(--muted);font-size:12px">' + esc(p.note) + '</div>' : '') + '</td>' +
            '<td>' + esc(p.sales_name) + '</td><td style="color:var(--muted);font-size:12px">' + esc(p.by) + '</td>' +
            (r.can_delete ? '<td><button type="button" class="btn ghost sm" data-podel="' + esc(p.id) + '" title="Hapus PO">' + ico('trash-2', 13) + '</button></td>' : '') + '</tr>';
        }).join('') : '<tr><td colspan="5" style="color:var(--muted)">Belum ada PO untuk chat ini.</td></tr>';
        box.innerHTML =
          '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><b>PO &amp; Close Deal</b><button type="button" class="btn ghost sm" id="slPoClose">' + ico('x', 14) + '</button></div>' +
          '<p style="font-size:13px;margin:6px 0 10px">Sales: ' + (cur ? '<b>' + esc(cur.name) + '</b>' : '<span style="color:#b91c1c">belum dipilih — pilih Sales di kepala chat dulu</span>') +
            ' · Lead: ' + (ls ? '<span class="tag" style="background:' + ls.bg + ';color:' + ls.fg + '">' + esc(ls.label) + '</span>' : '<span style="color:var(--muted)">belum ada</span>') + '</p>' +
          (cur ? '<div class="grid2"><div class="row"><label class="fl">Tanggal PO</label><input type="date" id="slPoDate" value="' + slYmd203() + '"></div>' +
              '<div class="row"><label class="fl">No. PO (opsional)</label><input type="text" id="slPoNo" maxlength="60"></div></div>' +
            '<div class="row"><label class="fl">Catatan (opsional)</label><input type="text" id="slPoNote" maxlength="300" placeholder="mis. 2 unit, DP masuk"></div>' +
            '<div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end">' +
              (leadSt === 'closed_deal' ? '<span class="tag" style="background:#d1fae5;color:#065f46;align-self:center">' + ico('check-circle-2', 12) + ' Lead sudah Close Deal</span>'
                : '<button type="button" class="btn ghost sm" id="slPoDeal">' + ico('check-circle-2', 14) + ' Jadikan Lead Close Deal</button>') +
              '<button type="button" class="btn sm" id="slPoAdd">' + ico('save', 14) + ' Simpan PO</button></div>' : '') +
          '<div class="scroll" style="margin-top:12px;max-height:40vh"><table class="tbl"><thead><tr><th>Tanggal</th><th>No. PO</th><th>Sales</th><th>Oleh</th>' + (r.can_delete ? '<th></th>' : '') + '</tr></thead><tbody>' + rows + '</tbody></table></div>';
        $('#slPoClose').onclick = close;
        if ($('#slPoAdd')) $('#slPoAdd').onclick = function () {
          var btn = this; btn.disabled = true;
          api('sales_po_add', { method: 'POST', body: { number: num, date: $('#slPoDate').value, no: $('#slPoNo').value, note: $('#slPoNote').value } }).then(function (x) {
            btn.disabled = false;
            if (x && x.ok) { toast('PO tersimpan.'); draw(); refresh(); } else toast((x && x.error) || 'Gagal menyimpan PO.', true);
          });
        };
        if ($('#slPoDeal')) $('#slPoDeal').onclick = function () {
          if (!confirm('Jadikan lead chat ini Close Deal atas nama sales ' + cur.name + '?')) return;
          var btn = this; btn.disabled = true;
          api('sales_deal', { method: 'POST', body: { number: num } }).then(function (x) {
            btn.disabled = false;
            if (x && x.ok) { toast('Lead ditandai Close Deal.'); draw(); refresh(); fetchWaConvs(); } else toast((x && x.error) || 'Gagal.', true);
          });
        };
        $$('#slPoModal [data-podel]').forEach(function (d) {
          d.onclick = function () {
            if (!confirm('Hapus PO ini?')) return;
            api('sales_po_del', { method: 'POST', body: { id: d.dataset.podel } }).then(function (x) {
              if (x && x.ok) { toast('PO dihapus.'); draw(); refresh(); } else toast((x && x.error) || 'Gagal menghapus.', true);
            });
          };
        });
      });
    };
    draw();
  }
  // Tim & Agent: daftar Sales + laporan per Sales (Supervisor ke atas)
  function slTimLoad203() {
    if (!$('#slCard') || role === 'wa_agent') return;
    if (!$('#slrFrom').value) { var d = new Date(); $('#slrFrom').value = slYmd203(new Date(d.getFullYear(), d.getMonth(), 1)); $('#slrTo').value = slYmd203(d); }
    $('#btnSlrLoad').onclick = slReport203;
    $('#btnSlrCsv').onclick = slReportCsv203;
    $('#btnSlAdd').onclick = function () { slSave203({ name: $('#slName').value, phone: $('#slPhone').value }, function () { $('#slName').value = ''; $('#slPhone').value = ''; }); };
    slList203(true);
  }
  function slSave203(body, ok) {
    api('sales_save', { method: 'POST', body: body }).then(function (r) {
      if (r && r.ok) { toast('Sales tersimpan.'); if (ok) ok(); slList203(false); }
      else toast((r && r.error) || 'Gagal menyimpan sales.', true);
    });
  }
  function slList203(withReport) {
    api('sales_list').then(function (r) {
      var lk = !!(r && r.locked);
      $('#slLocked').style.display = lk ? '' : 'none';
      $('#slLocked').innerHTML = lk ? ico('octagon-alert', 13) + ' ' + esc(r.locked_msg || '') : '';
      $('#slBody').style.display = lk ? 'none' : '';
      $('#slrCard').style.display = lk ? 'none' : '';
      if (!r || !r.ok || lk) return;
      var it = r.items || [];
      $('#tblSl').innerHTML = it.length ? it.map(function (s) {
        return '<tr data-sl="' + esc(s.id) + '"><td><input type="text" class="sl-nm" value="' + esc(s.name) + '" maxlength="60" style="min-width:140px"></td>' +
          '<td><input type="text" class="sl-ph" value="' + esc(s.phone) + '" maxlength="20" placeholder="opsional" style="min-width:110px"></td>' +
          '<td><label class="switch" title="Sales nonaktif tidak muncul di pilihan chat"><input type="checkbox" class="sl-on"' + (s.active ? ' checked' : '') + '><span class="sl"></span></label></td>' +
          '<td style="white-space:nowrap"><button type="button" class="btn ghost sm sl-save" title="Simpan">' + ico('save', 13) + '</button> <button type="button" class="btn ghost sm sl-del" title="Hapus">' + ico('trash-2', 13) + '</button></td></tr>';
      }).join('') : '<tr><td colspan="4" style="color:var(--muted)">Belum ada sales. Tambahkan di bawah.</td></tr>';
      $$('#tblSl tr[data-sl]').forEach(function (tr) {
        var id = tr.dataset.sl;
        var sv = function () { slSave203({ id: id, name: tr.querySelector('.sl-nm').value, phone: tr.querySelector('.sl-ph').value, active: tr.querySelector('.sl-on').checked }); };
        tr.querySelector('.sl-save').onclick = sv;
        tr.querySelector('.sl-on').onchange = sv;
        tr.querySelector('.sl-del').onclick = function () {
          if (!confirm('Hapus sales ini?\n\nChat & PO yang sudah ditandai tetap tercatat dengan nama "(sales dihapus)". Untuk berhenti memakai sales, cukup matikan Aktif.')) return;
          api('sales_delete', { method: 'POST', body: { id: id } }).then(function (x) { if (x && x.ok) { toast('Sales dihapus.'); slList203(false); } else toast((x && x.error) || 'Gagal.', true); });
        };
      });
      if (withReport) slReport203();
    });
  }
  var slRep203 = null;
  function slReport203() {
    var q = '&from=' + encodeURIComponent($('#slrFrom').value) + '&to=' + encodeURIComponent($('#slrTo').value);
    $('#tblSlr').innerHTML = '<tr><td colspan="6" style="color:var(--muted)">Memuat…</td></tr>';
    api('sales_report', { query: q }).then(function (r) {
      if (!r || !r.ok) { slRep203 = null; $('#slrKpis').innerHTML = ''; $('#tblSlr').innerHTML = '<tr><td colspan="6" style="color:#b91c1c">' + esc((r && r.error) || 'Gagal memuat.') + '</td></tr>'; return; }
      slRep203 = r;
      var t = r.totals || {}, kpi = function (n, l) { return '<div class="tim-kpi"><div class="n">' + n + '</div><div class="l">' + l + '</div></div>'; };
      $('#slrKpis').innerHTML = kpi(t.chats || 0, 'Chat di-tag') + kpi(t.po || 0, 'PO') + kpi(t.deal || 0, 'Close Deal') + kpi(t.conv == null ? '–' : t.conv + '%', 'Konversi (Close Deal ÷ Chat)');
      var rows = r.rows || [];
      if (!rows.length) { $('#tblSlr').innerHTML = '<tr><td colspan="6" style="color:var(--muted)">Belum ada sales / aktivitas di rentang ini.</td></tr>'; return; }
      $('#tblSlr').innerHTML = rows.map(function (s, i) {
        return '<tr class="slr-row" data-i="' + i + '" style="cursor:pointer" title="Klik untuk rincian"><td>' + ico('chevron-down', 13) + ' ' + esc(s.name) + (s.id && !s.active ? ' <span class="tag">nonaktif</span>' : '') + '</td>' +
          '<td style="text-align:right">' + s.chats + '</td><td style="text-align:right">' + s.po + '</td>' +
          '<td style="text-align:right;font-weight:600">' + s.deal + '</td><td style="text-align:right">' + s.lost + '</td>' +
          '<td style="text-align:right">' + (s.conv == null ? '–' : s.conv + '%') + '</td></tr>' +
          '<tr class="slr-det" data-i="' + i + '" style="display:none"><td colspan="6" style="background:var(--brand-soft)">' + slDetail203(s) + '</td></tr>';
      }).join('');
      $$('#tblSlr .slr-row').forEach(function (tr) {
        tr.onclick = function () { var d = $('#tblSlr .slr-det[data-i="' + tr.dataset.i + '"]'); if (d) d.style.display = d.style.display === 'none' ? '' : 'none'; };
      });
      $$('#tblSlr [data-slnum]').forEach(function (a) { a.onclick = function (ev) { ev.preventDefault(); openLeadConv(a.dataset.slnum); }; });
    });
  }
  function slDetail203(s) {
    var it = s.items || [];
    if (!it.length) return '<span style="color:var(--muted);font-size:12px">Tidak ada chat di rentang ini.</span>';
    return '<table class="tbl" style="font-size:12px"><thead><tr><th>Kontak</th><th>Di-tag</th><th style="text-align:right">PO</th><th>Status lead</th></tr></thead><tbody>' +
      it.map(function (x) {
        var ls = LEAD_STATUS[x.status];
        return '<tr><td><a href="#" data-slnum="' + esc(x.number) + '">' + esc(x.name || ('+' + x.number)) + '</a>' + (x.name ? ' <span style="color:var(--muted)">+' + esc(x.number) + '</span>' : '') + '</td>' +
          '<td>' + (x.tagged ? ico('check-circle-2', 12) : '<span style="color:var(--muted)">—</span>') + '</td><td style="text-align:right">' + (x.po || '—') + '</td>' +
          '<td>' + (ls ? '<span class="tag" style="background:' + ls.bg + ';color:' + ls.fg + '">' + esc(ls.label) + '</span>' : '<span style="color:var(--muted)">—</span>') + '</td></tr>';
      }).join('') + '</tbody></table>' +
      (s.items_total > it.length ? '<div class="help">Menampilkan ' + it.length + ' dari ' + s.items_total + ' chat.</div>' : '');
  }
  function slReportCsv203() {
    var r = slRep203; if (!r) { toast('Tampilkan laporan dulu.', true); return; }
    var q = function (v) { v = String(v == null ? '' : v); return /[",\n;]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var L = [['Sales', 'Chat di-tag', 'PO', 'Close Deal', 'Close Lose', 'Konversi %'].join(',')];
    (r.rows || []).forEach(function (s) { L.push([s.name, s.chats, s.po, s.deal, s.lost, s.conv == null ? '' : s.conv].map(q).join(',')); });
    L.push(''); L.push(['Sales', 'Nomor', 'Nama kontak', 'Di-tag', 'PO', 'Status lead'].join(','));
    (r.rows || []).forEach(function (s) { (s.items || []).forEach(function (x) { L.push([s.name, "'" + x.number, x.name, x.tagged ? 'ya' : '', x.po, (LEAD_STATUS[x.status] || {}).label || ''].map(q).join(',')); }); });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob(['﻿' + L.join('\n')], { type: 'text/csv;charset=utf-8' }));
    a.download = 'laporan-sales-' + r.from + '_' + r.to + '.csv';
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }
  // Leads: badge + filter per Sales
  var leadAll203 = [], leadSales203 = '';
  function slLeadFilt203(a) {
    if (!leadSales203) return a;
    var want = leadSales203 === '_none' ? '' : leadSales203;
    return a.filter(function (l) { return (l.sales_id || '') === want; });
  }
  function slLeadBadge203(l) { return l.sales_name ? ' <span class="tag" style="background:#e0f2fe;color:#075985" title="Sales">' + ico('briefcase-business', 11) + ' ' + esc(l.sales_name) + '</span>' : ''; }
  function slLeadSel203() {
    var sel = $('#leadSalesFlt'); if (!sel) return;
    var seen = {};
    leadAll203.forEach(function (l) { if (l.sales_id) seen[l.sales_id] = l.sales_name || l.sales_id; });
    var ids = Object.keys(seen).sort(function (a, b) { return String(seen[a]).localeCompare(String(seen[b])); });
    sel.style.display = ids.length ? '' : 'none';
    sel.innerHTML = '<option value="">Semua sales</option>' + ids.map(function (id) { return '<option value="' + esc(id) + '">' + esc(seen[id]) + '</option>'; }).join('') + '<option value="_none">Tanpa sales</option>';
    if (leadSales203 && leadSales203 !== '_none' && !seen[leadSales203]) leadSales203 = '';
    sel.value = leadSales203;
    sel.onchange = function () { leadSales203 = sel.value; leadData = slLeadFilt203(leadAll203); renderLeads(); };
  }
'''

s = rd(JS)
if TAG not in s:
    s = rep(s, "  function tfBadgeHtml(tp) {", JS_LIB + "  function tfBadgeHtml(tp) {", what='js lib')
    s = rep(s, "    // v1.2.19: nama kontak (dari daftar percakapan) + tombol koreksi\n",
            "    toolBtns += slThreadTools203(res);   // " + TAG + "\n    // v1.2.19: nama kontak (dari daftar percakapan) + tombol koreksi\n", what='tools')
    s = rep(s, "    tfBindThread(num, res);   // v1.2.138: filter-topik\n",
            "    tfBindThread(num, res);   // v1.2.138: filter-topik\n    slBindThread203(num, res);   // " + TAG + "\n", what='bind')
    s = rep(s, "    loadAgentReport();\n  }\n  function timModeNote() {",
            "    loadAgentReport();\n    slTimLoad203();   // " + TAG + "\n  }\n  function timModeNote() {", what='loadTim')
    s = rep(s, "      leadData = res.leads || [];\n",
            "      leadAll203 = res.leads || []; slLeadSel203(); leadData = slLeadFilt203(leadAll203);   // " + TAG + "\n", what='fetchLeads')
    s = rep(s, "          ' ' + contactStageBadgeHtml(l.contact_stage, l.contact_vip, ';margin-left:2px') +\n",
            "          ' ' + contactStageBadgeHtml(l.contact_stage, l.contact_vip, ';margin-left:2px') + slLeadBadge203(l) +\n", what='lead badge')
    s = rep(s, "              '<div style=\"color:var(--muted);font-size:12px\">Dianalisa ' + esc((l.analyzed_at || '').slice(0, 16)) + '</div>' +\n",
            "              '<div style=\"color:var(--muted);font-size:12px\">' + (l.analyzed_at ? 'Dianalisa ' + esc(l.analyzed_at.slice(0, 16)) : 'Dibuat dari PO ' + esc((l.updated_at || '').slice(0, 16))) + '</div>' +   // " + TAG + "\n", what='lead tanggal')
    s = rep(s, "            '<div style=\"margin-top:6px\">' + contactStageBadgeHtml(l.contact_stage, l.contact_vip) + '</div>' +\n",
            "            '<div style=\"margin-top:6px\">' + contactStageBadgeHtml(l.contact_stage, l.contact_vip) + slLeadBadge203(l) + '</div>' +\n", what='kanban badge')
    save(JS, s)
else: print('sudah', JS)

# ============================== HTML ==============================
HT_CARDS = '''      <!-- v1.2.203: sales-tag -->
      <div class="card" data-role-card="super_admin,admin,supervisor" id="slCard"><h3>Sales</h3>
        <div class="desc">Daftar nama sales untuk ditandai di tiap chat WhatsApp (kepala chat › Sales). Sales tidak perlu akun login. Agent &amp; Supervisor memilih sales, mencatat PO, dan menjadikan lead Close Deal langsung dari chat.</div>
        <div id="slLocked" style="display:none;background:#fef2f2;border:1px solid #fecaca;color:#b91c1c;border-radius:8px;padding:10px 12px;font-size:13px"></div>
        <div id="slBody">
          <div class="scroll"><table class="tbl"><thead><tr><th>Nama</th><th>No. HP</th><th>Aktif</th><th></th></tr></thead><tbody id="tblSl"></tbody></table></div>
          <div class="row" style="flex-direction:row;gap:8px;align-items:flex-end;flex-wrap:wrap;margin-top:10px">
            <div><label class="fl">Nama sales</label><input type="text" id="slName" maxlength="60" style="width:auto"></div>
            <div><label class="fl">No. HP (opsional)</label><input type="text" id="slPhone" maxlength="20" style="width:auto"></div>
            <button class="btn" id="btnSlAdd" type="button"><span data-ico="user-plus" data-ico-size="15"></span> Tambah</button>
          </div>
        </div>
      </div>

      <div class="card" data-role-card="super_admin,admin,supervisor" id="slrCard"><h3>Laporan per Sales</h3>
        <div class="row" style="flex-direction:row;gap:8px;align-items:flex-end;flex-wrap:wrap">
          <div><label class="fl">Dari</label><input type="date" id="slrFrom" style="width:auto"></div>
          <div><label class="fl">Sampai</label><input type="date" id="slrTo" style="width:auto"></div>
          <button class="btn ghost" id="btnSlrLoad" type="button"><span data-ico="rotate-cw" data-ico-size="15"></span> Tampilkan</button>
          <button class="btn ghost" id="btnSlrCsv" type="button"><span data-ico="download" data-ico-size="15"></span> Unduh CSV</button>
        </div>
        <div class="tim-kpis" id="slrKpis"></div>
        <div class="scroll"><table class="tbl"><thead><tr><th>Sales</th><th style="text-align:right">Chat di-tag</th><th style="text-align:right">PO</th><th style="text-align:right">Close Deal</th><th style="text-align:right">Close Lose</th><th style="text-align:right">Konversi</th></tr></thead><tbody id="tblSlr"></tbody></table></div>
        <div class="help" style="margin-top:8px">Chat di-tag dihitung dari tanggal chat ditandai ke sales itu, PO dari tanggal PO, Close Deal/Lose dari tanggal status lead berubah (tercatat sejak v1.2.203). Konversi = Close Deal ÷ Chat di-tag. Klik baris untuk rincian chat.</div>
      </div>

'''

s = rd(HT)
if TAG not in s:
    s = rep(s, '<script src="app.js?v=1.2.202"></script><!-- v1.2.202: id-noweb -->',
            '<script src="app.js?v=1.2.203"></script><!-- ' + TAG + ' --><!-- v1.2.202: id-noweb -->', what='app.js?v')
    s = rep(s, '      <div class="card"><h3>Laporan per Agent</h3>', HT_CARDS + '      <div class="card"><h3>Laporan per Agent</h3>', what='tim cards')
    s = rep(s, '          <button class="btn ghost sm" id="btnReloadLeads">&#8635; Muat ulang</button>',
            '          <select id="leadSalesFlt" class="btn ghost sm" style="display:none;width:auto" title="Filter per sales"></select><!-- ' + TAG + ' -->\n'
            '          <button class="btn ghost sm" id="btnReloadLeads">&#8635; Muat ulang</button>', what='lead filter')
    save(HT, s)
else: print('sudah', HT)
print('patch v1.2.203 selesai')
