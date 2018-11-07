import boto3
import configparser
import os
# aws.executeScript(instancesids=ids, path_to_key='/home/willian/Documents/cepetro/aws/willkey.pem', path_to_file='test.sh', username='ubuntu')


def getHosts(ids):
    ec2 = boto3.resource('ec2')
    public_ips = []
    private_ips = []
    hostnames = []
    os.remove('public_ip')
    os.remove('private_ip')
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


def run_fwi():
    cfg = configparser.ConfigParser()
    cfg.read('cfcluster.out')

    ids = []
    ids.append(cfg['nodes']['masterid'])
    ids.append(cfg['nodes']['computeid'])

    public_ips, private_ips, hostnames = getHosts(ids)

    with open('hosts.old', 'r') as file:
        lines = file.readlines()

    for i in range(len(public_ips)):
        lines.insert(2, public_ips[i]+' '+hostnames[i]+'\n')

    for i in range(len(private_ips)):
        lines.insert(2, private_ips[i]+' '+hostnames[i]+'\n')

    with open('hosts', 'w') as file:
        for line in lines:
            file.write(line)
