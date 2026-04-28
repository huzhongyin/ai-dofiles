#!/bin/bash
# PreToolUse hook: 在 Skill/Agent 被调用前写入临时标记
# Claude Code 通过 stdin 传入 JSON，包含 tool_name 字段

MARK_FILE="$HOME/.claude/.skill-calls-pending"
TODAY=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)

TOOL_INPUT=$(cat)
TOOL_NAME=$(echo "$TOOL_INPUT" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name','unknown'))" \
  2>/dev/null || echo "unknown")

# 只记录 Skill 和 Agent 工具
if [[ "$TOOL_NAME" != "Skill" && "$TOOL_NAME" != "Agent" ]]; then
  exit 0
fi

echo "$TODAY $TIME $TOOL_NAME" >> "$MARK_FILE"
