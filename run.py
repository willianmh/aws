import boto3
import os
from pathlib import Path
import src.awsFunctions as aws
import time
import sys


def getHosts(ids, prefix='.'):
    """
    param ids: list of instances ids
    """
    ec2 = boto3.resource('ec2')
    public_ips = []
    private_ips = []
    hostnames = []

    # remove existing files
    if Path(prefix + '/public_ip').is_file():
        os.remove(prefix + '/public_ip')

    if Path(prefix + '/private_ip').is_file():
        os.remove(prefix + '/private_ip')

    if Path(prefix + '/hostname').is_file():
        os.remove(prefix + '/hostname')

    with open(prefix + '/public_ip', 'a') as public_ip_file, \
            open(prefix + '/private_ip', 'a') as private_ip_file, \
            open(prefix + '/hostname', 'a') as hostname_file:
        for id in ids:
            instance = ec2.Instance(id)

            public_ips.append(instance.public_ip_address)
            private_ips.append(instance.private_ip_address)
            hostnames.append('ip-' + str(instance.private_ip_address).replace('.', '-'))


            public_ip_file.write(str(instance.public_ip_address) + '\n')
            private_ip_file.write(str(instance.private_ip_address) + '\n')
            hostname_file.write('ip-' + str(instance.private_ip_address).replace('.', '-') + '\n')

    return public_ips, private_ips, hostnames


def config_host_alias(ids, prefix='.'):
    public_ips, private_ips, hostnames = getHosts(ids, prefix)

    with open('hosts.old', 'r') as file:
        lines = file.readlines()

    for i in range(len(public_ips)):
        lines.insert(2, str(public_ips[i])+' '+str(hostnames[i])+'\n')

    for i in range(len(private_ips)):
        lines.insert(2, str(private_ips[i])+' '+str(hostnames[i])+'\n')

    with open(prefix + '/hosts', 'w') as file:
        for line in lines:
            file.write(line)


def main():
    path_to_instance = sys.argv[1]
    path_to_configure = sys.argv[2]
    path_to_key = sys.argv[3]
    dir = sys.argv[4]

    if not os.path.isdir(dir):
        os.makedirs(dir)

    # path_to_instance = 'instances/c5.xlarge.json'
    print('starting program')
    instances, ids = aws.launch_instances(path_to_instance, path_to_configure)
    # write ids on file
    if Path(dir + '/instances_ids').is_file():
        os.remove(dir + '/instances_ids')
    with open(dir + '/instances_ids', 'w') as id_file:
        for id in ids:
            id_file.write(str(id) + '\n')

    cores = instances[0].cpu_options['CoreCount'] * instances[0].cpu_options['ThreadsPerCore']
    total_cores = len(ids) * cores
    print('total cores: %d' % total_cores)

    # create 4 files and configure a host alias
    # - hostname:       all hostames
    # - public_ips:     public ips (Warning! The values will change if stop instance)
    # - private_ips:    private ips to be used as hostfile
    # - hosts:          a file to be moved to /etc/hosts
    config_host_alias(ids, dir)

    # necessary files to run mpi applications
    files = {
        dir + '/hosts':                       '/home/ubuntu/hosts',
        dir + '/hostname':                    '/home/ubuntu/hostname',
        dir + '/public_ip':                   '/home/ubuntu/public_ip',
        dir + '/private_ip':                  '/home/ubuntu/private_ip',
        dir + '/instances_ids':               '/home/ubuntu/instances_ids',
        'scripts/firstscript.sh':              '/home/ubuntu/firstscript.sh',
        'scripts/ping.sh':                     '/home/ubuntu/ping.sh',
        'scripts/copy_all.sh':                 '/home/ubuntu/copy_all.sh',
        'scripts/disable_hyperthreading.sh':   '/home/ubuntu/disable_hyperthreading.sh',
        'scripts/run_fwi_toydac.sh':           '/home/ubuntu/run_fwi_toydac.sh'
    }

    # aws.uploadFiles(ids, path_to_key, files, 'ubuntu')
    aws.transfer_parallel(ids, path_to_key, files)
    # necessary commands to to run mpi applications
    commands = [
        'echo 0 | sudo tee cat /proc/sys/kernel/yama/ptrace_scope',
        'sudo mv ~/hosts /etc/hosts',
        'chmod +x firstscript.sh',
        'chmod +x ping.sh',
        'chmod +x copy_all.sh',
        'chmod +x disable_hyperthreading.sh',
        'chmod +x run_fwi_toydac.sh',
        # 'sudo ./disable_hyperthreading.sh',
        ]
    # aws.executeCommands(ids, path_to_key, commands)
    aws.execute_parallel(ids, path_to_key, commands)

    commands = [
        './firstscript.sh',
        './run_fwi_toydac.sh'
    ]
    aws.execute_commands(ids[:1], path_to_key, commands)

    # POST PROCESS - depends on your application
    print('running fwi with %d processes' % total_cores)
    commands = ['./run_fwi_toydac.sh ']
    stdout, stderr = aws.execute_commands(ids[:1], path_to_key, commands)

    with open('test.log', 'w') as filelog:
        for line in stdout:
            filelog.write(str(line))

    # instance_type = os.path.basename(path_to_instance).replace('.json', '')
    result_dir = 'results/' + dir
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    for i in range(1, 4):
        remote_path = '/home/ubuntu/inversion_'+str(i)+'.out'
        local_path = result_dir + '/inversion_'+str(i)+'.out'
        aws.download_file(ids[0], path_to_key, remote_path, local_path)

    os.system('mkdir -p %s' % result_dir+'/pings')
    os.system('scripts/get_pings.sh %s' % result_dir+'/pings')

    aws.terminate_instances(ids)
    # time.sleep(20)


main()
