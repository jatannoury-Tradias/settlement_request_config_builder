import datetime
import time
import boto3

lambda_client = boto3.client('lambda')
event_client = boto3.client('events')
def convert_end_time_to_cron(end_time,frequency,trigger_day):
    # Convert the end_time to a datetime object
    end_time_obj = datetime.datetime.strptime(end_time, '%I:%M:%S %p')

    # Extract hours and minutes from the datetime object
    hours = end_time_obj.hour
    minutes = end_time_obj.minute
    day_of_week = "?" if frequency.casefold() == "daily" else trigger_day[:3].upper()
    day_of_month = "*" if frequency.casefold() != "monthly" else "L"

    # Create the cron expression
    cron_expression = f'cron({minutes} {hours} {day_of_month} * {day_of_week} *)'
def add_lambda_trigger(end_time,frequency,trigger_day):
    rule_name = f'settlement_request_{end_time}'.replace(":","_").replace(" ","_") # Define a var for rule_name
    cron_sec = convert_end_time_to_cron(end_time,frequency,trigger_day) # Define a var for cron
    lambda_fc_name = 'settlement_request_config_reader' # Define a var for lambda name
    lambda_fc_arn = "arn:aws:lambda:eu-central-1:363589960244:function:settlement_request_config_reader"
    add_permission_role_arn = 'arn:aws:iam::431660491089:role/add_permission' # put create role ARN
    # use boto3 create a rule
    create_rule_resp = event_client.put_rule(
            Name=rule_name, # There put your rule name
            ScheduleExpression=cron_sec, # there put your cron
            State='ENABLED', # there set the rule state ENABLED or DISABLED
            EventBusName='default'
    )

    put_target_resp = event_client.put_targets(
            Rule=rule_name,
            Targets=[{
                'Id': lambda_fc_name,
                'Arn': lambda_fc_arn
            }]
        )

    # use if to determine the lambda_fc_arn weather '$' exists
    # if the '$' in lambda_fc_arn,just remove from $

    if '$' in lambda_fc_arn:
        lambda_fc_arn = lambda_fc_arn[:-8]
    add_lambda_permission = lambda_client.add_permission(
            FunctionName=lambda_fc_arn,
            StatementId=str(time.time())[-5:]+lambda_fc_name,
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=create_rule_resp['RuleArn']
        )
