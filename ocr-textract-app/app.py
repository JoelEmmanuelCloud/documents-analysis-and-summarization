import json
import boto3
import os
import base64
import time

s3 = boto3.client('s3')
textract = boto3.client('textract')

def lambda_handler(event, context):
    try:
        # Get the base64 file content from the event body
        base64_content = event["body"]

        # Fix incorrect padding if necessary
        base64_content += '=' * (-len(base64_content) % 4)

        # Decode base64 file content
        file_content = base64.b64decode(base64_content)
        file_name = "uploaded.pdf"

        # Upload the file to the S3 bucket
        bucket = os.environ['OUTPUT_BUCKET']
        s3.put_object(Bucket=bucket, Key=file_name, Body=file_content)

        # Call Textract to start text detection from the uploaded PDF
        response = textract.start_document_text_detection(
            DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': file_name}}
        )

        # Extract job ID
        job_id = response['JobId']

        # Poll for job completion (This is a simplistic approach)
        status = 'IN_PROGRESS'
        while status == 'IN_PROGRESS':
            time.sleep(5)  # Wait for a few seconds before checking the job status again
            response = textract.get_document_text_detection(JobId=job_id)
            status = response['JobStatus']

        if status == 'SUCCEEDED':
            # Extract the detected text
            text = ''
            for item in response['Blocks']:
                if item['BlockType'] == 'LINE':
                    text += item['Text'] + '\n'

            # Save the extracted text to the S3 bucket
            output_key = file_name.replace('.pdf', '.txt')
            s3.put_object(Bucket=bucket, Key=output_key, Body=text.encode('utf-8'))

            return {
                'statusCode': 200,
                'body': json.dumps('Text extraction completed successfully')
            }
        else:
            failure_reason = response.get('StatusMessage', 'Unknown reason')
            return {
                'statusCode': 500,
                'body': json.dumps(f'Text detection job failed with status: {status}. Reason: {failure_reason}')
            }

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing file: {str(e)}')
        }
