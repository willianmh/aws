#!/bin/bash

DIR=$1
OUTPUT_FILE=$DIR/times
rm $OUTPUT_FILE

for folder in $(ls ${DIR})
do
	echo ${DIR}/$folder >> $OUTPUT_FILE
	cat ${DIR}/${folder}/inversion.out| tail -n 100 | sed -e '/summary/,$!d' -e '/END OF PROGRAM/,+1 d' >> $OUTPUT_FILE
	echo '' >> $OUTPUT_FILE
done
