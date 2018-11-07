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
### important

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

### Understanding

Once you've executed run.py, it will create 4 files.

```
public_ip
private_ip
hostname
hosts
```

The _hosts_ file is important to run mpi application, it must be moved to /etc/hosts.
The script will edit _hosts.old_ and add the necessary lines.
Don't worry, the run.py script do the job for you.

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

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) - Boto is the Amazon Web Services (AWS) SDK for Python
