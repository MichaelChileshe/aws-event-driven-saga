{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "StartValidationWorkflowOnly",
      "Effect": "Allow",
      "Action": "states:StartExecution",
      "Resource": "arn:aws:states:@@REGION@@:@@ACCOUNT_ID@@:stateMachine:nkosi-txn-validate"
    },
    {
      "Sid": "DeliverToFinanceBusOnly",
      "Effect": "Allow",
      "Action": "events:PutEvents",
      "Resource": "arn:aws:events:@@REGION@@:@@FIN_ACCOUNT_ID@@:event-bus/nkosi-finance-events"
    }
  ]
}
