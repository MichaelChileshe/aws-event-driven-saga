# ADR 0003: Use the settlement ID as the execution name

**Status:** Accepted
**Context:** Duplicate submissions (a scheduler retry, a double-click, a replayed message) are how merchants get paid twice.

## Decision

Every saga execution is started with `--name <settlement_id>`.

## Why this works

Step Functions Standard refuses a second execution with the same name on the same state machine for 90 days. If the first execution is still running **and** the input is identical, AWS returns the original execution instead of starting a new one. Either way, the settlement runs once.

## Consequences

- Re-submitting `S-DEMO-0001` returned `ExecutionAlreadyExists` (exit 254). No lock table, no extra code.
- Settlement IDs must be unique and stable at the source, and never reused. That's a reasonable business rule for a payments ledger anyway.
- The protection covers 90 days. Beyond that, the ledger itself (a `STATUS` item per settlement) is the long-term guard.
- Express workflows don't offer this guarantee, which is one reason settlement is Standard (ADR 0004).
