import json
import os
from loguru import logger
import threading

import boto3
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

# Make aws clients
ses = boto3.client(
    'ses',
    region_name=AWS_REGION,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_ACCESS_KEY
)

def process_message():
    try:
        sqs = boto3.client('sqs', region_name=AWS_REGION, aws_access_key_id=ACCESS_KEY,
                           aws_secret_access_key=SECRET_ACCESS_KEY)

        #Receive message
        response = sqs.receive_message(QueueUrl=P3_QUEUE, MessageAttributeNames=['All'],
                                       MaxNumberOfMessages=1, WaitTimeSeconds=20)

        messages = response.get('Messages')

        #If there are messages in queue
        if messages is not None:
            #Get the first message
            message = messages[0]
            logger.info(f"Message received from queue with ID: {message["MessageId"]}")

            #Get the body
            body = json.loads(message['Body'])

            #Validate body
            if "title" in body and "description" in body:
                if body["title"] and body["description"]:
                    #Try sending email
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
                    logger.info(f"SES email sent with body: {json.dumps({
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
                        })}")

                #Display errors for bad message body
                else:
                    logger.error("Either the title or description or both are empty")
            else:
                logger.error("Either the title or description or both are missing from the SQS message")

            #Delete message from sqs queue
            sqs.delete_message(
                QueueUrl=P3_QUEUE,
                ReceiptHandle=message['ReceiptHandle']
            )
            logger.info(f"Message deleted from queue with ID: {message["MessageId"]}")
        #If no messages in queue then display that
        else:
            logger.info("No messages in queue")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

def background_thread():
    thread = threading.Thread(target=process_message, daemon=True)
    thread.start()
    return thread

bg_thread = background_thread()

if __name__ == '__main__':
    try:
        app.run(host="0.0.0.0")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        stop_flag = True
        bg_thread.join()

#Helth check for api
@app.route('/', methods=['GET'])
def health_check():
    return 'OK', 200