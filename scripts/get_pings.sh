#!/bin/bash

# This script get pings files from all instances, after executed pings.sh and put in $DIR
# It should be executed in local, or a host that you will collect and post process data

FILE=$1
DIR=$2

for i in $(cat ${FILE})
do
  ssh-keygen -R $i
  ssh-keyscan -H $i >> ~/.ssh/known_hosts
  scp -r -i "willkey.pem" ubuntu@${i}:pings/* $DIR
done
