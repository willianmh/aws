import boto3
import configparser
import json
import os
import paramiko
import time
from pathlib import Path

import math
import threading


# Send and receive files
# start and stop instances
# launch instances
# create cluster via cloudformation
# create volume
# attach and dettach volume


# *********************************************************
# Broadcast
# *********************************************************
#
# upload files to all VMs 
# NOTE: It do NOT WORK with DIRECTORIES!!!!!


def upload_files(instances_ids, path_to_key, paths_to_files, username='ubuntu', n_attempts=7):
    ec2 = boto3.resource('ec2')
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print('uploading files')
    # k = paramiko.RSAKey.from_private_key_file(path_to_key)

    transfer_status = {}
    for id in instances_ids:  # iterate over each instance
        # get IP
        ip = ec2.Instance(id).public_ip_address

        transfer_status[id] = False
        for attempts in range(n_attempts):  # Try to upload
            try:
                transfer_status[id] = True  # update status for specific instance
                # paramiko stuff
                ssh_client.connect(hostname=ip, username=username, key_filename=path_to_key)
                ftp_client = ssh_client.open_sftp()
                for file in paths_to_files:
                    # file = os.path.basename(path_to_file)
                    # ftp_client.put(path_to_file, '/home/ubuntu/'+file)
                    ftp_client.put(str(file), str(paths_to_files[file]))
                ftp_client.close()
                ssh_client.close()
                print('upload success on %s!' % str(ip))
                break
            except Exception as e:
                print(e)
                print('trying again')
                time.sleep(2)
                continue
        if not transfer_status[id]:
            print('could not transfer files to instance %s' % id)
    return transfer_status


def transfer_parallel(instances_ids, path_to_key, paths_to_files, username='ubuntu', n_attempts=7):
    if len(instances_ids) >= 4:
        y = math.ceil(len(instances_ids)/4)
        t1 = threading.Thread(target=upload_files, args=(instances_ids[:y], path_to_key, paths_to_files, username, n_attempts,))
        t2 = threading.Thread(target=upload_files, args=(instances_ids[y:2*y], path_to_key, paths_to_files, username, n_attempts,))
        t3 = threading.Thread(target=upload_files, args=(instances_ids[2*y:3*y], path_to_key, paths_to_files, username, n_attempts,))
        t4 = threading.Thread(target=upload_files, args=(instances_ids[3*y:len(instances_ids)], path_to_key, paths_to_files, username, n_attempts,))

        t1.start()
        t2.start()
        t3.start()
        t4.start()

        t1.join()
        t2.join()
        t3.join()
        t4.join()
    else:
        upload_files(instances_ids, path_to_key, paths_to_files, username, n_attempts)
# *********************************************************
# Download Files to local
# *********************************************************
#
# Download a single file
#


def download_file(instance_id, path_to_key, remote_path, local_path, username='ubuntu', n_attempts=7):
    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(instance_id)
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ip = instance.public_ip_address

    done = False
    for attempts in range(n_attempts):
        try:
            done = True
            ssh_client.connect(hostname=ip, username=username, key_filename=path_to_key)
            print('downloading files')
            ftp_client = ssh_client.open_sftp()
            ftp_client.get(remote_path, local_path)
            ftp_client.close()
            ssh_client.close()
            break
        except Exception as e:
            print(e)
            print('trying again')
            time.sleep(1)
            continue
    return done
# *********************************************************
# Execute a list of commands to all VMS
# *********************************************************
#
# Execute the same commands to each VM
#


def execute_commands(instances_ids, path_to_key, commands, username='ubuntu', n_attempts=7):
    ec2 = boto3.resource('ec2')
    # if you need to wait your command, you must read its output, otherwise it will return and your command may not be executed
    output = []
    output_err = []

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print('executing commands')
    # k = paramiko.RSAKey.from_private_key_file(path_to_key)

    execute_status = {}
    for id in instances_ids:
        ip = ec2.Instance(id).public_ip_address
        execute_status[id] = False
        for attempts in range(n_attempts):
            try:
                execute_status[id] = True
                ssh_client.connect(hostname=ip, username=username, key_filename=path_to_key)
                for command in commands:
                    print('executing command: %s' % command)
                    stdin, stdout, stderr = ssh_client.exec_command(command)
                    output.append(stdout.readlines())
                    output_err.append(stderr.readlines())
                ssh_client.close()
                break
            except Exception as e:
                print(e)
                print('trying again')
                time.sleep(1)
                continue
        if not execute_status[id]:
            print('could not execute files to instance %s' % id)
    return execute_status, output, output_err


def execute_parallel(instances_ids, path_to_key, commands, username='ubuntu', n_attempts=7):
    if len(instances_ids) >= 4:
        y = math.ceil(len(instances_ids)/4)
        t1 = threading.Thread(target=execute_commands, args=(instances_ids[:y], path_to_key, commands, username, n_attempts,))
        t2 = threading.Thread(target=execute_commands, args=(instances_ids[y:2*y], path_to_key, commands, username, n_attempts,))
        t3 = threading.Thread(target=execute_commands, args=(instances_ids[2*y:3*y], path_to_key, commands, username, n_attempts,))
        t4 = threading.Thread(target=execute_commands, args=(instances_ids[3*y:len(instances_ids)], path_to_key, commands, username, n_attempts,))

        t1.start()
        t2.start()
        t3.start()
        t4.start()

        t1.join()
        t2.join()
        t3.join()
        t4.join()
    else:
        execute_commands(instances_ids, path_to_key, commands, username, n_attempts)

# *********************************************************
# Launch instances
# *********************************************************
#
# Launch instances based on a template file
#


def allocate_host(instance_type, quantity, availability_zone, auto_placement, Tags):
    client = boto3.client('ec2')

    response = client.allocate_hosts(
        InstanceType=instance_type,
        Quantity=quantity,
        AvailabilityZone=availability_zone,
        AutoPlacement=auto_placement,
        TagSpecifications=[
            {
                'ResourceType': 'dedicated-host',
                'Tags': Tags
            },
        ]
    )

    return response


def check_placement_group(placement_name):
    ec2 = boto3.resource('ec2')
    placement_groups = list(ec2.placement_groups.all())
    exist = False
    if len(placement_groups):
        for placement_group in placement_groups:
            if placement_group.group_name == placement_name:
                exist = True
    return exist


def launch_instances(path_to_instance, path_to_file):
    """
    path_to_instance: path for template file
    path_to_file: path for configure file

    it will return instances objects and ids
    instances: list of objects
    ids: list of strings
    """
    # Initialize the ec2 object
    ec2 = boto3.resource('ec2')
    client = boto3.client('ec2')
    iam = boto3.resource('iam')
    current_user = iam.CurrentUser()

    user_data = """#!/bin/bash
"""
    cfg = configparser.ConfigParser()
    cfg.read(path_to_file)

    Tags =[{'Key': 'owner', 'Value': current_user.user_name}]
    for tag in cfg['tags']:
        if not tag == 'owner':
            Tags.append({
                'Key': tag,
                'Value': cfg['tags'][tag]
            })
    # print(Tags)

    machine_definitions = json.load(open(path_to_instance, 'r'))

    # Configure Placement & Tenancy
    if 'Placement' in cfg['instance']:
        if cfg['instance']['Placement'] == 'True':  # Configure Placement Group
            if not check_placement_group(cfg['placement']['Name']):  # Check if placement already exists
                print('creating placement_group: %s' % cfg['placement']['Name'])
                response = client.create_placement_group(
                    GroupName=cfg['placement']['Name'],
                    Strategy=cfg['placement']['Strategy']
                )
                print('placement group %s created!' % cfg['placement']['Name'])
            machine_definitions['Placement']['GroupName'] = cfg['placement']['Name']

    if 'Tenancy' in cfg['instance']:  # Configure Tenancy
        if cfg['instance']['Tenancy'] == 'True':
            machine_definitions['Placement']['Tenancy'] = cfg['tenancy']['Type']

            if cfg['tenancy']['Type'] == 'host':
                reserved_hosts = client.describe_hosts(
                    HostIds=[
                        cfg['placement']['HostdID']
                    ]
                )['Hosts']
                if len(reserved_hosts) == 0:
                    print('error: could not found dedicated host')
                    exit()

                machine_definitions['Placement']['HostId'] = cfg['placement']['hostdID']
                machine_definitions['Placement']['Affinity'] = 'host'

    # Overwrite definitions with configure file
    machine_definitions['UserData'] = user_data
    machine_definitions['ImageId'] = cfg['instance']['CustomAMI']
    machine_definitions['SubnetId'] = cfg['instance']['SubnetID']
    machine_definitions['SecurityGroupIds'][0] = cfg['instance']['SecurityGroupID']
    machine_definitions['MaxCount'] = int(cfg['instance']['MaxCount'])
    machine_definitions['MinCount'] = int(cfg['instance']['MinCount'])

    machine_definitions['BlockDeviceMappings'][0]['Ebs']['VolumeType'] = cfg['Volume']['Type']
    machine_definitions['BlockDeviceMappings'][0]['Ebs']['VolumeSize'] = int(cfg['Volume']['Size'])
    machine_definitions['TagSpecifications'][0]['Tags'] = Tags

    print('starting %d %s' % (int(cfg['instance']['MaxCount']), path_to_instance))
    instances = ec2.create_instances(**machine_definitions)

    # get all IDs
    ids = []
    for i in range(len(instances)):
        ids.append(instances[i].id)
    # waiter for status running on each instances
    waiter = client.get_waiter('instance_running')
    waiter.wait(
        InstanceIds=ids
    )
    print('instances launched!')
    return instances, ids

# *********************************************************
# Start all VMS
# *********************************************************


def start_instances(ids, n_attempts=2):
    client = boto3.client('ec2')
    print('starting instances')
    status = False
    for attempts in range(n_attempts):
        try:
            status = True
            response = client.start_instances(
                instance_ids=ids
            )
            waiter = client.get_waiter('instance_running')
            waiter.wait(
                instance_ids=ids
            )
            print('instances running')
            break
        except Exception as e:
            print(e)
            print('trying again')
            continue
    return status
# *********************************************************
# Start all VMS
# *********************************************************


def stop_instances(ids, n_attempts=2):
    client = boto3.client('ec2')
    print('stopping instances')
    status = False
    for attempts in range(n_attempts):
        try:
            status = True
            response = client.stop_instances(
                instance_ids=ids
            )
            waiter = client.get_waiter('instance_stopped')
            waiter.wait(
                instance_ids=ids
            )
            print('instances stopped')
            break
        except Exception as e:
            print(e)
            print('trying again')
            continue
    return status

# *********************************************************
# Start all VMS
# *********************************************************


def terminate_instances(ids, n_attempts=2):
    client = boto3.client('ec2')
    print('terminating instances')
    status = False
    for attempts in range(n_attempts):
        try:
            status = True
            response = client.terminate_instances(
                InstanceIds=ids
            )
            waiter = client.get_waiter('instance_terminated')
            waiter.wait(
                InstanceIds=ids
            )
            print('instances terminated')
            break
        except Exception as e:
            print(e)
            print('trying again')
            continue
    return status


# af
# *****************************************************************************************
#
# CLOUDFORMATION FUNCTIONS
#
# *****************************************************************************************


def cfn_validate_template(TemplateBody):
    client = boto3.client('cloudformation')

    print('Validating template.')
    # log.debug('Template: ' + str(TemplateBody))
    with open(TemplateBody, 'r') as f:
        try:
            response = client.validate_template(TemplateBody=f.read())
        except Exception as e:
            print(e)
            exit()


def cfn_read_template(configFile):
    config = configparser.ConfigParser()
    config.read(configFile)

    print('Reading configure file.')
    # log.debug('File: ' + str(configFile))

    if 'Template'   not in config['cloudformation']:
        print("You must specify a template")
        return False, {}
    if 'StackName'  not in config['cloudformation']:
        print("You must specify a stack name")
        return False, {}
    if 'Owner'      not in config['user']:
        print("Must specify an owner")
        return False, {}
    if 'KeyName'    not in config['user']:
        print("Must specify a keypair")
        return False, {}
    if 'CustomAMI'  not in config['aws']:
        print("You must specify an IMAGE")
        return False, {}

    if 'MasterInstanceType' not in config['aws']:
        config['aws']['MasterInstanceType'] = 'c5.large'

    if 'ComputeInstanceType' not in config['aws']:
        config['aws']['ComputeInstanceType'] = 'c5.large'

    if 'AvailabilityZone' not in config['aws']:
        config['aws']['AvailabilityZone'] = 'us-east-1a'

    if 'VPCID' not in config['aws']:
        config['aws']['VPCID'] = 'NONE'

    if 'SubnetID' not in config['aws']:
        config['aws']['SubnetID'] = 'NONE'

    if 'InternetGatewayID' not in config['aws']:
        config['aws']['InternetGatewayID'] = 'NONE'

    if 'SecurityGroupID' not in config['aws']:
        config['aws']['SecurityGroupID'] = 'NONE'

    print('Configure file read!')
    return True, config


def cfn_create_cluster(configFile):
    client = boto3.client('cloudformation')
    cloudformation = boto3.resource('cloudformation')

    print('Initializing...')

    response, config = cfn_read_template(configFile)
    if response:
        cfn_validate_template("./templates/" + config['cloudformation']['Template'])
        print('Creating Stack')
        with open("./templates/" + config['cloudformation']['template'], 'r') as template:

            stack = cloudformation.create_stack(
                StackName=config['cloudformation']['stackName'],
                TemplateBody=template.read(),
                Parameters=[
                    {
                        'ParameterKey': 'KeyName',
                        'ParameterValue': config['user']['KeyName']
                    },
                    {
                        'ParameterKey': 'Owner',
                        'ParameterValue': config['user']['Owner']
                    },
                    {
                        'ParameterKey': 'MasterInstanceType',
                        'ParameterValue': config['aws']['MasterInstanceType']
                    },
                    {
                        'ParameterKey': 'ComputeInstanceType',
                        'ParameterValue': config['aws']['ComputeInstanceType']
                    },
                    {
                        'ParameterKey': 'CustomAMI',
                        'ParameterValue': config['aws']['CustomAMI']
                    },
                    {
                        'ParameterKey': 'AvailabilityZone',
                        'ParameterValue': config['aws']['AvailabilityZone']
                    },
                    {
                        'ParameterKey' : 'SubnetID',
                        'ParameterValue': config['aws']['SubnetID']
                    },
                    {
                        'ParameterKey': 'VPCID',
                        'ParameterValue': config['aws']['VPCID']
                    },
                    {
                        'ParameterKey': 'InternetGatewayID',
                        'ParameterValue': config['aws']['InternetGatewayID']
                    },
                    {
                        'ParameterKey': 'SecurityGroupID',
                        'ParameterValue': config['aws']['SecurityGroupID']
                    }
                ]
            )

            waiter = client.get_waiter('stack_create_complete')
            waiter.wait(
                StackName=config['cloudformation']['StackName']
            )
            print('Stack completed')

            outputs = cloudformation.Stack(config['cloudformation']['StackName']).outputs

            output_file = open('cfncluster.out', 'w')
            config = configparser.ConfigParser()

            config.add_section('nodes')

            for output in list(outputs):
                config.set('nodes', output['OutputKey'], output['OutputValue'])

            config.write(output_file)
            output_file.close()

            return cloudformation.Stack(config['cloudformation']['StackName']).outputs, stack

# *********************************************************
# List EC2 instances
# *********************************************************


def listInstances(instance_id):
    ec2 = boto3.resource('ec2')

    return list(ec2.instances.filter(
        instance_ids=[instance_id]
    ))

# *********************************************************
# List EBS volumes
# *********************************************************


def getVolume(owner, name):
    ec2 = boto3.resource('ec2')

    return list(ec2.volumes.filter(
        Filters=[
            {'Name': 'tag:owner', 'Values': [owner]},
            {'Name': 'tag:Name', 'Values': [name]}
            ]))

# *********************************************************
# Create EBS
# *********************************************************


def create_volume(volume_name, AZ='us-east-1a', size=20, snap='', volume_type='gp2'):
    client = boto3.client('ec2')
    iam = boto3.resource('iam')
    current_user = iam.CurrentUser()

    volume_id = None
    try:
        response = client.create_volume(
            AvailabilityZone=AZ,
            Encrypted=False,
            Size=size,
            SnapshotId=snap,
            VolumeType=volume_type,
            TagSpecifications=[
                {
                    'ResourceType': 'volume',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': volume_name
                        },
                        {
                            'Key': 'owner',
                            'Value': current_user.user_name
                        }
                    ]
                },
            ]
        )
        volume_id = response['VolumeId']
    except Exception as e:
        print(e)
        exit()
    return volume_id

# *********************************************************
# Manage EC2 instances
# *********************************************************

# Attach Volume to instance


def attach_volume(instance_id, volume_id, n_attempts=3):
    client = boto3.client('ec2')
    ec2 = boto3.resource('ec2')

    volume = ec2.Volume(volume_id)

    attached = False
    if volume.state == "available":
        for attempt in range(n_attempts):
            try:
                response = volume.attach_to_instance(
                    Device='/dev/sdh',
                    InstanceId=instance_id,
                    )

                waiter = client.get_waiter('volume_in_use')
                waiter.wait(
                    VolumeIds=[volume.id]
                )
                attached = True
                break
            except Exception as e:
                print(e)
                print('error to attach volume to instance, trying again')
                continue
    elif volume.state == "in-use":
        if volume.attachments[0]['instance_id'] == instance_id:
            attached = True
        else:
            print('error Volume attached in another instance')

    return attached

# Dettach volume from instance


def dettach_volume(instance_id, volume_id):
    client = boto3.client('ec2')
    ec2 = boto3.resource('ec2')

    volume = ec2.Volume(volume_id)
    if volume.state == 'in-use':
        response = volume.detach_from_instance(
            instance_id=instance_id,
            )
        waiter = client.get_waiter('volume_available')
        waiter.wait(
            VolumeIds=[volume.id]
        )
        return True
    return False
