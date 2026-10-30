    case 'import_contacts': {   // v1.2.113: import-kontak
        // Data pribadi masuk dalam jumlah besar -> hanya Super Admin & Admin.
        $me = requireAuth(['super_admin', 'admin']);
        if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'POST') jsonOut(['ok' => false, 'error' => 'Gunakan POST.'], 405);
        $in = bodyInput();
        $rows = $in['rows'] ?? null;
        if (!is_array($rows) || !$rows) jsonOut(['ok' => false, 'error' => 'Tidak ada baris untuk diimpor.'], 400);
        if (count($rows) > 1000) jsonOut(['ok' => false, 'error' => 'Maksimal 1.000 kontak per kiriman.'], 400);
        $overwrite = !empty($in['overwrite']);
        $src = mb_substr(trim((string)($in['file'] ?? '')), 0, 80);
        $now = date('Y-m-d H:i:s');

        // Normalisasi + gabung nomor ganda (tahap tertinggi menang, jumlah dijumlah).
        $clean = []; $invalid = 0;
        foreach ($rows as $r) {
            if (!is_array($r)) { $invalid++; continue; }
            $num = contactImportNormNum($r['n'] ?? '');
            if ($num === '') { $invalid++; continue; }
            $stage = (string)($r['stage'] ?? '');
            if ($stage !== '' && !contactStageValid($stage)) $stage = '';
            $nm = trim(preg_replace('/\s+/u', ' ', (string)($r['name'] ?? '')));
            $item = ['stage' => $stage, 'name' => mb_substr($nm, 0, 100),
                     'st' => mb_substr(trim((string)($r['st'] ?? '')), 0, 60),
                     'cnt' => max(1, min(9999, (int)($r['cnt'] ?? 1))), 'src' => $src];
            if (!isset($clean[$num])) { $clean[$num] = $item; continue; }
            $old = $clean[$num];
            $item['cnt'] += $old['cnt'];
            if (contactImportRank($old['stage']) >= contactImportRank($stage)) { $old['cnt'] = $item['cnt']; $item = $old; }
            if ($item['name'] === '') $item['name'] = $old['name'];
            $clean[$num] = $item;
        }

        $cnt = ['created' => 0, 'updated' => 0, 'kept' => 0];
        $byStage = [];
        if (!deiStorageMysql()) {
            // Mode berkas: satu kunci + satu tulis untuk seluruh kiriman.
            deiWithLock('wa-contacts', function () use ($clean, $overwrite, $now, &$cnt) {
                $all = waGetContacts();
                foreach ($clean as $num => $r) {
                    $isNew = !isset($all[$num]) || !is_array($all[$num]);
                    $c = $isNew ? waContactDefaults() : $all[$num];
                    $res = 'updated';
                    contactImportApply($c, $isNew, $r, $overwrite, $now, $res);
                    $all[$num] = $c;
                    $cnt[$res]++;
                }
                writeJson(CONTACTS_FILE, $all);
            });
        } else {
            foreach ($clean as $num => $r) {
                $res = 'updated';
                waContactUpdate($num, function (&$c, $isNew) use ($r, $overwrite, $now, &$res) {
                    contactImportApply($c, $isNew, $r, $overwrite, $now, $res);
                });
                $cnt[$res]++;
            }
        }
        foreach ($clean as $r) { $k = $r['stage'] === '' ? 'none' : $r['stage']; $byStage[$k] = ($byStage[$k] ?? 0) + 1; }
        try { waAuditLog('contacts_import', $me['username'] ?? '?', '', ['file' => $src, 'n' => count($clean)] + $cnt); } catch (\Throwable $e) {}
        error_log('import_contacts: ' . ($me['username'] ?? '?') . ' ' . count($clean) . ' kontak dari ' . $src . ' ' . json_encode($cnt));
        jsonOut(['ok' => true, 'total' => count($clean), 'invalid' => $invalid, 'by_stage' => $byStage] + $cnt);
        break;
    }

