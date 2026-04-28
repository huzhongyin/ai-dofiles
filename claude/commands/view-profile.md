# view-profile

查看当前用户能力画像、偏好设置，以及历史归档统计。

---

## 执行步骤

### Step 1：读取画像文件

并行读取：
- `~/.claude/profile/USER_PROFILE.md`
- `~/.claude/profile/PREFERENCES.md`

### Step 2：统计归档历史

扫描以下目录，统计归档文件数量：
- `~/.claude/learning/` — 学习文档
- `~/.claude/decisions/` — 架构决策
- `~/.claude/reviews/` — 代码审查

输出统计摘要：
```
【归档统计】
学习文档：N 篇（最新：YYYY-MM-DD-<topic>）
架构决策：N 篇
代码审查：N 篇
```

### Step 3：输出画像摘要

格式化输出当前状态：

```
━━━ 用户能力画像摘要 ━━━

【核心技术能力】
• Python：中级
• Streamlit：有经验
• CAN/CAN FD：领域专家
• ...

【工作偏好】
• 回应风格：结论优先
• 代码修改：最小化
• ...

【已建立工作流】
• /implement — 两阶段约束门控
• /debug-streamlit — 结构化5步诊断
• /capture-knowledge — 知识归档
• /identify-intent — 意图识别归档
• ...

【画像最后更新】YYYY-MM-DD（共更新 N 次）

━━━ 结束 ━━━
```

### Step 4：提供操作建议

根据画像状态，给出建议：
- 如果距上次更新超过30天：「建议运行 `/update-profile` 同步最新状态」
- 如果学习文档较多但能力画像未反映：「发现 N 篇学习文档，建议同步到能力评估」

---

## 示例调用

```
/view-profile
```
