#!/usr/bin/env bash
# PreToolUse hook — fires before Edit or Write.
# Warns if the file being written contains hardcoded secrets.
# Exit 0 = proceed. Exit 2 = block with message.

FILE="$1"
[ -z "$FILE" ] && exit 0

# Patterns that should never appear verbatim in source files
PATTERNS=(
  "ADMIN_PASSWORD\s*="
  "SECRET_KEY\s*="
  "tok_live_"
  "pk_live_"
  "sk_live_"
  "Bearer tok_test_khsc"
  "opev_pass"
)

for pattern in "${PATTERNS[@]}"; do
  if grep -qE "$pattern" "$FILE" 2>/dev/null; then
    echo "BLOCKED: '$pattern' detected in $FILE. Use environment variables or .env instead." >&2
    exit 2
  fi
done

exit 0
