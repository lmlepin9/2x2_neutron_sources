import pandas as pd
import numpy as np


def filter_hits(hits_set):
    '''
    Function to filter out hits with negative energies
    or with nan entries in any of the useful fields

    Args:
        hits_set (np.array): array with hits

    Returns:
        hits_set_filtered (np.array): array with hits passing the filter  
    '''
    # Remove hits with negative energy
    hits_set_filtered = hits_set[hits_set[:,3] > 0.]
    # Remove hits with any NaN field
    hits_set_filtered = hits_set_filtered[~np.isnan(hits_set_filtered).any(axis=1)]
    return hits_set_filtered

def save_to_csv(clusters_array,output_path):
    '''
    This function takes a numpy array containing all the clusters obtained
    it creates and pandas data frame and saves it to a user defined path

    Args:
        clusters_array (np.array): array of clusters to be saved
        out_clusters (string): path to save csv file 
    '''

    print(f"\nSaving clusters to a csv file: {output_path}")
    df = pd.DataFrame(clusters_array, columns=['x', 'y', 'z', 'E', 'Q', 'light_id', 'cluster_label', 'file_id'])

    df["id"] = (
        df["file_id"].astype(str)
        + "::" + df["light_id"].astype(str)
        + "::" + df["cluster_label"].astype(str)
    )

    df.to_csv(output_path)
