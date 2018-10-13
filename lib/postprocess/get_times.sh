#!/bin/bash

DIR=$1
OUTPUT_FILE=$DIR/all_times
rm $OUTPUT_FILE
rm $DIR/a $DIR/b $DIR/time.csv
for folder in $(ls ${DIR})
do
	echo ${DIR}/$folder  >> $OUTPUT_FILE
	cat ${DIR}/${folder}/inversion.out | tail -n 350 | sed -e '/summary/,$!d' -e '/END OF PROGRAM/,+1 d' >> $OUTPUT_FILE
	echo '' >> $OUTPUT_FILE
done

grep 'results_*' $OUTPUT_FILE | sed 's/results_*\///g' > $DIR/a
grep 'Average' $OUTPUT_FILE > $DIR/b

sed -i 's/|[^|]*$//;s/ //g;s/Average|//;s/[|].*$//g' $DIR/b
paste -d, $DIR/a $DIR/b > $DIR/time.csv
rm $DIR/a $DIR/b
