#!/usr/bin/python

import boto3
import sys
import json

from aux_functions import getLogger

# aws ec2 run-instances --cli-input-json file://ec2runinst.json

# ========= Accepted Params for ec2.create_instances ===========

# BlockDeviceMappings, ImageId, InstanceType, Ipv6AddressCount, Ipv6Addresses,
# KernelId, KeyName, MaxCount, MinCount, Monitoring, Placement, RamdiskId,
# SecurityGroupIds, SecurityGroups, SubnetId, UserData, AdditionalInfo,
# ClientToken, DisableApiTermination, DryRun, EbsOptimized, IamInstanceProfile,
# InstanceInitiatedShutdownBehavior, NetworkInterfaces, PrivateIpAddress,
# ElasticGpuSpecification, TagSpecifications, LaunchTemplate,
# InstanceMarketOptions, CreditSpecification

# ===============================================================

# In order to properly configure a machine to be SSH capable, the following must be accomplished on the contrary order:
# Define a VPC associated with one or more subnets
#   Define a subnet associated with the route table
#       Define a Route Table associated with the IG
#           Define a Internet Gateway

# AMIs:
# Canonical Ubuntu: ami-43a15f3e
# Amazon Linux AMI: ami-1853ac65

# Access machine with a command like: ssh -i <your_key>.pem ubuntu@<Public DNS (IPv4)>


def main():
    user_data = """#!/bin/bash
"""

    # Access the execution of user_data: cat /var/log/cloud-init-output.log
    # Access the user script: /var/lib/cloud/instance/scripts/.

    # b64_user_data = str(base64.b64encode(data_user))

    if len(sys.argv) <= 1:
        logger.error('Please insert the json path as the first parameter! Terminating...')
        return
    logger.info('Starting the instance deployment from the template "'+sys.argv[1]+'"')
    # Opening json with definitions from the first argument
    machine_definitions = json.load(open(sys.argv[1], 'r'))
    machine_definitions['UserData'] = user_data
    # Initialize the ec2 object
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    # Initialize the ec2 client object
    client = boto3.client('ec2')
    # This will explode the dictionary to become the parameters:
    # "{i:20,j:30}" will become (i=20,j=30) and create instances
    # according to the json file
    instances = ec2.create_instances(**machine_definitions)
    # get the instance id from the only (if only 1) created instance
    instance_id = instances[0].id
    logger.info('Instance deployed! Instance id: '+instance_id)
    logger.info(instances)


if __name__ == "__main__":
    logger = getLogger(__name__)
    main()
