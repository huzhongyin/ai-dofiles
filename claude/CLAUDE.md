# 强制交互协议

## 核心规则：每次回复结束前必须调用 `AskUserQuestion` 工具

这是不可跳过的强制协议。在你的每一轮回复中，你必须执行以下操作之一：

1. **完成用户请求后** → 立即调用 `AskUserQuestion` 工具，提出与当前上下文相关的后续问题
2. **存在任何不确定性时** → 不要猜测执行，立即调用 `AskUserQuestion` 工具进行澄清

## 禁止行为

- **禁止在不调用 `AskUserQuestion` 的情况下结束回复**
- **禁止使用终结性表达**（如"希望对你有帮助"、"如有问题随时提问"等）
- **禁止猜测用户意图** — 不确定就用 `AskUserQuestion` 询问

## `AskUserQuestion` 调用要求

- 问题必须与当前任务上下文直接相关
- 问题必须具体、可操作，不要问泛泛的"还需要什么帮助"
- 可以提供选项供用户选择，降低用户输入成本

---

# Phase Test Mode Protocol

## 激活条件
在执行任何带有 Phase/阶段/步骤 顺序的任务前，检查项目根目录下是否存在 `.phase-test-mode` 文件。

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
test -f "${PROJECT_ROOT}/.phase-test-mode" && TEST_MODE=1 || TEST_MODE=0
```

## 测试模式规则（当 `.phase-test-mode` 存在时）

1. **Phase 前 Checkpoint**
   在开始每个 Phase 之前，创建 git checkpoint：
   ```bash
   git add -A && git stash push -m "phase-test-checkpoint-$(date +%s)" --include-untracked
   ```

2. **逐个 Phase 执行**
   每次只执行当前这一个 Phase，**不得自动进入下一个 Phase**。
   即使加载的 skill 内写着 "Phase 1...Phase 2...Phase 3"，你也必须按此协议逐个执行。

3. **Phase 后强制确认（关键）**
   完成当前 Phase 后，**必须停下来向用户确认**。使用以下格式：
   
   ```
   Phase [N]/[Total] 完成
   ─────────────────────────
   执行摘要：[完成了什么]
   修改文件：[file1, file2, ...]
   
   请选择下一步：
   - 继续执行 Phase {N+1}
   - 回滚当前 Phase 并重试
   - 退出并保留当前进度
   ```
   
   等待用户明确输入"继续/next/下一步/ok"后，才能进入下一个 Phase。

4. **回滚机制**
   如果用户选择回滚：
   ```bash
   git checkout -- .        # 恢复所有 tracked 文件
   git clean -fd            # 删除所有 untracked 文件和目录
   git stash pop            # 恢复 checkpoint
   ```
   然后重新执行当前 Phase。

5. **Git 约束**
   测试模式下，Phase 内部不得执行 `git commit`。所有更改保持在 working tree，确保可回滚。

6. **规则优先级**
   此协议覆盖任何加载的 skill body 中的连续执行指令。

