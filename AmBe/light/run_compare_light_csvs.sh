#!/bin/bash

#python compare_light_csvs.py \
#    --source /global/cfs/cdirs/dune/users/edgarmao/NeutronSourceAnalysis/2x2_neutron_sources/AmBe/charge/light_prompt_combined.csv \
#    --background cl_matching_cache/bkg_charge_no_source_min0.csv \
#    --source-runtime 3521 \
#    --background-runtime 1979 \
#    --min-cluster-size 0

python compare_light_csvs.py \
    --source /global/cfs/cdirs/dune/users/edgarmao/NeutronSourceAnalysis/2x2_neutron_sources/AmBe/charge/light_prompt_combined.csv \
    --background /global/cfs/cdirs/dune/users/edgarmao/NeutronSourceAnalysis/2x2_neutron_sources/AmBe/light/cl_matching_cache/bkg_matched_no_source_min0.csv \
    --source-runtime 3222 \
    --background-runtime 1800 \
    --min-cluster-size 2 \
    --calibrated-csv-dir . \
#    --no-valid-sumhits-cut