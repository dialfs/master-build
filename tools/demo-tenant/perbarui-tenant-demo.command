#!/usr/bin/env bash
# Perbarui tenant DEMO: data contoh baru (Topik, Customer Feedback, iklan CTWA, UTM web, chat "hari ini")
# + reset harian otomatis (tanggal digeser ke hari ini, perubahan pengunjung kembali ke awal).
exec > >(tee "$HOME/Herd/master-build/tools/demo-tenant/perbarui.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; TD="$HERD/master-build/tools/demo-tenant"
TRAILER="Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwbByZtkJEADKG6cU5W"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
echo "== 1/4 Cek & commit =="
php -l "$TD/demo-reset.php" || stop "LINT GAGAL"
[[ "$(md5 -q "$TD/demo-data.zip")" == "713fa835b7ef1b33249373723ec323ef" ]] || stop "demo-data.zip tidak cocok (md5)."
rm -f "$HERD/master-build/.git/"*.lock
(cd "$HERD/master-build" && git add tools/demo-tenant && git commit -qm "tools: tenant demo — data laporan lengkap + reset harian" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/master-build" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "master-build OK $(git rev-parse --short HEAD)") || echo "(!) push master-build gagal — lanjut, push nanti"
source "$HERD/dei-pusat/dev/config.sh" || stop "dev/config.sh dei-pusat tidak ada"
SSHC=(ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}")
echo; echo "== 2/4 Kirim ke server =="
"${SSHC[@]}" "mkdir -p ~/dei-demo-seed" || stop "SSH GAGAL"
scp -P "${SSH_PORT}" "$TD/demo-reset.php" "$TD/demo-data.zip" "${SSH_USER}@${SSH_HOST}:dei-demo-seed/" || stop "SCP GAGAL"
echo; echo "== 3/4 Reset sekarang + pasang cron tiap jam (jalan sekali per hari, WIB) =="
"${SSHC[@]}" 'cd ~/dei-demo-seed && php demo-reset.php force=1' || stop "RESET GAGAL — data lama tidak diubah bila gagal sebelum tukar folder"
"${SSHC[@]}" 'P=$(command -v php); L="7 * * * * $P $HOME/dei-demo-seed/demo-reset.php >> $HOME/dei-demo-seed/reset.log 2>&1"; (crontab -l 2>/dev/null | grep -v "dei-demo-seed/demo-reset.php"; echo "$L") | crontab - && crontab -l | grep demo-reset' || echo "(!) cron gagal dipasang — tambahkan manual di cPanel > Cron Jobs"
echo; echo "== 4/4 Cek dari luar =="
T=$(date +%s); B=https://chatbot.deintegra.com/demo
TOK=$(curl -s -X POST -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin"}' "$B/api/index.php?action=login" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("token",""))')
[[ -n "$TOK" ]] && echo "login admin OK" || echo "(!) login admin gagal"
curl -s -H "Authorization: Bearer $TOK" "$B/api/index.php?action=report&channel=all&x=$T" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("kontak hari ini:",d["contacts"]["today"]["unique"],"| minggu ini:",d["contacts"]["week"]["unique"])'
curl -s -H "Authorization: Bearer $TOK" "$B/api/index.php?action=topic_scan_get&x=$T" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("scan topik:",list(d.get("scans",{}).keys()))'
curl -s -o /dev/null -w "data/demo-anchor.json publik HTTP %{http_code}  <- harus 403/404\n" "$B/data/demo-anchor.json?x=$T"
echo; echo "Buka: $B/dashboard/chatbot-ai/login.html (admin/admin, sales/sales) — Cmd+Shift+R"
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
