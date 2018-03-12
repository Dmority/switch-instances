import boto3
import json
import requests
import time
import os

def lambda_handler(event, context):
    # get parameter from parameter store
    ssm = boto3.client('ssm')
    ec2 = boto3.client('ec2')
    sw = ssm.get_parameter(Name=os.environ['parameter_name'])['Parameter']['Value']
    switch_stat = json.loads(sw)
    
    # check http
    fail_count = 0
    for i in range(3):
        try:
            res = requests.get('http://' + switch_stat['instance-info'][switch_stat['master-id']]['instance-ip'] + '/index.html', timeout=5)
            res_code = res.status_code
        except:
            res_code = 900
            
        print(res_code)
        if res_code != 200:
            fail_count += 1 
            print(fail_count)
    
    # check the count of fail
    if fail_count < 3:
        return None

    eni_attr_id = ec2.describe_network_interface_attribute(Attribute='attachment',NetworkInterfaceId=switch_stat['eni-id'])
    
    # detatch eni
    res = ec2.detach_network_interface(AttachmentId=eni_attr_id['Attachment']['AttachmentId'], Force=True)

    # check the status of eni detatched (max 6)
    for i in range(6):
        attach_stat = ec2.describe_network_interfaces(NetworkInterfaceIds=[switch_stat['eni-id']])
        if attach_stat['NetworkInterfaces'][0]['Status'] != 'available':
            print(i)
            time.sleep(10)
    
    # reattach eni 
    res = ec2.attach_network_interface(DeviceIndex=1, InstanceId=switch_stat['instance-info'][switch_stat['slave-id']]['instance-id'], NetworkInterfaceId=switch_stat['eni-id'])

    # update parameter store
    bf_master_id = switch_stat['master-id']
    bf_slave_id = switch_stat['slave-id']
    switch_stat['master-id'] = bf_slave_id
    switch_stat['slave-id'] = bf_master_id
    res = ssm.put_parameter(Name=os.environ['parameter_name'], Value=json.dumps(switch_stat), Type='String', Overwrite=True)

