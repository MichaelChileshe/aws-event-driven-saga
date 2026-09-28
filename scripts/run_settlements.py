#!/usr/bin/env python3
"""Run a batch of merchant settlements through either design and wait for the results.

Usage:
  python3 scripts/run_settlements.py <RUN> <COUNT> --mode monolith     the old single Lambda
  python3 scripts/run_settlements.py <RUN> <COUNT> --mode saga         the Step Functions saga

Every batch uses the SAME failure pattern, so the two designs are compared like for like:
  every 4th settlement  -> scenario payout_fail  (bank rejects: permanent)
  every 5th settlement  -> scenario transient    (bank times out twice, then answers)
  everything else       -> scenario ok
Settlement IDs are S-<RUN>-0001 ... and the saga uses them as execution names.
"""
import argparse, json, os, tempfile, time
from kit_aws import aws, env

p = argparse.ArgumentParser()
p.add_argument("run")
p.add_argument("count", type=int)
p.add_argument("--mode", choices=["monolith", "saga"], required=True)
a = p.parse_args()


def scenario(i):
    if i % 4 == 0:
        return "payout_fail"
    if i % 5 == 0:
        return "transient"
    return "ok"


def settlement(i):
    return {"settlement_id": f"S-{a.run}-{i:04d}", "merchant_id": f"M-{100 + i % 7}",
            "amount_zar": f"{(i * 1379) % 20000 + 1500:.2f}", "scenario": scenario(i)}


batch = [settlement(i) for i in range(1, a.count + 1)]
plan = {s: sum(1 for b in batch if b["scenario"] == s) for s in ("ok", "transient", "payout_fail")}
print(f"{a.run}: {a.count} settlements via {a.mode}  (ok {plan['ok']}, transient {plan['transient']}, payout_fail {plan['payout_fail']})")
start = time.time()

if a.mode == "monolith":
    ok = failed = 0
    for s in batch:
        out = os.path.join(tempfile.gettempdir(), "monolith-out.json")
        res = aws("lambda", "invoke", "--function-name", "nkosi-settlement-monolith",
                  "--cli-binary-format", "raw-in-base64-out", "--payload", json.dumps(s), out)
        if res.get("FunctionError"):
            failed += 1
            print(f"  {s['settlement_id']}  {s['scenario']:<12} FAILED  ({json.load(open(out)).get('errorType')})")
        else:
            ok += 1
    print(f"\nmonolith finished in {time.time() - start:.0f}s: {ok} completed, {failed} crashed mid-run")
else:
    sm = env("SAGA_ARN")
    arns = {}
    for s in batch:
        res = aws("stepfunctions", "start-execution", "--state-machine-arn", sm,
                  "--name", s["settlement_id"], "--input", json.dumps(s))
        arns[s["settlement_id"]] = res["executionArn"]
    print(f"  started {len(arns)} executions, waiting for them to finish ...")
    results = {}
    while len(results) < len(arns):
        time.sleep(5)
        for sid, arn in arns.items():
            if sid in results:
                continue
            d = aws("stepfunctions", "describe-execution", "--execution-arn", arn)
            if d["status"] != "RUNNING":
                results[sid] = (d["status"], d.get("error", ""))
    succeeded = sum(1 for st, _ in results.values() if st == "SUCCEEDED")
    compensated = sum(1 for st, err in results.values() if err == "SettlementCompensated")
    other = len(results) - succeeded - compensated
    for sid in sorted(results):
        st, err = results[sid]
        if st != "SUCCEEDED":
            print(f"  {sid}  {st}  {err}")
    print(f"\nsaga finished in {time.time() - start:.0f}s: {succeeded} succeeded, "
          f"{compensated} failed-and-compensated, {other} other")
