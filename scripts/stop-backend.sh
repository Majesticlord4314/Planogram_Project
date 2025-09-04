#!/usr/bin/env bash
set -euo pipefail

# Stop backend server listening on port (default 5001)
PORT=${PORT:-5001}

pids=$(lsof -t -i :${PORT} -sTCP:LISTEN || true)
if [ -n "$pids" ]; then
  echo "[INFO] Stopping backend (port ${PORT}) PIDs: $pids"
  # Try graceful first
  kill -INT $pids || true
  sleep 1
  # Ensure killed
  if lsof -t -i :${PORT} -sTCP:LISTEN >/dev/null; then
    echo "[WARN] Forcing stop for remaining PIDs"
    kill -9 $pids || true
  fi
else
  echo "[INFO] No backend process found on port ${PORT}"
fi

