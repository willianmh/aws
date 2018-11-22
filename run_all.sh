#!/bin/bash

# source /opt/intel/compilers_and_libraries_2018.3.222/linux/bin/compilervars.sh -arch intel64 -platform linux
source /opt/intel/parallel_studio_xe_2019.1.053/bin/psxevars.sh

echo -e "pinging everyone to everyone"
for host in $(cat private_ip)
do
  ssh $host ./ping.sh &
done

wait

mkdir -p latency
for host in $(cat private_ip)
do
  scp -qr $host:pings/* latency
done

cd ~/

cp private_ip fwi_toy2dac/
cp private_ip fwi_src/

ulimit -s unlimited

echo -e "modeling"
cd fwi_toy2dac/
sed -i 's/marmousi_init_751_2301.bin qp rho/marmousi_exact_751_2301.bin qp rho/' fdfd_input
sed -i 's/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input

cd ~/
./copy_all.sh fwi_toy2dac
cd fwi_toy2dac
head -n 8 private_ip > hostfile
# mpirun -n 32 -ppn 4 -f hostfile ../toy2dac/bin/toy2dac

sed -i 's/marmousi_exact_751_2301.bin qp rho/marmousi_init_751_2301.bin qp rho/' fdfd_input
sed -i 's/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input

cd ~/
./copy_all.sh fwi_toy2dac
./copy_all.sh fwi_src

for machines in 64 52 40 36 32 28 24 20 16 12 8 4 2 1
do

  cd ~/
  n_stop=$((64-${machines}))

  echo -e "stopping ${n_stop} machines"
  tail -n ${n_stop} instances_ids > instances_to_stop # from the alive, stop some of them
  # python3 aws/stop.py instances_to_stop

  # head -n ${machines} instances_ids | tail -n $((${machines}-1)) > instances_to_start
  # python3 aws/start.py instances_to_start

  # tar -xzf fwi_toy2dac.tar.gz fwi_toy2dac
  # tar -xzf fwi_src.tar.gz fwi_src

  # echo -e "copying run_marmousi to others workers"
  # python3 aws/transfer.py instances_to_start willkey.pem fwi_src.tar.gz fwi_toy2dac.tar.gz
  # python3 aws/execute.py instances_to_start willkey.pem 'tar -xzf fwi_src.tar.gz' 'tar -xzf fwi_toy2dac.tar.gz'

  # for i in $(cat hostname | head -n ${machines});do
  #   if [ ! "$i" == "$(hostname)" ]; then
  #     for attempts in `seq 1 10`; do
  #       scp -q -r fwi_toy2dac ${i}:
  #       if [ $? == 0 ]; then
  #         break
  #       fi
  #       sleep 4
  #     done
  #   fi
  # done
  # for i in $(cat hostname | head -n ${machines});do
  #   if [ ! "$i" == "$(hostname)" ]; then
  #     ssh $i "echo -e 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope"
  #     # scp -q -r fwi_src ${i}:
  #   fi
  # done

  echo -e "executing with ${machines} machines"
  for ppn in 1 2 4 8
  do
    echo -e "\tppn ${ppn}"
    total_processes=$((${machines}*${ppn}))
    omp=$((8/$ppn))
    result_dir_toy2dac=/home/ubuntu/results/toy2dac/
    result_dir_fwi=/home/ubuntu/results/joe_fwi/

    mkdir -p ${result_dir_toy2dac}
    mkdir -p ${result_dir_fwi}

    cd ~/fwi_src/examples
    cat ~/private_ip | head -n ${machines} > hostfile
    echo -e "\t- Runnign fwi joe"
    for i in `seq 1 3`; do
      echo -e "\t\titeration ${i}"
      ./run_marmousi_141_681.sh $ppn $machines 5 160 ${result_dir_fwi}/time_m${machines}_ppn${ppn}_${i}.out >> ${result_dir_fwi}/fwi_m${machines}_ppn${ppn}_${i}.out
    done

    # cd ~/fwi_toy2dac/
    # cat private_ip | head -n ${machines} > hostfile
    # echo -e "\t- Runnign toy2dac"
    # for i in `seq 1 3`; do
    #   echo -e "\t\titeration ${i}"
    #   mpirun -n ${total_processes} \
    #   -ppn ${ppn} \
    #   -genv OMP_NUM_THREADS=${omp} \
    #   -genv I_MPI_PIN_DOMAIN=omp \
    #   -f hostfile ~/toy2dac/bin/toy2dac >> ${result_dir_toy2dac}/inversion_m${machines}_ppn${ppn}_${i}.out
    # done
    sleep 1
  done
done
