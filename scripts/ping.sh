#!/bin/bash

# this script pings all instances based on a file with private IPs
# To collect a matrix of pings, it must be executed in every instance
# Sample:
#
# for instance in $(cat private_ip)
# do
#   ssh $instance ./pings.sh
# done

mkdir -p pings
for host in $(cat private_ip)
do
  ping -c 20 $host >> pings/ping_$(hostname)_to_${host} &
done

wait
