Before ANY multi-step task, MUST load relevant skills: planning → writing-plans, coding → test-driven-development, bugs → systematic-debugging, parallel tasks → subagent-driven-development. User explicitly requires this — not optional.
§
STOP rule: user asks "为什么/原理/怎么实现/怎么回事" about Hermes/tools → load skill:learning-notes, answer, append via `python3 ~/.hermes/scripts/append_learning_note.py YYYY-MM-DD <<'EOF'...EOF'`. NEVER write_file/heredoc on learning-notes — past overwrites caused data loss.
§
User operates 8+ AI agents (Hermes, Claude Code, Kimi, Kiro, Cursor, Codex, Trae, Windsurf, Copilot). Skills unified under ~/.agents/skills/. Expects zero-intrusion, frictionless automation.
§
User has strong architectural cleanliness standards: insists on zero-intrusion designs (never modify existing files unless necessary), cares about proper category boundaries (e.g., framework skills must not pollute domain-specific categories), and demands verifiable results via sandbox testing with explicit pass/fail metrics.
§
⚠️ 强制规则：Skill 加载审批门

在任何会话中，准备调用 skill_view 加载 skill 之前，必须先在对话窗口中显式输出即将加载的 skill 名称、类别、触发原因

此规则优先级高于任何自动加载 skill 的内部判断逻辑，即使 100% 匹配也必须经过审批。
§
Feynman method: if user challenges with experience-based objections, do NOT win with analogies. Immediately look up official docs/source to verify. User's real-world experience is often more accurate than my assumptions.
**特别场景强化：**涉及具体产品架构对比（如"X 和 Y 有什么区别"、"Z 是否支持隔离"等），**first response 必须先查官方文档**，不能凭记忆中"常识"回答。尤其是对比 Claude Code、OpenAI Codex 等竞品工具时，过时经验极易误导。
§
XPMotors_IOS 的 submodule/ 是独立 git 仓库（无 .gitmodules），由 CocoaPods 本地路径 :path 管理。检查时不能用 git submodule foreach（会返回空列表），必须直接 cd 进入各子目录执行 git status。术语惯性误判：目录名为 submodule/ 不等于是标准 git submodule。
§
用户纠正了我在 Bug 分析链路中的设计假设：跨部门协作时，App 团队应仅分析模块边界内问题（上游输入 + 下游输出状态），证据指向外部模块时生成转交报告，禁止推测外部根因。这个原则已落地到 project-common.md 和 bug-analysis skill 中。
§
spec-coding 自动进化 vs Hermes skill：前者是项目级量化评分+改进跟踪+知识审计的文件化闭环；后者是通用框架的被动响应式能力扩展。