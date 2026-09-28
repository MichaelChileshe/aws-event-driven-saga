# Cost model

## What this build cost

Everything in this design bills **per use**. Nothing runs by the hour, so an idle settlement platform costs close to nothing.

| Item | Usage in this build | Approx. cost (us-east-1 list price) |
|---|---|---|
| Step Functions Standard | 24 executions × ~10 transitions ≈ 250 transitions | free tier (4,000 transitions/month); then US$0.025 per 1,000 |
| Step Functions Express | 200 executions, a few ms each | < US$0.01 (US$1.00 per million requests + duration) |
| Lambda | ~50 invocations, arm64, 128 MB | free tier |
| EventBridge | a few hundred custom events, cross-account delivery, 24 replayed | < US$0.01 (US$1.00 per million custom events) |
| Archive | a few KB, 1-day retention | < US$0.01 |
| DynamoDB on-demand | a few hundred writes, a few scans | < US$0.01 |
| SQS | a few hundred messages | free tier |
| **Total** | | **a few cents** |

## Why Cost Explorer showed `-US$0.00` on build day

Cost Explorer isn't a live meter. Billing data is processed in batches and refreshed at least once every 24 hours, so today's usage appears tomorrow ([`26`](screenshots/26-step12-cost-explorer-same-day.png)). The same-day **clean check** ([`25`](screenshots/25-step12-clean-check-both-accounts.png)) proves nothing is left running; the next day's Cost Explorer confirms the final figure.

## At Nkosi's real volume

Assume 5,000 merchants settled nightly and 2 million card transactions a month:

| Component | Monthly volume | Approx. monthly cost |
|---|---|---|
| Settlement saga (Standard) | 150,000 executions × ~10 transitions = 1.5 M transitions | ~US$37 |
| Validation (Express) | 2 M short executions | ~US$2–4 |
| EventBridge | ~2.3 M events | ~US$2.30 |
| Lambda (bank calls) | 150,000 invocations | ~US$0.05 |

The saga is the largest line, and it's the part that buys an auditable, never-half-done settlement. Validation runs 13× more often at a fraction of the cost, which is exactly the Standard vs Express split in [ADR 0004](adr/0004-express-for-high-volume-validation.md). Figures are illustrative list prices, excluding free tier.
