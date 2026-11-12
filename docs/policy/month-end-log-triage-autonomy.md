# Month-end log triage — autonomy policy (Invoice Approval, tier-2)

**Applies to:** Weekly on-call during the last three business days of the month (approval/payment peaks). **Team:** Six engineers; two ramping.

Use `ops/incidents/INC-2041` (PayEx errors after deploy) and `INC-2047` (notifications stalled after schema rename) as reference triage: investigate read-only, present mitigations with cost/undo, no solo prod change in a live month-end incident.

## Autonomy levels

| Level | Name | Without named approver |
| --- | --- | --- |
| **R0** | Observe | Logs, metrics, `ops/pipeline/run-timings.csv`, read-only Service Bus inspect, vendor status. No writes. |
| **R1** | Recommend | Correlate evidence, rank hypotheses, draft Slack/IC updates, list mitigations with blast radius and undo. |
| **R2** | Execute (guarded) | Approved runbook only; caps on scope and rate; audit log; no payment, schema, or messaging contract changes. |
| **R3** | Autonomous (SLO) | Bounded, reversible automation (e.g. capped scale-out) when error budget allows and month-end freeze is off. |

**Never unattended R3:** PayEx submit/replay/mass inquiry; DB or schema migration; month-end rollback; Service Bus subscription or rule changes; API key rotation; bulk notification backfill; anything risking double-pay or audit loss.

## Controls by level

| Level | Controls |
| --- | --- |
| R0 | Read-only observability role; time-boxed exports; cite log lines. |
| R1 | Template includes “known / not done”; no imperative prod commands in drafts. |
| R2 | Runbook, blast-radius cap, metric check before repeat; IC within 15 minutes. |
| R3 | Resource ceilings, auto-revert, month-end freeze unless IC tags incident; audit stream. |

## Task → level mapping

| Task | Level | Promote when | Approver |
| --- | --- | --- | --- |
| Correlate logs, metrics, deploy/CI (INC-2041) | R0→**R1** | Two matching postmortems; &lt;20% false positives on drills | Engineering lead |
| Slack / IC summary (INC-2047) | **R1** | IC used draft unchanged on three incidents | On-call lead |
| Vendor status; open ticket (no PayEx API write) | R1→**R2** | No mistaken sev-1 tickets in 90 days | Incident commander |
| Propose rollback, scale, restart (options only) | **R1** | IC picked ranked options twice without reorder | IC + release owner |
| Restart one App Service web instance | **R2** | Game day: restart helped without masking cause | Platform lead + IC |
| Scale App Service (+1, max 5) | R2→**R3** | Game day met SLO; no payment regression | Platform lead |
| Restart notification worker | **R1** | Queue depth rules out filter mismatch (INC-2047) | IC |

Payment/outbox paths: **R1 max** for restart or replay proposals; execution needs IC plus a reader of `docs/decisions/exactly-once-payex.md`.

**Global promotion:** Per task, not per person—drills or incidents, approver sign-off, retro confirms controls. Demote after unapproved prod change or payment near-miss.

## Day-one level for this rotation

**Maximum on day one: R1 (Recommend).** Week one allows R0 and R1 only—no R2 runbooks and no R3 until a joint game day (INC-2041 correlation plus guarded restart drill) includes all six engineers. Two ramping engineers lack context for PayEx, outbox, and event naming; INC-2047 shows zero worker throughput often means subscription filters, not a restart. R2 restarts before that training repeat INC-2041’s brief false relief and invite month-end mutation without IC. R1 still delivers fast correlation and finance-ready summaries; every prod change waits on IC or engineering lead. Payment-side actions stay human-only on day one—we do not accept unattended risk.
