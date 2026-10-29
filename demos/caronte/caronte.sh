#!/usr/bin/env bash
# uso: caronte.sh subir | trocar admin|teacher | consulta | cobertura
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
        sed -nE 's/.*FROM (docker\.io\/[^ ]+@sha256:[0-9a-f]+).*/\1/p' "$log"
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

imagem=caronte-core-prejanus-back:latest
uvicorn=(uvicorn src.main:app --host 0.0.0.0 --port 8000)

backend() {
    local porta=$1; shift
    docker rm -f "prejanus-back-consulta-$porta" > /dev/null 2>&1 || true
    docker run -d --rm --name "prejanus-back-consulta-$porta" --network shared_network -p "$porta:8000" \
        -e DB_CONNECTION_STRING=postgresql+psycopg://caronte_prejanus:caronte_prejanus@db:5432/caronte_prejanus_consulta \
        -e DB_CONNECTION_STRING_FORMS=postgresql+psycopg://caronte_forms_reader:caronte_forms_reader@db:5432/caronte_forms_consulta \
        -v "$PWD/../demos/caronte/uploads-consulta:/shared/uploads:ro" "$@" > /dev/null
    curl -sf --retry 30 --retry-all-errors --retry-delay 1 "http://localhost:$porta/" > /dev/null
}

consulta() {
    local admin d=../demos/caronte
    admin=$(sed -n 's/^POSTGRES_ADMIN_USER=//p' .env)
    docker rm -f prejanus-back-consulta-8093 prejanus-back-consulta-8094 > /dev/null 2>&1 || true
    dc exec -T db psql -v ON_ERROR_STOP=1 -q -U "$admin" -d postgres \
        -c "drop database if exists caronte_forms_consulta" \
        -c "drop database if exists caronte_prejanus_consulta" \
        -c "create database caronte_forms_consulta owner caronte_forms" \
        -c "create database caronte_prejanus_consulta owner caronte_prejanus" \
        -c "grant connect on database caronte_forms_consulta to caronte_forms_reader"
    for b in forms prejanus; do
        dc exec -T db pg_dump -s -U "$admin" "caronte_$b" |
            dc exec -T db psql -v ON_ERROR_STOP=1 -q -U "$admin" -d "caronte_${b}_consulta" > /dev/null
    done
    carga() { dc exec -T db psql -v ON_ERROR_STOP=1 -q --single-transaction -U "caronte_$1" -d "caronte_$1_consulta" > /dev/null; }
    carga forms < $d/fixture-forms.sql
    carga forms < $d/fixture-consulta-forms.sql
    carga prejanus < $d/seed.sql
    carga prejanus < $d/fixture-prejanus.sql
    carga prejanus < $d/fixture-consulta-prejanus.sql

    backend 8093 -e APP_ENV=local -e DEV_USER_ID=2 "$imagem" "${uvicorn[@]}"
    # sem o atalho DEV_USER_ID, para conferir o 401 sem sessão
    backend 8094 -e APP_ENV=sem-atalho "$imagem" "${uvicorn[@]}"
}

cobertura() {
    # coverage do venv de demos/ montado na imagem congelada: mesmo Python 3.11 e glibc
    local out=$PWD/../demos/caronte/.cobertura
    local cov=(-v "$PWD/../demos/.venv/lib/python3.11/site-packages/coverage:/cov/coverage:ro" -e PYTHONPATH=/cov
               -v "$out:/out" -e COVERAGE_FILE=/out/.coverage -u "$(id -u):$(id -g)")
    mkdir -p "$out"
    consulta
    backend 8093 -e APP_ENV=local -e DEV_USER_ID=2 "${cov[@]}" "$imagem" \
        python -m coverage run --source=src --omit='*/tests/*,*/migrations/*,*conftest.py' -m "${uvicorn[@]}"
    (cd ../demos && uv run pytest caronte/gabarito -q)
    docker stop prejanus-back-consulta-8093 > /dev/null
    docker run --rm "${cov[@]}" "$imagem" python -m coverage json -q -o /out/cobertura.json
    (cd ../demos && uv run python caronte/cobertura.py caronte/.cobertura/cobertura.json)
    backend 8093 -e APP_ENV=local -e DEV_USER_ID=2 "$imagem" "${uvicorn[@]}"
}

case "${1:-}" in
    subir) subir ;;
    trocar) trocar "${2:-}" ;;
    consulta) consulta ;;
    cobertura) cobertura ;;
    *) echo "uso: $0 subir | trocar admin|teacher | consulta | cobertura" >&2; exit 1 ;;
esac
