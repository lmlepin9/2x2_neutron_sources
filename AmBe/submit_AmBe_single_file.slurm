#!/bin/bash
#
# NERSC Perlmutter SLURM submission script
# One AmBe input file per submission
#
# Usage:
#   sbatch submit_ambe_single_file.slurm /full/path/to/input_file.hdf5 JOB_NAME
#

#SBATCH -A dune
#SBATCH -C cpu
#SBATCH -q regular
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH -t 02:00:00
#SBATCH -o /pscratch/sd/l/%u/cluster_logs/%x-%j.out
#SBATCH -e /pscratch/sd/l/%u/cluster_logs/%x-%j.err

set -euo pipefail

INPUT_FILE="${1:?ERROR: missing input file argument}"
JOB_NAME_ARG="${2:-ambe_job}"
DEBUG="${3:-0}"
SINGLE_TRIGGER="${4:-1}"
USE_TRIGGER="${5:-0}"
PERIOD="${6:-320}"

OUTPUT_ROOT="/pscratch/sd/l/${USER}/cluster_outputs"
LOG_DIR="/pscratch/sd/l/${USER}/cluster_logs"
JOB_OUTPUT_DIR="${OUTPUT_ROOT}/${JOB_NAME_ARG}"

mkdir -p "${OUTPUT_ROOT}"
mkdir -p "${LOG_DIR}"
mkdir -p "${JOB_OUTPUT_DIR}"

INPUT_BASENAME=$(basename "${INPUT_FILE}")
INPUT_STEM="${INPUT_BASENAME%.FLOW.hdf5}"

OUTPUT_FILE="${JOB_OUTPUT_DIR}/${INPUT_STEM}_clusters.csv"

# Setup python environment
source "$HOME/lm_env/bin/activate"

# Setup neutron_env
cd ../ || exit 1
source setup_env.sh
cd ./AmBe || exit 1

echo "=========================================="
echo "Running AmBe clustering job"
echo "Hostname:        $(hostname)"
echo "Start time:      $(date)"
echo "Input file:      ${INPUT_FILE}"
echo "Job name arg:    ${JOB_NAME_ARG}"
echo "Output dir:      ${JOB_OUTPUT_DIR}"
echo "Output file:     ${OUTPUT_FILE}"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "=========================================="

echo "Config:"
echo "  DEBUG=${DEBUG}"
echo "  SINGLE_TRIGGER=${SINGLE_TRIGGER}"
echo "  USE_TRIGGER=${USE_TRIGGER}"
echo "  PERIOD=${PERIOD}"

python ./charge/process_CL_AmBe_data.py \
    --input "${INPUT_FILE}" \
    --out "${OUTPUT_FILE}" \
    --trig "${USE_TRIGGER}" \
    --st "${SINGLE_TRIGGER}" \
    --p "${PERIOD}" \
    --debug "${DEBUG}"

echo "Finished at: $(date)"