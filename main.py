import json
import logging
import os
import string
import threading

import boto3
from botocore.exceptions import ClientError
from flask import Flask
from dotenv import load_dotenv

app = Flask(__name__)

# loading variables from .env file
load_dotenv()
AWS_REGION = os.getenv('AWS_REGION')
P3_QUEUE = os.getenv('P3_QUEUE')
ACCESS_KEY = os.getenv('ACCESS_KEY')
SECRET_ACCESS_KEY = os.getenv('SECRET_ACCESS_KEY')
EMAIL = os.getenv('EMAIL')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Make aws clients
ses = boto3.client(
    'ses',
    region_name=AWS_REGION,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_ACCESS_KEY
)

def process_message():
    sqs = boto3.client('sqs', region_name=AWS_REGION, aws_access_key_id=ACCESS_KEY,
                       aws_secret_access_key=SECRET_ACCESS_KEY)

    #Messagehandling
    response = sqs.receive_message(QueueUrl=P3_QUEUE, MessageAttributeNames=['All'],
                                   MaxNumberOfMessages=1, WaitTimeSeconds=20)

    logger.info("Message received from queue with ID" + json.dumps(response.get('MessageId')))

    messages = response.get('Messages')
    if messages is not None:
        message = messages[0]
        body = json.loads(message['Body'])

        if "title" in body and "description" in body:
            if body["title"] and body["description"]:
                #Try sending email
                try:
                    logger.info("Sending SES email")
                    response = ses.send_email(
                        Destination={
                            'ToAddresses': [
                                EMAIL,
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
                        Source=EMAIL
                    )
                    logger.info("SES email sent with body:" + json.dumps({
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
                        }))

                #Catch error
                except ClientError as e:
                    logger.error(e.response)
            else:
                logger.error("Either the title or description or both are empty")
        else:
            logger.error("Either the title or description or both are missing from the SQS message")

        #Delete message from sqs queue
        sqs.delete_message(
            QueueUrl=P3_QUEUE,
            ReceiptHandle=message['ReceiptHandle']
        )
        logger.info("Message deleted from queue with ID" + json.dumps(response.get('MessageId')))
    else:
        logger.info("No messages in queue")

if __name__ == '__main__':
    threading.Thread(target=process_message, daemon=True).start()
    app.run()

#Helth check for api
@app.route('/health', methods=['GET'])
def health_check():
    return 'OK', 200