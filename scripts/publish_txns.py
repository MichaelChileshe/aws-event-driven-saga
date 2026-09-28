#!/usr/bin/env python3
"""Publish TransactionReceived events to the nkosi-payments bus, 10 per PutEvents call.

Usage:  python3 scripts/publish_txns.py <RUN> <COUNT> [--invalid-every N]
Every Nth transaction is deliberately invalid, rotating through: wrong currency, zero amount,
bad merchant ID, missing currency. Transaction IDs are T-<RUN>-0001 ...
"""
import argparse, datetime, json, os, tempfile
from kit_aws import aws

p = argparse.ArgumentParser()
p.add_argument("run")
p.add_argument("count", type=int)
p.add_argument("--invalid-every", type=int, default=10)
a = p.parse_args()

KINDS = ["currency", "amount", "merchant", "missing"]
entries, invalid = [], 0
for i in range(1, a.count + 1):
    d = {"txn_id": f"T-{a.run}-{i:04d}", "merchant_id": f"M-{100 + i % 7}",
         "amount_zar": round(50 + (i * 37) % 4000 + 0.99, 2), "currency": "ZAR"}
    if a.invalid_every and i % a.invalid_every == 0:
        kind = KINDS[(i // a.invalid_every) % len(KINDS)]
        invalid += 1
        if kind == "currency":
            d["currency"] = "USD"
        elif kind == "amount":
            d["amount_zar"] = 0
        elif kind == "merchant":
            d["merchant_id"] = "X-999"
        else:
            del d["currency"]
    entries.append({"EventBusName": "nkosi-payments", "Source": "nkosi.acquiring",
                    "DetailType": "TransactionReceived", "Detail": json.dumps(d)})

sent = failed = 0
for start in range(0, len(entries), 10):  # PutEvents takes at most 10 entries
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(entries[start:start + 10], f)
        path = f.name
    res = aws("events", "put-events", "--entries", f"file://{path}")
    os.remove(path)
    failed += res.get("FailedEntryCount", 0)
    sent += len(entries[start:start + 10]) - res.get("FailedEntryCount", 0)

now = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
print(f"{now} UTC  published {sent} TransactionReceived ({a.count - invalid} valid, {invalid} deliberately invalid)  failed: {failed}")
