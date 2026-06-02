#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
ENV_FILE="$ROOT_DIR/.env"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
REQUIREMENTS="$ROOT_DIR/requirements.txt"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.10+ was not found. Install Python and run this script again."
  exit 1
fi

if [ ! -x "$PYTHON_BIN" ]; then
  echo "Creating local virtual environment: .venv"
  python3 -m venv "$VENV_DIR"
fi

echo "Installing project dependencies..."
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r "$REQUIREMENTS"

APP_PORT="${APP_PORT:-8080}"
APP_HOST="${APP_HOST:-127.0.0.1}"
LLM_PROVIDER="${LLM_PROVIDER:-kimi}"

if "$PYTHON_BIN" - "$APP_HOST" "$APP_PORT" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])
check_host = "0.0.0.0" if host == "0.0.0.0" else "127.0.0.1"
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(0.4)
try:
    in_use = sock.connect_ex((check_host, port)) == 0
finally:
    sock.close()
sys.exit(0 if in_use else 1)
PY
then
  echo "Port $APP_PORT is already in use. Change APP_PORT in .env or stop the other service."
  exit 1
fi

if [ -z "${LLM_API_KEY:-}" ] && [ -z "${KIMI_API_KEY:-}" ] && [ "$LLM_PROVIDER" != "ollama" ]; then
  echo "LLM key is not configured. The app will start in local mode."
  echo "Open the web app and use Configure Model, or set LLM_API_KEY in .env."
else
  echo "LLM provider configured: $LLM_PROVIDER"
fi

echo "Starting AI-From-Zero..."
echo "Local URL: http://127.0.0.1:$APP_PORT"
if [ "$APP_HOST" = "0.0.0.0" ]; then
  echo "LAN mode is enabled. Use this only on trusted networks."
fi

"$PYTHON_BIN" "$BACKEND_DIR/server.py"
