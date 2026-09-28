# Express workflow: validating every card transaction

## Why Express here

Every card transaction needs a quick sanity check before settlement trusts it. That's high volume, a few milliseconds each, the same logic every time, and nobody will ever inspect an individual run.

| | Standard | **Express** |
|---|---|---|
| Max duration | 1 year | 5 minutes |
| Pricing | per state transition | per request + duration |
| Execution history | 90 days, per execution | **none** (only via CloudWatch Logs) |
| Semantics | exactly-once | at-least-once (async) |
| Fits | settlement saga | per-transaction validation |

## What I built

- EventBridge rule `nkosi-txn-received-to-validate` on the `nkosi-payments` bus, matching `source: nkosi.acquiring`, `detail-type: TransactionReceived`.
- Target: the Express state machine `nkosi-txn-validate`, started through an EventBridge role allowed `states:StartExecution` on that one state machine.
- Definition: [`statemachines/txn-validate.asl.json`](../statemachines/txn-validate.asl.json). One `Choice` state whose rules are evaluated **in order**, first match wins:
  1. any of `txn_id`, `merchant_id`, `currency`, `amount_zar` missing → `missing_field`
  2. `currency` ≠ `ZAR` → `currency_not_zar`
  3. `amount_zar` not numeric, or ≤ 0 → `amount_not_positive`
  4. `merchant_id` doesn't match `M-*` → `unknown_merchant_format`
  5. otherwise → `ACCEPTED`
- Each outcome writes directly to DynamoDB `nkosi-txn-validations`. No Lambda.

**Why the presence checks come first:** comparing a field that doesn't exist is a runtime error in a Choice state, not a "no match". Checking `IsPresent` first turns malformed input into a clean rejection instead of a failed execution.

## Result

[`scripts/publish_txns.py`](../scripts/publish_txns.py) sent 200 `TransactionReceived` events, 10 per `PutEvents` call. Every 10th was deliberately bad, rotating through the four failure kinds.

```
run VAL: 200/200 validated | ACCEPTED 180 | REJECTED 20  (all recorded within 3s of starting to count)
  rejected   5 x amount_not_positive
  rejected   5 x currency_not_zar
  rejected   5 x missing_field
  rejected   5 x unknown_merchant_format
```

Evidence: [`16`](screenshots/16-step8-200-transactions-validated.png).

## The trade-off, demonstrated

```
aws stepfunctions list-executions --state-machine-arn <express ARN>
→ StateMachineTypeNotSupported: This operation is not supported by this type of state machine
```

Express doesn't keep a list of its executions. That's part of why it's cheap, and it means **the workflow itself must record its outcomes**. I designed it that way from the start. In production I'd also enable CloudWatch Logs at `ERROR` level, so failed executions are visible without paying to log every success.
