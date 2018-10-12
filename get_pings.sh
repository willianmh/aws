#!/bin/bash

DIR=$1

for i in $(cat public_ip)
do
  ssh-keygen -R $i
  ssh-keyscan -H $i >> ~/.ssh/known_hosts
  scp -r -i "willkey.pem" ubuntu@${i}:pings/* $DIR
done
