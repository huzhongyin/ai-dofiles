---
name: phase-test-mode
description: |
  Activate session-level phase test mode for all phased skills in the current project.
  When active, the agent MUST pause for human confirmation after each Phase of any loaded skill.
  Does NOT modify any existing skill files.
version: 2.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [phased-execution, testing, debugging, workflow, session-override, framework]
    related_skills: [phase-run]
---

# Phase 测试模式 - Session Override

不修改任何已有 Skill 文件，通过会话级元规则覆盖 Phase 执行行为。

---

## 开启测试模式

Trigger: 用户说"开启测试模式"、"phase test on"、"启用测试模式"、"测试模式"、"步步确认"、"逐步执行"、"测试 phase"。

### Step 1: 创建项目标记

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
touch "${PROJECT_ROOT}/.phase-test-mode"
```

如果当前是 git 仓库且 working tree 有改动：
```bash
git add -A && git stash push -m "phase-test-mode-entry-$(date +%s)"
```

### Step 2: 注入会话级元规则（关键）

在当前会话中明确记录并持久化以下强制执行协议。这条协议将在本会话中持续生效，覆盖任何后续加载的 Phased Skill 的原始执行指令：

┌─────────────────────────────────────────────────────────┐
│              PHASE TEST MODE ACTIVE - SESSION OVERRIDE              │
├─────────────────────────────────────────────────────────┤
│                                                                    │
│  RULE: 本会话中，执行任何带有 Phase/阶段/步骤 顺序的 Skill 时：       │
│                                                                    │
│  1. 在执行 Phase N 之前，检查项目根目录下的 `.phase-test-mode`         │
│     是否存在。若不存在，按原始 Skill 指令连续执行。                  │
│                                                                    │
│  2. 若 `.phase-test-mode` 存在：                                      │
│     a) 每个 Phase 开始前，如果是 git 仓库，执行：                    │
│        git add -A && git stash push -m "phase-checkpoint-$(date +%s)" │
│        --include-untracked                                             │
│     b) 仅执行当前 Phase 的指令，不得自动进入下一个 Phase               │
│     c) Phase 执行完成后，**必须**调用 `clarify` 工具                   │
│     d) 等待用户回复。用户说"继续/next/下一步"才能继续               │
│     e) 用户说"回滚/rollback/重来"时：                              │
│        - 执行回滚：git checkout -- . && git clean -fd                  │
│        - 然后 git stash pop 恢复 checkpoint                          │
│        - 重新执行当前 Phase                                            │
│     f) 用户说"退出/exit/stop"时：停止执行，保留当前进度                │
│                                                                    │
│  3. 此规则的优先级高于任何 Skill Body 内的连续执行指令。              │
│     即使 Skill 内写着"Phase 1...Phase 2...Phase 3"，你也必须       │
│     按上述规则逐个 Phase 执行。                                      │
│                                                                    │
│  4. 测试模式下，Phase 内部不得执行 `git commit`，所有更改保持在        │
│     working tree，确保可回滚。                                       │
│                                                                    │
└─────────────────────────────────────────────────────────┘

### Step 3: 创建 Todo 锚定（关键，解决长会话失效问题）

调用 `todo` 工具创建一个持久化任务项，确保即使会话变长、元规则被忘记时，agent 仍能通过 todo 列表看到测试模式状态：

```python
todo([
    {"id": "phase-test-active", "content": "【PHASE TEST MODE ACTIVE】所有带 Phase 的 Skill 必须逐个执行，每个 Phase 后 clarify 确认。回滚: git checkout -- . && git clean -fd && git stash pop", "status": "in_progress"}
])
```

**原理：** Hermes 的 todo 列表会在每个 turn 注入 agent 上下文。即使 conversation history 被压缩或溢出，todo 作为结构化状态仍然可见，元规则被忘记时 agent 仍能通过 todo 项"想起"测试模式。

### Step 4: 告知用户

"✅ 测试模式已开启。之后在本会话中，任何带 Phase 的 Skill 被触发后都将自动分步确认，不需要修改任何 Skill 文件。"

---

## 关闭测试模式

Trigger: 用户说"关闭测试模式"、"phase test off"、"禁用测试模式"。

Steps:
1. 确定项目根目录。
2. 删除标记文件：`rm -f "${PROJECT_ROOT}/.phase-test-mode"`
3. 将 todo 项标记为完成：
   ```python
   todo([{"id": "phase-test-active", "content": "...已关闭", "status": "completed"}], merge=True)
   ```
4. 告知用户："✅ 测试模式已关闭。之后的 Skill 将连续执行所有 Phase。"

---

## 查询状态

Trigger: 用户询问测试模式状态。

Steps:
1. 检查 `.phase-test-mode` 是否存在。
2. 检查 todo 列表中是否有 `phase-test-active` 项目。
3. 告知用户当前状态。

---

## 注意事项

- `.phase-test-mode` 是项目级标记，不同项目之间互不干扰。
- 建议将 `.phase-test-mode` 加入 `.gitignore`。
- 采用了**"三重锚定"机制**来应对长会话失效问题：
  1. **文件锚定**：`.phase-test-mode` 标记文件
  2. **会话锚定**：Session Override 元规则（短会话时可靠）
  3. **任务锚定**：todo 项目（长会话时保险）
- 如果发现 Skill 没有自动分步，可以说"开启测试模式"重新注入元规则，或检查 todo 列表中是否有 `phase-test-active`。
