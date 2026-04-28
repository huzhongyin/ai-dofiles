# additionalDirectories 工作机制

**日期：** 2026-03-16
**主题：** Claude Code 中 `additionalDirectories` 的作用与必要性

---

## 核心结论

`additionalDirectories` 解决的是 **Read 工具的可信目录白名单**问题，而不是"自动加载内容"。

---

## 背景：为什么需要它

Claude Code 启动时的当前工作目录（CWD）是项目目录，例如 `/Users/xpeng/Projects/my-app/`。

`Read` 工具默认只信任 **CWD 及其子目录**的文件读取。

| 文件 | 加载方式 | 需要 additionalDirectories？ |
|------|---------|-------------------------------|
| `~/.claude/CLAUDE.md` | 系统层面特殊注入，绕过 CWD 限制 | ❌ 不需要 |
| `~/.claude/profile/USER_PROFILE.md` | 需要 Claude 主动 `Read` 读取 | ✅ 需要授权 |

关键点：**CLAUDE.md 的系统注入特权不会传递给同目录下的其他文件**。

---

## 完整工作流程

```
CLAUDE.md 被系统自动注入
    ↓ 指示 Claude "去读 USER_PROFILE.md"
    ↓
Claude 尝试用 Read 工具读取 ~/.claude/profile/USER_PROFILE.md
    ↓ 该路径不在当前 CWD 下
    ↓
additionalDirectories 将 ~/.claude/profile/ 加入白名单
    ↓
读取成功
```

---

## 配置位置

`additionalDirectories` 在 `settings.json` 的 `permissions` 下，这也印证了它是**权限控制**而非内容加载：

```json
"permissions": {
    "additionalDirectories": [
        "/Users/xpeng/.claude/profile"
    ]
}
```

---

## 易混淆点

- ❌ 误解：`additionalDirectories` 会自动把目录内容加载到上下文
- ✅ 正确：它只是让 `Read` 工具被允许访问该目录，内容仍需 Claude 主动读取
- ✅ 正确：`~/.claude/CLAUDE.md` 与 `~/.claude/profile/` 虽在同一父目录，但加载机制完全不同
