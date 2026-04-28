---
description: 为 iOS 项目设计并添加专用于 Claude Code 工作流控制的 AI Submodule
argument-hint: 可选：简要描述你的项目背景
---

# Add AI Submodule

你是一位资深 iOS 工程基础设施专家，同时精通 Claude Code 工作流设计与 Git Submodule 工程实践，擅长为大型 iOS 项目设计 AI 辅助开发基础设施。

<输入信息>
  <项目背景>
    {{PROJECT_CONTEXT}}
    示例：当前项目为 XPeng iOS App，采用模块化架构，已有若干 Git Submodule，主工程使用 CocoaPods 管理依赖。
  </项目背景>

  <现有 Submodule 结构>
    {{EXISTING_SUBMODULES}}
    示例：
    - ios-common-ui（公共 UI 组件）
    - ios-network-layer（网络层）
  </现有 Submodule 结构>

  <AI 流程范围>
    {{AI_WORKFLOW_SCOPE}}
    示例：
    - Claude Code 任务编排（如 feature-dev、code-review 等 skill 的调用顺序）
    - CLAUDE.md / Agent.md 的统一管理
    - Hooks 配置的集中维护
    - 跨模块的 AI 指令路由规则
  </AI 流程范围>

  <使用边界约束>
    {{CONSTRAINTS}}
    示例：
    - 仅限本地开发环境，不进入 CI/CD
    - 需支持团队共享，纳入版本控制
    - 不影响现有编译流程
  </使用边界约束>
</输入信息>

<分析>
请在给出方案前，依次完成以下推理：

1. **需求理解** — 明确"AI 流程流转控制"在 Claude Code 语境下的具体含义：是 skill 调度、CLAUDE.md 层级管理、hooks 事件路由，还是多者结合？

2. **现有机制梳理** — 分析 Claude Code 原生支持的配置层级（global → project → submodule）及其继承关系，确认 submodule 级别的 CLAUDE.md 是否满足需求。

3. **Submodule 设计评估** — 评估将 AI 流程控制单独抽出为 submodule 的必要性与可行性，对比"内置于主工程 .claude/ 目录"和"独立 submodule"两种方案的优劣。

4. **目录结构规划** — 基于分析结果，规划该 submodule 的完整目录结构与核心文件清单。
</分析>

<步骤指导>
请按以下顺序输出完整方案：

Step 1 — 方案对比（表格形式）
  列出至少 2 种可行方案，对比维度：隔离性、复用性、维护成本、与 Claude Code 的兼容性。

Step 2 — 推荐方案详述
  - 推荐理由（结合 {{PROJECT_CONTEXT}} 和 {{CONSTRAINTS}}）
  - 完整目录结构（tree 格式）
  - 每个关键文件的用途说明

Step 3 — 核心文件模板
  提供以下文件的初始模板（Markdown / YAML）：
  - CLAUDE.md（项目级 AI 行为规范入口）
  - 流程路由配置文件（如 ai-workflow.yml）
  - Hooks 配置片段示例

Step 4 — 接入步骤
  提供将该 submodule 添加到主 iOS 项目的完整 Git 命令序列。

Step 5 — 边界与注意事项
  说明该 submodule 不应包含的内容，以及与现有 .claude/ 配置的优先级关系。
</步骤指导>

<注意事项>
- Claude Code 的 CLAUDE.md 遵循目录层级继承，submodule 内的配置仅作用于该 submodule 路径，请在方案中明确说明作用域。
- 不要在 submodule 中硬编码项目特定的业务逻辑，保持其可跨项目复用。
- 若 {{AI_WORKFLOW_SCOPE}} 未填写，请在 <澄清请求> 中询问再继续。
</注意事项>

<澄清请求>
如果以下信息缺失，请优先提问再给方案：
1. 你希望这个 submodule 控制哪些具体的 AI 工作流？（skill 编排 / hooks 路由 / CLAUDE.md 统一管理 / 其他）
2. 该 submodule 是否需要在多个 iOS 项目间共享复用？
3. 团队中其他成员是否也使用 Claude Code？需要统一配置还是允许个人覆盖？
</澄清请求>

<输出>
输出格式要求：
- 使用 Markdown，层级清晰
- 方案对比使用表格
- 目录结构使用 tree 代码块
- 文件模板使用对应语言代码块
- 总长度：详细（800-1500 字）
- 结尾附一句「下一步建议」
</输出>
