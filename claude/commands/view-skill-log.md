# view-skill-log

查看 Skill/Agent 调用日志，支持三种模式。

## 参数解析

$ARGUMENTS 的三种格式：
- 空（无参数）→ 显示今天的记录
- 数字（如 `7`）→ 显示最近 N 天的记录
- `stats` → 统计分析模式

## 执行步骤

### 模式1：无参数 / 数字参数

1. 读取 `~/.claude/skill-log.md`
2. 如果文件不存在，输出「暂无记录，请先使用 Skill 或 Agent 工具」
3. 无参数：提取今天（`## YYYY-MM-DD`）的全部记录并输出
4. 数字 N：提取最近 N 天（按日期标题，从最新往前数）的记录并输出
5. 如果该时间段内无记录，输出「该时段暂无 Skill/Agent 调用记录」

### 模式2：stats 参数

1. 读取 `~/.claude/skill-log.md` 全部内容
2. 统计所有 `**调用对象：**` 行中出现的 Skill/Agent 名称及次数
3. 统计所有 `**触发意图：**` 行中出现的意图类型及次数
4. 计算时间范围（最早记录的 `## YYYY-MM-DD` 日期 ~ 今天）和总条数（`###` 标题数量）
5. 按次数降序输出两张排名表，用 █ 字符绘制简易柱状图（每个 █ 代表1次，最多显示10个；这是实现决策，非 Spec 要求）
6. 根据最高频意图类型给出一条建议：
   - FEATURE_IMPL 最多 → 「建议运行 /update-profile 更新功能实现能力评估」
   - ARCHITECTURE 最多 → 「建议运行 /update-profile 更新架构设计能力评估」
   - BUG_FIX 最多 → 「建议回顾 TESTING.md，检查是否有未归档的约束」
   - LEARNING 最多 → 「建议运行 /identify-intent 归档学习内容」
   - 其他（含 DIRECT_COMMAND / GENERAL / RETROSPECTIVE） → 「建议运行 /view-profile 查看当前能力画像」

## 示例调用

```
/view-skill-log
/view-skill-log 7
/view-skill-log stats
```
