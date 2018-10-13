#!/bin/bash

PATH_TO_DIR=$1
OUTPUT_FILE=${PATH_TO_DIR}/latencies.csv

echo "${PATH_TO_DIR}," > $OUTPUT_FILE

for folder in $(ls $PATH_TO_DIR)
do
  if [ -d "${PATH_TO_DIR}/${folder}" ]
  then
    PING_DIR=${PATH_TO_DIR}/${folder}/pings
#    echo $PING_DIR
    BASE=$(ls ${PING_DIR} | tail -n 1)
#    echo $BASE
    rm IPS
    ls ${PING_DIR}/$(sed 's/\_[^\_]*$//' <<< ${BASE} )* > IPS
    sed -i 's/^.*\_[^\_]/1/' IPS

    echo $folder | tr '\n' ',' >> ${OUTPUT_FILE}
    for j in $(cat IPS)
    do
      echo $j | tr '\n' ',' >> ${OUTPUT_FILE}
    done


    echo '' >> ${OUTPUT_FILE}

    for i in $(cat IPS)
    do
      echo $i | tr '\n' ',' >> ${OUTPUT_FILE}
      for j in $(cat IPS)
      do
        i_aux=$(sed 's/\./-/g' <<< $i) # 10-0-0-95
#        grep avg ${PING_DIR}/ping_ip-${i_aux}_to_${j}
        AVG_PING=$(grep avg ${PING_DIR}/ping_ip-${i_aux}_to_${j} | \
          sed -e 's/^.*= //' -e 's/^[^\/]*\///g' -e 's/[\/].*$//')
        echo ${AVG_PING} | tr '\n' ',' >> $OUTPUT_FILE
      done
      echo '' >> ${OUTPUT_FILE}
    done
  fi
done

sed -i 's/.$//g' $OUTPUT_FILE
