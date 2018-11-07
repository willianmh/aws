#!/usr/bin/python

import boto3
import json

import configparser


def launch_instances(instance_type, path_to_file):
    user_data = """#!/bin/bash
"""
    cfg = configparser.ConfigParser()
    cfg.read(path_to_file)

    # Initialize the ec2 object
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    client = boto3.client('ec2')
    machine_definitions = json.load(open(instance_type, 'r'))

    if cfg['aws']['cluster'] == 'True':
        placement_groups = list(ec2.placement_groups.all())
        not_exist = True
        if len(placement_groups):
            for placement_group in placement_groups:
                if placement_group.group_name == cfg['aws']['placement']:
                    not_exist = False

        if not_exist:
            response = client.create_placement_group(
                GroupName=cfg['aws']['placement'],
                Strategy='cluster'
            )
        machine_definitions['Placement']['GroupName'] = cfg['aws']['placement']

    # Opening json with definitions from the first argument
    machine_definitions['UserData'] = user_data

    machine_definitions['ImageId'] = cfg['instance']['CustomAMI']
    machine_definitions['SubnetId'] = cfg['instance']['SubnetID']
    machine_definitions['SecurityGroupIds'][0] = cfg['instance']['SecurityGroupID']

    machine_definitions['MaxCount'] = int(cfg['instance']['MaxCount'])
    machine_definitions['MinCount'] = int(cfg['instance']['MinCount'])

    instances = ec2.create_instances(**machine_definitions)
    # get the instance id from the only (if only 1) created instance
    return instances
