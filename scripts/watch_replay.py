#!/usr/bin/env python3
"""Poll an EventBridge replay until it finishes and report how long it took.

Usage:  python3 scripts/watch_replay.py <replay-name>
"""
import datetime, sys, time
from kit_aws import aws

name = sys.argv[1]
while True:
    r = aws("events", "describe-replay", "--replay-name", name)
    state = r["State"]
    print(f"  {datetime.datetime.now(datetime.timezone.utc):%H:%M:%S}  {state}")
    if state in ("COMPLETED", "FAILED", "CANCELLED"):
        break
    time.sleep(10)

print(f"\nreplay {name}: {state}" + (f"  reason: {r.get('StateReason')}" if r.get("StateReason") else ""))
print(f"  events from {r.get('EventStartTime')} to {r.get('EventEndTime')}")
s, e = r.get("ReplayStartTime"), r.get("ReplayEndTime")
if s and e:
    try:
        fmt = lambda t: datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
        print(f"  replay ran {s} -> {e}  =  {(fmt(e) - fmt(s)).total_seconds():.0f} seconds")
    except ValueError:
        print(f"  replay ran {s} -> {e}")
