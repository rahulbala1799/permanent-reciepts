#!/bin/bash
set -euo pipefail

# Always restart the Flask app on port 5001 by first killing anything bound to it

# Move to project root (this script is in scripts/)
cd "$(dirname "$0")/.."

PORT=5001
LOG_FILE="app.log"
PID_FILE=".app.pid"
VENV_ACTIVATE="venv/bin/activate"

echo "[restart] Killing any process on port ${PORT}..."
# Kill processes bound to port 5001
PIDS=$(lsof -ti:${PORT} || true)
if [[ -n "${PIDS}" ]]; then
  kill -9 ${PIDS} || true
fi

# Also kill any lingering python app.py processes (reloader, etc.)
pkill -9 -f "python.*app.py" 2>/dev/null || true

sleep 2

echo "[restart] Starting app on port ${PORT}..."
if [[ -f "${VENV_ACTIVATE}" ]]; then
  # shellcheck disable=SC1090
  source "${VENV_ACTIVATE}"
fi

nohup python app.py > "${LOG_FILE}" 2>&1 & echo $! > "${PID_FILE}"

sleep 3

echo "[restart] Tail of ${LOG_FILE}:"
tail -n 40 "${LOG_FILE}" || true

echo "[restart] Done."



