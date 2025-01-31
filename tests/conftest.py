import os

import boto3
import pytest
from dotenv import load_dotenv
from moto import mock_aws

# loading variables from .env file
load_dotenv()
REGION=os.getenv('AWS_REGION')
@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'


@pytest.fixture(scope='function')
def sqs_client(aws_credentials):
    # setup
    with mock_aws():
        yield boto3.client('sqs', region_name=REGION)

@pytest.fixture(scope='function')
def ses_client(aws_credentials):
    # setup
    with mock_aws():
        yield boto3.client('ses', region_name=REGION)

