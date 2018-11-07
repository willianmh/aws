import boto3
import configparser
import json
import os
import paramiko
import time
import datetime
from pathlib import Path


class Logger:
    def __init__(self):
        self.debug = False

    def write(self, s):
        print(datetime.datetime.now() + " " + s)

    def debug(self, s):
        if self.debug:
            self.write(s)

basedir = os.getcwd().split('aws',1)[0] + 'aws'

debug = False
log = Logger()
log.debug = debug

# *********************************************************
# Broadcast
# *********************************************************
#
# upload files to all VMs
#


def uploadFiles(instancesids, path_to_key, paths_to_files, username='ubuntu', n_attempts=5):
    ec2 = boto3.resource('ec2')
    public_ips = []

    for id in instancesids:
        instance = ec2.Instance(id)
        public_ips.append(instance.public_ip_address)

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    log.write('uploanding files')
    # k = paramiko.RSAKey.from_private_key_file(path_to_key)
    for ip in public_ips:
        for attempts in range(n_attempts):
            try:
                ssh_client.connect(hostname=ip, username=username, key_filename=path_to_key)
                ftp_client = ssh_client.open_sftp()
                for path_to_file in paths_to_files:
                    file = os.path.basename(path_to_file)
                    ftp_client.put(path_to_file, '/home/ubuntu/'+file)
                ftp_client.close()
                ssh_client.close()
                log.write('upload success on %s!' % str(ip))
                break
            except Exception as e:
                log.write(e)
                log.write('trying again')
                time.sleep(1)
                continue

# *********************************************************
# Download Files to local
# *********************************************************
#
# Download a single file
#


def downloadFile(instanceid, path_to_key, remote_path, local_path, username='ubuntu'):
    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(instanceid)

    ip = instance.public_ip_address

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=ip, username=username, key_filename=path_to_key)
    log.write('downloading files')
    ftp_client = ssh_client.open_sftp()
    ftp_client.get(remote_path, local_path)
    ftp_client.close()
    ssh_client.close()

# *********************************************************
# Execute a list of commands to all VMS
# *********************************************************
#
# Execute the same commands to each VM
#


def executeCommands(instancesids, path_to_key, commands, username='ubuntu'):
    ec2 = boto3.resource('ec2')
    public_ips = []
    output = []
    output_err = []
    for id in instancesids:
        instance = ec2.Instance(id)
        public_ips.append(instance.public_ip_address)

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    log.write('executing commands')
    # k = paramiko.RSAKey.from_private_key_file(path_to_key)
    for ip in public_ips:
        ssh_client.connect(hostname=ip, username=username, key_filename=path_to_key)
        for command in commands:
            log.write('executing commmand: %s' % command)
            stdin, stdout, stderr = ssh_client.exec_command(command)
            output.append(stdout.readlines())
            output_err.append(stderr.readlines())
    ssh_client.close()

    return output, output_err

# *********************************************************
# Launch instances
# *********************************************************
#
# Launch instances based on a template file
#


def launch_instances(path_to_instance, path_to_file):
    """
    path_to_instance: path for template file
    path_to_file: path for configure file

    it will return instances objects and ids
    intances: list of objects
    ids: list of strings
    """

    user_data = """#!/bin/bash
"""
    cfg = configparser.ConfigParser()
    cfg.read(path_to_file)

    # Initialize the ec2 object
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    client = boto3.client('ec2')
    machine_definitions = json.load(open(path_to_instance, 'r'))

    if cfg['placement']['enable'] == 'True' and cfg['tenancy']['enable'] == 'True':
        log.write('Error in definitions. You must select between placement and tenancy')
        exit()

    # Launch Instances on Placement
    if cfg['placement']['enable'] == 'True':
        # Check if placement already exists
        placement_groups = list(ec2.placement_groups.all())
        not_exist = True
        if len(placement_groups):
            for placement_group in placement_groups:
                if placement_group.group_name == cfg['placement']['name']:
                    not_exist = False

        if not_exist:
            log.write('creating placement_group: %s' % cfg['placement']['name'])
            response = client.create_placement_group(
                GroupName=cfg['placement']['name'],
                Strategy=cfg['placement']['strategy']
            )
        machine_definitions['Placement']['GroupName'] = cfg['placement']['name']
    # Launch Instances on Specific Tenancy
    if cfg['tenancy']['enable'] == 'True':
        machine_definitions['Placement']['Tenancy'] = cfg['tenancy']['type']
        if cfg['placement']['type'] == 'host':
            machine_definitions['Placement']['HostId'] = cfg['placement']['hostdID']
            machine_definitions['Placement']['Affinity'] = 'host'

    # Overwrite definitions with configure file
    machine_definitions['UserData'] = user_data
    machine_definitions['ImageId'] = cfg['instance']['CustomAMI']
    machine_definitions['SubnetId'] = cfg['instance']['SubnetID']
    machine_definitions['SecurityGroupIds'][0] = cfg['instance']['SecurityGroupID']
    machine_definitions['MaxCount'] = int(cfg['instance']['MaxCount'])
    machine_definitions['MinCount'] = int(cfg['instance']['MinCount'])

    log.write('starting %d %s' % (int(cfg['instance']['MaxCount']), path_to_instance))
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
    # write ids on file
    myfile = Path('instances_ids')
    if myfile.is_file():
        os.remove('hostname')
    with open('instances_ids', 'a') as id_file:
        for id in ids:
            id_file.write(str(id) + '\n')

    log.write('instances launched!')
    return instances, ids

# *********************************************************
# Terminate all VMS
# *********************************************************


def terminate_instances(ids):
    client = boto3.client('ec2')
    log.write('terminating instances')
    response = client.terminate_instances(
        InstanceIds=ids
    )
    waiter = client.get_waiter('instance_terminated')
    waiter.wait(
        InstanceIds=ids
    )
    log.write('instances terminated')

# *****************************************************************************************
#
# CLOUDFORMATION FUNCTIONS
#
# *****************************************************************************************


def validateTemplate(TemplateBody):
    client = boto3.client('cloudformation')

    log.write('Validating template.')
    log.debug('Template: ' + str(TemplateBody))
    with open(TemplateBody, 'r') as f:
        response = client.validate_template(TemplateBody=f.read())


def readConfigFile(configFile):
    config = configparser.ConfigParser()
    config.read(configFile)

    log.write('Reading configure file.')
    log.debug('File: ' + str(configFile))

    if 'Template' not in config['cloudformation']:
        log.write("You must specify a template")
        return False, {}

    if 'StackName' not in config['cloudformation']:
        log.write("You must specify a stack name")
        return False, {}

    if 'Owner' not in config['user']:
        log.write("Must specify an owner")
        return False, {}

    if 'KeyName' not in config['user']:
        log.write("Must specify a keypair")
        return False, {}


    if 'CustomAMI' not in config['aws']:
        log.write("You must specify an IMAGE")
        return False, {}

    if 'MasterInstanceType' not in config['aws']:
        config['aws']['MasterInstanceType'] = 'c5.large'
    log.debug('Master Instance Type: ' + config['aws']['MasterInstanceType'])

    if 'ComputeInstanceType' not in config['aws']:
        config['aws']['ComputeInstanceType'] = 'c5.large'
    log.debug('Compute Instance Type: ' + config['aws']['ComputeInstanceType'])

    if 'AvailabilityZone' not in config['aws']:
        config['aws']['AvailabilityZone'] = 'us-east-1a'
    log.debug('Availability Zone: ' + config['aws']['AvailabilityZone'])

    if 'VPCID' not in config['aws']:
        config['aws']['VPCID'] = 'NONE'
    log.debug('VPC Id: ' + config['aws']['VPCID'])

    if 'SubnetID' not in config['aws']:
        config['aws']['SubnetID'] = 'NONE'
    log.debug('Subnet: ' + config['aws']['SubnetID'])

    if 'InternetGatewayID' not in config['aws']:
        config['aws']['InternetGatewayID'] = 'NONE'
    log.debug('Internet Gateway Id: ' + config['aws']['InternetGatewayID'])

    if 'SecurityGroupID' not in config['aws']:
        config['aws']['SecurityGroupID'] = 'NONE'
    log.debug('Security Group: ' + config['aws']['SecurityGroupID'])

    log.write('Configure file read!')
    return True, config

def createCloudEnviroment(configFile):
    client = boto3.client('cloudformation')
    cloudformation = boto3.resource('cloudformation')

    log.write('Initializing...')

    response, config = readConfigFile(configFile)
    if response:
        validateTemplate(basedir + "/templates/" + config['cloudformation']['Template'])
        log.write('Creating Stack')
        with open(basedir + "/templates/" + config['cloudformation']['template'], 'r') as template:

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
            log.debug('Stack launched, waiting to complete...')
            waiter = client.get_waiter('stack_create_complete')
            waiter.wait(
                StackName=config['cloudformation']['StackName']
            )
            log.write('Stack completed')

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
        InstanceIds=[instance_id]
    ))

# *********************************************************
# List EBS volumes
# *********************************************************


def getVolume(owner, name):
    ec2 = boto3.resource('ec2')

    return list(ec2.volumes.filter(
        Filters=[
            {'Name': 'tag:Owner', 'Values': [owner]},
            {'Name': 'tag:Name', 'Values': [name]}
            ]))

# *********************************************************
# Create EBS
# *********************************************************


def createVolume(owner, name, AZ='us-east-1a', snap="snap-145ee46b"):
    client = boto3.client('ec2')

    response = client.create_volume(
        AvailabilityZone=AZ,
        Encrypted=False,
        Size=500,
        SnapshotId=snap,
        VolumeType='st1',
        TagSpecifications=[
            {
                'ResourceType': 'volume',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': name
                    },
                    {
                        'Key': 'Owner',
                        'Value': owner
                    }
                ]
            },
        ]
    )
    return response['VolumeId']

# *********************************************************
# Manage EC2 instances
# *********************************************************

# Start Instance


def startInstance(instance_id):
    client = boto3.client('ec2')
    ec2 = boto3.resource('ec2')

    instance = ec2.Instance(instance_id)

    if instance.state["Name"] == "stopped":
        response = instance.start()

        waiter = client.get_waiter('instance_running')
        waiter.wait(
            InstanceIds=[instance.id]
        )
        log.write("intances are running")
    return instance

# Stop Instance


def stopInstance(instance_id):
    client = boto3.client('ec2')
    ec2 = boto3.resource('ec2')

    instance = ec2.Instance(instance_id)
    if instance.state["Name"] == "running":
        response = instance.stop()

        waiter = client.get_waiter('instance_stopped')
        waiter.wait(
            InstanceIds=[instance.id]
        )
        log.write("intances are stopped")
        return True
    return False

# Attach Volume to instance


def attachVolume(instance_id, volume_id):
    client = boto3.client('ec2')
    ec2 = boto3.resource('ec2')

    volume = ec2.Volume(volume_id)
    if volume.state == "available":
        response = volume.attach_to_instance(
            Device='/dev/sdh',
            InstanceId=instance_id,
            )
        waiter = client.get_waiter('volume_in_use')
        waiter.wait(
            VolumeIds=[volume.id]
        )
        return ec2.Volume(volume_id)
    elif volume.state == "in-use":
        if volume.attachments[0]['InstanceId'] == instance_id:
            return ec2.Volume(volume_id)
    return None

# Dettache volume from instance


def dettachVolume(instance_id, volume_id):
    client = boto3.client('ec2')
    ec2 = boto3.resource('ec2')

    volume = ec2.Volume(volume_id)
    if volume.state == 'in-use':
        response = volume.detach_from_instance(
            InstanceId=instance_id,
            )
        waiter = client.get_waiter('volume_available')
        waiter.wait(
            VolumeIds=[volume.id]
        )
        return True
    return False

# *********************************************************
# Prepare enviroment
# *********************************************************


def startVisualization(instance_id, volume_id, pem_key):
    instance = startInstance(instance_id)
    log.write(instance)
    if instance:
        if attachVolume(instance_id, volume_id):
            os.system('ssh -i "%s" ubuntu@%s mkdir /home/ubuntu/shared' % (pem_key, instance.public_ip_address))
            os.system('ssh -i "%s" ubuntu@%s sudo mount /dev/nvme1n1 /home/ubuntu/shared' % (pem_key, instance.public_ip_address))

            log.write("Instance %s is running and mounted to volume %s." % (instance_id, volume_id))
            log.write("Connect to instance with the following IP:")
            log.write("%s" % instance.public_ip_address)
        else:
            log.write("Volume is already attached to some instance")


def stopVisualization(instance_id, volume_id):
    if dettachVolume(instance_id=instance_id, volume_id=volume_id):
        log.write("Volume dettached")
        if stopInstance(instance_id=instance_id):
            log.write("Instance stopped")
            return True
    return False
