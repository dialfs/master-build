#!/usr/bin/env bash
# Pasang tenant "DEI Support" (Asisten Bantuan) di chatbot.deintegra.com/support.
# 1) commit + push + deploy backend/support-provision.php ke pusat  2) jalankan lewat SSH  3) cek.
exec > >(tee "$HOME/Herd/master-build/tools/support-tenant/pasang.log") 2>&1
set -uo pipefail
HERD="$HOME/Herd"; TD="$HERD/master-build/tools/support-tenant"
TRAILER="Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01F3pjwcAJ8kPdQosx8u6HFb"
stop() { echo "$1"; read -r -p "Tekan Enter untuk menutup..." _; exit 1; }
date
echo "== 1/3 Commit, push, deploy =="
cmp -s "$TD/support-provision.php" "$HERD/dei-pusat/backend/support-provision.php" || cp "$TD/support-provision.php" "$HERD/dei-pusat/backend/support-provision.php"
php -l "$HERD/dei-pusat/backend/support-provision.php" || stop "LINT GAGAL"
rm -f "$HERD/master-build/.git/"*.lock "$HERD/dei-pusat/.git/"*.lock
(cd "$HERD/master-build" && git add tools/support-tenant && git commit -qm "tools: pasang tenant DEI Support" -m "$TRAILER" && echo "master-build commit OK") || echo "(master-build: tidak ada yang di-commit)"
(cd "$HERD/dei-pusat" && git add backend/support-provision.php && git commit -qm "Asisten Bantuan: skrip pasang tenant DEI Support (CLI)" -m "$TRAILER" && echo "dei-pusat commit OK") || echo "(dei-pusat: tidak ada yang di-commit)"
for R in master-build dei-pusat; do
  cd "$HERD/$R" && rm -f .git/*.lock && git pull --ff-only origin main && git push -q origin main && echo "$R OK $(git rev-parse --short HEAD)" || stop "$R push GAGAL"
done
cd "$HERD/dei-pusat" || stop "folder dei-pusat tidak ada"
[[ -z "$(git status --porcelain)" ]] || { git status --short; stop "dei-pusat masih punya perubahan belum di-commit; dibatalkan."; }
./dev/deploy.sh --go | tail -6 || stop "DEPLOY GAGAL"
echo; echo "== 2/3 Pasang tenant di server =="
source dev/config.sh
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "cd ${REMOTE_ROOT} && php backend/support-provision.php" || echo "(!) skrip pasang selesai dengan kode bukan 0, baca pesan di atas"
echo; echo "== 3/3 Cek dari luar =="
T=$(date +%s)
curl -s -o /dev/null -w "dashboard login HTTP %{http_code}  <- harus 200\n" "https://chatbot.deintegra.com/support/dashboard/chatbot-ai/login.html?x=$T"
echo "bootstrap: $(curl -s "https://chatbot.deintegra.com/support/api/index.php?action=bootstrap&x=$T" | head -c 160)"
echo; echo "Berikutnya: tunggu 2-10 menit, lalu Admin Pusat > Pengaturan > Asisten Support harus menunjukkan 'Terakhir ditarik'."
echo "SELESAI $(date)"
read -r -p "Tekan Enter untuk menutup..." _
