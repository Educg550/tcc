#!/usr/bin/env bash
# uso: caronte.sh subir | trocar admin|teacher
set -euo pipefail
cd "$(dirname "$0")/../../caronte-core"

dc() {
    docker compose --project-directory . -f docker-compose.yml -f ../demos/caronte/compose.yml \
        --profile develop --profile clamav "$@"
}

subir() {
    cp .env.example .env
    cp prejanus-back/.env.example prejanus-back/.env
    sed 's|^NEXT_PUBLIC_BASE_URL=.*|NEXT_PUBLIC_BASE_URL=http://localhost|' prejanus-front/.env.example > prejanus-front/.env
    sed -e 's/^#USE_CLAMAV=.*/USE_CLAMAV=1/' -e '/^DEV_USER_EMAIL=/d' forms/.env.example > forms/.env

    # mesmos donos que bin/deploy.sh, sem sudo
    docker run --rm -v "$PWD/docker:/d" alpine sh -c '
        mkdir -p /d/postgres_data /d/redis_cache /d/shared_tmp /d/clamd_socket /d/shared_uploads
        chown -R 999:999 /d/postgres_data /d/redis_cache
        chown -R 1001:1001 /d/shared_tmp /d/clamd_socket /d/shared_uploads'

    (cd static-assets && npm ci && npm run build)

    # sem --build: o original é congelado, então só constrói imagem ausente e não volta ao Docker Hub
    log=$(mktemp)
    dc --progress plain up -d --wait 2>&1 | tee "$log"
    curl -sf --retry 30 --retry-all-errors --retry-delay 2 http://localhost:8083/ > /dev/null
    dc exec -T db psql -v ON_ERROR_STOP=1 -U caronte_prejanus -d caronte_prejanus < ../demos/caronte/seed.sql

    # bases do build não ficam no image store; o digest vem do log, e o que não foi reconstruído mantém o registro anterior
    {
        grep -oE 'FROM docker.io/[^ ]+@sha256:[0-9a-f]+' "$log" | cut -d' ' -f2
        docker image inspect --format '{{index .RepoDigests 0}}' redis rnwood/smtp4dev alpine
        cat ../demos/caronte/imagens.txt
    } | sort -s -u -t@ -k1,1 > "$log.imagens"
    mv "$log.imagens" ../demos/caronte/imagens.txt
}

trocar() {
    case "${1:-}" in
        admin) id=1 ;;
        teacher) id=2 ;;
        *) echo "uso: $0 trocar admin|teacher" >&2; exit 1 ;;
    esac
    DEV_USER_ID=$id dc up -d --no-deps prejanus-back
}

case "${1:-}" in
    subir) subir ;;
    trocar) trocar "${2:-}" ;;
    *) echo "uso: $0 subir | trocar admin|teacher" >&2; exit 1 ;;
esac
