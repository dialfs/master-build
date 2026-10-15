#!/usr/bin/env bash
# =============================================================================
# Pasang / perbarui kit server Halte Bus di VPS — dijalankan dari Mac.
#   cd ~/Herd/master-build && ./server/deploy-vps.sh                     (bawaan Sinar Jaya)
#   ./server/deploy-vps.sh root@212.85.25.180 sinarjaya haltebus.chat/sinarjaya 8
# Langkah: cek DNS & SSH -> kirim server/ + dei-master.zip -> install-server.sh
# (aman diulang) -> add-client.sh (dilewati kalau klien sudah ada).
# Password root diminta sekali saja (koneksi SSH dipakai ulang).
# =============================================================================
set -euo pipefail
TARGET="${1:-root@212.85.25.180}"
SLUG="${2:-sinarjaya}"
ADDR="${3:-haltebus.chat/sinarjaya}"
WORKERS="${4:-8}"
ZIP="${MASTER_ZIP:-$HOME/Herd/dei-pusat/master/dei-master.zip}"
BRAND="${BRAND:-haltebus}"
HERE="$(cd "$(dirname "$0")" && pwd)"
HOST="${ADDR%%/*}"; IP="${TARGET#*@}"

[ -f "$ZIP" ] || { echo "dei-master.zip tidak ada: $ZIP"; exit 1; }
VER="$(unzip -p "$ZIP" '*/api/index.php' | grep -m1 -o "DEI_VERSION', 'v[0-9.]*" | grep -o 'v[0-9.]*' || true)"
echo "==> Kode: $ZIP ($VER)"

echo "==> DNS $HOST"
GOT="$(dig +short "$HOST" A 2>/dev/null | tail -1 || true)"
if [ "$GOT" = "$IP" ]; then echo "    OK -> $GOT"
else echo "    PERINGATAN: $HOST -> '${GOT:-kosong}', bukan $IP. Server tetap dipasang, HTTPS menyusul setelah DNS benar."; fi

SOCK="$HOME/.ssh/dei-%r@%h:%p"
SSH=(ssh -o ControlMaster=auto -o ControlPath="$SOCK" -o ControlPersist=10m -o StrictHostKeyChecking=accept-new)
cleanup() { ssh -o ControlPath="$SOCK" -O exit "$TARGET" 2>/dev/null || true; }
trap cleanup EXIT

echo "==> SSH ke $TARGET (masukkan password root VPS kalau diminta)"
"${SSH[@]}" "$TARGET" '. /etc/os-release; echo "    $PRETTY_NAME, $(nproc) vCPU, $(awk "/MemTotal/{print int(\$2/1024)}" /proc/meminfo) MB RAM, disk bebas $(df -h / | awk "NR==2{print \$4}")"
  [ "$ID" = ubuntu ] || { echo "    BUKAN Ubuntu. Instal ulang OS VPS ke Ubuntu 24.04 atau 26.04 di panel Hostinger dulu."; exit 3; }'

echo "==> Kirim kit server + master zip"
"${SSH[@]}" "$TARGET" 'rm -rf /opt/dei-src/server && mkdir -p /opt/dei-src'
tar -C "$HERE/.." --exclude='.DS_Store' -czf - server | "${SSH[@]}" "$TARGET" 'tar -C /opt/dei-src -xzf -'
"${SSH[@]}" "$TARGET" 'cat > /opt/dei-src/dei-master.zip' < "$ZIP"

echo "==> install-server.sh (beberapa menit pada pemasangan pertama)"
"${SSH[@]}" "$TARGET" 'bash /opt/dei-src/server/install-server.sh'

echo "==> Klien $SLUG di https://$ADDR"
if "${SSH[@]}" "$TARGET" "[ -d /var/www/$SLUG ]"; then
  echo "    Sudah terpasang — dilewati. (Perbarui kode: sudo /opt/dei/server/update-all.sh $SLUG)"
else
  "${SSH[@]}" "$TARGET" "BRAND=$BRAND bash /opt/dei/server/add-client.sh $SLUG $ADDR $WORKERS /opt/dei-src/dei-master.zip" | tee "$HOME/hb-deploy-$SLUG.txt"
  echo
  echo "    Password admin di atas juga tersimpan di ~/hb-deploy-$SLUG.txt — catat di tempat aman, lalu hapus berkas itu."
fi

echo "==> Cek"
"${SSH[@]}" "$TARGET" "sudo -u dei-$SLUG php /var/www/$SLUG/api/index.php action=wa_queue_status | head -12; supervisorctl status | grep -c RUNNING | sed 's/^/    worker RUNNING: /'"
curl -s -o /dev/null -w "    https://$ADDR/ -> HTTP %{http_code}\n" "https://$ADDR/" || echo "    HTTPS belum bisa diakses (DNS/sertifikat)."
