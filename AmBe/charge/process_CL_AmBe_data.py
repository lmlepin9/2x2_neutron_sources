import h5py as h5 

import matplotlib.pyplot as plt
from matplotlib import cm, colors
import matplotlib.patches as mpatches
from matplotlib.colors import BoundaryNorm
from matplotlib import colors, ticker

import numpy as np
import os, sys
import traceback
import pandas as pd

import h5flow 
plt.style.use('../../utils/dune.mplstyle')
from sklearn.cluster import DBSCAN 

# Path to repo root (two directories above notebook)
light_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(light_root)

from light.PMT_analysis_utils import * 

# Path to repo root (two directories above notebook)
repo_root = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))
sys.path.append(repo_root)

from utils.backtracking import get_charge_event_hits, hit_backtracker, get_ancestry # Now this works
from utils.my_ev_display import event_display

DEBUG=True

# Configure your analysis here 

input_dataset = "/pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/one_pmt_trig_no_source"
#input_dataset = "/pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin2/one_trig_32us_window"
#input_dataset = "/global/cfs/cdirs/dune/www/data/2x2/reflows_run2/v0/flow/ColdOperations/data/2025_Operations_Cold/source/AmBe_1112"
#input_dataset = "/pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin0/mod2_pmt_trig"
#input_dataset =  "/pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin3/two_trig_109us_period"
#input_dataset = "/pscratch/sd/d/dunepro/mkramer/output/Reflow_2x2_Run2_v0p2/flow/source_ambe_bin4/two_trig_320us_period"
out_clusters = "../output/source_one_pmt_trig_no_source_clusters.csv"

job_config = {
    "DEBUG":False,
    "SINGLE":True,
    "PMT_trigger":False,
    "PERIOD":320

}

#-------------------------------------------------------------------------------------------------------------------------------------- 

def filter_hits(hits_set):
    # Remove hits with negative energy
    hits_set = hits_set[hits_set[:,3] > 0.]
    # Remove hits with any NaN field
    hits_set = hits_set[~np.isnan(hits_set).any(axis=1)]
    return hits_set 


def CL_AmBe_analysis(input_file,file_id,input_config):

    is_debug=input_config["DEBUG"]
    single=input_config["SINGLE"]
    use_trigger=input_config["PMT_trigger"]
    period=input_config["PERIOD"]

    h5_file = h5flow.data.H5FlowDataManager(input_file,'r')
    g_triggers = None
    b_triggers = None

    # Initialize output dataset 
    out_dataset = {
        "clusters":None
    }

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
    light_wvfms = h5_file['light/wvfm',g_triggers]
    charge_events = h5_file['light/events','charge/events',g_triggers]
    charge_hits = h5_file['light/events','charge/events','charge/calib_prompt_hits',g_triggers]

    # Charge
    non_zero_charge_hits = charge_hits[charge_events.data['nhit'][:,0] >= 1]
    non_zero_charge_events = charge_events[charge_events.data['nhit'][:,0] >= 1]
    non_zero_charge_light_ev = light_events[charge_events.data['nhit'][:,0] >= 1] 

    E_clusters = []
    n_cluster = [] 
    n_hits_clusters = [] 
    cluster_light_ev_id = [] 

    clusterized_hits = [] 
    print(f"Number of non-zero charge events to be processed {len(non_zero_charge_events)}")
    db = DBSCAN(eps=3,min_samples=2)
    for icharge in range(len(non_zero_charge_events)):
    #for icharge in range(2):
        test_event_hits = non_zero_charge_hits[:,0][icharge][0:non_zero_charge_events.data['nhit'][:,0][icharge]]
        this_event_light_id = non_zero_charge_light_ev['id'][icharge]
        hits_stack_unfiltered = np.column_stack((test_event_hits.data['x'],test_event_hits.data['y'],test_event_hits.data['z'],test_event_hits.data['E'],np.ones(len(test_event_hits))*this_event_light_id))
        hits_stack = filter_hits(hits_stack_unfiltered)
        if(len(hits_stack)==0):
            continue
        labels = db.fit_predict(hits_stack[:,:3])
        hits_stack_label = np.column_stack((hits_stack[:,0],hits_stack[:,1],hits_stack[:,2],hits_stack[:,3],np.ones(len(hits_stack))*int(this_event_light_id),labels,np.ones(len(hits_stack))*int(file_id)))
        clusterized_hits.extend(hits_stack_label.tolist())
        temp_n_clusters = 0

        for l in np.unique(labels):
            if(l!=-1):
                this_l_hits = hits_stack_label[hits_stack_label[:,5]==l]
                n_hits_clusters.append(len(this_l_hits))
                E_clusters.append(np.sum(this_l_hits[:,3]))
                cluster_light_ev_id.append([l,this_event_light_id])
                temp_n_clusters+=1
            else:
                continue
        n_cluster.append(temp_n_clusters)

    out_dataset["clusters"] = clusterized_hits


    return out_dataset



all_clusters = []
print("Starting file processing...")

# Filter out .json files 
file_list = os.listdir(input_dataset)
file_list = [f for f in file_list if not f.endswith(".json")]

for file_count, ifile in enumerate(file_list):

    # Run over 10% of the dataset
    if DEBUG and file_count >= 5:
        break

    this_file = os.path.join(input_dataset, ifile)
    print(this_file)

    try:
        temp_out = CL_AmBe_analysis(
            this_file,
            file_count,
            job_config
        )
        all_clusters.extend(temp_out["clusters"])

    except Exception as e:
        print(f"[WARNING] Failed processing {this_file}: {e}")
        continue


print("\n Showing amount of clusters per file:")
all_clusters_array = np.array(all_clusters)
for ifile in np.unique(all_clusters_array[:,6]):
    print(f"Dimensions of file {ifile} {all_clusters_array[all_clusters_array[:,6]==ifile].shape}")


print(f"\nSaving clusters to a csv file: {out_clusters}")
df = pd.DataFrame(all_clusters_array, columns=[f"c{i}" for i in range(7)])
df["id"] = (
    df["c6"].astype(str)
    + "::" + df["c4"].astype(str)
    + "::" + df["c5"].astype(str)
)

df.to_csv(out_clusters)
print("\nThis script has finished successfully, happy analysis!") 