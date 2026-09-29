#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONT_DIR="$ROOT_DIR/Front"

if [ ! -d "$FRONT_DIR" ]; then
  echo "No existe la carpeta Front en: $FRONT_DIR"
  exit 1
fi

cd "$FRONT_DIR"

if ! command -v npm >/dev/null 2>&1; then
  echo "Falta npm. Instálalo antes de correr el front."
  exit 1
fi

if [ ! -d "node_modules" ] || [ ! -x "node_modules/.bin/vite" ]; then
  echo "Instalando dependencias del front..."
  npm install --no-fund --no-audit
fi

PORT="8081"
echo "Levantando Front en http://localhost:$PORT"

exec ./node_modules/.bin/vite --host 0.0.0.0 --port "$PORT"
