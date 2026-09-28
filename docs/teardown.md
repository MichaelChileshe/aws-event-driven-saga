# Teardown: both accounts

There is no `Deny` statement anywhere in this project, so every delete works for the account administrator. Order matters only where AWS enforces it: a rule must lose its targets before it's deleted, and a bus must lose its rules before it's deleted.

## Nkosi account: events

```bash
aws events remove-targets --rule nkosi-txn-received-to-validate --event-bus-name nkosi-payments --ids validate
aws events delete-rule --name nkosi-txn-received-to-validate --event-bus-name nkosi-payments
aws events remove-targets --rule nkosi-settlement-feed --event-bus-name nkosi-payments --ids feed
aws events delete-rule --name nkosi-settlement-feed --event-bus-name nkosi-payments
aws events remove-targets --rule nkosi-replay-inspect --event-bus-name nkosi-payments --ids inspect
aws events delete-rule --name nkosi-replay-inspect --event-bus-name nkosi-payments
aws events remove-targets --rule nkosi-settlements-to-finance --event-bus-name nkosi-payments --ids finance-bus
aws events delete-rule --name nkosi-settlements-to-finance --event-bus-name nkosi-payments
aws events delete-archive --archive-name nkosi-payments-archive
sleep 10
aws events delete-event-bus --name nkosi-payments
```

Deleting the archive also removes its managed rule. Replays have no delete API; they're records, not resources, and cost nothing.

## Finance account

```bash
aws events remove-targets --rule finance-settlements-to-inbox --event-bus-name nkosi-finance-events --ids inbox --profile finance-admin
aws events delete-rule --name finance-settlements-to-inbox --event-bus-name nkosi-finance-events --profile finance-admin
aws events delete-event-bus --name nkosi-finance-events --profile finance-admin
aws sqs delete-queue --queue-url "$FIN_Q_URL" --profile finance-admin
```

Deleting the bus removes its permission for Nkosi's account, closing the cross-account door.

## Nkosi account: workflows, functions, IAM, data

```bash
aws stepfunctions delete-state-machine --state-machine-arn "$SAGA_ARN"
aws stepfunctions delete-state-machine --state-machine-arn "$VALIDATE_ARN"
aws lambda delete-function --function-name nkosi-bank-gateway
aws lambda delete-function --function-name nkosi-settlement-monolith
aws logs delete-log-group --log-group-name /aws/lambda/nkosi-bank-gateway
aws logs delete-log-group --log-group-name /aws/lambda/nkosi-settlement-monolith

aws iam delete-role-policy --role-name nkosi-settlement-saga-role --policy-name saga-permissions
aws iam delete-role --role-name nkosi-settlement-saga-role
aws iam delete-role-policy --role-name nkosi-txn-validate-role --policy-name validate-permissions
aws iam delete-role --role-name nkosi-txn-validate-role
aws iam delete-role-policy --role-name nkosi-eventbridge-targets-role --policy-name eventbridge-targets
aws iam delete-role --role-name nkosi-eventbridge-targets-role
aws iam detach-role-policy --role-name nkosi-bank-gateway-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name nkosi-bank-gateway-role
aws iam detach-role-policy --role-name nkosi-settlement-monolith-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role-policy --role-name nkosi-settlement-monolith-role --policy-name monolith-ledger-write
aws iam delete-role --role-name nkosi-settlement-monolith-role

aws dynamodb delete-table --table-name nkosi-settlement-ledger
aws dynamodb delete-table --table-name nkosi-txn-validations
aws sqs delete-queue --queue-url "$FEED_URL"
aws sqs delete-queue --queue-url "$REPLAY_Q_URL"
```

## Clean check (after 60 s)

```bash
aws events list-event-buses --query "EventBuses[?Name!='default'].Name" --output text
aws events list-event-buses --profile finance-admin --query "EventBuses[?Name!='default'].Name" --output text
aws events list-archives --query 'Archives[].ArchiveName' --output text
aws stepfunctions list-state-machines --query "stateMachines[?starts_with(name,'nkosi-')].name" --output text
aws lambda list-functions --query "Functions[?starts_with(FunctionName,'nkosi-')].FunctionName" --output text
aws iam list-roles --query "Roles[?starts_with(RoleName,'nkosi-settlement') || starts_with(RoleName,'nkosi-bank') || starts_with(RoleName,'nkosi-txn') || starts_with(RoleName,'nkosi-eventbridge')].RoleName" --output text
aws dynamodb list-tables --query "TableNames[?starts_with(@,'nkosi-')]" --output text
aws sqs list-queues --queue-name-prefix nkosi- --query QueueUrls --output text
aws sqs list-queues --queue-name-prefix nkosi- --profile finance-admin --query QueueUrls --output text
```

My result: every query came back empty, both accounts ([`25`](screenshots/25-step12-clean-check-both-accounts.png)).
