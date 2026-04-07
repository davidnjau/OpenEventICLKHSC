#!/usr/bin/env bash
# health_check.sh — Check the status of all services in the KHSC stack.
# Usage: bash tools/health_check.sh

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}  ✓ $1${NC}"; }
fail() { echo -e "${RED}  ✗ $1${NC}"; }
warn() { echo -e "${YELLOW}  ~ $1${NC}"; }

echo ""
echo "══════════════════════════════════════════"
echo "  KHSC Stack Health Check"
echo "══════════════════════════════════════════"

# 1. Docker containers
echo ""
echo "Docker containers:"
for name in opev-web opev-postgres opev-redis opev-khsc-mock opev-celery; do
  STATUS=$(docker ps --filter "name=$name" --format "{{.Status}}" 2>/dev/null | head -1)
  if [[ "$STATUS" == Up* ]]; then
    ok "$name ($STATUS)"
  else
    fail "$name — NOT RUNNING"
  fi
done

# 2. Open Event server
echo ""
echo "Open Event Server (port 8080):"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8080/v1/events 2>/dev/null || echo "000")
if [[ "$HTTP" == "200" ]]; then
  ok "GET /v1/events → HTTP $HTTP"
else
  fail "GET /v1/events → HTTP $HTTP"
fi

# 3. KHSC mock
echo ""
echo "KHSC Mock (port 9090):"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
  -H "X-API-Username: admin_desk_1" \
  -H "Authorization: Bearer tok_test_khsc_mock_2026" \
  -H "X-Pass-Key: pk_test_khsc_mock_2026" \
  -H "X-Secret-Key: sk_test_khsc_mock_2026" \
  "http://localhost:9090/api/index.php?endpoint=event_stats" 2>/dev/null || echo "000")
if [[ "$HTTP" == "200" ]]; then
  ok "GET ?endpoint=event_stats → HTTP $HTTP"
else
  fail "GET ?endpoint=event_stats → HTTP $HTTP"
fi

# 4. Intellisoft middleware
echo ""
echo "Intellisoft Middleware (port 7000):"
HEALTH=$(curl -s --max-time 5 http://localhost:7000/health 2>/dev/null || echo "")
if [[ -n "$HEALTH" ]]; then
  OE_STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('open_event','unknown'))" 2>/dev/null || echo "unknown")
  KHSC_STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('khsc','unknown'))" 2>/dev/null || echo "unknown")
  ok "Reachable — OE: $OE_STATUS, KHSC: $KHSC_STATUS"
else
  warn "Not running on port 7000 — start with: cd intellisoft-middleware && .venv/bin/uvicorn app.main:app --reload --port 7000"
fi

echo ""
echo "══════════════════════════════════════════"
echo ""
