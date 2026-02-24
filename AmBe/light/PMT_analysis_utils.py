import h5py as h5 
import uproot 
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm
import os 

plt.style.use('../../utils/dune.mplstyle')

def min_range_baseline(array, segment_size=25, num_segments=40, num_means=4):

    # You should adjust segment size to the respective readout window length 
    # In neutrino data, 1000 samples, AmBe: 600 samples 

    # Define start and end indices for segments
    indices = np.arange(num_segments + 1) * segment_size  # (41,)
    start_indices, end_indices = indices[:-1], indices[1:]  # (40,)

    # Generate index array for advanced indexing
    segment_range = np.arange(segment_size)  # (25,)
    index_array = start_indices[:, None] + segment_range  # Shape: (40, 25)

    # Extract data from segments using indexing
    sliced_data = array[..., index_array]  # Shape (..., 40, 25)

    # Compute range (peak-to-peak difference) and mean for each segment
    ranges = np.abs(np.ptp(sliced_data, axis=-1))  # Shape (..., 40)
    means = np.mean(sliced_data, axis=-1)  # Shape (..., 40)

    # Mask zero ranges
    mask_zero = (ranges != 0)
    ranges = np.where(mask_zero, ranges, np.nan)
    means = np.where(mask_zero, means, np.nan)

    # Find the ordering of the segments based on the smallest range
    smallest_ordering = np.argsort(ranges, axis=-1)  # Shape (..., 40)

    # Sort means according to the ordering of smallest ranges
    sorted_means = np.take_along_axis(means, smallest_ordering, axis=-1)  # Shape (..., 40)

    # Compute the average of the 2nd, 3rd, and 4th smallest means
    average_mean = np.mean(sorted_means[..., 1:num_means], axis=-1)  # Shape (...)

    # calculate RMS for the ranges of the smallest range segments
    rms = np.sqrt(np.mean(np.square(np.take_along_axis(ranges, smallest_ordering[..., :num_means], axis=-1)), axis=-1))

    return average_mean, rms


# -----------------------------------------------------------
# Read histograms from DQM ROOT files 
# -----------------------------------------------------------
def read_waveforms_from_root(file_path, directory="self"):
    """
    Opens a ROOT file using uproot and extracts all histograms
    from a given directory. Returns a list of numpy arrays representing
    the waveform ADC values.
    """
    waveforms = []
    DC_shift = None 
    with uproot.open(file_path) as f:
        if directory not in f:
            raise ValueError(f"Directory '{directory}' not found in file.")
        dir_obj = f[directory]

        run_info = f["runinfo"]
        DC_shift = run_info["ped"].array(library="np")[0]
        print(f"DC shift {DC_shift} ADC counts")
        # Iterate over all histograms in directory
        for name, obj in dir_obj.items():
            if not hasattr(obj, "to_numpy"):
                continue  # skip non-histogram objects
            values, _ = obj.to_numpy()
            waveforms.append(values)        
    return waveforms, DC_shift


def make_voltage_hist(wvfm, nbins=30):
    # --- Compute histogram data ---
    counts, bin_edges = np.histogram(wvfm, bins=nbins)
    bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])

    # --- Fit a Gaussian to get sigma ---
    mu, sigma = norm.fit(wvfm)

    # --- Find the bin with maximum count ---
    max_bin_index = np.argmax(counts)
    max_bin_center = bin_centers[max_bin_index]

    # --- Apply 2-sigma cut around the histogram maximum ---
    lower_limit = max_bin_center - 0.1 * sigma
    upper_limit = max_bin_center + 0.1 * sigma
    filtered_wvfm = wvfm[(wvfm >= lower_limit) & (wvfm <= upper_limit)]

    # --- Return the filtered array ---
    return filtered_wvfm

def make_waveform_plot(waveform,fig_name,index,voltage=True,version="flow"):

    prompt_window=None
    x_axis_label=None
    if(version=="flow"):
        prompt_window=(115,122)
        x_axis_label="Time ticks [16 ns]"
    else:
        prompt_window=(215,265)
        x_axis_label="Time ticks [2 ns]"



    time_ns = np.arange(len(waveform))
    noise_std = np.std(waveform[0:30])
    plt.figure(figsize=(10, 5))
    plt.plot(time_ns, waveform, color='red', linewidth=1.2)
    plt.axhline(y=1.*noise_std, color='black', linestyle='--', linewidth=1., label=r'1$\sigma$')

    # Draw shaded regions for prompt and total window 
    plt.axvspan(prompt_window[0], prompt_window[1], color='blue', alpha=0.3, hatch='//', label='Prompt window')

    plt.title(f"Waveform {index}",size=15)
    plt.xlabel(x_axis_label)
    if(voltage):
        plt.ylabel("Voltage [V]")
    else:
        plt.ylabel("ADC counts")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.show()




def DC_offset_correction(waveform, offset):
    '''
    DC offset correction for DQM data.
    '''
    waveform_corrected = waveform - offset
    return waveform_corrected



def baseline_correction(wvfm, n_iterations,sigma=1):
    '''
    Make a baseline correction by looking at the distributon 
    of voltages or ADCs
    '''
    for i in range(n_iterations):
        filtered = make_voltage_hist(wvfm,nbins=100)
        wvfm = wvfm - np.mean(filtered)
    return wvfm

def ADC_to_voltage(wvfm):
    # scale waveform to voltage
    signed_14bit_max = 2**13 - 1  # 8191
    volts_per_count = 2.0 / (2 * signed_14bit_max)
    return wvfm*volts_per_count/4.0 # need to check where this four comes from 


def FPrompt_calculation(wvfm_input,version="flow",use_rms=True):
    wvfm = wvfm_input
    if(use_rms):
        threshold = 1*np.std(wvfm[500:600])
        wvfm[wvfm < threshold] = 0
    fprompt = None
    prompt_window = None
    if(version=="flow"):
         prompt_window=(115,122)
    else:
         prompt_window=(215,265)
    prompt_int = np.sum(wvfm[prompt_window[0]:prompt_window[1]])
    total_int = np.sum(wvfm[prompt_window[0]:300])
    fprompt = prompt_int/total_int
    return fprompt 



def thd_correct(array):
    """
    Can go to a different file
    Baseline corrects waveforms
    """

    max_samples = 600

    # Define start and end indices
    indices = np.arange(0, 20) * 25  # (39,)
    start_indices, end_indices = indices[:-1], indices[1:]  # (39,)

    segment_range = np.arange(25)  # Shape: (25,)
    index_array = start_indices[:, None] + segment_range  # Shape: (39, 25)

    # Extract data using advanced indexing
    sliced_data = array[..., index_array]
    
    ranges = np.ptp(sliced_data, axis=-1)  # Compute range (n, 8, 64, 39)
    means = np.mean(sliced_data, axis=-1)  # Compute mean (n, 8, 64, 39)

    # Find ordering based on the smallest range
    smallest_ordering = np.argsort(ranges, axis=-1)  # Shape (n, 8, 64, 39)

    # Sort means using the ordering
    sorted_means = np.take_along_axis(means, smallest_ordering, axis=-1)  # Shape (n, 8, 64, 39)
    sorted_range = np.take_along_axis(ranges, smallest_ordering, axis=-1)
    # Compute average of 2nd, 3rd, and 4th smallest means
    average_mean = np.mean(sorted_means[..., 1:4], axis=-1)  # Shape (n, 8, 64)
    expanded_mean = average_mean[..., None] 
    broadcasted_mean = np.tile(expanded_mean, (1,max_samples))  
    filtered_wvfm = array - broadcasted_mean

    return filtered_wvfm


def get_dead_SiPMs():
    '''
    Docstring for get_dead_SiPMs

    Returns a 8 by 64 array with the status of the 2x2 SiPMS 
    
    Inactive channels: -1
    Dead channels: 0 
    Active channels: 1

    '''
    dead_array = [np.array([7,10,20]),
    np.array([]),
    np.array([22,54]),
    np.array([27,61]),
    np.array([4,15,36,47]),
    np.array([37]),
    np.array([14,15,20,21,22,23,46,47,52,53,54,55]),
    np.array([4,15])]

    sipm_channels = ([4,5,6,7,8,9] + 
    [10,11,12,13,14,15] + 
    [20,21,22,23,24,25] + 
    [26,27,28,29,30,31] + 
    [36,37,38,39,40,41] + 
    [42,43,44,45,46,47] + 
    [52,53,54,55,56,57] + 
    [58,59,60,61,62,63])

    new_dead_array = np.ones((8,64))*-1
    for i in range(8):

        # Turn on used channels 
        new_dead_array[i][sipm_channels] = 1 

        # Turn off dead channels
        if len(dead_array[i]) > 0:
            new_dead_array[i][dead_array[i]]= 0

    return new_dead_array


def PMT_wvfm_selection(offbeam_wvfm_v1,fprompt_min=0.001,fprompt_max=0.2,width=15):

    '''
    This function returns an array with the waveforms
    passing the PMT trigger selection (by A. White). 

    '''



    pmt_wvfm_v1 = np.array(offbeam_wvfm_v1[:,0,16,:]*(-1), dtype=np.int64) / 4 #The divide by 4 is just removing lowest bits
    pmt_wvfm_v2 = pmt_wvfm_v1 - np.mean(pmt_wvfm_v1[0:50])
    noise_sum_all = np.sum(pmt_wvfm_v2[:,5:100], axis=-1)
    noise_sum_fast = np.sum(pmt_wvfm_v2[:,5:18], axis=-1)
    fast_light = np.sum(pmt_wvfm_v2[:,105:118], axis=-1) - noise_sum_fast
    all_light = np.sum(pmt_wvfm_v2[:,105:200], axis=-1) - noise_sum_all
    fprompt_mask = ((fast_light/all_light) > fprompt_min)*((fast_light/all_light) < fprompt_max)
    thd_mask = (pmt_wvfm_v2[:,100:300] > 70)
    pick_out_low = (np.sum(thd_mask[:,5:120], axis=-1) <= width)
    valid_trig = (fprompt_mask==1) * (pick_out_low==0)
    return valid_trig


def even_or_odd_indices(N, kind="even"):
    """
    Return indices (0-based) for an array of length N.

    Parameters
    ----------
    N : int
        Length of the array
    kind : str
        "even" or "odd"

    Returns
    -------
    range
        Iterable of indices
    """
    if kind not in {"even", "odd"}:
        raise ValueError("kind must be 'even' or 'odd'")

    start = 0 if kind == "even" else 1
    return range(start, N, 2)

def check_first_trig(this_h5_file,trig_period):
    fst_ev = this_h5_file['light/events',0]
    sec_ev = this_h5_file['light/events',1]
    fst_ev_time = fst_ev['tai_ns'][0][0] # The time of any ADC is OK
    sec_ev_time = sec_ev['tai_ns'][0][0] # The time of any ADC is OK
    diff_time = (sec_ev_time - fst_ev_time)*1e-3 # Convert to micro-sec
    print(diff_time)
    print(round(diff_time))
    if(round(diff_time)==trig_period):
        print("The first trigger is a PMT trigger")
        return 0
    else:
        print("The first trigger is a delayed trigger")
        return 1
    

def classify_triggers_single(this_h5_file, debug=True):

    '''
    Docstring for classify_triggers

    This function works with files that have only prompt triggers  

    
    :param this_h5_file: Input h5 file 
    :param debug: run in only a subset of events 

    Returns the IDs of triggers passing the PMT selection, and the ids of the rejected triggers. 

    '''
    N_events = None
    test_PMT_events = None
    if(debug):
        N_events=int(len(this_h5_file['light/events']['data'])*0.1)
        print(f"Running in debug mode with {N_events} events (10 percent)")
    else:
        N_events = len(this_h5_file['light/events']['data'])
        print(f"Running with all the {N_events} events")


    light_events = this_h5_file['light/events',np.arange(N_events)]
    light_wvfm = this_h5_file['light/wvfm',np.arange(N_events)]['samples']   
    good_triggers = PMT_wvfm_selection(light_wvfm,width=31)
    print(f"Fraction of good triggers {len(good_triggers[good_triggers==1])/len(good_triggers)}")
    good_triggers_ids = light_events['id'][good_triggers==1]
    bad_triggers_ids = light_events['id'][good_triggers==0]
    return good_triggers_ids,bad_triggers_ids


def classify_triggers(this_h5_file,parity,debug=True):

    '''
    Docstring for classify_triggers

    This function works with files that have both prompt and delayed triggers. 

    
    :param this_h5_file: Input h5 file
    :param parity: string telling if a file is even (PMT triggers on even entries) or odd (viceversa). 
    :param debug: run in only a subset of events 

    Returns the IDs of triggers passing the PMT selection, and the ids of the rejected triggers. 

    '''


    N_events = None
    test_PMT_events = None
    if(debug):
        N_events=int(len(this_h5_file['light/events']['data'])*0.1)
        print(f"Running in debug mode with {N_events} events (10 percent)")
    else:
        N_events = len(this_h5_file['light/events']['data'])
        print(f"Running with all the {N_events} events")

    test_PMT_events = even_or_odd_indices(N_events,parity)

    light_events = this_h5_file['light/events',test_PMT_events]
    light_wvfm = this_h5_file['light/wvfm',test_PMT_events]['samples']   
    good_triggers = PMT_wvfm_selection(light_wvfm,width=31)
    print(f"Fraction of good trigger {len(good_triggers[good_triggers==1])/len(good_triggers)}")
    good_triggers_ids = light_events['id'][good_triggers==1]
    bad_triggers_ids = light_events['id'][good_triggers==0]
    return good_triggers_ids,bad_triggers_ids