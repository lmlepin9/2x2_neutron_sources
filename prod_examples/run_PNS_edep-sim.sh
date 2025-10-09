 #!/user/bin/env bash

# Setup dependencies

source /pscratch/sd/l/lmlepin/setup_2x2_container.sh

# Geometry with no MINERvA 
export ARCUBE_GEOM='/pscratch/sd/l/lmlepin/2x2_sim_develop/2x2_sim/geometry/Merged2x2MINERvA_v4_noRock_2x2_only_sense.gdml'
export NEVENTS='50000'
export SIM_DIR='/pscratch/sd/l/lmlepin/2x2_sim_develop/2x2_sim'
export OUT_DIR='/global/cfs/cdirs/dune/users/lmlepin/2x2_neutron_prod/PNS_tests'
export OUT_FILE="${OUT_DIR}/MR5_DTG_sim_updated_distribution.root"
export MAC_FILE="${SIM_DIR}/run-edep-sim/macros/2x2_DTG_P385_single.mac"
#export MAC_FILE="${SIM_DIR}/run-edep-sim/macros/2x2_DTG_single_updated.mac"
#export MAC_FILE="${SIM_DIR}/run-edep-sim/macros/2x2_source_test.mac"
export PS_LIST='MyQGSP_BERT_ArHP'
export OUT_NAME="DTG_P385_test"


#edep-sim -C -g "$ARCUBE_GEOM" -o "$OUT_FILE" -p "$PS_LIST" -e "$NEVENTS" "$MAC_FILE"


# RUN NEUTRON SPILL BUILDER

export FILE_ID=1
export PULSE_WIDTH=5e-6 # in s
export ACC_VOLTAGE=40
export CURRENT=20
export FREQUENCY=10000.0
export DUTY_FACTOR=0.05
export OUT_FILE_SPILL="${OUT_DIR}/${OUT_NAME}.root"

root -l -b -q  -e "gSystem->Load(\"$LIBTG4EVENT_DIR/libTG4Event.so\")" \
                  "../DTG/utils/create_neutron_pulses.C(\"${OUT_FILE}\",${FILE_ID}, ${PULSE_WIDTH},${ACC_VOLTAGE}, ${CURRENT}, ${DUTY_FACTOR},\"${OUT_FILE_SPILL}\")"

# Run convert2h5 

echo "Running convert2h5..."
export OUTPUT_H5="${OUT_DIR}/${OUT_NAME}.EDEPSIM.hdf5"
rm -f $OUTPUT_H5

# After going from ROOT 6.14.06 to 6.28.06, apparently we need to point CPATH to
# the edepsim-io headers. Otherwise convert2h5 fails. (This "should" be set in
# the container already.)
export CPATH=$EDEPSIM/include/EDepSim:$CPATH

export keepAllDets=False
echo "Keep all dets? ${keepAllDets}"

python3 ${SIM_DIR}/run-convert2h5/convert_edepsim_roottoh5.py --input_file "$OUT_FILE_SPILL" --output_file "$OUTPUT_H5" --gps True