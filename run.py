import boto3
import os
from pathlib import Path
import src.awsFunctions as aws
import time
import sys


def getHosts(ids):
    """
    param ids: list of instances ids
    """
    ec2 = boto3.resource('ec2')
    public_ips = []
    private_ips = []
    hostnames = []

    # remove existing files
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
    path_to_configure = sys.argv[2]
    path_to_key = sys.argv[3]
    # path_to_instance = 'instances/c5.xlarge.json'
    print('starting program')
    instances, ids = aws.launch_instances(path_to_instance, path_to_configure)
    time.sleep(2)

    cores = instances[0].cpu_options['CoreCount'] * instances[0].cpu_options['ThreadsPerCore']
    total_cores = len(ids) * cores
    print('total cores: %d' % total_cores)

    # create 4 files and configure a host alias
    # - hostname:       all hostames
    # - public_ips:     public ips (Warning! The values will change if stop instance)
    # - private_ips:    private ips to be used as hostfile
    # - hosts:          a file to be moved to /etc/hosts
    config_host_alias(ids)

    # necessary files to run mpi applications
    files = [
        'hosts',
        'hostname',
        'public_ip',
        'private_ip',
        'instances_ids',
        'firstscript.sh',
        'ping.sh',
        'copy_all.sh',
        'disable_hyperthreading.sh',
        'run_all.sh',
        ]
    # aws.uploadFiles(ids, path_to_key, files, 'ubuntu')
    aws.transferParallel(ids, path_to_key, files)
    # necessary commands to to run mpi applications
    commands = [
        'echo 0 | sudo tee cat /proc/sys/kernel/yama/ptrace_scope',
        'sudo mv ~/hosts /etc/hosts',
        'chmod +x firstscript.sh',
        'chmod +x ping.sh',
        'chmod +x copy_all.sh',
        'chmod +x disable_hyperthreading.sh',
        'chmod +x run_all.sh',
        ]
    # aws.executeCommands(ids, path_to_key, commands)
    aws.executeParallel(ids, path_to_key, commands)

    commands = ['./firstscript.sh']
    aws.executeCommands(ids[:1], path_to_key, commands)
    # n_iterations = 1
    # print('running fwi with %d processes' % total_cores)
    # commands = ['./run_fwi.sh ' + str(total_cores) + ' ' + str(n_iterations)]
    # stdout, stderr = aws.executeCommands(ids[:1], path_to_key, commands)
    #
    # with open('test.log', 'w') as filelog:
    #     for line in stdout:
    #         filelog.write(str(line))
    #
    # instance_type = os.path.basename(path_to_instance).replace('.json', '')
    # result_dir = 'results/' + instance_type
    #
    # if not os.path.exists(result_dir):
    #     os.makedirs(result_dir)
    #
    # for i in range(1, 3):
    #     for j in range(1, n_iterations+1):
    #         remote_path = '/home/ubuntu/inversion_'+str(i)+'_'+str(j)+'.out'
    #         local_path = result_dir + '/inversion_'+str(i)+'_'+str(j)+'.out'
    #         aws.downloadFile(ids[0], path_to_key, remote_path, local_path)
    #
    #         remote_path = '/home/ubuntu/modeling_'+str(i)+'_'+str(j)+'.out'
    #         local_path = result_dir + '/modeling_'+str(i)+'_'+str(j)+'.out'
    #         aws.downloadFile(ids[0], path_to_key, remote_path, local_path)
    #
    # os.system('mkdir -p %s' % result_dir+'/pings')
    # os.system('./get_pings.sh %s' % result_dir+'/pings')
    #
    # aws.terminate_instances(ids)
    # time.sleep(20)


main()
