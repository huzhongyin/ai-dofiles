# 用户能力画像

> 本文件由 Claude Code 在会话中自动维护，也可通过 `/update-profile` 命令手动更新。
> 加载方式：通过 `~/.claude/settings.json` 的 `additionalDirectories` 自动注入所有会话。

---

## 元信息

| 字段 | 值 |
|------|---|
| 最后更新 | 2026-03-19（更新5） |
| 更新次数 | 5 |
| 主要工作语言 | 中文 |
| 主要技术栈 | Python / Streamlit / CAN-FD / 嵌入式通信 / iOS(Swift) / Claude Code 元工作流 / Claude Code Plugin 开发 |

---

## 技术能力评估

| 领域 | 能力层级 | 评估依据 |
|------|---------|---------|
| Python | 中级 | 能读懂完整工程代码，可以理解设计思路；架构层面决策需要引导 |
| Streamlit | 初学 → 有经验 | 经历了 3 个框架 Bug（key冲突/JS越界/浮点展示）后形成深入理解 |
| CAN / CAN FD 协议 | 领域专家 | 主导设计了 CAN 信号模拟工具，熟悉 Intel/Motorola 字节序、物理值换算、帧结构 |
| DBC 文件格式 | 有经验 | 能描述 DBC 结构需求，熟悉 cantools 库 |
| 串口通信 | 基础 | 了解 pyserial，熟悉自定义帧封装协议 |
| Claude Code 元工作流 | 探索中 → **初级** | 主动设计了知识归档系统；刚刚理解 superpowers 插件架构（spec review loop、subagent dispatch 机制）；已落地多个自定义命令（/summarize、/my-first-command）；能主动识别 spec 与实现的落差，具备 plugin 架构层审视能力，完整主导了 /diagnose 功能的 brainstorming → spec → plan → review 全生命周期 |
| Claude Code Plugin 开发 | **入门中** | 正在开发自定义 plugin；理解 Agent/Skill/Command 三种组件本质区别；掌握 subagent 独立上下文机制、token 计费原理、plugin agent 与全局 agent 的作用域优先级差异 |
| iOS / Swift 开发 | 有经验 | 熟悉 iOS 项目结构、UIKit/SwiftUI、日常开发工具链 |
| Git / 版本控制 | 基础 | 未在对话中体现深度使用 |

---

## 偏好与习惯

### 回应风格
- **结论优先**：先给出结论/方案，再解释原因（不喜欢铺垫过长）
- **最小化修改**：修复 Bug 或优化时，只改有问题的部分，不接受整个函数重写
- **表格对比**：决策类问题喜欢用表格呈现多方案的对比
- **方案确认**：在实现前先确认方案，不接受"惊喜式"直接实现

### 文档习惯
- 喜欢结构化 Markdown（章节 / 表格 / 代码块）
- 主动为项目建立文档体系（README / TESTING / Agent.md）
- 重视知识归档，不让经验停留在聊天记录里

### 工作流偏好
- 已建立：知识归档系统（`/capture-knowledge` → TESTING.md / Agent.md）
- 已建立：调试工作流（`/debug-streamlit` → 结构化5步诊断）
- 已建立：实现工作流（`/implement` → 两阶段约束门控）
- 已建立：意图识别系统（`~/.claude/CLAUDE.md` + 本画像文件）
- 已建立：会话意图归档（`/identify-intent` → 按意图路由到 TESTING.md / decisions / learning）
- 已建立：画像管理（`/update-profile` 更新能力画像，`/view-profile` 查看当前状态）
- 已建立：Skill/Agent 调用日志（`/view-skill-log` → 查看今日/近N天/统计分析）
- 已建立：prompt 优化工作流（`/improve-prompt` → 专业级 prompt 优化，支持传参）
- 已建立：交互式总结命令（`/summarize` → 逐一问答后生成结构化技术文档）
- 已建立：学习迭代命令（`/my-first-command` → 内置学习 prompt，执行前可优化并写回自身）
- 习惯：完成功能/修复Bug后运行 `/capture-knowledge` 归档
- 习惯：会话结束时运行 `/identify-intent` 将学习内容和决策归档
- **新发现习惯**：学了工具/原理后立即落地为可复用命令（学完即工具化）

---

## 项目经历（影响能力评估）

| 项目 | 时间 | 关键经历 |
|------|------|---------|
| CAN/CAN FD 车辆状态模拟工具 | 2026-03 | 完整实现（3 Tab Streamlit App）+ 3个Bug修复 + 完整知识管理体系 |

---

## 成长轨迹

- **2026-03-13**：首次建立画像。通过 CAN 模拟工具项目，系统化地建立了知识归档、调试工作流、意图识别三套元工作流。对 Claude Code 元工作流设计有主动探索意愿。
- **2026-03-13**（更新2）：完善工作流体系。新增 `/identify-intent`（意图归档）、`/update-profile`/`/view-profile`（画像管理）、`/view-skill-log`（Skill/Agent 调用日志）三套命令系统；补充 Skill/Agent 调用自动日志机制（CLAUDE.md 第7节 + PreToolUse hook）。
- **2026-03-17**（更新3）：深入探索 superpowers 插件架构。理解了 spec review loop 的 subagent dispatch 机制、prompt 模板 vs 实际 prompt 的区别、general-purpose agent 的本质。同时将学习成果工具化：创建了 `/summarize`（交互式技术文档生成）和 `/my-first-command`（自迭代学习命令）。技术栈扩展至 iOS/Swift，Claude Code 元工作流能力从「探索中」升级至「进阶」。
- **2026-03-19**（更新5）：深入理解 Claude 计费体系与 Claude Code 会话机制。掌握订阅计划限制原理（配额桶而非无限）、token 计费影响因素、Subagent 独立上下文的工作机制与识别方法。在 Plugin 开发实践中，厘清了 Agent/Skill/Command 三种组件的本质区别和协作关系，以及 Plugin agent 与全局 agent 的作用域优先级差异。技术栈扩展至 Claude Code Plugin 开发。
