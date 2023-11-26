import json
import boto3
from config.s3_config import bucket_name, config_file_name
from helpers.add_lambda_trigger import add_lambda_trigger

s3 = boto3.client("s3")


def lambda_handler(event, context):
    try:
        if "queryStringParameters" in event and "environment" in event['queryStringParameters']:
            raw_response = s3.get_object(Bucket=bucket_name, Key=f"settlement_client_config/{event['queryStringParameters']['environment'].upper()}/settlement_client_config.json")
            polished_response = raw_response['Body'].read()
            json_response = json.loads(polished_response)
        else:
            return {
                "statusCode":400,
                "message":"Environment not specified"
            }
        if "queryStringParameters" in event and "delete_config" in event['queryStringParameters'] and "client_id" in event['queryStringParameters']:
            client_id = event['queryStringParameters']['client_id']
            if client_id not in json_response:
                return {
                'statusCode': 400,
                'body': "Client not configured"
                }
    
            json_response[event['queryStringParameters']['client_id']]['is_deleted'] = True
            updated_json_str = json.dumps(json_response)
        else:
            event['body'] = json.loads(event['body'])
            # Update the client_id field with the value from the Lambda event body
            print(event['body']['client_id'],"<================")
            if event['body']['client_id'] in json_response and "automated_srs" in json_response[event['body']['client_id']]:
                automated_srs = json_response[event['body']['client_id']]['automated_srs']
                json_response[event['body']['client_id']] = event['body']
                json_response[event['body']['client_id']]['automated_srs'] = automated_srs
                add_lambda_trigger(end_time=event['body']['end_time'],frequency=event['body']['frequency'],trigger_day=event['body']['day_limit'])
            else:
                json_response[event['body']['client_id']] = event['body']
            print(json_response)
            updated_json_str = json.dumps(json_response)
            
        # Push the modified JSON back to S3
        s3.put_object(Bucket=bucket_name, Key=f"settlement_client_config/{event['queryStringParameters']['environment'].upper()}/settlement_client_config.json", Body=updated_json_str)
        
        return {
            'statusCode': 200,
            'body': json.dumps('JSON updated and pushed to S3 successfully!')
        }
        
    except Exception as e:
        return {
            "statusCode":500,
            "message":f"{e}"
        }