#!/usr/bin/env python3
"""v1.2.103: model-terbaru — daftar model AI diperbarui ke generasi Okt 2026 (Claude 5.5, Gemini 3.x/4,
GPT-6 Luna/Sol, DeepSeek V4.1), tabel tarif per model, default tenant baru/cadangan.
Model lama tetap bisa dipilih (grup "Versi lama") supaya pengaturan tenant yang ada tidak hilang.
Idempoten. Pakai: patch_v12103_model.py <Herd>"""
import sys, os, time, shutil
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd'); T = H + '/dei-tenant'; P = H + '/dei-pusat'
TAG = 'v1.2.103: model-terbaru'
st = time.strftime('%Y%m%d-%H%M%S')

def patch(path, pairs, mark_check):
    s = open(path, encoding='utf-8').read()
    if mark_check(s): print('sudah:', path); return
    shutil.copy2(path, path + '.bak-v12103-' + st)
    for old, new in pairs:
        c = s.count(old); assert c == 1, (path, c, old[:90])
        s = s.replace(old, new)
    open(path, 'w', encoding='utf-8').write(s); print('patched:', path)

# ---------- api/index.php ----------
patch(T + '/api/index.php', [
 ("define('DEI_VERSION', 'v1.2.102');", "define('DEI_VERSION', 'v1.2.103');"),
 ("""function deiModelPrice($model) {
    $m = strtolower((string)$model);
    if (strpos($m, 'opus') !== false)   return [5.00, 25.00];
    if (strpos($m, 'sonnet') !== false) return [3.00, 15.00];
    if (strpos($m, 'haiku-3') !== false || strpos($m, '3-haiku') !== false) return [0.25, 1.25];
    if (strpos($m, 'haiku') !== false)  return [1.00, 5.00];
    if (strpos($m, 'gemini') !== false && strpos($m, 'flash') !== false) return [0.10, 0.40];
    if (strpos($m, 'gpt-4o-mini') !== false) return [0.15, 0.60];
    if (strpos($m, 'deepseek') !== false) return [0.30, 1.20];
    if (strpos($m, 'qwen') !== false) return [0.20, 0.60];
    return [1.00, 5.00];   // tidak dikenal: tarif Haiku (aman, cenderung lebih tinggi)
}""", """function deiModelPrice($model) {
    $m = strtolower((string)$model);
    // v1.2.103: model-terbaru — tarif USD per 1 juta token [input, output], Okt 2026
    $c5 = (bool)preg_match('/claude-(opus|sonnet|haiku|fable)-5/', $m);
    if (strpos($m, 'fable') !== false)  return [10.00, 50.00];
    if (strpos($m, 'opus') !== false)   return $c5 ? [4.00, 20.00] : [5.00, 25.00];
    if (strpos($m, 'sonnet') !== false) return $c5 ? [2.00, 10.00] : [3.00, 15.00];
    if (strpos($m, 'haiku-3') !== false || strpos($m, '3-haiku') !== false || strpos($m, '3.5-haiku') !== false) return [0.25, 1.25];
    if (strpos($m, 'haiku') !== false)  return $c5 ? [0.10, 0.50] : [1.00, 5.00];
    if (strpos($m, 'gemini') !== false) {
        $g2 = (bool)preg_match('/gemini-2/', $m);
        if (strpos($m, 'flash-lite') !== false) return $g2 ? [0.10, 0.40] : [0.30, 2.50];
        if (strpos($m, 'flash') !== false) {
            if (strpos($m, 'gemini-2.5') !== false) return [0.30, 2.50];
            return $g2 ? [0.10, 0.40] : [0.75, 3.75];
        }
        return [2.00, 12.00];   // pro / argon
    }
    if (strpos($m, 'gpt-6-luna') !== false) return [0.10, 0.50];
    if (strpos($m, 'luna') !== false) return [0.20, 1.20];
    if (strpos($m, 'nano') !== false) return [0.05, 0.40];
    if (strpos($m, 'gpt-4o-mini') !== false) return [0.15, 0.60];
    if (strpos($m, 'sol') !== false || strpos($m, 'gpt-4o') !== false) return [2.00, 10.00];
    if (strpos($m, 'deepseek') !== false) return [0.30, 1.20];
    if (strpos($m, 'qwen') !== false) return strpos($m, 'max') !== false ? [2.00, 6.00] : [0.20, 0.60];
    return [1.00, 5.00];   // tidak dikenal: tarif aman (cenderung lebih tinggi)
}"""),
 ("$settings['api']['openrouter_model'] ?? 'google/gemini-2.0-flash-001',", "$settings['api']['openrouter_model'] ?? 'anthropic/claude-haiku-5.5',"),
 (" *   'ai_fallback' => ['provider' => 'openrouter', 'model' => 'anthropic/claude-haiku-4.5']", " *   'ai_fallback' => ['provider' => 'openrouter', 'model' => 'google/gemini-3.5-flash-lite']"),
 ("$settings['api']['model'] ?? 'claude-haiku-4-5-20251001',", "$settings['api']['model'] ?? 'claude-haiku-5-5',"),
], lambda s: TAG in s)

# ---------- dashboard/chatbot-ai/app.js ----------
patch(T + '/dashboard/chatbot-ai/app.js', [
 ("$('#a_model').value = a.model || 'claude-haiku-4-5-20251001';",
  "(function(){ var ms = $('#a_model'), v = a.model || 'claude-haiku-5-5', ada = false; // v1.2.103: model-terbaru\n        for (var i = 0; i < ms.options.length; i++) { if (ms.options[i].value === v) { ada = true; break; } }\n        if (!ada) { var o = document.createElement('option'); o.value = v; o.textContent = v + ' (tersimpan)'; ms.appendChild(o); }\n        ms.value = v; })();"),
 ("setOrModel(a.openrouter_model || 'google/gemini-2.5-flash');", "setOrModel(a.openrouter_model || 'anthropic/claude-haiku-5.5');"),
 ("return (cust?cust.value.trim():'') || 'google/gemini-2.5-flash';", "return (cust?cust.value.trim():'') || 'anthropic/claude-haiku-5.5';"),
], lambda s: 'v1.2.103: model-terbaru' in s)

# ---------- dashboard/chatbot-ai/index.html ----------
patch(T + '/dashboard/chatbot-ai/index.html', [
 ("""            <select id="a_model">
              <option value="claude-haiku-4-5-20251001">Claude Haiku 4.5 — cepat &amp; hemat</option>
              <option value="claude-sonnet-4-6">Claude Sonnet 4.6 — lebih cerdas</option>
              <option value="claude-opus-4-6">Claude Opus 4.6 — paling canggih</option>
            </select>""", """            <select id="a_model"><!-- v1.2.103: model-terbaru -->
              <option value="claude-haiku-5-5">Claude Haiku 5.5 — cepat &amp; paling hemat</option>
              <option value="claude-sonnet-5-5">Claude Sonnet 5.5 — lebih cerdas</option>
              <option value="claude-opus-5-5">Claude Opus 5.5 — paling canggih</option>
              <optgroup label="Versi lama">
                <option value="claude-haiku-4-5-20251001">Claude Haiku 4.5</option>
                <option value="claude-sonnet-4-6">Claude Sonnet 4.6</option>
                <option value="claude-opus-4-6">Claude Opus 4.6</option>
              </optgroup>
            </select>"""),
 ("""              <optgroup label="Google Gemini">
                <option value="google/gemini-2.5-flash-lite">Gemini 2.5 Flash-Lite — paling hemat</option>
                <option value="google/gemini-2.5-flash">Gemini 2.5 Flash — cepat &amp; murah</option>
                <option value="google/gemini-2.5-pro">Gemini 2.5 Pro — pintar</option>
              </optgroup>
              <optgroup label="OpenAI GPT">
                <option value="openai/gpt-4o-mini">GPT-4o mini — murah</option>
                <option value="openai/gpt-4o">GPT-4o</option>
              </optgroup>
              <optgroup label="Anthropic Claude">
                <option value="anthropic/claude-3.5-haiku">Claude 3.5 Haiku</option>
                <option value="anthropic/claude-3.7-sonnet">Claude 3.7 Sonnet</option>
              </optgroup>
              <optgroup label="Qwen">
                <option value="qwen/qwen-2.5-72b-instruct">Qwen 2.5 72B</option>
              </optgroup>
              <optgroup label="DeepSeek">
                <option value="deepseek/deepseek-chat">DeepSeek V3</option>
              </optgroup>""", """              <optgroup label="Anthropic Claude">
                <option value="anthropic/claude-haiku-5.5">Claude Haiku 5.5 — cepat &amp; hemat (disarankan)</option>
                <option value="anthropic/claude-sonnet-5.5">Claude Sonnet 5.5 — lebih cerdas</option>
              </optgroup>
              <optgroup label="Google Gemini">
                <option value="google/gemini-3.5-flash-lite">Gemini 3.5 Flash-Lite — hemat</option>
                <option value="google/gemini-3.8-flash">Gemini 3.8 Flash — cepat</option>
                <option value="google/gemini-4-argon">Gemini 4 Argon — pintar</option>
              </optgroup>
              <optgroup label="OpenAI GPT">
                <option value="openai/gpt-6-luna">GPT-6 Luna — murah</option>
                <option value="openai/gpt-6.1-sol">GPT-6.1 Sol</option>
              </optgroup>
              <optgroup label="DeepSeek">
                <option value="deepseek/deepseek-v4.1-flash">DeepSeek V4.1 Flash — murah</option>
              </optgroup>
              <optgroup label="Qwen">
                <option value="qwen/qwen3.8-max-0902">Qwen 3.8 Max</option>
              </optgroup>
              <optgroup label="Versi lama">
                <option value="google/gemini-2.5-flash">Gemini 2.5 Flash</option>
                <option value="google/gemini-2.5-flash-lite">Gemini 2.5 Flash-Lite</option>
                <option value="anthropic/claude-haiku-4.5">Claude Haiku 4.5</option>
                <option value="openai/gpt-4o-mini">GPT-4o mini</option>
              </optgroup>"""),
 ("""              <option value="openrouter:google/gemini-2.5-flash-lite">Gemini 2.5 Flash-Lite</option>
              <option value="openrouter:google/gemini-2.5-flash">Gemini 2.5 Flash</option>
              <option value="openrouter:anthropic/claude-haiku-4.5">Claude Haiku 4.5</option>
              <option value="openrouter:openai/gpt-4o-mini">GPT-4o mini</option>
              <option value="openrouter:deepseek/deepseek-chat">DeepSeek V3</option>""", """              <option value="openrouter:google/gemini-3.5-flash-lite">Gemini 3.5 Flash-Lite</option>
              <option value="openrouter:anthropic/claude-haiku-5.5">Claude Haiku 5.5</option>
              <option value="openrouter:openai/gpt-6-luna">GPT-6 Luna</option>
              <option value="openrouter:deepseek/deepseek-v4.1-flash">DeepSeek V4.1 Flash</option>
              <option value="openrouter:google/gemini-2.5-flash">Gemini 2.5 Flash (lama)</option>"""),
 ("""              <option value="anthropic:claude-haiku-4-5-20251001">Claude Haiku 4.5</option>
              <option value="anthropic:claude-sonnet-4-6">Claude Sonnet 4.6</option>""", """              <option value="anthropic:claude-haiku-5-5">Claude Haiku 5.5</option>
              <option value="anthropic:claude-sonnet-5-5">Claude Sonnet 5.5</option>"""),
], lambda s: 'v1.2.103: model-terbaru' in s)

# ---------- dei-pusat: default daftar mandiri ----------
patch(P + '/backend/signup-lib.php', [
 ("'model'            => 'google/gemini-2.5-flash',", "'model'            => 'anthropic/claude-haiku-5.5', // v1.2.103: model-terbaru"),
 ("'fallback'         => 'openrouter:google/gemini-2.5-flash-lite',", "'fallback'         => 'openrouter:google/gemini-3.5-flash-lite',"),
], lambda s: 'v1.2.103: model-terbaru' in s)
patch(P + '/admin/index.html', [
 ('placeholder="google/gemini-2.5-flash"></div>', 'placeholder="anthropic/claude-haiku-5.5"></div>'),
 ('placeholder="openrouter:google/gemini-2.5-flash-lite"></div>', 'placeholder="openrouter:google/gemini-3.5-flash-lite"></div>'),
], lambda s: 'placeholder="anthropic/claude-haiku-5.5"' in s)
