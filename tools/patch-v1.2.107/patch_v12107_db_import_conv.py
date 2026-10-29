#!/usr/bin/env python3
"""v1.2.107: db_import ikut memindahkan percakapan (convs/*.jsonl + conv-open.json) ke dei_conversations.
Pakai: patch_v12107_db_import_conv.py <Herd>   (idempoten, backup *.bak-v12107-*)"""
import os, sys, time, shutil
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd')
F = H + '/dei-tenant/api/index.php'
TAG = 'v1.2.107: db-import-percakapan'
s = open(F, encoding='utf-8').read()
if TAG in s:
    print('sudah dipatch'); sys.exit(0)
shutil.copy2(F, F + '.bak-v12107-' + time.strftime('%Y%m%d-%H%M%S'))

old_v = "define('DEI_VERSION', 'v1.2.106');   // v1.2.106: kontak-sinkron"
assert s.count(old_v) == 1, 'DEI_VERSION tidak ditemukan'
s = s.replace(old_v, "define('DEI_VERSION', 'v1.2.107');   // " + TAG)

anchor = "        $res['conv_state'] = $n;\n        echo 'db_import: ' . json_encode($res) . \"\\n\";"
assert s.count(anchor) == 1, 'anchor db_import tidak ditemukan'
add = r"""        $res['conv_state'] = $n;
        // v1.2.107: db-import-percakapan — convs/*.jsonl (baris terakhir per id) lalu conv-open.json (paling baru)
        if ($force || !(int)$db->query('SELECT COUNT(*) FROM dei_conversations')->fetchColumn()) {
            $all = [];
            $files = (array)glob(CONV_DIR . '/*.jsonl');   // cek-storage: boleh (impor sekali)
            sort($files);
            foreach ($files as $f) {
                $fh = @fopen($f, 'r');
                if (!$fh) continue;
                while (($line = fgets($fh)) !== false) {
                    $c = json_decode($line, true);
                    if (is_array($c) && !empty($c['id'])) $all[(string)$c['id']] = $c;
                }
                fclose($fh);
            }
            foreach ((array)readJson(CONV_OPEN_FILE, []) as $c) {   // cek-storage: boleh (impor sekali)
                if (is_array($c) && !empty($c['id'])) $all[(string)$c['id']] = $c;
            }
            $n = 0;
            $db->beginTransaction();
            foreach ($all as $c) {
                if (empty($c['num']) || empty($c['opened_at']) || empty($c['status'])) continue;
                convDbSave($c); $n++;
            }
            $db->commit();
            $res['conversations'] = $n;
        } else $res['conversations'] = 'dilewati (tabel tidak kosong)';
        echo 'db_import: ' . json_encode($res) . "\n";"""
s = s.replace(anchor, add)
open(F, 'w', encoding='utf-8').write(s)
print('OK', F)
