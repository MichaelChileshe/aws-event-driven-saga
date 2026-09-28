{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "WriteSettlementLedgerOnly",
      "Effect": "Allow",
      "Action": "dynamodb:PutItem",
      "Resource": "arn:aws:dynamodb:@@REGION@@:@@ACCOUNT_ID@@:table/nkosi-settlement-ledger"
    },
    {
      "Sid": "CallBankGatewayOnly",
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": [
        "arn:aws:lambda:@@REGION@@:@@ACCOUNT_ID@@:function:nkosi-bank-gateway",
        "arn:aws:lambda:@@REGION@@:@@ACCOUNT_ID@@:function:nkosi-bank-gateway:*"
      ]
    },
    {
      "Sid": "PublishToPaymentsBusOnly",
      "Effect": "Allow",
      "Action": "events:PutEvents",
      "Resource": "arn:aws:events:@@REGION@@:@@ACCOUNT_ID@@:event-bus/nkosi-payments"
    }
  ]
}
