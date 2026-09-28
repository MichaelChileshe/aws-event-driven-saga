# ADR 0005: Announce results on a custom EventBridge bus and deliver across accounts

**Status:** Accepted
**Context:** Finance needs to know about every completed settlement. Finance works in a separate AWS account and must not read Nkosi's ledger directly.

## Options considered

| Option | Verdict |
|---|---|
| Give finance read access to the ledger table | ❌ Couples finance to Nkosi's schema; every table change becomes a cross-team negotiation |
| SNS topic with a cross-account subscription | ⚠️ Works, but no content-based routing on the event body, and no archive/replay |
| **EventBridge custom bus + cross-account bus delivery** | ✅ Chosen |

## Decision

- The saga publishes `SettlementCompleted` / `SettlementCompensated` (`source: nkosi.settlement`) to the custom bus `nkosi-payments`.
- **Finance side:** bus `nkosi-finance-events` with a resource policy allowing Nkosi's account to `PutEvents`, and their own rule → SQS inbox.
- **Nkosi side:** rule `nkosi-settlements-to-finance` (`SettlementCompleted`, not replays) → the finance bus, using a role allowed `events:PutEvents` on that bus ARN only.

## Consequences

- `S-XACCT-0001` arrived in the finance account's queue, "from" Nkosi's account.
- Each side can revoke its half independently: finance removes the bus permission, or Nkosi removes the rule or role.
- Only completed settlements cross the boundary; compensations and card transactions stay internal.
- Consumers depend on the **event schema**, not the table schema. Event contracts need versioning discipline (a `version` field in `detail`) as more consumers join.
