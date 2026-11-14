<?php
/**
 * v1.2.174: update-dari-pusat — pusat memasang rilis terbaru ke tenant.
 *
 * Jalur per tenant (versi dari cron-status bila ada, kalau tidak current_version):
 *   v1.2.174+      : POST <api_url>?action=update_remote  (X-Tenant-Id + X-License-Key, sama dengan cron_tick)
 *   v1.2.90–173    : sso_login (akun internal "dei-internal", super admin) -> update_check -> update_apply
 *   < v1.2.90      : tidak bisa dari pusat — update manual sekali dari dashboard tenant.
 * Hasil terakhir disimpan di tenants.json › last_update_push; current_version langsung distempel.
 */
define('PU_MIN_SSO', 'v1.2.90');
define('PU_MIN_REMOTE', 'v1.2.174');

function puVerCmp(string $a, string $b): int { return version_compare(ltrim($a, 'v'), ltrim($b, 'v')); }
function puUrl(string $api, string $action): string { return $api . (strpos($api, '?') === false ? '?' : '&') . 'action=' . $action; }

function puHttp(string $url, array $headers, array $body, int $timeout): array {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => $timeout, CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_FOLLOWLOCATION => true, CURLOPT_MAXREDIRS => 2, CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($body ?: new stdClass()),
        CURLOPT_HTTPHEADER => array_merge(['Content-Type: application/json', 'User-Agent: DEI-Pusat-Update/1.2.174'], $headers),
    ]);
    $raw = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch);
    $j = json_decode((string)$raw, true);
    if (!is_array($j)) {
        $j = ['ok' => false, 'error' => $err !== '' ? $err : ('HTTP ' . $code . ' ' . mb_substr(trim(strip_tags((string)$raw)), 0, 120))];
    } elseif (empty($j['ok']) && empty($j['error'])) {
        $j['error'] = 'HTTP ' . $code;
    }
    $j['_http'] = $code;
    return $j;
}

/** Versi tenant paling akurat: DEI_VERSION dari cron_tick terakhir, kalau tidak ada current_version. */
function puVerOf(array $t, array $cron): string {
    $c = (string)($cron[tidNorm((string)($t['tenant_id'] ?? ''))]['version'] ?? '');
    if (preg_match('/^v\d+\.\d+\.\d+$/', $c)) {
        $cur = (string)($t['current_version'] ?? '');
        return (preg_match('/^v\d+\.\d+\.\d+$/', $cur) && puVerCmp($cur, $c) > 0) ? $cur : $c;
    }
    return (string)($t['current_version'] ?? '');
}

function puStamp(string $tid, array $row): void {
    $tenants = readJson(TENANTS_FILE, []);
    foreach ($tenants as $i => $t) {
        if (!tidEq($t['tenant_id'] ?? '', $tid)) continue;
        if (!empty($row['ok']) && !empty($row['version'])) $tenants[$i]['current_version'] = $row['version'];
        $tenants[$i]['last_update_push'] = $row;
        writeJson(TENANTS_FILE, $tenants);
        return;
    }
}

/** Pasang rilis $latest ke satu tenant. Mengembalikan baris hasil (juga disimpan ke tenants.json). */
function puPushOne(array $t, string $latest, array $cron, string $by = 'pusat'): array {
    $tid  = tidNorm((string)($t['tenant_id'] ?? ''));
    $from = puVerOf($t, $cron);
    $row  = ['tenant_id' => $tid, 'from' => $from, 'target' => $latest, 'at_wib' => wibNowPu(), 'by' => $by];
    $done = function (array $r) use (&$row, $tid) { $row = $r + $row; if (empty($row['skipped'])) puStamp($tid, $row); return $row; };

    if (empty($t['active'])) return $done(['ok' => false, 'error' => 'Tenant nonaktif.', 'skipped' => true]);
    $api = trim((string)($t['api_url'] ?? ''));
    if ($api === '') return $done(['ok' => false, 'error' => 'URL API tenant belum diketahui (isi di Detail).']);
    if ($from !== '' && puVerCmp($from, $latest) >= 0) return $done(['ok' => true, 'skipped' => true, 'version' => $from, 'message' => "Sudah versi terbaru ($from)."]);
    if ($from === '' || puVerCmp($from, PU_MIN_SSO) < 0) {
        return $done(['ok' => false, 'error' => 'Tenant masih ' . ($from ?: 'versi tak dikenal') . ' — update pertama harus manual dari dashboard tenant (butuh v1.2.90+).']);
    }

    if (puVerCmp($from, PU_MIN_REMOTE) >= 0) {
        $row['via'] = 'remote';
        $r = puHttp(puUrl($api, 'update_remote'), ['X-Tenant-Id: ' . $tid, 'X-License-Key: ' . (string)($t['license_key'] ?? '')], [], 160);
    } else {
        $row['via'] = 'sso';
        $r = puHttp(puUrl($api, 'sso_login'), [], ['sso' => suSsoToken($t, 'dei-internal', true, 'Tim DEI (update dari pusat)', 300)], 20);
        if (!empty($r['ok']) && !empty($r['token'])) {
            $ah = ['X-Auth-Token: ' . $r['token']];
            $c = puHttp(puUrl($api, 'update_check'), $ah, [], 40);
            if (empty($c['ok'])) $r = $c;
            elseif (empty($c['update_available'])) $r = ['ok' => true, 'version' => (string)($c['current'] ?? $from), 'updated' => false];
            else $r = puHttp(puUrl($api, 'update_apply'), $ah, ['zip_url' => (string)($c['zip_url'] ?? ''), 'manifest_url' => (string)($c['manifest_url'] ?? ''), 'target' => (string)($c['latest'] ?? '')], 120);
        } elseif (!empty($r['ok'])) {
            $r = ['ok' => false, 'error' => 'Masuk otomatis ke tenant gagal (token kosong).'];
        }
    }

    if (empty($r['ok'])) return $done(['ok' => false, 'error' => (string)($r['error'] ?? 'Gagal.'), 'http' => (int)($r['_http'] ?? 0)]);
    $ver = (string)($r['version'] ?? '');
    $res = ['ok' => true, 'version' => $ver, 'replaced' => count((array)($r['replaced'] ?? []))];
    if (isset($r['updated']) && $r['updated'] === false) {
        $res['message'] = 'Tenant melapor tidak ada pembaruan (terpasang ' . ($ver ?: '?') . ').';
        if ($ver !== '' && puVerCmp($ver, $latest) < 0) { $res['ok'] = false; $res['error'] = $res['message']; }
    } else {
        $res['message'] = $tid . ': ' . ($from ?: '?') . ' → ' . $ver;
    }
    return $done($res);
}

function wibNowPu(): string { return gmdate('Y-m-d H:i:s', time() + 7 * 3600); }
