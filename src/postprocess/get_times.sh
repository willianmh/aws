#!/bin/bash

DIR=$1

# generate one file for each case (1 & 2)
for i in `seq 1 2`
do
  OUTPUT_FILE=$DIR/all_times_${i}
  rm $OUTPUT_FILE
  # iterate under each item in dir
  for folder in $(ls ${DIR})
  do
    if [ -d "${DIR}/$folder" ]
    then
      for j in `seq 1 5`
      do
	       echo ${DIR}/$folder  >> $OUTPUT_FILE
    	  cat ${DIR}/${folder}/inversion_${i}_${j}.out | tail -n 350 | sed -e '/summary/,$!d' -e '/END OF PROGRAM/,+1 d' >> $OUTPUT_FILE
    	  echo '' >> $OUTPUT_FILE
      done
    fi
  done
  grep 'results_' $OUTPUT_FILE > $DIR/a
  grep 'Average' $OUTPUT_FILE > $DIR/b

  sed -i 's/|[^|]*$//;s/ //g;s/Average|//;s/[|].*$//g' $DIR/b
  paste -d, $DIR/a $DIR/b > $DIR/time_${i}.csv
done




rm -f $DIR/a $DIR/b
