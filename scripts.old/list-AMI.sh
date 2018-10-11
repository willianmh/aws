#!/bin/bash

## declare an array variable
declare -a regions=("ap-northeast-1"
"ap-northeast-2"
"ap-northeast-3"
"ap-south-1"
"ap-southeast-1"
"ap-southeast-2"
"ca-central-1"
"eu-central-1"
"eu-west-1"
"eu-west-2"
"eu-west-3"
"sa-east-1"
"us-east-1"
"us-east-2"
"us-west-1"
"us-west-2"
"us-gov-west-1")

## now loop through the above array
for region in "${regions[@]}"
do
  echo $region | tr '\n' ' ' >> ubuntu-regions
  aws ec2 describe-images --owners 099720109477 \
    --region $region \
    --filters 'Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-????????' 'Name=state,Values=available' | jq -r '.Images | sort_by(.CreationDate) | last(.[]).ImageId' >> ubuntu-regions

done
