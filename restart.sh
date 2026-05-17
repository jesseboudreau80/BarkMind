#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[BARKMIND] Restarting BarkMind..."

"$APP_DIR/stop.sh"
sleep 1
"$APP_DIR/start.sh"
