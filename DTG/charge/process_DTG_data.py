import h5py as h5
import numpy as np
import os, sys
import traceback
import pandas as pd
import argparse
import h5flow
import time

print(f"TOP DIRECTORY: {os.environ['REPO_DIR']}")
repo_root = os.path.abspath(os.environ['REPO_DIR'])
sys.path.append(repo_root)

import utils.cluster_tools as cltools


def DTG_data_cluster_analysis(
    input_file,
    file_id,
    output_dir,
    chunk_size=2000,
    is_CL=False,
    is_debug=False
):
    """
    Process one h5flow file in chunks and save one CSV per chunk.

    Output naming convention:
        <base_file>.chunk_0000.csv
        <base_file>.chunk_0001.csv
        ...

    Returns a summary dictionary.
    """

    is_CL = bool(is_CL)
    is_debug = bool(is_debug)

    if is_debug:
        print(f"Chunk size: {chunk_size}")
        print(f"Is CL? {is_CL}")

    os.makedirs(output_dir, exist_ok=True)

    base_file = os.path.basename(input_file)
    h5_file = h5flow.data.H5FlowDataManager(input_file, 'r')

    total_start_time = time.time()
    chunks_written = 0
    total_clusters_written = 0

    try:
        if is_CL:
            event_ids = h5_file['light/events/data']['id']
        else:
            event_ids = h5_file['charge/events/data']['id']

        n_events = len(event_ids)

        if is_debug:
            print(f"Total events in file: {n_events}")

        n_chunks = int(np.ceil(n_events / chunk_size))

        for chunk_idx, start in enumerate(range(0, n_events, chunk_size)):
            chunk_start_time = time.time()

            stop = min(start + chunk_size, n_events)
            event_slice = slice(start, stop)

            print(f"\n[Chunk {chunk_idx + 1}/{n_chunks}] Processing events {start}:{stop}")

            # ------------------ Read events ------------------
            t0 = time.time()
            if is_CL:
                light_events = h5_file['light/events', event_slice]
                charge_events = h5_file['light/events', 'charge/events', event_slice]
            else:
                charge_events = h5_file['charge/events', event_slice]
            t1 = time.time()

            # ------------------ Read hits ------------------
            t2 = time.time()
            if is_CL:
                charge_hits = h5_file['light/events', 'charge/events', 'charge/calib_prompt_hits', event_slice]
                this_non_zero_data = [
                    charge_events,
                    charge_hits,
                    light_events
                ]
                n_events_this_chunk = len(light_events)
            else:
                mask = charge_events['nhit'] >= 1
                if not np.any(mask):
                    print("  No events passed nhit cut")
                    del charge_events
                    continue

                non_zero_charge_events = charge_events[mask]
                selected_ids = non_zero_charge_events['id']
                non_zero_charge_hits = h5_file['charge/events', 'charge/calib_prompt_hits', selected_ids]
                this_non_zero_data = [
                    non_zero_charge_events,
                    non_zero_charge_hits
                ]
                n_events_this_chunk = len(non_zero_charge_events)
            t3 = time.time()

            if is_debug:
                if is_CL:
                    print(f"  CL events in chunk: {n_events_this_chunk}")
                else:
                    print(f"  Non-zero charge events: {n_events_this_chunk}")

            t4 = time.time()
            temp_out = cltools.cluster_hits(
                this_non_zero_data,
                file_id,
                select_io=True,
                is_debug=is_debug
            )
            t5 = time.time()

            # ------------------ Save this chunk ------------------
            n_clusters_this_chunk = 0

            if temp_out is None:
                print("  cluster_hits returned None, skipping save")
            else:
                this_clusters = temp_out.get("clusters", None)

                if this_clusters is None:
                    print("  No 'clusters' key found in cluster_hits output, skipping save")
                else:
                    this_clusters = np.array(this_clusters)

                    if this_clusters.size == 0:
                        print("  No clusters found in this chunk, skipping save")
                    else:
                        chunk_output_name = f"{base_file}.chunk_{chunk_idx:04d}.csv"
                        chunk_output_path = os.path.join(output_dir, chunk_output_name)

                        cltools.save_to_csv(this_clusters, chunk_output_path)

                        # Number of rows in output array
                        n_clusters_this_chunk = len(this_clusters)
                        chunks_written += 1
                        total_clusters_written += n_clusters_this_chunk

                        print(f"  Saved chunk CSV: {chunk_output_path}")
                        print(f"  Output shape: {this_clusters.shape}")

            chunk_end_time = time.time()

            # ------------------ Timing summary ------------------
            print(f"  Time read events: {t1 - t0:.3f} s")
            print(f"  Time read hits:   {t3 - t2:.3f} s")
            print(f"  Time clustering:  {t5 - t4:.3f} s")
            print(f"  Chunk total time: {chunk_end_time - chunk_start_time:.3f} s")
            print(f"  Clusters saved in chunk: {n_clusters_this_chunk}")

            # Optional cleanup
            if is_CL:
                del light_events, charge_events, charge_hits
            else:
                del charge_events, non_zero_charge_events, non_zero_charge_hits
            if temp_out is not None:
                del temp_out
            if 'this_clusters' in locals():
                del this_clusters

    finally:
        try:
            h5_file.close()
        except Exception:
            pass

    total_end_time = time.time()
    total_time = total_end_time - total_start_time

    print(f"\nFinished processing file: {input_file}")
    print(f"Chunks written: {chunks_written}")
    print(f"Total clusters written: {total_clusters_written}")
    print(f"Total processing time: {total_time:.2f} s")

    return {
        "input_file": input_file,
        "chunks_written": chunks_written,
        "total_clusters_written": total_clusters_written,
        "total_time_s": total_time
    }


if __name__ == "__main__":
    print("Running DTG CR cluster tool")
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        nargs=1,
        required=True,
        help="text file with input files"
    )

    parser.add_argument(
        "--out",
        nargs=1,
        required=True,
        help="output directory"
    )

    parser.add_argument(
        "--cs",
        nargs=1,
        default=[2000],
        type=int,
        help="indicates chunk size"
    )

    parser.add_argument(
        "--cl",
        nargs=1,
        default=[0],
        type=int,
        help="is CL file?"
    )

    parser.add_argument(
        "--debug",
        nargs=1,
        default=[1],
        type=int,
        help="Run in debug mode, default: yes"
    )

    args = parser.parse_args()

    print("Starting file processing...")
    os.makedirs(args.out[0], exist_ok=True)

    with open(args.input[0], 'r') as f:
        file_list = [line.strip() for line in f if line.strip()]

    print("DEBUG:", bool(args.debug[0]))
    if bool(args.debug[0]):
        print("Running in debug mode, only 5 files will be processed.")

    file_summaries = []

    for file_count, ifile in enumerate(file_list):
        time_start = time.time()

        if bool(args.debug[0]) and file_count >= 1:
            break

        this_file = ifile
        print(f"\nProcessing file {file_count + 1}: {this_file}")

        try:
            summary = DTG_data_cluster_analysis(
                input_file=this_file,
                file_id=file_count,
                output_dir=args.out[0],
                chunk_size=args.cs[0],
                is_CL=args.cl[0],
                is_debug=args.debug[0]
            )

            file_summaries.append(summary)

            if bool(args.debug[0]):
                print(f"Time processing this file: {time.time() - time_start:.3f} s")

        except Exception as e:
            print(f"[WARNING] Failed processing {this_file}: {e}")
            traceback.print_exc()
            continue

    print("\nPer-file summary:")
    for summary in file_summaries:
        print(summary)

    print("\nThis script has finished successfully, happy analysis!")
