import boto3
import json
import configparser
import os
import lib.awsFunctions as aws


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


def getHosts(ids):
    ec2 = boto3.resource('ec2')
    public_ips = []
    private_ips = []
    hostnames = []

    os.remove('public_ip')
    os.remove('private_ip')
    os.remove('hostname')

    for id in ids:
        instance = ec2.Instance(id)

        public_ips.append(instance.public_ip_address)
        private_ips.append(instance.private_ip_address)
        hostnames.append('ip-' + str(instance.private_ip_address).replace('.', '-'))

        with open('public_ip', 'a') as public_ip_file, open('private_ip', 'a') as private_ip_file, open('hostname', 'a') as hostname_file:
            public_ip_file.write(str(instance.public_ip_address) + '\n')
            private_ip_file.write(str(instance.private_ip_address) + '\n')
            hostname_file.write('ip-' + str(instance.private_ip_address).replace('.', '-') + '\n')

    return public_ips, private_ips, hostnames


def config_instances(ids):
    cfg = configparser.ConfigParser()
    cfg.read('cfcluster.out')

    public_ips, private_ips, hostnames = getHosts(ids)

    with open('hosts.old', 'r') as file:
        lines = file.readlines()

    for i in range(len(public_ips)):
        lines.insert(2, public_ips[i]+' '+hostnames[i]+'\n')

    for i in range(len(private_ips)):
        lines.insert(2, private_ips[i]+' '+hostnames[i]+'\n')

    with open('hosts', 'w') as file:
        for line in lines:
            file.write(line)


def main():
    for instance_type in os.listdir('instances'):
        instances = launch_instances(instance_type, 'config/instance_cfg_ini')
        ids = []
        for i in range(len(instances)):
            ids.append(i.id)

        config_instances(ids)
        files = ['hosts', 'hostname', 'public_ip', 'private_ip', 'firstscript.sh']
        aws.transferfile(ids, 'willkey.pem', files, 'ubuntu')
        commands = ['echo 0 | sudo tee /proc/sys/kernel/yama/ptrace-scope',
            'sudo mv ~/hosts /etc/hosts',
            './firstscript.sh']



main()
