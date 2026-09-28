# ADR 0004: Express workflow for per-transaction validation; Standard for settlement

**Status:** Accepted
**Context:** Two very different workloads: ~5,000 settlements a night that must be exactly-once and auditable, and millions of card transactions a month that each need a millisecond sanity check.

## Decision

| | Settlement | Transaction validation |
|---|---|---|
| Type | **Standard** | **Express** |
| Trigger | one execution per settlement | EventBridge rule on `TransactionReceived` |
| Why | exactly-once, 90-day history, idempotent names | cheap per request, fast, no history needed |
| Outcome record | ledger + execution history | DynamoDB `nkosi-txn-validations` |

The Express definition is a single ordered `Choice` state with direct DynamoDB writes. Presence checks come first, so malformed input is a clean rejection, not a runtime error.

## Consequences

- 200 transactions validated, all recorded within 3 s of counting; 20 bad ones caught, 5 of each reason.
- **Express keeps no execution list** (`list-executions` → `StateMachineTypeNotSupported`), so the workflow must record its own outcomes. In production, add CloudWatch Logs at `ERROR` level.
- Express async delivery is at-least-once. The validation write is keyed on `txn_id`, so a duplicate run overwrites the same result rather than creating two.
- At Nkosi's volume, validation runs ~13× more often than settlement at a fraction of the cost (see `docs/cost-model.md`).
