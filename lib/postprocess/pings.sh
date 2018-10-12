#!/bin/bash


for folder in $(ls)
do
  BASE=ls "${folder}/pings" | tail -n 1
  ls $(sed 's/\_[^\_]*$//' <<< ${BASE} )*
