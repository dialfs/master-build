#!/usr/bin/env python3
"""v1.2.80 — Model AI: Gemini 2.5 Flash-Lite di pilihan model + Model Cadangan dipilih di dashboard.
settings.api.fallback = "" (bawaan: ikut data/server.php 'ai_fallback', bila ada) | "none" | "<provider>:<model>".
Idempoten. Pakai: patch_v1280_ai_fallback.py <root dei-chatbot-ai>"""
import re, sys, pathlib
R = pathlib.Path(sys.argv[1])
api = R/'api/index.php'; html = R/'dashboard/chatbot-ai/index.html'; js = R/'dashboard/chatbot-ai/app.js'
A = api.read_text(encoding='utf-8'); H = html.read_text(encoding='utf-8'); J = js.read_text(encoding='utf-8')
if 'function deiAiFallback(' in A: print('sudah terpasang'); sys.exit(0)
def rep(s, old, new, n=1):
    c = s.count(old)
    if c != n: raise SystemExit(f'ANCHOR {c}x: {old[:80]!r}')
    return s.replace(old, new)
A = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.80');", A, count=1)

# --- api: helper + callClaude memakai helper
A = rep(A, """function callClaude($settings, $systemBlocks, $messages) {
    $r = callClaudeOnce($settings, $systemBlocks, $messages);
    if (!empty($r[0])) return $r;
    $fb = deiServerConf()['ai_fallback'] ?? null;
    if (!is_array($fb) || empty($fb['model'])) return $r;""",
"""/* v1.2.80: model cadangan dipilih Super Admin di dashboard (settings.api.fallback = "provider:model").
 * "" = bawaan (data/server.php 'ai_fallback' bila ada), "none" = tanpa cadangan. */
function deiAiFallback($settings) {
    $v = trim((string)($settings['api']['fallback'] ?? ''));
    if ($v === 'none') return null;
    if ($v !== '' && strpos($v, ':') !== false) {
        list($p, $m) = explode(':', $v, 2);
        $p = ($p === 'openrouter') ? 'openrouter' : 'anthropic';
        $m = trim($m);
        if ($m === '') return null;
        $fb = ['provider' => $p, 'model' => $m];
    } else {
        $fb = deiServerConf()['ai_fallback'] ?? null;
        if (!is_array($fb) || empty($fb['model'])) return null;
        $fb = ['provider' => (string)($fb['provider'] ?? ($settings['api']['provider'] ?? 'anthropic')), 'model' => (string)$fb['model']];
    }
    // sama dengan model utama = tidak ada gunanya dicoba ulang
    $pp = (string)($settings['api']['provider'] ?? 'anthropic');
    $pm = $pp === 'openrouter' ? (string)($settings['api']['openrouter_model'] ?? '') : (string)($settings['api']['model'] ?? '');
    if ($fb['provider'] === $pp && $fb['model'] === $pm) return null;
    return $fb;
}
function callClaude($settings, $systemBlocks, $messages) {
    $r = callClaudeOnce($settings, $systemBlocks, $messages);
    if (!empty($r[0])) return $r;
    $fb = deiAiFallback($settings);
    if (!is_array($fb) || empty($fb['model'])) return $r;""")
A = rep(A, "                'ai_fallback' => (string)(deiServerConf()['ai_fallback']['model'] ?? ''), 'ai_fail_handoff'",
           "                'ai_fallback' => (string)((deiAiFallback(getSettings()) ?? [])['model'] ?? ''), 'ai_fail_handoff'")
A = rep(A, """        $s['api']['openrouter_key_is_set'] = !empty($raw['api']['openrouter_api_key']);
""", """        $s['api']['openrouter_key_is_set'] = !empty($raw['api']['openrouter_api_key']);
        $sfb = deiServerConf()['ai_fallback'] ?? null;   // v1.2.80: info cadangan bawaan server
        $s['api']['server_fallback'] = (is_array($sfb) && !empty($sfb['model'])) ? (string)$sfb['model'] : '';
""")

# --- html: Flash-Lite + pilihan model cadangan
H = rep(H, """                <option value="google/gemini-2.5-flash">Gemini 2.5 Flash — cepat &amp; murah</option>
                <option value="google/gemini-2.5-pro">Gemini 2.5 Pro — pintar</option>""",
"""                <option value="google/gemini-2.5-flash-lite">Gemini 2.5 Flash-Lite — paling hemat</option>
                <option value="google/gemini-2.5-flash">Gemini 2.5 Flash — cepat &amp; murah</option>
                <option value="google/gemini-2.5-pro">Gemini 2.5 Pro — pintar</option>""")
H = rep(H, """            <div class="help">Daftar lengkap &amp; harga: openrouter.ai/models</div>
          </div>
        </div>
""", """            <div class="help">Daftar lengkap &amp; harga: openrouter.ai/models</div>
          </div>
        </div>
        <!-- v1.2.80: model cadangan -->
        <div class="row"><label class="fl">Model Cadangan</label>
          <select id="a_fallback">
            <option value="" id="a_fallback_default">Bawaan server</option>
            <option value="none">Tidak pakai cadangan</option>
            <optgroup label="OpenRouter (pakai OpenRouter API Key)">
              <option value="openrouter:google/gemini-2.5-flash-lite">Gemini 2.5 Flash-Lite</option>
              <option value="openrouter:google/gemini-2.5-flash">Gemini 2.5 Flash</option>
              <option value="openrouter:anthropic/claude-haiku-4.5">Claude Haiku 4.5</option>
              <option value="openrouter:openai/gpt-4o-mini">GPT-4o mini</option>
              <option value="openrouter:deepseek/deepseek-chat">DeepSeek V3</option>
            </optgroup>
            <optgroup label="Anthropic langsung (pakai Claude API Key)">
              <option value="anthropic:claude-haiku-4-5-20251001">Claude Haiku 4.5</option>
              <option value="anthropic:claude-sonnet-4-6">Claude Sonnet 4.6</option>
            </optgroup>
          </select>
          <div class="help">Dipakai sekali bila model utama gagal menjawab (gangguan penyedia, batas kuota, dsb). Pilih model dari penyedia yang API key-nya sudah diisi; sebaiknya berbeda dari model utama.</div>
        </div>
""")

# --- js: muat & simpan
J = rep(J, """      setOrModel(a.openrouter_model || 'google/gemini-2.5-flash');
      wireAiProvider();""", """      setOrModel(a.openrouter_model || 'google/gemini-2.5-flash');
      (function(){ // v1.2.80: model cadangan
        var fs = $('#a_fallback'); if (!fs) return;
        var d = $('#a_fallback_default');
        if (d) d.textContent = a.server_fallback ? ('Bawaan server (' + a.server_fallback + ')') : 'Bawaan (tidak ada cadangan)';
        var v = a.fallback || '';
        var ada = false; for (var i = 0; i < fs.options.length; i++) { if (fs.options[i].value === v) { ada = true; break; } }
        if (!ada && v) { var o = document.createElement('option'); o.value = v; o.textContent = v; fs.appendChild(o); }
        fs.value = v;
      })();
      wireAiProvider();""")
J = rep(J, """      openrouter_model: getOrModel(),
      max_tokens:""", """      openrouter_model: getOrModel(),
      fallback: $('#a_fallback') ? $('#a_fallback').value : '',   // v1.2.80
      max_tokens:""")
api.write_text(A, encoding='utf-8'); html.write_text(H, encoding='utf-8'); js.write_text(J, encoding='utf-8')
print('OK v1.2.80 terpasang')
