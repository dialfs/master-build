#!/usr/bin/env python3
"""v1.2.172 trial-paket (PUSAT): trial bisa memakai paket Starter atau Growth (maksimal Growth).
Kuota fitur (klasifikasi topik, nomor WA tambahan, unit bisnis, balasan AI) ikut paket yang dicoba.
Admin: ganti paket trial, kembalikan tenant yang terlanjur dijadikan berbayar ke status trial,
paket trial bawaan pendaftar. Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
P = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-pusat')
CLS = P + '/backend/classify-lib.php'; SU = P + '/backend/signup-lib.php'; IDX = P + '/backend/index.php'; ADM = P + '/admin/index.html'
TAG = 'v1.2.172: trial-paket'; stamp = time.strftime('%Y%m%d-%H%M%S')
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    shutil.copy2(p, p + '.bak-v12172-' + stamp); wr(p, fn(s)); print('OK', p)
TRIAL_LINE = "    if (is_array($t['trial'] ?? null) || strtolower((string)($t['tier'] ?? '')) === 'trial') return 0;\n"

def cls(s):
    s = rep(s, "function clsTierQuotas() {",
        "// " + TAG + " — trial mencoba paket Starter atau Growth (maksimal Growth); kuota fitur ikut paket yang dicoba.\n"
        "if (!defined('TRIAL_GROWTH_CAP')) define('TRIAL_GROWTH_CAP', 2000);   // balasan AI trial Growth = kuota paket Growth\n"
        "function isTrialTenant($t) { return is_array($t) && (is_array($t['trial'] ?? null) || strtolower((string)($t['tier'] ?? '')) === 'trial'); }\n"
        "// Paket yang dicoba selama trial: trial.tier, atau tier yang diubah manual saat masih trial. Di atas Growth dibatasi ke Growth.\n"
        "function trialTier($t) {\n"
        "    $v = strtolower((string)(is_array($t['trial'] ?? null) ? ($t['trial']['tier'] ?? '') : ''));\n"
        "    if ($v === '') $v = strtolower((string)($t['tier'] ?? ''));\n"
        "    return in_array($v, ['growth', 'business', 'pro', 'custom', 'enterprise'], true) ? 'growth' : 'starter';\n"
        "}\n"
        "// Paket untuk menghitung kuota fitur.\n"
        "function featTier($t) { return isTrialTenant($t) ? trialTier($t) : strtolower((string)($t['tier'] ?? '')); }\n"
        "function trialNoGrowth($t) { return isTrialTenant($t) && trialTier($t) !== 'growth'; }\n"
        "function clsTierQuotas() {", 'helper')
    # clsQuota
    s = rep(s, TRIAL_LINE + "    if (array_key_exists('classify_quota', $t)",
               "    if (trialNoGrowth($t)) return 0;   // " + TAG + "\n    if (array_key_exists('classify_quota', $t)", 'cls trial')
    s = rep(s, "    return clsTierQuotas()[strtolower((string)($t['tier'] ?? ''))] ?? 0;",
               "    return clsTierQuotas()[featTier($t)] ?? 0;", 'cls tier')
    # buQuota
    s = rep(s, TRIAL_LINE + "    return buTierMax()[strtolower((string)($t['tier'] ?? ''))] ?? 0;",
               "    if (trialNoGrowth($t)) return 0;   // " + TAG + "\n    return buTierMax()[featTier($t)] ?? 0;", 'bu')
    # waNumQuota
    s = rep(s, TRIAL_LINE + "    $own = (int)($t['max_wa_numbers'] ?? 0);",
               "    if (trialNoGrowth($t)) return 0;   // " + TAG + "\n    $own = (int)($t['max_wa_numbers'] ?? 0);", 'wa trial')
    s = rep(s, "    return waNumTierMax()[strtolower((string)($t['tier'] ?? ''))] ?? 0;",
               "    return waNumTierMax()[featTier($t)] ?? 0;", 'wa tier')
    return s

def su(s):
    s = rep(s, "        'trial_cap'        => 500,\n",
               "        'trial_cap'        => 500,\n        'trial_tier'       => 'starter',   // " + TAG + " — starter | growth (maks Growth)\n", 'default')
    s = rep(s, "    $c['trial_cap']  = max(1, min(100000, (int)$c['trial_cap']));\n",
               "    $c['trial_cap']  = max(1, min(100000, (int)$c['trial_cap']));\n"
               "    $c['trial_tier'] = strtolower((string)$c['trial_tier']) === 'growth' ? 'growth' : 'starter';   // " + TAG + "\n", 'norm')
    s = rep(s, "function suTrialPayload(array $t): ?array {",
               "/** " + TAG + " — kuota balasan AI trial: Growth minimal sama dengan kuota paket Growth. */\n"
               "function suTrialCap(array $t): int {\n"
               "    $c = (int)($t['trial']['cap'] ?? 500);\n"
               "    return trialTier($t) === 'growth' ? max($c, TRIAL_GROWTH_CAP) : $c;\n"
               "}\n"
               "function suTrialPayload(array $t): ?array {", 'cap fn')
    s = rep(s, "    return ['start' => (int)($tr['start'] ?? 0), 'ends' => (int)$tr['ends'], 'cap' => (int)($tr['cap'] ?? 500),\n"
               "            'upgrade_url' => (string)($cfg['upgrade_url'] ?? '')];",
               "    return ['start' => (int)($tr['start'] ?? 0), 'ends' => (int)$tr['ends'], 'cap' => suTrialCap($t),\n"
               "            'upgrade_url' => (string)($cfg['upgrade_url'] ?? ''), 'tier' => trialTier($t)];   // " + TAG, 'payload')
    s = rep(s, "        $trial = ['start' => $now, 'ends' => $now + $cfg['trial_days'] * 86400, 'cap' => (int)$cfg['trial_cap'], 'days' => (int)$cfg['trial_days']];",
               "        $trial = ['start' => $now, 'ends' => $now + $cfg['trial_days'] * 86400, 'cap' => (int)$cfg['trial_cap'], 'days' => (int)$cfg['trial_days'],\n"
               "                  'tier' => $cfg['trial_tier']];   // " + TAG + "\n"
               "        if ($trial['tier'] === 'growth') $trial['cap'] = max($trial['cap'], TRIAL_GROWTH_CAP);", 'provision')
    s = rep(s, "'trial' => ['start' => $trial['start'], 'ends' => $trial['ends'], 'cap' => $trial['cap'], 'upgrade_url' => (string)$cfg['upgrade_url']]];",
               "'trial' => ['start' => $trial['start'], 'ends' => $trial['ends'], 'cap' => $trial['cap'], 'upgrade_url' => (string)$cfg['upgrade_url'], 'tier' => $trial['tier']]];", 'cache')
    s = rep(s, "$cap = (int)($tr['cap'] ?? 0);", "$cap = suTrialCap($t);   // " + TAG, 'reminder')
    if "require_once __DIR__ . '/classify-lib.php'" not in s:
        s = rep(s, "/* ---------- trial ---------- */", "require_once __DIR__ . '/classify-lib.php';   // " + TAG + " — trialTier()\n/* ---------- trial ---------- */", 'require')
    return s

def idx(s):
    s = rep(s, "                $capInfo['trial'] = $tp;\n",
               "                $capInfo['trial'] = $tp;\n                $capInfo['trial_tier'] = $tp['tier'] ?? 'starter';   // " + TAG + "\n", 'capinfo')
    # trial_update: op set_tier & revert
    s = rep(s, "            if (!is_array($t['trial'] ?? null)) jsonOut(['ok' => false, 'error' => 'Tenant ini bukan trial.'], 400);\n            if ($op === 'extend') {",
        "            // " + TAG + " — revert: tenant yang terlanjur dijadikan berbayar kembali ke trial (paket maks Growth)\n"
        "            if ($op === 'revert') {\n"
        "                if (is_array($t['trial'] ?? null)) jsonOut(['ok' => false, 'error' => 'Tenant ini masih trial.'], 400);\n"
        "                $cfg = suCfg();\n"
        "                $h = is_array($t['trial_history'] ?? null) ? $t['trial_history'] : [];\n"
        "                $rt = strtolower((string)($in['tier'] ?? ''));\n"
        "                if (!in_array($rt, ['starter', 'growth'], true)) $rt = trialTier(['tier' => $t['tier'] ?? '']);\n"
        "                $days = max(1, min(90, (int)($in['days'] ?? 0) ?: 7));\n"
        "                $ends = (int)($h['ends'] ?? 0);\n"
        "                if (!empty($in['days']) || $ends < time() + 86400) $ends = time() + $days * 86400;\n"
        "                $t['trial'] = ['start' => (int)($h['start'] ?? time()), 'ends' => $ends, 'cap' => (int)($h['cap'] ?? $cfg['trial_cap']),\n"
        "                               'days' => (int)($h['days'] ?? $cfg['trial_days']), 'tier' => $rt];\n"
        "                $t['paid_tier_before_revert'] = (string)($t['tier'] ?? '');\n"
        "                $t['tier'] = 'trial'; $t['reverted_at'] = gmdate('Y-m-d H:i:s');\n"
        "                $t['monthly_chat_cap'] = suTrialCap($t);\n"
        "                if ($rt === 'growth') $t['monthly_cost_cap_usd'] = 6;\n"
        "                unset($t['trial_history'], $t['converted_at']);\n"
        "                $msg = 'Tenant kembali trial paket ' . ucfirst($rt) . ' sampai ' . gmdate('d-m-Y', $ends + 7 * 3600) . '.';\n"
        "                $found = true; break;\n"
        "            }\n"
        "            if (!is_array($t['trial'] ?? null)) jsonOut(['ok' => false, 'error' => 'Tenant ini bukan trial.'], 400);\n"
        "            if ($op === 'set_tier') {   // " + TAG + "\n"
        "                $nt = strtolower((string)($in['tier'] ?? ''));\n"
        "                if (!in_array($nt, ['starter', 'growth'], true)) jsonOut(['ok' => false, 'error' => 'Trial maksimal paket Growth.'], 400);\n"
        "                $t['trial']['tier'] = $nt; $t['tier'] = 'trial';\n"
        "                $t['monthly_chat_cap'] = suTrialCap($t);\n"
        "                $msg = 'Paket trial kini ' . ucfirst($nt) . ' (' . suTrialCap($t) . ' balasan AI).';\n"
        "            } elseif ($op === 'extend') {", 'trial_update')
    # set_cap: tenant trial maksimal Growth
    s = rep(s, "            if (tidEq($t['tenant_id'] ?? '', $id)) {\n                $t['tier']                 = $tier;\n",
        "            if (tidEq($t['tenant_id'] ?? '', $id)) {\n"
        "                if (is_array($t['trial'] ?? null)) {   // " + TAG + " — tenant trial: tier = paket yang dicoba, maks Growth\n"
        "                    if (!in_array($tier, ['trial', 'starter', 'growth'], true)) jsonOut(['ok' => false, 'error' => 'Tenant ini masih trial — trial maksimal paket Growth. Untuk paket di atasnya, pakai \"Jadikan berbayar\".'], 400);\n"
        "                    if ($tier === 'growth') $t['trial']['tier'] = 'growth';   // starter/trial = paket trial tidak diubah (turunkan lewat kotak Trial)\n"
        "                    $tier = 'trial';\n"
        "                }\n"
        "                $t['tier']                 = $tier;\n", 'set_cap')
    return s

def adm(s):
    s = rep(s, "      <div style=\"flex:1;min-width:200px\"><label>Maks. balasan AI (total trial)</label><input id=\"su_trial_cap\" type=\"number\" min=\"1\" style=\"width:100%\"></div>\n",
        "      <div style=\"flex:1;min-width:200px\"><label>Maks. balasan AI (total trial)</label><input id=\"su_trial_cap\" type=\"number\" min=\"1\" style=\"width:100%\"></div>\n"
        "      <div style=\"flex:1;min-width:200px\"><label>Paket trial</label><select id=\"su_trial_tier\" style=\"width:100%\"><option value=\"starter\">Starter</option><option value=\"growth\">Growth (balasan AI min. 2.000)</option></select></div><!-- " + TAG + " -->\n", 'su field')
    s = rep(s, "const SU_FIELDS = ['trial_days','trial_cap',", "const SU_FIELDS = ['trial_days','trial_cap','trial_tier',", 'su list')
    # detail trial: pilih paket trial
    s = rep(s, "              <button type=\"button\" class=\"ghost\" onclick=\"trialOp('${esc(t.tenant_id)}','extend')\">Perpanjang trial</button>\n",
        "              <button type=\"button\" class=\"ghost\" onclick=\"trialOp('${esc(t.tenant_id)}','extend')\">Perpanjang trial</button>\n"
        "              <select id=\"m_trial_tier\" style=\"width:auto\"><option value=\"starter\" ${ti.tier!=='growth'?'selected':''}>Trial Starter</option><option value=\"growth\" ${ti.tier==='growth'?'selected':''}>Trial Growth</option></select>\n"
        "              <button type=\"button\" class=\"ghost\" onclick=\"trialOp('${esc(t.tenant_id)}','set_tier')\">Simpan paket trial</button><!-- " + TAG + " -->\n", 'detail')
    s = rep(s, "<div style=\"font-weight:700;color:#3730a3;margin-bottom:4px\">Trial ${ti.ended?'berakhir':ti.left+' hari lagi'}",
               "<div style=\"font-weight:700;color:#3730a3;margin-bottom:4px\">Trial ${ti.tier==='growth'?'Growth':'Starter'} · ${ti.ended?'berakhir':ti.left+' hari lagi'}", 'detail head')
    s = rep(s, "        }\n        return h; })()}\n",
        "        } else if(t.trial_history){   // " + TAG + "\n"
        "          const pt=(t.tier||'starter');\n"
        "          h += `<div style=\"background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:12px 14px;margin-bottom:6px\">\n"
        "            <div style=\"font-weight:700;color:#92400e;margin-bottom:4px\">Dulu trial · dijadikan ${esc(pt)}${t.converted_at?' pada '+esc(t.converted_at):''}</div>\n"
        "            <div class=\"hint\" style=\"margin:0 0 8px\">Kalau sebenarnya belum bayar, kembalikan ke status trial. Trial maksimal paket Growth; tanggal selesai lama dipakai bila masih &gt; 1 hari, selain itu diisi hari baru.</div>\n"
        "            <div class=\"row\" style=\"gap:8px\">\n"
        "              <select id=\"m_rev_tier\" style=\"width:auto\"><option value=\"growth\" ${pt!=='starter'?'selected':''}>Trial Growth</option><option value=\"starter\" ${pt==='starter'?'selected':''}>Trial Starter</option></select>\n"
        "              <input id=\"m_rev_days\" type=\"number\" min=\"1\" max=\"90\" placeholder=\"hari (opsional)\" style=\"width:140px\">\n"
        "              <button type=\"button\" onclick=\"trialOp('${esc(t.tenant_id)}','revert')\" style=\"background:#4f46e5\">Kembalikan ke Trial</button>\n"
        "            </div></div>`;\n"
        "        }\n        return h; })()}\n", 'revert box')
    s = rep(s, "  if(op==='convert'){ body.tier=$('#m_conv_tier').value; if(!confirm('Akhiri trial dan jadikan paket '+body.tier+'?')) return; }\n",
        "  if(op==='convert'){ body.tier=$('#m_conv_tier').value; if(!confirm('Akhiri trial dan jadikan paket '+body.tier+'?')) return; }\n"
        "  if(op==='set_tier'){ body.tier=$('#m_trial_tier').value; }   // " + TAG + "\n"
        "  if(op==='revert'){ body.tier=$('#m_rev_tier').value; const d=parseInt($('#m_rev_days').value,10); if(d) body.days=d; if(!confirm('Kembalikan tenant ini ke status trial paket '+body.tier+'?')) return; }\n", 'trialOp')
    s = rep(s, "  return {left, used, cap:tr.cap, ended:left<=0, out: used!=null && used>=tr.cap};",
        "  const tier = String(tr.tier || (['growth','business','pro','custom','enterprise'].includes(String(t.tier||'').toLowerCase()) ? 'growth' : 'starter'));   // " + TAG + "\n"
        "  const tg = ['growth','business','pro','custom','enterprise'].includes(tier) ? 'growth' : 'starter';\n"
        "  const cap = tg==='growth' ? Math.max(tr.cap||0, 2000) : tr.cap;\n"
        "  return {left, used, cap, tier:tg, ended:left<=0, out: used!=null && used>=cap};", 'trialInfo')
    s = rep(s, "${ti.ended?'trial berakhir':'trial '+ti.left+'h'}</span>`:''}",
               "${ti.ended?'trial berakhir':'trial '+(ti.tier==='growth'?'Growth ':'')+ti.left+'h'}</span>`:''}", 'list badge')
    return s

for p, fn in [(CLS, cls), (SU, su), (IDX, idx), (ADM, adm)]:
    patch(p, fn)
