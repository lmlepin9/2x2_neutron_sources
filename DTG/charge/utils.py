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




def hit_backtracker(hit_mc_assn, hit, ev_seg, ev_traj):

    '''
    Returns a dictionary containing:
    hit info,
    segment,
    trajectory,
    parent trajectory,
    grand dad trajectory  
    '''

    out_dict={}

    if(hit_mc_assn['segment_ids'][0] == -1):
        #print("This hit likely does not have a segment associated...")
        #print("First segment id: ",  hit_mc_assn['segment_ids'][0])
        return -1 

    else:

        hit_seg_num = hit_mc_assn['segment_ids'][hit_mc_assn['fraction'].argmax()]
        hit_seg = ev_seg[ev_seg['segment_id'] == hit_seg_num]

        #print(hit_seg_num)
        #print(hit_seg['traj_id'])

        # We go up to the "grandpa"
        hit_traj = ev_traj[(ev_traj['traj_id'] == hit_seg['traj_id'][0]) & (ev_traj['vertex_id'] == hit_seg['vertex_id'])]
        if(hit_traj['parent_id']==-1):
            return -1
        hit_p_traj = ev_traj[(ev_traj['traj_id'] == hit_traj['parent_id']) & (ev_traj['vertex_id'] == hit_traj['vertex_id'])]
        #print(hit_traj['pdg_id'])
        #print(hit_traj['parent_id'])
        #print(len(ev_traj['traj_id']))
        #print(len(hit_p_traj['parent_id'])) 
        hit_gp_traj = ev_traj[(ev_traj['traj_id'] == hit_p_traj['parent_id']) & (ev_traj['vertex_id'] == hit_p_traj['vertex_id'])]




        out_dict["hit"] = hit
        out_dict["segment"] = hit_seg
        out_dict["trajectory"] = hit_traj
        out_dict["p_trajectory"] = hit_p_traj
        out_dict["gp_trajectory"] = hit_gp_traj

        #print(hit_traj['pdg_id'])
        #print(hit_p_traj['pdg_id'])
        #print(hit_gp_traj['pdg_id'])

        return out_dict



def hit_backtracker_mod(hit_mc_assn, hit, ev_seg, ev_traj):

    '''
    Returns a dictionary containing:
    hit info,
    segment,
    trajectory,
    parent trajectory,
    grand dad trajectory  
    '''

    out_dict={}

    if(hit_mc_assn['segment_ids'][0] == -1):
       # print("This hit likely does not have a segment associated...")
       # print("First segment id: ",  hit_mc_assn['segment_ids'][0])
        return -1 

    else:

        hit_seg_num = hit_mc_assn['segment_ids'][hit_mc_assn['fraction'].argmax()]
        hit_seg = ev_seg[ev_seg['segment_id'] == hit_seg_num]

        #print(hit_seg_num)
        #print(hit_seg['traj_id'])

        # We go up to the "grandpa"  
        has_p = False
        has_gp = False
        hit_traj = ev_traj[(ev_traj['traj_id'] == hit_seg['traj_id'][0]) & (ev_traj['vertex_id'] == hit_seg['vertex_id'])]
        hit_p_traj = -1
        hit_gp_traj = -1

        # Attempt to create p trajs and gp trajs keys if any  
     
        if(hit_traj["traj_id"] !=0):
            hit_p_traj = ev_traj[(ev_traj['traj_id'] == hit_traj['parent_id']) & (ev_traj['vertex_id'] == hit_traj['vertex_id'])]
            has_p = True
        else:
            has_p = False

        try:
            if(hit_p_traj['traj_id']!=0):
                hit_gp_traj = ev_traj[(ev_traj['traj_id'] == hit_p_traj['parent_id']) & (ev_traj['vertex_id'] == hit_p_traj['vertex_id'])]
                has_gp = True 

        except Exception as e:
            has_gp = False
            

        out_dict["hit"] = hit
        out_dict["segment"] = hit_seg
        out_dict["trajectory"] = hit_traj
        out_dict["has_parent"] = has_p 
        out_dict["p_trajectory"] = hit_p_traj
        out_dict["has_gparent"] = has_gp 
        out_dict["gp_trajectory"] = hit_gp_traj

        return out_dict
