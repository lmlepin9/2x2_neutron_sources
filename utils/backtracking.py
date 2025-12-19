import h5py
import numpy as np 
import matplotlib.pyplot as plt



def get_daughters(parent_traj, ev_traj):

    daughter_trajs = ev_traj[(ev_traj['parent_id']==parent_traj['traj_id']) &
                             (ev_traj['vertex_id']==parent_traj['vertex_id'])]
    return daughter_trajs


def get_ev_packets_indexes(packets,ev_id):
    ev_packets_mask = []
    i = 0 
    for p in packets:
        if p['event_ids'][0] == ev_id:
            ev_packets_mask.append(i)
        i+=1
    return ev_packets_mask


def get_charge_event_hits(flow_entry, f):

    '''
    This function should return 
    prompt_hit_backtrack entries (if MC)
    and prompt_hit entries
    '''
    
    chits_region = f['charge/events/ref/charge/calib_prompt_hits/ref_region'][flow_entry]
    prompt_hits_backtrack = f['mc_truth/calib_prompt_hit_backtrack/data'][chits_region[0]:chits_region[1]]
    prompt_hits = f['charge/calib_prompt_hits/data'][chits_region[0]:chits_region[1]]
    
    return (prompt_hits_backtrack, prompt_hits) 



def get_ancestry(this_traj_id, ev_traj):


    '''
    Navigate traj_id list until we hit 
    a parent neutron 
    '''


    ancestry = []
    current = this_traj_id
    process = -1


    while True:
        p = ev_traj[ev_traj['traj_id']==current]
        ancestry.append(p['traj_id'])
        if p['pdg_id']==2112:
            process_string=f"{p['end_process'][0]}::{p['end_subprocess'][0]}"
            if(process_string=="4::121"):
                process = 0
            elif(process_string=="4::131"):
                process = 1

            break  # break once we hit a parent neutron
        elif ((p['parent_id']==-1) and p['pdg_id']!=2112):
            process=2
            break # break if we hit a primary particle, this is a non-neutron trajectory
        current = p['parent_id']
    return ancestry, process




def hit_backtracker(hit_mc_assn, hit, ev_seg, ev_traj):

    '''
    The idea is that we borrow the hit dataset structure
    and we expand it by adding two more fields. 

     - "best_segmend_id" which includes the maximum segment contributing to this hit -> DONE 
     - "Neutron process", which can be
            0 for inelastic
            1 for capture 
            2 for non-neutron hit
     - "parent_neutron_id" if the hit is neutron-induced it will keep the traj_id 
        of the parent neutron. -1 if not neutron-induced 

    The arguments are:
        event hit_mc_assn
        event hits
        event segments
        event trajectories

    Returns the expanded hit dataset 

    '''

    # Create output dset first-----------------------------------
    hits_dtype = hit.dtype

    new_fields = [
        ("best_segment_id", np.int32),
        ("neutron_process", np.int32),
        ("parent_neutron_id",np.int32)
    ]

    new_hits_dtype = np.dtype(hits_dtype.descr + new_fields)
    new_hits = np.zeros(hit.shape, dtype=new_hits_dtype)
    for name in hits_dtype.names:
        new_hits[name] = hit[name]

    #----------------------------------------------------------------
    # Fill best segment ID
    max_fractions = np.argmax(hit_mc_assn['fraction'],1)  
    result = hit_mc_assn['segment_ids'][np.arange(hit_mc_assn['segment_ids'].shape[0]), max_fractions]
    new_hits["best_segment_id"] = result 

    #-----------------------------------------------------------------
    # Backtraking 
    ev_traj_ids  = ev_traj['traj_id']
    ev_traj_pdgs = ev_traj['pdg_id']

    for hit in new_hits:
        seg_id = hit['best_segment_id']
        if(seg_id!=-1):
            this_hit_traj = np.unique(ev_traj_ids[ev_traj_ids == ev_seg[ev_seg['segment_id']==seg_id]['traj_id']])
            ancestry, process = get_ancestry(this_hit_traj,ev_traj)
            hit['neutron_process']=process
            hit['parent_neutron_id']=ancestry[-1]

        
        else:
            hit['neutron_process']=2
            hit['parent_neutron_id']=-1

    return new_hits 
