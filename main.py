import json
import os

import boto3
from botocore.exceptions import ClientError
from flask import Flask
from dotenv import load_dotenv

app = Flask(__name__)

def process_message():
    # loading variables from .env file
    load_dotenv()
    ses = boto3.client('ses', region_name=os.getenv('AWS_REGION'), aws_access_key_id=os.getenv('ACCESS_KEY'),
                       aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'))

    sqs = boto3.client('sqs', region_name=os.getenv('AWS_REGION'), aws_access_key_id=os.getenv('ACCESS_KEY'),
                       aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'))

    response = sqs.receive_message(QueueUrl=os.getenv('P1_QUEUE'), MessageAttributeNames=['All'],
                                   MaxNumberOfMessages=1, WaitTimeSeconds=20)

    messages = response.get('Messages')
    if messages is not None:
        message = messages[0]
        body = json.loads(message['Body'])
        print(body)

        try:
            response = ses.send_email(
                Destination={
                    'ToAddresses': [
                        os.getenv('RECIPIENT_EMAIL'),
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': "UTF-8",
                            'Data': body["description"],
                        }
                    },
                    'Subject': {
                        'Charset': "UTF-8",
                        'Data': body["title"],
                    },
                },
                Source=os.getenv('RECIPIENT_EMAIL')
            )

        except ClientError as e:
            print(e.response.text)

        sqs.delete_message(
            QueueUrl=os.getenv('P1_QUEUE'),
            ReceiptHandle=message['ReceiptHandle']
        )

if __name__ == '__main__':
    process_message()
    app.run()

@app.route('/health', methods=['GET'])
def health_check():
    return 'Service is all good', 200