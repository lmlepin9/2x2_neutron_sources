import h5py
import numpy as np 
from utils import *



def PNS_peak_analysis(f):

    E_pgammas = []
    nhits_gamma = []
 
    E_pgamma_hit = []
    E_hit_sum = [] 

    nhits_peak_gamma = []
    E_pgamma_hit_peak = []
    E_hit_sum_peak = [] 

    E_hit_peak = []

    seg = f['mc_truth/segments/data']
    traj = f['mc_truth/trajectories/data']



    for flow_entry in range(len(f['charge/events/data'])):
        # Get prompt hits and their associations
        phits_backtrack, phits = get_charge_event_hits(flow_entry, f)
        #print("Hits event numbers (should be just one!): ", np.unique(phits_backtrack['event_ids']))

        # Skip if zero hits
        if(len(phits)==0):
            continue
        event_num = phits_backtrack['event_ids'][0][0]
        # Get trajectories and segments 
        ev_seg = seg[seg['event_id']==event_num]
        ev_traj = traj[traj['event_id']==event_num]

        true_hits_assn = []

        for i in range(len(phits_backtrack)):
            #print(f"Printing data for hit {i}: ")
            hit_info = hit_backtracker(phits_backtrack[i],phits[i],ev_seg,ev_traj)
            if(hit_info == -1):
                #print("\n")
                continue
            else:
                true_hits_assn.append(hit_info) 
        
        # Create array of unique t_start 
        t_start = []
        for element in true_hits_assn:
            t_start.append(element['p_trajectory']['t_start'])
        t_start = np.unique(t_start)

        # Create as many sub-groups as vertices 
        groups_of_ixn = [[] for ts in t_start]

        # Group hits belonging to the same n-Ar vertex 
        temp_pgamma_traj = []

        temp_segs = []

        for hit in true_hits_assn:
            if(hit['p_trajectory']['pdg_id'] == 22):
                temp_tuple = [hit['p_trajectory']['vertex_id'][0], hit['p_trajectory']['traj_id'][0]]
                temp_segs.append(temp_tuple)
            p_ts = hit['p_trajectory']['t_start']
            ts_idx = np.where(t_start == p_ts)
            groups_of_ixn[ts_idx[0][0]].append(hit)

            temp_tuple = (hit['p_trajectory']['vertex_id'], hit['p_trajectory']['traj_id'],  hit['p_trajectory']['E_start'])
            if((temp_tuple not in temp_pgamma_traj) and hit['p_trajectory']['pdg_id'] == 22):
                temp_pgamma_traj.append(temp_tuple)
            
        E_pgammas.extend([t[2][0] for t in temp_pgamma_traj])

        temp_segs =np.unique(temp_segs,axis=0).tolist()
        groups_seg = [[] for seg in temp_segs]
        for hit in true_hits_assn:
            seg_id = [hit['p_trajectory']['vertex_id'][0], hit['p_trajectory']['traj_id'][0]]
            if(seg_id in temp_segs):
                seg_idx = temp_segs.index(seg_id)
                groups_seg[seg_idx].append(hit)

            
        for g in groups_seg:
            nhits_gamma.append(len(g))
            temp_energies = np.array([h['hit']['E'] for h in g])
            E_pgamma_hit.append(g[0]['p_trajectory']['E_start'][0])
            E_hit_sum.append(np.sum(temp_energies))
            #print(temp_energies)
            if((g[0]['p_trajectory']['E_start'] >=1.4 ) and g[0]['p_trajectory']['E_start'] <1.5 and len(g) > 1 ):
                nhits_peak_gamma.append(len(g)) 
                E_pgamma_hit_peak.append(g[0]['p_trajectory']['E_start'][0])
                E_hit_sum_peak.append(np.sum(temp_energies))
                E_hit_peak.extend(temp_energies)
                if(len(g) == 3):
                    print(f"Event ID of 3 hits event: {g[0]['p_trajectory']['event_id'][0]}")
                    for h in g:
                        print(h['hit']['x'], h['hit']['y'], h['hit']['z'])
                    print(np.sum(temp_energies))

        

    out_dict = {"E_truth_gamma":E_pgammas,
                "E_truth_gamma_hit":E_pgamma_hit,
                "E_hit_sum":E_hit_sum,
                "n_gamma_hits":nhits_gamma,
                "E_gamma_peak":E_pgamma_hit_peak,
                "E_hit_sum_peak":E_hit_sum_peak,
                "n_peak_hits":nhits_peak_gamma,
                "E_hit_peak":E_hit_peak
                }
    return out_dict



def display_hit_assn_data(true_hits_assn):
    for hit in true_hits_assn:
        if(hit["has_parent"] == False):
            print(f"Trajectory {hit['trajectory']['pdg_id']}")
            print(f"Trajectory ID: {hit['trajectory']['traj_id']}")
            print(f"Trajectory Parent ID: {hit['trajectory']['parent_id']}")
            print(f"Trajectory process: {hit['trajectory']['start_process']}::{hit['trajectory']['start_subprocess']}")
            continue
        else:
            print(f"Trajectory PDG: {hit['trajectory']['pdg_id']}")
            print(f"Trajectory ID: {hit['trajectory']['traj_id']}")
            print(f"Trajectory Parent ID: {hit['trajectory']['parent_id']}")
            print(f"Trajectory process: {hit['trajectory']['start_process']}::{hit['trajectory']['start_subprocess']}")
            print(f"Parent trajectory PDG: {hit['p_trajectory']['pdg_id']}")
            print(f"Parent Trajectory ID: {hit['p_trajectory']['traj_id']}")
            print(f"Parent Trajectory Parent ID: {hit['p_trajectory']['parent_id']}")
            print(f"Parent trajectory process: {hit['p_trajectory']['start_process']}::{hit['p_trajectory']['start_subprocess']}")
    

        if(hit["has_gparent"]==True):
            print(f"GParent trajectory {hit['gp_trajectory']['pdg_id']}")
            print(f"GParent Trajectory ID: {hit['gp_trajectory']['traj_id']}")
            print(f"GParent trajectory {hit['gp_trajectory']['start_process']}::{hit['gp_trajectory']['start_subprocess']}")
        print("------------------------")



def AmBe_captures(f):
    nhit_captures = []
    Ehit_captures = [] 
    nhit_elastic = [] 

    # Truth 
    seg = f['mc_truth/segments/data']
    traj = f['mc_truth/trajectories/data']

    zero_hit_counter = 0
    print(f"Number of charge events {len(f['charge/events/data'])}")
    for flow_entry in range(len(f['charge/events/data'])):
        # Get prompt hits and their associations
        phits_backtrack, phits = get_charge_event_hits(flow_entry, f)
        #print("Hits event numbers (should be just one!): ", np.unique(phits_backtrack['event_ids']))

        # Skip if zero hits
        if(len(phits)==0):
            zero_hit_counter+=1
            continue
        event_num = phits_backtrack['event_ids'][0][0]
        # Get trajectories and segments 
        ev_seg = seg[seg['event_id']==event_num]
        ev_traj = traj[traj['event_id']==event_num]

        true_hits_assn = []

        print(f"Number of hits: {len(phits_backtrack)}")

        for i in range(len(phits_backtrack)):
            hit_info = hit_backtracker_mod(phits_backtrack[i],phits[i],ev_seg,ev_traj)
            if(hit_info == -1):
                continue
            else:
                true_hits_assn.append(hit_info)

        # Print hit-assn data 
        display_hit_assn_data(true_hits_assn)
        temp_nhits = 0
        temp_nhits_elastic = 0
        temp_capture_E = 0
        for hit in true_hits_assn:
            p_traj_process = ""
            gp_traj_process = ""
            traj_process=f"{hit['trajectory']['start_process'][0]}::{hit['trajectory']['start_subprocess'][0]}"

            if(hit["has_parent"]):
                p_traj_process=f"{hit['p_trajectory']['start_process'][0]}::{hit['p_trajectory']['start_subprocess'][0]}"

            if(hit["has_gparent"]):
                gp_traj_process=f"{hit['gp_trajectory']['start_process'][0]}::{hit['gp_trajectory']['start_subprocess'][0]}"

            
            # Check if parent or gp were produced in capture
            if(p_traj_process == "4::131" or gp_traj_process == "4::131"):
                temp_nhits+=1
                temp_capture_E+=hit["hit"]["E"]
            elif(traj_process == "4::111" or hit["trajectory"]["parent_id"][0]==-1):
                temp_nhits_elastic+=1
            else:
                continue 
        if(temp_nhits >= 1):
            nhit_captures.append(temp_nhits)
            Ehit_captures.append(temp_capture_E)
        if(temp_nhits_elastic > 0):
            nhit_elastic.append(temp_nhits_elastic)
    
    out_dict = {"nhit_captures":nhit_captures,
                "Ehit_captures":Ehit_captures,
                "nhit_elastic":nhit_elastic}
    return out_dict