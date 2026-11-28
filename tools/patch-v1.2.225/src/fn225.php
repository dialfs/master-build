/* v1.2.225: es-coex — Embedded Signup coexistence untuk banyak tenant di satu Meta App.
 * deiEsSubscribe: langganan app ke WABA klien + override_callback_uri ke webhook tenant ini,
 *   supaya event WABA itu masuk ke tenant yang benar walau webhook app menunjuk tenant lain.
 * deiEsSmbSync: minta Meta mengirim kontak (smb_app_state_sync) & riwayat chat 6 bulan (history)
 *   dari aplikasi WhatsApp Business. Wajib dalam 24 jam setelah onboarding, hanya bisa sekali. */
function deiEsGraphPost($ver, $path, $token, $body, $json = false) {
    $ch = curl_init('https://graph.facebook.com/' . rawurlencode($ver) . '/' . ltrim($path, '/'));
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true, CURLOPT_POST => true, CURLOPT_TIMEOUT => 25,
        CURLOPT_HTTPHEADER     => array_merge(['Authorization: Bearer ' . $token], $json ? ['Content-Type: application/json'] : []),
        CURLOPT_POSTFIELDS     => $json ? json_encode($body) : (is_array($body) ? http_build_query($body) : (string)$body),
    ]);
    $resp = curl_exec($ch); $hc = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    $d = json_decode((string)$resp, true);
    $err = (is_array($d) && isset($d['error']['message'])) ? (string)$d['error']['message'] : ($resp === false ? 'tidak ada respons' : '');
    return [$hc, $d, $err];
}
function deiEsSubscribe($ver, $waba, $token, $verifyToken) {
    $cb = deiSelfApiUrl();
    $cb = ($cb !== '' && stripos($cb, 'https://') === 0) ? $cb . '?action=wa_webhook' : '';
    if ($cb !== '') {
        list($hc, , $err) = deiEsGraphPost($ver, rawurlencode($waba) . '/subscribed_apps', $token,
            ['override_callback_uri' => $cb, 'verify_token' => $verifyToken]);
        if ($hc >= 200 && $hc < 300) return ['ok' => true, 'override' => $cb];
        error_log('deiEsSubscribe override HTTP ' . $hc . ': ' . $err);
    }
    list($hc, , $err) = deiEsGraphPost($ver, rawurlencode($waba) . '/subscribed_apps', $token, '');
    if ($hc >= 200 && $hc < 300) return ['ok' => true, 'override' => '', 'note' => $cb === '' ? 'Dashboard tidak dibuka lewat HTTPS, webhook WABA ini memakai Callback URL app.' : 'Override webhook gagal, webhook WABA ini memakai Callback URL app.'];
    error_log('deiEsSubscribe HTTP ' . $hc . ': ' . $err);
    return ['ok' => false, 'error' => $err !== '' ? $err : ('HTTP ' . $hc)];
}
function deiEsSmbSync($ver, $pnid, $token) {
    $out = [];
    foreach (['smb_app_state_sync', 'history'] as $t) {
        list($hc, , $err) = deiEsGraphPost($ver, rawurlencode($pnid) . '/smb_app_data', $token,
            ['messaging_product' => 'whatsapp', 'sync_type' => $t], true);
        $out[$t] = ($hc >= 200 && $hc < 300) ? 'ok' : ($err !== '' ? $err : ('HTTP ' . $hc));
        if ($out[$t] !== 'ok') error_log('deiEsSmbSync ' . $t . ' HTTP ' . $hc . ': ' . $err);
    }
    return $out;
}

