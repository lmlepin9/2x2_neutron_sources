#!/bin/bash
#
# Helper script for running Combine_CSVs.py
#

# Disable HDF5 file locking
export HDF5_USE_FILE_LOCKING=FALSE

#python Combine_CSVs.py ./csvs prompt_combined.csv \
#    --file /global/cfs/cdirs/dune/users/lmlepin/cluster_outputs/AmBe_mod2_pmt_trigger_109us_period_20260409_1510/AmBe_mod2_pmt_trigger_109us_period_clusters_prompt.csv 109 \
#    --file /global/cfs/cdirs/dune/users/lmlepin/cluster_outputs/AmBe_mod2_pmt_trigger_128us_period_20260409_1524/AmBe_mod2_pmt_trigger_128us_period_clusters_prompt.csv 128 \
#    --file /global/cfs/cdirs/dune/users/lmlepin/cluster_outputs/AmBe_mod2_pmt_trigger_147us_period_20260409_1535/AmBe_mod2_pmt_trigger_147us_period_clusters_prompt.csv 147 \
#    --file /global/cfs/cdirs/dune/users/lmlepin/cluster_outputs/AmBe_mod2_pmt_trigger_176us_period_20260409_1539/AmBe_mod2_pmt_trigger_176us_period_clusters_prompt.csv 176 \
#    --file /global/cfs/cdirs/dune/users/lmlepin/cluster_outputs/AmBe_mod2_pmt_trigger_195us_period_20260409_1557/AmBe_mod2_pmt_trigger_195us_period_clusters_prompt.csv 195 \
#    --file /global/cfs/cdirs/dune/users/lmlepin/cluster_outputs/AmBe_mod2_pmt_trigger_224us_period_20260409_1557/AmBe_mod2_pmt_trigger_224us_period_clusters_prompt.csv 224 \
#    --file /global/cfs/cdirs/dune/users/lmlepin/cluster_outputs/AmBe_mod2_pmt_trigger_272us_period_20260409_1603/AmBe_mod2_pmt_trigger_272us_period_clusters_prompt.csv 272 \
#    --file /global/cfs/cdirs/dune/users/lmlepin/cluster_outputs/AmBe_mod2_pmt_trigger_291us_period_20260409_1645/AmBe_mod2_pmt_trigger_291us_period_clusters_prompt.csv 291 \
#    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_109us_period \
#    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_128us_period \
#    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_147us_period \
#    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_176us_period \
#    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_195us_period \
#    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_224us_period \
#    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_272us_period \
#    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_291us_period \
#    --calculate-runtime \
#    --debug-runtime


python Combine_CSVs.py ./csvs light_prompt_combined.csv \
    --file /global/cfs/cdirs/dune/users/edgarmao/NeutronSourceAnalysis/2x2_neutron_sources/AmBe/light/cl_matching_cache/events_109us_min0.csv 109 \
    --file /global/cfs/cdirs/dune/users/edgarmao/NeutronSourceAnalysis/2x2_neutron_sources/AmBe/light/cl_matching_cache/events_128us_min0.csv 128 \
    --file /global/cfs/cdirs/dune/users/edgarmao/NeutronSourceAnalysis/2x2_neutron_sources/AmBe/light/cl_matching_cache/events_147us_min0.csv 147 \
    --file /global/cfs/cdirs/dune/users/edgarmao/NeutronSourceAnalysis/2x2_neutron_sources/AmBe/light/cl_matching_cache/events_176us_min0.csv 176 \
    --file /global/cfs/cdirs/dune/users/edgarmao/NeutronSourceAnalysis/2x2_neutron_sources/AmBe/light/cl_matching_cache/events_195us_min0.csv 195 \
    --file /global/cfs/cdirs/dune/users/edgarmao/NeutronSourceAnalysis/2x2_neutron_sources/AmBe/light/cl_matching_cache/events_224us_min0.csv 224 \
    --file /global/cfs/cdirs/dune/users/edgarmao/NeutronSourceAnalysis/2x2_neutron_sources/AmBe/light/cl_matching_cache/events_272us_min0.csv 272 \
    --file /global/cfs/cdirs/dune/users/edgarmao/NeutronSourceAnalysis/2x2_neutron_sources/AmBe/light/cl_matching_cache/events_291us_min0.csv 291 \
    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_109us_period \
    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_128us_period \
    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_147us_period \
    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_176us_period \
    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_195us_period \
    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_224us_period \
    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_272us_period \
    --h5-dir /pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_291us_period \
    --calculate-runtime \
    --debug-runtime