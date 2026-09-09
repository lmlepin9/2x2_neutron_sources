#!/bin/bash
#
# Helper script for running charge_analysis_plots.py
#
# Usage:
#   ./run_charge_analysis_plots.sh
#
# Example:
#   ./run_charge_analysis_plots.sh
#

SOURCE_CSV="/global/cfs/cdirs/dune/users/lmlepin/cluster_outputs/AmBe_mod2_pmt_trigger_32us_period_20260409_1713/AmBe_mod2_pmt_trigger_32us_period_clusters_prompt.csv"
#SOURCE_CSV="/global/cfs/cdirs/dune/users/edgarmao/NeutronSim/Analysis/2x2_neutron_sources/AmBe/output/eps1_minsamples4/ambe_bin2_one_trig_32us_window_eps1size4.csv"
#SOURCE_CSV="/global/cfs/cdirs/dune/users/lmlepin/cluster_outputs/AmBe_mod2_pmt_trigger_195us_period_20260409_1557/AmBe_mod2_pmt_trigger_195us_period_clusters_prompt.csv"
SOURCE_HDF5_DIRECTORY="/pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin2/one_trig_32us_window"
#SOURCE_HDF5_DIRECTORY="/pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_195us_period"

NOSOURCE_CSV="/global/cfs/cdirs/dune/users/lmlepin/cluster_outputs/no_source_32us_window_20260309_070118_clusters.csv"
#NOSOURCE_CSV="/global/cfs/cdirs/dune/users/edgarmao/NeutronSim/Analysis/2x2_neutron_sources/AmBe/output/eps1_minsamples4/nosource_ambe_bin2_one_trig_32us_window_eps1size4.csv"
NOSOURCE_HDF5_DIRECTORY="/pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/one_pmt_trig_no_source"

OUTPUT_DIR="/pscratch/sd/e/edgarmao/AmBe_analysis_outputs/"

DEBUG=false

# Cluster quality cuts: (min_hits, min_energy [MeV], max_energy [MeV])
CLUSTER_MIN_HITS=4
CLUSTER_MIN_ENERGY=0.0
CLUSTER_MAX_ENERGY=None

# Disable HDF5 file locking
export HDF5_USE_FILE_LOCKING=FALSE

# Run Analysis

if $DEBUG; then
    python charge_analysis_plots.py \
        --source "$SOURCE_CSV" \
        --background "$NOSOURCE_CSV" \
        --source-directory "$SOURCE_HDF5_DIRECTORY" \
        --background-directory "$NOSOURCE_HDF5_DIRECTORY" \
        --cluster_quality_cut $CLUSTER_MIN_HITS $CLUSTER_MIN_ENERGY $CLUSTER_MAX_ENERGY\
        --output "$OUTPUT_DIR" \
        --debug
elif ! $DEBUG; then
    python charge_analysis_plots.py \
        --source "$SOURCE_CSV" \
        --background "$NOSOURCE_CSV" \
        --source-directory "$SOURCE_HDF5_DIRECTORY" \
        --background-directory "$NOSOURCE_HDF5_DIRECTORY" \
        --cluster_quality_cut $CLUSTER_MIN_HITS $CLUSTER_MIN_ENERGY $CLUSTER_MAX_ENERGY\
        --output "$OUTPUT_DIR"
fi