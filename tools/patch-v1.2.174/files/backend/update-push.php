<?php
/**
 * v1.2.174: update-dari-pusat — CLI: pasang rilis terbaru ke tenant dari server pusat.
 *   php backend/update-push.php all=1             -> semua tenant aktif yang tertinggal
 *   php backend/update-push.php only=pomeloteljkt -> satu tenant
 */
if (PHP_SAPI !== 'cli') { http_response_code(403); exit('CLI only'); }
date_default_timezone_set('Asia/Jakarta');
$args = [];
parse_str(implode('&', array_slice($argv, 1)), $args);
if (empty($args['all']) && empty($args['only'])) { fwrite(STDERR, "pakai: all=1 | only=<tenant_id>\n"); exit(1); }
define('DEI_PUSAT_CLI_LIB', true);
require __DIR__ . '/index.php';   // index.php berhenti sebelum routing saat konstanta ini ada
$latest = latestVersion();
if (!$latest) { echo "Belum ada rilis.\n"; exit(1); }
$cron = readJson(DATA_DIR . '/cron-status.json', []);
$only = tidNorm((string)($args['only'] ?? ''));
$fail = 0;
foreach (readJson(TENANTS_FILE, []) as $t) {
    $tid = tidNorm((string)($t['tenant_id'] ?? ''));
    if ($tid === '' || ($only !== '' && $tid !== $only)) continue;
    if ($only === '' && (empty($t['active']) || puVerCmp(puVerOf($t, $cron) ?: 'v0.0.0', $latest) >= 0)) continue;
    $r = puPushOne($t, $latest, $cron, 'cli');
    if (empty($r['ok'])) $fail++;
    echo str_pad($tid, 22) . (empty($r['ok']) ? 'GAGAL  ' . ($r['error'] ?? '') : 'OK     ' . ($r['message'] ?? '')) . (isset($r['via']) ? '  [' . $r['via'] . ']' : '') . "\n";
}
echo "Selesai — target $latest" . ($fail ? ", $fail gagal" : '') . ".\n";
exit($fail ? 2 : 0);
