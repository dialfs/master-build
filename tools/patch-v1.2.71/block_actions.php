    /* ---------- CLI (v1.2.71): worker antrean WA — mode queue=redis ----------
     * Dijalankan supervisord: php api/index.php action=wa_worker slot=<n>
     * Berhenti sendiri setelah max_jobs / max_sec supaya memori selalu segar. */
    case 'wa_worker': {
        if (PHP_SAPI !== 'cli') jsonOut(['ok' => false, 'error' => 'Hanya lewat CLI.'], 403);
        if (!deiQueueRedis()) { fwrite(STDERR, "wa_worker: queue bukan redis (lihat data/server.php)\n"); exit(1); }
        @set_time_limit(0);
        $slot    = preg_replace('/[^0-9a-z_-]/i', '', (string)($_GET['slot'] ?? '0'));
        if ($slot === '') $slot = '0';
        $maxJobs = max(1, (int)($_GET['max_jobs'] ?? 500));
        $maxSec  = max(5, (int)($_GET['max_sec'] ?? 3600));
        $rq   = deiRedis();
        $proc = 'q:wa:proc:' . $slot;
        $GLOBALS['dei_worker_slot'] = 'w' . $slot;
        // Job yang tertinggal dari proses slot ini sebelumnya (mati di tengah jalan) -> antre ulang di depan.
        while (($left = $rq->rPop($proc)) !== false && $left !== null) {
            $lj = json_decode($left, true);
            deiNumLockRelease($lj, 'w' . $slot);   // kunci nomor yang ditinggal proses mati
            $lj['try'] = (int)($lj['try'] ?? 0) + 1;
            if ($lj['try'] >= 3) { $rq->lPush('q:wa:dead', $left); $rq->lTrim('q:wa:dead', 0, 999); continue; }
            $rq->rPush('q:wa', json_encode($lj));
            error_log("wa_worker[$slot]: job tertinggal diantre ulang (percobaan {$lj['try']})");
        }
        $t0 = time(); $done = 0;
        while ($done < $maxJobs && (time() - $t0) < $maxSec) {
            $rq->set('w:hb:' . $slot, time(), ['ex' => 30]);
            $job = $rq->brPopLPush('q:wa', $proc, 5);
            if ($job === false || $job === null || $job === '') continue;
            $done++;
            $j = json_decode($job, true);
            unset($GLOBALS['dei_reply_mode_cache'], $GLOBALS['dei_features_cache']);   // settings bisa berubah antar job
            try {
                $s  = getSettings();
                $wa = waConf($s);
                waHandleMetaPayload($s, $wa, json_decode((string)($j['raw'] ?? ''), true));
            } catch (\Throwable $e) {
                error_log("wa_worker[$slot]: " . $e->getMessage());
                $try = (int)($j['try'] ?? 0) + 1;
                if ($try < 3) { $j['try'] = $try; $rq->lPush('q:wa', json_encode($j)); }
                else { $rq->lPush('q:wa:dead', $job); $rq->lTrim('q:wa:dead', 0, 999); }
            }
            $rq->lRem($proc, $job, 1);
        }
        exit(0);
    }

    /* ---------- CLI (v1.2.71): status antrean untuk pemantauan ---------- */
    case 'wa_queue_status': {
        if (PHP_SAPI !== 'cli') jsonOut(['ok' => false, 'error' => 'Hanya lewat CLI.'], 403);
        $out = ['ok' => true, 'version' => DEI_VERSION, 'storage' => deiServerConf()['storage'], 'queue' => deiServerConf()['queue']];
        if (deiQueueRedis()) {
            $rq = deiRedis();
            $out['pending'] = (int)$rq->lLen('q:wa');
            $out['dead']    = (int)$rq->lLen('q:wa:dead');
            $alive = 0;
            for ($i = 0; $i < 64; $i++) { if ($rq->exists('w:hb:' . $i)) $alive++; }
            $out['workers_alive'] = $alive;
        }
        echo json_encode($out, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n";
        exit(0);
    }

    /* ---------- CLI (v1.2.71): buat tabel MySQL ---------- */
    case 'db_init': {
        if (PHP_SAPI !== 'cli') jsonOut(['ok' => false, 'error' => 'Hanya lewat CLI.'], 403);
        if (!deiStorageMysql()) { fwrite(STDERR, "db_init: storage bukan mysql (lihat data/server.php)\n"); exit(1); }
        foreach (deiDbSchema() as $sql) deiDb()->exec($sql);
        echo "db_init: OK (" . count(deiDbSchema()) . " tabel)\n";
        exit(0);
    }

    /* ---------- CLI (v1.2.71): pindahkan data JSON lama ke MySQL ----------
     * Sekali saat tenant pindah ke server sendiri. Tabel harus kosong kecuali force=1. */
    case 'db_import': {
        if (PHP_SAPI !== 'cli') jsonOut(['ok' => false, 'error' => 'Hanya lewat CLI.'], 403);
        if (!deiStorageMysql()) { fwrite(STDERR, "db_import: storage bukan mysql\n"); exit(1); }
        $db = deiDb();
        foreach (deiDbSchema() as $sql) $db->exec($sql);
        $force = !empty($_GET['force']);
        $res = [];
        if ($force || !(int)$db->query('SELECT COUNT(*) FROM dei_log')->fetchColumn()) {
            $old = readJson(LOG_FILE, []);   // cek-storage: boleh (impor sekali)
            $db->beginTransaction();
            foreach (array_reverse(is_array($old) ? $old : []) as $e) { if (is_array($e)) logDbInsert($e); }
            $db->commit();
            $res['log'] = is_array($old) ? count($old) : 0;
        } else $res['log'] = 'dilewati (tabel tidak kosong)';
        if ($force || !(int)$db->query('SELECT COUNT(*) FROM dei_contacts')->fetchColumn()) {
            $old = readJson(CONTACTS_FILE, []);   // cek-storage: boleh (impor sekali)
            $up = $db->prepare('INSERT INTO dei_contacts (num, body) VALUES (?, ?) ON DUPLICATE KEY UPDATE body = VALUES(body)');
            $n = 0;
            foreach ((is_array($old) ? $old : []) as $num => $c) {
                $num = preg_replace('/\D/', '', (string)$num);
                if ($num === '' || !is_array($c)) continue;
                $up->execute([$num, logEncode($c)]); $n++;
            }
            $res['contacts'] = $n;
        } else $res['contacts'] = 'dilewati (tabel tidak kosong)';
        $n = 0;
        $up = $db->prepare('INSERT INTO dei_wa_sessions (num, ts, turns) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE ts = VALUES(ts), turns = VALUES(turns)');
        foreach ((array)glob(WA_SESSIONS_DIR . '/*.json') as $f) {   // cek-storage: boleh (impor sekali)
            $d = json_decode((string)@file_get_contents($f), true);
            if (!is_array($d) || empty($d['turns'])) continue;
            $up->execute([basename($f, '.json'), (int)($d['ts'] ?? 0), logEncode($d['turns'])]); $n++;
        }
        $res['sessions'] = $n;
        $n = 0;
        $up = $db->prepare('INSERT INTO dei_conv_state (num, last_at, body) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE last_at = VALUES(last_at), body = VALUES(body)');
        foreach ((array)readJson(CONV_STATE_FILE, []) as $num => $st) {   // cek-storage: boleh (impor sekali)
            $num = waNormNum($num);
            if ($num === '' || !is_array($st)) continue;
            $up->execute([$num, (int)($st['last_at'] ?? 0), logEncode($st)]); $n++;
        }
        $res['conv_state'] = $n;
        echo 'db_import: ' . json_encode($res) . "\n";
        exit(0);
    }

