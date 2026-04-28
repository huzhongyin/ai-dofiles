---
name: github-ai-trends
description: "Daily GitHub AI trends report: scrapes GitHub Trending for weekly star-growth-ranked AI projects, compares with historical snapshots, generates categorized report with core functions and key features, delivers via Feishu."
triggers:
  - "github ai trends"
  - "github trending"
  - "ai project tracking"
  - "github ai 周报"
---

# GitHub AI Trends Report

Daily automated report of top AI projects on GitHub, ranked by **weekly star growth** (not total stars).

## Architecture

- Script: `~/.hermes/scripts/github_trends.py`
- Data: `~/.hermes/data/github-trends/YYYY-MM-DD.json` (daily snapshots for trend comparison)
- Delivery: Feishu via `~/.hermes/scripts/feishu_send.py`
- Cron: Job `1ffaaa451950`, runs at 7:00 AM Beijing time daily

## Key Design Decisions (lessons learned)

### Why Trending, not Search
Initial approach used GitHub Search API sorted by total stars. This surfaced stale legacy repos (TensorFlow 194k, scikit-learn 65k) that aren't actually trending. Switched to scraping `github.com/trending?since=weekly` which ranks by **weekly star growth** — much better signal for "what's hot this week".

### Data source strategy
1. **Primary**: Scrape GitHub Trending weekly page (HTML parsing with regex)
2. **Supplement**: GitHub Search with `pushed:>date+stars:>N` filters for active AI repos
3. **Merge**: Trending repos override search data (they have weekly_star_growth), deduplicate by full_name
4. **Rank by**: `(weekly_star_growth, total_stars)` descending

### GitHub Trending HTML parsing
The Trending page uses `<article class="Box-row">` blocks. Key gotchas:
- Repo name is in `<h2><a href="/owner/repo">` — but `<a>` has many data-* attributes before `href`
- Correct regex: `r'<h2[^>]*>.*?<a[^>]+href="/([^/]+/[^/"]+)"'` (note `[^>]+` before `href`)
- Weekly stars: `r'([\d,]+)\s+stars?\s+this\s+week'`
- Description: `r'<p\s+class="col-9[^"]*"[^>]*>\s*(.*?)\s*</p>'`
- Language: `r'itemprop="programmingLanguage"[^>]*>\s*(.*?)\s*<'`

### Rate limiting
- **With GITHUB_TOKEN** (configured in `~/.hermes/.env`): 5000 core requests/hr, 30 search/min
- **Without token**: 60 core requests/hr, 10 search/min — severely limits data quality
- Token is essential: enables 5 search queries (was 2 without token), faster detail fetching
- Details fetch (repos, releases, commit_activity): Only fetch for repos missing star data

### Snapshot system for trends
- Save daily JSON snapshot with rank, full_name, stars, category
- Compare current rankings with yesterday and last week
- Compute rank_change: positive = rising, negative = falling, None = newcomer

## Delivery: Feishu Document (v4)

User rejected plain-text format in chat — wants proper Markdown with tables, headers, bold.
Feishu chat doesn't render Markdown, so the solution is:

1. Generate full Markdown report (tables, headers, bullet lists, bold, etc.)
2. Create a Feishu doc via Docx API
3. Convert Markdown → Feishu blocks and write to doc
4. Send a message card (interactive card with button) linking to the doc
5. User clicks card → opens Feishu doc with full rendered Markdown

### Feishu Docx API patterns

**Create doc:**
```python
POST /open-apis/docx/v1/documents
body: {"title": "Title", "folder_token": ""}
returns: document_id
```

**Add blocks** (root block_id = document_id):
```python
POST /open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children?document_revision_id=-1
body: {"children": [block, ...], "index": 0}
```

**Supported block types (tested):**
- `2` = text (property name: `text`, NOT `paragraph`)
- `3` = heading1
- `4` = heading2
- `5` = heading3
- `14` = code block (style: `{"language": 47}` for Python)
- `22` = divider

**NOT supported (tested, returns 400):**
- `12`/`13` = bullet/ordered lists

**Workaround for bullet lists:** Use type 2 (text) with "• " prefix.

**Block element format:**
```json
{
    "block_type": 2,
    "text": {
        "elements": [
            {"text_run": {
                "content": "text",
                "text_element_style": {"bold": true}
            }}
        ],
        "style": {}
    }
}
```

**Send document link card (interactive message):**
```python
POST /open-apis/im/v1/messages?receive_id_type=chat_id
msg_type: "interactive"
content: card JSON with header, summary div, and button linking to doc_url
```

**Markdown → Feishu blocks converter rules:**
- `# ` → heading1, `## ` → heading2, `### ` → heading3
- `- ` → text with "• " prefix (bullet blocks return 400)
- `|` rows → plain text with " | " separator (skip separator rows)
- `**bold**` → text_run with bold:true
- `*italic*` → plain text (no italic in Feishu)
- Skip code fences (```) and table separator rows

**Batch size:** Max 50 blocks per call. Use 30 for safety. Sleep 0.5s between batches.

### GitHub Trending total stars regex fix
Old pattern no longer matches. Correct: `r'</svg>\s*([\d,]+)</a>'` — star count appears right after SVG star icon within anchor tag.

### Report format (Markdown for Feishu doc)

```
GitHub AI 热榜 2026-W16  |  2026-04-16
====================================================

本周总增长  +126,442⭐  |  新上榜 0 个  |  Top 增长 +53,110⭐
增长冠军  owner/repo  [Category]

▎领域热度分布
  ████████████████ AI代理平台 +70,667
  ███████░░░░░░░░░ AI编程代理 +35,182

▎完整榜单 Top 20
   1. NEW  project-name                 ▓▓▓▓▓▓▓▓+53,110
      ⭐90k  [AI代理平台]  Chinese description

====================================================
▎关键洞察
  🔺 上升: project(+5), project(+3)
  🆕 新上榜: project, project
```

Full Markdown with proper tables, headers, bold. Two output formats:

**Markdown** (for Feishu doc):
```markdown
# GitHub AI 热榜 2026-W16
**2026-04-16** | 数据源: GitHub Trending Weekly

## 🔥 本周概览
- **总增长**: +126,442⭐
- **新上榜**: 3 个
- **增长冠军**: owner/repo (+53,110⭐)

## 📊 领域热度分布
| 领域 | 本周增长 | 热度 |
|------|---------|------|
| AI代理平台 | +70,667 | ██████████░░░░░░ |

## 🏆 完整榜单 Top 20
| # | 趋势 | 项目 | ⭐ 总Star | 📈 本周增长 | 分类 | 核心功能 |
|---|------|------|----------|-----------|------|---------|
| 1 | 🆕NEW | **name** | 90k | +53,110 | AI代理平台 | 可成长的开源AI代理 |

## 💡 关键洞察
**🔺 上升最快:**
- project (+5)
```

**Summary** (for chat message card):
```
📊 GitHub AI 热榜 W16 (2026-04-16)
总增长 +126,442⭐ | 新上榜 3 个
冠军: hermes-agent +53,110⭐

Top 5:
  1. hermes-agent +53,110
  2. ...
```

The function returns `{"markdown": ..., "summary": ...}`.

### Chat targets
- User: `oc_6dc97fe5ef1e2ede13691456af4a3c66`
- 0101: `oc_53db3b1bdc6280ffae4805ba96868eb9`

### Human-readable descriptions (KNOWN_PROJECTS dict)
For popular/recurring projects, maintain a `KNOWN_PROJECTS` dict with Chinese descriptions:
- `core_func`: one-liner in Chinese explaining what it does
- `key_feature`: what makes it special (often from latest release or unique capability)
- `layer`: "tool" or "core"
- `category`: specific category name

Unknown repos fall back to auto-inference from GitHub description/topics — quality is lower. Update KNOWN_PROJECTS as new projects trend.

### Project descriptions: desc_long field
Each KNOWN_PROJECTS entry now has a `desc_long` field (~100 Chinese chars) explaining what the project does, its tech stack, use case, and why it matters. This is shown in the "📖 项目详解" section of the Feishu doc. For unknown repos, `desc_long` is auto-generated from GitHub description + topics + latest release.

### Python string gotcha: Chinese quotes
Chinese quotation marks `""` inside Python strings delimited by `""` cause SyntaxError. Use `''` (single quotes) or regular single-quote `'...'` instead. Example:
```python
# BROKEN — inner "" terminates the string
"核心理念是"与用户共同成长""
# FIXED
"核心理念是'与用户共同成长'"
```

### feishu_send.py pitfall (still used for plain text fallback)
When calling `feishu_send.py` from Python subprocess, argument order matters — no `--message` flag exists:
```python
# CORRECT
cmd = ["python3", script, "--chat-id", chat_id, "--", message]
# WRONG — silently ignores --chat-id, sends to default
cmd = ["python3", script, "--message", message, "--chat-id", chat_id]
```

### Memory management after complex projects
After building this system, memory had 8 entries (97% full). Lesson: move implementation details to the skill file, keep memory lean:
- **Memory**: only user preferences (chat_ids, delivery format), behavioral rules (must load skills), and trigger rules (learning notes)
- **Skill file**: all implementation details (pitfalls, rate limits, architecture decisions, HTML parsing gotchas)
- **Session transcripts** (state.db): recoverable via `session_search` if needed later
- This reduced memory from 2134→744 chars (97%→34%)

## Usage

```bash
# Preview report (no send)
python3 ~/.hermes/scripts/github_trends.py

# Generate + create Feishu doc + send card to both targets
python3 ~/.hermes/scripts/github_trends.py --send
```

## Sending targets
Defined in `CHAT_IDS` list in the script:
- User: `oc_6dc97fe5ef1e2ede13691456af4a3c66`
- 0101: `oc_53db3b1bdc6280ffae4805ba96868eb9`

### Filtering non-AI repos
Use `NON_AI_SIGNALS` blacklist + `is_ai_related()` whitelist to filter:
- Blacklist catches: textbook collections, interview prep, roadmaps, generic "awesome-*" lists
- Whitelist requires: at least one AI keyword (ai, llm, agent, rag, diffusion, ml, etc.) in name/description/topics
- Both trending AND search results go through filtering before ranking
- Parse release body for concise "what's new" summaries
- Add weekly commit velocity as ranking signal alongside star growth
- Auto-generate Chinese descriptions for unknown repos (currently falls back to raw English)
- Expand KNOWN_PROJECTS dict as new projects trend week over week
