#!/bin/bash

for i in $(ls instances)
do
  echo $i
  python3 run_test.py $i 2>&1 | tee -a ${i}.log
done
