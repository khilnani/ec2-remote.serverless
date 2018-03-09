
# Overview

This project enables you to start or shutdown an EC2 instance via a simple button click from your your phone. Its built using AWS [Lambda](https://aws.amazon.com/lambda/), [API Gateway](https://aws.amazon.com/api-gateway/) and the [iOS Workflow app](https://workflow.is). 

If you are like me and play around with AWS a lot and want an easy want to stop and start your EC2 instances, this might be useful for you. 

It makes obvious sense to keep your production EC2 instance online all the time you do not need to keep your development instance online 24x7 in many cases. While its pretty easy to shutdown and start instances from a computer using the AWS CLI, you need to have the AWS credentionals and scripts setup. This means only the computer setup can perform the tasks in an automated manner. Everyone else needs to log into the AWS console. This is not much fun to do from a mobile device.

We'll solve this using:

- [AWS Lambda](https://aws.amazon.com/lambda/), [AWS API Gateway](https://aws.amazon.com/api-gateway/) - Look, no servers!
- [Python](http://python.org/) - Yup, serverless without NodeJS.
- [Serverless Framework](https://serverless.com) - Framework to setup and manage AWS resources
- [Workflow on iOS](https://workflow.is) - Create a Today Widget for instant access - swipe down and click

## Screenshots

> Below are screenshots once the API is setup and in use.

<img src="https://raw.githubusercontent.com/khilnani/ec2-remote.serverless/master/docs/home-screen.png" width="30%" /><img src="https://raw.githubusercontent.com/khilnani/ec2-remote.serverless/master/docs/instance-list.png" width="30%" /><img src="https://raw.githubusercontent.com/khilnani/ec2-remote.serverless/master/docs/select-action.png" width="30%" /><img src="https://raw.githubusercontent.com/khilnani/ec2-remote.serverless/master/docs/instance-info.png" width="30%" /><img src="https://raw.githubusercontent.com/khilnani/ec2-remote.serverless/master/docs/email.jpg" width="30%" />

# Setup

OK, lets get started. There are quite a few steps here and you may need 30 mins to 1 hour depending on your familiarity with AWS. 

*Note*

- The default setup will create a public API endpoint. Take a look at the *Private API Setup* section to make the API private. 
- The project has been tested on Ubuntu, macOS as well as Bash on Windows 10, with and without Docker.

## AWS Setup

Since we're working with AWS Lambda and AWS API Gateway, we need to setup AWS credentials. 
We are also going to use the Serverless framework to manage the AWS tech stack.

> - The role Serverless needs requires a lot of privilages. 
> - The role used to setup and deploy is different from the permissions set on the lambda code that runs.
> - If this concerns you, create a new AWS account to play around with.

### Serverless AWS Credentials Setup

- Follow the instructions at https://serverless.com/framework/docs/providers/aws/guide/credentials/ . They cover the setup pretty well.

### Manual AWS IAM Setup

- Create an IAM Group with:
  - Attach Managed Policies:
    - AmazonEC2FullAccess - Start and stop EC2 instances
    - AWSLambdaFullAccess - Create and manage Lambda functions
    - AmazonS3FullAccess - Create a bucket to store the lambda function code
    - CloudWatchLogsFullAccess - Create and manage Cloudwatch logs
    - CloudWatchEventsFullAccess - Manage Cloudwatch events
    - AmazonSESFullAccess - Send Emails for alerts
    - AmazonAPIGatewayAdministrator - Create and manage API endpoints
    - IAMFullAccess - Create new role for the Lambda to work with EC2 instances
  - Create Custom Group Policy > Custom Policy:
    - Custom CloudFormation policy (below)- Create and manage CloudFormation stacks
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1499009146000",
            "Effect": "Allow",
            "Action": [
                "cloudformation:*"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```
- Create an IAM User and assign the User the newly created Group
- Setup AWS credentials with this user's security credentials. Check the above link since it has a good overview.

## Code Setup

- Make sure you have Python 2.7.
- Install NodeJS - https://nodejs.org/en/download/
- Import helper shortcut commands - `source source.sh`. The commands imported are in the format `s-NAME`.
- Install Serverless - `s-install` or `npm install -g serverless --upgrade`

# Build and Deploy

- Install Python dependencies that will get packaged and deployed with your Lambda function. 
    - Run `s-requirements`, or
```
mkdir -p ./site-packages
pip install --upgrade -t site-packages/ -r requirements.txt`
```
- Next, deploy the service - `s-deploy` or `serverless deploy --verbose`. 
    - This will package and deploy your Lambda function and create the API endpoint
    - Once complete, it will display information about the stack. e.g. The API endpoint URL you need below
    - The resources used will be prefixed with `ec2-remote-dev` in AWS Lambda, AWS API Gateway and AWS CloudWatch logs.
    - Logs are setup to expire after 7 days.
    - Details are available in `serverless.yaml`
- If you need to get the info again, run `s-info` or `serverless info --verbose`

# Whitelist EC2 Instances

Even though you may (and should) secure the API with an api key, you will need to tag EC2 instances to:

1. Limit which EC2 instances that can be controlled by this API, and
2. Auto-list the instances available (to avoid memorizing the names) via the *list* endpoint

Tag info to use:

> The tag Key can be customized in the `serverless.yml` file

- Key: `ec2-remote-filter`
- Value: `true`

# Email Notification of Running Instances

If you would like to be alerted if instances are left running for more than a day, you can tag them using the info below
and set an email address an alert should be sent to. 

Email address:

- Go to https://console.aws.amazon.com/ses/home?region=us-east-1#verified-senders-email - Add and verify your email address.
- Edit `environment\EC2_EMAIL` in `serverless.yml` and update the email address.
- Edit `environment\EC2_EMAIL_PREFIX` in `serverless.yml` and update the email subject prefix. The default is `[EC2-Remote]`.

Tag info to use:

> The tag Key and schedule can be customized in the `serverless.yml` file

- Key: `ec2-remote-monitor`
- Value: `true`

# Testing

## The Email Notification

There are two options for testing the email notification:

Lambda invocation

- `s-run ec2-monitor` - Local code
- `s-run-remote ec2-monitor` - Code deployed to AWS

Via the API

-  https://API_ID.execute-api.us-east-1.amazonaws.com/dev/ec2/check

## Test the API Endpoints

> Don't forget to replace `INSTANCE_TAG_NAME`  and `API_ID` (Output from serverless deploy)
> By default, the API is public. CHeck the section below to make it secure/private.

Descptive Endpoints

- List - https://API_ID.execute-api.us-east-1.amazonaws.com/dev/ec2/list/
Sample JSON Output:
```
{
    "message": ["name1", "name2"]
}
```

Action Endpoints

- Status - https://API_ID.execute-api.us-east-1.amazonaws.com/dev/ec2/status/INSTANCE_NAME
Sample JSON Output:
```
{
    "message": "i-78ffff49 running"
}
```
- Stop - https://API_ID.execute-api.us-east-1.amazonaws.com/dev/ec2/stop/INSTANCE_NAME
Sample JSON Output:
```
{
    "message": "i-78ffff49 stopped"
}
```
- Start - https://API_ID.execute-api.us-east-1.amazonaws.com/dev/ec2/start/INSTANCE_NAME
Sample JSON Output:
```
{
    "message": "i-78ffff49 pending"
}
```

## Private API Setup

In most cases you will want to secure access to this API. We'll do this using an AWS API Key using the steps below:

- Create an API Key - https://console.aws.amazon.com/apigateway/home?region=us-east-1#/api-keys
- Create a Usage Plan - https://console.aws.amazon.com/apigateway/home?region=us-east-1#/usage-plans
    - Add the API (`ec2-remote-dev`) and API Key you created to the Usage Plan.
- Update `private` to `true` in the `serverless.yaml` method definition for the `unread` function 
- Make API calls with the Request Header `x-api-key: APIKEY`. 
- Example:
```
curl -H "x-api-key: AWS_API_KEY" https://API_ID.execute-api.us-east-1.amazonaws.com/dev/ec2/status/INSTANCE_NAME
```

# iOS Workflow App Setup

Once you have an api, you can call it from where ever you want. Since we (or I) want to use a phone as a remote, we'll use [Workflow on iOS](https://workflow.is). 

- Download the app from the app store - https://workflow.is/download
- Launch https://github.com/khilnani/ec2-remote.serverless/raw/master/files/EC2%20Remote%20Template.wflow in Safari on your iOS device
    - Open the file using the Workflow app. 
    - It will create a workflow called 'EC2 Remote Sample'
- Replace `api_url` with the url from the deployment stack output.
  - `https://API_ID.execute-api.us-east-1.amazonaws.com/dev/ec2`
  - Note, there is no ending '/'
- Replace `api_key` with the AWS API Key created earlier
- Edit the list with `INSTANCE_TAG_NAME` with names (tag:name) for the iEC2 instances you want to control, one instance name per line.
- Run the workflow!

