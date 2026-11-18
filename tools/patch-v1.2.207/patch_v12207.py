#!/usr/bin/env python3
"""v1.2.207 (hapus-lead): tombol Hapus lead di menu Leads (daftar & kanban), SPV ke atas.
Lead yang dihapus tidak dibuat ulang otomatis oleh analisa 8 pesan (data/leads-hidden.json);
Analisa manual dari chat membuatnya lagi. Kontak, chat, tag sales tidak disentuh.
Butuh v1.2.206. Idempoten.  Pakai: patch_v12207.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.207: hapus-lead'; NEED = 'v1.2.206: sales-lead'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12207-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ============================== API ==============================
s = rd(API)
assert NEED in s, 'v1.2.206 belum terpasang'
if TAG not in s:
    s = rep(s, "define('DEI_VERSION', 'v1.2.206');   // v1.2.206:",
            "define('DEI_VERSION', 'v1.2.207');   // " + TAG + " — hapus kartu lead (SPV+), tidak dibuat ulang otomatis; v1.2.206:", what='DEI_VERSION')
    s = rep(s, "define('LEADS_FILE', DATA_DIR . '/leads.json');           // v1.2.20: kartu lead hasil analisa AI\n",
            "define('LEADS_FILE', DATA_DIR . '/leads.json');           // v1.2.20: kartu lead hasil analisa AI\n"
            "define('LEADS_HIDDEN_FILE', DATA_DIR . '/leads-hidden.json');   // " + TAG + ": nomor yang lead-nya dihapus -> analisa otomatis dilewati\n", what='LEADS_FILE')
    ONCE = "    if (!$force && isset($all[$number]) && (string)($all[$number]['analyzed_at'] ?? '') !== '') return false;   // sudah punya kartu -> sekali saja (v1.2.206: sales-lead: lead dari tag/PO tanpa analisa tetap dianalisa)\n"
    s = rep(s, ONCE, ONCE +
            "    if (!$force && !isset($all[$number])) { $hdn207 = readJson(LEADS_HIDDEN_FILE, []); if (is_array($hdn207) && isset($hdn207[$number])) return false; }   // " + TAG + ": lead dihapus -> tidak dibuat ulang otomatis\n", what='lead once')
    s = rep(s, "    foreach (['sales', 'closed_ts', 'src'] as $slK203) if (isset($lama[$slK203])) $all[$number][$slK203] = $lama[$slK203];   // v1.2.203: sales-tag\n    writeJson(LEADS_FILE, $all);\n    return true;\n}\n",
            "    foreach (['sales', 'closed_ts', 'src'] as $slK203) if (isset($lama[$slK203])) $all[$number][$slK203] = $lama[$slK203];   // v1.2.203: sales-tag\n    writeJson(LEADS_FILE, $all);\n"
            "    if ($force) deiWithLock('leads-hidden', function () use ($number) {   // " + TAG + ": analisa manual = lead dipakai lagi\n"
            "        $h = readJson(LEADS_HIDDEN_FILE, []);\n"
            "        if (is_array($h) && isset($h[$number])) { unset($h[$number]); writeJson(LEADS_HIDDEN_FILE, $h); }\n"
            "    });\n"
            "    return true;\n}\n", what='lead write')
    s = rep(s, "    case 'analyze_lead': {\n",
            "    case 'delete_lead': {   // " + TAG + "\n"
            "        $u = requireAuth(['super_admin', 'admin', 'supervisor']);\n"
            "        $num = preg_replace('/\\D/', '', (string)(bodyInput()['number'] ?? ''));\n"
            "        if ($num === '') jsonOut(['ok' => false, 'error' => 'Nomor tidak valid.'], 400);\n"
            "        deiGuardSpvScope($u, $num);\n"
            "        $gone = deiWithLock('leads', function () use ($num) {\n"
            "            $all = leadsGetAll();\n"
            "            if (!isset($all[$num])) return false;\n"
            "            unset($all[$num]);\n"
            "            writeJson(LEADS_FILE, $all);\n"
            "            return true;\n"
            "        });\n"
            "        if (!$gone) jsonOut(['ok' => false, 'error' => 'Lead tidak ditemukan.'], 404);\n"
            "        deiWithLock('leads-hidden', function () use ($num, $u) {\n"
            "            $h = readJson(LEADS_HIDDEN_FILE, []);\n"
            "            if (!is_array($h)) $h = [];\n"
            "            $h[$num] = ['at' => date('Y-m-d H:i:s'), 'by' => (string)($u['username'] ?? '')];\n"
            "            writeJson(LEADS_HIDDEN_FILE, $h);\n"
            "        });\n"
            "        jsonOut(['ok' => true]);\n"
            "        break;\n"
            "    }\n\n"
            "    case 'analyze_lead': {\n", what='analyze_lead')
    save(API, s)
else: print('sudah', API)

# ============================== HTML ==============================
s = rd(HT)
if TAG not in s:
    s = rep(s, '<script src="app.js?v=1.2.206"></script><!-- v1.2.206: sales-lead -->',
            '<script src="app.js?v=1.2.207"></script><!-- ' + TAG + ' --><!-- v1.2.206: sales-lead -->', what='app.js?v')
    s = rep(s, "  .lk-card .lk-chat{border:1px solid var(--line);background:#fff;border-radius:7px;padding:4px 7px;cursor:pointer;color:var(--brand);display:inline-flex}\n",
            "  .lk-card .lk-chat{border:1px solid var(--line);background:#fff;border-radius:7px;padding:4px 7px;cursor:pointer;color:var(--brand);display:inline-flex}\n"
            "  .lk-card .lk-del{border:1px solid #fecaca;background:#fff;border-radius:7px;padding:4px 7px;cursor:pointer;color:#dc2626;display:inline-flex}/* " + TAG + " */\n", what='lk css')
    save(HT, s)
else: print('sudah', HT)

# ============================== JS ==============================
s = rd(JS)
if TAG not in s:
    s = rep(s, "          (user.role === 'wa_agent' ? '' : '<button class=\"btn ghost sm lead-reanalyze\">Analisa ulang</button>') +\n",
            "          (user.role === 'wa_agent' ? '' : '<button class=\"btn ghost sm lead-reanalyze\">Analisa ulang</button>') +\n"
            "          (user.role === 'wa_agent' ? '' : '<button class=\"btn danger sm lead-del\" style=\"margin-left:auto\">' + ico('trash-2', 14) + ' Hapus lead</button>') +   // " + TAG + "\n", what='list btn')
    s = rep(s, "          else toast((r && r.error) || 'Analisa gagal.', true);\n        });\n      };\n    });\n  }\n\n  // v1.2.147: leads-kanban",
            "          else toast((r && r.error) || 'Analisa gagal.', true);\n        });\n      };\n"
            "      var btnDel = card.querySelector('.lead-del');   // " + TAG + "\n"
            "      if (btnDel) btnDel.onclick = function () { deleteLead207(num); };\n"
            "    });\n  }\n\n  // v1.2.147: leads-kanban", what='list handler')
    s = rep(s, "              '<button type=\"button\" class=\"lk-chat\" title=\"Lihat percakapan\">' + ico('message-circle', 14) + '</button></div>' +\n",
            "              '<button type=\"button\" class=\"lk-chat\" title=\"Lihat percakapan\">' + ico('message-circle', 14) + '</button>' +\n"
            "              (user.role === 'wa_agent' ? '' : '<button type=\"button\" class=\"lk-del\" title=\"Hapus lead\">' + ico('trash-2', 14) + '</button>') + '</div>' +   // " + TAG + "\n", what='kanban btn')
    s = rep(s, "      c.querySelector('.lk-chat').onclick = function () { openLeadConv(num); };\n",
            "      c.querySelector('.lk-chat').onclick = function () { openLeadConv(num); };\n"
            "      var kd = c.querySelector('.lk-del'); if (kd) kd.onclick = function () { deleteLead207(num); };   // " + TAG + "\n", what='kanban handler')
    s = rep(s, "  function saveLead(num, body) {\n",
            "  // " + TAG + " — hapus kartu lead saja; kontak, percakapan, tag sales tetap\n"
            "  function deleteLead207(num) {\n"
            "    var l = leadData.filter(function (x) { return x.number === num; })[0] || {};\n"
            "    var nm = l.name ? l.name + ' (+' + num + ')' : '+' + num;\n"
            "    if (!confirm('Hapus lead ' + nm + '?\\n\\nKartu lead dan hasil analisanya hilang. Kontak, percakapan, dan tag sales tidak ikut terhapus.\\nLead ini tidak dibuat ulang otomatis; bisa dianalisa lagi manual dari chat.')) return;\n"
            "    api('delete_lead', { method: 'POST', body: { number: num } }).then(function (r) {\n"
            "      if (r && r.ok) {\n"
            "        toast('Lead dihapus.');\n"
            "        delete leadOpenState[num];\n"
            "        fetchLeads();\n"
            "        if (typeof fetchWaConvs === 'function') { try { fetchWaConvs(); } catch (e) {} }\n"
            "      } else toast((r && r.error) || 'Gagal menghapus lead.', true);\n"
            "    });\n"
            "  }\n\n"
            "  function saveLead(num, body) {\n", what='saveLead')
    save(JS, s)
else: print('sudah', JS)
print('patch v1.2.207 selesai')
