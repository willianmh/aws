import boto3
import os

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
