#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACK_DIR="$ROOT_DIR/Back"

if [ ! -d "$BACK_DIR" ]; then
  echo "No existe la carpeta Back en: $BACK_DIR"
  exit 1
fi

if [ -d "$ROOT_DIR/.venv" ]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif [ -d "$ROOT_DIR/venv" ]; then
  PYTHON_BIN="$ROOT_DIR/venv/bin/python"
else
  PYTHON_BIN=""
  for candidate in python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi

if [ -z "$PYTHON_BIN" ] || ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "No se encontró una versión compatible de Python 3.10+ para el backend."
  exit 1
fi

cd "$BACK_DIR"

if [ ! -f "$BACK_DIR/requirements.txt" ]; then
  echo "No existe requirements.txt en $BACK_DIR"
  exit 1
fi

if ! "$PYTHON_BIN" -c "import fastapi, uvicorn, mysql.connector" >/dev/null 2>&1; then
  echo "Instalando dependencias del back..."
  "$PYTHON_BIN" -m pip install --upgrade pip
  "$PYTHON_BIN" -m pip install -r "$BACK_DIR/requirements.txt"
fi

PORT="5678"
echo "Levantando Back en http://localhost:$PORT"

exec "$PYTHON_BIN" -m uvicorn API:app --host 0.0.0.0 --port "$PORT" --reload
