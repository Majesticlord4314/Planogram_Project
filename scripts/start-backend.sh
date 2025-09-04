#!/usr/bin/env bash
set -euo pipefail

# Repo root assumed as this script's parent parent
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR%/scripts}"

cd "$ROOT_DIR/web-ui/backend"

# Activate Python 3.10 virtualenv created earlier
if [ -f "../../py310/bin/activate" ]; then
  # shellcheck disable=SC1091
  source ../../py310/bin/activate
else
  echo "[ERROR] py310 virtualenv not found at ../../py310. Create it with:"
  echo "       python3.10 -m venv py310 && source py310/bin/activate && pip install -r web-ui/backend/requirements.txt"
  exit 1
fi

# Default port 5001 (5000 is often taken by macOS AirPlay Receiver)
export PORT="${PORT:-5001}"

# Prefer app.py for dev; fall back to gunicorn if needed
if python - <<'PY'
import importlib.util, os
spec = importlib.util.spec_from_file_location("app", "app.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(hasattr(mod, 'app'))
PY
then
  echo "[INFO] Starting Flask dev server on port ${PORT}"
  python app.py
else
  echo "[WARN] Could not import app.py; starting via gunicorn"
  exec gunicorn -b 0.0.0.0:${PORT} app:app
fi

