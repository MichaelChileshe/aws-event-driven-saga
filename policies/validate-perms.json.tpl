{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "RecordValidationResultsOnly",
      "Effect": "Allow",
      "Action": "dynamodb:PutItem",
      "Resource": "arn:aws:dynamodb:@@REGION@@:@@ACCOUNT_ID@@:table/nkosi-txn-validations"
    }
  ]
}
