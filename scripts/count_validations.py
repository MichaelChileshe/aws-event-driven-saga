#!/usr/bin/env python3
"""Count what the Express validation workflow recorded for a run, optionally waiting until all arrive.

Usage:  python3 scripts/count_validations.py <RUN> <EXPECTED> [--wait]
"""
import argparse, json, time
from collections import Counter
from kit_aws import aws

p = argparse.ArgumentParser()
p.add_argument("run")
p.add_argument("expected", type=int)
p.add_argument("--wait", action="store_true")
a = p.parse_args()

start = time.time()
while True:
    res = aws("dynamodb", "scan", "--table-name", "nkosi-txn-validations",
              "--filter-expression", "begins_with(txn_id, :p)",
              "--expression-attribute-values", json.dumps({":p": {"S": f"T-{a.run}-"}}))
    items = res.get("Items", [])
    if not a.wait or len(items) >= a.expected or time.time() - start > 300:
        break
    print(f"  {len(items)}/{a.expected} recorded after {time.time() - start:.0f}s ...")
    time.sleep(5)

status = Counter(i["status"]["S"] for i in items)
reasons = Counter(i["reason"]["S"] for i in items if i["status"]["S"] == "REJECTED")
print(f"run {a.run}: {len(items)}/{a.expected} validated | ACCEPTED {status['ACCEPTED']} | REJECTED {status['REJECTED']}"
      + (f"  (all recorded within {time.time() - start:.0f}s of starting to count)" if a.wait else ""))
for reason, n in sorted(reasons.items()):
    print(f"  rejected {n:>3} x {reason}")
