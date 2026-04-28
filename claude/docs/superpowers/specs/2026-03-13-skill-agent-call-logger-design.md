# Skill/Agent 调用日志系统 — 设计文档

**日期：** 2026-03-13
**状态：** 已审批
**目标：** 自动记录每次 Claude Code 会话中触发的 Skill 和 Agent 调用，包含触发意图、调用目的、执行结果，支持回顾学习、调试溯源和统计分析。

---

## 1. 需求总结

| 维度 | 决策 |
|------|------|
| 触发方式 | 自动（Claude 调用 Skill/Agent 工具后立即写入） |
| 存储格式 | 单一追加文件 `~/.claude/skill-log.md` |
| 主要用途 | 回顾学习 + 调试溯源 + 统计分析（三者均有） |
| 兜底机制 | `Stop` hook 检查当天日志是否遗漏 |

---

## 2. 日志文件格式

**路径：** `~/.claude/skill-log.md`

```markdown
## YYYY-MM-DD

### HH:MM | <意图类型> → <调用对象>
**触发意图：** <意图类型>（<一句话描述用户的请求>）
**调用对象：** Skill `<name>` / Agent `<subagent_type>`
**目的：** <一句话说明调用这个skill/agent是为了做什么>
**结果：** <一句话说明执行结果或产出>

---
```

**示例：**

```markdown
## 2026-03-13

### 10:42 | ARCHITECTURE → superpowers:brainstorming
**触发意图：** ARCHITECTURE（设计skill/agent调用记录系统）
**调用对象：** Skill `superpowers:brainstorming`
**目的：** 探索需求、提出方案，为实现做设计前置
**结果：** 用户选择方案C（CLAUDE.md指令 + Stop hook兜底）

---

### 11:15 | FEATURE_IMPL → superpowers:writing-plans
**触发意图：** FEATURE_IMPL（实现skill调用日志功能）
**调用对象：** Skill `superpowers:writing-plans`
**目的：** 将brainstorm设计转化为可执行实现步骤
**结果：** 生成实现计划文档

---
```

**追加规则：**
- 如果 `skill-log.md` 文件不存在，先创建空文件，再写入今天的标题和记录
- 同一天的记录追加在同一个 `## YYYY-MM-DD` 标题下
- 不同天自动新建标题块
- 同一会话内多次调用按时间顺序追加
- 每次日志写入成功后，执行 `rm -f ~/.claude/.skill-calls-pending` 清除兜底标记

---

## 3. 主触发机制：CLAUDE.md 第7节

在 `~/.claude/CLAUDE.md` 末尾追加以下规则，使 Claude 在每次调用 Skill 或 Agent 工具后自动写日志：

```markdown
## 7. Skill / Agent 调用日志规则

每次使用 `Skill` 工具或 `Agent` 工具**之后**，立即向 `~/.claude/skill-log.md` 追加一条记录：

1. 如果 `~/.claude/skill-log.md` 文件不存在，先用 Bash 工具创建空文件
2. 检查文件中是否已有今天的 `## YYYY-MM-DD` 标题，没有则在文件末尾新建
3. 在今天的标题下追加记录（格式见记录模板）
4. 用 Bash 工具执行 `rm -f ~/.claude/.skill-calls-pending` 清除兜底标记
5. 写入完成后继续正常回应，**不需要向用户声明"已记录"**

记录模板：
### HH:MM | <意图类型> → <Skill名称 或 Agent的subagent_type>
**触发意图：** <意图类型>（<一句话描述用户的请求>）
**调用对象：** Skill `<name>` / Agent `<subagent_type>`
**目的：** <一句话说明调用这个skill/agent是为了做什么>
**结果：** <一句话说明执行结果或产出>

---

注意事项：
- 意图类型从 CLAUDE.md 第2节的分类表中选取
- 如果通过 slash command 直接触发（不经意图识别流程），意图类型记录为 `DIRECT_COMMAND`
- 如果意图无法明确归类，使用 `GENERAL`
- Agent 调用记录 subagent_type 字段值（如 `general-purpose`、`Explore`、`superpowers:code-reviewer`）
- 不记录辅助性的内部工具调用（Read/Glob/Grep/Bash 等），只记录 Skill 和 Agent
```

---

## 4. 兜底机制：PreToolUse Hook

**触发时机：** 每次 Claude 调用 `Skill` 或 `Agent` 工具之前（Claude Code 的 `PreToolUse` 事件）

> **设计说明：** Stop hook 的 stdout 对 Claude 不可见，无法驱动 Claude 补写日志。因此改用 `PreToolUse` hook：在每次 Skill/Agent 工具被调用前，将调用的工具名写入一个临时标记文件 `~/.claude/.skill-calls-pending`。如果 CLAUDE.md 规则正常执行，日志写入后 Claude 会同时清除此标记（通过 Bash 工具）。若会话异常中断，下次会话启动时（SessionStart hook）检测到标记文件存在，即提示补写。

**脚本路径：** `~/.claude/hooks/pre-skill-call-mark.sh`

**逻辑：**
```bash
#!/bin/bash
# 将本次 Skill/Agent 调用记录到临时标记文件
# 参数由 Claude Code 以 JSON 注入到 stdin

MARK_FILE="$HOME/.claude/.skill-calls-pending"
TODAY=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)

# 读取 tool_name（Claude Code 通过 stdin 传入 JSON）
TOOL_INPUT=$(cat)
TOOL_NAME=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name','unknown'))" 2>/dev/null || echo "unknown")

# 只记录 Skill 和 Agent 工具
if [[ "$TOOL_NAME" != "Skill" && "$TOOL_NAME" != "Agent" ]]; then
  exit 0
fi

echo "$TODAY $TIME $TOOL_NAME" >> "$MARK_FILE"
```

**SessionStart 检查脚本：** `~/.claude/hooks/session-start-check.sh`

```bash
#!/bin/bash
# 会话启动时检查是否有未完成的日志记录
MARK_FILE="$HOME/.claude/.skill-calls-pending"

if [ -f "$MARK_FILE" ] && [ -s "$MARK_FILE" ]; then
  COUNT=$(wc -l < "$MARK_FILE")
  echo "⚠️ 检测到上次会话有 $COUNT 次 Skill/Agent 调用可能未写入 skill-log.md。请检查并补写记录，完成后删除 ~/.claude/.skill-calls-pending。"
fi
```

**settings.json 注册方式：**

在 `settings.json` 的 `hooks` 字段中追加（如已有其他 hook 条目，合并到对应数组中，不要替换）：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Skill|Agent",
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
  }
}
```

**CLAUDE.md 规则补充：** 日志写入成功后，Claude 需执行以下命令清除标记：
```bash
rm -f ~/.claude/.skill-calls-pending
```

---

## 5. 查阅命令：/view-skill-log

**文件路径：** `~/.claude/commands/view-skill-log.md`

**三种调用模式：**

| 命令 | 作用 |
|------|------|
| `/view-skill-log` | 显示今天的所有记录 |
| `/view-skill-log 7` | 显示最近 N 天的记录 |
| `/view-skill-log stats` | 统计分析（skill/意图使用频率） |

**stats 模式输出格式（默认统计全部历史记录）：**
```
【Skill 使用统计】（YYYY-MM-DD ~ YYYY-MM-DD，共 N 条记录）

按调用次数排序（Skill）：
  superpowers:brainstorming    ████████  8次  (35%)
  superpowers:writing-plans    █████     5次  (22%)
  capture-knowledge            ████      4次  (17%)

按意图类型排序：
  FEATURE_IMPL      10次
  ARCHITECTURE       6次
  BUG_FIX            4次
  RETROSPECTIVE      3次
  DIRECT_COMMAND     2次

【建议】频繁使用 ARCHITECTURE 意图，建议运行 /update-profile 更新架构设计能力评估
```

**`~/.claude/commands/view-skill-log.md` 完整文件内容：**

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
4. 数字 N：提取最近 N 天（按日期标题）的记录并输出
5. 如果该时间段内无记录，输出「该时段暂无 Skill/Agent 调用记录」

### 模式2：stats 参数

1. 读取 `~/.claude/skill-log.md` 全部内容
2. 统计所有 `**调用对象：**` 行中出现的 Skill/Agent 名称及次数
3. 统计所有 `**触发意图：**` 行中出现的意图类型及次数
4. 计算时间范围（最早记录日期 ~ 今天）和总条数
5. 按次数降序输出两张排名表（用 █ 字符绘制简易柱状图）
6. 根据最高频意图类型给出一条建议（如频繁 ARCHITECTURE → 建议 /update-profile）

## 示例调用

​```
/view-skill-log
/view-skill-log 7
/view-skill-log stats
​```
```

---

## 6. 涉及文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `~/.claude/CLAUDE.md` | 追加第7节 | 主触发规则（含文件创建、标记清除逻辑） |
| `~/.claude/hooks/pre-skill-call-mark.sh` | 新建 | PreToolUse hook，写临时标记文件 |
| `~/.claude/hooks/session-start-check.sh` | 新建 | SessionStart hook，检测未写日志的历史调用 |
| `~/.claude/settings.json` | 追加 hooks.PreToolUse 和 hooks.SessionStart | 注册两个 hook |
| `~/.claude/commands/view-skill-log.md` | 新建 | 查阅命令（含完整指令内容） |
| `~/.claude/skill-log.md` | 运行时自动创建 | 日志数据文件 |
| `~/.claude/.skill-calls-pending` | 运行时自动管理 | 临时标记文件，日志写入后自动删除 |

---

## 7. 不在范围内

- 不记录 Read/Glob/Grep/Bash 等辅助工具调用（噪音过多，无分析价值）
- 不记录 Claude 内部推理过程（只记录工具调用结果）
- 不自动将日志内容注入未来会话上下文（查阅按需，不污染代码上下文）
- **V1 不做日志轮转**：`skill-log.md` 为单一追加文件，长期积累后若文件过大，后续版本可考虑按月分文件（如 `skill-log-2026-03.md`）
