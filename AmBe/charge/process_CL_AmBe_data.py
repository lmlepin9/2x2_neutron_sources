import numpy as np
import os, sys
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

def CL_AmBe_analysis(input_file, file_id, single, use_trigger, period, is_debug=False):

    use_trigger = bool(use_trigger)
    single = bool(single)

    print(f"Use trigger: {use_trigger}")
    print(f"Single trigger: {single}")

    h5_file = h5flow.data.H5FlowDataManager(input_file, 'r')

    def build_cluster_input(trigger_ids, label=""):
        """
        Retrieve event products for the given trigger ids, keep only events
        with at least one hit, and return the input expected by cluster_hits().
        """
        trigger_ids = np.asarray(trigger_ids, dtype=np.int64)

        if len(trigger_ids) == 0:
            print(f"No events to process {label}")
            return None

        light_events  = h5_file['light/events', trigger_ids]
        charge_events = h5_file['light/events', 'charge/events', trigger_ids]
        charge_hits   = h5_file['light/events', 'charge/events', 'charge/calib_prompt_hits', trigger_ids]

        # Keep only events with at least one hit
        hit_mask = charge_events.data['nhit'][:, 0] >= 1

        non_zero_charge_hits = charge_hits[hit_mask]
        non_zero_charge_events = charge_events[hit_mask]
        non_zero_charge_light_ev = light_events[hit_mask]

        print(f"Number of events with >=1 hit to be processed {label}: {len(non_zero_charge_events)}")

        if len(non_zero_charge_events) == 0:
            return None

        return [
            non_zero_charge_events,
            non_zero_charge_hits,
            non_zero_charge_light_ev
        ]

    def run_cluster(trigger_ids, label=""):
        """
        Run cluster_hits() and always return a 2D numpy array of shape (N, 9).
        """
        cluster_input = build_cluster_input(trigger_ids, label=label)

        if cluster_input is None:
            return np.empty((0, 9))

        out = cltools.cluster_hits(
            cluster_input,
            file_id
        )

        if out is None or "clusters" not in out or out["clusters"] is None:
            return np.empty((0, 9))

        return out["clusters"]

    # ------------------------------------------------------------------
    # Case 1: single-trigger mode with trigger selection
    # ------------------------------------------------------------------
    if single and use_trigger:
        g_triggers, b_triggers = classify_triggers_single(h5_file)
        g_triggers = np.asarray(g_triggers, dtype=np.int64)

        print(f"Number of events to be processed: {len(g_triggers)}")

        prompt_clusters = run_cluster(g_triggers, label="(single trigger mode)")

        return {
            "clusters": prompt_clusters,
            "prompt_clusters": prompt_clusters,
            "delayed_clusters": np.empty((0, 9))
        }

    # ------------------------------------------------------------------
    # Case 2: multi-trigger mode with trigger selection
    #         event N = prompt, event N+1 = delayed
    # ------------------------------------------------------------------
    elif (single == False) and use_trigger:
        first_trig = check_first_trig(h5_file, period)
        parity_str = "odd" if first_trig else "even"
        print(f"Parity of this file: {parity_str}")

        g_triggers, b_triggers = classify_triggers(h5_file, parity_str)
        g_triggers = np.asarray(g_triggers, dtype=np.int64)

        print(f"Number of prompt events found: {len(g_triggers)}")

        delayed_triggers = g_triggers + 1

        # Keep only pairs where delayed event exists in the file
        all_light_ids = np.asarray(h5_file['light/events/data']['id'], dtype=np.int64)
        valid_ids = set(all_light_ids.tolist())

        pair_mask = np.array([evt in valid_ids for evt in delayed_triggers], dtype=bool)

        prompt_triggers = g_triggers[pair_mask]
        delayed_triggers = delayed_triggers[pair_mask]

        print(f"Number of valid prompt-delayed pairs: {len(prompt_triggers)}")

        # Pair-preserving debug mode: sample pairs, not individual events
        if is_debug and len(prompt_triggers) > 0:
            n_debug = max(1, int(0.1 * len(prompt_triggers)))

            rng = np.random.default_rng(12345)
            debug_idx = np.sort(
                rng.choice(len(prompt_triggers), size=n_debug, replace=False)
            )

            prompt_triggers = prompt_triggers[debug_idx]
            delayed_triggers = delayed_triggers[debug_idx]

            print(
                f"DEBUG enabled: processing {len(prompt_triggers)} prompt-delayed pairs "
                f"({100.0 * len(prompt_triggers) / max(1, pair_mask.sum()):.1f}% of valid pairs)"
            )

        prompt_clusters = run_cluster(prompt_triggers, label="(prompt)")
        delayed_clusters = run_cluster(delayed_triggers, label="(delayed)")

        if len(prompt_clusters) == 0 and len(delayed_clusters) == 0:
            combined_clusters = np.empty((0, 9))
        elif len(prompt_clusters) == 0:
            combined_clusters = delayed_clusters
        elif len(delayed_clusters) == 0:
            combined_clusters = prompt_clusters
        else:
            combined_clusters = np.vstack([prompt_clusters, delayed_clusters])

        return {
            "clusters": combined_clusters,
            "prompt_clusters": prompt_clusters,
            "delayed_clusters": delayed_clusters
        }

    # ------------------------------------------------------------------
    # Case 3: no trigger selection
    # ------------------------------------------------------------------
    elif use_trigger == False:
        all_triggers = np.asarray(h5_file['light/events/data']['id'], dtype=np.int64)

        print(f"Number of events to be processed: {len(all_triggers)}")

        if is_debug and len(all_triggers) > 0:
            n_debug = max(1, int(0.1 * len(all_triggers)))

            rng = np.random.default_rng(12345)
            debug_idx = np.sort(
                rng.choice(len(all_triggers), size=n_debug, replace=False)
            )

            all_triggers = all_triggers[debug_idx]

            print(
                f"DEBUG enabled: processing {len(all_triggers)} events "
                f"({100.0 * len(all_triggers) / max(1, len(h5_file['light/events/data']['id'])):.1f}% of all events)"
            )

        all_clusters = run_cluster(all_triggers, label="(all events)")

        return {
            "clusters": all_clusters,
            "prompt_clusters": all_clusters,
            "delayed_clusters": np.empty((0, 9))
        }
    

if __name__ == "__main__":
    print("Running AmBe CR cluster tool")
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        required=True,
        help="input HDF5 file"
    )

    parser.add_argument(
        "--out",
        required=True,
        help="output csv file"
    )

    parser.add_argument(
        "--trig",
        default=1,
        type=int,
        help="indicates if the PMT trigger has to be used"
    )

    parser.add_argument(
        "--st",
        default=1,
        type=int,
        help="Single trigger or multi (prompt, delayed) triggers"
    )

    parser.add_argument(
        "--p",
        default=320,
        type=int,
        help="Period between prompt and delayed trigger (if applicable)"
    )

    parser.add_argument(
        "--debug",
        default=1,
        type=int,
        help="Run in debug mode, default: yes"
    )

    args = parser.parse_args()

    print("Starting file processing...")
    print("Input file:", args.input)
    print("DEBUG:", bool(args.debug))

    try:
        temp_out = CL_AmBe_analysis(
            args.input,
            0,                  # file_id
            args.st,
            args.trig,
            args.p,
            bool(args.debug)
        )

        all_clusters = temp_out["clusters"]
        prompt_clusters = temp_out["prompt_clusters"]
        delayed_clusters = temp_out["delayed_clusters"]

    except Exception as e:
        print(f"[WARNING] Failed processing {args.input}: {e}")
        all_clusters = []
        prompt_clusters = []
        delayed_clusters = []

    print("\nShowing amount of clusters per file:")
    all_clusters_array = np.array(all_clusters)

    if len(all_clusters_array) > 0:
        for ifile in np.unique(all_clusters_array[:, 8]):
            print(
                f"Dimensions of file {ifile} "
                f"{all_clusters_array[all_clusters_array[:, 8] == ifile].shape}"
            )

        cltools.save_to_csv(all_clusters_array, args.out)
    else:
        print("No clusters were produced, combined output CSV will not be written.")

    # Optional separate outputs
    if len(prompt_clusters) > 0:
        prompt_out = args.out.replace(".csv", "_prompt.csv")
        cltools.save_to_csv(np.array(prompt_clusters), prompt_out)
        print(f"Prompt clusters written to: {prompt_out}")

    if len(delayed_clusters) > 0:
        delayed_out = args.out.replace(".csv", "_delayed.csv")
        cltools.save_to_csv(np.array(delayed_clusters), delayed_out)
        print(f"Delayed clusters written to: {delayed_out}")

    print("\nThis script has finished successfully, happy analysis!")