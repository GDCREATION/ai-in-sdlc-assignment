# Measurement plan — baselines before on-call

**Context:** The invoice approval service described under `ops/` is not deployed from this demo repo. This plan names **production-intent** metrics, states what we can measure **today** from fiction (`ops/pipeline/`) and local git, and records **two baselines captured on 2026-11-12**.

Nothing here substitutes for live VCS, deploy, or incident tooling once the real service ships.

---

## Metrics and data sources

| Metric | Definition (production) | Source / query (when live) | What we have in this repo | Proxy vs production-ready |
| --- | --- | --- | --- | --- |
| **Lead time for changes** | Time from first commit on a change until that change is running in production (DORA: commit → deploy) | GitHub/GitLab API: PR `created_at` → deploy workflow success on `main`; or Argo/CD audit | **Not measurable:** this clone has linear workshop commits, no PR timestamps, no deploy events. Local git cannot approximate prod lead time. | **Proxy (future):** sum of PR open→merge (VCS) + pipeline median below as a *lower bound* on “change ready” until deploy telemetry exists. |
| **Change failure rate** | % of production deploys that cause rollback, hotfix revert, or SEV within 24h | Deploy tracker + incident index; numerator = failed deploys or linked INC | **Proxy today:** `ops/pipeline/run-timings.csv` — % of CI runs where `conclusion != success` (failed main/PR pipeline ≈ change would not have shipped). | **Proxy** until deploy + incident correlation exists. |
| **Review turnaround** | Time from PR opened to first human review comment (or approval) | VCS pull request timeline API | **Not measurable:** no PR export in repo. | **Proxy (future):** time from PR open → first CI `success` on latest push (automated “ready for human” signal), or calendar SLA from team policy. Until then, track **Unit tests** step duration in CI as a *capacity* signal for how fast automated review gates complete. |

### Supporting artefacts

| File | Use |
| --- | --- |
| `ops/pipeline/ci-pipeline.yml` | Step names for interpreting `run-timings.csv` (Unit tests, Static analysis, E2E, container scan, …). |
| `ops/pipeline/run-timings.csv` | Last **20** fictional production CI runs (step-level `duration_seconds`, per-run `conclusion`). |
| `.github/workflows/ci.yml` (demo) | Cut-down CI for the assignment app — **not** the production pipeline above. |

### Ongoing collection (after go-live)

1. **Lead time:** weekly export `pull_request` events + production deploy workflow completions; report p50/p90 in hours.
2. **Change failure rate:** monthly — `(rollbacks + hotfix_deploys) / total_prod_deploys`, cross-check `ops/incidents/`.
3. **Review turnaround:** weekly p50 from VCS; alert if p90 &gt; 4 business hours for `main`-bound PRs.

---

## Baselines captured today (2026-11-12)

Two numbers measured from `ops/pipeline/run-timings.csv` in this repository.

### Baseline 1 — Median total CI duration per run (**proxy** for “time to know if a change is safe”)

| Field | Value |
| --- | --- |
| **Metric** | Total pipeline duration (sum of all steps per `run_number`) |
| **Value** | **1875 seconds** (~31.3 minutes) median over 20 runs |
| **Also** | mean 1880.5 s; min 1702 s; max 2108 s |
| **Source** | `ops/pipeline/run-timings.csv` |
| **Captured at** | 2026-11-12 (local) |

**Reproduce:**

```bash
python3 - <<'PY'
import csv
from collections import defaultdict
from statistics import mean

path = "ops/pipeline/run-timings.csv"
totals = defaultdict(int)
with open(path) as f:
    for row in csv.DictReader(f):
        totals[int(row["run_number"])] += int(row["duration_seconds"])
vals = sorted(totals.values())
n = len(vals)
med = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
print("runs:", n)
print("median_seconds:", int(med))
print("mean_seconds:", round(mean(vals), 1))
print("min:", min(vals), "max:", max(vals))
PY
```

**Label:** **Proxy** — production pipeline fiction, not this repo’s `.github/workflows` runs.

---

### Baseline 2 — CI change failure rate (**proxy** for change failure rate)

| Field | Value |
| --- | --- |
| **Metric** | % of pipeline runs with `conclusion != success` |
| **Value** | **10.0%** (2 failed of 20 runs; runs **6** and **14**) |
| **Source** | `conclusion` column on each row of `ops/pipeline/run-timings.csv` (one conclusion per `run_number`) |
| **Captured at** | 2026-11-12 (local) |

**Reproduce:**

```bash
python3 - <<'PY'
import csv
from collections import defaultdict

path = "ops/pipeline/run-timings.csv"
conclusion_by_run = {}
with open(path) as f:
    for row in csv.DictReader(f):
        conclusion_by_run[int(row["run_number"])] = row["conclusion"]
failed = [rn for rn, c in conclusion_by_run.items() if c != "success"]
print("failed_runs:", len(failed), "of", len(conclusion_by_run))
print("failure_rate_pct:", round(100 * len(failed) / len(conclusion_by_run), 1))
print("failed run_numbers:", failed)
PY
```

**Label:** **Proxy** — CI failure ≠ production incident; use as a **pre-deploy** quality gate baseline until deploy rollback data exists.

---

## Third metric — not captured as a number today

**Review turnaround** is **not measurable from this repository** (no PR timeline export). When VCS is available, use first-review timestamp minus PR `created_at`. Interim capacity proxy already in CSV: **Unit tests** step median **86 s** (same file, `step == "Unit tests"`) — useful for pipeline tuning, not human review SLA.

---

## How we will use these baselines

| Baseline | Target direction (first 90 days on-call) |
| --- | --- |
| Median CI ~31 min | Keep p50 under 35 min while adding PayEx integration tests; watch **Static analysis** and **E2E** steps in `run-timings.csv` for regressions. |
| CI failure 10% | Drive below **5%** on `main` by fixing flaky E2E and container scan; correlate each remaining failure with a ticket before treating CFR as acceptable. |
| Review turnaround (TBD) | Establish VCS p50 within two weeks of cutover; until then, no SLA claim. |

---

## Done-when checklist (story 13)

- [x] Plan lists all three metrics with sources
- [x] Two numbers captured with commands reproduced above
- [x] Proxy vs production-ready labeled per metric
