#!/usr/bin/env bash
# reset_delegates.sh — Reset delegates.json to the original 12 test delegates
# and clear their check-in state. Useful after a test run.
# Usage: bash tools/reset_delegates.sh

DELEGATES_FILE="open-event-server/khsc_mock/delegates.json"

if [ ! -f "$DELEGATES_FILE" ]; then
  echo "Error: $DELEGATES_FILE not found. Run from repo root." >&2
  exit 1
fi

echo "Resetting is_checked_in = false for all delegates in $DELEGATES_FILE..."

python3 - <<'EOF'
import json, sys

path = "open-event-server/khsc_mock/delegates.json"
with open(path) as f:
    delegates = json.load(f)

count = 0
for d in delegates:
    if d.get("is_checked_in"):
        d["is_checked_in"] = False
        count += 1

with open(path, "w") as f:
    json.dump(delegates, f, indent=2)

print(f"  Reset {count} delegate(s) to is_checked_in=false")
print(f"  Total delegates: {len(delegates)}")
EOF

echo ""
echo "Done. The mock server will serve fresh check-in state on the next request."
echo "Note: Open Event DB still has old check-in records — run /sync or re-import to reconcile."
