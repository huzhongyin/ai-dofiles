# 用户偏好设置

> 本文件记录用户的明确偏好配置，用于 Claude 在所有项目中保持一致的行为风格。
> 与 USER_PROFILE.md 一起通过 additionalDirectories 自动加载。

---

## 回应风格

```yaml
language: 中文（默认）
tone: 直接、专业、不废话
structure: 结论 → 解释 → 细节（金字塔原则）
code_comments: 中文注释
emoji: 仅在文档标题/警告时使用，正文不用
```

---

## 代码修改原则

```yaml
change_scope: minimal  # 最小化修改，不重写不相关的代码
confirm_before_impl: true  # 非trivial改动，先输出方案等确认
rewrite_whole_file: false  # 禁止整个文件重写
new_file_threshold: "功能独立且>50行才考虑新建文件"
```

---

## 方案呈现偏好

```yaml
comparison_format: table  # 多方案用表格对比
recommendation: always  # 对比后必须给出推荐+理由
tradeoffs: required  # 必须说明方案的权衡点
```

---

## 文档偏好

```yaml
format: markdown
headers: always  # 使用标题层级组织内容
tables: preferred  # 优先用表格呈现对比/清单
code_blocks: language_tagged  # 代码块必须标注语言
length: comprehensive  # 文档写完整，不省略
```

---

## 知识归档偏好

```yaml
bug_fix_archive: TESTING.md  # Bug修复后必须归档
constraint_archive: Agent.md  # 新发现的约束归入约束章节
learning_archive: ~/.claude/learning/  # 学习内容单独存放
trigger: end_of_session  # 每次会话结束时触发 /capture-knowledge
```

---

## 意图识别偏好

```yaml
auto_detect: true  # 自动检测意图，不需要声明给用户
ux_optimize_confirm: true  # UX优化必须先确认目标
learning_mode_document: true  # 学习会话结束后建议归档
profile_update_suggest: true  # 发现能力变化时建议更新画像
```
