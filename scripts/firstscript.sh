#!/bin/bash

# This script configure ssh keys and create an nfs server
# It will mount the nfs on ~/shared directory

setup_ssh_keys() {

  # add access credential for all vm's
  for hostname in $(cat public_ip); do
    # echo " Copy id from $hostname"
    ssh-keygen -R $hostname
    ssh-keygen -R `dig +short $hostname`
    ssh-keyscan -H $hostname >> ~/.ssh/known_hosts
  done

  for hostname in $(cat private_ip); do
    # echo " Copy id from $hostname"
    ssh-keygen -R $hostname
    ssh-keygen -R `dig +short $hostname`
    ssh-keyscan -H $hostname >> ~/.ssh/known_hosts
  done

  for hostname in $(cat hostname); do
    # echo " Copy id from $hostname"
    ssh-keygen -R $hostname
    ssh-keygen -R `dig +short $hostname`
    ssh-keyscan -H $hostname >> ~/.ssh/known_hosts
  done

  SSH_ADDR="ubuntu@$(cat private_ip | tail -n 1)"

  ssh-keygen -f ~/.ssh/id_rsa_new -t rsa -N ''
  cp ~/.ssh/id_rsa_new.pub id_rsa_coordinator.pub

  for hostname in $(cat public_ip); do
      # echo "Put ssh key on $hostname"
      ssh-copy-id -f -i id_rsa_coordinator.pub "ubuntu@${hostname}"
  done

  for host in $(cat private_ip)
  do
    scp .ssh/known_hosts "${host}:.ssh"
  done
}

set_nfs() {
  mkdir -p shared
#  sudo chown ubun:nogroup ~/shared

  echo "/home/ubuntu/shared *(rw,sync,no_root_squash,no_subtree_check)" | sudo tee -a /etc/exports
  sudo service nfs-kernel-server restart
  sudo exportfs -a

  echo $(hostname) > master
  ./copy_all.sh master

  for host in $(cat hostname)
  do
    if [ ! "$(hostname)" == "$host" ];then
      ssh $host mkdir -p ~/shared
      ssh $host 'sudo mount -t nfs $(cat ~/master):/home/ubuntu/shared ~/shared'
      ssh $host 'echo "$(cat ~/master):/home/ubuntu/shared /home/ubuntu/shared nfs" | sudo tee -a /etc/fstab'
    fi
  done
}

setup_ssh_keys
set_nfs
