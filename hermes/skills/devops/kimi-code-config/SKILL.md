---
name: kimi-code-config
description: Configure Hermes to use Kimi Code API instead of Moonshot platform
triggers:
  - "kimi code"
  - "kimi code api"
  - "kimi.com/coding"
  - "use kimi code instead of moonshot"
  - "kimi endpoint"
version: 1.0
author: hermes-agent
---

# Kimi Code API Configuration for Hermes

## Overview
Configure Hermes to use Kimi Code API (`api.kimi.com`) instead of Moonshot's open platform (`api.moonshot.ai`).

## Key Differences

| Provider | Base URL | Key Prefix | Description |
|----------|----------|------------|-------------|
| Kimi Code | `https://api.kimi.com/coding/v1` | `sk-kimi-` | Kimi Code console (kimi.com/code) |
| Moonshot | `https://api.moonshot.ai/v1` | Other prefixes | Legacy Moonshot platform |
| Moonshot CN | `https://api.moonshot.cn/v1` | Other prefixes | China region |

## Configuration Steps

### 1. Set Environment Variables in `~/.hermes/.env`
```bash
# For Kimi Code (sk-kimi- prefixed keys)
KIMI_API_KEY=sk-kimi-your-key-here
KIMI_BASE_URL=https://api.kimi.com/coding/v1

# For legacy Moonshot (optional)
# KIMI_BASE_URL=https://api.moonshot.ai/v1
```

### 2. Update Config in `~/.hermes/config.yaml`
```yaml
# Use simple format (NOT nested objects)
model: kimi-coding/kimi-k2.5

# Available models for kimi-coding:
# - kimi-for-coding  (Kimi Code dedicated)
# - kimi-k2.5
# - kimi-k2-thinking
# - kimi-k2-thinking-turbo
# - kimi-k2-turbo-preview
# - kimi-k2-0905-preview
```

### 3. Restart and Test
```bash
hermes gateway restart
hermes chat -q "测试连接"
```

## Auto-Detection Logic
Hermes automatically detects the correct endpoint based on API key prefix:
- Keys starting with `sk-kimi-` → `api.kimi.com/coding/v1`
- Other keys → `api.moonshot.ai/v1` (default)
- `KIMI_BASE_URL` env var always takes precedence

## Troubleshooting

### Issue: Still using Nous Portal
- **Cause**: Config format wrong (nested objects instead of simple string)
- **Fix**: Use `model: kimi-coding/kimi-k2.5` not nested YAML

### Issue: 404 Model Not Found
- **Cause**: Provider still set to `nous` instead of `kimi-coding`
- **Fix**: Ensure model string includes provider prefix

### Issue: Banner Shows "Nous Research"
- **Note**: This is hardcoded in `hermes_cli/banner.py` line 380
- **Reality**: Display text doesn't reflect actual provider
- **Ignore**: This is cosmetic, not functional

### Issue: Authentication Errors
- **Check**: Key starts with `sk-kimi-` for Kimi Code
- **Verify**: Account has sufficient balance
- **Test**: `curl -H "Authorization: Bearer $KIMI_API_KEY" $KIMI_BASE_URL/models`

## Verification Commands
```bash
# Check current config
hermes config show | grep -A5 "Model"

# Check environment
source ~/.hermes/.env
echo ${KIMI_API_KEY:0:8}  # Should show: sk-kimi-
echo $KIMI_BASE_URL        # Should show: https://api.kimi.com/coding/v1

# Test connection
hermes doctor | grep -i kimi
```

## Notes
- The `kimi-coding` provider in `auth.json` should show `base_url: "https://api.kimi.com/coding/v1"`
- Kimi Code API is compatible with OpenAI format
- Provider auto-detection is in `hermes_cli/auth.py` (`_resolve_kimi_base_url` function)
- Available models are defined in `hermes_cli/models.py` under `_PROVIDER_MODELS["kimi-coding"]`