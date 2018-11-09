#!/bin/bash

FILE=$1

for i in $(cat hostname)
do
	if [ ! "$(hostname)" == "$i" ]
	then
		scp -r $FILE ${i}:
		echo $i
	fi
done
