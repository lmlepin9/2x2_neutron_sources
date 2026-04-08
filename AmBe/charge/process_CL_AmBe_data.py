import h5py as h5 
import numpy as np
import os, sys
import traceback
import pandas as pd
import argparse
import h5flow 

# Path to repo root (two directories above notebook)
light_root = os.path.abspath(f"{os.environ['REPO_DIR']}/AmBe")
sys.path.append(light_root)

from light.PMT_analysis_utils import * 


repo_root = os.path.abspath(os.environ['REPO_DIR'])
sys.path.append(repo_root)

import utils.cluster_tools as cltools



import numpy as np
import h5flow

def CL_AmBe_analysis(input_file, file_id, single, use_trigger, period, is_debug=False):

    use_trigger = bool(use_trigger)
    single = bool(single)

    print(f"Use trigger: {use_trigger}")
    print(f"Single trigger: {single}")

    h5_file = h5flow.data.H5FlowDataManager(input_file, 'r')
    g_triggers = None
    b_triggers = None

    if single and use_trigger:
        g_triggers, b_triggers = classify_triggers_single(h5_file, debug=is_debug)

    elif (single == False) and use_trigger:
        # The period between triggers is hard-coded, needs fix
        first_trig = check_first_trig(h5_file, period)
        parity_str = "odd" if first_trig else "even"
        print(f"Parity of this file: {parity_str}")
        g_triggers, b_triggers = classify_triggers(h5_file, parity_str)

    elif use_trigger == False:
        g_triggers = h5_file['light/events/data']['id']

    print(f"Number of events to be processed {len(g_triggers)}")

    # Retrieve products linked to good triggers
    light_events  = h5_file['light/events', g_triggers]
    charge_events = h5_file['light/events', 'charge/events', g_triggers]
    charge_hits   = h5_file['light/events', 'charge/events', 'charge/calib_prompt_hits', g_triggers]

    # Keep only events with more than one hit
    hit_mask = charge_events.data['nhit'][:, 0] >= 1

    non_zero_charge_hits = charge_hits[hit_mask]
    non_zero_charge_events = charge_events[hit_mask]
    non_zero_charge_light_ev = light_events[hit_mask]

    print(f"Number of events with >1 hit to be processed {len(non_zero_charge_events)}")

    # In debug mode, run only on 10% of the surviving events
    if is_debug and len(non_zero_charge_events) > 0:
        n_debug = max(1, int(0.1 * len(non_zero_charge_events)))

        # Reproducible random subset
        rng = np.random.default_rng(12345)
        debug_idx = np.sort(rng.choice(len(non_zero_charge_events), size=n_debug, replace=False))

        non_zero_charge_hits = non_zero_charge_hits[debug_idx]
        non_zero_charge_events = non_zero_charge_events[debug_idx]
        non_zero_charge_light_ev = non_zero_charge_light_ev[debug_idx]

        print(f"DEBUG enabled: processing {len(non_zero_charge_events)} events "
              f"({100.0 * len(non_zero_charge_events) / max(1, hit_mask.sum()):.1f}% of events with >1 hit)")

    this_non_zero_data = [
        non_zero_charge_events,
        non_zero_charge_hits,
        non_zero_charge_light_ev
    ]

    this_file_clusters = cltools.cluster_hits(
        this_non_zero_data,
        file_id
    )

    return this_file_clusters


if __name__ == "__main__":
    print("Running AmBe CR cluster tool")
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        nargs=1,
        required=True,  
        help="directory with input files"
    )

    parser.add_argument(
        "--out",
        nargs=1,
        required=True,
        help="output csv file"
    )

    parser.add_argument(
        "--trig",
        nargs=1,
        default=True,
        type=int,
        help="indicates if the PMT trigger has to be used"
    )

    parser.add_argument(
        "--st",
        nargs=1,
        default="1",
        type=int,
        help="Single trigger or multi (prompt,delayed) triggers"
    )

    parser.add_argument(
        "--p",
        nargs=1,
        default=320,
        help="Period bt prompt and delayed trigger (if applicable)"
    )

    parser.add_argument(
        "--debug",
        nargs=1,
        default=1,
        type=int,
        help="Run in debug mode, default: yes" 
    )

    args = parser.parse_args()
    # Execute clustering

    all_clusters = []
    print("Starting file processing...")

    # Filter out .json files 
    file_list = os.listdir(args.input[0])
    file_list = [f for f in file_list if not f.endswith(".json")]

    print("DEBUG: ",bool(args.debug[0]))
    for file_count, ifile in enumerate(file_list):

        this_file = os.path.join(args.input[0], ifile)
        print(this_file)

        try:
            temp_out = CL_AmBe_analysis(
                    this_file,
                    file_count,
                    args.st[0],
                    args.trig[0],
                    args.p[0],
                    bool(args.debug[0])

            )
            all_clusters.extend(temp_out["clusters"])

        except Exception as e:
            print(f"[WARNING] Failed processing {this_file}: {e}")
        continue


    print("\n Showing amount of clusters per file:")
    all_clusters_array = np.array(all_clusters)
    for ifile in np.unique(all_clusters_array[:,7]):
        print(f"Dimensions of file {ifile} {all_clusters_array[all_clusters_array[:,7]==ifile].shape}")


    # Save to csv
    cltools.save_to_csv(all_clusters_array,args.out[0])
    print("\nThis script has finished successfully, happy analysis!") 



    