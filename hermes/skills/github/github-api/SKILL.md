---
name: github-api
description: GitHub REST API scraping patterns — rate limiting, search queries, data collection, and common pitfalls discovered through trial and error.
---

# GitHub API Scraping Patterns

Use when: fetching repo data, searching GitHub programmatically, building trend/metric trackers.

## Rate Limiting (Critical)

GitHub API has strict rate limits:
- **Without token**: 10 search requests/minute, 60 core requests/hour
- **With token**: 30 search requests/minute, 5000 core requests/hour

### Pitfall: 403 errors from too many queries
Discovered during github_trends.py development: 7 sequential search queries with 3s delay triggered rate limiting on second run.

### Solution: Minimize queries + generous delays
- Use **at most 3 search queries** without a token
- Add **8 second delay** between queries (safe margin)
- Use `stars:>20000` filter to get high-quality results from fewer queries
- Combine terms with `OR` in a single query to cover more ground

## Search Query Optimization

### Use GitHub search qualifiers for precision
```
?q=artificial+intelligence+stars:>20000          # filter by star count
?q=llm+OR+generative+AI+stars:>20000            # combine keywords with OR
?sort=stars&order=desc&per_page=30               # sort by stars, max 30 per page
```

### Python type annotations
On systems with Python < 3.10, `dict | None` syntax fails. Always use:
```python
from typing import Optional, List
def func(data: Optional[dict]) -> List[dict]:
```

## Data Collection Pattern

1. Fetch with multiple queries, deduplicate by `full_name`
2. Sort globally by star count
3. Save daily snapshots to `~/.hermes/data/<tracker>/YYYY-MM-DD.json`
4. Compare current vs snapshot for trend analysis

## Authentication

GitHub token stored in `~/.hermes/.env` as `GITHUB_TOKEN`. Currently commented out — uncomment and set for higher rate limits. The script checks `os.environ.get("GITHUB_TOKEN")` and adds `Authorization: token <TOKEN>` header if present.
