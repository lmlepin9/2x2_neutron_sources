#!/bin/bash
#
# DUNE GPVM job submission worker script
# One AmBe file-list per submission
#

set -euo pipefail

echo pwd

#INPUT_LIST="${1:?ERROR: missing input file list argument}"
INPUT_LIST="/exp/dune/app/users/edgarmao/2x2_neutron_sources/AmBe/one_pmt_trig_no_source_file_list.txt"
DEBUG="${2:-0}"

#OUTPUT_ROOT="/exp/dune/app/users/${USER}/neutron_cluster_outputs"
#LOG_DIR="/exp/dune/app/users/${USER}/neutron_cluster_logs"

OUTPUT_ROOT="/exp/dune/app/users/edgarmao/neutron_cluster_outputs"
LOG_DIR="/exp/dune/app/users/edgarmao/neutron_cluster_logs"

if [ ! -f "${INPUT_LIST}" ]; then
    echo "ERROR: input file list does not exist: ${INPUT_LIST}"
    echo "Current Location:"
    pwd
    exit 1
fi

mkdir -p "${OUTPUT_ROOT}"
mkdir -p "${LOG_DIR}"

LIST_BASENAME=$(basename "${INPUT_LIST}")
LIST_STEM="${LIST_BASENAME%.txt}"
LIST_STEM_LC=$(echo "${LIST_STEM}" | tr '[:upper:]' '[:lower:]')

###############################################################
# Infer config from filename
###############################################################

SINGLE_TRIGGER=1
USE_TRIGGER=0
PERIOD=320

if [[ "${LIST_STEM_LC}" == *period* ]]; then
    SINGLE_TRIGGER=0
fi

if [[ "${LIST_STEM_LC}" == *pmt_trigger* ]] || [[ "${LIST_STEM_LC}" == *trigger* ]]; then
    USE_TRIGGER=1
fi

if [[ "${LIST_STEM_LC}" =~ ([0-9]+)us ]]; then
    PERIOD="${BASH_REMATCH[1]}"
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M")

JOB_NAME="${LIST_STEM}_${TIMESTAMP}"
JOB_OUTPUT_DIR="${OUTPUT_ROOT}/${JOB_NAME}"
OUTPUT_FILE="${JOB_OUTPUT_DIR}/${LIST_STEM}_clusters.csv"

mkdir -p "${JOB_OUTPUT_DIR}"

# Count files listed inside the text file
N_INPUT_FILES=$(grep -v '^[[:space:]]*$' "${INPUT_LIST}" | grep -vc '^[[:space:]]*#' || true)

#--------------------------------------------------------------
# Setup environment
#--------------------------------------------------------------

cd /exp/dune/app/users/edgarmao/2x2_neutron_sources
source setup_env.sh
cd AmBe

echo "=========================================="
echo "Hostname:        $(hostname)"
echo "Start time:      $(date)"
echo "Input list:      ${INPUT_LIST}"
echo "Files:           ${N_INPUT_FILES}"
echo "Output:          ${OUTPUT_FILE}"
echo "=========================================="

python charge/process_CL_AmBe_data.py \
    --input "${INPUT_LIST}" \
    --out "${OUTPUT_FILE}" \
    --trig "${USE_TRIGGER}" \
    --st "${SINGLE_TRIGGER}" \
    --p "${PERIOD}" \
    --debug "${DEBUG}"

echo "Finished at $(date)"