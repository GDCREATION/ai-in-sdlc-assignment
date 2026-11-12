# Exactly-once PayEx submission after invoice approval

**Status:** Proposed  
**Date:** 2026-11-11  
**Deciders:** Invoice approval team (workshop submission)

## Context

We are taking the invoice approval service to production with an outbound **PayEx** HTTPS integration. PayEx returns a payment reference on success. The client timeout is **30 seconds** (`stories/notes/scenario-facts.md`), and a timeout does **not** reliably mean the payment failed—the submission may have succeeded without a response.

**Volume:** Roughly **40,000 invoices per month**, with about **60%** of submissions in the last three business days of the month. Peak approve traffic is on the order of **80 actions per minute** at month-end (`stories/notes/scenario-facts.md`; corroborated by INC-2041 log line reporting 384 approvals in five minutes vs a 96 seven-day baseline).

**Operations:** Six engineers maintain the service; on-call is **tier-2**, weekly rotation, with two engineers still ramping on the codebase (`stories/notes/scenario-facts.md`).

**Today in this repo:** `ApprovalService.Approve` only updates `IInvoiceRepository`—there is **no PayEx call** under `backend/` (`backend/src/InvoiceApp.Domain/ApprovalService.cs`). Persistence is **in-memory** inside the API process (`InMemoryInvoiceRepository`). Production plans assume **Azure App Service**, **Azure SQL**, and a provisioned **Service Bus** topic that is **not wired in application code** yet (`docs/architecture/target.md`, `ops/README.md`).

**Scenario evidence:** INC-2041 (`ops/incidents/INC-2041/`) shows the failure mode when PayEx is invoked on the **synchronous approve path** after release 2.14.0: approve latency and 5xx rates spike under month-end load while PayEx’s public status stays green. That pack is scripted ops fiction, but it matches the timeout-≠-failure constraint we must design for.

**Compliance:** SOC 2 certification is targeted within six months; approval and submission audit data need a **seven-year** retention horizon (`stories/notes/scenario-facts.md`).

## Decision

Adopt **transactional outbox + dedicated submission worker** for PayEx:

1. In a **single Azure SQL transaction**, persist the invoice as `Approved` and insert a row into `submission_outbox` (same database as invoices).
2. The **approve HTTP API** commits that transaction and returns success **without** calling PayEx on the request thread.
3. A **submission worker** (separate App Service plan or equivalent) claims outbox rows with leases, calls PayEx with a **stable idempotency key per outbox row** (e.g. outbox id or invoice id + approval timestamp), and records the PayEx reference on success.
4. On **ambiguous timeout**, move the row to an `Unknown` state, **inquire PayEx by merchant reference** when an API exists, and only then retry or complete—**never** blind resubmit.
5. **v1 delivery:** **poll-based** outbox processing only. **Service Bus** remains available for optional event fan-out (e.g. notifications) but is **not** on the critical path for exactly-once submission in v1.

**Minimal supporting pieces:** outbox lag and oldest-unprocessed-age alerts; runbook for single-invoice PayEx truth checks; admin read path or SQL queries for outbox state during incidents.

### Defense against the strongest objection (option B)

The strongest objection to this pattern is **operational surface area**: a second runtime, lease bugs, and backlog growth can stall payouts while approve dashboards stay green (`stories/notes/adr-explore.md`). We accept that cost because INC-2041 demonstrated that coupling PayEx to approve is worse at month-end peaks, and because exactly-once under ambiguous timeout requires a **durable intent-to-pay** recorded **before** any external call. We mitigate backlog blindness by making **outbox lag** a tier-1 SLO (not approve p95 alone), by lease expiry metrics, and by forbidding mass replay without per-invoice PayEx verification (`stories/notes/adr-stress.md`).

## Options considered

| Option | Summary | Why not (for us) |
| --- | --- | --- |
| **A — Idempotency key + dedupe table** | Ledger row per submission; async PayEx with dedupe before call | Viable and simpler ops than full outbox. We still need inquire-before-retry and async submit. We chose **B** to align approve + intent in one **transaction** and to match the planned target shape; A collapses toward B unless we accept weaker atomicity between approval and “must pay.” |
| **B — Transactional outbox + worker** | **Selected.** Txn: approve + outbox; worker → PayEx | — |
| **C — Optimistic submit + nightly reconciliation** | Fast approve; fix drift in batch | Does not meet **exactly-once in the business window**; duplicate payments can occur before recon; weak SOC 2 story unless PayEx guarantees are proven. |

## Consequences

### Positive

- Approve latency decoupled from PayEx’s 30s tail; avoids repeating INC-2041’s synchronous coupling.
- Clear audit trail: who approved, when, outbox row id, PayEx reference (when known)—fits SQL retention policy.
- Retries and backoff isolated in the worker; API tier can scale on HTTP load without multiplying PayEx calls per instance.

### Negative

- Second deployable, on-call runbooks, and lease/outbox expertise—harder for two ramping engineers.
- **False green** risk if we only monitor approve HTTP metrics while outbox depth grows.
- PayEx **inquire API** may be missing or immature; without it, `Unknown` rows require manual process.

### Neutral

- Service Bus stays provisioned but unused on the submission critical path in v1—capacity already paid (`ops/README.md` scenario).
- Domain layer can remain free of PayEx types; integration lives in Api + worker (consistent with `AGENTS.md` boundary).

## 3 a.m. month-end failure mode

On the last working day, approve volume ~80/minute fills the outbox faster than the worker drains it if PayEx is slow or workers are under-scaled. **Approve returns 200** and SQL shows `Approved`, but **PayEx references are missing** for a growing tail of rows—finance reports “approved but not funded” while `http-5xx-rate` on approve looks fine.

A deploy or worker crash can leave rows stuck in `Processing` with **expired leases**. Alerts: `outbox-lag`, `oldest-unprocessed-age`, `outbox-lease-expired-count`, worker `PayEx_submit_timeout` rate. Tired on-call or new teammates may scale **API** instances (INC-2041 muscle memory) instead of the worker, or trigger **bulk replay** after timeouts.

**First trusted manual action:** stop automated mass-replay; inspect outbox depth and status breakdown; for **one** stuck invoice, resolve truth with PayEx (lookup by merchant reference or support); complete or retry **that row** with a fixed idempotency key; only then scale worker concurrency.

**Never:** bulk re-approve via API, delete outbox rows, or treat client timeout as proof of failure.

## Cost

### Build (one-time migration)

| Work | Estimate | Grounding |
| --- | --- | --- |
| SQL repository + migration off in-memory store | | Required for production scenario |
| Outbox schema, transactional approve, worker host, leases | **5–6 person-weeks** | Team of six, two ramping; no PayEx in `backend/` today |
| Tests, CI for worker, dashboards/alerts | | `AGENTS.md` expects tests per rule/endpoint |

*Assumption:* PayEx client and inquire flow are built net-new in the worker; INC-2041’s `PayExClient` exists only in `ops/incidents/INC-2041/deploy-diff.patch`, not in this repo.

### Run (steady state, monthly incremental)

| Item | Order of magnitude | Notes |
| --- | --- | --- |
| API App Service (3 instances) | ~$0 marginal | Already provisioned per INC-2041 scenario |
| Worker App Service (1–2 small instances) | $30–80 | **Assumption:** SKU and count sized after load test |
| Azure SQL | $50–120 | **Grounded:** ~40k rows/month growth; tier price **not** in repo |
| Service Bus | $0–25 marginal | Topic already provisioned |
| Observability | $20–60 | **Assumption:** log volume from retries |

**Total incremental:** ~**$100–285/month** (wide band; needs measurement after v1 deploy).

## Revisit when

| Trigger | Action |
| --- | --- |
| **Duplicate PayEx reference** for the same invoice/outbox id (any in prod) | Incident review; halt replays; re-evaluate idempotency key and inquire contract |
| **>0.1%** of month-end approvals lack PayEx ref **>15 minutes** after approve | Revisit worker scale, PayEx rate limits, or collapse toward option A ledger-only |
| **Reconciliation drift** (approved in SQL vs PayEx) **>0.5%** on weekly sample | Escalate PayEx API gap; consider temporary read-only approve freeze playbook |
| PayEx publishes **documented idempotency + status API** | Revisit whether option A subset can simplify worker |
| Outbox **p95 lag** exceeds agreed SLO for **2** consecutive month-ends | Capacity planning or separate PayEx submission queue tier |

## Where the agent was wrong or useless

- **Confused fiction with as-built:** Early exploration talk of “PayEx on approve” blurred `ops/incidents/INC-2041/deploy-diff.patch` (scenario) with `backend/`—today **`ApprovalService` does not call PayEx**. Any “fix the controller” advice without SQL + outbox first was misleading for this repo.
- **Run cost for Service Bus:** The agent added **$150–400/mo** bands that implied new messaging spend without stating that the topic is **already provisioned** in the scenario; marginal fan-out cost is likely near zero for ~40k messages/month unless we choose bus-driven claiming.
- **Timeout numbers:** Workshop scenario says **30s** PayEx timeout; INC-2041 logs reference a **100s** `HttpClient.Timeout` on the fictional synchronous path—the agent did not flag that mismatch when citing INC-2041 as evidence for the 30s rule.
- **Hand-wavy peak math:** “80 workers for 80 approvals/min” style reasoning appeared without using PayEx concurrency limits (unknown) or parallel in-flight cap per worker instance—sizing remains guesswork until load test.
