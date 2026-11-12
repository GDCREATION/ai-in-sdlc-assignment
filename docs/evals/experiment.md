# Eval experiment (run 4)

## Changed variable

**Prompt** (only change; model and context unchanged)

## Before

v1 fixed prompt from `ops/evals/README.md`:

> Review this diff for defects. For each finding give the file, the line, what goes wrong, and how confident you are. If you find nothing, say so explicitly rather than listing general observations.

## After

v2 adds a production-behavior filter:

> Review this diff for defects. **Ignore style. Only report defects that cause wrong behavior in production.** For each finding give the file, the line, what goes wrong, and how confident you are. If you find nothing, say so explicitly rather than listing general observations.

## Hypothesis

v2 should cut **false alarms** on clean cases (especially test-only diffs like case-06) by ignoring style and hypothetical contract mismatches, with little loss on obvious code defects. Doc-only defects (case-09) may stay flaky because they are not “production behavior” in the model’s eyes.

## How run 4 was executed

- Fresh `review-evaluator` Task per case (12 total: `ops/evals/cases/case-01` … `case-10`, plus `docs/evals/cases/case-11` and `case-12`).
- v2 prompt pasted in the Task **prompt** field explicitly; subagent `.md` instructions were **not** edited (strict eval preserved).
- `prompt_version` = `v2` on run 4 rows only; runs 1–3 left unchanged.
