import boto3
import json
import configparser
import os
from pathlib import Path
import lib.awsFunctions as aws
import time


def launch_instances(path_to_instance, path_to_file):
    """
    path_to_instance: path for template file
    path_to_file: path for configure file
    """

    user_data = """#!/bin/bash
"""
    cfg = configparser.ConfigParser()
    cfg.read(path_to_file)

    # Initialize the ec2 object
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    client = boto3.client('ec2')
    machine_definitions = json.load(open(path_to_instance, 'r'))

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

    ids = []
    for i in range(len(instances)):
        ids.append(instances[i].id)

    waiter = client.get_waiter('instance_running')
    waiter.wait(
        InstanceIds=ids
    )
    return instances


def terminate_instances(ids):
    client = boto3.client('ec2')

    response = client.terminate_instances(
        InstanceIds=ids
    )
    waiter = client.get_waiter('instance_terminated')
    waiter.wait(
        InstanceIds=ids
    )

def getHosts(ids):
    ec2 = boto3.resource('ec2')
    public_ips = []
    private_ips = []
    hostnames = []
    myfile = Path('public_ip')
    if myfile.is_file():
        os.remove('public_ip')

    myfile = Path('private_ip')
    if myfile.is_file():
        os.remove('private_ip')

    myfile = Path('hostname')
    if myfile.is_file():
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


def config_host_alias(ids):
    public_ips, private_ips, hostnames = getHosts(ids)

    with open('hosts.old', 'r') as file:
        lines = file.readlines()

    for i in range(len(public_ips)):
        lines.insert(2, str(public_ips[i])+' '+str(hostnames[i])+'\n')

    for i in range(len(private_ips)):
        lines.insert(2, str(private_ips[i])+' '+str(hostnames[i])+'\n')

    with open('hosts', 'w') as file:
        for line in lines:
            file.write(line)


def main():
    for instance_type in os.listdir('instances'):
        path_to_instance = os.path.join('instances/', instance_type)
        print('starting instances: %s' % path_to_instance)
        instances = launch_instances(path_to_instance, 'config/instances_cfg.ini')
        print('instances launched!')

        time.sleep(20)

        ids = []
        for i in range(len(instances)):
            ids.append(instances[i].id)
        if os.path.basename(instance_type)[3] == 'x':
            cores = 4
        if os.path.basename(instance_type)[3] == '2':
            cores = 8
        if os.path.basename(instance_type)[3] == '4':
            cores = 16

        total_cores = len(ids) * cores

        config_host_alias(ids)
        files = ['hosts', 'hostname', 'public_ip', 'private_ip', 'firstscript.sh', 'run_fwi.sh']
        print('transfering files')
        aws.uploadFiles(ids, 'willkey.pem', files, 'ubuntu')

        commands = ['echo 0 | sudo tee cat /proc/sys/kernel/yama/ptrace_scope', 'sudo mv ~/hosts /etc/hosts']
        print('executing commands')
        aws.executeCommands(ids, 'willkey.pem', commands)

        print('running fwi with %d processes' % total_cores)
        commands = ['chmod +x run_fwi.sh', 'chmod +x firstscript.sh', './run_fwi.sh ' + str(total_cores) + ' >> fwi.out']
        aws.executeCommands(ids[:1], 'willkey.pem', commands)

        instance_type = os.path.basename(instance_type).replace('.json', '')
        result_dir = 'results/' + instance_type

        if not os.path.exists(result_dir):
            os.makedirs(result_dir)

        print('dowloanding output files')
        remote_path = '/home/ubuntu/run_marmousi_template/inversion.out'
        local_path = result_dir + '/inversion.out'
        aws.downloadFile(ids[0], 'willkey.pem', remote_path, local_path)

        remote_path = '/home/ubuntu/run_marmousi_template/modeling.out'
        local_path = result_dir + '/modeling.out'
        aws.downloadFile(ids[0], 'willkey.pem', remote_path, local_path)

        ec2 = boto3.resource('ec2')
        instance = ec2.Instance(ids[0])
        ip = instance.public_ip_address

        os.system('scp -r -i "willkey.pem" ubuntu@%s:pings %s' % (ip, result_dir))
        print('everything downloaded')
        # terminate_instances(ids)
        time.sleep(30)
main()
