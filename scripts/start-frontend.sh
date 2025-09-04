#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR%/scripts}"

cd "$ROOT_DIR/web-ui/frontend"

# If using Node 20+, pass workaround flags automatically unless overridden
export SKIP_PREFLIGHT_CHECK=${SKIP_PREFLIGHT_CHECK:-true}
export NODE_OPTIONS=${NODE_OPTIONS:---openssl-legacy-provider}

npm start

