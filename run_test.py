import boto3
import json
import configparser
import os
from pathlib import Path
import lib.awsFunctions as aws
import time
import sys


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
            print('creating placement_group: %s' % cfg['aws']['placement'])
            response = client.create_placement_group(
                GroupName=cfg['aws']['placement'],
                Strategy='spread'
            )
        machine_definitions['Placement']['GroupName'] = cfg['aws']['placement']

    if 'tenancy' in cfg['aws']:
        machine_definitions['Placement']['Tenancy'] = cfg['aws']['tenancy']
        if cfg['aws']['tenancy'] == 'host':
            machine_definitions['Placement']['HostId'] = cfg['aws']['hostdID']
            machine_definitions['Placement']['Affinity'] = 'host'

    # Opening json with definitions from the first argument
    machine_definitions['UserData'] = user_data

    machine_definitions['ImageId'] = cfg['instance']['CustomAMI']
    machine_definitions['SubnetId'] = cfg['instance']['SubnetID']
    machine_definitions['SecurityGroupIds'][0] = cfg['instance']['SecurityGroupID']

    machine_definitions['MaxCount'] = int(cfg['instance']['MaxCount'])
    machine_definitions['MinCount'] = int(cfg['instance']['MinCount'])

    print('starting %d %s' % (int(cfg['instance']['MaxCount']), path_to_instance))
    instances = ec2.create_instances(**machine_definitions)

    ids = []
    for i in range(len(instances)):
        ids.append(instances[i].id)

    waiter = client.get_waiter('instance_running')
    waiter.wait(
        InstanceIds=ids
    )
    print('instances launched!')
    return instances


def terminate_instances(ids):
    client = boto3.client('ec2')
    print('terminating instances')
    response = client.terminate_instances(
        InstanceIds=ids
    )
    waiter = client.get_waiter('instance_terminated')
    waiter.wait(
        InstanceIds=ids
    )
    print('instances terminated')


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
    path_to_instance = sys.argv[1]
    n_iterations = 5
    # path_to_instance = 'instances/c5.xlarge.json'
    print('starting program')
    instances = launch_instances(path_to_instance, 'config/instances_cfg.ini')
    time.sleep(20)

    ids = []
    for i in range(len(instances)):
        ids.append(instances[i].id)

    cores = instances[0].cpu_options['CoreCount'] * instances[0].cpu_options['ThreadsPerCore']
    total_cores = len(ids) * cores
    print('total cores: %d' % total_cores)

    config_host_alias(ids)
    files = ['hosts', 'hostname', 'public_ip', 'private_ip', 'firstscript.sh', 'run_fwi.sh', 'ping.sh']
    aws.uploadFiles(ids, 'willkey.pem', files, 'ubuntu')

    commands = ['echo 0 | sudo tee cat /proc/sys/kernel/yama/ptrace_scope', 'sudo mv ~/hosts /etc/hosts']
    aws.executeCommands(ids, 'willkey.pem', commands)
    commands = ['chmod +x run_fwi.sh', 'chmod +x firstscript.sh', 'chmod +x ping.sh']
    aws.executeCommands(ids, 'willkey.pem', commands)

    print('running fwi with %d processes' % total_cores)
    commands = ['./run_fwi.sh ' + str(total_cores) + ' ' + str(n_iterations)]
    stdout, stderr = aws.executeCommands(ids[:1], 'willkey.pem', commands)

    with open('test.log', 'w') as filelog:
        for line in stdout:
            filelog.write(str(line))

    instance_type = os.path.basename(path_to_instance).replace('.json', '')
    result_dir = 'results/' + instance_type

    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    for i in range(1, 3):
        for j in range(1, n_iterations+1):
            remote_path = '/home/ubuntu/inversion_'+str(i)+'_'+str(j)+'.out'
            local_path = result_dir + '/inversion_'+str(i)+'_'+str(j)+'.out'
            aws.downloadFile(ids[0], 'willkey.pem', remote_path, local_path)

            remote_path = '/home/ubuntu/modeling_'+str(i)+'_'+str(j)+'.out'
            local_path = result_dir + '/modeling_'+str(i)+'_'+str(j)+'.out'
            aws.downloadFile(ids[0], 'willkey.pem', remote_path, local_path)

    os.system('mkdir -p %s' % result_dir+'/pings')
    os.system('./get_pings.sh %s' % result_dir+'/pings')

    terminate_instances(ids)
    time.sleep(20)


main()
