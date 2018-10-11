#!/bin/bash

    "Placement": {
      "GroupName": ""
    },
INSERT='    "Placement": {
      "GroupName": ""
    },'

for i in $(ls)
do

  awk -i inplace -v insert="$INSERT" '{print} NR==2{print insert}' $i
done
