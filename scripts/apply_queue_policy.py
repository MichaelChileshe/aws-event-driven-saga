#!/usr/bin/env python3
"""Let exactly one EventBridge rule deliver into an SQS queue.

Usage:  python3 scripts/apply_queue_policy.py <queue-url> <rule-arn> [--profile NAME]
Allow-only: principal events.amazonaws.com, action sqs:SendMessage, condition aws:SourceArn = the rule.
"""
import argparse, json, os
from kit_aws import ROOT, aws, use_profile

p = argparse.ArgumentParser()
p.add_argument("queue_url")
p.add_argument("rule_arn")
p.add_argument("--profile")
a = p.parse_args()
use_profile(a.profile)

queue_arn = aws("sqs", "get-queue-attributes", "--queue-url", a.queue_url,
                "--attribute-names", "QueueArn")["Attributes"]["QueueArn"]
policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "AllowOneEventBridgeRuleOnly",
        "Effect": "Allow",
        "Principal": {"Service": "events.amazonaws.com"},
        "Action": "sqs:SendMessage",
        "Resource": queue_arn,
        "Condition": {"ArnEquals": {"aws:SourceArn": a.rule_arn}},
    }],
}
aws("sqs", "set-queue-attributes", "--queue-url", a.queue_url, "--attributes", json.dumps({"Policy": json.dumps(policy)}))
os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
name = queue_arn.rsplit(":", 1)[-1]
with open(os.path.join(ROOT, "build", f"queue-policy-{name}.json"), "w") as f:
    json.dump(policy, f, indent=2)
print(f"{name}: only {a.rule_arn.split('/')[-1]} may send (copy in build/queue-policy-{name}.json)")
