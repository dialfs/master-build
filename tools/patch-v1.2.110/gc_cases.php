    /* ---------- v1.2.109: guest-comment / v1.2.110: customer-feedback — form publik (QR di meja/kasir/kamar) ---------- */
    case 'gc_form': {
        $s = getSettings();
        header('Content-Type: text/html; charset=utf-8');
        header('Cache-Control: no-store');
        header('X-Robots-Tag: noindex');
        $room = mb_substr(preg_replace('/[^A-Za-z0-9 -]/', '', (string)($_GET['room'] ?? '')), 0, 20);
        $act = false;
        try { $act = gcActive(); } catch (\Throwable $e) { error_log('gc_form: ' . $e->getMessage()); }
        echo gcFormHtml($s, $act, $room);
        exit;
    }

    case 'gc_submit': {
        if ($_SERVER['REQUEST_METHOD'] !== 'POST') jsonOut(['ok' => false, 'error' => 'Method not allowed'], 405);
        if (!gcActive()) jsonOut(['ok' => false, 'error' => 'Form feedback belum tersedia.'], 403);
        $in = bodyInput();
        if (trim((string)($in['hp'] ?? '')) !== '') jsonOut(['ok' => true]);   // jebakan bot spam
        if (!checkRateLimit('gc:' . clientIp(), 8)) jsonOut(['ok' => false, 'error' => 'Terlalu banyak kiriman. Silakan coba lagi nanti.'], 429);
        $conf = gcConf();
        $rIn = is_array($in['ratings'] ?? null) ? $in['ratings'] : [];
        $r = [];
        foreach ($conf['aspects'] as $a) { $v = (int)($rIn[$a['id']] ?? 0); if ($v >= 1 && $v <= 5) $r[$a['id']] = $v; }
        if (count($r) < count($conf['aspects'])) jsonOut(['ok' => false, 'error' => (($in['lang'] ?? '') === 'en' ? 'Please rate every aspect.' : 'Mohon beri nilai untuk semua aspek.')], 400);
        $phone = mb_substr(preg_replace('/[^0-9+]/', '', (string)($in['phone'] ?? '')), 0, 20);
        gcStore(['channel' => 'web',
                 'name'    => $conf['ask_name'] ? mb_substr(trim((string)($in['name'] ?? '')), 0, 60) : '',
                 'room'    => $conf['ask_room'] ? mb_substr(trim(preg_replace('/[^\p{L}\p{N} -]/u', '', (string)($in['room'] ?? ''))), 0, 20) : '',
                 'phone'   => $conf['ask_phone_web'] ? $phone : '',
                 'lang'    => (($in['lang'] ?? '') === 'en') ? 'en' : 'id',
                 'ratings' => $r,
                 'comment' => mb_substr(trim(str_replace("\r", '', (string)($in['comment'] ?? ''))), 0, 2000)]);
        jsonOut(['ok' => true]);
    }

    /* ---------- v1.2.109: guest-comment — dashboard ---------- */
    case 'gc_admin': {
        $u  = requireAuth(['super_admin', 'admin', 'supervisor']);
        $in = bodyInput();
        $op = (string)($in['op'] ?? ($_GET['op'] ?? 'get'));
        $canEdit = in_array(($u['role'] ?? ''), ['super_admin', 'admin'], true);
        $plan = gcPlan();
        if ($op === 'get') {
            $s = getSettings();
            $wl = [];
            foreach (waChannels($s) as $c) { if ((string)$c['number'] !== '') $wl[] = ['label' => $c['label'], 'number' => $c['number']]; }
            jsonOut(['ok' => true, 'plan' => $plan, 'locked' => !$plan['ok'], 'locked_msg' => gcLockedMsg(), 'conf' => gcConf(),
                     'can_edit' => $canEdit, 'form_url' => gcFormUrl(), 'wa' => $wl, 'count' => count(gcAll())]);
        }
        if ($op === 'save') {
            if (!$canEdit) jsonOut(['ok' => false, 'error' => 'Khusus Super Admin / Admin.'], 403);
            $c = gcClean(is_array($in['conf'] ?? null) ? $in['conf'] : []);
            if ($c['enabled'] && !$plan['ok']) jsonOut(['ok' => false, 'error' => gcLockedMsg(), 'locked' => true], 403);
            writeJson(GC_CONF_FILE, $c);
            unset($GLOBALS['dei_gc_conf']);
            try { waAuditLog('gc_conf_set', $u['username'], '', ['enabled' => $c['enabled'], 'aspects' => count($c['aspects'])]); } catch (\Throwable $e) {}
            jsonOut(['ok' => true, 'conf' => gcConf()]);
        }
        if ($op === 'list') {
            $from = preg_match('/^\d{4}-\d{2}-\d{2}$/', (string)($in['from'] ?? '')) ? $in['from'] : '';
            $to   = preg_match('/^\d{4}-\d{2}-\d{2}$/', (string)($in['to'] ?? '')) ? $in['to'] : '';
            $chan = (string)($in['channel'] ?? 'all');
            $rate = (string)($in['rating'] ?? 'all');
            $stat = (string)($in['status'] ?? 'all');
            $q    = mb_strtolower(trim((string)($in['q'] ?? '')), 'UTF-8');
            $conf = gcConf();
            $rows = [];
            $agg = []; $n = 0; $sumAvg = 0.0; $lowN = 0; $byCh = ['whatsapp' => 0, 'web' => 0]; $dist = [1 => 0, 2 => 0, 3 => 0, 4 => 0, 5 => 0];
            foreach (gcAll() as $e) {
                $d = substr((string)($e['ts'] ?? ''), 0, 10);
                if ($from !== '' && $d < $from) continue;
                if ($to !== '' && $d > $to) continue;
                if ($chan !== 'all' && ($e['channel'] ?? '') !== $chan) continue;
                if ($rate === 'low' && empty($e['low'])) continue;
                if ($rate === 'high' && (float)($e['avg'] ?? 0) < 4) continue;
                if ($stat !== 'all' && ($e['status'] ?? 'baru') !== $stat) continue;
                if ($q !== '') {
                    $hay = mb_strtolower(($e['name'] ?? '') . ' ' . ($e['room'] ?? '') . ' ' . ($e['num'] ?? '') . ' ' . ($e['phone'] ?? '') . ' ' . ($e['comment'] ?? '') . ' ' . ($e['note'] ?? ''), 'UTF-8');
                    if (mb_strpos($hay, $q) === false) continue;
                }
                $rows[] = $e;
                $n++; $sumAvg += (float)($e['avg'] ?? 0);
                if (!empty($e['low'])) $lowN++;
                $ch = ($e['channel'] ?? '') === 'whatsapp' ? 'whatsapp' : 'web';
                $byCh[$ch]++;
                $ra = (int)round((float)($e['avg'] ?? 0)); if ($ra >= 1 && $ra <= 5) $dist[$ra]++;
                foreach ((array)($e['ratings'] ?? []) as $k => $v) {
                    if (!isset($agg[$k])) $agg[$k] = [0, 0];
                    $agg[$k][0] += (int)$v; $agg[$k][1]++;
                }
            }
            $asp = []; $known = [];
            foreach ($conf['aspects'] as $a) {
                $known[$a['id']] = 1;
                $x = $agg[$a['id']] ?? [0, 0];
                $asp[] = ['id' => $a['id'], 'label' => $a['label'], 'avg' => $x[1] ? round($x[0] / $x[1], 2) : 0, 'n' => $x[1]];
            }
            foreach ($agg as $k => $x) {   // aspek lama yang sudah dihapus dari pengaturan
                if (isset($known[$k])) continue;
                $lbl = $k;
                foreach ($rows as $e) { if (!empty($e['labels'][$k])) { $lbl = $e['labels'][$k]; break; } }
                $asp[] = ['id' => $k, 'label' => $lbl, 'avg' => round($x[0] / $x[1], 2), 'n' => $x[1], 'old' => true];
            }
            $all = !empty($in['all']);
            $off = max(0, (int)($in['offset'] ?? 0));
            $lim = $all ? GC_MAX : max(1, min(200, (int)($in['limit'] ?? 50)));
            jsonOut(['ok' => true, 'total' => $n, 'items' => array_slice($rows, $all ? 0 : $off, $lim),
                     'stats' => ['n' => $n, 'avg' => $n ? round($sumAvg / $n, 2) : 0, 'low' => $lowN, 'by_channel' => $byCh, 'dist' => $dist, 'aspects' => $asp],
                     'low_th' => $conf['low']]);
        }
        if ($op === 'update' || $op === 'delete') {
            $id = preg_replace('/[^a-z0-9]/', '', (string)($in['id'] ?? ''));
            if ($id === '') jsonOut(['ok' => false, 'error' => 'id kosong'], 400);
            if ($op === 'delete' && !$canEdit) jsonOut(['ok' => false, 'error' => 'Khusus Super Admin / Admin.'], 403);
            $status = (string)($in['status'] ?? '');
            if ($op === 'update' && !in_array($status, ['baru', 'ditindak', 'selesai'], true)) jsonOut(['ok' => false, 'error' => 'Status tidak dikenal.'], 400);
            $note = mb_substr(trim(str_replace("\r", '', (string)($in['note'] ?? ''))), 0, 1000);
            $who = (string)($u['username'] ?? '');
            $res = deiWithLock('gc', function () use ($id, $op, $status, $note, $who) {
                $all = gcAll();
                foreach ($all as $i => $e) {
                    if (($e['id'] ?? '') !== $id) continue;
                    if ($op === 'delete') { array_splice($all, $i, 1); writeJson(GC_FILE, $all); return ['deleted' => true]; }
                    $all[$i]['status'] = $status;
                    $all[$i]['note'] = $note;
                    $all[$i]['handled_by'] = $who;
                    $all[$i]['handled_at'] = wibDate('Y-m-d H:i:s');
                    writeJson(GC_FILE, $all);
                    return $all[$i];
                }
                return null;
            });
            if ($res === null) jsonOut(['ok' => false, 'error' => 'Entri tidak ditemukan.'], 404);
            jsonOut(['ok' => true, 'item' => $op === 'update' ? $res : null]);
        }
        jsonOut(['ok' => false, 'error' => 'op tidak dikenal'], 400);
    }

