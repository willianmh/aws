#!/usr/bin/python

import boto3


def info_retriever():
    ec2 = boto3.resource('ec2')  # call ec2 recourse to perform further actions
    instances = list(ec2.instances.all())  # get all instances from above region

    if len(instances):
        for instance in instances:
            print ("Instance ID: %s" % instance.id)
            print ("Number cores: %d" % instance.cpu_options['CoreCount'])
            print ("Number threads per core: %d" % instance.cpu_options['ThreadsPerCore'])
            print ("-------------------------")


if __name__ == "__main__":
    info_retriever()
