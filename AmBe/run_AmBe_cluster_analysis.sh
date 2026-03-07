#!/bin/bash

# Script to run DBScan cluster on AmBe files.


#---------------------------- Configure your job ------------------------------------------------------
DEBUG=1
JOB_NAME="no_source_32us_window_test"
INPUT_DSET="/global/cfs/cdirs/dune/users/lmlepin/neutron_source_CL_data/source_ambe_bin3/one_pmt_trig_no_source/"

OUTPUT_DIR="/pscratch/sd/l/${USER}/cluster_outputs/"
OUTPUT_FILE="${OUTPUT_DIR}${JOB_NAME}_$(date +"%Y%m%d_%H%M%S")_clusters.csv"

LOG_DIR="/pscratch/sd/l/${USER}/cluster_logs/"
LOG_FILE="${LOG_DIR}${JOB_NAME}_$(date +"%Y%m%d_%H%M%S").log"

SINGLE_TRIGGER=1
USE_TRIGGER=0
PERIOD=320
NOHUP_OPT=0


#----------------------------------------------------------------------------------------------------- 

echo "Creating output directory"
mkdir -p $OUTPUT_DIR

echo "Creating log directory"
mkdir -p ${LOG_DIR}

if [ "$NOHUP_OPT" = 0 ]; then
    echo "Running AmBe cluster with nohup..."
    echo "Executing command:"
    echo "nohup python ./charge/process_CL_AmBe_data.py --input ${INPUT_DSET} --out ${OUTPUT_FILE} --trig ${USE_TRIGGER} --st ${SINGLE_TRIGGER} --p ${PERIOD} --debug ${DEBUG} > ${LOG_FILE} 2>&1 &"
    nohup python ./charge/process_CL_AmBe_data.py --input ${INPUT_DSET} --out ${OUTPUT_FILE} --trig ${USE_TRIGGER} --st ${SINGLE_TRIGGER} --p ${PERIOD} --debug ${DEBUG} > ${LOG_FILE} 2>&1 &
else
    echo "Running AmBe cluster..."
    echo "Executing command:"
    echo "python ./charge/process_CL_AmBe_data.py --input ${INPUT_DSET} --out ${OUTPUT_FILE} --trig ${USE_TRIGGER} --st ${SINGLE_TRIGGER} --p ${PERIOD} --debug ${DEBUG}"
    python ./charge/process_CL_AmBe_data.py --input ${INPUT_DSET} --out ${OUTPUT_FILE} --trig ${USE_TRIGGER} --st ${SINGLE_TRIGGER} --p ${PERIOD} --debug ${DEBUG}
fi 

