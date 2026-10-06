#!/usr/bin/env bash
# Uso: ./subir_run.sh <numero> <baseline|tdd> [modelo=deepseek] [porta=8000]
set -euo pipefail
porta="${4:-8000}"
cd "$(dirname "$0")/runs/batch/${3:-deepseek}/run${1:?informe o numero da run}/${2:?informe o grupo: baseline ou tdd}"
echo "http://localhost:$porta"
exec uv run --isolated --no-project --python 3.11 --with pytest --with "fastapi[standard]" \
  uvicorn app:app --host 127.0.0.1 --port "$porta"
