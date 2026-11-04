<?php
/**
 * v1.2.138: filter-topik — server pusat mengklasifikasi topik percakapan WA untuk tenant.
 *  - Key OpenRouter milik pusat DEI (admin-config.json › classify.openrouter_key; kosong = pakai key pendaftaran).
 *  - Model bawaan anthropic/claude-haiku-5.5.
 *  - Kuota per bulan (WIB) per tenant: bawaan per paket (Growth 5.000, Business 15.000, Pro 30.000,
 *    Custom/Enterprise 30.000; Starter & trial 0), bisa ditimpa per tenant (tenants.json › classify_quota).
 *  - Dipakai backend/index.php (action classify, get/save_classify_config, set_cap) dan cron-tick.php (X-Dei-Features).
 * Prompt HARUS sama dengan tpPrompt() di tenant (api/index.php).
 */
if (!defined('CLS_DATA')) define('CLS_DATA', dirname(__DIR__) . '/data');
if (!defined('CLS_MAX_ITEMS')) define('CLS_MAX_ITEMS', 10);

function clsRead($f, $def) { if (!is_file($f)) return $def; $d = json_decode((string)file_get_contents($f), true); return is_array($d) ? $d : $def; }
function clsWrite($f, $data) {
    $tmp = $f . '.tmp.' . getmypid();
    if (file_put_contents($tmp, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE), LOCK_EX) !== false) rename($tmp, $f);
}
function clsTierQuotas() { return ['growth' => 5000, 'business' => 15000, 'pro' => 30000, 'custom' => 30000, 'enterprise' => 30000]; }
// Kuota efektif tenant / bulan. 0 = tidak dapat fitur ini.
function clsQuota($t) {
    if (!is_array($t)) return 0;
    if (is_array($t['trial'] ?? null) || strtolower((string)($t['tier'] ?? '')) === 'trial') return 0;
    if (array_key_exists('classify_quota', $t) && $t['classify_quota'] !== null && $t['classify_quota'] !== '') return max(0, (int)$t['classify_quota']);
    return clsTierQuotas()[strtolower((string)($t['tier'] ?? ''))] ?? 0;
}
function clsMonth() { return gmdate('Y-m', time() + 7 * 3600); }
function clsConfig() {
    $all = clsRead(CLS_DATA . '/admin-config.json', []);
    $c = is_array($all['classify'] ?? null) ? $all['classify'] : [];
    $own = trim((string)($c['openrouter_key'] ?? ''));
    $key = $own !== '' ? $own : trim((string)($all['signup']['openrouter_key'] ?? ''));
    return ['key' => $key, 'own_key' => $own !== '', 'model' => trim((string)($c['model'] ?? '')) ?: 'anthropic/claude-haiku-5.5',
            'enabled' => !array_key_exists('enabled', $c) || !empty($c['enabled'])];
}
function clsSaveConfig($in) {
    $all = clsRead(CLS_DATA . '/admin-config.json', []);
    $c = is_array($all['classify'] ?? null) ? $all['classify'] : [];
    $k = trim((string)($in['openrouter_key'] ?? ''));
    if ($k !== '' && strpos($k, '•') === false) $c['openrouter_key'] = $k;
    if (!empty($in['clear_key'])) $c['openrouter_key'] = '';
    if (array_key_exists('model', $in)) $c['model'] = trim((string)$in['model']);
    if (array_key_exists('enabled', $in)) $c['enabled'] = !empty($in['enabled']);
    $all['classify'] = $c;
    clsWrite(CLS_DATA . '/admin-config.json', $all);
    return clsConfigPublic();
}
function clsConfigPublic() {
    $c = clsConfig();
    $all = clsRead(CLS_DATA . '/admin-config.json', []);
    $own = trim((string)($all['classify']['openrouter_key'] ?? ''));
    return ['enabled' => $c['enabled'], 'model' => $c['model'], 'key_set' => $c['key'] !== '', 'own_key' => $c['own_key'],
            'key_masked' => $own !== '' ? substr($own, 0, 10) . '••••' . substr($own, -4) : '',
            'tiers' => clsTierQuotas(), 'month' => clsMonth(), 'usage' => clsUsageAll()];
}
function clsUsageAll() {
    $u = clsRead(CLS_DATA . '/classify-usage.json', []);
    $m = clsMonth(); $out = [];
    foreach ($u as $tid => $rows) if (is_array($rows[$m] ?? null)) $out[$tid] = $rows[$m];
    return $out;
}
function clsUsageFor($tid) {
    $u = clsRead(CLS_DATA . '/classify-usage.json', []);
    $r = $u[strtolower(trim((string)$tid))][clsMonth()] ?? null;
    return is_array($r) ? $r : ['n' => 0, 'cost' => 0];
}
function clsUsageAdd($tid, $n, $in, $out, $cost) {
    $f = CLS_DATA . '/classify-usage.json';
    $lock = @fopen(CLS_DATA . '/classify-usage.lock', 'c'); if ($lock) @flock($lock, LOCK_EX);
    $u = clsRead($f, []);
    $tid = strtolower(trim((string)$tid)); $m = clsMonth();
    $r = is_array($u[$tid][$m] ?? null) ? $u[$tid][$m] : ['n' => 0, 'in' => 0, 'out' => 0, 'cost' => 0];
    $r['n'] += (int)$n; $r['in'] += (int)$in; $r['out'] += (int)$out; $r['cost'] = round((float)$r['cost'] + (float)$cost, 6);
    $r['at'] = gmdate('Y-m-d H:i:s', time() + 7 * 3600);
    $u[$tid][$m] = $r;
    ksort($u[$tid]); $u[$tid] = array_slice($u[$tid], -12, null, true);
    clsWrite($f, $u);
    if ($lock) { @flock($lock, LOCK_UN); @fclose($lock); }
    return $r;
}
function clsPrompt($business, $topics, $msgs) {
    $list = '';
    foreach ($topics as $t) $list .= '- ' . $t['id'] . ': ' . $t['name'] . (($t['desc'] ?? '') !== '' ? ' (' . $t['desc'] . ')' : '') . "\n";
    $sys = "Anda mengklasifikasi percakapan WhatsApp pelanggan" . ($business !== '' ? " dengan bisnis \"" . $business . "\"" : '') . ".\n"
         . "Tentukan topik yang sedang ditanyakan/dibahas PELANGGAN, HANYA dari daftar ini (pakai id-nya):\n" . $list
         . "\nATURAN:\n- t: semua id topik yang dibahas pelanggan (boleh lebih dari satu, maks 4). Abaikan sapaan/basa-basi.\n"
         . "- m: satu id topik utama = yang paling relevan dengan pesan pelanggan TERAKHIR.\n"
         . "- Kalau tidak ada yang cocok atau hanya basa-basi: t = [] dan m = \"\".\n"
         . "- c: keyakinan 0-1.\nBalas HANYA JSON: {\"t\":[\"id\"],\"m\":\"id\",\"c\":0.9}";
    $conv = '';
    foreach ($msgs as $b) $conv .= (($b['r'] ?? '') === 'p' ? 'Pelanggan: ' : 'Kami: ') . str_replace(["\r", "\n"], ' ', (string)($b['t'] ?? '')) . "\n";
    return [$sys, "Percakapan (lama ke baru):\n" . $conv];
}
function clsParse($raw, $ids) {
    $raw = (string)$raw; $a = strpos($raw, '{'); $b = strrpos($raw, '}');
    $j = ($a !== false && $b !== false) ? json_decode(substr($raw, $a, $b - $a + 1), true) : null;
    if (!is_array($j)) return null;
    $ok = array_flip($ids); $t = [];
    foreach ((array)($j['t'] ?? []) as $x) { $x = (string)$x; if (isset($ok[$x]) && !in_array($x, $t, true)) $t[] = $x; }
    $t = array_slice($t, 0, 4);
    $m = (string)($j['m'] ?? '');
    if (!isset($ok[$m])) $m = $t[0] ?? '';
    if ($m !== '' && !in_array($m, $t, true)) array_unshift($t, $m);
    return ['t' => $t, 'm' => $m, 'c' => max(0, min(1, (float)($j['c'] ?? 0)))];
}
function clsClean($s, $max) { return mb_substr(trim(preg_replace('/\s+/u', ' ', (string)$s)), 0, $max); }

/** action=classify — body {tenant_id, license_key, business, topics:[{id,name,desc}], items:[{id, msgs:[{r,t}]}]} */
function clsHandle($tenants, $body) {
    $tid = strtolower(trim((string)($body['tenant_id'] ?? '')));
    $lic = trim((string)($body['license_key'] ?? ''));
    $t = null;
    foreach ($tenants as $x) if (is_array($x) && strtolower(trim((string)($x['tenant_id'] ?? ''))) === $tid) { $t = $x; break; }
    if (!$t || $tid === '') return [404, ['ok' => false, 'error' => 'Tenant tidak terdaftar di server pusat.']];
    if (!hash_equals((string)($t['license_key'] ?? ''), $lic)) return [403, ['ok' => false, 'error' => 'License key tidak cocok.']];
    $st = (string)($t['license_status'] ?? 'active');
    if (empty($t['active']) && array_key_exists('active', $t)) return [403, ['ok' => false, 'error' => 'Tenant nonaktif.']];
    if (in_array($st, ['suspended', 'blocked'], true)) return [403, ['ok' => false, 'error' => 'Lisensi ' . $st . '.']];
    $cfg = clsConfig();
    if (!$cfg['enabled']) return [503, ['ok' => false, 'error' => 'Klasifikasi topik sedang dimatikan di server pusat.']];
    if ($cfg['key'] === '') return [503, ['ok' => false, 'error' => 'OpenRouter key klasifikasi belum diatur di server pusat.']];
    $limit = clsQuota($t);
    $use = clsUsageFor($tid);
    $quota = ['limit' => $limit, 'used' => (int)($use['n'] ?? 0), 'month' => clsMonth()];
    if ($limit <= 0) return [403, ['ok' => false, 'quota_out' => true, 'quota' => $quota, 'error' => 'Paket ini belum termasuk Filter Topik (mulai paket Growth).']];
    if ($quota['used'] >= $limit) return [429, ['ok' => false, 'quota_out' => true, 'quota' => $quota, 'error' => 'Kuota klasifikasi topik bulan ini habis (' . $quota['used'] . '/' . $limit . ').']];

    $topics = []; $ids = [];
    foreach (array_slice((array)($body['topics'] ?? []), 0, 40) as $x) {
        if (!is_array($x)) continue;
        $id = preg_replace('/[^a-z0-9_]/', '', strtolower((string)($x['id'] ?? '')));
        $nm = clsClean($x['name'] ?? '', 50);
        if ($id === '' || $nm === '' || isset($ids[$id])) continue;
        $ids[$id] = true;
        $topics[] = ['id' => $id, 'name' => $nm, 'desc' => clsClean($x['desc'] ?? '', 160)];
    }
    if (!$topics) return [400, ['ok' => false, 'error' => 'Daftar topik kosong.']];
    $biz = clsClean($body['business'] ?? '', 80);
    $items = [];
    foreach (array_slice((array)($body['items'] ?? []), 0, CLS_MAX_ITEMS) as $it) {
        if (!is_array($it)) continue;
        $msgs = [];
        foreach (array_slice((array)($it['msgs'] ?? []), -20) as $m) {
            if (!is_array($m)) continue;
            $tx = clsClean($m['t'] ?? '', 300);
            if ($tx !== '') $msgs[] = ['r' => (($m['r'] ?? '') === 'p') ? 'p' : 'k', 't' => $tx];
        }
        if ($msgs) $items[] = ['id' => (int)($it['id'] ?? 0), 'msgs' => $msgs];
    }
    $room = $limit - $quota['used'];
    $results = [];
    if (count($items) > $room) {
        foreach (array_slice($items, $room) as $it) $results[] = ['id' => $it['id'], 'ok' => false, 'error' => 'kuota habis'];
        $items = array_slice($items, 0, $room);
    }
    // panggil OpenRouter paralel
    $mh = curl_multi_init(); $hs = [];
    foreach ($items as $it) {
        list($sys, $user) = clsPrompt($biz, $topics, $it['msgs']);
        $ch = curl_init(getenv('DEI_CLS_OR_URL') ?: 'https://openrouter.ai/api/v1/chat/completions');   // env: uji dengan mock
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_POST => true, CURLOPT_TIMEOUT => 30, CURLOPT_CONNECTTIMEOUT => 8,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'Authorization: Bearer ' . $cfg['key'], 'X-Title: DEI Filter Topik'],
            CURLOPT_POSTFIELDS => json_encode(['model' => $cfg['model'], 'max_tokens' => 150, 'temperature' => 0, 'usage' => ['include' => true],
                'messages' => [['role' => 'system', 'content' => $sys], ['role' => 'user', 'content' => $user]]], JSON_UNESCAPED_UNICODE)]);
        curl_multi_add_handle($mh, $ch);
        $hs[] = [$ch, $it['id']];
    }
    do { $s = curl_multi_exec($mh, $run); if ($run) curl_multi_select($mh, 1.0); } while ($run && $s === CURLM_OK);
    $n = 0; $tin = 0; $tout = 0; $cost = 0.0;
    $idList = array_keys($ids);
    foreach ($hs as list($ch, $iid)) {
        $res = curl_multi_getcontent($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $err = curl_error($ch);
        curl_multi_remove_handle($mh, $ch); curl_close($ch);
        $j = json_decode((string)$res, true);
        if ($code !== 200 || !is_array($j) || empty($j['choices'])) {
            $results[] = ['id' => $iid, 'ok' => false, 'error' => 'AI: ' . (is_array($j) ? (string)($j['error']['message'] ?? ('HTTP ' . $code)) : ($err !== '' ? $err : 'HTTP ' . $code))];
            continue;
        }
        $n++;
        $tin += (int)($j['usage']['prompt_tokens'] ?? 0); $tout += (int)($j['usage']['completion_tokens'] ?? 0);
        if (isset($j['usage']['cost']) && is_numeric($j['usage']['cost'])) $cost += (float)$j['usage']['cost'];
        $ans = $j['choices'][0]['message']['content'] ?? '';
        if (is_array($ans)) { $tx = ''; foreach ($ans as $seg) $tx .= is_array($seg) ? ($seg['text'] ?? '') : (string)$seg; $ans = $tx; }
        $p = clsParse($ans, $idList);
        $results[] = $p ? (['id' => $iid, 'ok' => true] + $p) : ['id' => $iid, 'ok' => false, 'used' => true, 'error' => 'jawaban tak terbaca'];
    }
    curl_multi_close($mh);
    $r = $n ? clsUsageAdd($tid, $n, $tin, $tout, $cost) : $use;
    $quota['used'] = (int)($r['n'] ?? $quota['used']);
    return [200, ['ok' => true, 'results' => $results, 'quota' => $quota]];
}
