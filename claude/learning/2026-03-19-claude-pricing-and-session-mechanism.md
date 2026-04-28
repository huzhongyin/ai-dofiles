# Claude 定价体系与会话机制

> 归档时间：2026-03-19
> 来源：Claude.ai 官方文档 + claude.com/pricing + code.claude.com/docs

---

## 一、Claude.ai 订阅计划

| 计划 | 价格 | 适用人群 |
|------|------|---------|
| Free | 免费 | 个人轻度使用 |
| Pro | $20/月 | 个人重度用户 |
| Max 5x | $100/月 | Pro 的 5 倍用量，频繁使用者 |
| Max 20x | $200/月 | Pro 的 20 倍用量，全天协作用户 |
| Team | ~$25-30/人/月（≤75座位）| 5-100 人团队，含 SSO |
| Enterprise（自助）| 联系销售 | 需 SCIM、审计日志 |
| Enterprise（定制）| 定制报价 | HIPAA 合规、MSA 等 |

**限制机制**：不是无限使用。本质是购买更大的配额桶，用完等重置（按小时/滚动日重置，不是月底一次性）。

---

## 二、Claude API 定价（按 token 计费）

### 最新模型（2026-03 当前推荐）

| 模型 | 输入/百万token | 输出/百万token | 上下文窗口 | 最大输出 |
|------|--------------|--------------|-----------|---------|
| Claude Opus 4.6 | $5 | $25 | 1M token | 128k |
| Claude Sonnet 4.6 | $3 | $15 | 1M token | 64k |
| Claude Haiku 4.5 | $1 | $5 | 200k token | 64k |

### 旧版模型（仍可用）

| 模型 | 输入 | 输出 |
|------|------|------|
| Claude Opus 4 / 4.5 | $15 | $75 |
| Claude Opus 4.1 | $15 | $75 |
| Claude Sonnet 4 / 4.5 | $3 | $15 |
| Claude Haiku 3（⚠️ 2026-04-19 下线）| $0.25 | $1.25 |

**额外费用**：Batch API 折扣 / Prompt 缓存命中优惠 / Extended Thinking 额外计费 / 长上下文（>200k token）专项定价

---

## 三、Claude Code 会话与 Token 计费机制

### 什么是一个会话

Claude Code 会话 = 一个连续的上下文窗口，从启动 `claude` 到退出或清空为止。

| 操作 | 是否开启新会话 |
|------|--------------|
| `/clear` | ✅ 是（清空上下文） |
| 退出后重启（不用 --resume） | ✅ 是 |
| `claude --resume` | ❌ 否（恢复旧会话） |
| 切换文件/任务 | ❌ 否 |
| 上下文满触发 auto-compaction | ❌ 否（自动压缩，不开新会话）|

### Token 消耗影响因素

- 上下文越长，每次请求消耗越多（历史全量带入）
- 读取大文件 = 大量 token 消耗
- Extended Thinking 消耗大量输出 token
- MCP 工具定义常驻上下文占位
- 后台任务（会话总结等）每次约 $0.04

### 官方数据参考

- 平均 **$6/天/开发者**
- 90% 用户每天低于 **$12**
- 月均约 **$100-200/人**（Sonnet 4.6）

### 常用控制命令

```
/clear          # 切换不相关任务时清空（最有效！）
/compact        # 压缩历史，保留摘要
/cost           # 查看当前 token 消耗（仅 API 用户）
/stats          # 订阅用户查看使用模式
/model          # 切换到更便宜的模型
```

### 订阅用户 vs API 用户

| | 订阅（Pro/Max） | API |
|--|--|--|
| 计费 | 包含在月订阅里 | 按实际 token 付费 |
| `/cost` | 无意义（不反映计费）| 有意义 |
| 上限 | 有配额，超了等重置 | 无上限，钱够用 |

---

## 四、Subagent 独立上下文机制

### 本质

Subagent = 临时开出的独立子上下文窗口，任务完成后把摘要返回主会话。

```
主会话（Main Session）
├── 上下文窗口 A（主对话历史）
├── → 派发 Subagent-1：独立上下文 B → 摘要返回 A
└── → 派发 Subagent-2：独立上下文 C → 摘要返回 A
```

### 如何识别 Subagent 在独立上下文运行

1. **UI 颜色标签**：Subagent 有独立颜色和名称显示
2. **缩进层级**：输出比主会话缩进一级
3. **遗忘测试**：主会话里说的话，agent 不知道 → 证明独立上下文
4. **Transcript 文件**：`~/.claude/projects/{project}/{sessionId}/subagents/agent-{id}.jsonl` 独立存储

### Subagent 独立上下文的优点

| 优点 | 说明 |
|------|------|
| 隔离噪音 | 大量中间输出不污染主会话 |
| 模型分级 | Agent 用 Haiku，主会话用 Opus，节省成本 |
| 权限隔离 | Agent 只读，主会话可写 |
| 并行执行 | 多个 agent 同时跑，互不干扰 |
| 持久记忆 | `memory: user` 跨会话积累知识 |

### Subagent 独立上下文的缺点

| 缺点 | 说明 |
|------|------|
| 天然失忆 | Agent 看不到主会话历史，必须在 prompt 里手动传背景 |
| 返回结果撑大主会话 | Agent 摘要进入主会话，多个 agent 后主会话反而变大 |
| 总 token 开销更高 | Agent 有启动开销，总消耗 > 直接在主会话跑 |
| 调试困难 | 内部推理不透明，需翻 `.jsonl` 文件排查 |
| 不能嵌套 | Subagent 不能再派发 Subagent |

### Agent Teams vs Subagent

| | Subagent（单会话内） | Agent Teams（跨会话）|
|--|--|--|
| 上下文 | 独立，摘要返回主会话 | 完全独立，互相通信 |
| 嵌套 | ❌ 不能 | ✅ 可并行协调 |
| Token 开销 | 中等 | 高（约 7x）|
| 适用 | 隔离单步任务 | 大规模并行任务 |

---

## 五、Plugin 三种组件的本质区别

### Agent（`agents/` 目录）= Subagent 定义

- 运行在**独立上下文窗口**
- 有自己的 system prompt、工具权限、模型
- 适合：隔离高输出任务、专项领域工作
- ⚠️ Plugin 中的 agent **不支持** `hooks`、`mcpServers`、`permissionMode` 字段

### Skill（`skills/` 目录）= 注入上下文的知识

- **不开新窗口**，内容直接注入当前上下文
- 按需加载，用户调用或 Claude 自动触发
- 适合：复用工作流、领域知识、操作规范

### Command（`commands/` 目录）= Slash 命令触发器

- 是**入口**，不是执行者
- 用户输入 `/xxx` 调用
- 内部可组合调用 agent 和 skill
- 适合：封装常用流程，团队统一入口

### 组件作用域优先级

| 位置 | 优先级 |
|------|--------|
| CLI `--agents` 参数 | 1（最高）|
| `.claude/agents/`（项目级）| 2 |
| `~/.claude/agents/`（用户级）| 3 |
| Plugin `agents/`（插件级）| 4（最低）|

---

## 六、最佳实践总结

- **切换不相关任务时用 `/clear`**，是控制 token 最有效的操作
- **Agent 做脏活**：把高输出、批量处理外包给 agent，主会话只收摘要
- **模型分级**：Haiku 处理简单子任务，Sonnet 处理常规任务，Opus 留给复杂决策
- **派发 agent 时要喂背景**：agent 看不到主会话历史，必须在 prompt 里提供关键上下文
- **Plugin agent 的限制**：需要 hooks/mcpServers/permissionMode 时，复制到 `.claude/agents/`
