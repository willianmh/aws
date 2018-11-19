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
sed -i 's/1 !Nfreq/5 !Nfreq/' freq_management
sed -i 's/3. 5. 7. 9./3. 4. 5. 6. 7./' freq_management
sed -i 's/10        ! number of nonlinear iterations/50        ! number of nonlinear iterations' fwi_input

ulimit -s unlimited

mpirun -n 4 ../toy2dac/bin/toy2dac

sed -i 's/vp_Marmousi_exact qp rho/vp_Marmousi_init qp rho/' fdfd_input
sed -i 's/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input
cd ~/
cp instances_ids ids

for machines in 64 32 16 8 4 2 1
do

  cd ~/
  tail -n $((64-${machines})) instances_ids > instances_to_stop # from the alive, stop some of them

  python3 aws/stop.py instances_to_stop

  # head -n ${machines} instances_ids | tail -n $((${machines}-1)) > instances_to_start
  # python3 aws/start.py instances_to_start

  # tar -xzf run_marmousi_template.tar.gz run_marmousi_template
  # tar -xzf fwi_src.tar.gz fwi_src

  # echo "copying run_marmousi to others workers"
  # python3 aws/transfer.py instances_to_start willkey.pem fwi_src.tar.gz run_marmousi_template.tar.gz
  # python3 aws/execute.py instances_to_start willkey.pem 'tar -xzf fwi_src.tar.gz' 'tar -xzf run_marmousi_template.tar.gz'

  # for i in $(cat hostname | head -n ${machines});do
  #   if [ ! "$i" == "$(hostname)" ]; then
  #     for attempts in `seq 1 10`; do
  #       scp -q -r run_marmousi_template ${i}:
  #       if [ $? == 0 ]; then
  #         break
  #       fi
  #       sleep 4
  #     done
  #   fi
  # done
  # for i in $(cat hostname | head -n ${machines});do
  #   if [ ! "$i" == "$(hostname)" ]; then
  #     ssh $i "echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope"
  #     # scp -q -r fwi_src ${i}:
  #   fi
  # done

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
