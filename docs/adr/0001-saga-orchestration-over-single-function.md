# ADR 0001: Replace the single settlement function with an orchestrated saga

**Status:** Accepted
**Context:** One Lambda reserved funds, credited the ledger, called the bank and marked the settlement complete. A failure at the bank call left the first two writes behind: 8 of 20 settlements PARTIAL, R76,110.00 stranded, in the reproduced run.

## Options considered

| Option | Verdict |
|---|---|
| Add try/except and manual rollback inside the function | ❌ Rollback code runs in the same process that just failed. A timeout or crash kills the rollback too, and there's no record of what was attempted |
| One database transaction across all steps | ❌ The bank payout is an external API call; it can't join a DynamoDB transaction |
| Choreography: each step emits an event, the next reacts | ⚠️ Decoupled, but "where is settlement X?" has no single answer, and compensation logic spreads across services |
| **Orchestrated saga in Step Functions Standard** | ✅ Chosen |

## Decision

- Each step is a separate state with a defined compensation: reserve ↔ release, credit ↔ reverse.
- On failure before the payout, compensation runs in **reverse order**. The payout is the **pivot**: after it, steps are retried, never compensated.
- Simple writes and event publishing use **direct service integrations**; only the bank call is a Lambda.

## Consequences

- Same batch, same failures: **0 partial, R0.00 stranded**; 15 completed, 5 cleanly compensated.
- Every settlement has a durable, step-by-step execution history for 90 days, which answers "what happened to settlement X?" in one click.
- A compensated settlement shows as `FAILED` (`SettlementCompensated`) while the ledger is consistent, so operators see failures without confusing them with corruption.
- The logic lives in a JSON state machine, not code. Changes are reviewed as definitions and validated with `validate-state-machine-definition` before deployment.
