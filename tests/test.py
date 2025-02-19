import json
import os
from unittest.mock import patch

from dotenv import load_dotenv
from moto.core import DEFAULT_ACCOUNT_ID
from moto.ses import ses_backends

import main

def set_environment_variables(queue_url, email):
    main.P3_QUEUE = queue_url
    main.AWS_REGION = 'eu-west-2'
    main.ACCESS_KEY = 'testing'
    main.SECRET_ACCESS_KEY = 'testing'
    main.EMAIL = email


def test_process_message(sqs_client, ses_client):
    queue = sqs_client.create_queue(QueueName='queue')

    queue_url = queue['QueueUrl']

    ses_client.verify_email_identity(EmailAddress="test@test.com")

    set_environment_variables(queue_url, 'test@test.com')

    expected_msg = json.dumps({'description': 'Happening right now', 'title': 'Bug'})
    sqs_messages = sqs_client.send_message(QueueUrl=queue_url, MessageBody=expected_msg)

    main.process_message(ses_client)

    send_quota = ses_client.get_send_quota()
    sent_count = int(send_quota["SentLast24Hours"])

    messages = sqs_messages.get('Messages')
    assert sent_count == 1
    assert messages is None

def test_process_message_wrong_data(sqs_client, ses_client):
    queue = sqs_client.create_queue(QueueName='queue')

    queue_url = queue['QueueUrl']

    ses_client.verify_email_identity(EmailAddress="test@test.com")

    set_environment_variables(queue_url, 'test@test.com')

    expected_msg = json.dumps({'description': 'Happening right now'})
    sqs_messages = sqs_client.send_message(QueueUrl=queue_url, MessageBody=expected_msg)

    main.process_message(ses_client)

    send_quota = ses_client.get_send_quota()
    sent_count = int(send_quota["SentLast24Hours"])

    messages = sqs_messages.get('Messages')
    assert sent_count == 0
    assert messages is None