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
export OUT_FILE_SPILL="2x2_${PS_LIST}_${TYPE}_${timestamp}_${JOB}_spill.root"
export IS_SPILL=1
export PULSE_PERIOD=1.2
export MAC_FILE="${TOP_DIR}/run-edep-sim/macros/2x2_AmBe_OUT.mac"


# Create working directory
export WORK_DIR="${WORK_TOP_DIR}/${TYPE}_${timestamp}_${JOB}"
mkdir -p $WORK_DIR

cd $WORK_DIR 
echo $PWD 

echo "The following edep-sim command will be executed..."
echo "edep-sim -g ${ARCUBE_GEOM} -o ${OUT_FILE_ROOT} -p ${PS_LIST} -u -e ${NEVENTS} ${MAC_FILE}"
edep-sim -C -g "$ARCUBE_GEOM" -o "$OUT_FILE_ROOT" -p "$PS_LIST" -e "$NEVENTS" "$MAC_FILE"

# Filter for captures 
echo "Runnning neutron capture filter..."
root -l -b -q  "/pscratch/sd/l/lmlepin/2x2_sim_develop/2x2_sim/batch-jobs/filter_capture_events_v2.C(\"${OUT_FILE_ROOT}\",\"${OUT_FILE_SPILL}\", ${IS_SPILL}, ${JOB}, ${PULSE_PERIOD})"


# Here we perform the conversion from .root to hdf5 
echo "Running convert2h5 now..."

# After going from ROOT 6.14.06 to 6.28.06, apparently we need to point CPATH to
# the edepsim-io headers. Otherwise convert2h5 fails. (This "should" be set in
# the container already.)
export CPATH=$EDEPSIM/include/EDepSim:$CPATH

python3 ${TOP_DIR}/run-convert2h5/convert_edepsim_roottoh5.py --input_file "$OUT_FILE_SPILL" --output_file "$OUT_FILE_HDF5" --gps True 

# Clean temp filtered file
rm ${OUT_FILE_SPILL}

# Move edepsim outputs to output dir 
mv $OUT_FILE_ROOT $OUT_FILE_HDF5 $OUT_DIR_EDEPSIM
