# Agent setup audit vs lethal trifecta

**Date:** 2026-11-12  
**Scope:** Repo-configured Cursor agent setup (`.cursor/`, `docs/augmentation/`). Runtime IDE plugins (extra MCP namespaces) are noted where they widen blast radius beyond what the repo declares.

## Framework (Simon Willison — session / course)

The **lethal trifecta** is three capabilities in the **same** agent loop. If all three are present, prompt injection and confused-deputy behavior can turn untrusted text into theft or destructive action; removing **at least one** leg is the architectural fix.

| Leg | Name |
| --- | --- |
| **A** | Access to **private data** (secrets, customer data, tokens, full repo, local files) |
| **B** | Exposure to **untrusted / attacker-controlled content** (web pages, issues, MCP results, fetched docs) |
| **C** | Ability to **communicate or act externally** (HTTP, git push, shell side effects, browser posting data out) |

This audit does **not** claim the repo is safe. It scores what is configured here.

---

## 1. Setup summary

### Hooks and logging

| Item | Evidence |
| --- | --- |
| Hook manifest | `.cursor/hooks.json` — registers five hooks: `beforeSubmitPrompt`, `afterMCPExecution`, `afterFileEdit`, `subagentStop`, `stop` |
| Hook script | `.cursor/hooks/augmentation-log.py` — appends JSONL to `docs/augmentation/log.jsonl` |
| Fail-open | `augmentation-log.py` docstring and `except` block: errors exit 0 and still return `{"continue": true}` for `beforeSubmitPrompt` (lines 2, 64–70) |
| Redaction | Only demo password `ChangeMe123!` → `[redacted]` (`SECRET`, `redact()`, lines 11–15, 35) |
| Activation | `docs/augmentation/README.md`: Cursor loads `.cursor/hooks.json` after save (no `hooksrt.json` in this repo — story typo; active file is `hooks.json`) |
| Log volume | `docs/augmentation/log.jsonl` — **180** lines at audit time (`wc -l`) |

### MCP (repo)

`.cursor/mcp.json` declares:

| Server | Blast-radius note |
| --- | --- |
| `playwright` | Browser automation — untrusted web content (leg B) and outbound navigation / network (leg C) |
| `mermaid` | Diagram generation — lower direct exfil risk; still runs `npx` subprocess |

Repo MCP does **not** list git-write or shell MCP servers; those can still exist via Cursor built-ins (`Shell` tool) and user-installed plugins (browser, GitKraken, etc.) outside this file.

### Subagents and skills

| Path | Role |
| --- | --- |
| `.cursor/agents/architecture-cartographer.md` | As-built diagrams from code; refuses fictitious `ops/` infra |
| `.cursor/agents/review-evaluator.md` | Fixed eval review prompt for `ops/evals` diffs |
| `.cursor/skills/cited-diagrams/` | Diagram conventions |
| `.cursor/skills/invoice-app-map/` | Codebase map skill |
| `.cursor/skills/review-eval/` | Eval workflow skill |

### Inventory snapshot (2026-11-12)

```
.cursor/hooks.json, mcp.json
.cursor/hooks/augmentation-log.py
.cursor/agents/ (2)
.cursor/skills/ (3)
docs/augmentation/log.jsonl (180 lines)
```

---

## 2. Trifecta legs in this setup

### Leg A — Private data

**Verdict: present (partial mitigations)**

| Evidence | Why |
| --- | --- |
| Full workspace read | Agent conventions (`AGENTS.md`) and normal Cursor use imply read access to source, `ops/` packs, and local git state |
| Prompt logging | `beforeSubmitPrompt` stores full `prompt` text in `log.jsonl` (`augmentation-log.py` lines 31–35; `docs/augmentation/README.md` table) — expands private-data surface if logs are committed or shared |
| Redaction gap | README states MCP result bodies are not stored, but only one literal secret is redacted |

Partial: no production DB or PayEx credentials in the app repo itself; demo credentials are documented and partially redacted in logs.

### Leg B — Untrusted content

**Verdict: present (partial)**

| Evidence | Why |
| --- | --- |
| `playwright` MCP | `.cursor/mcp.json` — agent can load arbitrary web pages into context |
| Repo + hand-ins | `ops/incidents/`, eval diffs, and future issues/PR text are attacker-influenceable if sourced from outside a tight trust boundary |
| Runtime plugins | Browser / fetch / search tools (when enabled in the IDE) ingest third-party content without repo-level restriction |

Partial: assignment work is mostly local files under team control; no RAG over customer tickets in repo config.

### Leg C — External communication / exfiltration

**Verdict: present (partial)**

| Evidence | Why |
| --- | --- |
| `playwright` MCP | Can drive a real browser and hit external URLs (`.cursor/mcp.json`) |
| Cursor `Shell` | Not in `mcp.json` but available to the agent in standard Agent mode — network when permitted, file writes, `git` commands |
| User rules | Commit/push allowed when explicitly requested — git write is human-gated by policy, not by hook |
| Hooks | `afterMCPExecution` logs server/tool names only, not payloads (`augmentation-log.py` 36–39) — does not block exfil |

Partial: repo MCP omits explicit “git write” MCP; destructive git still possible via shell if the human approves tool runs.

### Combined assessment

For a typical **Agent mode** session on this project, **all three legs are at least partial**. That matches the trifecta warning: the workshop setup prioritizes observability (JSONL hand-in) and capability (Playwright, subagents) over cutting a leg.

### MCP servers that expand blast radius (repo + typical runtime)

| Source | Capability |
| --- | --- |
| `.cursor/mcp.json` → `playwright` | Browser, untrusted input, outbound HTTP |
| `.cursor/mcp.json` → `mermaid` | Subprocess / `npx` (supply-chain exposure, not primary exfil) |
| Cursor built-in `Shell` | Git, curl, deploy commands, file system |
| Optional IDE MCP (e.g. browser, GitKraken) | Git push, PR create, live browsing — **not** in repo `mcp.json` but often enabled locally |

---

## 3. Decision

**Redesign — remove leg A’s weakest link for this repo: stop persisting full prompt bodies in the augmentation log.**

Rationale:

- Legs B and C are needed for the assignment (web research, tests, Playwright e2e, git workflow).
- Leg A cannot be eliminated entirely while the agent edits a real repo, but **full prompt retention** in a committable `log.jsonl` is the highest-risk *repo-owned* amplifier: it duplicates secrets, PII, and proprietary text with only demo-password redaction.

Concrete change (not yet implemented in code; recorded as the chosen redesign):

1. In `.cursor/hooks/augmentation-log.py`, log `prompt_length` and a **SHA-256 hash** of the redacted prompt instead of the `prompt` field.
2. Update `docs/augmentation/README.md` to document the new schema.
3. Add `docs/augmentation/log.jsonl` to a pre-commit or CI check that fails if a line contains `"prompt":` with length &gt; 0 (belt-and-suspenders).

We **do not** accept “all three legs with full prompt logging” as a steady state for anything beyond local solo use.

---

## 4. Revisit trigger

Re-audit or block agent autonomy if **any** of the following occur:

| Trigger | Measurement |
| --- | --- |
| **Secret in hand-in log** | `rg -i '(api[_-]?key|password|Bearer |BEGIN (RSA )?PRIVATE)' docs/augmentation/log.jsonl` returns a hit **other than** `[redacted]` or documented demo strings |
| **Unreviewed merge** | A commit lands on `main` authored by automation (bot email or message tag `cursor-agent`) without an associated human-approved PR in the same 24h window |
| **Playwright exfil pattern** | `afterMCPExecution` rows show `playwright` + tool names suggesting navigation, and the same session’s `beforeSubmitPrompt` hash/length correlates with a user report of unintended external URL access |

If any trigger fires: implement the prompt-hash redesign immediately, remove `playwright` from `.cursor/mcp.json` until reviewed, and re-run this audit.

---

## 5. Checklist (story done-when)

- [x] Each trifecta leg: present / absent / partial with file citations
- [x] Single decision: **redesign** (strip full prompt logging), not vague accept-and-hope
- [x] Revisit triggers are specific and measurable
