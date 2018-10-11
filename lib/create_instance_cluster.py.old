#!/usr/bin/python

import boto3
import sys
import json
import argparse

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

# General purpose: M4, M5, M5d
#
# Compute optimized: C3, C4, C5, C5d, cc2.8xlarge
#
# Memory optimized: cr1.8xlarge, R3, R4, R5, R5d, X1, X1e, z1d
#
# Storage optimized: D2, H1, hs1.8xlarge, I2, I3, i3.metal
#
# Accelerated computing: F1, G2, G3, P2, P3

def main():
    user_data = """#!/bin/bash
"""

    parser = argparse.ArgumentParser()
    # create arguments
    parser.add_argument('-n', action='store', dest='number_machines',
                        help='Select number machines to instanciate')
    parser.add_argument('-i', action='store', dest='instance',
                        help='Select instance type')

    results = parser.parse_args()

    if results.number_machines:
        number_machines = results.number_machines
    else:
        number_machines = 1

    if results.instance:
        instance = results.instance
    else:
        logger.error(logger.error('Please insert the json path as the first parameter! Terminating...'))
        return

    logger.info('Starting the cluster deployment from the template "' + instance + '"')

    # Initialize the ec2 object
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    # Initialize the ec2 client object
    client = boto3.client('ec2')

    placement_groups = list(ec2.placement_groups.all())

    not_exist = True
    if len(placement_groups):
        for placement_group in placement_groups:
            if placement_group.group_name == '501st':
                not_exist = False

    if not_exist:
        response = client.create_placement_group(
            GroupName='501st',
            Strategy='cluster'
        )

    # Opening json with definitions from the first argument
    machine_definitions = json.load(open(instance, 'r'))
    machine_definitions['UserData'] = user_data

    machine_definitions['Placement']['GroupName'] = '501st'
    machine_definitions['MaxCount'] = number_machines
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
