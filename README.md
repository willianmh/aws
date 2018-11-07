# HPC - Hayashida's Power Cloud

A fantastic tool to setup and automate test on AWS cloud enviroment using python.

## Getting Started

First, you need an AWS account. These scripts were made with python and bash.

### Prerequisites

To use boto3, you need awscli. Install it, and configure with you secret access key and ID.

```bash
sudo apt-get install awscli
aws configure
```

You need boto3, paramiko and configparser packages installed on your machine

```bash
pip install boto3 paramiko configparser
```
### Important

The main function will need two file, a configure file and a instance template file.
In this repository the files are on _instances_ and _config_ folder.
The configure file has priority, so it will overwrite the definitions on template file.

Basically, the instance template is a file to define the instance type to be launched. If you look on the _instances_ folder, you'll see that the templates are all the same, except the instance type.

## Usage

Edit configure file and template file and run.

```bash
python3 run.py 'path_to_template' 'path_to_configure_file' 'path_to_pem_key'
```

Example:

```bash
python3 run.py 'instances/c5.xlarge.json' 'config/instances_cfg.ini' 'mykey.pem'
```

You just need to adapt run.py to your application.

### Understanding

Once you've executed run.py, it will create 4 files.

```
public_ip
private_ip
hostname
hosts
```

They are all copied to remote on run.py.

The _hosts_ file is important to run mpi application, it must be moved to /etc/hosts.
The run.py edit _hosts.old_ and add the necessary lines.

The _private_ip_ and _hostname_ are important to configure ssh keys on remote.
They can also be used as _hostfile_ with mpirun.

On remote:

```bash
mv private_ip hostfile
mpirun -n 4 -f hostfile ./foo
```

The _public_ip_ will be used to configure the ssh keys, but it is not an essencial file.
After you stop and start a VM, the value of public IP will change.

I strongly recommend to use the private IP when running mpi applicatins.

### Firstscript

The firstscript.sh is responsable to configure SSH KEYS, and it will use _private_ip_, _public_ip_ and _hostname_.
You can edit it to do more stuff for you.
## Using AWS Functions

```python
import src.awsFunctions as aws
```

### transfering files to remote

You need to define a list with the paths to the files and the IDs of the instances.

```python
username = "ubuntu" # AWS use it by default on ubuntu VMs
files = ['file_1', '../file_2', 'file_3']
aws.uploadFiles(ids, path_to_key, files, username)
```

It works like a broadcast.
Copy the same files to all remotes on "~/".



### Connecting to remote

With the _public_ip_ file, you can execute:

```bash
ssh -i "path_to_pem_key" ubuntu@$(cat public_ip | tail -n 1)
```

Be carefull that it will not work if you stop the instance and start again.

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) - Boto is the Amazon Web Services (AWS) SDK for Python
