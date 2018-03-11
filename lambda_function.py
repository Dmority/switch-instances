import boto3
import json

def lambda_handler(event, context):
    ssm = boto3.client('ssm')
    
    sw = ssm.get_parameter(Name='prod-switch-stat')['Parameter']['Value']
    switch_stat = json.loads(sw)

    print(switch_stat)
