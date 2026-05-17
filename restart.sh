#!/usr/bin/env bash
# BarkMind Restart Script
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[BARKMIND $(date '+%H:%M:%S')] Restarting BarkMind..."

"$APP_DIR/stop.sh"

# Short pause to allow port release
sleep 2

"$APP_DIR/start.sh"
