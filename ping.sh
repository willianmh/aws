#!/bin/bash

mkdir -p pings
for host in $(cat private_ip)
do
  ping -c 15 $host >> pings/ping_$(hostname)_to_${host} &
done
