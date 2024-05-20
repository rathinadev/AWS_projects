import json
import boto3
import csv
import io
import os

s3client = boto3.client('s3')
ses_client = boto3.client('ses', region_name='ap-south-1')

def read_s3_file(bucket_name, file_path):
    obj = s3client.get_object(Bucket=bucket_name, Key=file_path)
    text = obj['Body'].read().decode('utf-8')
    return text

def read_s3_json_file(bucket_name, file_path):
    obj = s3client.get_object(Bucket=bucket_name, Key=file_path)
    json_content = json.loads(obj['Body'].read().decode('utf-8'))
    return json_content

def lambda_handler(event, context):
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        # Read JSON content
        json_content = read_s3_json_file(bucket, key)
        original_text = read_s3_file(bucket, json_content["path_to_text_file"])

        # Replace placeholders in the original text
        for key1, value in json_content.items():
            original_text = original_text.replace(key1, value)

        # Read the CSV file
        response = s3client.get_object(Bucket=bucket, Key=json_content["path_to_customer_file"])
        data = response['Body'].read().decode('utf-8')
        reader = csv.reader(io.StringIO(data))
        next(reader)  # Skip the header

        for row in reader:
            customer_name = row[0]
            email = row[1]
            text = original_text.replace("customer_name", customer_name)

            try:
                response = ses_client.send_email(
                    Source=os.environ['SES_SOURCE_EMAIL'],
                    Destination={
                        'ToAddresses': [email]
                    },
                    Message={
                        'Subject': {
                            'Data': json_content["subject"],
                            'Charset': 'UTF-8'
                        },
                        'Body': {
                            'Text': {
                                'Data': text,
                                'Charset': 'UTF-8'
                            }
                        }
                    }
                )
                print(f"Email sent to {email}")
            except Exception as e:
                print(f"Error sending email to {email}: {str(e)}")

    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")

