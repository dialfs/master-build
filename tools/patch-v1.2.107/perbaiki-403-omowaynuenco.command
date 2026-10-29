#!/usr/bin/env bash
# Perbaiki 403 omowaynuenco (5 file 600 dari dei-master.zip) + kirim master.zip yang sudah dibetulkan ke pusat.
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.107/perbaiki-403.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; source "$HERD/dei-pusat/dev/config.sh"
echo "== 1/3 chmod 644 di omowaynuenco =="
ssh -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" 'cd ~/public_html/chatbot.deintegra.com/omowaynuenco && \
  find . -path ./data -prune -o -type f -perm 600 -print -exec chmod 644 {} + ; \
  find . -path ./data -prune -o -type d ! -perm 755 -print -exec chmod 755 {} + ; \
  ls -l api/index.php dashboard/chatbot-ai/index.html assets/js/chat-widget.js'
echo; echo "== 2/3 Uji alamat =="
for u in "dashboard/chatbot-ai/" "dashboard/chatbot-ai/login.html" "assets/js/chat-widget.js" "api/index.php?action=bootstrap"; do
  printf '%s  %s\n' "$(curl -s -o /dev/null -w '%{http_code}' "https://chatbot.deintegra.com/omowaynuenco/$u")" "$u"; done
echo; echo "== 3/3 Commit + deploy master.zip (izin 644) =="
cd "$HERD/dei-pusat"
# berkas yang dibuat sesi Claude bisa ber-izin 600 di Mac; rsync -a membawanya ke server -> 403
chmod 644 releases/v1.2.107/* master/dei-master.zip master/master.json "$HERD/dei-tenant/api/index.php" \
  "$HERD/dei-tenant/dashboard/chatbot-ai/"{app.js,index.html,login.html} "$HERD/dei-tenant/assets/js/chat-widget.js"
ls -l releases/v1.2.107/ master/
git add master/dei-master.zip master/master.json
git commit -m $'master: v1.2.107 izin file 644 (perbaikan 403)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01F3pjwbAQ4anDzRuZ6AGn97' || true
git pull --rebase origin main && git push origin main && ./dev/deploy.sh --go | tail -10
ssh -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "cd ${REMOTE_ROOT} && chmod 644 releases/v1.2.107/* master/dei-master.zip master/master.json && ls -l releases/v1.2.107 master"
for u in releases/v1.2.107/manifest.json releases/v1.2.107/update.zip master/master.json master/dei-master.zip; do
  printf '%s  %s\n' "$(curl -s -o /dev/null -w '%{http_code}' "https://chat.deintegra.com/$u")" "$u"; done
cd "$HERD/master-build" && git add tools/patch-v1.2.107 && git commit -m $'tools: v1.2.107 perbaikan izin master + 403\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01F3pjwbAQ4anDzRuZ6AGn97' && git push origin HEAD || true
read -r -p "Tekan Enter untuk menutup..." _
