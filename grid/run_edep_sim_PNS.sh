#!/bin/bash

echo "Running edep-sim, this are the variables used:"
echo "NEVENTS: ${NEVENTS}"
echo "PHYSLIST: ${PS_LIST}"
echo "SOURCE: ${TYPE}"
echo "JOB NUM: ${JOB}"

timestamp=$(date +%s)

source $SCRATCH/setup_2x2_container.sh 
export ARCUBE_GEOM='/pscratch/sd/l/lmlepin/2x2_sim_develop/2x2_sim/geometry/Merged2x2MINERvA_v4_noRock_2x2_only_sense.gdml'
export TOP_DIR='/pscratch/sd/l/lmlepin/2x2_sim_develop/2x2_sim'
export OUT_FILE_ROOT="2x2_${PS_LIST}_${TYPE}_${timestamp}_${JOB}.root"
export OUT_FILE_HDF5="2x2_${PS_LIST}_${TYPE}_${timestamp}_${JOB}.EDEPSIM.hdf5"
export MAC_FILE="${TOP_DIR}/run-edep-sim/macros/2x2_DTG_single_updated.mac "

# Replace energy value 
# sed -i 's/\${energy}/'$ENERGY'/g' $MAC_FILE

# Create working directory
export WORK_DIR="${WORK_TOP_DIR}/${TYPE}_${timestamp}_${JOB}"
mkdir -p $WORK_DIR

cd $WORK_DIR 
echo $PWD 

echo "The following edep-sim command will be executed..."
echo "edep-sim -g ${ARCUBE_GEOM} -o ${OUT_FILE_ROOT} -p ${PS_LIST} -u -e ${NEVENTS} ${MAC_FILE}"
edep-sim -C -g "$ARCUBE_GEOM" -o "$OUT_FILE_ROOT" -p "$PS_LIST" -e "$NEVENTS" "$MAC_FILE"

# RUN NEUTRON SPILL BUILDER

export FILE_ID=1
export PULSE_PERIOD=1.2 # in s
export ACC_VOLTAGE=40
export CURRENT=20
export FREQUENCY=10000.0
export DUTY_FACTOR=0.05
export OUT_FILE_SPILL="${OUT_DIR}/MR5_DTG_sim_updated_distribution.root"

root -l -b -q  -e "gSystem->Load(\"$LIBTG4EVENT_DIR/libTG4Event.so\")" \
                  "${TOP_DIR}/batch-jobs/create_neutron_pulses.C(\"${OUT_FILE_ROOT}\",${FILE_ID}, ${PULSE_PERIOD},${ACC_VOLTAGE}, ${CURRENT}, ${FREQUENCY}, ${DUTY_FACTOR})"

# Here we perform the conversion from .root to hdf5 
echo "Running convert2h5 now..."

# After going from ROOT 6.14.06 to 6.28.06, apparently we need to point CPATH to
# the edepsim-io headers. Otherwise convert2h5 fails. (This "should" be set in
# the container already.
export CPATH=$EDEPSIM/include/EDepSim:$CPATH

python3 ${TOP_DIR}/run-convert2h5/convert_edepsim_roottoh5.py --input_file 2x2_DTG_edepsim_rectified_spill.root --output_file "$OUT_FILE_HDF5" "$keepAllDets" --gps True

# Clean temp filtered file
rm 2x2_DTG_edepsim_rectified_spill.root

# Move edepsim outputs to output dir 
mv $OUT_FILE_ROOT $OUT_FILE_HDF5 $OUT_DIR_EDEPSIM