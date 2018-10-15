#!/bin/bash

var=$1

for i in 1 2 4 6 8 12 24 48	
do
	echo "MPI: $((48/$i)) | OMP: $i"
done

