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

The main function will need two file, the first one is a configure file and the second one a instance template file.
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

```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags).

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc
