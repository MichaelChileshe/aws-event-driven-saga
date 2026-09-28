"""The 'before': Nkosi's original settlement run - one function, no compensation.

It reserves funds and credits the merchant ledger, THEN calls the bank. If the bank call
fails, the function dies and the first two writes stay behind: a partial settlement.
"""
import datetime
import os

import boto3

ddb = boto3.client("dynamodb")
TABLE = os.environ["TABLE"]


class BankTimeout(Exception):
    pass


class PayoutRejected(Exception):
    pass


def put(settlement_id, entry, event, **extra):
    item = {
        "settlement_id": {"S": settlement_id},
        "entry": {"S": entry},
        "merchant_id": {"S": event["merchant_id"]},
        "amount_zar": {"S": event["amount_zar"]},
        "at": {"S": datetime.datetime.now(datetime.timezone.utc).isoformat()},
    }
    for key, value in extra.items():
        item[key] = {"S": value}
    ddb.put_item(TableName=TABLE, Item=item)


def handler(event, context):
    sid = event["settlement_id"]
    scenario = event.get("scenario", "ok")

    put(sid, "RESERVE", event)
    put(sid, "LEDGER_CREDIT", event)

    # the bank call: no retry, no compensation
    if scenario == "transient":
        raise BankTimeout(f"bank did not answer for {sid}")
    if scenario == "payout_fail":
        raise PayoutRejected(f"beneficiary account closed for {sid}")

    put(sid, "PAYOUT", event, bank_ref=f"BNK-{sid}-A1")
    put(sid, "STATUS", event, status="COMPLETED")
    return {"settlement_id": sid, "status": "COMPLETED"}
