# Review eval summary

## Method

| Item | Value |
| --- | --- |
| Model | `composer-2.5-fast` |
| Prompt | v1 (runs 1–3, 11–12 baseline rows), v2 (run 4 only) — see `docs/evals/experiment.md` |
| Reviewer | `review-evaluator` subagent via Cursor Task |
| Isolation | Fresh Task per case; single diff path only |
| Cases | 10 fixtures under `ops/evals/cases/` plus custom `docs/evals/cases/case-11.diff`, `case-12.diff` |

v2 adds: *Ignore style. Only report defects that cause wrong behavior in production.*

## Ground truth

Labeled in `stories/notes/eval-ground-truth.md` by reading each diff in isolation (no repo answer key). **9 defect** cases (`case-01`–`03`, `05`, `07`–`11`) and **3 clean** cases (`04`, `06`, `12`). Custom cases: **case-11** maps approval conflicts to HTTP 200; **case-12** renames `EnsurePending` only.

## Results table (cases with known truth, n=12 per run)

| Run | Prompt | Caught | Missed | False alarm | Clean OK | Caught rate | False alarm rate |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | v1 | 9 | 0 | 0 | 3 | 100% (9/9) | 0% (0/3) |
| 2 | v1 | 8 | 1 | 0 | 3 | 88.9% (8/9) | 0% (0/3) |
| 3 | v1 | 8 | 1 | 1 | 2 | 88.9% (8/9) | 33.3% (1/3) |
| 4 | v2 | 7 | 2 | 1 | 2 | 77.8% (7/9) | 33.3% (1/3) |

**Rates:** caught rate = `caught / (caught + missed)`; false alarm rate = `false_alarm / (false_alarm + clean_ok)`.

**Baseline average (runs 1–3):** caught **92.6%** (25/27), false alarm **11.1%** (1/9).

## Flip analysis (runs 1–3)

| Case | Truth | Run 1 | Run 2 | Run 3 | Note |
| --- | --- | --- | --- | --- | --- |
| case-09 | defect | caught | missed | missed | Doc-only false reset claim; often skipped |
| case-06 | clean | clean_ok | clean_ok | false_alarm | Run 3 invented test/production contract defects |
| case-11 | defect | caught | caught | caught | Stable across v1 runs |
| case-12 | clean | clean_ok | clean_ok | clean_ok | Stable across v1 runs |

All other cases (01–05, 07–08, 10): stable **caught** or **clean_ok** across runs 1–3.

## Experiment (run 4 vs baseline)

| Metric | Avg runs 1–3 | Run 4 (v2) | Better? |
| --- | ---: | ---: | --- |
| Caught rate | 92.6% | 77.8% | **No** — missed `case-07` (PII logging) and `case-09` (README) |
| False alarm rate | 11.1% | 33.3% | **No** — fixed `case-06` but **false alarm** on `case-12` (invented `ReportsRepository`) |

**Verdict: Nuanced.** v2 did what we hoped on **case-06** (clean test diff left alone) but traded away sensitivity on logging/docs and did not prevent a hallucinated defect on a rename-only custom case.

## Confidence at this sample size

With **n = 12** cases per run and a **stochastic** LLM reviewer, these numbers are **directional only**, not stable estimates. One flip on `case-09` or `case-06` moves caught or false-alarm rate by ~8–11 points. To narrow a rate to about **±5%** at this defect/clean mix would need **roughly twice as many labeled cases** and more than three baseline runs. I would not choose production reviewer settings from run 4 alone without manual adjudication on **case-07** (is PII logging a “production defect” for your policy?) and **case-12 run 4** (clear false alarm).

## Manual adjudication candidate

**case-12, run 4** — reviewer described changes in `ReportsRepository.cs` that do not exist in `case-12.diff`; score as false alarm. Worth a human read of the subagent transcript before treating v2 as safe on scary refactors.
