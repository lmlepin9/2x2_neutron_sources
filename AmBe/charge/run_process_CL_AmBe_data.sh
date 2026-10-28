#!/usr/bin/env bash
# ======================================================================
#  run_ambe_clusters.sh
#  Wrapper for the AmBe CR cluster tool.
#  Edit the variables in the "USER OPTIONS" block, then run:
#       bash run_ambe_clusters.sh
# ======================================================================

#set -euo pipefail
set -o pipefail

# ------------------------- USER OPTIONS -------------------------------

# Repository root (the Python script reads this as $REPO_DIR)
REPO_DIR="/global/cfs/cdirs/dune/users/edgarmao/NeutronSourceAnalysis/2x2_neutron_sources"

# Python interpreter and the analysis script
PYTHON="python3"
SCRIPT="${REPO_DIR}/AmBe/charge/process_CL_AmBe_data.py"

# Text file listing input HDF5 files (one per line, '#' = comment)
INPUT_LIST="/global/cfs/cdirs/dune/users/edgarmao/two_trig_128us_period_filelist.txt"

# Base output CSV (must end in .csv). Per-file outputs are named
# <base>_<inputname>.csv, plus _prompt / _delayed variants.
OUTPUT_CSV="./Cluster_Results/ambe_two_trig_128us.csv"

# Use the PMT trigger selection?            1 = yes, 0 = no
USE_TRIGGER=1

# Single trigger (1) or prompt+delayed (0)  (only used if USE_TRIGGER=1)
SINGLE_TRIGGER=0

# Period between prompt and delayed trigger (only used if SINGLE_TRIGGER=0)
PERIOD=128

# Debug mode: process a random 10% subset.  1 = yes, 0 = no
DEBUG=1

# Log file (leave empty "" to print only to the terminal)
LOG_FILE="./output/ambe_clusters_128us.log"

# ----------------------- END USER OPTIONS -----------------------------


# ---------- Sanity checks ----------
[[ -d "$REPO_DIR"   ]] || { echo "ERROR: REPO_DIR not found: $REPO_DIR"; exit 1; }
[[ -f "$SCRIPT"     ]] || { echo "ERROR: script not found: $SCRIPT"; exit 1; }
[[ -f "$INPUT_LIST" ]] || { echo "ERROR: input list not found: $INPUT_LIST"; exit 1; }
[[ "$OUTPUT_CSV" == *.csv ]] || { echo "ERROR: OUTPUT_CSV must end in .csv"; exit 1; }

for v in USE_TRIGGER SINGLE_TRIGGER DEBUG; do
    [[ "${!v}" == "0" || "${!v}" == "1" ]] || { echo "ERROR: $v must be 0 or 1"; exit 1; }
done

mkdir -p "$(dirname "$OUTPUT_CSV")"
[[ -n "$LOG_FILE" ]] && mkdir -p "$(dirname "$LOG_FILE")"

export REPO_DIR

# ---------- Summary ----------
echo "================ AmBe cluster run ================"
echo " Script       : $SCRIPT"
echo " Input list   : $INPUT_LIST ($(grep -cv -e '^\s*#' -e '^\s*$' "$INPUT_LIST") files)"
echo " Output CSV   : $OUTPUT_CSV"
echo " Use trigger  : $USE_TRIGGER"
echo " Single trig  : $SINGLE_TRIGGER"
echo " Period       : $PERIOD"
echo " Debug        : $DEBUG"
echo " Log file     : ${LOG_FILE:-<none>}"
echo "=================================================="

CMD=( "$PYTHON" "$SCRIPT"
      --input "$INPUT_LIST"
      --out   "$OUTPUT_CSV"
      --trig  "$USE_TRIGGER"
      --st    "$SINGLE_TRIGGER"
      --p     "$PERIOD"
      --debug "$DEBUG" )

# ---------- Run ----------
START=$(date +%s)
if [[ -n "$LOG_FILE" ]]; then
    "${CMD[@]}" 2>&1 | tee "$LOG_FILE"
else
    "${CMD[@]}"
fi
echo "Done in $(( $(date +%s) - START )) s"