import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN 


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


def cluster_hits(non_zero_charge_data,
                 file_id,
                 user_eps=3,
                 user_nsamples=1):
    
    '''
    
    Function to perform DBScan cluster on 
    AmBe or DTG data. At the bare minimum it requires
    the set of hits for a given file and the charge event ids.
    If CL-matched files are being processed this function will keep
    light event ids instead.

    Args:
        non_zero_charge_data (list): list containing non zero charge hits, charge ev ids, and optionally light ev ids
        file_id: A number representing the file being processed

        (opt) user_esp and user_nsamples: User defined config for DBScan
    
    Returns:
       out_dataset: A python dictionary containing a numpy array stack with hit-level information and the 
                    corresponding cluster labels, file-ev ids. 
    
    '''



    # Initialize output dataset 
    # This will be a dictionary so it can be saved as a csv later  
    clusterized_hits = [] 
    out_dataset = {
        "clusters":None
    }

    # Get charge events and hits 
    non_zero_charge_events = non_zero_charge_data[0]
    non_zero_charge_hits = non_zero_charge_data[1]


    # Setup DBScan 
    db = DBSCAN(eps=user_eps,min_samples=user_nsamples)

    for icharge in range(len(non_zero_charge_events)):
        # Grab hits of this event 
        test_event_hits = non_zero_charge_hits[:,0][icharge][0:non_zero_charge_events.data['nhit'][:,0][icharge]]


        this_event_id = None

        # If we include light events use this as event id for correlation with light analysis 
        if(len(non_zero_charge_data)==3):
            non_zero_charge_light_ev = non_zero_charge_data[2]
            this_event_id = non_zero_charge_light_ev['id'][icharge]
        
        # Otherwise keep charge event id
        else:
            this_event_id = icharge



        # Stack hits data and filter
        hits_stack_unfiltered = np.column_stack((test_event_hits.data['x'],
                                                 test_event_hits.data['y'],
                                                 test_event_hits.data['z'],
                                                 test_event_hits.data['E'],
                                                 test_event_hits.data['Q'],
                                                 np.ones(len(test_event_hits))*this_event_id))
        hits_stack = filter_hits(hits_stack_unfiltered)

        # Skip if no hits 
        if(len(hits_stack)==0):
            continue

        # Run DBScan with x,y,z 
        labels = db.fit_predict(hits_stack[:,:3])

        # Add labels and append to the clusterized hits array 
        hits_stack_label = np.column_stack((hits_stack[:,0],
                                            hits_stack[:,1],
                                            hits_stack[:,2],
                                            hits_stack[:,3],
                                            hits_stack[:,4],
                                            np.ones(len(hits_stack))*int(this_event_id),
                                            labels,
                                            np.ones(len(hits_stack))*int(file_id)))
        clusterized_hits.extend(hits_stack_label.tolist())

    out_dataset["clusters"] = clusterized_hits


    return out_dataset


