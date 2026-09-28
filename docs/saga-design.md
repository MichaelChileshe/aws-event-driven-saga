# The settlement saga, state by state

Definition: [`statemachines/settlement-saga.asl.json`](../statemachines/settlement-saga.asl.json). Type: **Standard**. Input: one settlement.

```json
{"settlement_id": "S-DEMO-0002", "merchant_id": "M-105", "amount_zar": "7320.50", "scenario": "transient"}
```

## Forward path

| State | What it does | On failure |
|---|---|---|
| `ReserveFunds` | DynamoDB `putItem` → `RESERVE` | nothing to undo yet: the execution fails |
| `PostLedgerCredit` | DynamoDB `putItem` → `LEDGER_CREDIT` | `Catch` → `ReleaseFunds` |
| `Payout` | Lambda `nkosi-bank-gateway` | `Retry` on `BankTimeout` (3×, 2 → 4 → 8 s); `Catch` everything else → `ReverseLedgerCredit` |
| `RecordPayout` | `putItem` → `PAYOUT` with the bank reference | **the pivot**: retried, never compensated |
| `NotifyAndAudit` | **Parallel**: EventBridge `PutEvents` `SettlementCompleted` ‖ `putItem` → `AUDIT` | retried |
| `MarkCompleted` | `putItem` → `STATUS = COMPLETED` | retried |

## Compensation path (reverse order)

`ReverseLedgerCredit` → `ReleaseFunds` → `MarkCompensated` (`STATUS = COMPENSATED`, reason = the error name) → `PublishSettlementCompensated` → `Fail: SettlementCompensated`.

- Every compensation step retries up to 5 times. An undo must not give up easily.
- The final `Fail` state marks the **execution** as `FAILED`, so it stands out in the console and in alarms, while the **ledger** is perfectly consistent. "The settlement failed" and "the books are wrong" are different things, and this design keeps them apart.

## Design choices worth calling out

**Direct service integrations.** Every DynamoDB write and both event publishes are made by Step Functions itself (`arn:aws:states:::dynamodb:putItem`, `arn:aws:states:::events:putEvents`). Only the bank call needs a Lambda. Fewer functions means less code to patch, secure and pay for.

**The retry counter reaches the bank.** `Payout` passes `"retry_count.$": "$$.State.RetryCount"` from the context object into the Lambda's payload. My simulated bank uses it to fail attempts 1 and 2 and answer on attempt 3. That's what makes the retry demonstration deterministic, and every bank reference records which attempt succeeded (`BNK-S-DEMO-0002-A3`).

**Error names come from exception classes.** The bank raises `BankTimeout` or `PayoutRejected`. Step Functions sees the class name as the error name, which is how `Retry` can target timeouts only, and why a rejection goes straight to `Catch` instead of wasting retries.

**The execution name is the idempotency key.** Executions are named after the settlement (`S-DEMO-0001`). Standard workflows refuse a second execution with the same name for 90 days, so re-submitting a settlement returns `ExecutionAlreadyExists` ([`10`](screenshots/10-step6-duplicate-settlement-refused.png)). No lock table, no extra code.

## What the three demo settlements showed

| Settlement | Scenario | Result | Evidence |
|---|---|---|---|
| `S-DEMO-0001` | ok | `SUCCEEDED`, `BNK-…-A1` | [`06`](screenshots/06-step5-completed-retried-compensated.png), [`09`](screenshots/09-step5-console-graph-happy-path.png) |
| `S-DEMO-0002` | transient | history shows `BankTimeout`, `BankTimeout`; `SUCCEEDED`, `BNK-…-A3` | [`06`](screenshots/06-step5-completed-retried-compensated.png), [`07`](screenshots/07-step5-retries-compensation-path-ledger-feed.png) |
| `S-DEMO-0003` | payout_fail | path `ReserveFunds → PostLedgerCredit → Payout → ReverseLedgerCredit → ReleaseFunds → MarkCompensated → PublishSettlementCompensated`; `FAILED: SettlementCompensated` | [`07`](screenshots/07-step5-retries-compensation-path-ledger-feed.png), [`08`](screenshots/08-step5-console-graph-compensation.png) |

`check_ledger.py DEMO`: COMPLETE 2 | COMPENSATED 1 | PARTIAL 0 | R0.00 stranded.

In the 20-settlement batch, the console showed the cost of resilience in time: the three timeout settlements took **~7.1 s** (the 2 s + 4 s backoff), and clean ones **~0.8 s** ([`12`](screenshots/12-step7-console-executions-list.png)). Seven seconds is a very good price for a settlement that doesn't need a two-day manual reconciliation.
