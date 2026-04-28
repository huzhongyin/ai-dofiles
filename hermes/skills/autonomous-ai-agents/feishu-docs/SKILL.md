---
name: feishu-docs
description: "Create Feishu/Lark documents, write content blocks, and send document link cards via the Docx API. Use when user wants to generate rich-formatted reports, documents, or notes delivered via Feishu."
version: 1.0.0
author: Hermes Agent
tags: [feishu, lark, documents, docx, reports]
---

# Feishu Documents (Docx API)

Create rich-formatted Feishu documents and deliver them as link cards in chat.

## When to Use

- User wants reports with tables, headers, bold (not just plain text)
- Feishu chat can't render the desired format
- Content is too long for a single chat message
- User wants a shareable/lasting document

## Prerequisites

- `FEISHU_APP_ID` and `FEISHU_APP_SECRET` in `~/.hermes/.env`
- API scope: `docx:document` (read/write documents)
- API scope: `im:message:send_as_bot` (send message cards)

## Workflow

1. Get tenant_access_token
2. Create document → get document_id
3. Convert content to Feishu blocks
4. Add blocks to document (batch API)
5. Send interactive message card with doc link

## API Reference

### Get Token
```python
POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
body: {"app_id": "...", "app_secret": "..."}
→ tenant_access_token
```

### Create Document
```python
POST https://open.feishu.cn/open-apis/docx/v1/documents
body: {"title": "Title", "folder_token": ""}
Authorization: Bearer {token}
→ document_id
```

### Add Blocks
```python
POST https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children?document_revision_id=-1
body: {"children": [block, ...], "index": 0}
```

- `block_id` for the root = `document_id`
- Max 50 blocks per call (use 30 for safety)
- Sleep 0.5s between batches

### Block Types (tested, working)

| type | name | property key | notes |
|------|------|-------------|-------|
| 2 | text | `text` | NOT `paragraph` — common mistake |
| 3 | heading1 | `heading1` | |
| 4 | heading2 | `heading2` | |
| 5 | heading3 | `heading3` | |
| 14 | code | `code` | style: `{"language": 47}` (Python) |
| 22 | divider | `divider` | empty object |

### Block Types (NOT working, returns 400)

| type | name | workaround |
|------|------|-----------|
| 12 | bullet | Use text + "• " prefix |
| 13 | ordered | Use text + "1. " prefix |

### Block Format

```json
{
    "block_type": 2,
    "text": {
        "elements": [
            {
                "text_run": {
                    "content": "Hello world",
                    "text_element_style": {
                        "bold": false,
                        "inline_code": false,
                        "italic": false,
                        "strikethrough": false,
                        "underline": false
                    }
                }
            }
        ],
        "style": {"align": 1}
    }
}
```

For bold text, set `"bold": true` in text_element_style.

### Send Document Link Card

```python
POST https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id
body: {
    "receive_id": "oc_xxx",
    "msg_type": "interactive",
    "content": JSON.stringify({
        "header": {"title": {"tag": "plain_text", "content": "Report Title"}},
        "elements": [
            {"tag": "div", "text": {"tag": "plain_text", "content": "Summary text"}},
            {"tag": "action", "actions": [{
                "tag": "button",
                "text": {"tag": "plain_text", "content": "📖 查看"},
                "url": "https://feishu.cn/docx/{doc_id}",
                "type": "primary"
            }]}
        ]
    })
}
```

## Markdown → Feishu Blocks Converter

Rules for converting Markdown to Feishu block format:

| Markdown | Feishu block |
|----------|-------------|
| `# text` | type 3 (heading1) |
| `## text` | type 4 (heading2) |
| `### text` | type 5 (heading3) |
| `- text` | type 2 (text) with "• " prefix |
| `**bold**` | text_run with bold:true |
| `*italic*` | text_run with bold:false (no italic support) |
| `---` | type 22 (divider) |
| `\| table \|` | type 2 (text) with " \| " separator |
| `` ```code``` `` | skip or type 14 (code) |
| table separator row | skip |

Parse inline `**bold**` segments into separate text_run elements with different bold settings.

## Pitfalls

1. **Property name is `text`, not `paragraph`** for block_type 2. Using `paragraph` returns 400.
2. **Bullet/ordered list blocks return 400.** Use text blocks with manual prefixes.
3. **document_revision_id=-1** means "latest" — always use this for appending.
4. **Batch limit is 50 blocks** per API call. Exceeding returns error.
