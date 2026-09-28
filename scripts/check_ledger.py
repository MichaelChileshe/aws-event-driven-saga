#!/usr/bin/env python3
"""THE measurement: is every settlement in a run either fully done or fully undone?

Usage:  python3 scripts/check_ledger.py <RUN>

  COMPLETE     RESERVE + LEDGER_CREDIT + PAYOUT all present
  COMPENSATED  no PAYOUT, and every forward step has its reversal
               (RESERVE -> RESERVE_RELEASED, LEDGER_CREDIT -> LEDGER_REVERSED)
  PARTIAL      anything else: money reserved or credited with no payout and no reversal
"""
import json, sys
from collections import defaultdict
from kit_aws import aws

run = sys.argv[1]
res = aws("dynamodb", "scan", "--table-name", "nkosi-settlement-ledger",
          "--filter-expression", "begins_with(settlement_id, :p)",
          "--expression-attribute-values", json.dumps({":p": {"S": f"S-{run}-"}}))
entries, amount = defaultdict(set), {}
for item in res.get("Items", []):
    sid = item["settlement_id"]["S"]
    entries[sid].add(item["entry"]["S"])
    amount[sid] = float(item["amount_zar"]["S"])

complete, compensated, partial = [], [], []
for sid, e in sorted(entries.items()):
    if {"RESERVE", "LEDGER_CREDIT", "PAYOUT"} <= e:
        complete.append(sid)
    elif "PAYOUT" not in e and ("RESERVE" not in e or "RESERVE_RELEASED" in e) \
            and ("LEDGER_CREDIT" not in e or "LEDGER_REVERSED" in e):
        compensated.append(sid)
    else:
        partial.append(sid)

stranded = sum(amount[s] for s in partial)
print(f"run {run}: {len(entries)} settlements | COMPLETE {len(complete)} | COMPENSATED {len(compensated)} "
      f"| PARTIAL {len(partial)} | money stranded R{stranded:,.2f}")
for sid in partial:
    print(f"  PARTIAL {sid}: {', '.join(sorted(entries[sid]))}")
