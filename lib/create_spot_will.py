#!/usr/bin/python
# Copyright 2018 Nicholas Torres Okita <nicholas.okita@ggaunicamp.com>

import boto3
import base64
from botocore.exceptions import ClientError
import sys
from datetime import datetime
import time

from lib.aux_functions import getLogger


def main():
    subnets = {
        'us-east-1a': 'subnet-0fc78340b0af1017d',
    }

    user_data = """#!/bin/bash

"""

    if len(sys.argv) <= 1:
        logger.error('Please insert instance type')
        return

    instance_type_in = sys.argv[1]

    ec2 = boto3.client('ec2', region_name='us-east-1')
    conn = ec2
    # zones = conn.describe_availability_zones()
    zoneNames = [ 'us-east-1a' ]

    bestZone = ['', sys.float_info.max]
    for zone in zoneNames:
        history = conn.describe_spot_price_history(
                StartTime=datetime.now().isoformat(),
                EndTime=datetime.now().isoformat(),
                ProductDescriptions=['Linux/UNIX'],
                InstanceTypes=[instance_type_in],
                AvailabilityZone=zone);
        for h in history['SpotPriceHistory']:
            if float(h['SpotPrice']) < bestZone[1]:
                bestZone[0] = h['AvailabilityZone']
                bestZone[1] = float(h['SpotPrice'])

    if len(sys.argv) == 4:
        bestZone[0] = sys.argv[2]
        bestZone[1] = float(sys.argv[3])

    price = bestZone[1]
    PRICE = str(price*1.2)

    logger.info("Instance " + instance_type_in + " in " + bestZone[0] + " for " + str(price))

    response  = ec2.request_spot_instances(
            SpotPrice=PRICE,
            InstanceCount=1,
            LaunchSpecification={
                'InstanceType': instance_type_in,
                'ImageId': 'ami-0ec6192b8b6c593b9',
                'SecurityGroupIds': ['sg-02f4ea97d74f5e263'],
                'SubnetId': subnets[bestZone[0]],
                'UserData': (base64.b64encode(user_data.encode())).decode(),
                'KeyName': 'willkey',
                'Monitoring': {
                    'Enabled': True
                },
                'Placement': {
                    'AvailabilityZone': bestZone[0]
                },
                'BlockDeviceMappings': [{
                    'DeviceName': '/dev/sda1',
                    'VirtualName': 'eth0',
                    'Ebs': {
                        'DeleteOnTermination': True,
                        'VolumeSize': 20,
                        'VolumeType': 'gp2',
                    },
                    'NoDevice': ''
                },
                ]
            })

    spot_request_id = response['SpotInstanceRequests'][0]['SpotInstanceRequestId']
    logger.info('Spot Request done! Spot Request Id: '+spot_request_id)

    time.sleep(30)
    response = ec2.describe_spot_instance_requests(SpotInstanceRequestIds=[spot_request_id])
    cur_spot = response['SpotInstanceRequests'][0]
    if ('InstanceId' in cur_spot):
        logger.info('Spot Instance Id: ' + cur_spot['InstanceId'])
        result = ec2.create_tags(Resources=[cur_spot['InstanceId']],
                Tags=[
                    {
                        'Key': 'type',
                        'Value': 'spot'
                    }
                    ]
                )
    else:
        logger.error('Spot Request for ' + instance_type_in + ' failed in zone ' + bestZone[0])
        ec2.cancel_spot_instance_requests(SpotInstanceRequestIds=[spot_request_id])


if __name__ == '__main__':
    logger = getLogger(__name__)
    main()
