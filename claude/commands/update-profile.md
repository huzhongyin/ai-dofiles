# update-profile

手动更新用户能力画像（`~/.claude/profile/USER_PROFILE.md`）和偏好设置（`~/.claude/profile/PREFERENCES.md`）。

---

## 更新描述

$ARGUMENTS

---

## 执行步骤

### Step 1：读取现有画像

读取以下文件，了解当前状态：
- `~/.claude/profile/USER_PROFILE.md`
- `~/.claude/profile/PREFERENCES.md`

### Step 2：解析更新内容

根据 `$ARGUMENTS`，将描述映射到具体字段：

**能力层级更新示例：**
- "我现在对Streamlit很熟悉了" → `USER_PROFILE.md` 技术能力评估表中 Streamlit 行
- "我学会了Motorola字节序的算法" → USER_PROFILE.md 中 CAN/CAN FD 能力层级描述

**偏好更新示例：**
- "以后不用给我加代码注释了" → `PREFERENCES.md` 的 `code_comments`
- "我想要更简短的回答" → `PREFERENCES.md` 的 `length`

**新项目记录示例：**
- "我开始了一个新的iOS项目" → `USER_PROFILE.md` 项目经历表，追加新行

### Step 3：输出修改草稿

```
━━━ 文件：~/.claude/profile/USER_PROFILE.md ━━━
修改位置：<章节名称>

原文：
<原有内容>

修改为：
<新内容>

━━━ 结束 ━━━
```

### Step 4：直接写入

**不需要等待用户确认**，直接使用 Edit 工具将修改内容写入对应文件，同时更新「最后更新」日期，并将「更新次数」加1。

写入完成后，输出一行摘要：
```
✅ USER_PROFILE.md — 已更新 <字段名>（更新次数：N）
```

---

## 示例调用

```
/update-profile 我现在对Streamlit有了深入理解，能独立Debug框架级Bug
/update-profile 以后回答我时不需要太详细的背景解释，直接给结论
/update-profile 新增项目：iOS车联网App，2026-03开始
```
