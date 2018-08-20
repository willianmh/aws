#!/bin/bash

cd meteo-only
export TMPDIR=./tmp
ulimit -s 65536
date > hello
echo $1 > number_processors
/opt/mpich3/bin/mpirun -n $1 -f hostfile ./brams 2>&1 | tee log_brams_meteo_only.out
