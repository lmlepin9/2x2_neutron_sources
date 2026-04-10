#!/bin/bash
#
# Helper script: submit one sbatch job for one AmBe input file-list
#
# Usage:
#   ./submit_ambe_list.sh /full/path/to/input_file_list.txt [DEBUG]
#
# Example:
#   ./submit_ambe_list.sh ./AmBe_mod2_pmt_trigger_109us_period.txt 0
#

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 input_file_list.txt [DEBUG]"
    exit 1
fi

INPUT_LIST="$1"
DEBUG="${2:-0}"

if [ ! -f "${INPUT_LIST}" ]; then
    echo "ERROR: input file list does not exist: ${INPUT_LIST}"
    exit 1
fi

LIST_BASENAME=$(basename "${INPUT_LIST}")
LIST_STEM="${LIST_BASENAME%.txt}"
TIMESTAMP=$(date +"%Y%m%d_%H%M")
SLURM_JOB_NAME="${LIST_STEM}_${TIMESTAMP}"

echo "=========================================="
echo "Submitting AmBe file-list job"
echo "Input list:      ${INPUT_LIST}"
echo "DEBUG:           ${DEBUG}"
echo "Slurm job name:  ${SLURM_JOB_NAME}"
echo "Submit time:     $(date)"
echo "=========================================="

sbatch --job-name="${SLURM_JOB_NAME}" \
    submit_ambe_file_list.slurm \
    "${INPUT_LIST}" \
    "${DEBUG}"