# ADR 0002: Retry transient bank errors; compensate permanent ones

**Status:** Accepted
**Context:** The bank fails in two different ways: it times out (it might answer next time), or it rejects the payout (a closed account will never succeed). The old function treated both as fatal.

## Decision

On the `Payout` state:

- `Retry` on **`BankTimeout`** only: 3 attempts, interval 2 s, backoff rate 2 (waits 2 s, 4 s, 8 s).
- `Retry` on AWS's own transient Lambda errors (`Lambda.ServiceException`, `Lambda.TooManyRequestsException`, and so on) with the same backoff.
- `Catch` on **everything else** (`States.ALL`): record the error at `$.error`, go to compensation.
- The bank function raises distinct exception classes (`BankTimeout`, `PayoutRejected`). Step Functions uses the class name as the error name, which is what makes the split possible.

## Consequences

- All 3 timeout settlements in the batch **completed** instead of becoming partial. The history of `S-DEMO-0002` shows `BankTimeout`, `BankTimeout`, then success on attempt 3.
- All 5 rejections went straight to compensation without wasting retries.
- Retried settlements took ~7.1 s instead of ~0.8 s. That's the backoff, and a useful early-warning signal if the bank degrades.
- Error naming becomes part of the contract with the bank integration: a new transient error type must be added to the `Retry` list deliberately, not caught by accident.
