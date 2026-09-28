# Archive and replay: sending yesterday's events again, safely

## The scenario

Finance's reconciliation job had a bug for a day and dropped events. Once it's fixed, they need that day's events again. Re-running the settlements is out of the question: that would pay merchants twice. Replaying the **events** from the archive gives consumers another chance without touching the money.

## What AWS allows (checked before building)

- **A replay can only go back to the bus the archive belongs to.** Replaying "into a test bus" isn't possible, so isolation has to come from **routing**.
- **Replayed events carry `replay-name`.** EventBridge adds it to every replayed event, and rules can match on it. The archive's own managed rule uses `{"replay-name": [{"exists": false}]}`, so replays are never archived twice.
- **Wait about 10 minutes before replaying recent events.** Events can reach the archive with a delay, so the replay window should end 10 minutes in the past.
- The archive's `EventCount` is reconciled over 24 hours, so it isn't evidence. The replay result is.

## How I contained it

| Rule on `nkosi-payments` | Pattern | Receives replays? |
|---|---|---|
| `nkosi-settlement-feed` | `nkosi.settlement`, `replay-name` **exists: false** | no |
| `nkosi-settlements-to-finance` | `SettlementCompleted`, `replay-name` **exists: false** | no |
| `nkosi-txn-received-to-validate` | `TransactionReceived` | not in `FilterArns` |
| `nkosi-replay-inspect` | `nkosi.settlement`, `replay-name` **exists: true** | **yes: the only rule in `FilterArns`** |

Two independent guards: the patterns keep replays out of live rules, and `FilterArns` names only the inspection rule ([`replay-destination.json.tpl`](../policies/replay-destination.json.tpl)).

Before replaying, I cleared the live feed of the 21 live events that steps 7 and 9 had left in it ([`20`](screenshots/20-step10-live-feed-cleared-replay-window.png)). Otherwise the "after" check would have shown them and looked like a leak.

## The result

```
start-replay --event-start-time 2026-09-28T11:56:00Z --event-end-time 2026-09-28T13:15:54Z
  STARTING → STARTING → STARTING → RUNNING → COMPLETED
  replay ran 13:26:26 → 13:27:37 UTC  =  71 seconds
```

| Queue | Events |
|---|---|
| `nkosi-replay-inspect` | **24**: 18 `SettlementCompleted` + 6 `SettlementCompensated`, every one `replay-name: nkosi-replay-1` |
| `nkosi-settlement-feed` | **0** |
| `nkosi-finance-inbox` | **0** |

24 = 3 demo + 20 batch + 1 cross-account settlement: every settlement event in the window, and nothing else. Evidence: [`21`](screenshots/21-step10-replay-completed-71-seconds.png), [`22`](screenshots/22-step10-24-events-replayed-to-inspection-only.png), [`23`](screenshots/23-step10-live-feed-and-finance-untouched.png).

Most of the 71 seconds was setup: the replay still showed `STARTING` about a minute in, then ran and completed within seconds. For a small window, replay time is mostly setup, not per-event work. Plan recovery runbooks around a minute or two, not seconds.

## How finance would use it for real

Point a **temporary** rule, `replay-name exists: true` plus the event types they need, at their corrected consumer. Replay the affected window with `FilterArns` naming only that rule, confirm, then delete the rule. The live path never sees a duplicate.
