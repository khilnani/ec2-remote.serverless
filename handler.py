import sys

# Import local dependencies
sys.path.append('./site-packages')

import os
from pprint import pprint
import traceback
import json

import boto3
from botocore.exceptions import ClientError

def get_instance(client, event):
    """Find an instance's id and status based on the Name tag given to it.
    Assumes the name tag is unique. if not, will pick the first"""

    instance_name = None
    instance_id = None
    instance_state = None
    error_message = None

    # Get the instance name from the path
    try:
        instance_name = event['pathParameters']['name']
        print( 'Instance Name: %s' % instance_name)
    except:
        instance_name = None

    if instance_name:
        r = client.describe_instances(
                Filters=[{'Name':'tag:Name', 'Values': [instance_name]}]
            )
        # AWS' boto3 api involves a lot of looping
        if len(r['Reservations']) > 0:
            for res in r['Reservations']:
                for ins in res['Instances']:
                    ins_id = ins['InstanceId']
                    ins_state = ins['State']['Name']
                    if ins_state in ('shutting-down', 'terminated'):
                        error_message = 'No action taken. Instance %s is %s' % (ins_id, ins_state)
                    else:
                        instance_id = ins_id
                        instance_state = ins_state
                    break
        else:
	    error_message = 'Unable to find instance with tag:Name - %s' % instance_name
    else:
        error_message = 'No instance name specified'

    print(error_message, instance_name, instance_id, instance_state)
    return (error_message, instance_name, instance_id, instance_state)

def ec2_status(event, context):
    """Take an instance tag:name via an API call and return its status"""
    body = {}
    status_code = 200

    try:
        client = boto3.client('ec2')
        # Find the instance
        error, instance_name, instance_id, instance_state = get_instance(client, event)
        if error:
            body["message"] = error
        else:
            body["message"] = str(instance_id) + ' ' + str(instance_state)
    except Exception as e:
        print(traceback.format_exc())
        status_code = 500
        body["message"] = str(e)

    response = {
        "statusCode": status_code,
        "body": json.dumps(body)
    }
    return response

def ec2_start(event, context):
    """Start an instance by its tag:Name via an API call"""
    body = {}
    status_code = 200

    try:
        client = boto3.client('ec2')
        # Find the instance
        error, instance_name, instance_id, instance_state = get_instance(client, event)
        if error:
            body["message"] = error
        else:
            # Start the instance
            r = client.start_instances(InstanceIds=[instance_id])
            if len(r['StartingInstances']) > 0:
                instance_state = r['StartingInstances'][0]['CurrentState']['Name']
                body["message"] = str(instance_id) + ' ' + str(instance_state)
            else:
                status_code = 500
                body["message"] = 'Unable to start: ' + str(instance_id) + ' ' + str(instance_state)
    except Exception as e:
        print(traceback.format_exc())
        status_code = 500
        body["message"] = str(e)

    response = {
        "statusCode": status_code,
        "body": json.dumps(body)
    }
    return response


def ec2_stop(event, context):
    """"Stop an instance by its tag:Name via an API call"""
    body = {}
    status_code = 200

    try:
        # Get the instance name from the path
        client = boto3.client('ec2')
        # Find the instance
        error, instance_name, instance_id, instance_state = get_instance(client, event)
        if error:
            body["message"] = error
        else:
            # Stop the instance
            r = client.stop_instances(InstanceIds=[instance_id])
            if len(r['StoppingInstances']) > 0:
                instance_state = r['StoppingInstances'][0]['CurrentState']['Name']
                body["message"] = str(instance_id) + ' ' + str(instance_state)
            else:
                status_code = 500
                body["message"] = 'Unable to stop: ' + str(instance_id) + ' ' + str(instance_state)
    except Exception as e:
        print(traceback.format_exc())
        status_code = 500
        body["message"] = str(e)

    response = {
        "statusCode": status_code,
        "body": json.dumps(body)
    }

    return response
