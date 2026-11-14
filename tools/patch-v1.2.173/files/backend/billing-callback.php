<?php
/* v1.2.173 — Callback Duitku untuk pembayaran mandiri chatbot (POST x-www-form-urlencoded).
   Satu-satunya sumber status "lunas" selain cek status manual. Duitku mengulang (maks 5x) bila tidak dapat HTTP 200. */
date_default_timezone_set('Asia/Jakarta');
require_once __DIR__ . '/signup-lib.php';
require_once __DIR__ . '/classify-lib.php';
require_once __DIR__ . '/billing-lib.php';
header('Content-Type: text/plain; charset=UTF-8');

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') { http_response_code(405); exit('Method not allowed'); }
$p = $_POST;
$id = (string)($p['merchantOrderId'] ?? '');
blLog('callback ' . $id . ' result=' . ($p['resultCode'] ?? '') . ' amount=' . ($p['amount'] ?? '') . ' ref=' . ($p['reference'] ?? ''));

if (!blCallbackValid($p)) { http_response_code(400); blLog("callback DITOLAK (signature) $id"); exit('Bad signature'); }
$o = blOrderLoad($id);
if (!$o) { http_response_code(404); blLog("callback order tidak ada $id"); exit('Order not found'); }
if ((int)($p['amount'] ?? 0) !== (int)$o['amount']) { http_response_code(400); blLog("callback DITOLAK (nominal) $id {$p['amount']} != {$o['amount']}"); exit('Amount mismatch'); }

$info = ['reference' => (string)($p['reference'] ?? ''), 'paymentCode' => (string)($p['paymentCode'] ?? ''), 'resultCode' => (string)($p['resultCode'] ?? ''),
         'settlementDate' => (string)($p['settlementDate'] ?? ''), 'source' => 'callback'];
if (($p['resultCode'] ?? '') === '00') blMarkPaid($id, $info);
elseif (($o['status'] ?? '') === 'pending') { $o['status'] = 'failed'; $o['payment'] = $info; blOrderSave($o); }
http_response_code(200);
echo 'OK';
