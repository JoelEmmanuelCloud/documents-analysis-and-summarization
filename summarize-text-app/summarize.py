import json
import boto3
import logging
from prompt import get_system_prompt, get_user_prompt

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Initialize S3 and Bedrock clients
    s3 = boto3.client('s3')
    bedrock_client = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1"
    )

    try:
        # Retrieve file info from the event
        bucket = event['bucket']
        key = event['key']

        # Get the text file from S3
        obj = s3.get_object(Bucket=bucket, Key=key)
        text_content = obj['Body'].read().decode('utf-8')

        # Prepare prompts for Bedrock
        system_prompt = get_system_prompt()
        user_prompt = get_user_prompt()

        full_prompt = f"System: {system_prompt}\n\nHuman: {user_prompt}\n\n{text_content}\n\nAssistant:"

        # Convert full prompt to JSON
        body = json.dumps({
            "prompt": full_prompt,
            "max_tokens_to_sample": 500,
            "temperature": 0.1,
            "top_p": 0.9
        })

        # Invoke Bedrock model
        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-v2',
            body=body,
            contentType='application/json',
            accept='application/json'
        )
        response_body = json.loads(response['body'].read().decode('utf-8'))
        summary = response_body.get('completion', "Summary not generated.")

        # Save the summary back to S3
        summary_key = key.replace('.txt', '_summary.txt')
        s3.put_object(Bucket=bucket, Key=summary_key, Body=summary.encode('utf-8'))

        return {
            'statusCode': 200,
            'body': json.dumps({'Summary': summary})
        }

    except Exception as e:
        logger.error(f"Failed to generate or save summary due to: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error processing summary: {str(e)}")
        }
