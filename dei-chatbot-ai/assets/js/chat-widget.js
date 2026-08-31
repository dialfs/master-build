/* DEI AI Chat Widget — loaded via Google Tag Manager (or direct <script>).
 * All appearance/behaviour comes from the dashboard via ?action=bootstrap.
 * The widget figures out the API host from window.DEI_CHATBOT_BASE (set by the
 * GTM snippet) or, failing that, from this script's own src URL.
 */
(function () {
  'use strict';
  if (window.__deiChatLoaded) return;
  window.__deiChatLoaded = true;

  /* ---- resolve API base ------------------------------------------------ */
  function resolveBase() {
    if (window.DEI_CHATBOT_BASE) return String(window.DEI_CHATBOT_BASE).replace(/\/+$/, '');
    var cur = document.currentScript;
    if (!cur) {
      var sc = document.getElementsByTagName('script');
      for (var i = sc.length - 1; i >= 0; i--) {
        if (sc[i].src && sc[i].src.indexOf('chat-widget.js') !== -1) { cur = sc[i]; break; }
      }
    }
    if (cur && cur.src) {
      // .../assets/js/chat-widget.js -> strip the last 3 path segments
      return cur.src.replace(/\/assets\/js\/chat-widget\.js.*$/, '');
    }
    return '';
  }
  var BASE = resolveBase();
  var API = BASE + '/api/index.php';

  /* ---- UTM + page capture --------------------------------------------- */
  function getUTM() {
    var p = new URLSearchParams(window.location.search);
    return {
      utm_source: p.get('utm_source') || '',
      utm_medium: p.get('utm_medium') || '',
      utm_campaign: p.get('utm_campaign') || '',
      page: window.location.pathname + window.location.search,
      referrer: document.referrer || ''
    };
  }

  /* ---- helpers --------------------------------------------------------- */
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function el(html) { var d = document.createElement('div'); d.innerHTML = html.trim(); return d.firstChild; }

  /* v1.1.9: 12 Lucide avatar icons (matches dashboard hybrid picker) */
  var AVATAR_ICONS = {
    'bot':                '<path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>',
    'message-circle':     '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    'hand':               '<path d="M18 11V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2"/><path d="M14 10V4a2 2 0 0 0-2-2a2 2 0 0 0-2 2v2"/><path d="M10 10.5V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/>',
    'smile':              '<circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" x2="9.01" y1="9" y2="9"/><line x1="15" x2="15.01" y1="9" y2="9"/>',
    'headphones':         '<path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H4a1 1 0 0 1-1-1zm18 0h-3a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h2a1 1 0 0 0 1-1zM3 14a9 9 0 0 1 18 0"/>',
    'user-round':         '<circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 0 0-16 0"/>',
    'briefcase-business': '<path d="M12 12h.01"/><path d="M16 6V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/><path d="M22 13a18.15 18.15 0 0 1-20 0"/><rect width="20" height="14" x="2" y="6" rx="2"/>',
    'phone':              '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>',
    'sparkles':           '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/><path d="M4 17v2"/><path d="M5 18H3"/>',
    'mail':               '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    'life-buoy':          '<circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/><circle cx="12" cy="12" r="4"/>',
    'crown':              '<path d="M11.562 3.266a.5.5 0 0 1 .876 0L15.39 8.87a1 1 0 0 0 1.516.294L21.183 5.5a.5.5 0 0 1 .798.519l-2.834 10.246a1 1 0 0 1-.956.734H5.81a1 1 0 0 1-.957-.734L2.02 6.02a.5.5 0 0 1 .798-.519l4.276 3.664a1 1 0 0 0 1.516-.294z"/><path d="M5 21h14"/>',
  };
  function lucideAvatar(name) {
    var path = AVATAR_ICONS[name] || AVATAR_ICONS['bot'];
    return '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + path + '</svg>';
  }

  /* ---- boot ------------------------------------------------------------ */
  fetch(API + '?action=bootstrap')
    .then(function (r) { return r.json(); })
    .then(function (res) {
      if (!res || !res.ok) return;
      init(res.config);
    })
    .catch(function () { /* silently fail — never break the host page */ });

  function init(cfg) {
    var ap = cfg.appearance || {};
    var color = ap.primary_color || '#140383';
    var side = ap.position === 'left' ? 'left' : 'right';
    var ob = (ap.offset_bottom != null ? ap.offset_bottom : 24);
    var or = (ap.offset_right != null ? ap.offset_right : 24);
    var bot = cfg.bot || {};
    var history = [];

    /* avatar markup */
    // v1.1.6+v1.1.9: respect explicit avatar_type — image | icon | emoji.
    // Fallback (older widget_config without avatar_type): image wins if URL set.
    var useImage = ap.avatar_type
      ? (ap.avatar_type === 'image' && !!ap.avatar_image)
      : !!ap.avatar_image;
    var useIcon = ap.avatar_type === 'icon' && !!ap.avatar_icon_name;
    var avatar;
    if (useImage) {
      avatar = '<img src="' + esc(ap.avatar_image) + '" alt="" style="width:30px;height:30px;border-radius:50%;object-fit:cover">';
    } else if (useIcon) {
      avatar = '<span style="display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;color:#fff">' + lucideAvatar(ap.avatar_icon_name) + '</span>';
    } else {
      avatar = '<span style="font-size:20px">' + esc(ap.avatar_emoji || '🤖') + '</span>';
    }

    /* ---- styles ---- */
    var css = document.createElement('style');
    css.textContent = [
      '.dei-w *{box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}',
      '#dei-chat-btn{position:fixed;bottom:' + ob + 'px;' + side + ':' + or + 'px;width:60px;height:60px;border-radius:50%;background:' + color + ';border:none;cursor:pointer;box-shadow:0 6px 24px rgba(0,0,0,.25);z-index:2147483000;display:flex;align-items:center;justify-content:center;transition:transform .15s}',
      '#dei-chat-btn:hover{transform:scale(1.07)}',
      '#dei-chat-btn svg{width:28px;height:28px;fill:#fff}',
      '#dei-chat-btn.dei-pulse::after{content:"";position:absolute;inset:0;border-radius:50%;box-shadow:0 0 0 0 ' + color + '66;animation:dei-pulse 2.2s infinite}',
      '@keyframes dei-pulse{0%{box-shadow:0 0 0 0 ' + color + '55}70%{box-shadow:0 0 0 14px ' + color + '00}100%{box-shadow:0 0 0 0 ' + color + '00}}',
      '#dei-teaser{position:fixed;bottom:' + (ob + 76) + 'px;' + side + ':' + or + 'px;width:300px;max-width:calc(100vw - 32px);background:#fff;border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,.22);z-index:2147483000;overflow:hidden;display:none;animation:dei-in .25s ease}',
      '#dei-teaser .tz-h{background:' + color + ';color:#fff;padding:12px 14px;display:flex;align-items:center;gap:9px}',
      '#dei-teaser .tz-av{width:30px;height:30px;border-radius:50%;background:rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;flex-shrink:0}',
      '#dei-teaser .tz-nm{font-weight:600;font-size:13.5px;line-height:1.2}',
      '#dei-teaser .tz-st{font-size:10.5px;opacity:.85}',
      '#dei-teaser .tz-x{margin-left:auto;background:none;border:none;color:#fff;font-size:18px;cursor:pointer;opacity:.85;line-height:1}',
      '#dei-teaser .tz-g{padding:13px 14px 6px;font-size:13.5px;color:#1a1a2e;line-height:1.45;cursor:pointer}',
      '#dei-teaser .tz-q{display:flex;flex-wrap:wrap;gap:6px;padding:4px 14px 14px}',
      '#dei-teaser .tz-q button{background:#fff;border:1px solid ' + color + ';color:' + color + ';border-radius:16px;padding:7px 12px;font-size:12.5px;cursor:pointer;text-align:left}',
      '#dei-teaser .tz-q button:hover{background:' + color + ';color:#fff}',
      '#dei-chat-window{position:fixed;bottom:' + (ob + 76) + 'px;' + side + ':' + or + 'px;width:360px;max-width:calc(100vw - 32px);height:520px;max-height:calc(100vh - 120px);background:#fff;border-radius:16px;box-shadow:0 12px 48px rgba(0,0,0,.25);z-index:2147483000;display:none;flex-direction:column;overflow:hidden;animation:dei-in .2s ease}',
      '@keyframes dei-in{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}',
      '.dch{background:' + color + ';color:#fff;padding:14px 16px;display:flex;align-items:center;gap:10px;flex-shrink:0}',
      '.dch-av{width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;flex-shrink:0}',
      '.dch-name{font-weight:600;font-size:15px;line-height:1.2}',
      '.dch-sub{font-size:11px;opacity:.8}',
      '.dch-x{margin-left:auto;background:none;border:none;color:#fff;font-size:22px;cursor:pointer;opacity:.85;line-height:1}',
      '.dch-body{flex:1;overflow-y:auto;padding:16px;background:#f5f6fa}',
      '.dm{display:flex;margin-bottom:10px}',
      '.dm.user{justify-content:flex-end}',
      '.dm-b{max-width:80%;padding:10px 13px;border-radius:14px;font-size:14px;line-height:1.45;white-space:pre-wrap;word-wrap:break-word}',
      '.dm.bot .dm-b{background:#fff;color:#1a1a2e;border-bottom-left-radius:4px;box-shadow:0 1px 2px rgba(0,0,0,.06)}',
      '.dm.user .dm-b{background:' + color + ';color:#fff;border-bottom-right-radius:4px}',
      '.dch-quick{display:flex;flex-wrap:wrap;gap:6px;padding:0 16px 10px;background:#f5f6fa}',
      '.dch-quick button{background:#fff;border:1px solid ' + color + ';color:' + color + ';border-radius:16px;padding:6px 12px;font-size:12px;cursor:pointer}',
      '.dch-quick button:hover{background:' + color + ';color:#fff}',
      '.dch-foot{display:flex;gap:8px;padding:12px;border-top:1px solid #eee;background:#fff;flex-shrink:0}',
      '.dch-foot input{flex:1;border:1px solid #ddd;border-radius:20px;padding:10px 14px;font-size:14px;outline:none}',
      '.dch-foot input:focus{border-color:' + color + '}',
      '.dch-send{background:' + color + ';border:none;border-radius:50%;width:40px;height:40px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}',
      '.dch-send svg{width:18px;height:18px;fill:#fff}',
      '.dch-typing{display:flex;gap:4px;padding:10px 13px}',
      '.dch-typing span{width:7px;height:7px;border-radius:50%;background:#bbb;animation:dei-bounce 1.2s infinite}',
      '.dch-typing span:nth-child(2){animation-delay:.2s}.dch-typing span:nth-child(3){animation-delay:.4s}',
      '@keyframes dei-bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-5px)}}',
      '#dei-wa-btn{position:fixed;bottom:' + ob + 'px;' + side + ':' + (or + (cfg.chatbot_enabled ? 72 : 0)) + 'px;width:56px;height:56px;border-radius:50%;background:#25d366;border:none;cursor:pointer;box-shadow:0 6px 24px rgba(0,0,0,.22);z-index:2147482999;display:flex;align-items:center;justify-content:center}',
      '#dei-wa-btn svg{width:30px;height:30px;fill:#fff}'
    ].join('');
    document.head.appendChild(css);

    var wrap = document.createElement('div');
    wrap.className = 'dei-w';
    document.body.appendChild(wrap);

    /* ---- WhatsApp button ---- */
    if (cfg.whatsapp_enabled && cfg.whatsapp_number) {
      var waUrl = 'https://wa.me/' + cfg.whatsapp_number.replace(/[^0-9]/g, '') +
        (cfg.whatsapp_message ? '?text=' + encodeURIComponent(cfg.whatsapp_message) : '');
      var wa = el('<button id="dei-wa-btn" title="WhatsApp"><svg viewBox="0 0 24 24"><path d="M17.5 14.4c-.3-.1-1.7-.8-2-.9-.3-.1-.5-.1-.7.1-.2.3-.7.9-.9 1.1-.2.2-.3.2-.6.1-1.6-.8-2.7-1.4-3.7-3.2-.3-.5.3-.5.8-1.5.1-.2 0-.4 0-.5 0-.1-.7-1.6-.9-2.2-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.5s1.1 2.9 1.2 3.1c.1.2 2.1 3.3 5.2 4.6 2 .9 2.7.9 3.7.8.6-.1 1.7-.7 2-1.4.2-.7.2-1.2.2-1.4-.1-.1-.3-.2-.6-.3zM12 2a10 10 0 0 0-8.6 15l-1.3 4.7L7 20.4A10 10 0 1 0 12 2z"/></svg></button>');
      wa.onclick = function () { window.open(waUrl, '_blank'); };
      wrap.appendChild(wa);
    }

    /* ---- Chatbot ---- */
    if (cfg.chatbot_enabled) {
      var btn = el('<button id="dei-chat-btn" title="Chat"><svg viewBox="0 0 24 24"><path d="M12 3C6.5 3 2 6.6 2 11c0 2.2 1.1 4.2 3 5.6V21l3.9-2.1c1 .3 2 .4 3.1.4 5.5 0 10-3.6 10-8s-4.5-8-10-8z"/></svg></button>');
      var win = el(
        '<div id="dei-chat-window">' +
          '<div class="dch">' +
            '<div class="dch-av">' + avatar + '</div>' +
            '<div><div class="dch-name">' + esc(bot.bot_name || 'Assistant') + '</div><div class="dch-sub">Online • Powered by AI</div></div>' +
            '<button class="dch-x" aria-label="Tutup">&times;</button>' +
          '</div>' +
          '<div class="dch-body" id="dei-body"></div>' +
          '<div class="dch-quick" id="dei-quick"></div>' +
          '<div class="dch-foot">' +
            '<input id="dei-input" type="text" placeholder="Ketik pesan..." autocomplete="off">' +
            '<button class="dch-send" aria-label="Kirim"><svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg></button>' +
          '</div>' +
        '</div>'
      );
      wrap.appendChild(btn);
      wrap.appendChild(win);

      var body = win.querySelector('#dei-body');
      var quick = win.querySelector('#dei-quick');
      var input = win.querySelector('#dei-input');
      var opened = false;

      function addMsg(role, text) {
        var m = el('<div class="dm ' + role + '"><div class="dm-b"></div></div>');
        m.querySelector('.dm-b').textContent = text;
        body.appendChild(m);
        body.scrollTop = body.scrollHeight;
        return m;
      }
      function showTyping() {
        var t = el('<div class="dm bot" id="dei-typing"><div class="dm-b dch-typing"><span></span><span></span><span></span></div></div>');
        body.appendChild(t); body.scrollTop = body.scrollHeight; return t;
      }
      function renderQuick() {
        quick.innerHTML = '';
        (bot.quick_replies || []).forEach(function (q) {
          var b = document.createElement('button');
          b.textContent = q;
          b.onclick = function () { send(q); };
          quick.appendChild(b);
        });
      }
      function toggle(open) {
        opened = (open != null) ? open : !opened;
        win.style.display = opened ? 'flex' : 'none';
        btn.style.display = opened ? 'none' : 'flex';
        if (opened && !body.childElementCount) {
          addMsg('bot', bot.greeting || 'Halo!');
          renderQuick();
        }
        if (opened) input.focus();
      }

      function send(text) {
        text = (text || input.value).trim();
        if (!text) return;
        input.value = '';
        quick.innerHTML = '';
        addMsg('user', text);
        history.push({ role: 'user', content: text });
        var typing = showTyping();

        fetch(API + '?action=chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, history: history.slice(-8), utm: getUTM() })
        })
          .then(function (r) { return r.json(); })
          .then(function (res) {
            typing.remove();
            if (res && res.ok) {
              addMsg('bot', res.answer);
              history.push({ role: 'assistant', content: res.answer });
            } else {
              addMsg('bot', (res && res.error) || 'Maaf, terjadi gangguan. Coba lagi nanti.');
            }
          })
          .catch(function () {
            typing.remove();
            addMsg('bot', 'Maaf, koneksi bermasalah. Coba lagi nanti.');
          });
      }

      btn.onclick = function () { hideTeaser(true); toggle(true); };
      win.querySelector('.dch-x').onclick = function () { toggle(false); };
      win.querySelector('.dch-send').onclick = function () { send(); };
      input.addEventListener('keydown', function (e) { if (e.key === 'Enter') send(); });

      /* ---- attention teaser: greeting + quick-reply options on the launcher ---- */
      var qreplies = (bot.quick_replies || []).filter(function (q) { return String(q).trim() !== ''; });
      var teaser = el(
        '<div id="dei-teaser" role="dialog" aria-label="Chat">' +
          '<div class="tz-h">' +
            '<div class="tz-av">' + avatar + '</div>' +
            '<div><div class="tz-nm">' + esc(bot.bot_name || 'Assistant') + '</div><div class="tz-st">Online • Powered by AI</div></div>' +
            '<button class="tz-x" aria-label="Tutup">&times;</button>' +
          '</div>' +
          '<div class="tz-g"></div>' +
          '<div class="tz-q"></div>' +
        '</div>'
      );
      wrap.appendChild(teaser);
      teaser.querySelector('.tz-g').textContent = bot.greeting || 'Halo! Ada yang bisa kami bantu?';

      var tzq = teaser.querySelector('.tz-q');
      qreplies.slice(0, 4).forEach(function (q) {
        var b = document.createElement('button');
        b.textContent = q;
        b.onclick = function (e) {
          e.stopPropagation();
          hideTeaser(true);
          toggle(true);
          send(q);               // open chat and send this prefilled message
        };
        tzq.appendChild(b);
      });

      // Clicking the greeting area just opens the chat normally
      teaser.querySelector('.tz-g').onclick = function () { hideTeaser(true); toggle(true); };
      teaser.querySelector('.tz-x').onclick = function (e) { e.stopPropagation(); hideTeaser(true); };

      function hideTeaser(remember) {
        teaser.style.display = 'none';
        btn.classList.remove('dei-pulse');
        if (remember) { try { sessionStorage.setItem('dei_teaser_dismissed', '1'); } catch (e) {} }
      }
      function showTeaser() {
        if (opened) return;
        var dismissed = false;
        try { dismissed = sessionStorage.getItem('dei_teaser_dismissed') === '1'; } catch (e) {}
        if (dismissed) { btn.classList.add('dei-pulse'); return; }
        teaser.style.display = 'block';
        btn.classList.add('dei-pulse');
      }
      // appear shortly after load to grab attention (once per browser session)
      setTimeout(showTeaser, 1800);
    }
  }
})();
