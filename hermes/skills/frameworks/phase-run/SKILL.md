---
name: phase-run
description: Execute any phased skill in step-by-step test mode with checkpoint/rollback. Reads target skill content, splits phases, and inserts confirmation gates.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [phased-execution, orchestrator, testing, debug, framework]
    related_skills: [phase-test-mode]
---

# Phase-Run Orchestrator

一个通用的 Phased Skill 执行器，支持测试模式（逐步确认 + 回滚）和正常模式。

## 触发方式

1. 显式调用：`phase-run <skill-name>` 或 `测试执行 <skill-name>`
2. 在测试模式下：直接说 `<skill-name>`

例如：
- phase-run deployment
- phase-run migration
- 测试执行 database-setup

## 执行流程

### Step 0: 检测试模式

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
if [ -f "${PROJECT_ROOT}/.phase-test-mode" ]; then
    TEST_MODE=1
else
    TEST_MODE=0
fi
```

### Step 1: 解析目标 Skill

从用户输入中提取 skill 名称（比如用户说"phase-run deployment"，目标是 deployment）。

使用 `skill_view(name="<target-skill>")` 读取目标 skill 的完整内容。

### Step 2: Phase 拆解

分析目标 skill 内容，识别出所有 Phase：
- 查找 "## Phase 1", "## Phase 2" 等标记
- 也兼容 "阶段 1"、"步骤 1"、"Step 1" 等变体
- 提取每个 Phase 的具体执行指令

如果没有明显的 Phase 标记，将整个 skill 视为单个 Phase。

### Step 3: 执行策略

#### 正常模式 (TEST_MODE=0)

直接按照目标 skill 的原始内容执行，不拆解 Phase。

可选：使用 `delegate_task` 委托给子 agent 执行。

#### 测试模式 (TEST_MODE=1)

对于每个 Phase i 从 1 到 N：

**A. Checkpoint 打点**

如果是 git 仓库：
```bash
git add -A
git stash push -m "phase-run-pre-${i}-$(date +%s)" --include-untracked
```

记录 stash 索引为 `CHECKPOINT_${i}`。

**B. Phase 执行**

提取并执行 Phase i 的指令。

可选策略：
1. 直接在当前会话执行（简单 Phase）
2. `delegate_task` 委托给子 agent（复杂 Phase）

**C. Gate 断点（关键）**

Phase i 执行完成后，**必须**调用 `clarify` 工具：

```
Question: "Phase i/N 完成。

执行结果摘要：
- 修改的文件：[files]
- 主要操作：[summary]
- 状态：成功/部分失败

请选择下一步："

Choices: [
    "继续执行 Phase {i+1}",
    "回滚当前 Phase 并重试",
    "回滚到上一个 Phase 重试",
    "退出测试，保留当前进度",
    "完全放弃并恢复初始状态"
]
```

**D. 处理用户选择**

1. **继续执行 Phase {i+1}**
   - 如果有 git checkpoint，提交当前 Phase 的更改：
     ```bash
     git add -A && git commit -m "wip: phase ${i} complete" --no-verify || true
     ```
   - 进入下一个 Phase

2. **回滚当前 Phase 并重试**
   - 执行 rollback：
     ```bash
     git checkout -- .       # 恢复所有 tracked 文件
     git clean -fd           # 删除所有 untracked 文件和目录
     git stash pop           # 恢复 checkpoint
     ```
   - 重新执行当前 Phase i

3. **回滚到上一个 Phase 重试**
   - 如果当前是 Phase 1，同选项2（回滚到初始状态）
   - 如果当前是 Phase i > 1：
     - 回滚到 Phase i-1 的 checkpoint
     - 重新执行 Phase i-1（然后用户可能又要确认）

4. **退出测试，保留当前进度**
   - 停止执行，保留已完成的 Phase 结果
   - 告知用户之后可以用 `phase-run <skill-name>` 从中断处继续

5. **完全放弃并恢复初始状态**
   - 回滚到最初的 checkpoint（Phase 1 之前）
   - 删除所有测试产生的临时提交
   - 告知用户已恢复

### Step 4: 完成处理

所有 Phase 执行完成后：

1. 汇总完整执行结果
2. 如果 TEST_MODE=1 且用户确认，可执行：
   ```bash
   git add -A && git commit -m "feat: complete $(skill-name) via phase-run"
   ```
3. 提示用户"是否关闭测试模式"

## 非 Git 项目的处理

如果当前目录不是 git 仓库：

- 无法提供自动回滚功能
- 测试模式下，Gate 处的选项变为：
  - "继续执行下一个 Phase"
  - "退出并保留当前进度"
- 如果用户需要回滚，需要手动撤销更改

## 使用示例

### 开启测试模式
```
用户: 开启测试模式
Agent: 已创建 .phase-test-mode。之后 phase-run 将逐步执行。
```

### 测试执行 Skill
```
用户: phase-run deployment

Agent: 
1. 检测到 .phase-test-mode，进入测试模式
2. 读取 deployment skill 内容
3. 识别到 5 个 Phase
4. 执行 Phase 1...
5. [clarify] Phase 1/5 完成。请选择...

用户: 回滚并重试
Agent: 回滚完成，重新执行 Phase 1...

用户: 继续
Agent: 执行 Phase 2...
...
```

### 正常模式执行
```
用户: phase-run migration
Agent: 未检测到测试模式，按原始 skill 内容直接执行。
[...直接执行所有 Phase...]
```

## 与 phase-test-mode skill 的配合

本 skill 与 `phase-test-mode` 配合使用：

- `phase-test-mode`：负责开启/关闭测试模式（创建/删除 `.phase-test-mode` 文件）
- `phase-run`：负责根据 `.phase-test-mode` 的存在于否决定执行策略

用户可以用同一个对话：
```
用户: 开启测试模式，然后 phase-run deployment
```
