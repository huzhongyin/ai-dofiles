# 架构决策：project-reader `/diagnose` 功能扩展

**日期：** 2026-03-17
**项目：** project-reader Claude Code plugin
**决策类型：** 功能扩展架构选型

---

## 背景

project-reader plugin 原始 spec 目标 #3 明确要求「辅助后续问题定位」，但 5 个已实现命令（/read、/trace、/deps、/explain、/export）均不支持「用户提供线上报障日志 → 定位根因」的使用场景。本次设计填补这一空白。

---

## 问题定义

用户提供日志文件（iOS Crash Log / 系统日志 / 自定义 App 日志 / Logcat）及可选的时间点或关键词，需要 plugin 自动：
1. 解析日志，提取错误症状
2. 关联已缓存的工程分析（PROJECT_MAP / CALL_CHAINS / DEP_GRAPH）
3. 推断根本原因，评估影响范围，给出修复建议
4. 持久化诊断结果，支持跨会话复用和历史缺陷比对

---

## 方案对比

| 方案 | 描述 | 优点 | 缺点 | 结论 |
|------|------|------|------|------|
| A：轻量扩展 | 在 `/explain` 增加 `--log` 参数 | 改动最小 | explain-agent 职责混乱，无法独立管理知识库 | ❌ 否决 |
| B：独立命令 + 共享 Agent | 新增 `/diagnose` + `log-investigator` agent + `log-analyzer` skill | 职责清晰，与现有架构模式一致，可扩展 | 新增 3 个组件文件 | ✅ 选择 |
| C：独立命令 + 独立分析管道 | 新增 3 命令 + 3 层 agent 流水线 | 功能最完整 | 严重 YAGNI，维护成本高 | ❌ 否决 |

**选择方案 B 的理由：**
- 与现有 command → agent → skill 三层架构完全对齐，新人零学习成本
- DEFECT_KB/ 子目录与 CALL_CHAINS/、LEGACY_NOTES/ 同级，符合现有缓存设计语言
- 控制在最小必要范围，未来可增量扩展

---

## 核心架构决策

### 1. 三层组件分工

| 组件 | 路径 | 职责边界 |
|------|------|---------|
| Command `/diagnose` | `commands/diagnose.md` | 参数解析、激活门控、前置检查、缓存命中、分发 |
| Agent `log-investigator` | `agents/log-investigator.md` | 5 阶段协调：解析→关联→影响→比对→推断 |
| Skill `log-analyzer` | `skills/log-analyzer/SKILL.md` | 纯知识层：格式识别、符号提取、时间切片 |

### 2. DEFECT_KB 缓存目录设计

```
~/.claude/analyses/<project_key>/
├── PROJECT_MAP.md
├── DEP_GRAPH.md
├── CALL_CHAINS/
├── LEGACY_NOTES/
└── DEFECT_KB/           ← 新增
    ├── INDEX.md         ← 缺陷索引
    └── YYYYMMDD-HHMMSS-<keyword>.md
```

### 3. INDEX.md 复合键设计（重要）

INDEX.md 的「关键词」字段存储**复合键**：`<logfile_hash>|<time_or_empty>|<keywords_joined_or_empty>`

- `logfile_hash` = 文件**内容**的 md5[:8]（非路径 hash，路径变了也能命中）
- 精确命中：三字段完全相同 → 直接返回历史报告
- 模糊命中：keyword 子串匹配 OR 错误类型相同 → 提示相似缺陷，继续分析
- `--reanalyze` flag：传 `overwrite_index_entry=true` 给 agent，覆盖旧条目

### 4. log-analyzer skill 符号提取规则

- 业务前缀（首选）：`XP[A-Z][A-Za-z]+`（小鹏 OC 业务类）
- 通用降权提取：`[A-Z][A-Za-z]+`（系统/第三方类权重低）
- 系统框架符号（`com.apple.*`、`libsystem_*`）降低权重而非排除

### 5. agent 参数传递规范

command 传给 agent 的完整参数集：
- `logfile`（绝对路径，command 负责 realpath 转换）
- `logfile_hash`（command 计算，agent 写入 INDEX 时使用）
- `time`、`keyword`、`project_key`、`cache_dir`
- `overwrite_index_entry`（`--reanalyze` 时为 true）

---

## 产出文件

| 文件 | 路径 | 审查状态 |
|------|------|---------|
| Spec 文档 | `docs/superpowers/specs/2026-03-17-project-reader-diagnose-design.md` | ✅ spec-document-reviewer 通过 |
| 实现计划 | `docs/superpowers/plans/2026-03-17-project-reader-diagnose.md` | ✅ plan-document-reviewer 通过（4轮修复后） |

---

## 经验总结

1. **spec 与实现的落差需要主动识别**：spec 中写了目标但没有对应命令时，不能假设「以后再加」，应在 brainstorming 阶段直接设计
2. **复合键设计的两侧一致性**：写入侧（agent）和读取侧（command）必须使用完全相同的格式，否则精确命中永远失效——plan reviewer 在第一轮就识别出了这个跨组件一致性问题
3. **agent 输入参数需要完整声明**：agent 用到的每个值（如 `logfile_hash`）都必须出现在输入参数列表中，不能假设 agent 会自行计算
4. **`realpath` 转换应尽早执行**：在任何依赖路径的计算（hash、缓存查询）之前，先将用户输入的相对路径转换为绝对路径
