import sys

# Import local dependencies
sys.path.append('./site-packages')

import os
from pprint import pprint
import traceback
import json

import boto3
from botocore.exceptions import ClientError


ALL_INSTANCES_NAME = "@all"


def get_filter_tag():
    tag = os.environ['EC2_FILTER_TAG']
    return tag

def get_monitor_tag():
    tag = os.environ['EC2_MONITOR_TAG']
    return tag

def get_monitor_email():
    email = os.environ['EC2_EMAIL']
    return email

def get_monitor_email_prefix():
    prefix = os.environ['EC2_EMAIL_PREFIX']
    return prefix

def send_email(client, email, subject, body):
    response = client.send_email(
        Destination={
            'ToAddresses': [
                email,
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': 'UTF-8',
                    'Data': body,
                },
                'Text': {
                    'Charset': 'UTF-8',
                    'Data': body,
                },
            },
            'Subject': {
                'Charset': 'UTF-8',
                'Data': subject,
            },
        },
        ReplyToAddresses=[
        ],
        Source=email,
    )
    return response

def get_monitor_instances(client, event):
    """Return a list of instances based on the monitor tag in serverles.yml"""

    instance_names = []
    error_message = None
    filter_tag = get_monitor_tag()

    r = client.describe_instances(
            Filters=[
                {'Name':'tag-key', 'Values':[filter_tag]}
                ]
        )
    # AWS' boto3 api involves a lot of looping
    if len(r['Reservations']) > 0:
        for res in r['Reservations']:
            for ins in res['Instances']:
                ins_id = ins['InstanceId']
                ins_state = ins['State']['Name']
                if ins_state == "running":
                    tags = ins['Tags']
                    for tag in tags:
                        if tag['Key'] == "Name":
                            instance_names.append( tag['Value'] )
    else:
        error_message = 'Unable to find instances'

    print(error_message, instance_names)
    return (error_message, instance_names)


def is_get_all_instances(event):
    """Check if the request is to apply the action to all
    '@all' is the reserved instance name"""

    instance_name = None

    # Get the instance name from the path
    try:
        instance_name = event['pathParameters']['name']
        print( 'Instance Name: %s' % instance_name)
    except:
        instance_name = None

    return (instance_name == ALL_INSTANCES_NAME)



def get_instances(client, event):
    """Return a list of instances based on the filter tag in serverless.yml"""

    instance_names = []
    error_message = None
    filter_tag = get_filter_tag()

    r = client.describe_instances(
            Filters=[
                {'Name':'tag-key', 'Values':[filter_tag]}
                ]
        )
    # AWS' boto3 api involves a lot of looping
    if len(r['Reservations']) > 0:
        for res in r['Reservations']:
            for ins in res['Instances']:
                ins_id = ins['InstanceId']
                tags = ins['Tags']
                for tag in tags:
                    if tag['Key'] == "Name":
                        instance_names.append( tag['Value'] )
    else:
        error_message = 'Unable to find instances'

    print(error_message, instance_names)
    return (error_message, instance_names)



def get_instances_status(client, event):
    """Return a list of instances' status based on the filter tag in serverles.yml"""

    instances = []
    error_message = None
    filter_tag = get_filter_tag()

    r = client.describe_instances(
            Filters=[
                {'Name':'tag-key', 'Values':[filter_tag]}
                ]
        )
    # AWS' boto3 api involves a lot of looping
    if len(r['Reservations']) > 0:
        for res in r['Reservations']:
            for ins in res['Instances']:
                ins_id = ins['InstanceId']
                ins_state = ins['State']['Name']
                tags = ins['Tags']
                for tag in tags:
                    if tag['Key'] == "Name":
                        instances.append({ 
                                'name': tag['Value'],
                                'id': ins_id,
                                'state': ins_state
                            })
    else:
        error_message = 'Unable to find instances'

    print(error_message, instances)
    return (error_message, instances)



def get_instance(client, event):
    """Find an instance's id and status based on the Name tag given to it.
    Assumes the name tag is unique. if not, will pick the first"""

    instance_name = None
    instance = None
    error_message = None
    filter_tag = get_filter_tag()

    # Get the instance name from the path
    try:
        instance_name = event['pathParameters']['name']
        print( 'Instance Name: %s' % instance_name)
    except:
        instance_name = None

    if instance_name:
        r = client.describe_instances(
                Filters=[
                    {'Name':'tag:Name', 'Values': [instance_name]},
                    {'Name':'tag-key', 'Values':[filter_tag]}
                    ]
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
                        instance = { 
                                'name': instance_name,
                                'id': ins_id,
                                'state': ins_state
                            }
                    break
        else:
            error_message = 'Unable to find instance with tag:Name - %s' % instance_name
    else:
        error_message = 'No instance name specified'

    print(error_message, instance)
    return (error_message, instance)


def ec2_monitor(event, context):
    """Send an email with list of running instances"""
    body = {}
    status_code = 200

    try:
        client = boto3.client('ec2')
        # Find the instances
        error, instance_names = get_monitor_instances(client, event)

        prefix = get_monitor_email_prefix()
        message = prefix + " Running ec2 instances: %s" % (", ".join(instance_names))
        print(message)

        if error:
            body["error"] = error
        else:
            if len(instance_names) > 0:
                email = get_monitor_email()
                eclient = boto3.client('ses')
                response = send_email(eclient, email, message, message)
                body["message"] = response
            else:
                body["message"] = message

    except Exception as e:
        print(traceback.format_exc())
        status_code = 500
        body["error"] = str(e)

    response = {
        "statusCode": status_code,
        "body": json.dumps(body)
    }
    return response

def ec2_list(event, context):
    """Return a list of instances based on the tag in serverles.yml"""
    body = {}
    status_code = 200

    try:
        client = boto3.client('ec2')
        # Find the instances
        error, instance_names = get_instances(client, event)
        if error:
            body["error"] = error
        else:
            # Add only if no error
            instance_names.append(ALL_INSTANCES_NAME)
            body["message"] = instance_names
    except Exception as e:
        print(traceback.format_exc())
        status_code = 500
        body["error"] = str(e)

    response = {
        "statusCode": status_code,
        "body": json.dumps(body)
    }
    return response

def ec2_status(event, context):
    """Return the status of the instance requested"""
    body = {}
    status_code = 200

    try:
        client = boto3.client('ec2')
        if is_get_all_instances(event):
            # Check all instances
            error, instances = get_instances_status(client, event)
            if error:
                body["error"] = error
            else:
                body["message"] = instances
        else:
            # Find the instance
            error, instance = get_instance(client, event)
            if error:
                body["error"] = error
            else:
                body["message"] = [instance]
    except Exception as e:
        print(traceback.format_exc())
        status_code = 500
        body["error"] = str(e)

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
        error, instance  = get_instance(client, event)
        instance_id = instance.get('name')
        if error:
            body["message"] = error
        else:
            # Start the instance
            r = client.start_instances(InstanceIds=[instance.get('id')])
            if len(r['StartingInstances']) > 0:
                instance['state'] = r['StartingInstances'][0]['CurrentState']['Name']
                body["message"] = [instance]
            else:
                status_code = 500
                body["error"] = 'Unable to start: ' + str(instance_id) + ' ' + str(instance_state)
    except Exception as e:
        print(traceback.format_exc())
        status_code = 500
        body["error"] = str(e)

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
        error, instance = get_instance(client, event)
        if error:
            body["error"] = error
        else:
            # Stop the instance
            r = client.stop_instances(InstanceIds=[instance.get('id')])
            if len(r['StoppingInstances']) > 0:
                instance['state'] = r['StoppingInstances'][0]['CurrentState']['Name']
                body["message"] = [instance]
            else:
                status_code = 500
                body["error"] = 'Unable to stop: ' + str(instance_id) + ' ' + str(instance_state)
    except Exception as e:
        print(traceback.format_exc())
        status_code = 500
        body["error"] = str(e)

    response = {
        "statusCode": status_code,
        "body": json.dumps(body)
    }

    return response
