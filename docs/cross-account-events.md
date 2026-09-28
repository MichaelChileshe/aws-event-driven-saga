# Cross-account events: telling the finance team

Finance works in its own AWS account (`nkosi-sandbox`). It needs to know about every completed settlement, without reading Nkosi's database and without Nkosi calling finance's systems.

## Each side controls its half

| | Nkosi Payments (sender) | Finance (receiver) |
|---|---|---|
| Bus | `nkosi-payments` | `nkosi-finance-events` |
| Permission | IAM role `nkosi-eventbridge-targets-role`: `events:PutEvents` on the finance bus ARN only | **Bus resource policy**: `events:PutEvents` allowed for Nkosi's account only (`put-permission`) |
| Rule | `nkosi-settlements-to-finance`: `SettlementCompleted`, **not** replays | `finance-settlements-to-inbox` → SQS `nkosi-finance-inbox` |
| Can revoke by | removing the rule or the role | removing the bus permission |

This is the same both-sides rule I proved for S3 and IAM in `aws-cross-account-access-patterns`, applied to events. The receiving side decides **who** may send; the sending side decides **what** is sent.

## What crosses the boundary, and what doesn't

The sending rule's pattern is deliberately narrow:

```json
{
  "source": ["nkosi.settlement"],
  "detail-type": ["SettlementCompleted"],
  "replay-name": [{ "exists": false }]
}
```

- Only completed settlements go to finance. Compensations and the 200 card transactions stay inside Nkosi's account.
- **Replayed events never cross.** When I replayed the archive, the finance inbox received **0** events ([`23`](screenshots/23-step10-live-feed-and-finance-untouched.png)).

## The proof

`S-XACCT-0001` was settled in Nkosi's account. Twenty seconds later, reading the queue **in the finance account** with the `finance-admin` profile showed:

```
nkosi-finance-inbox: 1 event(s)
  SettlementCompleted     S-XACCT-0001      <Nkosi account ID>   -
```

Evidence: [`17`](screenshots/17-step9-finance-account-queue-rule-target.png), [`18`](screenshots/18-step9-cross-account-delivery-proven.png). The "from account" field is Nkosi's management account: the event kept its origin as it crossed.
