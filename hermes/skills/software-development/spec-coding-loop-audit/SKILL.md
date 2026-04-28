---
name: spec-coding-loop-audit
description: 对基于 skills + knowledge base 的 spec-coding 分层规范体系进行闭环链路审计，识别链路断裂点并制定修复方案。当用户需要“检查架构闭环”、“审计 skill 链路”、“检查知识飞轮”、“优化 spec-coding 流程”、“架构健康检查”时触发。
---

# Spec-Coding 架构闭环链路审计

## 触发条件
当用户需要对基于 skills + knowledge base 的分层规范体系进行健康检查时使用。典型场景：
- “检查架构闭环是否完整”
- “审计 skill 链路”
- “检查知识飞轮”
- “优化 spec-coding 流程”
- “架构健康检查”

## 审计方法论

### 第一步: 地图探测
通过以下命令快速探测项目的规范体系：
```bash
find <project-root> -type d -name ".claude" -o -name ".ai-knowledge" | sort
find <project-root>/.claude/skills -name "SKILL.md" | sort
find <project-root>/.ai-knowledge/architecture-diagrams -type f | sort
find <project-root>/.ai-engineering -type f | sort
```

### 第二步: 读取所有 SKILL.md
必须逐个读取 `.claude/skills/*/SKILL.md`，记录每个 skill 的：
- 输入是什么
- 输出是什么
- 触发条件是什么
- 是否被其他 skill 显式调用
- 是否有 `disable-model-invocation` 等阻止自动触发的标记

### 第三步: 读取架构图
读取 `.ai-knowledge/architecture-diagrams/*.mmd`，确认图中是否遗漏了某些实际存在的 skill。图纸比文字更容易暴露缺口。

### 第四步: 绘制链路地图
在脑海中构建（或用纸笔）：
```
通用层 (constitution/rules/knowledge-recall)
    ↓
需求评审 (spec-proposal → spec-design → spec-tasks)
    ↓
代码影响 (code-review / deps-lint / deps-sync)
    ↓
Bug 分析 (bug-analysis)
    ↓
闭环反馈 (spec-quality-score / post-task-review / knowledge-audit)
    → 回到通用层 (知识沉淀)
```

### 第五步: 检查每个链路节点
对每个节点问以下问题：
1. **前置连接**: 谁调用了它？调用是显式还是隐式？
2. **后置连接**: 它的输出被谁消费？有没有下游消费者？
3. **自动触发**: 它能否被自动触发？是否有 `disable-model-invocation`？
4. **输出持久化**: 它的输出是否被持久化存储？是否有人消费？
5. **反向驱动**: 下游问题能否反向驱动上游重新评审？

## 常见缺口模式

### 模式 A: 实施 → 审查 衔接断裂
- **征兆**: spec-tasks 完成后直接进入沉淀，中间缺少审查环节
- **修复**: 在 spec-tasks 中增加 Phase 5.5 审查网关，创建 `pre-commit-check` skill 串联 deps-lint + code-review-ios

### 模式 B: 改进建议无生命周期管理
- **征兆**: spec-quality-score 提出改进建议后没有跟踪机制
- **修复**: 创建 `improvement-tracker.md`，spec-quality-score 自动追加，post-task-review 自动更新状态

### 模式 C: 审计盲区无下一步引导
- **征兆**: knowledge-audit 发现盲区后只是报告，没有推荐动作
- **修复**: 在 knowledge-audit 中增加自动填充建议生成

### 模式 D: 审查风险无转化跟踪
- **征兆**: code-review-ios 发现的 保存删 问题如未修复没有跟踪
- **修复**: code-review-ios 输出到 `pending-review-risks/` 目录，bug-analysis 时关联检查

### 模式 E: Bug 修复无架构级反向驱动
- **征兆**: bug-analysis 只解决单点问题，架构缺陷类 Bug 未驱动系统性修复
- **修复**: bug-analysis 中增加根因归因升级，架构缺陷类自动建议启动 spec-proposal

### 模式 F: 预提交网关缺失
- **征兆**: 多个独立 skill 没有在提交前统一触发
- **修复**: 创建 `pre-commit-check` skill 作为统一网关

## 执行顺序原则

修复执行必须遵循依赖顺序：
1. 先创建/修改基础文件（如 improvement-tracker.md、pending-review-risks 目录）
2. 再修改引用这些文件的 skills
3. 最后更新架构图和培训文档

## 输出
- 审计报告: 链路地图 + 缺口清单 + 优化建议
- 执行修复: 按依赖顺序修改相关 SKILL.md 和文档
