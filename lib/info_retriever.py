#!/usr/bin/python

import boto3
import os


def info_retriever():
    ec2 = boto3.resource('ec2')  # call ec2 recourse to perform further actions
    instances = list(ec2.instances.all())  # get all instances from above region

    # os.remove("hostfile")
    # os.remove("myPublicIPs")

    if len(instances):
        for instance in instances:
            print ("Instance ID: %s" % instance.id)
            print ("Instance type: %s" % instance.instance_type)
            print ("Instance state: %s" % instance.state['Name'])
            print ("Number cores: %d" % instance.cpu_options['CoreCount'])
            print ("Number threads per core: %d" % instance.cpu_options['ThreadsPerCore'])
            # get diference between spot and on demands instances
            if instance.tags and len(instance.tags) and 'Value' in list(instance.tags)[0]:
                print ("Type: %s" % instance.tags[0]['Value'])
            print ("-------------------------")

    placement_groups = list(ec2.placement_groups.all())

    if len(placement_groups):
        for placement_group in placement_groups:
            print ("Group Name: %s" % placement_group.group_name)




if __name__ == "__main__":
    info_retriever()
