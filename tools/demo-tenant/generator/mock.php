<?php
// Mock: OpenRouter (/ai), WAHA (/api/*), pusat (/backend/index.php)
$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$raw = file_get_contents('php://input');
$in = json_decode($raw, true) ?: [];
header('Content-Type: application/json');
@file_put_contents(__DIR__ . '/mock.log', date('c') . " $uri " . substr($raw, 0, 300) . "\n", FILE_APPEND);
if ($uri === '/ai') {
    $msgs = $in['messages'] ?? [];
    $last = '';
    for ($i = count($msgs) - 1; $i >= 0; $i--) if (($msgs[$i]['role'] ?? '') === 'user') { $c = $msgs[$i]['content']; $last = is_array($c) ? json_encode($c) : (string)$c; break; }
    $sys = json_encode($msgs[0]['content'] ?? '');
    if (strpos($raw, 'Anda menganalisa transkrip') !== false) {
        $reply = @file_get_contents(__DIR__ . '/lead-next.json') ?: '{"nama":"","kebutuhan":"","waktu":"","anggaran":"","ringkasan":""}';
        echo json_encode(['id' => 'gen-x', 'choices' => [['message' => ['role' => 'assistant', 'content' => $reply], 'finish_reason' => 'stop']], 'usage' => ['prompt_tokens' => 900, 'completion_tokens' => 80, 'total_tokens' => 980, 'cost' => 0.0003]]);
        exit;
    }
    if (strpos($raw, 'Anda adalah Nadia') === false) { file_put_contents(__DIR__ . '/mock-other.log', substr($raw, 0, 1500) . "\n---\n", FILE_APPEND); }
    $q = @json_decode(@file_get_contents(__DIR__ . '/ai-queue.json'), true) ?: [];
    $reply = null;
    if ($q) { $reply = array_shift($q); file_put_contents(__DIR__ . '/ai-queue.json', json_encode($q)); }
    if ($reply === null) $reply = 'Baik Kak, terima kasih. Ada lagi yang bisa kami bantu?';
    echo json_encode(['id' => 'gen-' . uniqid(), 'model' => 'google/gemini-2.5-flash', 'choices' => [['message' => ['role' => 'assistant', 'content' => $reply], 'finish_reason' => 'stop']],
        'usage' => ['prompt_tokens' => 1800 + rand(0, 600), 'completion_tokens' => 60 + rand(0, 90), 'total_tokens' => 2000, 'cost' => 0.0007]]);
    exit;
}
if (strpos($uri, '/backend/index.php') === 0) {
    echo json_encode(['ok' => true, 'license' => ['status' => 'active', 'message' => '', 'expires_at' => ''], 'license_status' => 'active', 'update_available' => false,
        'cap_info' => ['cap_reached' => false, 'cap_warning' => false, 'usage_pct' => 1, 'tier' => 'pro', 'monthly_chat_cap' => 0, 'chats_this_month' => 0,
            'max_agents' => 10, 'max_supervisors' => 3, 'white_label' => false, 'topic_scan_quota' => 10, 'max_wa_numbers' => 2, 'max_business_units' => 3, 'classify_quota' => 2000]]);
    exit;
}
if (strpos($uri, '/api/') === 0) {
    if (preg_match('#/api/sessions/[^/]+$#', $uri) || preg_match('#/api/sessions#', $uri)) { echo json_encode(['name' => 'dei-demo', 'status' => 'WORKING', 'me' => ['id' => '6281100000001@c.us', 'pushName' => 'Nusa EV']]); exit; }
    echo json_encode(['id' => 'true_' . ($in['chatId'] ?? 'x') . '_3EB0' . strtoupper(bin2hex(random_bytes(8))), 'ack' => 1, 'timestamp' => time()]);
    exit;
}
echo json_encode(['ok' => true]);
