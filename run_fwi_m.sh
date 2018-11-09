#!/bin/bash

N_ITERATIONS=$1

source /opt/intel/compilers_and_libraries_2018.3.222/linux/bin/compilervars.sh -arch intel64 -platform linux
source /opt/intel/parallel_studio_xe_2018.3.051/bin/psxevars.sh

#./firstscript.sh

# echo "pinging everyone to everyone"
# mkdir -p pings
# for host in $(cat private_ip)
# do
#   ssh $host ./ping.sh
# done

for i in 1 2 4 6 8 12 24 48
do
  N_MPI=${i}
  N_OMP=$((48/${i}))
  echo "running case: ${N_MPI} mpi and ${N_OMP} openmp"
  for j in `seq 1 ${N_ITERATIONS}`
  do
    echo "iteration $j"
    cd ~/
    rm -rf run_ball*
    rm -rf run_marmousi*
    cp -r toy2dac/run_marmousi_template/ .
    cp private_ip run_marmousi_template/hostfile

    echo "modeling"
    cd run_marmousi_template/
    sed -i 's/vp_Marmousi_init qp rho epsilon_m delta_m theta_m/vp_Marmousi_exact qp rho/' fdfd_input
    sed -i 's/0           ! Hicks interpolation (1 YES, 0 NO)/1           ! Hicks interpolation (1 YES, 0 NO)/' fdfd_input
    sed -i 's/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input

    ulimit -s 65536

    mpirun -n 4 ../toy2dac/bin/toy2dac >> ~/modeling_${i}_${j}.out

    sed -i 's/vp_Marmousi_exact qp rho/vp_Marmousi_init qp rho/' fdfd_input
    sed -i 's/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input

    # echo "copying run_marmousi to others workers"
    # cd ~/
    # for host in $(cat private_ip)
    # do
    #   scp -r run_marmousi_template $host:
    # done

    # cd run_marmousi_template
    echo "inversion"

    mpirun -n ${N_MPI} -genv OMP_NUM_THREADS=${N_OMP} -genv I_MPI_PIN_DOMAIN=omp ../toy2dac/bin/toy2dac >> ~/inversion_${i}_${j}.out
    sleep 1
  done
done
