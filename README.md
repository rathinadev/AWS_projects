
# Automating Customer Emails with AWS Lambda, S3, and SES

This project automates the process of sending personalized customer emails using AWS services. When a new S3 event occurs, an AWS Lambda function is triggered to read configuration and template files from S3, process customer data from a CSV file, and send emails via AWS SES.

## Overview

The Lambda function performs the following tasks:
- **Reads a JSON configuration file** from S3 that includes:
  - The S3 path to a text file (email template).
  - The S3 path to a CSV file containing customer details.
  - Other key values like the email subject.
- **Fetches the email template** (a plain text file) and replaces placeholder keys with actual values from the JSON.
- **Parses the CSV file** to retrieve customer names and email addresses.
- **Sends personalized emails** to each customer using AWS SES.
- **Handles errors gracefully** and logs success or failure for each email sent.

For a step-by-step explanation of the approach, see the detailed [Medium article](https://medium.com/@rathina2024/automating-customer-emails-with-aws-a-step-by-step-guide-b549dc50ebb8) citeturn0file0.

## Architecture

- **AWS S3:** Hosts the JSON configuration file, the email template (text file), and the customer CSV file.
- **AWS Lambda:** Contains the Python code that reads the S3 files, processes the template, and sends emails.
- **AWS SES:** Sends out the emails using the SES API.
- **IAM Permissions:** Ensure that the Lambda function has sufficient permissions to access S3 objects and send emails via SES.

## Prerequisites

- An active AWS account.
- An S3 bucket with:
  - A JSON configuration file containing keys such as `"path_to_text_file"`, `"path_to_customer_file"`, and `"subject"`.
  - A text file template with placeholders (e.g., `"customer_name"`).
  - A CSV file with customer records (columns: customer name, email, etc.).
- AWS SES setup with a verified sender email.
- An AWS Lambda function with an IAM role that allows:
  - Reading objects from S3.
  - Sending emails using SES.
- Python 3.8+ with the `boto3` and `csv` libraries.

## Setup & Configuration

1. **S3 Bucket Setup:**
   - Create an S3 bucket.
   - Upload the JSON configuration file, email template text file, and the customer CSV file.

2. **AWS SES Setup:**
   - Verify the sender email address.
   - (Optional) Verify recipient emails if your account is in the SES sandbox.

3. **Lambda Function:**
   - Create a new Lambda function using Python 3.8+.
   - Upload the following code as your function (or include it in your deployment package):

     ```python
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

             # Read JSON configuration file
             json_content = read_s3_json_file(bucket, key)
             original_text = read_s3_file(bucket, json_content["path_to_text_file"])

             # Replace placeholders in the original text template
             for key1, value in json_content.items():
                 original_text = original_text.replace(key1, value)

             # Read the CSV file containing customer data
             response = s3client.get_object(Bucket=bucket, Key=json_content["path_to_customer_file"])
             data = response['Body'].read().decode('utf-8')
             reader = csv.reader(io.StringIO(data))
             next(reader)  # Skip header row

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
     ```

4. **Environment Variables:**
   - Set the environment variable `SES_SOURCE_EMAIL` to your verified sender email address.
   - (Optional) Configure additional environment variables if needed.

5. **Trigger Setup:**
   - Configure your S3 bucket to trigger the Lambda function upon object creation (e.g., when the JSON configuration file is uploaded).

## How It Works

1. **Trigger:**  
   An S3 event triggers the Lambda function when a new JSON file (configuration) is uploaded.

2. **Configuration Parsing:**  
   The function reads the JSON file to determine:
   - The path to the email template (text file).
   - The path to the customer CSV file.
   - Other key-value pairs such as the email subject.

3. **Template Processing:**  
   The text template is read and placeholders are replaced using values from the JSON configuration.

4. **CSV Processing:**  
   The CSV file is read to extract customer names and email addresses.

5. **Email Sending:**  
   For each customer record, the function customizes the email content and uses AWS SES to send the email.

6. **Logging:**  
   Success and error messages are logged to CloudWatch for troubleshooting.

## Testing & Deployment

- **Testing:**  
  Use a test event in the AWS Lambda console that mimics an S3 trigger event. Verify that the Lambda function reads the files correctly and that emails are sent as expected.

- **Deployment:**  
  Deploy the Lambda function via the AWS Management Console or CLI. Ensure your deployment package includes all necessary dependencies.

## Further Reading

- Detailed step-by-step guide and additional context is available on [Medium](https://medium.com/@rathina2024/automating-customer-emails-with-aws-a-step-by-step-guide-b549dc50ebb8) .
- For more on AWS SES and Lambda integration, check out the [AWS SES documentation](https://docs.aws.amazon.com/ses/latest/dg/send-email.html).
