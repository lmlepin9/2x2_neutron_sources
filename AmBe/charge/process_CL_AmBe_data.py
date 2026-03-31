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



def CL_AmBe_analysis(input_file,file_id,single,use_trigger,period,is_debug=False):

    use_trigger = bool(use_trigger)
    single = bool(single)

    print(f"Use trigger: {use_trigger}")
    print(f"Single trigger: {single}")

    h5_file = h5flow.data.H5FlowDataManager(input_file,'r')
    g_triggers = None
    b_triggers = None

    if(single and use_trigger):
        g_triggers, b_triggers = classify_triggers_single(h5_file,debug=is_debug)
    
    elif single==False and use_trigger:  
        # The period between triggers is hard-coded, needs fix
        first_trig = check_first_trig(h5_file,period)
        parity_str = None
        if(first_trig):
            parity_str = "odd"
        else:
            parity_str = "even"
        print(f"Parity of this file: {parity_str}")
        g_triggers, b_triggers = classify_triggers(h5_file,parity_str,debug=is_debug)
    elif use_trigger==False:
        g_triggers = h5_file['light/events/data']['id']

    #print(f"List of good triggers: {g_triggers}")
    print(f"Number of events to be processed {len(g_triggers)}")
    # Retrieve products linked to good triggers 
    light_events = h5_file['light/events',g_triggers]
    charge_events = h5_file['light/events','charge/events',g_triggers]
    charge_hits = h5_file['light/events','charge/events','charge/calib_prompt_hits',g_triggers]

    # Charge
    non_zero_charge_hits = charge_hits[charge_events.data['nhit'][:,0] >= 1]
    non_zero_charge_events = charge_events[charge_events.data['nhit'][:,0] >= 1]
    non_zero_charge_light_ev = light_events[charge_events.data['nhit'][:,0] >= 1] 

    print(f"Number of non-zero charge events to be processed {len(non_zero_charge_events)}")

    this_non_zero_data = [
        non_zero_charge_events,
        non_zero_charge_hits,
        non_zero_charge_light_ev
    ]

    this_file_clusters = cltools.cluster_hits(this_non_zero_data,
                                              file_id)

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
    if(bool(args.debug[0])==True):
        print("Running in debug mode, only 5 files will be processed.")

    for file_count, ifile in enumerate(file_list):

        # Run over 10% of the dataset
        if bool(args.debug[0]) and file_count >= 5:
            break

        this_file = os.path.join(args.input[0], ifile)
        print(this_file)

        try:
            temp_out = CL_AmBe_analysis(
                    this_file,
                    file_count,
                    args.st[0],
                    args.trig[0],
                    args.p[0]

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



    