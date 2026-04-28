# Claude Code 工作原理学习笔记

**日期：** 2026-03-17
**背景：** iOS 开发者视角，有 AI 工具基础，目标是理解底层机制

---

## TL;DR

1. Claude Code = 能读写本地文件 + 执行命令的 AI，不是网页聊天工具
2. 工作方式：你说目标 → 模型自主规划工具调用序列 → Hook 层可拦截审查
3. `CLAUDE.md` 是控制行为的最重要文件，写好它等于给 AI 配置了团队规范

---

## 与其他 AI 工具核心区别

| 对比维度 | ChatGPT / 网页 Claude | GitHub Copilot | Claude Code |
|---------|----------------------|---------------|-------------|
| 读取本地文件 | ❌ 需手动粘贴 | ✅ 当前文件 | ✅ 整个项目目录 |
| 执行命令 | ❌ | ❌ | ✅ Bash/Shell |
| 跨会话记忆 | ❌ | ⚠️ 仅编辑器内 | ✅ CLAUDE.md |
| 工作流自动化 | ❌ | ❌ | ✅ Hooks/Skills/Agents |

---

## 七层流转架构

```
用户输入
  ↓ [1] CLI 解析层        → 解析命令、确定工作目录
  ↓ [2] 上下文构建层      → 合并 CLAUDE.md + 会话历史 + 系统 prompt
  ↓ [3] API 请求层        → 打包发送到 Anthropic API，携带工具定义
  ↓ [4] 模型推理层        → Claude 决策：直接回答 or 调用工具（ReAct 循环）
  ↓ [5] 工具调用层        → 执行 Read/Write/Edit/Bash/Glob/Grep/Agent
  ↓ [6] Hook 拦截层       → PreToolUse/PostToolUse 钩子，开发者最强干预点
  ↓ [7] 输出返回层        → 流式打印结果
```

### 关键设计原则

- **模型只负责决策**（第4层），不直接操作文件
- **CLI 负责执行**（第5层），是实际执行者
- **Hook 负责审查**（第6层），是安全阀
- 三层分离，每层独立可扩展

### ReAct 循环（第4-5层反复迭代）

```
模型思考 → 请求工具 → CLI执行 → 结果返回模型 → 模型再思考 → ...
```

---

## 核心能力模块（iOS 开发者视角）

| 能力 | iOS 类比 | 触发方式 |
|------|---------|---------|
| Tools | FileManager / Process() | 模型自动决策 |
| CLAUDE.md | .xcconfig + 团队规范 | 启动自动加载 |
| Hooks | Build Phases Run Script | settings.json 配置 |
| Skills | 自定义 Xcode Snippet + 执行逻辑 | `/skill-name` |
| Slash Commands | Makefile target | `~/.claude/commands/` |
| Agents | GCD DispatchQueue.async 并行 | Agent 工具调用 |
| MCP | Swift Package Manager 插件 | `.mcp.json` 配置 |

---

## 开发者干预点总结

| 层级 | 干预方式 | 示例 |
|------|---------|------|
| 上下文层 | 编写 CLAUDE.md | 注入代码规范、禁止操作 |
| API 层 | 配置 MCP | 注册自定义工具 |
| Hook 层 | PreToolUse/PostToolUse | 拦截危险命令、自动跑测试 |
| 命令层 | ~/.claude/commands/ | 自定义 slash command |

---

## 关键文件位置

| 文件 | 位置 | 作用 |
|------|------|------|
| 项目记忆 | `./CLAUDE.md` | 项目规范，自动加载 |
| 全局配置 | `~/.claude/settings.json` | Hooks 等全局设置 |
| 自定义命令 | `~/.claude/commands/*.md` | 全局 slash command |
| 自定义技能 | `~/.claude/skills/*.md` | 可复用工作流 |

---

## 七层流转详解（完整版）

### [1] CLI 解析层

**做了什么：** 解析输入命令，识别交互模式 / `-p` 单次模式，确定工作目录根路径。

**为什么这样设计：** Claude Code 需要知道"工作区域"在哪里才能定位 CLAUDE.md 和执行文件操作。类似 Xcode workspace，所有操作都相对于一个根路径展开。

**开发者可干预：**
```bash
claude -p "检查代码规范" --cwd /path/to/project   # 指定工作目录
```

---

### [2] 上下文构建层

**做了什么：** 把以下内容合并成完整的对话上下文：
- `CLAUDE.md` 内容（项目规范、禁止操作）
- 当前会话历史消息
- 系统级 prompt（Claude Code 内置指令）
- 用户当前输入

**为什么这样设计：** 大语言模型是"无状态"的，每次 API 调用都是全新的。Claude Code 通过在每次请求里携带完整历史来模拟"记忆"。CLAUDE.md 注入到每次请求最前面，确保模型始终遵守项目规范。

**开发者可干预：** 编写 CLAUDE.md 就是在干预这一层。
```markdown
## 约束
- 修改 Swift 文件时必须同步更新对应 Test 文件
- 不得使用强制解包 !
```

---

### [3] API 请求层

**做了什么：** 把上下文打包成 JSON，通过 HTTPS POST 发送给 `api.anthropic.com`，同时携带**工具定义**（告诉模型它能用哪些工具）。

**为什么这样设计：** 工具定义（Tool Use）是关键——模型收到工具的"说明书"才知道自己有 Read/Write/Bash/Agent 等能力可以选择。类似 iOS App 声明权限，模型只能使用已声明的工具。

**开发者可干预：** 通过 MCP 在这一层扩展可用工具。
```json
// .mcp.json：注册自定义工具
{
  "mcpServers": {
    "jira": { "command": "npx", "args": ["@your-org/mcp-jira"] }
  }
}
```

---

### [4] 模型推理层（ReAct 循环）

**做了什么：** Claude 决策下一步动作：
1. 直接回答 → 不需要工具，生成文字
2. 调用工具 → 返回"工具调用请求"（如：我要 Read 这个文件）
3. 多步推理 → 先读文件，分析后再决定写文件

**ReAct 循环：**
```
模型思考 → 请求工具 → CLI执行工具 → 结果返回模型 → 模型再思考 → ...
```
循环可执行多轮，直到模型认为任务完成。

🤖 **这一层完全由模型自主决策，开发者无法直接干预**，只能通过 CLAUDE.md 的指令影响决策方向。

---

### [5] 工具调用层

**核心内置工具：**

| 工具 | 作用 | iOS 类比 |
|------|------|---------|
| `Read` | 读取文件内容 | `FileManager.contents(atPath:)` |
| `Write` | 写入/创建文件 | `FileManager.createFile(atPath:)` |
| `Edit` | 精确替换文件中的字符串 | 比 Write 更安全，只改指定部分 |
| `Bash` | 执行 Shell 命令 | `Process()` |
| `Glob` | 按模式搜索文件 | `find . -name "*.swift"` |
| `Grep` | 在文件中搜索内容 | `grep -r "keyword" .` |
| `Agent` | 启动子 Claude 实例执行子任务 | `DispatchQueue.async` 并行 |

---

### [6] Hook 拦截层

**做了什么：** 在工具调用前后执行自定义脚本，可拦截、审查、触发后续自动化。

**为什么这样设计：** 类似 `UIViewController` 生命周期，你可以在 `viewWillAppear` / `viewDidAppear` 插入逻辑。Hook 就是工具调用的生命周期回调，给开发者"安全阀"和"扩展点"。

**Hook 事件：**

| 事件 | 触发时机 | 典型用途 |
|------|---------|---------|
| `PreToolUse` | 工具执行前 | 拦截危险命令、审查即将写入的代码 |
| `PostToolUse` | 工具执行后 | 自动跑测试、同步文档 |
| `SessionStart` | 会话启动时 | 加载项目环境变量 |
| `Stop` | Claude 准备结束时 | 检查未完成的 TODO |

**配置示例：**
```json
// ~/.claude/settings.json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write",
      "hooks": [{
        "type": "command",
        "command": "swiftlint lint --path $TOOL_OUTPUT_FILE"
      }]
    }]
  }
}
```

🔧 **这一层是开发者干预能力最强的节点。**

---

### [7] 输出返回层

**做了什么：** 把模型生成的文字流式打印到终端，工具执行结果一并呈现。

**为什么流式输出：** 大模型生成是逐 token 产生的，流式输出让你不用等全部生成完才看到结果，体验更即时。这也是为什么 Claude Code 的回复是"一点一点出现"而不是"整块返回"。

---

## 端到端追踪：「帮我重构 NetworkManager.swift」

```
你输入："帮我重构 NetworkManager.swift，拆分职责"
  │
  │ [1] CLI 解析层
  │     识别为交互模式，工作目录 = 当前目录
  │
  │ [2] 上下文构建层
  │     注入 CLAUDE.md："不得使用强制解包，修改需同步测试"
  │
  │ [3] API 请求层
  │     携带 Read/Write/Edit/Bash 工具定义发送给模型
  │
  │ [4] 模型推理层  🤖
  │     "我需要先读文件才能重构"
  │     → 请求调用 Read("NetworkManager.swift")
  │
  │ [5] 工具调用层
  │     执行 Read → 返回 500 行代码给模型
  │
  │ [4] 模型再次推理  🤖
  │     分析代码，识别 3 个可拆分职责
  │     → 请求 Edit("NetworkManager.swift", 重构后代码)
  │     → 请求 Write("RequestBuilder.swift", 新文件)
  │     → 请求 Write("ResponseParser.swift", 新文件)
  │
  │ [6] Hook 拦截层  🔧
  │     PostToolUse(Write) → 自动执行 SwiftLint → 通过
  │
  │ [4] 模型再次推理  🤖
  │     "CLAUDE.md 说修改要同步测试"
  │     → 请求 Edit("NetworkManagerTests.swift", 更新测试)
  │     → 请求 Bash("xcodebuild test") → 测试通过
  │
  │ [7] 输出返回层
        打印："已完成重构，拆分为 3 个文件，测试全部通过"
```

**关键结论：**
- 🤖 模型只负责**决策**（第4层），不直接操作文件
- 🔧 CLI 负责**执行**（第5层），是实际执行者
- 🛡️ Hook 负责**审查**（第6层），是安全阀
- 三层分离，每层独立可扩展

---

## Slash Command vs Skill 对比

> **Slash Command = 做什么（What）**，**Skill = 怎么做（How）**

| 维度 | Slash Command | Skill |
|------|--------------|-------|
| **触发方式** | `/命令名` 手动输入 | `Skill` 工具调用（Claude 自动或手动）|
| **本质** | 用户主动执行的指令 | Claude 按需加载的行为规范/知识 |
| **执行主体** | Claude 读取后一次性执行 | Claude 加载后遵循指导持续行动 |
| **触发时机** | 用户显式输入 `/xxx` | Claude 判断相关性后主动调用 |
| **适用场景** | 固定工作流（提交、归档、复盘）| 行为规范、领域知识、工作方法 |
| **参数支持** | ✅ 支持 `args` 参数 | ❌ 无参数，靠上下文判断 |
| **调用链** | 可在命令内部调用 Skill | Skill 可被命令、Hook、Claude 调用 |

### 典型协作模式

```
用户输入 /commit
    ↓
Claude 读取 slash command 文件（What：做提交）
    ↓
Command 内部调用 Skill tool → git-commit skill（How：怎么提交）
    ↓
Skill 提供：分析 diff → 生成 conventional commit → 校验 → 执行
```

---

## iOS 开发者实战示例

**示例 1：分析陌生项目架构**
```bash
claude
> 这个项目用了 VIPER 还是 MVVM？帮我画出模块依赖关系图
# Claude 自动 Glob 扫描文件 → Read 关键文件 → 归纳架构
```

**示例 2：自动化 Code Review**
```bash
claude -p "审查 git diff HEAD~1，重点检查：内存管理、线程安全、错误处理"
```

**示例 3：追踪调用链**
```bash
claude
> 从 LoginViewController 的登录按钮点击开始，追踪到网络请求发出，列出完整调用链
```

**示例 4：Hook 自动跑 SwiftLint（每次写文件后）**
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write",
      "hooks": [{ "type": "command", "command": "swiftlint lint --path $TOOL_OUTPUT_FILE" }]
    }]
  }
}
```
