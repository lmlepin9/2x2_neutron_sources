#!/bin/bash

set -u

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 file_list.txt [cl:0|1] [debug:0|1]"
    exit 1
fi

FILE_LIST="$1"
IS_CL="${2:-0}"
DEBUG="${3:-0}"

if [[ "${IS_CL}" != "0" && "${IS_CL}" != "1" ]]; then
    echo "ERROR: CL toggle must be 0 or 1, got: ${IS_CL}"
    exit 1
fi

if [[ "${DEBUG}" != "0" && "${DEBUG}" != "1" ]]; then
    echo "ERROR: DEBUG toggle must be 0 or 1, got: ${DEBUG}"
    exit 1
fi

if [ ! -f "${FILE_LIST}" ]; then
    echo "ERROR: File list does not exist: ${FILE_LIST}"
    exit 1
fi

# Extract base name (remove path and .txt)
FILE_LIST_NAME=$(basename "${FILE_LIST}")
FILE_LIST_STEM="${FILE_LIST_NAME%.txt}"

# Current date + hour + minute
DATE_STR=$(date +"%Y%m%d_%H%M")

# Final job name
JOB_NAME="${FILE_LIST_STEM}_${DATE_STR}"

echo "Using job name: ${JOB_NAME}"
echo "CL mode: ${IS_CL}"
echo "Debug mode: ${DEBUG}"

while IFS= read -r this_file || [ -n "${this_file}" ]; do
    [ -z "${this_file}" ] && continue
    echo "Submitting: ${this_file}"
    sbatch --job-name="${JOB_NAME}" submit_dtg_single_file.slurm "${this_file}" "${IS_CL}" "${DEBUG}"
done < "${FILE_LIST}"
