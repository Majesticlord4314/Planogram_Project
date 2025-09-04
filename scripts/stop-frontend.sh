#!/usr/bin/env bash
set -euo pipefail

# CRA typically listens on 3000 in dev
PORT=${PORT:-3000}

pids=$(lsof -t -i :${PORT} -sTCP:LISTEN || true)
if [ -n "$pids" ]; then
  echo "[INFO] Stopping frontend (port ${PORT}) PIDs: $pids"
  kill -INT $pids || true
  sleep 1
  if lsof -t -i :${PORT} -sTCP:LISTEN >/dev/null; then
    echo "[WARN] Forcing stop for remaining PIDs"
    kill -9 $pids || true
  fi
else
  echo "[INFO] No frontend process found on port ${PORT}"
fi

