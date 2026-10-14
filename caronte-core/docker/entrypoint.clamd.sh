#!/bin/sh
set -eu

echo "[entrypoint] Preparando /run/clamav..."

mkdir -p /run/clamav
chown -R clamav:clamav /run/clamav
chmod 775 /run/clamav

mkdir -p /var/log/clamav
chown -R clamav:clamav /var/log/clamav

if [ -S /run/clamav/clamd.sock ]; then
    echo "[entrypoint] Removendo socket antigo /run/clamav/clamd.sock"
    rm -f /run/clamav/clamd.sock
fi

echo "[entrypoint] Executando /init..."
exec /init "$@"