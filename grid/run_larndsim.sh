#!/bin/bash

echo "Printing gpu details..."
nvidia-smi 


# Using up-to-date larnd-sim and flow 
export TOP_DIR='/pscratch/sd/l/lmlepin/2x2_sim_main/2x2_sim'
source $TOP_DIR/util/init.inc.sh
source $TOP_DIR/run-larnd-sim/larnd.venv/bin/activate


# Create working directory
export WORK_DIR="${WORK_TOP_DIR}/${TYPE}_${PROJECT_NAME}_${JOB}"
mkdir -p $WORK_DIR


export OUT_FILE_LARNDSIM="2x2_${PS_LIST}_${TYPE}_${PROJECT_NAME}_${JOB}.LARNDSIM.hdf5"

cd $WORK_DIR

# This will create the larnd-sim directly into the output directory 
echo "Running larnd-sim..."

if [ "$TYPE" = "AmBe" ]; then 
       python3 ${TOP_DIR}/run-larnd-sim/larnd-sim/cli/simulate_pixels.py --config 2x2 --input_filename ${OUT_FILE_HDF5} --output_filename ${OUT_FILE_LARNDSIM}
else
       python3 ${TOP_DIR}/run-larnd-sim/larnd-sim/cli/simulate_pixels.py --config 2x2 --input_filename ${OUT_FILE_HDF5} --output_filename ${OUT_FILE_LARNDSIM}                                 
fi

# deactivate larnd-sim venv and activate nd-flow venv 
deactivate

echo "Loading libraries..."
module unload python 2>/dev/null
module load python/3.11
source $TOP_DIR/util/init.inc.sh
source $TOP_DIR/run-ndlar-flow/flow.venv/bin/activate

export FLOW_TOP_DIR="${TOP_DIR}/run-ndlar-flow/ndlar_flow"



# charge workflows
workflow1="${FLOW_TOP_DIR}/yamls/proto_nd_flow/workflows/charge/charge_event_building_mc.yaml"
workflow2="${FLOW_TOP_DIR}/yamls/proto_nd_flow/workflows/charge/charge_event_reconstruction_mc.yaml"
workflow3="${FLOW_TOP_DIR}/yamls/proto_nd_flow/workflows/combined/combined_reconstruction_mc.yaml"
workflow4="${FLOW_TOP_DIR}/yamls/proto_nd_flow/workflows/charge/prompt_calibration_mc.yaml"
workflow5="${FLOW_TOP_DIR}/yamls/proto_nd_flow/workflows/charge/final_calibration_mc.yaml"

# light workflows
workflow6="${FLOW_TOP_DIR}/yamls/proto_nd_flow/workflows/light/light_event_building_mc.yaml"
workflow7="${FLOW_TOP_DIR}/yamls/proto_nd_flow/workflows/light/light_event_reconstruction_mc.yaml"

# charge-light trigger matching
workflow8="${FLOW_TOP_DIR}/yamls/proto_nd_flow/workflows/charge/charge_light_assoc_mc.yaml"

OUT_FILE_FLOW="2x2_${PS_LIST}_${TYPE}_${PROJECT_NAME}_${JOB}.FLOW.hdf5"

echo "Running flow..."
cd $FLOW_TOP_DIR

# Enable LZF compression of output file
opts="-z lzf"


h5flow $opts -c $workflow1 $workflow2 $workflow3 $workflow4 $workflow5\
       -i "$WORK_DIR/$OUT_FILE_LARNDSIM" -o "$OUT_DIR_FLOW/$OUT_FILE_FLOW"

h5flow $opts -c $workflow6 $workflow7\
       -i "$WORK_DIR/$OUT_FILE_LARNDSIM" -o "$OUT_DIR_FLOW/$OUT_FILE_FLOW"

h5flow $opts -c $workflow8 -i "$OUT_DIR_FLOW/$OUT_FILE_FLOW" -o "$OUT_DIR_FLOW/$OUT_FILE_FLOW"

cd $WORK_DIR

# Move products to output directories
mv $OUT_FILE_LARNDSIM $OUT_DIR_LARNDSIM