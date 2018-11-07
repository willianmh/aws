#!/bin/bash

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


  SSH_ADDR="ubuntu@$(cat public_ip | tail -n 1)"

  ssh ${SSH_ADDR} "ssh-keygen -f ~/.ssh/id_rsa_new -t rsa -N '' "
  scp ${SSH_ADDR}:.ssh/id_rsa_new.pub id_rsa_coordinator.pub

  for hostname in $(cat public_ip); do
      # echo "Put ssh key on $hostname"
      ssh-copy-id -f -i id_rsa_coordinator.pub "ubuntu@${hostname}"
  done

  for host in $(cat private_ip)
  do
    scp .ssh/known_hosts "${host}:.ssh"
  done
}

setup_ssh_keys
