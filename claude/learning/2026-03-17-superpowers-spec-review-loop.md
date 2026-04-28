# Superpowers Spec Review Loop 架构笔记

**日期：** 2026-03-17
**来源：** 会话查询 + 文件探索

---

## 核心结论

"Spec review loop with subagent" 属于 **`superpowers:brainstorming` skill** 的一部分（Step 7）。

---

## 文件位置

```
~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.2/
├── skills/
│   ├── brainstorming/
│   │   ├── SKILL.md                         ← 主技能，Step 7 含 spec review loop
│   │   └── spec-document-reviewer-prompt.md ← subagent 的 reviewer prompt
│   └── subagent-driven-development/
│       ├── SKILL.md                         ← 执行阶段两阶段 review
│       └── spec-reviewer-prompt.md          ← 执行阶段 spec reviewer prompt
```

---

## 两处 Spec Review 的区别

| 位置 | Skill | 触发时机 | 目的 |
|------|-------|---------|------|
| `brainstorming/SKILL.md` Step 7 | `superpowers:brainstorming` | 写完设计文档后、给用户看之前 | 自动审查 spec 质量（最多5轮），确保设计文档完整 |
| `subagent-driven-development/SKILL.md` | `superpowers:subagent-driven-development` | 每个任务实现后 | 两阶段：①spec compliance（代码符合spec？）②code quality |

---

## 关键机制

- brainstorming 的 spec review loop：**主 agent 修 → subagent 审 → 循环**，最多5轮，通过后才展示给用户
- subagent-driven-development 的 review：**implementer subagent 实现 → spec reviewer subagent 审 → code quality reviewer subagent 审**，发现问题回到 implementer 修复再审

---

## Spec Review Loop 详细机制（2026-03-17 补充）

### 流程图

```
写完 spec 文件（保存+commit）
    ↓
dispatch Agent(general-purpose)
    prompt = spec-document-reviewer-prompt.md 模板
             注入 [SPEC_FILE_PATH]（不传 session history！）
    ↓
subagent Read 文件 → 按 checklist 审查
    ↓
返回标准格式：Status: ✅ Approved | ❌ Issues Found
    ↓
✅ → 退出循环 → 展示给用户
❌ → 主 agent 修复 spec → 重新 dispatch（最多5轮）
```

### 关键设计决策：为什么不传 session history

- 避免 context window 超限
- 保持 reviewer 客观性（不受对话情绪影响）
- subagent 只看文件内容本身，结果更可靠

### Reviewer Checklist（来自 spec-document-reviewer-prompt.md）

| 类别 | 检查项 |
|------|--------|
| 完整性 | TODOs、占位符、TBD、未完成段落 |
| 覆盖度 | 缺失错误处理、边界情况、集成点 |
| 一致性 | 内部矛盾、冲突需求 |
| 清晰度 | 模糊需求 |
| YAGNI | 未被请求的功能、过度设计 |
| 范围 | 是否聚焦（不跨多个独立子系统） |
| 架构 | 单元边界清晰、接口明确、可独立理解和测试 |

---

## Spec Review Prompt 生成机制（2026-03-17 深入）

### 模板 vs 最终 prompt

`spec-document-reviewer-prompt.md` 只是**骨架模板**，真正 dispatch 的 prompt 由主 agent 组装：

```
模板（固定）
  + 项目名称（从会话提炼）
  + 核心目标摘要（从会话提炼）
  + 用户上下文（从会话提炼）
  + 针对当前 spec 的定制审查维度
  + 实际文件路径
= 最终 dispatch 给 subagent 的 prompt
```

SKILL.md 原文："dispatch spec-document-reviewer subagent with **precisely crafted review context**"
→ "precisely crafted" = 主 agent 自主扩充，不是机械套模板

### general-purpose agent 是什么

- **不是文件**，是 Claude Code 内置 `Agent` 工具的预设类型
- 调用：`Agent(subagent_type="general-purpose", prompt="...")`
- 特点：拥有所有工具（Read/Glob/Grep/Bash），无专业限制
- subagent 收到 prompt 后，自己 Read 文件执行审查，结果返回主 agent

---

## 会话归档补充（2026-03-17 下午）

### /improve-prompt 命令机制

- 文件位置：`~/.claude/commands/improve-prompt.md`
- 触发方式：`/improve-prompt <待优化的prompt文本>`
- `$ARGUMENTS` 占位符接收命令参数
- 这是用户自建的全局自定义命令，非 Claude Code 官方内置

### /summarize 命令（新建）

- 文件位置：`~/.claude/commands/summarize.md`
- 交互式：逐一询问4个问题（对象类型/读者/踩坑记录/工具栈粒度）收集后生成文档
- 输出结构：TL;DR → 背景目标 → 架构总览 → 流程 → 工具调用栈 → 原理深解 → 速查表

### /my-first-command 命令（新建）

- 文件位置：`~/.claude/commands/my-first-command.md`
- 功能：内置 Claude Code 学习 prompt，执行前可选择修改目标，修改后自动写回文件
- 设计亮点：「执行前展示目标 → y/n → 优化并写回 → 再执行」的自迭代循环
