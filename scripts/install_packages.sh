#!/bin/bash

set -x

sudo apt-get install -y htop vim tmux tree zsh git
sudo apt-get install -y gcc g++ gfortran build-essential
sudo apt-get install -y libtool m4 automake
sudo apt-get install -y grads
sudo apt-get install -y libz-dev

if [ ! -f ~/mpich-3.2.1.tar.gz ]
then
  wget http://www.mpich.org/static/downloads/3.2.1/mpich-3.2.1.tar.gz
fi

tar xfz mpich-3.2.1.tar.gz
cd mpich-3.2.1
./configure -disable-fast CFLAGS=-O2 FFLAGS=-O2 CXXFLAGS=-O2 FCFLAGS=-O2 -prefix=/opt/mpich3 CC=gcc FC=gfortran F77=gfortran
make
sudo make install
cd ~/
