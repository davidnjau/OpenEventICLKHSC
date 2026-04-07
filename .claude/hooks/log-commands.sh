#!/usr/bin/env bash
# PostToolUse hook — fires after every Bash tool call.
# Appends the command and exit code to a session log for audit purposes.
# This is a no-op for normal flow (always exits 0).

LOG_DIR=".claude/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/session-$(date +%Y-%m-%d).log"

echo "[$(date '+%H:%M:%S')] EXIT=$CLAUDE_TOOL_EXIT_CODE CMD=${CLAUDE_TOOL_INPUT_COMMAND:0:120}" >> "$LOG_FILE"

exit 0
