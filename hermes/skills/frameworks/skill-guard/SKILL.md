---
name: skill-guard
description: |
  Agent-level skill loading approval gate. When active, the agent MUST pause for human confirmation BEFORE calling skill_view.
  Displays skill name, category, and trigger reason, then waits for user approval via clarify.
  Zero-intrusion: does NOT modify any existing skill files.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [skill-loading, approval-gate, debugging, workflow, session-override, framework]
    related_skills: [phase-test-mode]
---

# Skill Guard - Skill 加载审批门

不修改任何已有 Skill 文件，通过会话级元规则覆盖 skill_view 执行行为。

---

## 开启审批模式

Trigger: 用户说"开启 skill 审批模式"、"skill guard on"、"启用 skill guard"、"加载技能前要确认"。

### Step 1: 创建会话标记

```bash
touch "${HOME}/.hermes/.skill-guard-mode"
```

### Step 2: 注入会话级元规则（关键）

在当前会话中明确记录并持久化以下强制执行协议：

┌─────────────────────────────────────────────────────────┐
│              SKILL GUARD MODE ACTIVE - SESSION OVERRIDE              │
├─────────────────────────────────────────────────────────┤
│                                                                    │
│  RULE: 本会话中，准备调用 skill_view 时：                                 │
│                                                                    │
│  1. 在真正发起 skill_view 工具调用之前，必须：                          │
│     a) 在对话窗口中显式输出即将加载的 skill 名称、类别、触发原因       │
│     b) 调用 clarify 工具，阻塞等待用户确认                          │
│                                                                    │
│  2. 用户选项：                                                        │
│     - "确认加载" → 执行 skill_view                              │
│     - "取消" → 不执行 skill_view，跳过该 skill，继续通用处理      │
│     - "加载其他 skill" → 让用户指定替代 skill 名称             │
│                                                                    │
│  3. 回滚机制：                                                        │
│     - 用户可以在任何时候说"卸载 skill xxx"或"回滚 skill"         │
│     - 被卸载的 skill 加入当前会话黑名单，后续忽略其指令          │
│                                                                    │
│  4. 优先级：                                                         │
│     - 此规则优先级高于任何自动加载 skill 的内部判断逻辑              │
│     - 即使觉得某个 skill 100% 匹配，也必须先经过审批门           │
│                                                                    │
└─────────────────────────────────────────────────────────┘

### Step 3: 创建 Todo 锚定（解决长会话失效问题）

调用 `todo` 工具创建持久化任务项，确保即使 context 被压缩或溢出时，agent 仍能看到审批门状态：

```python
todo([
    {"id": "skill-guard-active", "content": "🔒 SKILL GUARD ACTIVE：所有 skill_view 调用前必须经过 clarify 确认。关闭: '关闭 skill 审批模式'", "status": "in_progress"}
])
```

### Step 4: 告知用户

"✅ Skill Guard 已开启。之后本会话中，每次我准备加载 skill 时都会先停下来让你确认，不会再有黑箱操作。"

---

## 关闭审批模式

Trigger: 用户说"关闭 skill 审批模式"、"skill guard off"、"禁用 skill guard"。

Steps:
1. 删除标记文件：`rm -f "${HOME}/.hermes/.skill-guard-mode"`
2. 将 todo 项标记为完成：`todo([{"id": "skill-guard-active", "status": "completed"}], merge=True)`
3. 告知用户："✅ Skill Guard 已关闭。之后的 skill 将自动加载，不再询问确认。"

---

## 审批门执行流程（每次触发时）

当 agent 判断需要加载 skill 时，按以下步骤执行：

### Step 1: 检查模式

```bash
if [ -f "${HOME}/.hermes/.skill-guard-mode" ]; then
    SKILL_GUARD_ACTIVE=1
else
    SKILL_GUARD_ACTIVE=0
fi
```

### Step 2: 如果审批门未开启

按原始行为直接调用 skill_view，不做额外处理。

### Step 3: 如果审批门已开含

**A. 检查黑名单**

如果该 skill 已在当前会话黑名单中：
- 跳过加载，告知用户："⚠️ skill 'xxx' 已被卸载，忽略。"
- 继续通用处理

**B. 公示即将加载的 skill**

在对话窗口中输出：

```
🔒 SKILL GUARD: 准备加载 skill
   名称: systematic-debugging
   类别: software-development
   触发原因: 用户报告 bug，命中 bugs 分类规则
```

**C. 调用 clarify 等待确认**

```python
clarify(
    question="确认加载 skill 'systematic-debugging'？",
    choices=["确认加载", "取消（跳过该 skill）", "加载其他 skill"]
)
```

**D. 处理用户选择**

1. **"确认加载"**
   - 执行 skill_view
   - 记录已加载 skills 列表

2. **"取消"**
   - 不执行 skill_view
   - 告知用户："已取消加载 systematic-debugging，继续通用处理。"

3. **"加载其他 skill"**
   - 询问用户想要加载什么 skill
   - 用户回复后，返回 Step B 重新公示

### Step 4: 回滚机制

用户可以在任何时候发起回滚：

**回滚指令**——用户说：
- "卸载 skill xxx"
- "回滚 skill xxx"
- "忽略 skill xxx"

**Agent 执行**：
1. 检查当前会话已加载 skills 列表
2. 如果该 skill 存在：
   - 将其加入黑名单
   - 告知用户："✅ 已将 'xxx' 加入黑名单，后续会话中忽略其指令。"
3. 如果不存在：
   - 告知用户："⚠️ 当前会话中未加载 'xxx'。"

---

## 查询状态

Trigger: 用户询问 skill guard 状态。

Steps:
1. 检查 `${HOME}/.hermes/.skill-guard-mode` 是否存在。
2. 检查 todo 列表中是否有 `skill-guard-active` 项目。
3. 列出当前会话已加载的 skills（如果有记录）。
4. 告知用户当前状态。

---

## 注意事项

- `.skill-guard-mode` 是会话级标记，仅对当前会话生效。
- 建议将 `.skill-guard-mode` 加入 `.gitignore`（如果在 git 项目中）。
- 采用三重锚定机制：
  1. **文件锚定**：`.skill-guard-mode` 标记文件
  2. **会话锚定**：Session Override 元规则
  3. **任务锚定**：todo 列表中的 `skill-guard-active` 项
- 回滚机制是"逻辑回滚"（忽略 skill 指令），不是"内存回滚"（无法真正从 system prompt 中抽出已注入的 skill 内容）。
