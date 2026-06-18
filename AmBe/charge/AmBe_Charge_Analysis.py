import h5py as h5 

import matplotlib.pyplot as plt
from matplotlib import cm, colors
import matplotlib.patches as mpatches
from matplotlib.colors import BoundaryNorm
from matplotlib import colors, ticker

import numpy as np
import os, sys
import traceback
import glob
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


'''
AmBe analysis code for running with nohup
'''

# Configure your analysis here 
# This debug mode will process only the 10% of the dataset , use this if looking at source data
DEBUG = False
MULTI = False

def filter_hits(hits_set):
    # Remove hits with negative energy
    hits_set = hits_set[hits_set[:,3] > 0.]
    # Remove hits with any NaN field
    hits_set = hits_set[~np.isnan(hits_set).any(axis=1)]
    return hits_set

def CL_AmBe_analysis(input_file,file_id,single=True,clust_eps=1,clust_min_samples=4):
    '''
    Produces AmBe analysis objects

    Column names:
    x, y, z, E, Q, light_id, cluster_label, file_id

    '''

    h5_file = h5flow.data.H5FlowDataManager(input_file,'r')
    g_triggers = None
    b_triggers = None

    # Initialize output dataset 
    out_dataset = {
        "clusters":None
    }

    if(single):
        g_triggers, b_triggers = classify_triggers_single(h5_file,debug=False)
    
    else: 
        first_trig = check_first_trig(h5_file,291)
        parity_str = None
        if(first_trig):
            parity_str = "odd"
        else:
            parity_str = "even"
        print(f"Parity of this file: {parity_str}")
        g_triggers, b_triggers = classify_triggers(h5_file,parity_str,debug=False)

    #print(f"List of good triggers: {g_triggers}")

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

    db = DBSCAN(eps=clust_eps,min_samples=clust_min_samples)
    for icharge in range(len(non_zero_charge_events)):
    #for icharge in range(2):
        test_event_hits = non_zero_charge_hits[:,0][icharge][0:non_zero_charge_events.data['nhit'][:,0][icharge]]
        this_event_light_id = non_zero_charge_light_ev['id'][icharge]
        hits_stack_unfiltered = np.column_stack((test_event_hits.data['x'],test_event_hits.data['y'],test_event_hits.data['z'],test_event_hits.data['E'],test_event_hits.data['Q'],np.ones(len(test_event_hits))*this_event_light_id))
        hits_stack = filter_hits(hits_stack_unfiltered)
        if(len(hits_stack)==0):
            continue
        labels = db.fit_predict(hits_stack[:,:3])
        hits_stack_label = np.column_stack((hits_stack[:,0],hits_stack[:,1],hits_stack[:,2],hits_stack[:,3],hits_stack[:,4],np.ones(len(hits_stack))*int(this_event_light_id),labels,np.ones(len(hits_stack))*int(file_id)))
        clusterized_hits.extend(hits_stack_label.tolist())
        temp_n_clusters = 0

        for l in np.unique(labels):
            if(l!=-1):
                this_l_hits = hits_stack_label[hits_stack_label[:,6]==l]
                n_hits_clusters.append(len(this_l_hits))
                E_clusters.append(np.sum(this_l_hits[:,3]))
                cluster_light_ev_id.append([l,this_event_light_id])
                temp_n_clusters+=1
            else:
                continue
        n_cluster.append(temp_n_clusters)

    out_dataset["clusters"] = clusterized_hits

    return out_dataset

def get_AmBe_analysis_data(input_file):
    all_clusters = []

    for file_count, ifile in enumerate(os.listdir(input_file)):

        # Run over 10% of the dataset
        if DEBUG and file_count >= int(len(os.listdir(input_file))*0.1):
            break

        this_file = os.path.join(input_file, ifile.decode('utf-8'))
        print(this_file)

        try:
            temp_out = CL_AmBe_analysis(
                this_file,
                file_count,
                single=not MULTI
            )
            all_clusters.extend(temp_out["clusters"])

        except Exception as e:
            print(f"[WARNING] Failed processing {this_file}: {e}")
            continue

    all_clusters_array = np.array(all_clusters)
    return all_clusters_array


# Load source data clustered with eps=1cm, minimum_cluster_size=4
df_eps1size4 = pd.read_csv('../output/eps1_minsamples4/ambe_bin2_one_trig_32us_window_eps1size4.csv')

# Load no source data clustered with eps=1cm, minimum_cluster_size=4
df_nosource_eps1size4 = pd.read_csv('../output/eps1_minsamples4/nosource_ambe_bin2_one_trig_32us_window_eps1size4.csv')


# Get cluster energies and cluster hit count
source_eps1size4_clusterE = []
source_eps1size4_clusterhitcount = []

nosource_eps1size4_clusterE = []
nosource_eps1size4_clusterhitcount = []

# select as many triggers as the dataset with the least triggers:
df_eps1size4_trig_ids = df_eps1size4['file_id'].astype(str)+ '::' + df_eps1size4['light_id'].astype(str)
df_nosource_eps1size4_trig_ids = df_nosource_eps1size4['file_id'].astype(str)+ '::' + df_nosource_eps1size4['light_id'].astype(str)

n = min([len(np.unique(df_eps1size4_trig_ids)), len(np.unique(df_nosource_eps1size4_trig_ids))])

for i in np.unique(df_eps1size4_trig_ids)[:n]:
    temp_ids = df_eps1size4['id'][(df_eps1size4_trig_ids==i) & (df_eps1size4['cluster_label']!=-1)]
    for j in np.unique(temp_ids):
        source_eps1size4_clusterE.append(sum(df_eps1size4['E'][df_eps1size4['id']==j]))
        source_eps1size4_clusterhitcount.append(len(df_eps1size4['E'][df_eps1size4['id']==j]))

print('1/2 Completed')

for i in np.unique(df_nosource_eps1size4_trig_ids)[:n]:
    temp_ids = df_nosource_eps1size4['id'][(df_nosource_eps1size4_trig_ids==i) & (df_nosource_eps1size4['cluster_label']!=-1)]
    for j in np.unique(temp_ids):
        nosource_eps1size4_clusterE.append(sum(df_nosource_eps1size4['E'][df_nosource_eps1size4['id']==j]))
        nosource_eps1size4_clusterhitcount.append(len(df_nosource_eps1size4['E'][df_nosource_eps1size4['id']==j]))

print('2/2 Completed')


# Visualize and compare

# Cluster energy

plt.figure(figsize=(12, 6))

plt.hist(source_eps1size4_clusterE, color='blue', histtype='step', bins=np.arange(0,10,0.2), label='Source Data (eps1 size4)')
plt.hist(nosource_eps1size4_clusterE, color='red', histtype='step', bins=np.arange(0,10,0.2), label='No Source Data (eps1 size4)')

plt.xlabel('Energy of Clusters (MeV)')
plt.ylabel('Cluster Count')
plt.grid(True)
#plt.yscale('log')
#plt.ylim((0,10))
plt.legend()
plt.show()
plt.savefig(f'../output/plots/eps1_maxsize4_tot_cluster_E_{n}clusts.png')


# Cluster hit count

plt.figure(figsize=(12, 6))

plt.hist(source_eps1size4_clusterhitcount, color='blue', histtype='step', bins=np.arange(0,10,1), label='Source Data (eps1 size4)')
plt.hist(nosource_eps1size4_clusterhitcount, color='red', histtype='step', bins=np.arange(0,10,1), label='No Source Data (eps1 size4)')

plt.xlabel('Number of Hits in Clusters')
plt.ylabel('Cluster Count')
plt.grid(True)
#plt.yscale('log')
#plt.ylim((0,10))
plt.legend()
plt.show()
plt.savefig(f'../output/plots/eps1_maxsize4_tot_cluster_hitcount_{n}clusts.png')


source_eps1size4_clusterE = np.array(source_eps1size4_clusterE)
source_eps1size4_clusterhitcount = np.array(source_eps1size4_clusterhitcount)

nosource_eps1size4_clusterE = np.array(nosource_eps1size4_clusterE)
nosource_eps1size4_clusterhitcount = np.array(nosource_eps1size4_clusterhitcount)


# Divide up the clusters with less than 5 hits and more than 5 hits

source_eps1size4_capturelike_E = source_eps1size4_clusterE[source_eps1size4_clusterhitcount>=5]
source_eps1size4_inelasticlike_E = source_eps1size4_clusterE[source_eps1size4_clusterhitcount<5]

nosource_eps1size4_capturelike_E = nosource_eps1size4_clusterE[nosource_eps1size4_clusterhitcount>=5]
nosource_eps1size4_inelasticlike_E = nosource_eps1size4_clusterE[nosource_eps1size4_clusterhitcount<5]


# Cluster energy

plt.figure(figsize=(12, 6))

plt.hist(source_eps1size4_capturelike_E, color='blue', histtype='step', bins=np.arange(0,6,0.2), label='Source Data (eps1 size4)')
plt.hist(nosource_eps1size4_capturelike_E, color='red', histtype='step', bins=np.arange(0,6,0.2), label='No Source Data (eps1 size4)')

plt.xlabel('Energy of Clusters (MeV)')
plt.ylabel('Cluster Count')
plt.title(r'Clusters with $\geq 5 hits$')
plt.grid(True)
#plt.yscale('log')
#plt.ylim((0,10))
plt.legend()
plt.show()
plt.savefig(f'../output/plots/eps1_maxsize4_capt_cluster_E_{n}clusts.png')


plt.figure(figsize=(12, 6))

plt.hist(source_eps1size4_inelasticlike_E, color='blue', histtype='step', bins=np.arange(0,6,0.2), label='Source Data (eps1 size4)')
plt.hist(nosource_eps1size4_inelasticlike_E, color='red', histtype='step', bins=np.arange(0,6,0.2), label='No Source Data (eps1 size4)')

plt.xlabel('Energy of Clusters (MeV)')
plt.ylabel('Cluster Count')
plt.title('Clusters with < 5 hits')
plt.grid(True)
#plt.yscale('log')
#plt.ylim((0,10))
plt.legend()
plt.show()
plt.savefig(f'../output/plots/eps1_maxsize4_inelastic_cluster_E_{n}clusts.png')


# Plot the difference
bins_range = np.arange(0,6,0.2)
counts1, _ = np.histogram(source_eps1size4_capturelike_E, bins=bins_range)
counts2, _ = np.histogram(nosource_eps1size4_capturelike_E, bins=bins_range)

# Calculate the difference
diff = counts1 - counts2

# Plot the difference
plt.bar(bins_range[:-1], diff, width=np.diff(bins_range), align='edge', color='orange', alpha=0.7)
plt.xlabel('Energy of Clusters (MeV)')
plt.ylabel('Cluster Count')
plt.axhline(0, color='black', linestyle='--') # Add baseline
plt.show()
plt.savefig(f'../output/plots/eps1_maxsize4_capt_difference_cluster_E_{n}clusts.png')