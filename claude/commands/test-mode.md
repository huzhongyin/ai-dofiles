# 测试模式开关

控制当前项目下所有带 Phase 的 Skill 是否以测试模式执行（逐步确认）。

## 开启测试模式

Trigger: 用户说 "on"、"enable"、"开启"、"打开"、"激活"。

Steps:
1. 确定项目根目录：`PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)`
2. 创建标记文件：`touch "${PROJECT_ROOT}/.phase-test-mode"`
3. 如果当前是 git 仓库且 working tree 有改动：
   ```bash
   git add -A && git stash push -m "test-mode-entry-$(date +%s)"
   ```
4. 输出："✅ 测试模式已开启。当前项目下所有带 Phase 的 Skill 将在每个 Phase 完成后暂停，等待确认。选项：[继续] [回滚并重试] [退出]。"

## 关闭测试模式

Trigger: 用户说 "off"、"disable"、"关闭"、"禁用"。

Steps:
1. 确定项目根目录。
2. 删除标记文件：`rm -f "${PROJECT_ROOT}/.phase-test-mode"`
3. 输出："✅ 测试模式已关闭。Skill 将连续执行所有 Phase，中途不停顿。"

## 查询状态

Trigger: 用户诲问 "status"、"状态"、"是否开启"。

Steps:
1. 检查项目根目录下 `.phase-test-mode` 是否存在。
2. 输出当前状态。
