#!/bin/bash

source /opt/intel/compilers_and_libraries_2018.3.222/linux/bin/compilervars.sh -arch intel64 -platform linux
source /opt/intel/parallel_studio_xe_2018.3.051/bin/psxevars.sh

N_ITERATIONS=$2


cd ~/
rm -r run_marmousi_template
cp -r toy2dac/run_marmousi_template .
cp private_ip run_marmousi_template

echo "modeling"
cd run_marmousi_template/
sed -i '1s/^/0\n/' mumps_input
sed -i 's/vp_Marmousi_init qp rho epsilon_m delta_m theta_m/vp_Marmousi_exact qp rho/' fdfd_input
sed -i 's/0           ! Hicks interpolation (1 YES, 0 NO)/1           ! Hicks interpolation (1 YES, 0 NO)/' fdfd_input
sed -i 's/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input

ulimit -s unlimited

mpirun -n 4 ../toy2dac/bin/toy2dac

sed -i 's/vp_Marmousi_exact qp rho/vp_Marmousi_init qp rho/' fdfd_input
sed -i 's/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input


for machines in 1 2 4 8 16 32 64
do

  cd ~/
  head -n ${machines} instances_ids > instances_to_start
  python3 aws/start.py instances_to_start

  echo "copying run_marmousi to others workers"
  for i in $(cat hostname | head -n ${machines});do
    if [ ! "$i" == "$(hostname)" ]; then
      for attempts in `seq 1 10`; do
        scp -r run_marmousi_template ${i}:
        if [ $? == 0 ]; then
          break
        fi
        sleep 4
      done
    fi
  done
  for i in $(cat hostname | head -n ${machines});do
    if [ ! "$i" == "$(hostname)" ]; then
      ssh $i "echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope"
      scp -r fwi_src ${i}:
    fi
  done

  cd run_marmousi_template/

  echo "Runnign toy2dac"
  for ppn in 1 2 4 8
  do
    echo "ppn ${ppn}"
    total_processes=$((${machines}*${ppn}))
    omp=$((8/$ppn))
    result_dir=/home/ubuntu/results/toy2dac/

    mkdir -p ${result_dir}

    cat private_ip | head -n ${machines} > hostfile

    mpirun -n ${total_processes} \
    -ppn ${ppn} \
    -genv OMP_NUM_THREADS=${omp} \
    -genv I_MPI_PIN_DOMAIN=omp \
    -f hostfile ~/toy2dac/bin/toy2dac >> ${result_dir}/inversion_${machines}_${ppn}.out

    sleep 1
  done


done
