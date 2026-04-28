# Spec Coding 分层规范架构改造 · 复盘笔记

**时间**: 2026-04-17
**范围**: XPMotors iOS 项目 spec coding 体系从「项目级单层」升级到「五层按需加载」
**产物**:
- Spec: `docs/superpowers/specs/2026-04-17-spec-coding-tiered-architecture-design.md`
- Plan: `docs/superpowers/plans/2026-04-17-spec-coding-tiered-architecture.md`
- Validation: `docs/superpowers/specs/2026-04-17-spec-coding-tiered-architecture-validation.md`

## 架构要点
1. **五层**: L1 project 根 / L2 主工程 app (`XiaoPengQiChe/`) / L3 target (`.claude/targets/`) / L4 submodule / L5 localpod
2. **单一数据源**: `.ai-knowledge/module-registry.md` YAML 块（id / level / path / knowledge / owner_repo / keywords）
3. **依赖图**: 每个模块 `knowledge/deps.yml` 声明 `depends_on[]`，含可选 `critical_constraints`（path#anchor）与 `trigger_keywords`（v0.3，用于依赖扩展时上下文过滤）
4. **按需加载（knowledge-recall v0.2）**: 路径命中 ∪ 关键词命中 → 沿 deps 递归（深度 ≤ 2）→ 按 `trigger_keywords` 精筛 → 打印层级清单

## 关键踩坑
1. **submodule 被主仓 .gitignore**: `submodule/` 在主仓 .gitignore 中，无 `.gitmodules`。主仓 commit 不含 submodule pointer，每个 submodule 需独立 clone 与提交。
2. **L2 命中即全量展开**: 纯 UI 任务若命中 XiaoPengQiChe，无差别加载车控/路由 critical_constraints。修复方案：`trigger_keywords` 字段按任务上下文过滤。
3. **锚点匹配以 level-2 标题为准**: constitution.md 中的 `## xxx` 是 deps.yml `path#xxx` 的解析锚点，必须同步维护。

## 通用化机制
- `spec-coding-scaffold` skill: 4 种 level 模板（app / target / submodule / localpod）+ constitution.template + deps.schema.yml
- 批量骨架：6 submodule + 4 target + 8 高优先级 LocalPod 一次性生成；22 个低优先级 LocalPod 仅登记 registry

## 后续建议
- L4/L5 骨架待逐模块精修 constitution 实质内容
- spec-design / spec-proposal / spec-tasks 加 `--scope` 参数以支持 submodule 内独立 spec 流
- 定期 `knowledge-audit` 校验 deps.yml 锚点有效性
