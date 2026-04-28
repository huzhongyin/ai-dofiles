---
name: feishu-messaging
description: Send outbound messages via Feishu/Lark bot — single user, groups, and organizational contacts. Use when the user asks to send a Feishu message, ping someone on Feishu, or check Feishu bot capabilities.
version: 1.0.0
author: Hermes Agent
tags: [feishu, lark, messaging, outbound]
---

# Feishu Messaging (Outbound)

Hermes gateway is inbound-only — there is no built-in `hermes send` for Feishu. Use the custom script at `~/.hermes/scripts/feishu_send.py` which calls the Feishu Open API directly.

## Quick Reference

```bash
# Send to default recipient (user's own chat)
python3 ~/.hermes/scripts/feishu_send.py "your message"

# Send to a specific chat (group or DM)
python3 ~/.hermes/scripts/feishu_send.py --chat-id oc_xxx "your message"

# Send to a specific user by open_id
python3 ~/.hermes/scripts/feishu_send.py --open-id ou_xxx "your message"
```

Credentials (`FEISHU_APP_ID`, `FEISHU_APP_SECRET`) are read from `~/.hermes/.env`. Default `chat_id` is `oc_6dc97fe5ef1e2ede13691456af4a3c66` (hardcoded fallback in script).

## Organizational Capabilities

### Discovering users
Use the Contact API to list users in the org:
```python
# GET /open-apis/contact/v3/users?page_size=20&user_id_type=open_id
# Requires: contact:user.base:readonly permission
```
Each user has an `open_id` that can be used with `--open-id` to send DMs.

### Sending to groups
1. Bot must be added to the group first (user does this manually in Feishu)
2. List groups bot is in:
```python
# GET /open-apis/im/v1/chats?page_size=20
# Returns chat_id for each group
```
3. Send with `--chat-id <chat_id>`

### Required permissions (Feishu Open Platform)
- `im:message:send_as_bot` — send messages as bot
- `contact:user.base:readonly` — read org contacts (to find open_ids)
- `im:chat:readonly` — list groups bot has joined

## Agent Interaction Pattern

Users prefer **natural language** over CLI aliases. When a user says something like:
- "帮我在飞书上说XXX"
- "给手机发'XXX'"
- "提醒我飞书上..."

The agent should:
1. Extract the message content
2. Run `python3 ~/.hermes/scripts/feishu_send.py "<content>"`
3. Confirm delivery

Do NOT suggest shell aliases — just handle it conversationally.

## Feishu Permission Model (Two Layers)

Self-built apps (自建应用) have **two independent permission controls** — both must be configured:

### Layer 1: API Permission Scopes (权限开关)
Which API endpoints the app can call. Set in: **权限管理** tab.

Required for contact/messaging:
- `im:message:send_as_bot` — send messages as bot
- `contact:user.base:readonly` — read org contacts (open_id, name, etc.)
- `contact:user.employee:readonly` — read employee info (department, title)
- `im:chat:readonly` — list groups bot has joined

### Layer 2: App Availability Scope (应用可用范围)
Which users the app can *see and interact with*. Set in: **应用可用范围** or **发布管理**.

Options:
- "与应用的可用范围一致" — who can use the app = who the app can see
- If scope is too narrow (e.g. only yourself), the app can't query or message others

**Important:** After changing availability scope, you **must republish the app** (版本管理与发布 → 创建新版本 → 发布) for changes to take effect.

### Field-Level Permissions
Contact API may return users but omit the `name` field if field-level permissions are restricted. In 权限管理, check that `contact:user.name:readonly` or equivalent field access is granted.

## Pitfall: Subprocess Argument Ordering (Critical)

When calling `feishu_send.py` from Python subprocess, **argument order matters**. The script uses positional args for the message (no `--message` flag).

**WRONG** — `--message` is not a valid flag, gets absorbed into the text:
```python
# This silently ignores --chat-id, sends to DEFAULT chat!
cmd = ["python3", script, "--message", text, "--chat-id", chat_id]
```

**CORRECT** — flags first, then `--`, then message text:
```python
cmd = ["python3", script, "--chat-id", chat_id, "--", text]
```

Why it breaks: the script's arg parser stops at the first unrecognized token, then treats ALL remaining args (including `--chat-id`) as the message text. The `--chat-id` flag is never parsed, so it falls back to the hardcoded default `oc_6dc97fe5ef1e2ede13691456af4a3c66`.

Rule of thumb: **always put `--chat-id` BEFORE the message, and use `--` to separate flags from positional args.**

## Troubleshooting

### Common Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| `40004` | `no dept authority` — app can't see this department/user | Expand 应用可用范围, republish app |
| `230013` | `Bot has NO availability to this user` | User not in app's availability scope — add them |
| `99991663` | Search API auth failure | `/search/v1/user` requires `user_access_token`, not `tenant_access_token` |
| `403` | Forbidden on contact endpoint | Check both permission layers above |

### Diagnostics Checklist
1. Are API scopes enabled in 权限管理?
2. Is the target user in 应用可用范围?
3. Has the app been **republished** after scope changes?
4. Is it a personal Feishu account? (Personal accounts have no org structure — contact API is very limited)
5. For search: are you using `user_access_token`? (`tenant_access_token` does not work for search API)

### Cannot Send to a User
1. Check error code — `230013` = availability scope issue
2. Verify the user is in the app's 可用范围
3. Republish the app if scope was just changed
4. As a workaround: have the user send a message to the bot first — this grants the bot access to reply

### Contact API Returns Users Without Names
- Field-level permission issue
- Check 权限管理 → 通讯录 → confirm `name` field access is granted
- Some fields require the user to have set them visible in their privacy settings

## Personal vs Enterprise Feishu

| | Personal | Enterprise |
|---|----------|-----------|
| Org structure | No departments | Full department tree |
| Contact API | Very limited (only interacted users) | Full org directory (with scope) |
| Department query | Always fails (no concept) | Works with proper scope |
| Search API | Unusable (no user_access_token flow) | Requires user_access_token |
| Recommended approach | Have users message bot first | Configure availability scope |

## Finding a User on Personal Feishu (Step-by-Step)

Personal Feishu has **no org directory**. The only reliable way to discover a new contact:

1. **Ask the target user to message the bot first**
   - They search "胡中银的智能助手" (or your app name) in Feishu
   - They send any message (e.g., "hi")

2. **Extract their chat_id and open_id from gateway logs**
   ```bash
   grep "Inbound dm message" ~/.hermes/logs/gateway.log
   ```
   Look for lines like:
   ```
   [Feishu] Inbound dm message received: ... chat_id=oc_xxx text='...'
   inbound message: platform=feishu user=ou_xxx chat=oc_xxx msg='...'
   ```

3. **Verify by sending a test message**
   ```bash
   python3 ~/.hermes/scripts/feishu_send.py --chat-id oc_xxx "test"
   ```

4. **Save to memory** for future natural language use (e.g., "给0101发XXX")

### Why Other Methods Fail on Personal Feishu

| Method | Error | Reason |
|--------|-------|--------|
| `GET /contact/v3/users?department_id=0` | `40004 no dept authority` | No department concept on personal accounts |
| `GET /search/v1/user?query=xxx` | `99991663 Invalid access token` | Search API requires `user_access_token`, not `tenant_access_token`; personal accounts typically can't obtain user_access_token |
| `GET /contact/v3/users` (no dept) | Returns only interacted users | App can only see users who have chatted with the bot |

### Enterprise Feishu: Finding Users Without Messaging First

On enterprise Feishu, expand the app's availability scope:

1. Feishu Open Platform → your app → **应用可用范围**
2. Add the target department or select "全部员工"
3. **Republish the app** (版本管理与发布 → 创建新版本 → 发布)
4. Then `GET /contact/v3/users?department_id=0` will return all scoped users
