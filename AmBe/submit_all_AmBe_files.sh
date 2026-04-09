#!/bin/bash
#
# Helper script: submit one sbatch job per AmBe file listed in a text file
#
# Usage:
#   ./submit_all_ambe_files.sh AmBe_mod2_pmt_trigger_109us_period.txt
#

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 input_file_list.txt"
    exit 1
fi

FILE_LIST="$1"

if [ ! -f "${FILE_LIST}" ]; then
    echo "ERROR: File list does not exist: ${FILE_LIST}"
    exit 1
fi

# ---------------------------- Configure your job ----------------------------
DEBUG=1
USE_TRIGGER=1
# SINGLE_TRIGGER and PERIOD are inferred from FILE_LIST name
# ----------------------------------------------------------------------------

TIMESTAMP=$(date +"%Y%m%d_%H%M")
BASE_NAME=$(basename "${FILE_LIST}" .txt)

# ---------------- Infer SINGLE_TRIGGER from file list name ----------------
if [[ "${BASE_NAME}" == *"period"* ]]; then
    SINGLE_TRIGGER=0
else
    SINGLE_TRIGGER=1
fi

# ---------------- Extract PERIOD from file list name ----------------
# More robust match: looks for _109us, _32us, etc.
if [[ "${BASE_NAME}" =~ _([0-9]+)us ]]; then
    PERIOD="${BASH_REMATCH[1]}"
else
    echo "ERROR: Could not extract PERIOD from file list name: ${BASE_NAME}"
    echo "Expected something like: ..._109us_..."
    exit 1
fi

JOB_NAME="${BASE_NAME}_${TIMESTAMP}"

echo "=========================================="
echo "File list:        ${FILE_LIST}"
echo "Base name:        ${BASE_NAME}"
echo "Job name:         ${JOB_NAME}"
echo "DEBUG:            ${DEBUG}"
echo "USE_TRIGGER:      ${USE_TRIGGER}"
echo "SINGLE_TRIGGER:   ${SINGLE_TRIGGER}"
echo "PERIOD:           ${PERIOD}"
echo "=========================================="
echo

n_submit=0

while IFS= read -r this_file || [ -n "${this_file}" ]; do
    # Skip empty lines
    [ -z "${this_file}" ] && continue

    # Skip commented lines
    [[ "${this_file}" =~ ^[[:space:]]*# ]] && continue

    if [ ! -f "${this_file}" ]; then
        echo "WARNING: Skipping missing file: ${this_file}"
        continue
    fi

    echo "Submitting: ${this_file}"

    sbatch --job-name="${JOB_NAME}" \
        submit_AmBe_single_file.slurm \
        "${this_file}" \
        "${JOB_NAME}" \
        "${DEBUG}" \
        "${SINGLE_TRIGGER}" \
        "${USE_TRIGGER}" \
        "${PERIOD}"

    n_submit=$((n_submit + 1))
done < "${FILE_LIST}"

echo
echo "Submitted ${n_submit} jobs."