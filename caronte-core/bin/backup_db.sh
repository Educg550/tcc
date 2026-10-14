#!/bin/bash
set -e

source .env

BACKUP_DIR="$DOCKER_DATA_PATH/backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
mkdir -p "$BACKUP_DIR"

CONTAINER_NAME=$(docker compose ps -q db)
POSTGRES_USER=$(docker exec $CONTAINER_NAME printenv POSTGRES_USER)

echo "Running backup in folder $DOCKER_DATA_PATH"

docker exec -t $CONTAINER_NAME pg_dumpall -c -U $POSTGRES_USER > "$BACKUP_DIR/backup_$DATE.sql"