#!/usr/bin/env python3
"""v1.2.168 kuota-unit (PUSAT): batas Unit Bisnis per paket.
Growth 3 · Business 5 · Pro 10 · Starter/Trial 0 · Custom/Enterprise = atur manual (max_business_units).
Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
P = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-pusat')
LIB = P + '/backend/classify-lib.php'; IDX = P + '/backend/index.php'; CRON = P + '/backend/cron-tick.php'; ADM = P + '/admin/index.html'
TAG = 'v1.2.168: kuota-unit'; stamp = time.strftime('%Y%m%d-%H%M%S')
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label):
    n = s.count(old); assert n == 1, '%s: anchor %d kali' % (label, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    shutil.copy2(p, p + '.bak-v12168-' + stamp); wr(p, fn(s)); print('OK', p)

def lib(s):
    return rep(s, "function waNumQuota($t) {", """// v1.2.168: kuota-unit — jumlah Unit Bisnis per paket. max_business_units > 0 = timpa manual (Custom/Enterprise); trial = 0.
function buTierMax() { return ['starter' => 0, 'growth' => 3, 'business' => 5, 'pro' => 10, 'custom' => 0, 'enterprise' => 0]; }
function buQuota($t) {
    if (!is_array($t)) return 0;
    $own = (int)($t['max_business_units'] ?? 0);
    if ($own > 0) return min(50, $own);
    if (is_array($t['trial'] ?? null) || strtolower((string)($t['tier'] ?? '')) === 'trial') return 0;
    return buTierMax()[strtolower((string)($t['tier'] ?? ''))] ?? 0;
}
function waNumQuota($t) {""", 'lib')

def idx(s):
    s = rep(s, "'max_wa_numbers'       => waNumQuota($tenant),",
               "'max_wa_numbers'       => waNumQuota($tenant),\n                'max_business_units'   => buQuota($tenant),   // " + TAG, 'cap_info')
    s = rep(s, "$tt['max_wa_eff'] = waNumQuota($tt);", "$tt['max_wa_eff'] = waNumQuota($tt); $tt['max_bu_eff'] = buQuota($tt);   /* " + TAG + " */", 'list')
    s = rep(s, "'wa_numbers' => (int)($se['wa_numbers'] ?? 0), 'max_wa_numbers' => (int)($se['max_wa_numbers'] ?? 0),",
               "'wa_numbers' => (int)($se['wa_numbers'] ?? 0), 'max_wa_numbers' => (int)($se['max_wa_numbers'] ?? 0),\n                         'business_units' => isset($se['business_units']) ? (int)$se['business_units'] : null, 'max_business_units' => isset($se['max_business_units']) ? (int)$se['max_business_units'] : null,   // " + TAG, 'stats')
    s = rep(s, "        if ($maxWa !== null && ($maxWa < 0 || $maxWa > 20)) jsonOut(['ok' => false, 'error' => 'Nomor WA tambahan harus 0..20.'], 400);",
               "        if ($maxWa !== null && ($maxWa < 0 || $maxWa > 20)) jsonOut(['ok' => false, 'error' => 'Nomor WA tambahan harus 0..20.'], 400);\n"
               "        $maxBu = array_key_exists('max_business_units', $in) ? (int)$in['max_business_units'] : null;   // " + TAG + "\n"
               "        if ($maxBu !== null && ($maxBu < 0 || $maxBu > 50)) jsonOut(['ok' => false, 'error' => 'Unit bisnis harus 0..50.'], 400);", 'seats-in')
    s = rep(s, "                $maxWaEff = waNumQuota($t);   // v1.2.162: nomor-paket",
               "                $maxWaEff = waNumQuota($t);   // v1.2.162: nomor-paket\n"
               "                if ($maxBu !== null) $t['max_business_units'] = $maxBu;   // " + TAG + "\n"
               "                $maxBuEff = buQuota($t);", 'seats-set')
    s = rep(s, "'max_wa_numbers' => $maxWaOut ?? 0, 'max_wa_eff' => $maxWaEff ?? 0]);",
               "'max_wa_numbers' => $maxWaOut ?? 0, 'max_wa_eff' => $maxWaEff ?? 0, 'max_bu_eff' => $maxBuEff ?? 0]);   // " + TAG, 'seats-out')
    return s

def cron(s):
    return rep(s, "'max_wa_numbers' => waNumQuota($t), 'tier' =>", "'max_wa_numbers' => waNumQuota($t), 'max_business_units' => buQuota($t) /* " + TAG + " */, 'tier' =>", 'cron')

def adm(s):
    s = rep(s, "    return ` <span class=\"badge ${cls}\" title=\"Nomor WhatsApp tambahan terpakai / batas paket\">W ${u == null ? '–' : u}/${mw}</span>`; })();",
               "    return ` <span class=\"badge ${cls}\" title=\"Nomor WhatsApp tambahan terpakai / batas paket\">W ${u == null ? '–' : u}/${mw}</span>`; })();\n"
               "  const mb = t.max_bu_eff ?? 0;   // " + TAG + "\n"
               "  const bPart = (()=>{ const u = se && se.business_units != null ? se.business_units : null;\n"
               "    if (!mb && !u) return '';\n"
               "    const cls = u == null ? 'idle' : (u > mb ? 'off' : (u >= mb ? 'idle' : 'ok'));\n"
               "    return ` <span class=\"badge ${cls}\" title=\"Unit bisnis terpakai / batas paket\">U ${u == null ? '–' : u}/${mb}</span>`; })();", 'badge')
    s = rep(s, "${part(se?se.supervisors:null, ms, 'S')}${wPart}${sync}", "${part(se?se.supervisors:null, ms, 'S')}${wPart}${bPart}${sync}", 'badge2')
    s = rep(s, "Nomor yang terakhir ditambahkan terkunci lebih dulu bila batas diturunkan.</div>\n        </div>",
               "Nomor yang terakhir ditambahkan terkunci lebih dulu bila batas diturunkan.</div>\n        </div>\n"
               "        <div class=\"row\" style=\"gap:8px;margin-top:8px\"><!-- " + TAG + " -->\n"
               "          <div style=\"flex:1\"><label>Unit bisnis</label><input id=\"s_max_bu\" type=\"number\" min=\"0\" max=\"50\" placeholder=\"ikut paket\" value=\"${(t.max_business_units ?? 0) > 0 ? t.max_business_units : ''}\"></div>\n"
               "          <div style=\"flex:1;align-self:end\" class=\"hint\">Kosong/0 = ikut paket (Growth 3 · Business 5 · Pro 10 · Starter/Trial/Custom 0); isi angka untuk menimpa (Enterprise: sesuai kebutuhan). Berlaku sekarang: <b>${t.max_bu_eff ?? 0}</b>. ${se && se.business_units != null ? 'Terpakai: <b>' + se.business_units + '</b>.' : 'Pemakaian tampil setelah tenant v1.2.168.'} Unit yang terakhir ditambahkan nonaktif lebih dulu bila batas diturunkan.</div>\n"
               "        </div>", 'modal')
    s = rep(s, "  if(isNaN(w) || w<0 || w>20){ toast('Nomor WA tambahan harus 0..20.',true); return; }",
               "  if(isNaN(w) || w<0 || w>20){ toast('Nomor WA tambahan harus 0..20.',true); return; }\n"
               "  const b = $('#s_max_bu').value.trim()==='' ? 0 : parseInt($('#s_max_bu').value, 10);   // " + TAG + "\n"
               "  if(isNaN(b) || b<0 || b>50){ toast('Unit bisnis harus 0..50.',true); return; }", 'save1')
    s = rep(s, "max_supervisors:s, max_wa_numbers:w}})", "max_supervisors:s, max_wa_numbers:w, max_business_units:b}})", 'save2')
    s = rep(s, "+(res.max_wa_eff ?? res.max_wa_numbers)+' nomor WA tambahan'); closeModal();",
               "+(res.max_wa_eff ?? res.max_wa_numbers)+' nomor WA tambahan / '+(res.max_bu_eff ?? 0)+' unit bisnis'); closeModal();", 'save3')
    for o, n in [("· +2 nomor WA</option>", "· +2 nomor WA · 3 unit</option>"), ("· +4 nomor WA</option>", "· +4 nomor WA · 5 unit</option>"), ("· +9 nomor WA</option>", "· +9 nomor WA · 10 unit</option>")]:
        s = rep(s, o, n, o)
    return s

patch(LIB, lib); patch(IDX, idx); patch(CRON, cron); patch(ADM, adm)
