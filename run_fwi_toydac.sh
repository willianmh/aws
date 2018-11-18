#!/bin/bash

source /opt/intel/compilers_and_libraries_2018.3.222/linux/bin/compilervars.sh -arch intel64 -platform linux
source /opt/intel/parallel_studio_xe_2018.3.051/bin/psxevars.sh

TOTAL_CORES=$1
N_ITERATIONS=$2
OMP=$((${TOTAL_CORES}/4))
echo "total cores: $TOTAL_CORES"
./firstscript.sh

echo "pinging everyone to everyone"
mkdir -p pings
for host in $(cat private_ip)
do
  ssh $host ./ping.sh
done

echo "*** case 1 ***"

for i in `seq 1 ${N_ITERATIONS}`
do
  echo "iteration $i"
  cd ~/
  rm -r run_ball*
  rm -r run_marmousi*
  cp -r toy2dac/run_marmousi_template/ .
  cp private_ip run_marmousi_template/hostfile

  echo "modeling"
  cd run_marmousi_template/
  sed -i 's/vp_Marmousi_init qp rho epsilon_m delta_m theta_m/vp_Marmousi_exact qp rho/' fdfd_input
  sed -i 's/0           ! Hicks interpolation (1 YES, 0 NO)/1           ! Hicks interpolation (1 YES, 0 NO)/' fdfd_input
  sed -i 's/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input

  ulimit -s 65536

  mpirun -n 4 ../toy2dac/bin/toy2dac >> ~/modeling_1_${i}.out

  sed -i 's/vp_Marmousi_exact qp rho/vp_Marmousi_init qp rho/' fdfd_input
  sed -i 's/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input

  cd ~/
  echo "copying run_marmousi to others workers"
  for host in $(cat private_ip)
  do
    scp -r run_marmousi_template $host:
  done

  cd run_marmousi_template
  echo "inversion"

  mpirun -n $TOTAL_CORES -f hostfile -genv OMP_NUM_THREADS=1 -genv I_MPI_PIN_DOMAIN=omp ../toy2dac/bin/toy2dac >> ~/inversion_1_${i}.out
  sleep 1
done

echo "*** case 2 ***"

for i in `seq 1 ${N_ITERATIONS}`
do
  echo "iteration $i"
  cd ~/

  rm -r run_ball*
  rm -r run_marmousi*
  cp -r toy2dac/run_marmousi_template/ .
  cp private_ip run_marmousi_template/hostfile

  echo "modeling"
  cd run_marmousi_template/
  sed -i 's/vp_Marmousi_init qp rho epsilon_m delta_m theta_m/vp_Marmousi_exact qp rho/' fdfd_input
  sed -i 's/0           ! Hicks interpolation (1 YES, 0 NO)/1           ! Hicks interpolation (1 YES, 0 NO)/' fdfd_input
  sed -i 's/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input

  ulimit -s 65536

  mpirun -n 4 ../toy2dac/bin/toy2dac >> ~/modeling_2_${i}.out

  sed -i 's/vp_Marmousi_exact qp rho/vp_Marmousi_init qp rho/' fdfd_input
  sed -i 's/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input

  cd ~/
  echo "copying run_marmousi to others workers"
  for host in $(cat private_ip)
  do
    scp -r run_marmousi_template $host:
  done

  cd run_marmousi_template
  echo "inversion"

  mpirun -n 4 -ppn 1 -genv OMP_NUM_THREADS=${OMP} -genv I_MPI_PIN_DOMAIN=omp -f hostfile ../toy2dac/bin/toy2dac >> ~/inversion_2_${i}.out
  sleep 1
done