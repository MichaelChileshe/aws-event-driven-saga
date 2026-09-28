# Debugging journey

This build ran clean first time: every step did what it was designed to do. What's worth recording is the judgement calls made before and during the build that kept it that way, and the AWS behaviours that would have produced wrong conclusions if I hadn't planned around them.

---

## 1 · The replay plan changed when I checked the documentation

**The original idea:** replay yesterday's events from the archive into a separate *test* bus, so nothing live could be affected.

**What I found:** EventBridge only replays to the **source** bus the archive belongs to. A separate test bus isn't an option.

**What I built instead:** isolation by routing. Two independent guards:

1. Every live rule matches `"replay-name": [{"exists": false}]`; the inspection rule matches `"exists": true`.
2. The replay's `FilterArns` names only the inspection rule.

**Result:** 24 events replayed, and 0 reached the live feed or the finance account ([`23`](screenshots/23-step10-live-feed-and-finance-untouched.png)).

**Lesson:** read the service limits before designing around an assumption. Finding this in the design stage cost ten minutes. Finding it mid-incident would have cost a lot more.

---

## 2 · Clearing the live feed before the "after" check

**The risk:** by the time of the replay, steps 7 and 9 had left **21 live events** in `nkosi-settlement-feed`. If I'd replayed straight away and then read the feed, I'd have seen 21 events and concluded the replay had leaked into live consumers, which would be a false positive.

**What I did:** read and removed those 21 first (16 `SettlementCompleted`, 5 `SettlementCompensated`, all with no `replay-name`), recorded them ([`20`](screenshots/20-step10-live-feed-cleared-replay-window.png)), then replayed. The after-check read 0.

**Lesson:** a test only proves something if its starting state is known. Reset the thing you're about to measure.

---

## 3 · Express workflows keep no execution list

```
aws stepfunctions list-executions --state-machine-arn <express ARN>
→ StateMachineTypeNotSupported
```

Express workflows don't record per-execution history; that's part of why they're cheap. I knew this going in, so the validator writes every outcome (ACCEPTED, or REJECTED with a reason) to DynamoDB. That table is how I proved 200 of 200 were handled ([`16`](screenshots/16-step8-200-transactions-validated.png)).

**Lesson:** when you choose a service for its cost profile, check what observability you give up, and design the replacement in.

---

## 4 · Not trusting the archive's EventCount

`describe-archive` reports `EventCount` and `SizeBytes`, but AWS reconciles those values over **24 hours**, so they can read 0 for events archived minutes ago. I didn't use them as evidence. The replay itself (24 events delivered, each tagged `nkosi-replay-1`) proved the archive held what it should.

---

## 5 · IAM propagation never bit, by design

Five new roles were each used seconds after creation (Lambda, Step Functions, EventBridge). New IAM roles can take a few seconds before a service is allowed to assume them, and the failure ("role cannot be assumed") looks alarming. I chained `sleep 10` into every create-role-then-use sequence, so it never happened.

---

## 6 · Reading time in the execution list

The saga console listed the three timeout settlements at **~7.1 s** and every clean one at **~0.8 s** ([`12`](screenshots/12-step7-console-executions-list.png)). That's not a performance problem. It's the retry backoff (2 s + 4 s) doing its job, and it's the cheapest possible cost of a settlement that would otherwise have needed manual reconciliation. It's also a useful operational signal: a spike in settlement duration means the bank is slowing down, before it starts failing.
