---
name: learning-notes
description: Save learning Q&A from conversations as reviewable notes. Trigger when user asks a conceptual question (what/why/how) about tools, systems, or architecture.
version: 1.0.0
author: Hermes Agent
tags: [note-taking, learning, knowledge]
---

# Learning Notes

Save conceptual Q&A from conversations as structured learning notes for future review and team sharing.

## When to Save

Save a note when ALL of these are true:
- User asked a **conceptual question** ("X 是什么", "为什么 Y", "Z 的原理", "how does W work")
- The answer involved **non-trivial information** (not just a command or URL)
- The knowledge will be **useful again** (recurring system, architecture detail, gotcha)

Do NOT save:
- Simple factual lookups ("这个文件在哪")
- Task-specific details ("帮我改这个配置")
- Things already in memory or existing skills

## Where to Save

`~/.hermes/learning-notes/YYYY-MM-DD.md` — one file per day, append multiple entries.

## How to Save (MANDATORY)

**NEVER use `write_file` or heredoc directly on the note file.** This has caused data loss by overwriting existing entries.

Always use the safe append script:

```bash
python3 ~/.hermes/scripts/append_learning_note.py YYYY-MM-DD <<'EOF'
## [Topic Title]

### 问题
[...]

### 答案
[...]

### 关键点
- [...]

---
EOF
```

The script handles both creation (new day) and append (existing day) safely.

## Format

```markdown
# YYYY-MM-DD 学习笔记

## [Topic Title]

### 问题
[用户问了什么，用自己的话概括]

### 答案
[解释清楚核心概念]

### 关键点
- [要点1]
- [要点2]

---
```

## Example

```markdown
# 2026-04-15 学习笔记

## Hermes Memory 加载机制

### 问题
Memory 的存储路径是什么？什么时候加载？

### 答案
Memory 存在 `~/.hermes/memories/MEMORY.md` 和 `USER.md`。
会话启动时 `load_from_disk()` 读取，冻结为快照，之后每轮 API 调用从快照注入系统提示词。上下文压缩后会重新加载。

### 关键点
- 路径: ~/.hermes/memories/MEMORY.md + USER.md
- 加载时机: 会话启动 + 上下文压缩后
- 注入方式: 冻结快照，每轮都注入
- 用 memory 工具写入时同时更新磁盘和快照

---
```
