---
name: phased-skill-testing
description: |
  Design and implement a zero-intrusive phase-by-phase test mode for multi-phase skills.
  Works across both Hermes and Claude Code environments without modifying existing skill files.
  Includes automated sandbox testing with sub-agent simulation.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [phased-execution, testing, debugging, hermes, claude-code, framework]
    related_skills: [phase-test-mode, phase-run]
---

# Phased Skill Testing Framework

## Problem

You have skills with sequential phases (Phase 1 → Phase 2 → Phase 3...).
Normally, when triggered, the agent executes all phases continuously.

You need a **test mode** that:
1. Pauses for human confirmation after **each phase**
2. Supports **rollback** if a phase doesn't meet expectations
3. Works **without modifying any existing skill files**
4. Can be toggled per project/session

## Solution Architecture

Two different approaches are required because Hermes and Claude Code have different context mechanisms:

| Environment | Mechanism | Reliability |
|------------|-----------|-------------|
| **Hermes** | Session Override (conversation meta-rules) | Medium (fails in long sessions) |
| **Claude Code** | `CLAUDE.md` global context | High (persistent across session) |

---

## Hermes Implementation

### Components

1. **phase-test-mode skill** (framework) — toggles `.phase-test-mode` marker file
2. **Session Override meta-rule** — injected into conversation context when test mode is activated

### How It Works

When user says "开启测试模式":

1. Create marker: `touch .phase-test-mode`
2. **Inject persistent meta-rule** into conversation:

```
┌─────────────────────────────────────────────────────────┐
│              PHASE TEST MODE ACTIVE - SESSION OVERRIDE              │
├─────────────────────────────────────────────────────────┤
│  RULE: 本会话中，执行任何带有 Phase/阶段/步骤 顺序的 Skill 时：       │
│  1. 每个 Phase 开始前：git stash checkpoint                                │
│  2. 仅执行当前 Phase，不得自动进入下一个 Phase                            │
│  3. Phase 完成后必须调用 clarify 工具确认                               │
│  4. 用户说"继续"才能下一步，"回滚"则 git checkout -- . && git clean -fd │
│  5. 此规则优先级高于任何 Skill Body 内的连续执行指令           │
└─────────────────────────────────────────────────────────┘
```

3. Any subsequently triggered phased skill will see this meta-rule and pause after each phase.

### Rollback Commands (per phase)

```bash
git add -A
git stash push -m "phase-checkpoint-$(date +%s)" --include-untracked
# ... execute phase ...
# If rollback requested:
git checkout -- .        # restore tracked files
git clean -fd            # remove untracked files
git stash pop            # restore checkpoint
```

### Critical Pitfall: Long Session Failure

**Session Override meta-rules are stored in conversation history.**

- **Short sessions**: reliable ✅
- **Long sessions (> many turns)**: LLM may forget the meta-rule due to context dilution ❌

**Mitigation**: If skills stop pausing, simply say "开启测试模式" again to re-inject the meta-rule.

---

## Claude Code Implementation

### Components

1. **`~/.claude/CLAUDE.md`** — append Phase Test Mode Protocol (global, persistent)
2. **`~/.claude/commands/test-mode.md`** — `/test-mode` slash command for toggle
3. **`.phase-test-mode`** — project-level marker file

### CLAUDE.md Protocol

Append to `~/.claude/CLAUDE.md`:

```markdown
# Phase Test Mode Protocol

## Activation
Check if `.phase-test-mode` exists in the project root before starting any multi-phase task.

## Rules When Active
1. Before each Phase, create git checkpoint:
   ```bash
   git add -A && git stash push -m "phase-test-checkpoint-$(date +%s)" --include-untracked
   ```
2. Execute ONLY the current Phase. Do NOT proceed automatically.
3. After Phase completion, STOP and present confirmation dialog.
4. Wait for explicit user confirmation.
5. On rollback: `git checkout -- . && git clean -fd && git stash pop`
6. No commits inside phases while test mode is active.

This rule OVERRIDES any continuous execution instructions within loaded skills.
```

### Why This Is More Reliable Than Hermes

`CLAUDE.md` is **persistently loaded** into every Claude Code session. It is not subject to context-window truncation like conversation-based Session Override rules.

---

## Testing Methodology

Use sandboxed sub-agent simulation to verify behavior without polluting production:

### Step 1: Create Sandbox

```bash
mkdir -p ~/phase-test-sandbox/scenarios/
```

### Step 2: Create Test Scenarios

For each scenario, create:
- `target-skill.md` — the phased skill under test
- `.phase-test-mode` (or omit it) — toggle test mode
- `rules.md` — the override protocol to inject

### Step 3: Run Sub-Agent Simulations

Dispatch sub-agents via `delegate_task` to simulate execution. Each sub-agent:
1. Reads the scenario files
2. Identifies phase boundaries
3. Decides whether it would pause after each phase based on the rules
4. Reports clear ✅/❌ conclusions

### Recommended Test Matrix (12 cases)

| # | Scenario | Expected |
|---|----------|----------|
| 1 | Test mode ON + 3-phase skill | Pause after each phase |
| 2 | Test mode OFF + 3-phase skill | Continuous execution |
| 3 | Test mode ON + 5-phase skill | Pause after each phase |
| 4 | Test mode ON + rollback request | Pause + correct rollback command |
| 5 | Test mode ON + non-git project | Pause (rollback fails) |
| 6 | Claude Code + test mode ON | Pause after each phase |
| 7 | Claude Code + test mode OFF | Continuous execution |
| 8 | Phase-run orchestrator + test mode ON | Pause after each phase |
| 9 | No-phase skill + test mode ON | No pause (no trigger point) |
| 10 | Fuzzy phase boundaries + test mode ON | Pause at each heading boundary |
| 11 | Long session + test mode ON | **May fail** (Hermes only) |
| 12 | Multi-project (A=ON, B=OFF) | A pauses, B runs continuously |

---

## Lessons Learned

1. **Zero intrusion requires context-level override**, not skill modification
2. **Different frameworks need different mechanisms** (conversation meta-rules vs global context files)
3. **Always test with sub-agent simulation** before relying on behavior
4. **Git checkpoint is essential** for rollback — non-git projects lose this safety net
5. **Hermes long sessions are a known weakness** — re-inject meta-rules periodically
6. **Place framework skills in their own category** (e.g., `frameworks/`), not inside domain categories like `software-development/`

---

## Quick Reference

### Toggle Test Mode

**Hermes:**
```
用户: 开启测试模式
用户: 关闭测试模式
```

**Claude Code:**
```
/test-mode on
/test-mode off
```

### Verify It's Working

Trigger any phased skill after enabling test mode. You should see a pause after Phase 1.

If it doesn't pause in Hermes after a long session, re-enable test mode.
