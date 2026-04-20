#!/usr/bin/env bash
# Serve quick-report skill directory so ../vendor/ paths resolve correctly.
# Usage: ./serve.sh [port]
#   Default port: 8080
#   Kill with Ctrl-C or: kill $(cat /tmp/quick-report-serve.pid)

set -euo pipefail

PORT="${1:-8080}"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Serving quick-report from: $DIR"
echo "Report URL: http://$(hostname -I | awk '{print $1}'):${PORT}/reports/quick-report-skill-analysis.html"
echo "PID file:   /tmp/quick-report-serve.pid"
echo ""

cd "$DIR"
echo $$ > /tmp/quick-report-serve.pid
exec python3 -m http.server "$PORT"
