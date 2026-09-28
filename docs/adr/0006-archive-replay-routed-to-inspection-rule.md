# ADR 0006: Archive every event; replay only to an inspection rule

**Status:** Accepted
**Context:** When a consumer mishandles events (a bug, an outage), it needs them again. Re-running settlements would re-pay merchants. Replaying events doesn't touch money, but a careless replay would re-notify every live consumer, including finance.

## Constraints (from the AWS documentation)

- Replays go **only to the source bus**; a separate test bus isn't possible.
- Replayed events carry a `replay-name` field that rules can match on.
- Replay windows should end ~10 minutes in the past, because archiving can lag.

## Decision

- Archive every event on `nkosi-payments` (1-day retention in the lab; production retention matches the recovery window finance needs).
- Every live rule matches `"replay-name": [{"exists": false}]`.
- A dedicated inspection rule matches `"exists": true`, and each replay names **only** that rule in `FilterArns`.

## Consequences

- 24 settlement events replayed in 71 s, each tagged `nkosi-replay-1`. Live feed received **0**; the finance account received **0**.
- Two independent guards (pattern and `FilterArns`) mean one mistake doesn't cause duplicates.
- The recovery runbook becomes: create a temporary `exists: true` rule for the corrected consumer, replay the window with `FilterArns` = that rule, verify, delete the rule.
- The archive's `EventCount` reconciles over 24 hours, so it isn't used as evidence. The replay result is.
