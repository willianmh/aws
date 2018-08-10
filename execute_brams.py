#!/usr/bin/python

import boto3
import os


def execute_brams():

    ec2 = boto3.resource('ec2')  # call ec2 recourse to perform further actions
    instances = list(ec2.instances.all())  # get all instances from above region
    os.remove("hostfile")
    os.remove("myPublicIPs")

    number_processors = 0
    if len(instances):
        for instance in instances:
            with open("hostfile", 'a') as private_ip, open("myPublicIPs", 'a') as public_ip:
                private_ip.write(str(instance.private_ip_address) + '\n')
                public_ip.write(str(instance.public_ip_address) + '\n')
            number_processors += instance.cpu_options['CoreCount'] * instance.cpu_options['ThreadsPerCore']

        print ("total cores = %d" % number_processors)

        # get the last instance to be the master
        one_public_ip = instances[-1].public_ip_address

        # Transfer files
        os.system('scp -i "willkey.pem" hostfile ubuntu@%s:meteo-only' % one_public_ip)
        os.system('scp -i "willkey.pem" brams.sh ubuntu@%s:' % one_public_ip)
        # Execute brams
        os.system('ssh -i "willkey.pem" ubuntu@%s "nohup ./brams.sh %d &"' % (one_public_ip, number_processors))

    else:
        print("No instances found!")


if __name__ == "__main__":
    execute_brams()
