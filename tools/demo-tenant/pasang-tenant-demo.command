#!/usr/bin/env bash
# Pasang tenant DEMO di chatbot.deintegra.com/demo (data contoh Nusa EV; login admin/admin & sales/sales).
# 1) commit + push tools/demo-tenant  2) kirim skrip + data ke server  3) jalankan  4) cek dari luar.
exec > >(tee "$HOME/Herd/master-build/tools/demo-tenant/pasang.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; TD="$HERD/master-build/tools/demo-tenant"
TRAILER="Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwbByZtkJEADKG6cU5W"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
echo "== 1/4 Cek & commit =="
php -l "$TD/demo-provision.php" || stop "LINT GAGAL"
[[ "$(md5 -q "$TD/demo-data.zip")" == "b0a8c0fb6ba8c6a5fa580681a93eb3b4" ]] || stop "demo-data.zip tidak cocok (md5)."
rm -f "$HERD/master-build/.git/"*.lock
(cd "$HERD/master-build" && git add tools/demo-tenant && git commit -qm "tools: tenant demo (chatbot.deintegra.com/demo) dengan data contoh" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/master-build" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "master-build OK $(git rev-parse --short HEAD)") || echo "(!) push master-build gagal — lanjut pasang, push nanti"
source "$HERD/dei-pusat/dev/config.sh" || stop "dev/config.sh dei-pusat tidak ada"
echo; echo "== 2/4 Kirim ke server =="
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "mkdir -p ~/dei-demo-seed" || stop "SSH GAGAL"
scp -P "${SSH_PORT}" "$TD/demo-provision.php" "$TD/demo-data.zip" "${SSH_USER}@${SSH_HOST}:dei-demo-seed/" || stop "SCP GAGAL"
echo; echo "== 3/4 Pasang tenant di server =="
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ~/dei-demo-seed && php demo-provision.php pusat=\$HOME/public_html/chat.deintegra.com data=\$HOME/dei-demo-seed/demo-data.zip" || echo "(!) skrip pasang selesai dengan kode bukan 0, baca pesan di atas"
echo; echo "== 4/4 Cek dari luar =="
T=$(date +%s); B=https://chatbot.deintegra.com/demo
curl -s -o /dev/null -w "login.html HTTP %{http_code}  <- harus 200\n" "$B/dashboard/chatbot-ai/login.html?x=$T"
curl -s -o /dev/null -w "data/users.json publik HTTP %{http_code}  <- harus 403/404\n" "$B/data/users.json?x=$T"
echo "login admin: $(curl -s -X POST -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin"}' "$B/api/index.php?action=login" | head -c 60)"
echo; echo "Buka: $B/dashboard/chatbot-ai/login.html  (admin/admin, sales/sales)"
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
