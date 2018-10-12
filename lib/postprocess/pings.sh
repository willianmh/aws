#!/bin/bash


for folder in $(ls)
do
  BASE=$(ls "${folder}/pings" | tail -n 1)
  ls $(sed 's/\_[^\_]*$//' <<< ${BASE} )* > IPS
  sed -i 's/^.*\_[^\_]/1/' IPS

  for i in $(cat IPS)
  do
    for j in $(cat IPS)
    do
      i_aux=$(sed 's/\./-/g' <<< $i)

    done
  done
done


ping_ip-10-0-0-241_to_10.0.0.241
