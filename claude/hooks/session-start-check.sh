#!/bin/bash
# SessionStart hook: 检测上次会话是否有未写入日志的 Skill/Agent 调用

MARK_FILE="$HOME/.claude/.skill-calls-pending"

if [ -f "$MARK_FILE" ] && [ -s "$MARK_FILE" ]; then
  COUNT=$(wc -l < "$MARK_FILE" | tr -d ' ')
  echo "⚠️ 检测到上次会话有 $COUNT 次 Skill/Agent 调用可能未写入 skill-log.md。"
  echo "请检查 ~/.claude/skill-log.md 并补写记录，完成后删除 ~/.claude/.skill-calls-pending。"
fi
