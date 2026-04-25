#!/bin/bash
echo "Initializing LocalStack SQS queue: ${AWS_SQS_QUEUE_NAME}"

if [[ "$AWS_SQS_QUEUE_NAME" == *.fifo ]]; then
    awslocal sqs create-queue \
        --queue-name "${AWS_SQS_QUEUE_NAME}" \
        --attributes FifoQueue=true,ContentBasedDeduplication=true
else
    awslocal sqs create-queue \
        --queue-name "${AWS_SQS_QUEUE_NAME}"
fi

echo "LocalStack SQS Queue created successfully."
