#!/bin/bash

set -u

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 file_list.txt"
    exit 1
fi

FILE_LIST="$1"

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

while IFS= read -r this_file || [ -n "${this_file}" ]; do
    [ -z "${this_file}" ] && continue
    echo "Submitting: ${this_file}"
    sbatch --job-name="${JOB_NAME}" submit_dtg_single_file.slurm "${this_file}"
done < "${FILE_LIST}"