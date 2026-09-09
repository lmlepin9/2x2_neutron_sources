#!/bin/bash
#
# NERSC Perlmutter SLURM submission script
# One AmBe file-list per submission
#
# Usage:
#   sbatch submit_ambe_file_list.slurm /full/path/to/input_file_list.txt [DEBUG]
#
# Example:
#   sbatch submit_ambe_file_list.slurm ./AmBe_mod2_pmt_trigger_109us_period.txt 0
#

#SBATCH -A dune
#SBATCH -C cpu
#SBATCH -q debug
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH -t 00:30:00
#SBATCH -o /pscratch/sd/e/%u/cluster_logs/%x-%j.out
#SBATCH -e /pscratch/sd/e/%u/cluster_logs/%x-%j.err

set -euo pipefail

INPUT_LIST="${1:?ERROR: missing input file list argument}"
DEBUG="${2:-0}"

OUTPUT_ROOT="/pscratch/sd/e/${USER}/cluster_outputs"
LOG_DIR="/pscratch/sd/e/${USER}/cluster_logs"

if [ ! -f "${INPUT_LIST}" ]; then
    echo "ERROR: input file list does not exist: ${INPUT_LIST}"
    exit 1
fi

mkdir -p "${OUTPUT_ROOT}"
mkdir -p "${LOG_DIR}"

LIST_BASENAME=$(basename "${INPUT_LIST}")
LIST_STEM="${LIST_BASENAME%.txt}"
LIST_STEM_LC=$(echo "${LIST_STEM}" | tr '[:upper:]' '[:lower:]')

# ------------------------------------------------------------
# Infer config from input list name
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Setup environment
# ------------------------------------------------------------
cd ../ || exit 1
source setup_env.sh
cd ./AmBe || exit 1

echo "=========================================="
echo "Running AmBe clustering job"
echo "Hostname:         $(hostname)"
echo "Start time:       $(date)"
echo "Input file list:  ${INPUT_LIST}"
echo "List basename:    ${LIST_BASENAME}"
echo "Files in list:    ${N_INPUT_FILES}"
echo "Job output dir:   ${JOB_OUTPUT_DIR}"
echo "Combined output:  ${OUTPUT_FILE}"
echo "SLURM_JOB_ID:     ${SLURM_JOB_ID}"
echo "=========================================="

echo "Inferred config:"
echo "  DEBUG=${DEBUG}"
echo "  SINGLE_TRIGGER=${SINGLE_TRIGGER}"
echo "  USE_TRIGGER=${USE_TRIGGER}"
echo "  PERIOD=${PERIOD}"

python ./charge/process_CL_AmBe_data.py \
    --input "${INPUT_LIST}" \
    --out "${OUTPUT_FILE}" \
    --trig "${USE_TRIGGER}" \
    --st "${SINGLE_TRIGGER}" \
    --p "${PERIOD}" \
    --debug "${DEBUG}"

echo "Finished at: $(date)"
