import boto3
import json
import configparser
import os
from pathlib import Path
import lib.awsFunctions as aws
import time
import sys


aws.createCloudEnviroment('config/file.ini')
