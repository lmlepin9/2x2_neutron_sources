#!/bin/bash
#
# NERSC Perlmutter SLURM submission script
# One file per submission.
#
# Usage:
#   sbatch --job-name=MY_JOB_NAME submit_dtg_single_file.slurm /full/path/to/file.FLOW.hdf5 [cl:0|1] [debug:0|1]
#

# ------------------------------------------------------------------------------------
#SBATCH -A dune
#SBATCH -C cpu
#SBATCH -q regular
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH -t 00:01:00
#SBATCH -o /pscratch/sd/l/%u/cluster_logs/%x-%j.out
#SBATCH -e /pscratch/sd/l/%u/cluster_logs/%x-%j.err
# ------------------------------------------------------------------------------------

set -u

#---------------------------- Configure your job --------------------------------------
DEBUG="${3:-0}"
JOB_NAME="${SLURM_JOB_NAME}"

LOG_DIR="/pscratch/sd/l/${USER}/cluster_logs/"
CHUNK_SIZE=2000
IS_CL="${2:-0}"
#--------------------------------------------------------------------------------------

if [ "$#" -lt 1 ]; then
    echo "Usage: sbatch --job-name=MY_JOB_NAME $0 /full/path/to/input_file [cl:0|1] [debug:0|1]"
    exit 1
fi

INPUT_FILE="$1"

if [[ "${IS_CL}" != "0" && "${IS_CL}" != "1" ]]; then
    echo "ERROR: CL toggle must be 0 or 1, got: ${IS_CL}"
    exit 1
fi

if [[ "${DEBUG}" != "0" && "${DEBUG}" != "1" ]]; then
    echo "ERROR: DEBUG toggle must be 0 or 1, got: ${DEBUG}"
    exit 1
fi

if [ ! -f "${INPUT_FILE}" ]; then
    echo "ERROR: Input file does not exist: ${INPUT_FILE}"
    exit 1
fi

FILE_BASENAME=$(basename "${INPUT_FILE}")
FILE_STEM="${FILE_BASENAME%.*}"

OUTPUT_DIR="/pscratch/sd/l/${USER}/cluster_outputs/${JOB_NAME}_${SLURM_JOB_ID}"

echo "========== Job information =========="
echo "Job name          : ${SLURM_JOB_NAME}"
echo "Job ID            : ${SLURM_JOB_ID}"
echo "Node list         : ${SLURM_JOB_NODELIST}"
echo "Submit directory  : ${SLURM_SUBMIT_DIR}"
echo "Input file        : ${INPUT_FILE}"
echo "CL mode           : ${IS_CL}"
echo "Debug mode        : ${DEBUG}"
echo "Start time        : $(date)"
echo "====================================="

mkdir -p "${OUTPUT_DIR}"
mkdir -p "${LOG_DIR}"

cd "${SLURM_SUBMIT_DIR}" || exit 1

# Setup environment
cd ../ || exit 1
source setup_env.sh
cd ./DTG || exit 1

# Keep Python interface unchanged by creating a one-line input list
TMP_FILELIST="${OUTPUT_DIR}/input_${SLURM_JOB_ID}.txt"
printf "%s\n" "${INPUT_FILE}" > "${TMP_FILELIST}"

CMD="python ./charge/process_DTG_data.py --input ${TMP_FILELIST} --out ${OUTPUT_DIR} --cs ${CHUNK_SIZE} --cl ${IS_CL} --debug ${DEBUG}"

echo "Running DTG cluster analysis with srun..."
echo "Executing command:"
echo "srun ${CMD}"

srun ${CMD}
EXIT_CODE=$?

echo "Process exited with code: ${EXIT_CODE}"

if [ "${EXIT_CODE}" -gt 128 ]; then
    SIGNAL=$((${EXIT_CODE} - 128))
    echo "Process was killed by signal: ${SIGNAL}"
fi

echo "End time: $(date)"
exit "${EXIT_CODE}"
