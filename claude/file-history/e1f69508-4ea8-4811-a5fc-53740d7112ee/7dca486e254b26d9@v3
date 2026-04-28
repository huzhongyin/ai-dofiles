# 团队培训材料 — 实施方案

## Context

XPMotors iOS 团队已完成 L1-L5 五层 AI-Coding 工程化建设，并通过 BLE V3 RT Protocol 完成了首个 Spec 驱动开发完整闭环（F1-doc 97/A, F1-code A/95, 效率↑87.5%）。现在需要将这套体系转化为团队培训材料，让所有成员能够理解并日常使用。

用户要求覆盖 **4 个受众维度**（全量体系 + Spec 实战 + 日常指南 + 快速入门）× **4 种格式**（手册 + 幻灯片风格 + 分章节教程 + FAQ）。

**设计决策**: 以一个主文档统一承载，内部按章节分层，章节本身既可独立阅读（教程风格）也可串联培训（幻灯片风格摘要 + 详细手册内容 + FAQ 穿插）。这比创建 4×4=16 个文件更实用且易维护。

---

## 方案设计

### 产物结构

```
.ai-engineering/training/
├── README.md                        # 培训总览 + 导航
├── 01-quick-start.md                # 快速入门（30分钟上手）
├── 02-architecture-overview.md      # L1-L5 全量体系（架构演讲用）
├── 03-daily-usage-guide.md          # 日常使用指南（最常翻阅）
├── 04-spec-driven-development.md    # Spec 实战教程（含 BLE V3 案例复盘）
├── 05-knowledge-evolution.md        # 知识沉淀与自进化（L3+L5）
├── 06-faq.md                        # FAQ 手册
└── slides-summary.md               # 每章幻灯片式摘要（投影用）
```

### 各章节设计

#### README.md — 培训总览
- 培训目标和受众
- 各章节适用场景速查表
- 建议学习路径（新人 vs 资深 vs 管理者）

#### 01-quick-start.md — 快速入门（30 分钟）
- 目标: 团队成员看完能立即开始使用
- 内容:
  - Claude Code 安装与项目初始化（3 分钟）
  - CLAUDE.md 是什么 + 我们的 CLAUDE.md 做了什么（5 分钟）
  - 5 个最常用 Skill 及触发方式（10 分钟）
  - 第一个任务实操: 用 `module-context` 生成文档 / 用 `bug-analysis` 定位问题（10 分钟）
  - 上下文管理要点: /clear、不要混合任务（2 分钟）

#### 02-architecture-overview.md — L1-L5 全量体系
- 目标: 理解"为什么这样建"，适合团队分享会
- 内容:
  - 五层架构图 + 每层一句话总结
  - 核心痛点 → 解决方案映射表
  - 参考方法论来源（Anthropic/搜狗/淘系/OpenSpec）
  - 数据佐证: 知识库规模（40 知识点 + 26 踩坑 + 15 模块文档）
  - 数据佐证: 审计健康度演进（B+ 82 → A 96）
  - 数据佐证: 首个 Spec 案例效率提升 87.5%
  - 格式: 每个要点先有幻灯片式摘要框，再展开详细说明

#### 03-daily-usage-guide.md — 日常使用指南
- 目标: 日常工作中最常翻阅的参考手册
- 内容:
  - **开始任务前**: 确认 CLAUDE.md、加载知识（knowledge-recall 自动触发）
  - **开发中**: Plan Mode 使用、12 个 Skill 速查表（名称+触发词+一句话用途）、Rules 的 3 个文件覆盖内容
  - **代码审查**: code-review-ios Skill 使用
  - **任务完成后**: post-task-review 知识沉淀流程
  - **定期维护**: knowledge-audit 知识审计
  - 每个场景都附带具体操作步骤 + 示例截图描述

#### 04-spec-driven-development.md — Spec 实战教程
- 目标: 掌握 Spec 驱动开发全流程
- 内容:
  - **概念**: 从 Vibe Coding 到范式编程的演进
  - **项目宪法**: constitution.md 的 6 大约束域
  - **三阶段流程**: proposal → design → tasks
  - **实战案例复盘**: BLE V3 RT Protocol
    - proposal 阶段: 需求输入 → 知识召回 → 影响分析 → 4 个疑问点
    - design 阶段: 正向/反向调用链 → Constitution 检查 → 冲突风险标注
    - tasks 阶段: 15 个 Task 拆解 → 隐含依赖检测 → submodule 提交计划
    - 实施阶段: 13 文件 × 3 层架构 × 2 submodule
    - 沉淀阶段: +1 知识点 / +1 踩坑 / 2 更新
    - 评分: F1-doc 97, F1-code A, 效率↑87.5%
  - **关键经验**: 疑问点机制避免盲猜、Phase 2.5 隐含依赖检测

#### 05-knowledge-evolution.md — 知识沉淀与自进化
- 目标: 理解知识体系运转机制
- 内容:
  - **知识库结构**: modules / knowledge-points / pitfalls 三层
  - **知识点格式**: 触发关键词 + 分类 + 优先级 + 内容
  - **沉淀 SOP**: 6 步流程（回顾→提炼→分类→打标→存储→索引）
  - **自进化飞轮**: 实施→评分→改进→Skill 优化 → 循环
  - **审计机制**: 新鲜度/覆盖度/召回效果/文档同步
  - **实际效果**: 首次审计发现 14 路径错误全部修复、健康度 82→96

#### 06-faq.md — FAQ 手册
- 按使用场景组织的常见问题（预估 25-30 个问题）:
  - **入门类**: Claude Code 怎么安装、CLAUDE.md 放哪里、Skills 怎么触发
  - **日常使用类**: 上下文满了怎么办、/clear 什么时候用、Plan Mode vs 直接编码
  - **知识库类**: 怎么添加知识点、踩坑怎么记录、知识点没被召回怎么办
  - **Spec 类**: proposal 的疑问点怎么填、design 的调用链怎么追、tasks 的验证步骤
  - **维护类**: 知识审计多久做一次、模块文档过时了怎么更新
  - **故障排除类**: Skill 没触发怎么办、AI 生成的代码路径错误怎么办

#### slides-summary.md — 幻灯片式摘要
- 每章提炼 5-8 页"幻灯片"（标题 + 3-5 个要点 + 视觉图示）
- 适合团队分享会投影使用
- 每页控制在半屏以内

---

## 关键文件引用

培训材料需要准确引用的项目资产:

| 类别 | 文件数 | 关键文件 |
|------|--------|---------|
| CLAUDE.md | 1 | `/CLAUDE.md`（项目根） |
| Rules | 3 | `.claude/rules/ios-{architecture,coding,vehicle-sdk}.md` |
| Skills | 11 | `.claude/skills/{module-context,knowledge-recall,oc-to-swift,new-swift-module,code-review-ios,bug-analysis,spec-proposal,spec-design,spec-tasks,post-task-review,knowledge-audit,spec-quality-score}/SKILL.md` |
| 模块文档 | 15 | `.ai-knowledge/modules/*.md` |
| 知识点 | 40 | `.ai-knowledge/knowledge-points/*.kp.md` |
| 踩坑记录 | 6 | `.ai-knowledge/pitfalls/*.md` |
| Spec 模板 | 3 | `.ai-knowledge/specs/template-{proposal,design,tasks}.md` |
| 宪法 | 1 | `.ai-knowledge/specs/constitution.md` |
| Spec 案例 | 3 | `.ai-knowledge/specs/ble-v3-rt-protocol/{proposal,design,tasks}.md` |
| 评分卡 | 1 | `.ai-knowledge/quality-scores/score-ble-v3-rt-protocol-2026-04-08.md` |
| 审计报告 | 2 | `.ai-knowledge/audit-reports/audit-2026-04-08{,-v2}.md` |
| 进化日志 | 1 | `.ai-knowledge/evolution-log.md` |
| 索引 | 1 | `.ai-knowledge/index.md` |
| 团队指南 | 1 | `.ai-engineering/L1-tool-chain/team-guide.md` |
| 路线图 | 1 | `.ai-engineering/roadmap.md` |

---

## 实施顺序

1. **创建目录**: `.ai-engineering/training/`
2. **README.md**: 培训总览 + 导航
3. **01-quick-start.md**: 快速入门（最高优先级，团队能立即用）
4. **03-daily-usage-guide.md**: 日常指南（第二高频使用）
5. **02-architecture-overview.md**: 全量体系（分享会用）
6. **04-spec-driven-development.md**: Spec 实战（含案例复盘）
7. **05-knowledge-evolution.md**: 知识自进化
8. **06-faq.md**: FAQ
9. **slides-summary.md**: 幻灯片摘要
10. **更新 changelog.md**: 记录培训材料产出

---

## 验证方式

1. 新成员测试: 让不熟悉体系的同事只看 01-quick-start.md，验证能否在 30 分钟内完成首个 Skill 调用
2. 完整性检查: 确认所有 12 个 Skill、3 个 Rules、40 个知识点在材料中都有提及
3. 案例准确性: 04 中的 BLE V3 案例数据与评分卡/进化日志一致
