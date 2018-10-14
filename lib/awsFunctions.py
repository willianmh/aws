import boto3
import os
import configparser
import paramiko
import time
# import json


def validateTemplate(TemplateBody):
    client = boto3.client('cloudformation')

    with open(TemplateBody, 'r') as f:
        response = client.validate_template(TemplateBody=f.read())


def readConfigFile(configFile):
    config = configparser.ConfigParser()
    config.read(configFile)

    if 'Template' not in config['cloudformation']:
        print("You must specify a template")
        return False, {}

    if 'StackName' not in config['cloudformation']:
        print("You must specify a stack name")
        return False, {}

    if 'Owner' not in config['user']:
        print("Must specify an owner")
        return False, {}

    if 'KeyName' not in config['user']:
        print("Must specify a keypair")
        return False, {}


    if 'CustomAMI' not in config['aws']:
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

    return True, config


def uploadFiles(instancesids, path_to_key, paths_to_files, username='ubuntu'):
    ec2 = boto3.resource('ec2')
    public_ips = []

    for id in instancesids:
        instance = ec2.Instance(id)
        public_ips.append(instance.public_ip_address)

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print('uploanding files')
    # k = paramiko.RSAKey.from_private_key_file(path_to_key)
    for ip in public_ips:
        n_attempts = 5
        for attempts in range(n_attempts):
            try:
                ssh_client.connect(hostname=ip, username=username, key_filename=path_to_key)
                ftp_client = ssh_client.open_sftp()
                for path_to_file in paths_to_files:
                    file = os.path.basename(path_to_file)
                    ftp_client.put(path_to_file, '/home/ubuntu/'+file)
                ftp_client.close()
                ssh_client.close()
                print('upload success on %s!' % str(ip))
                break
            except Exception as e:
                print(e)
                print('trying again')
                time.sleep(1)
                continue


def downloadFile(instanceid, path_to_key, remote_path, local_path, username='ubuntu'):
    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(instanceid)

    ip = instance.public_ip_address

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=ip, username=username, key_filename=path_to_key)
    print('downloading files')
    ftp_client = ssh_client.open_sftp()
    ftp_client.get(remote_path, local_path)
    ftp_client.close()
    ssh_client.close()


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
    print('executing commands')
    # k = paramiko.RSAKey.from_private_key_file(path_to_key)
    for ip in public_ips:
        ssh_client.connect(hostname=ip, username=username, key_filename=path_to_key)
        for command in commands:
            print('executing commmand: %s' % command)
            stdin, stdout, stderr = ssh_client.exec_command(command)
            output.append(stdout.readlines())
            output_err.append(stderr.readlines())
    ssh_client.close()

    return output, output_err


def createEnviroment(configFile):
    client = boto3.client('cloudformation')
    cloudformation = boto3.resource('cloudformation')

    response, config = readConfigFile(configFile)
    if response:
        validateTemplate("../templates/"+config['cloudformation']['Template'])

        with open("../templates/"+config['cloudformation']['template'], 'r') as template:

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
        print("intances are running")
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
        print("intances are stopped")
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
    print(instance)
    if instance:
        if attachVolume(instance_id, volume_id):
            os.system('ssh -i "%s" ubuntu@%s mkdir /home/ubuntu/shared' % (pem_key, instance.public_ip_address))
            os.system('ssh -i "%s" ubuntu@%s sudo mount /dev/nvme1n1 /home/ubuntu/shared' % (pem_key, instance.public_ip_address))

            print("Instance %s is running and mounted to volume %s." % (instance_id, volume_id))
            print("Connect to instance with the following IP:")
            print("%s" % instance.public_ip_address)
        else:
            print("Volume is already attached to some instance")


def stopVisualization(instance_id, volume_id):
    if dettachVolume(instance_id=instance_id, volume_id=volume_id):
        print("Volume dettached")
        if stopInstance(instance_id=instance_id):
            print("Instance stopped")
            return True
    return False

# *********************************************************
# Prepare enviroment
# *********************************************************
