import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN 
import time


def filter_hits(h5_hits):
    '''
    Filter hits directly at h5flow level
    - remove negative energy
    - remove NaNs / infs in spatial coordinates
    '''

    x = h5_hits['x']
    y = h5_hits['y']
    z = h5_hits['z']
    E = h5_hits['E']

    mask = (
        (E > 0.0)
        & np.isfinite(x)
        & np.isfinite(y)
        & np.isfinite(z)
    )

    return h5_hits[mask]

def save_to_csv(clusters_array,output_path):
    '''
    This function takes a numpy array containing all the clusters obtained
    it creates and pandas data frame and saves it to a user defined path

    Args:
        clusters_array (np.array): array of clusters to be saved
        out_clusters (string): path to save csv file 
    '''

    print(f"\nSaving clusters to a csv file: {output_path}")
    df = pd.DataFrame(clusters_array, columns=['x', 'y', 'z', 'E', 'Q', 'io', 'light_id', 'cluster_label', 'file_id'])

    df["id"] = (
        df["file_id"].astype(str)
        + "::" + df["light_id"].astype(str)
        + "::" + df["cluster_label"].astype(str)
    )

    df.to_csv(output_path)


def run_DBScan(this_event_hits, this_event_id, file_id, this_dbscan):
    """
    Run DBSCAN on one set of hits and return a NumPy array with columns:
    x, y, z, E, Q, io_group, event_id, cluster_label, file_id
    """

    n_hits = len(this_event_hits)
    if n_hits == 0:
        return None

    hits_data = this_event_hits.data

    # Build unfiltered hit array once
    hits_stack = np.column_stack((
        hits_data['x'],
        hits_data['y'],
        hits_data['z'],
        hits_data['E'],
        hits_data['Q'],
        hits_data['io_group'],
        np.full(n_hits, int(this_event_id))
    ))



    if len(hits_stack) == 0:
        return None

    # DBSCAN only needs x,y,z
    labels = this_dbscan.fit_predict(hits_stack[:, :3])

    # Build final output array once
    out = np.column_stack((
        hits_stack[:, 0],                         # x
        hits_stack[:, 1],                         # y
        hits_stack[:, 2],                         # z
        hits_stack[:, 3],                         # E
        hits_stack[:, 4],                         # Q
        hits_stack[:, 5],                         # io_group
        np.full(len(hits_stack), int(this_event_id)),
        labels,
        np.full(len(hits_stack), int(file_id))
    ))

    return out


def split_hits_by_io(test_event_hits):
    """
    Split one event's hits by io_group efficiently using one sort.

    Returns:
        list of tuples: [(io_value, hits_for_that_io), ...]
    """

    n_hits = len(test_event_hits)
    if n_hits == 0:
        return []

    io_vals = test_event_hits.data['io_group']

    # Sort once by io_group
    order = np.argsort(io_vals, kind='stable')
    hits_sorted = test_event_hits[order]
    io_sorted = io_vals[order]

    # Find unique groups and boundaries
    unique_io, start_idx = np.unique(io_sorted, return_index=True)

    out = []
    for i, io in enumerate(unique_io):
        start = start_idx[i]
        stop = start_idx[i + 1] if i + 1 < len(start_idx) else n_hits
        out.append((io, hits_sorted[start:stop]))

    return out


def cluster_hits(non_zero_charge_data,
                 file_id,
                 user_eps=3,
                 user_nsamples=1,
                 select_io=False,
                 is_debug=False):
    """
    Perform DBSCAN clustering on AmBe or DTG data.

    Args:
        non_zero_charge_data (list):
            [non_zero_charge_events, non_zero_charge_hits]
            or
            [non_zero_charge_events, non_zero_charge_hits, non_zero_charge_light_ev]
        file_id (int): file index / identifier
        user_eps (float): DBSCAN eps
        user_nsamples (int): DBSCAN min_samples
        select_io (bool): if True, cluster each io_group separately
        is_debug (bool): print timing information

    Returns:
        dict with:
            out_dataset["clusters"] = np.ndarray of shape (N, 9)
    """

    out_dataset = {"clusters": None}

    non_zero_charge_events = non_zero_charge_data[0]
    non_zero_charge_hits = non_zero_charge_data[1]

    db = DBSCAN(eps=user_eps, min_samples=user_nsamples,algorithm='ball_tree')

    cluster_chunks = []

    n_events = len(non_zero_charge_events)

    # Timers
    t_total_extract = 0.0
    t_total_split_io = 0.0
    t_total_dbscan = 0.0
    t_total_loop = time.time()

    use_light_ids = (len(non_zero_charge_data) == 3)
    if use_light_ids:
        non_zero_charge_light_ev = non_zero_charge_data[2]

    for icharge in range(n_events):
        # ------------------ Extract event hits ------------------
        t0 = time.time()

        if use_light_ids:
            test_event_hits = non_zero_charge_hits[:, 0][icharge][
                0:non_zero_charge_events.data['nhit'][:, 0][icharge]
            ]
            this_event_id = non_zero_charge_light_ev['id'][icharge]
        else:
            test_event_hits = non_zero_charge_hits[icharge][
                0:non_zero_charge_events['nhit'][icharge]
            ]
            # Use true event id if available, else fallback to icharge
            if 'id' in non_zero_charge_events.dtype.names:
                this_event_id = non_zero_charge_events['id'][icharge]
            else:
                this_event_id = icharge

        t1 = time.time()
        t_total_extract += (t1 - t0)

        if len(test_event_hits) == 0:
            continue

        # Filter stuff here, before doing per IO stuff 
        test_event_hits = filter_hits(test_event_hits)

        # ------------------ Optional io-group split ------------------
        if select_io:
            t2 = time.time()
            io_hit_groups = split_hits_by_io(test_event_hits)
            t3 = time.time()
            t_total_split_io += (t3 - t2)

            for io, this_io_hits in io_hit_groups:
                # Skip tiny groups
                if len(this_io_hits) < user_nsamples:
                    continue

                t4 = time.time()
                arr = run_DBScan(this_io_hits, this_event_id, file_id, db)
                t5 = time.time()
                t_total_dbscan += (t5 - t4)

                if arr is not None and len(arr) > 0:
                    cluster_chunks.append(arr)

        else:
            t4 = time.time()
            arr = run_DBScan(test_event_hits, this_event_id, file_id, db)
            t5 = time.time()
            t_total_dbscan += (t5 - t4)

            if arr is not None and len(arr) > 0:
                cluster_chunks.append(arr)

    if is_debug:
        print(f"Time extracting event hits: {t_total_extract:.3f} s")
        if select_io:
            print(f"Time splitting by io_group: {t_total_split_io:.3f} s")
        print(f"Time in run_DBScan:         {t_total_dbscan:.3f} s")
        print(f"Total cluster_hits time:    {time.time() - t_total_loop:.3f} s")

    if len(cluster_chunks) == 0:
        out_dataset["clusters"] = np.empty((0, 9))
    else:
        out_dataset["clusters"] = np.vstack(cluster_chunks)

    return out_dataset