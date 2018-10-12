#!/bin/bash

for i in $(ls instances)
do
  echo "${i}"
  python3 run_test.py "instances/${i}" 2>&1 | tee -a log/${i}.log
done
