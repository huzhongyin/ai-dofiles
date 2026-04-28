# Skill/Agent 调用日志系统 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 每次 Claude Code 会话中调用 Skill 或 Agent 工具时，自动将触发意图、调用对象、目的和结果追加记录到 `~/.claude/skill-log.md`，并提供查阅命令和兜底检测机制。

**Architecture:** 三层设计——CLAUDE.md 行为指令（主触发，Claude 调用工具后自动写日志）+ PreToolUse/SessionStart hook 脚本（兜底标记，检测遗漏）+ `/view-skill-log` 查阅命令（日志读取和统计）。

**Tech Stack:** Bash shell scripts, Markdown, Claude Code hooks (PreToolUse / SessionStart), Claude Code commands

---

## Chunk 1: Hook 脚本 + settings.json 注册

### Task 1: 创建 hook 脚本目录和 PreToolUse 标记脚本

**Files:**
- Create: `/Users/xpeng/.claude/hooks/pre-skill-call-mark.sh`

- [ ] **Step 1: 创建 hooks 目录**

```bash
mkdir -p ~/.claude/hooks
```

- [ ] **Step 2: 写入 pre-skill-call-mark.sh**

文件内容：

```bash
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
```

- [ ] **Step 3: 赋予可执行权限**

```bash
chmod +x ~/.claude/hooks/pre-skill-call-mark.sh
```

- [ ] **Step 4: 手动验证脚本语法**

```bash
bash -n ~/.claude/hooks/pre-skill-call-mark.sh && echo "syntax OK"
```
Expected: `syntax OK`

- [ ] **Step 5: 功能冒烟测试**

```bash
echo '{"tool_name": "Skill"}' | bash ~/.claude/hooks/pre-skill-call-mark.sh
cat ~/.claude/.skill-calls-pending
```
Expected: 输出一行类似 `2026-03-13 10:42 Skill` 的记录

```bash
# 清理测试产物
rm -f ~/.claude/.skill-calls-pending
```

---

### Task 2: 创建 SessionStart 检查脚本

**Files:**
- Create: `/Users/xpeng/.claude/hooks/session-start-check.sh`

- [ ] **Step 1: 写入 session-start-check.sh**

```bash
#!/bin/bash
# SessionStart hook: 检测上次会话是否有未写入日志的 Skill/Agent 调用

MARK_FILE="$HOME/.claude/.skill-calls-pending"

if [ -f "$MARK_FILE" ] && [ -s "$MARK_FILE" ]; then
  COUNT=$(wc -l < "$MARK_FILE" | tr -d ' ')
  echo "⚠️ 检测到上次会话有 $COUNT 次 Skill/Agent 调用可能未写入 skill-log.md。"
  echo "请检查 ~/.claude/skill-log.md 并补写记录，完成后删除 ~/.claude/.skill-calls-pending。"
fi
```

- [ ] **Step 2: 赋予可执行权限**

```bash
chmod +x ~/.claude/hooks/session-start-check.sh
```

- [ ] **Step 3: 语法验证**

```bash
bash -n ~/.claude/hooks/session-start-check.sh && echo "syntax OK"
```
Expected: `syntax OK`

- [ ] **Step 4: 功能测试——有标记文件时**

```bash
echo "2026-03-13 10:42 Skill" > ~/.claude/.skill-calls-pending
echo "2026-03-13 10:55 Agent" >> ~/.claude/.skill-calls-pending
bash ~/.claude/hooks/session-start-check.sh
```
Expected: 输出 `⚠️ 检测到上次会话有 2 次 Skill/Agent 调用可能未写入 skill-log.md。...`

- [ ] **Step 5: 功能测试——无标记文件时**

```bash
rm -f ~/.claude/.skill-calls-pending
bash ~/.claude/hooks/session-start-check.sh
```
Expected: 无输出（静默退出）

---

### Task 3: 在 settings.json 中注册两个 hook

**Files:**
- Modify: `/Users/xpeng/.claude/settings.json`

- [ ] **Step 1: 读取当前 settings.json 确认当前结构**

```bash
cat ~/.claude/settings.json
```

- [ ] **Step 2: 在 settings.json 中插入 hooks 字段**

使用 Edit 工具，精确替换以下内容（以 `"model"` 行作为锚点，保持逗号正确）：

**old_string:**
```
  "model": "opus",
```

**new_string:**
```
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Skill",
        "hooks": [
          {
            "type": "command",
            "command": "bash /Users/xpeng/.claude/hooks/pre-skill-call-mark.sh"
          }
        ]
      },
      {
        "matcher": "Agent",
        "hooks": [
          {
            "type": "command",
            "command": "bash /Users/xpeng/.claude/hooks/pre-skill-call-mark.sh"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash /Users/xpeng/.claude/hooks/session-start-check.sh"
          }
        ]
      }
    ]
  },
  "model": "opus",
```

- [ ] **Step 3: 验证 JSON 格式合法**

```bash
python3 -c "import json; json.load(open('/Users/xpeng/.claude/settings.json')); print('JSON valid')"
```
Expected: `JSON valid`

---

## Chunk 2: CLAUDE.md 主触发规则

### Task 4: 在 CLAUDE.md 末尾追加第7节

**Files:**
- Modify: `/Users/xpeng/.claude/CLAUDE.md`

- [ ] **Step 1: 确认 CLAUDE.md 当前末尾内容**

```bash
tail -5 ~/.claude/CLAUDE.md
```

- [ ] **Step 2: 追加第7节内容**

在 `CLAUDE.md` 末尾追加以下内容（使用 Edit 工具，old_string 为文件末尾的最后一行，new_string 为原内容加上第7节）：

> ⚠️ 注意：下面内容中"记录模板"使用 `~~~` 围栏包裹，而非三反引号，以避免追加到 CLAUDE.md 后出现 Markdown 嵌套截断问题。

追加到 CLAUDE.md 末尾的文本：

```
---

## 7. Skill / Agent 调用日志规则

每次使用 `Skill` 工具或 `Agent` 工具**之后**，立即向 `~/.claude/skill-log.md` 追加一条记录：

1. 如果 `~/.claude/skill-log.md` 文件不存在，先用 Bash 工具执行 `touch ~/.claude/skill-log.md` 创建空文件
2. 检查文件中是否已有今天的 `## YYYY-MM-DD` 标题，没有则在文件末尾新建
3. 在今天的标题下追加记录（格式见下方记录模板）
4. 用 Bash 工具执行 `rm -f ~/.claude/.skill-calls-pending` 清除兜底标记
5. 写入完成后继续正常回应，**不需要向用户声明"已记录"**

记录模板：
~~~
### HH:MM | <意图类型> → <Skill名称 或 Agent的subagent_type>
**触发意图：** <意图类型>（<一句话描述用户的请求>）
**调用对象：** Skill `<name>` / Agent `<subagent_type>`
**目的：** <一句话说明调用这个skill/agent是为了做什么>
**结果：** <一句话说明执行结果或产出>

---
~~~

注意事项：
- 意图类型从本文件第2节的分类表中选取
- 如果通过 slash command 直接触发（不经意图识别流程），意图类型记录为 `DIRECT_COMMAND`
- 如果意图无法明确归类，使用 `GENERAL`
- Agent 调用记录 subagent_type 字段值（如 `general-purpose`、`Explore`、`superpowers:code-reviewer`）
- 不记录辅助性的内部工具调用（Read/Glob/Grep/Bash 等），只记录 Skill 和 Agent
```

- [ ] **Step 3: 确认追加成功**

```bash
tail -20 ~/.claude/CLAUDE.md
```
Expected: 能看到 `## 7. Skill / Agent 调用日志规则` 标题和记录模板

---

## Chunk 3: /view-skill-log 查阅命令

### Task 5: 创建 view-skill-log.md 命令文件

**Files:**
- Create: `/Users/xpeng/.claude/commands/view-skill-log.md`

- [ ] **Step 1: 确认 commands 目录存在**

```bash
ls ~/.claude/commands/
```
Expected: 看到 identify-intent.md / update-profile.md / view-profile.md

- [ ] **Step 2: 写入 view-skill-log.md**

文件内容：

```markdown
# view-skill-log

查看 Skill/Agent 调用日志，支持三种模式。

## 参数解析

$ARGUMENTS 的三种格式：
- 空（无参数）→ 显示今天的记录
- 数字（如 `7`）→ 显示最近 N 天的记录
- `stats` → 统计分析模式

## 执行步骤

### 模式1：无参数 / 数字参数

1. 读取 `~/.claude/skill-log.md`
2. 如果文件不存在，输出「暂无记录，请先使用 Skill 或 Agent 工具」
3. 无参数：提取今天（`## YYYY-MM-DD`）的全部记录并输出
4. 数字 N：提取最近 N 天（按日期标题，从最新往前数）的记录并输出
5. 如果该时间段内无记录，输出「该时段暂无 Skill/Agent 调用记录」

### 模式2：stats 参数

1. 读取 `~/.claude/skill-log.md` 全部内容
2. 统计所有 `**调用对象：**` 行中出现的 Skill/Agent 名称及次数
3. 统计所有 `**触发意图：**` 行中出现的意图类型及次数
4. 计算时间范围（最早记录的 `## YYYY-MM-DD` 日期 ~ 今天）和总条数（`###` 标题数量）
5. 按次数降序输出两张排名表，用 █ 字符绘制简易柱状图（每个 █ 代表1次，最多显示10个）
6. 根据最高频意图类型给出一条建议：
   - FEATURE_IMPL 最多 → 「建议运行 /update-profile 更新功能实现能力评估」
   - ARCHITECTURE 最多 → 「建议运行 /update-profile 更新架构设计能力评估」
   - BUG_FIX 最多 → 「建议回顾 TESTING.md，检查是否有未归档的约束」
   - LEARNING 最多 → 「建议运行 /identify-intent 归档学习内容」
   - 其他 → 「建议运行 /view-profile 查看当前能力画像」

## 示例调用

/view-skill-log
/view-skill-log 7
/view-skill-log stats
```

- [ ] **Step 3: 确认文件创建成功**

```bash
ls ~/.claude/commands/
```
Expected: 看到 view-skill-log.md 出现在列表中

- [ ] **Step 4: 用 cat 确认文件内容完整**

```bash
cat ~/.claude/commands/view-skill-log.md | head -20
```
Expected: 能看到 `# view-skill-log` 标题和参数解析部分

---

## Chunk 4: 端到端验证

### Task 6: 全系统冒烟测试

- [ ] **Step 1: 确认所有文件存在**

```bash
ls -la ~/.claude/hooks/pre-skill-call-mark.sh \
        ~/.claude/hooks/session-start-check.sh \
        ~/.claude/commands/view-skill-log.md
grep -c "Skill / Agent 调用日志规则" ~/.claude/CLAUDE.md || echo "⚠️ 第7节未找到，请检查 Task 4"
python3 -c "import json; d=json.load(open('/Users/xpeng/.claude/settings.json')); print('hooks registered:', list(d.get('hooks',{}).keys()))"
```
Expected:
```
/Users/xpeng/.claude/hooks/pre-skill-call-mark.sh
/Users/xpeng/.claude/hooks/session-start-check.sh
/Users/xpeng/.claude/commands/view-skill-log.md
1
hooks registered: ['PreToolUse', 'SessionStart']
```

- [ ] **Step 2: 模拟完整日志写入流程**

```bash
# 手动写入一条测试日志
LOG="$HOME/.claude/skill-log.md"
TODAY=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)

# 确保文件存在
touch "$LOG"

# 检查今天的标题是否存在，不存在则追加
if ! grep -q "^## $TODAY" "$LOG"; then
  echo "" >> "$LOG"
  echo "## $TODAY" >> "$LOG"
  echo "" >> "$LOG"
fi

# 追加测试记录
cat >> "$LOG" << EOF
### $TIME | DIRECT_COMMAND → view-skill-log [TEST]
**触发意图：** DIRECT_COMMAND（[TEST] 验证日志写入流程）
**调用对象：** Skill \`view-skill-log\`
**目的：** 验证端到端日志写入流程是否正常
**结果：** 测试记录写入成功

---
EOF

echo "--- 日志内容 ---"
cat "$LOG"
```
Expected: 能看到今天的标题和刚写入的测试记录

- [ ] **Step 3: 清理测试记录**

```bash
# 测试记录带有 [TEST] 标记，保留在日志中不影响真实记录
# 如需清理，取消注释：
# sed -i '' '/\[TEST\]/,/^---$/d' ~/.claude/skill-log.md
echo "测试记录已保留（含 [TEST] 标记），可与真实记录区分"
```

- [ ] **Step 4: 验证 SessionStart hook 的兜底逻辑**

```bash
# 模拟「上次会话有未写入记录」的场景
echo "2026-03-13 10:00 Skill" > ~/.claude/.skill-calls-pending
bash ~/.claude/hooks/session-start-check.sh
# 清理
rm -f ~/.claude/.skill-calls-pending
```
Expected: 输出包含 `⚠️ 检测到上次会话有 1 次 Skill/Agent 调用可能未写入 skill-log.md`

- [ ] **Step 5: 重启 Claude Code 会话，验证真实链路**

重启 Claude Code，执行以下验证序列：

1. 调用任意 Skill（如直接输入 `/view-skill-log`）
2. 在终端执行：
```bash
cat ~/.claude/skill-log.md
```
Expected（Pass 标准）：
- 能看到今天的 `## YYYY-MM-DD` 标题
- 标题下有至少一条 `### HH:MM |` 格式的记录
- 记录包含 `**触发意图：**`、`**调用对象：**`、`**目的：**`、`**结果：**` 四个字段

3. 确认兜底标记已清除：
```bash
ls ~/.claude/.skill-calls-pending 2>&1
```
Expected（Pass 标准）：
- 输出 `No such file or directory`（说明 Claude 正常清除了标记）

如以上三项均通过 → 系统运行正常 ✅
如日志未写入 → 检查 CLAUDE.md 第7节是否正确追加（运行 `tail -30 ~/.claude/CLAUDE.md`）
如标记未清除 → 检查 Claude 是否执行了 `rm -f ~/.claude/.skill-calls-pending`（可能是日志写入步骤失败）

---

## 文件变更摘要

| 文件路径 | 操作 | Chunk |
|---------|------|-------|
| `~/.claude/hooks/pre-skill-call-mark.sh` | 新建 | 1 |
| `~/.claude/hooks/session-start-check.sh` | 新建 | 1 |
| `~/.claude/settings.json` | 追加 hooks 字段 | 1 |
| `~/.claude/CLAUDE.md` | 追加第7节 | 2 |
| `~/.claude/commands/view-skill-log.md` | 新建 | 3 |
