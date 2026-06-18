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
Script for running AmBe MC + No Source overlay with nohup
'''


# Load no source data clustered with eps=1cm, minimum_cluster_size=4
df_nosource_eps1size4 = pd.read_csv('../output/eps1_minsamples4/nosource_ambe_bin2_one_trig_32us_window_eps1size4.csv')

def overlay_MC_Cosmic(cosmic_file, MC_file, clust_eps=1,clust_min_samples=4):
    '''
    Overlap each MC event (currently without light info) with a cosmic event to generate a new dataframe
    
    If there are less cosmic triggers than MC events there will be a notice of how many events were successfully overlapped
    '''

    file_id = 0
    mc_hit_arr = np.empty(9)

    # Load MC
    for file in glob.iglob(MC_file):
        with h5.File(file, 'r') as f:
            traj = f['mc_truth/trajectories/data']
            seg = f['mc_truth/segments/data']
            for event_id in np.unique(traj['event_id']):
                my_entry = event_id-1
                ev_traj= traj[traj['event_id']==event_id]
                ev_seg= seg[seg['event_id']==event_id]
                prompt_hits_backtrack, prompt_hits = get_charge_event_hits(my_entry,f)
                new_hits = hit_backtracker(prompt_hits_backtrack, prompt_hits, ev_seg, ev_traj)

                # Exclude negative hits
                positive_hits = new_hits[new_hits['E']>=0]

                # Use parent neutron id as light trigger id since they should correspond with each pmt id from data
                # All cluster ids are -2 for now as placeholder
                # All ids are 'nan' for now as placeholder
                mc_hit_arr = np.vstack([mc_hit_arr, np.column_stack([positive_hits['x'], positive_hits['y'], positive_hits['z'], positive_hits['E'], positive_hits['Q'], 1.0*positive_hits['parent_neutron_id'], -2*np.ones(len(positive_hits['x'])), file_id*np.ones(len(positive_hits['x'])), np.full(len(positive_hits['x']),fill_value='nan')])])
            file_id += 1

    mc_df = pd.DataFrame(mc_hit_arr, columns=['x', 'y', 'z', 'E', 'Q', 'light_id', 'cluster_label', 'file_id', 'id'])
    cosmic_df = pd.read_csv(cosmic_file)

    #mc_hit_trig_ids = mc_hit_arr[:,7].astype(str) + '::' + mc_hit_arr[:,5].astype(str)
    mc_hit_trig_ids = mc_df['file_id'].astype(str) + '::' + mc_df['light_id'].astype(str)
    cosmic_og_trig_ids = cosmic_df['file_id'].astype(str)+ '::' + cosmic_df['light_id'].astype(str)
    cosmic_og_trig_ids_unique = np.unique(cosmic_og_trig_ids)

    print('begin overlay')

    # Empty array for overlays
    overlay_arr = np.empty(9)
    for index,i in enumerate(np.unique(mc_hit_trig_ids)):
        cosmic_temp = cosmic_df[cosmic_og_trig_ids==cosmic_og_trig_ids_unique[index]]
        print(cosmic_temp)
        # Change file and light ids of the cosmic trigs
        cosmic_temp['file_id'] = mc_df['file_id'][index]
        cosmic_temp['light_id'] = mc_df['light_id'][index]
        overlay_arr = np.vstack([overlay_arr, np.vstack([mc_df[mc_hit_trig_ids==i], cosmic_temp])])
        print(cosmic_temp)
        print('~~~~~~')
    print(overlay_arr)

    # Convert the overlayed array to a dataframe
    overlay_df = pd.DataFrame(overlay_arr, columns=['x', 'y', 'z', 'E', 'Q', 'light_id', 'cluster_label', 'file_id', 'id'])

    # Perform clustering on overlayed dataset
    db = DBSCAN(eps=clust_eps,min_samples=clust_min_samples)
    # Generate a list of unique light trig_ids
    trig_ids = overlay_df['file_id'].astype(str)+ '::' + overlay_df['light_id'].astype(str)

    # Overlap every mc neutron with a cosmic trigger (assuming there's less mc neutrons than trigger)
    for i in np.unique(mc_hit_trig_ids):
        if len(np.unique(overlay_arr[:,-1][trig_ids==i]))!=1:
            print('yo')
            labels = db.fit_predict(overlay_arr[:,:3][trig_ids==i])
            # Change cluster labels to results based on the overlay
            overlay_df.loc[trig_ids==i,'cluster_label'] = labels
            # temporarily define the ids of clustered hits as something identifiable
            overlay_df.loc[trig_ids==i,'id'] = 'clustered'
        else:
            print(np.unique(overlay_arr[:,-1][trig_ids==i]))

    # Eliminate triggers that did not get overlayed
    final_overlay_df = overlay_df.drop(np.where(overlay_df['id']!='clustered')[0])
    final_overlay_df['id']=final_overlay_df['file_id'].astype(str) +'::'+ final_overlay_df['light_id'].astype(str) +'::'+ final_overlay_df['cluster_label'].astype(str)
    print(f'Total number of neutrons in MC file: {len(np.unique(mc_hit_trig_ids))}')
    print(f'Total number of triggers in cosmis file: {len(np.unique(trig_ids))}')
    print(f'Total number of overlay events generated: {len(np.unique(final_overlay_df["file_id"].astype(str) +"::"+ final_overlay_df["light_id"].astype(str)))}')
    print(f'Total number of hits in all overlayed events: {len(final_overlay_df["file_id"])}')
    return final_overlay_df

cosmic_data = '/global/cfs/cdirs/dune/users/edgarmao/NeutronSim/Analysis/2x2_neutron_sources/AmBe/output/eps1_minsamples4/nosource_ambe_bin2_one_trig_32us_window_eps1size4.csv'
#MC_data = '/global/cfs/cdirs/dune/users/lmlepin/2x2_neutron_prod/AmBe_tests/2x2_AmBe_in_mod2_prompt_window_test_11-19-2025_MOD.FLOW.hdf5'
#MC_data = '/global/cfs/cdirs/dune/users/lmlepin/2x2_neutron_prod/AmBe_Prod_V4/FLOW/*.hdf5'
MC_data = '/global/cfs/cdirs/dune/users/lmlepin/2x2_neutron_prod/AmBe_top_mod2_PROD_03-21/FLOW/*.hdf5'
#MC_data = '/global/cfs/cdirs/dune/users/lmlepin/2x2_neutron_prod/AmBe_top_mod2_PROD_03-21/FLOW/2x2_QGSP_BERT_HP_AmBe_1774119367_0_TIME_MOD.FLOW.hdf5'

# Run the overlay code
df_nosource_MC_overlay = overlay_MC_Cosmic(df_nosource_eps1size4, MC_data)

# Get cluster energy
nosource_MC_overlay_clustE = []

for i in np.unique(df_nosource_MC_overlay['id']):
    #print(df_nosource_MC_overlay['E'][df_nosource_MC_overlay['id']==i])
    nosource_MC_overlay_clustE.append(sum(df_nosource_MC_overlay['E'][df_nosource_MC_overlay['id']==i].astype(float)))

nosource_MC_overlay_clustE = np.array(nosource_MC_overlay_clustE)

# Visualize the overlayed results

# Cluster energy

plt.figure(figsize=(12, 6))

#plt.hist(source_eps1size4_clusterE, color='blue', histtype='step', bins=np.arange(0,10,0.2), label='Source Data (eps1 size4)')
#plt.hist(nosource_eps1size4_clusterE, color='red', histtype='step', bins=np.arange(0,10,0.2), label='No Source Data (eps1 size4)')
plt.hist(nosource_MC_overlay_clustE, color='peru', histtype='step', bins=np.arange(0,10,0.2), label='MC + No Source Overlay (eps1 size4)')

plt.xlabel('Energy of Clusters (MeV)')
plt.ylabel('Cluster Count')
plt.grid(True)
#plt.yscale('log')
#plt.ylim((0,10))
plt.legend()
plt.show()
plt.savefig(f'../output/plots/AmBe_MC_NoSource_Overlay_E_clusts.png')