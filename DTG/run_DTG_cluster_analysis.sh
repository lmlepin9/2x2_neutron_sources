#!/bin/bash

# Script to run DBScan cluster on AmBe files.


#---------------------------- Configure your job ------------------------------------------------------
DEBUG="${2:-1}"
JOB_NAME="DTG_data_test_03-30"
INPUT_DSET="./DTG_1212_files.txt"

OUTPUT_DIR="/pscratch/sd/l/${USER}/cluster_outputs/${JOB_NAME}_$(date +"%Y%m%d_%H%M%S")_clusters/"

LOG_DIR="/pscratch/sd/l/${USER}/cluster_logs/"
LOG_FILE="${LOG_DIR}${JOB_NAME}_$(date +"%Y%m%d_%H%M%S").log"

CHUNK_SIZE=2000
IS_CL="${1:-0}"
NOHUP_OPT=1


#----------------------------------------------------------------------------------------------------- 

if [[ "${IS_CL}" != "0" && "${IS_CL}" != "1" ]]; then
    echo "ERROR: CL toggle must be 0 or 1, got: ${IS_CL}"
    echo "Usage: $0 [cl:0|1] [debug:0|1]"
    exit 1
fi

if [[ "${DEBUG}" != "0" && "${DEBUG}" != "1" ]]; then
    echo "ERROR: DEBUG toggle must be 0 or 1, got: ${DEBUG}"
    echo "Usage: $0 [cl:0|1] [debug:0|1]"
    exit 1
fi

cd ../ || exit 1
source setup_env.sh
cd ./DTG || exit 1

echo "Creating output directory"
mkdir -p $OUTPUT_DIR

echo "Creating log directory"
mkdir -p ${LOG_DIR}

echo "CL mode: ${IS_CL}"
echo "Debug mode: ${DEBUG}"

if [ "$NOHUP_OPT" = 0 ]; then
    echo "Running DTG cluster analysis with nohup..."
    echo "Executing command:"
    echo "nohup python ./charge/process_DTG_data.py --input ${INPUT_DSET} --out ${OUTPUT_DIR} --cs ${CHUNK_SIZE} --cl ${IS_CL} --debug ${DEBUG} > ${LOG_FILE} 2>&1 &"
    nohup python ./charge/process_DTG_data.py --input ${INPUT_DSET} --out ${OUTPUT_DIR} --cs ${CHUNK_SIZE} --cl ${IS_CL} --debug ${DEBUG} > ${LOG_FILE} 2>&1 &
else
    echo "Running DTG cluster analysis..."
    echo "Executing command:"
    echo "python ./charge/process_DTG_data.py --input ${INPUT_DSET} --out ${OUTPUT_DIR} --cs ${CHUNK_SIZE} --cl ${IS_CL} --debug ${DEBUG}"
    python ./charge/process_DTG_data.py --input ${INPUT_DSET} --out ${OUTPUT_DIR} --cs ${CHUNK_SIZE} --cl ${IS_CL} --debug ${DEBUG}
fi 


EXIT_CODE=$?
echo "Process exited with code: $EXIT_CODE"

if [ $EXIT_CODE -gt 128 ]; then
    SIGNAL=$(($EXIT_CODE - 128))
    echo "Process was killed by signal: $SIGNAL"
fi
