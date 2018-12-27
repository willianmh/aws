#!/bin/bash

#source /opt/intel/compilers_and_libraries_2018.3.222/linux/bin/compilervars.sh -arch intel64 -platform linux
source ~/.bashrc

N_ITERATIONS=3

echo "pinging everyone to everyone"
mkdir -p pings
for host in $(cat private_ip)
do
  ssh $host ./ping.sh
done

cd ~/
rm -rf run_ball*
rm -rf run_marmousi*
cp -r toy2dac/run_marmousi_template/ .
cp private_ip run_marmousi_template/hostfile

echo "modeling"
cd run_marmousi_template/
sed -i 's/10        ! number of nonlinear iterations/20        ! number of nonlinear iterations' fwi_input
sed -i 's/vp_Marmousi_init qp rho epsilon_m delta_m theta_m/vp_Marmousi_exact qp rho/' fdfd_input
sed -i 's/0           ! Hicks interpolation (1 YES, 0 NO)/1           ! Hicks interpolation (1 YES, 0 NO)/' fdfd_input
sed -i 's/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input
sed -i '1s/^/0/' mumps_input
sed -i 's/1 !Nfreq/2 !Nfreq/' freq_management

ulimit -s unlimited

mpirun -n 4 ../toy2dac/bin/toy2dac >> ~/modeling_1.out

sed -i 's/vp_Marmousi_exact qp rho/vp_Marmousi_init qp rho/' fdfd_input
sed -i 's/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input

echo "copying run_marmousi to others workers"
cd ~/
./copy_all.sh run_marmousi_template

for i in `seq 1 ${N_ITERATIONS}`
do
  cd ~/run_marmousi_template
  echo "inversion"
  mpirun -n 8 -ppn 2 -genv OMP_NUM_THREADS=4 -genv I_MPI_PIN_DOMAIN=omp -f hostfile ../toy2dac/bin/toy2dac >> ~/inversion_${i}.out
  sleep 1
done
