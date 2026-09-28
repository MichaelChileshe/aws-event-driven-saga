#!/usr/bin/env python3
"""Read (and remove) the EventBridge events waiting in an SQS queue, and summarise them.

Usage:  python3 scripts/peek_queue.py <queue-url> [--profile NAME]
Shows each event's detail-type, settlement_id, source account and replay-name (if it was replayed).
"""
import argparse, json
from collections import Counter
from kit_aws import aws, use_profile

p = argparse.ArgumentParser()
p.add_argument("queue_url")
p.add_argument("--profile")
a = p.parse_args()
use_profile(a.profile)

seen = []
while True:
    res = aws("sqs", "receive-message", "--queue-url", a.queue_url,
              "--max-number-of-messages", "10", "--wait-time-seconds", "5")
    msgs = res.get("Messages", [])
    if not msgs:
        break
    for m in msgs:
        e = json.loads(m["Body"])
        seen.append((e.get("detail-type"), e.get("detail", {}).get("settlement_id", ""),
                     e.get("account"), e.get("replay-name", "-")))
        aws("sqs", "delete-message", "--queue-url", a.queue_url, "--receipt-handle", m["ReceiptHandle"])

name = a.queue_url.rsplit("/", 1)[-1]
print(f"{name}: {len(seen)} event(s)")
print(f"  {'detail-type':<24}{'settlement_id':<18}{'from account':<15}replay-name")
for dt, sid, acct, rn in sorted(seen, key=lambda x: x[1]):
    print(f"  {dt:<24}{sid:<18}{acct:<15}{rn}")
if seen:
    print("  totals:", ", ".join(f"{k} {v}" for k, v in Counter(s[0] for s in seen).items()))
