---
name: review-eval
description: Scores the fixed review cases in ops/evals. Use when running, scoring, or changing the review evaluation. One fresh context per case, the fixed review prompt only, and strict caught, missed, and false-alarm counts.
---

# Review evaluation

The cases live in `ops/evals/cases/`. The set has ten diffs. Which cases contain defects is not written down. Do not look up an answer key. Do not tell the reviewer which cases are clean.

## How to run one case

1. Start a fresh context. A previous case will change the answer. Use the `review-evaluator` agent for that isolation. With Cursor **Task**, set a short `description` (e.g. `Eval case-01`) and put `Review case ops/evals/cases/case-NN.diff using review-evaluator rules.` in **`prompt`** — Task fails if `prompt` is missing.
2. Give it the case diff and the review prompt below. Nothing else: no surrounding repository tour, no hint about the defect, no other case.
3. Record one row in the results CSV, starting from `ops/evals/results-template.csv`.

## Review prompt

Use this text verbatim:

> Review this diff for defects. For each finding give the file, the line, what goes wrong, and how confident you are. If you find nothing, say so explicitly rather than listing general observations.

## Scoring

Score one case per row.

- Caught: the case has a defect and the review named that defect.
- Missed: the case has a defect and the review did not name it.
- False alarm: the case is clean and the review asserted a defect.

A finding counts as caught only when it names the actual defect. A vague "could be improved" near the right line does not count. A correct finding reached for the wrong reason does not count. On a clean case, a style suggestion is not a false alarm. A false alarm is the review asserting a defect that is not there.

Run the whole set three times before comparing rates. A single pass is an anecdote. When changing the setup, change exactly one of the prompt, the model, or the context file, then run the set again.
