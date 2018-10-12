#!/bin/bash

set -x
source /opt/intel/compilers_and_libraries_2018.3.222/linux/bin/compilervars.sh -arch intel64 -platform linux
source /opt/intel/parallel_studio_xe_2018.3.051/bin/psxevars.sh

TOTAL_CORES=$1

./firstscript.sh

mkdir -p pings
for host in $(cat private_ip)
do
  ping -c 15 $host >> pings/ping_$(hostname)_to_${host} &
done


rm -r run_ball*
rm -r run_marmousi*
cp -r toy2dac/run_marmousi_template/ .
cp private_ip run_marmousi_template/hostfile


cd run_marmousi_template/
sed -i 's/vp_Marmousi_init qp rho epsilon_m delta_m theta_m/vp_Marmousi_exact qp rho/' fdfd_input
sed -i 's/0           ! Hicks interpolation (1 YES, 0 NO)/1           ! Hicks interpolation (1 YES, 0 NO)/' fdfd_input
sed -i 's/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input

ulimit -s 65536

mpirun -n 4 ../toy2dac/bin/toy2dac >> modeling.out

sed -i 's/vp_Marmousi_exact qp rho/vp_Marmousi_init qp rho/' fdfd_input
sed -i 's/0            ! mode of the code (0 = MODELING, 1 = INVERSION)/1            ! mode of the code (0 = MODELING, 1 = INVERSION)/' toy2dac_input

cd ~/

for host in $(cat private_ip)
do
  scp -r run_marmousi_template $host:
done

cd run_marmousi_template

mpirun -n $TOTAL_CORES -f hostfile ../toy2dac/bin/toy2dac >> inversion.out
