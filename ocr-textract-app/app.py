import json
import boto3
import os
import base64
import time
import logging

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
textract = boto3.client('textract')
lambda_client = boto3.client('lambda')

def upload_to_s3(file_content, bucket, file_name):
    try:
        s3.put_object(Bucket=bucket, Key=file_name, Body=file_content)
        logger.info(f"File {file_name} uploaded successfully to {bucket}.")
    except Exception as e:
        logger.error(f"Failed to upload file to S3: {str(e)}")
        raise

def start_textract_job(bucket, file_name):
    try:
        response = textract.start_document_text_detection(
            DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': file_name}}
        )
        return response['JobId']
    except Exception as e:
        logger.error(f"Failed to start Textract job: {str(e)}")
        raise

def get_textract_results(job_id):
    status = 'IN_PROGRESS'
    while status == 'IN_PROGRESS':
        time.sleep(5)
        response = textract.get_document_text_detection(JobId=job_id)
        status = response['JobStatus']
    return response

def invoke_summarization_function(bucket, output_key):
    try:
        response = lambda_client.invoke(
            FunctionName='ocr-textract-app-SummarizeFunction-hZbVIwFibrCc',
            InvocationType='RequestResponse',
            Payload=json.dumps({'bucket': bucket, 'key': output_key})
        )
        summary_response = json.load(response['Payload'])
        logger.info("Summarization function returned summary successfully.")
        return summary_response
    except Exception as e:
        logger.error(f"Failed to invoke summarization function: {str(e)}")
        raise

def get_summary_from_s3(bucket, summary_key):
    try:
        summary_obj = s3.get_object(Bucket=bucket, Key=summary_key)
        summary_content = summary_obj['Body'].read().decode('utf-8')
        logger.info(f"Summary retrieved successfully from {summary_key}.")
        return summary_content
    except Exception as e:
        logger.error(f"Failed to retrieve summary from S3: {str(e)}")
        raise

def lambda_handler(event, context):
    try:
        base64_content = event["body"]
        base64_content += '=' * (-len(base64_content) % 4)
        file_content = base64.b64decode(base64_content)
        file_name = "uploaded.pdf"
        bucket = os.environ['OUTPUT_BUCKET']

        upload_to_s3(file_content, bucket, file_name)
        job_id = start_textract_job(bucket, file_name)
        response = get_textract_results(job_id)

        if response['JobStatus'] == 'SUCCEEDED':
            text = ''.join(item['Text'] + '\n' for item in response['Blocks'] if item['BlockType'] == 'LINE')
            output_key = file_name.replace('.pdf', '.txt')
            s3.put_object(Bucket=bucket, Key=output_key, Body=text.encode('utf-8'))
            invoke_summarization_function(bucket, output_key)

            # Get the summary from the uploaded_summary.txt file
            summary_key = 'uploaded_summary.txt'
            summary_content = get_summary_from_s3(bucket, summary_key)

            # Extract JSON part from summary content
            json_start_index = summary_content.find('{')
            json_end_index = summary_content.rfind('}') + 1

            if json_start_index == -1 or json_end_index == -1:
                raise ValueError("JSON content not found in the summary file.")

            summary_json_content = summary_content[json_start_index:json_end_index]

            # Parse the extracted JSON content
            summary_json = json.loads(summary_json_content)

            return {
                'statusCode': 200,
                'body': json.dumps(summary_json, indent=2),
                'headers': {
                    'Content-Type': 'application/json'
                }
            }
        else:
            logger.error(f"Textract job failed with status: {response['JobStatus']}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': f"Text detection job failed with status: {response['JobStatus']}."
                }),
                'headers': {
                    'Content-Type': 'application/json'
                }
            }

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"Error processing file: {str(e)}"
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
