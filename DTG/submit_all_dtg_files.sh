#!/bin/bash
#
# Helper script: submit one sbatch job per file listed in a text file
#
# Usage:
#   ./submit_all_dtg_files.sh DTG_1212_files.txt
#

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

while IFS= read -r this_file || [ -n "$this_file" ]; do
    [ -z "${this_file}" ] && continue
    echo "Submitting: ${this_file}"
    sbatch submit_dtg_single_file.slurm "${this_file}"
done < "${FILE_LIST}"