"""Simulated bank payout API used by the settlement saga.

scenario "ok"          -> pays out, returns a bank reference
scenario "transient"   -> times out on the first two attempts, succeeds on the third
                          (Step Functions passes its own retry counter in as retry_count)
scenario "payout_fail" -> permanent rejection: the beneficiary account is closed
"""


class BankTimeout(Exception):
    """Transient: the bank did not answer in time. Safe to retry."""


class PayoutRejected(Exception):
    """Permanent: retrying will never succeed. The saga must compensate."""


def handler(event, context):
    settlement_id = event["settlement_id"]
    scenario = event.get("scenario", "ok")
    attempt = int(event.get("retry_count", 0)) + 1

    if scenario == "transient" and attempt < 3:
        raise BankTimeout(f"bank did not answer for {settlement_id} (attempt {attempt})")
    if scenario == "payout_fail":
        raise PayoutRejected(f"beneficiary account closed for {settlement_id}")

    return {"bank_ref": f"BNK-{settlement_id}-A{attempt}", "attempt": attempt}
