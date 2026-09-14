"""
Shared utilities for DTG (Deuterium-Tritium Generator) light analysis.

Provides baseline correction, trap aggregation, fprompt computation,
pileup detection, energy calibration, and file discovery — all shared
across the DTG analysis notebooks.
"""

import os
import re
import numpy as np
import h5py

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Data directories
NEARLINE_DIR = (
    "/global/cfs/cdirs/dune/www/data/2x2/nearline_run2/flowed_light/"
    "source_dtg_bin2/two_trig_40us_period_500tick/hv_65kV_beamC_25uA/"
    "dtg_30min_thenDecay/"
)
REFLOW_DIR = (
    "/global/cfs/cdirs/dunepro/www/data/nd-production/2x2_run2/reflows/"
    "v0p2.PRELIMINARY/flow/source_dtg_bin2/two_trig_40us_period_500tick/"
    "hv_65kV_beamC_25uA/dtg_30min_thenDecay/"
)
CHARGE_CSV_DIR = (
    "/global/cfs/cdirs/dune/users/lmlepin/cluster_outputs/"
    "DTG_ON_CL_eps_3_minsamp_1/"
)
COSMIC_DIR = (
    "/global/cfs/cdirs/dune/users/mnuland/run2flow/"
    "matched_flowed_run2_new_gains/"
)

# Processing thresholds
PEAK_TICK_FIXED = 82       # fixed peak position for decay data (nearline files)
PEAK_MAX_TICK = 300        # late-peak rejection threshold (DTG-on)
SAT_THRESHOLD = 59000      # raw ADC saturation threshold

# Pileup detection — find_peaks method (DTG-on)
PILEUP_MIN_DISTANCE = 100      # minimum tick separation between peaks
PILEUP_MIN_REL_HEIGHT = 0.5   # secondary peak >= this fraction of main peak

# Pileup detection — rising-tail method (decay)
PILEUP_LOOKBACK = 15           # ticks to look back for rising check
PILEUP_TAIL_REL_HEIGHT = 0.3  # threshold relative to peak amplitude

# Energy calibration
LCM_ENERGY_NORM = 147      # LCM normalization factor (ADC*tick → PE)
ENERGY_SCALE = 0.004       # MeV per PE
N_MODULES = 4              # number of detector modules
N_TPCS = 8                 # total TPCs (2 per module)
EXCLUDE_TPCS = [6]         # TPC 6 excluded (sparking)

# Ar-41 physics
AR41_HALF_LIFE = 109.61    # minutes


# ---------------------------------------------------------------------------
# Light trap definitions
# ---------------------------------------------------------------------------

TRAP_NAME_MAP = [
    dict(adc=0, channels=[4,5,6,7,8,9],      name="ACL 2.01", tpc=0, z_side="-z", position="bottom"),
    dict(adc=0, channels=[10,11,12,13,14,15], name="ACL 2.02", tpc=0, z_side="-z", position="top"),
    dict(adc=0, channels=[20,21,22,23,24,25], name="ACL 2.03", tpc=0, z_side="+z", position="bottom"),
    dict(adc=0, channels=[26,27,28,29,30,31], name="ACL 2.04", tpc=0, z_side="+z", position="top"),
    dict(adc=0, channels=[52,53,54,55,56,57], name="ACL 2.05", tpc=1, z_side="-z", position="bottom"),
    dict(adc=0, channels=[58,59,60,61,62,63], name="ACL 2.06", tpc=1, z_side="-z", position="top"),
    dict(adc=0, channels=[36,37,38,39,40,41], name="ACL 2.07", tpc=1, z_side="+z", position="bottom"),
    dict(adc=0, channels=[42,43,44,45,46,47], name="ACL 2.08", tpc=1, z_side="+z", position="top"),
    dict(adc=1, channels=[4,5,6,7,8,9],      name="LCM 100-102", tpc=0, z_side="-z", position="bottom"),
    dict(adc=1, channels=[10,11,12,13,14,15], name="LCM 103-105", tpc=0, z_side="-z", position="top"),
    dict(adc=1, channels=[20,21,22,23,24,25], name="LCM 106-108", tpc=0, z_side="+z", position="bottom"),
    dict(adc=1, channels=[26,27,28,29,30,31], name="LCM 109-111", tpc=0, z_side="+z", position="top"),
    dict(adc=1, channels=[52,53,54,55,56,57], name="LCM 112-114", tpc=1, z_side="-z", position="bottom"),
    dict(adc=1, channels=[58,59,60,61,62,63], name="LCM 115-117", tpc=1, z_side="-z", position="top"),
    dict(adc=1, channels=[36,37,38,39,40,41], name="LCM 118-120", tpc=1, z_side="+z", position="bottom"),
    dict(adc=1, channels=[42,43,44,45,46,47], name="LCM 121-123", tpc=1, z_side="+z", position="top"),
    dict(adc=2, channels=[4,5,6,7,8,9],      name="ACL 2.09", tpc=2, z_side="-z", position="bottom"),
    dict(adc=2, channels=[10,11,12,13,14,15], name="ACL 2.10", tpc=2, z_side="-z", position="top"),
    dict(adc=2, channels=[20,21,22,23,24,25], name="ACL 2.11", tpc=2, z_side="+z", position="bottom"),
    dict(adc=2, channels=[26,27,28,29,30,31], name="ACL 2.12", tpc=2, z_side="+z", position="top"),
    dict(adc=2, channels=[52,53,54,55,56,57], name="ACL 2.13", tpc=3, z_side="-z", position="bottom"),
    dict(adc=2, channels=[58,59,60,61,62,63], name="ACL 2.14", tpc=3, z_side="-z", position="top"),
    dict(adc=2, channels=[36,37,38,39,40,41], name="ACL 2.15", tpc=3, z_side="+z", position="bottom"),
    dict(adc=2, channels=[42,43,44,45,46,47], name="ACL 2.16", tpc=3, z_side="+z", position="top"),
    dict(adc=3, channels=[20,21,22,23,24,25], name="LCM 124-126", tpc=2, z_side="-z", position="bottom"),
    dict(adc=3, channels=[26,27,28,29,30,31], name="LCM 127-129", tpc=2, z_side="-z", position="top"),
    dict(adc=3, channels=[4,5,6,7,8,9],      name="LCM 130-132", tpc=2, z_side="+z", position="bottom"),
    dict(adc=3, channels=[10,11,12,13,14,15], name="LCM 133-135", tpc=2, z_side="+z", position="top"),
    dict(adc=3, channels=[52,53,54,55,56,57], name="LCM 136-138", tpc=3, z_side="-z", position="bottom"),
    dict(adc=3, channels=[58,59,60,61,62,63], name="LCM 139-141", tpc=3, z_side="-z", position="top"),
    dict(adc=3, channels=[36,37,38,39,40,41], name="LCM 142-144", tpc=3, z_side="+z", position="bottom"),
    dict(adc=3, channels=[42,43,44,45,46,47], name="LCM 145-147", tpc=3, z_side="+z", position="top"),
    dict(adc=4, channels=[42,43,44,45,46,47], name="ACL 2.17",    tpc=4, z_side="-z", position="bottom"),
    dict(adc=4, channels=[36,37,38,39,40,41], name="ACL 2.18",    tpc=4, z_side="-z", position="top"),
    dict(adc=4, channels=[52,53,54,55,56,57], name="LCM 148-150", tpc=4, z_side="+z", position="bottom"),
    dict(adc=4, channels=[58,59,60,61,62,63], name="LCM 151-153", tpc=4, z_side="+z", position="top"),
    dict(adc=4, channels=[26,27,28,29,30,31], name="ACL 2.19",    tpc=5, z_side="-z", position="bottom"),
    dict(adc=4, channels=[20,21,22,23,24,25], name="ACL 2.20",    tpc=5, z_side="-z", position="top"),
    dict(adc=4, channels=[10,11,12,13,14,15], name="ACL 2.21",    tpc=5, z_side="+z", position="bottom"),
    dict(adc=4, channels=[4,5,6,7,8,9],       name="ACL 2.22",    tpc=5, z_side="+z", position="top"),
    dict(adc=5, channels=[42,43,44,45,46,47], name="LCM 154-156", tpc=4, z_side="-z", position="bottom"),
    dict(adc=5, channels=[58,59,60,61,62,63], name="ACL 2.23",    tpc=4, z_side="+z", position="bottom"),
    dict(adc=5, channels=[52,53,54,55,56,57], name="ACL 2.24",    tpc=4, z_side="+z", position="top"),
    dict(adc=5, channels=[36,37,38,39,40,41], name="LCM 157-159", tpc=4, z_side="+z", position="top"),
    dict(adc=5, channels=[26,27,28,29,30,31], name="LCM 160-162", tpc=5, z_side="-z", position="bottom"),
    dict(adc=5, channels=[20,21,22,23,24,25], name="LCM 163-165", tpc=5, z_side="-z", position="top"),
    dict(adc=5, channels=[10,11,12,13,14,15], name="LCM 166-168", tpc=5, z_side="+z", position="bottom"),
    dict(adc=5, channels=[4,5,6,7,8,9],       name="LCM 169-171", tpc=5, z_side="+z", position="top"),
    dict(adc=6, channels=[4,5,6,7,8,9],      name="ACL 2.25", tpc=6, z_side="-z", position="bottom"),
    dict(adc=6, channels=[10,11,12,13,14,15], name="ACL 2.26", tpc=6, z_side="-z", position="top"),
    dict(adc=6, channels=[20,21,22,23,24,25], name="ACL 2.27", tpc=6, z_side="+z", position="bottom"),
    dict(adc=6, channels=[26,27,28,29,30,31], name="ACL 2.28", tpc=6, z_side="+z", position="top"),
    dict(adc=6, channels=[52,53,54,55,56,57], name="ACL 2.29", tpc=7, z_side="-z", position="bottom"),
    dict(adc=6, channels=[58,59,60,61,62,63], name="ACL 2.30", tpc=7, z_side="-z", position="top"),
    dict(adc=6, channels=[36,37,38,39,40,41], name="ACL 2.31", tpc=7, z_side="+z", position="bottom"),
    dict(adc=6, channels=[42,43,44,45,46,47], name="ACL 2.32", tpc=7, z_side="+z", position="top"),
    dict(adc=7, channels=[4,5,6,7,8,9],      name="LCM 172-174", tpc=6, z_side="-z", position="bottom"),
    dict(adc=7, channels=[10,11,12,13,14,15], name="LCM 175-177", tpc=6, z_side="-z", position="top"),
    dict(adc=7, channels=[20,21,22,23,24,25], name="LCM 178-180", tpc=6, z_side="+z", position="bottom"),
    dict(adc=7, channels=[26,27,28,29,30,31], name="LCM 181-183", tpc=6, z_side="+z", position="top"),
    dict(adc=7, channels=[52,53,54,55,56,57], name="LCM 184-186", tpc=7, z_side="-z", position="bottom"),
    dict(adc=7, channels=[58,59,60,61,62,63], name="LCM 187-189", tpc=7, z_side="-z", position="top"),
    dict(adc=7, channels=[36,37,38,39,40,41], name="LCM 190-192", tpc=7, z_side="+z", position="bottom"),
    dict(adc=7, channels=[42,43,44,45,46,47], name="LCM 193-195", tpc=7, z_side="+z", position="top"),
]


def get_trap_indices(detector="lcm", exclude_tpcs=None):
    """Return trap index and TPC arrays for a detector type.

    Parameters
    ----------
    detector : str
        "acl" or "lcm"
    exclude_tpcs : list of int or None
        TPCs to exclude (default: EXCLUDE_TPCS = [6])

    Returns
    -------
    idx : np.ndarray of int
        Indices into TRAP_NAME_MAP
    tpc : np.ndarray of int
        TPC number for each selected trap
    """
    if exclude_tpcs is None:
        exclude_tpcs = EXCLUDE_TPCS
    prefix = "ACL" if detector == "acl" else "LCM"
    idx = np.array([
        i for i, e in enumerate(TRAP_NAME_MAP)
        if e["name"].startswith(prefix) and e["tpc"] not in exclude_tpcs
    ])
    tpc = np.array([TRAP_NAME_MAP[i]["tpc"] for i in idx])
    return idx, tpc


# ---------------------------------------------------------------------------
# Baseline correction
# ---------------------------------------------------------------------------

def thd_correct(array):
    """Threshold-based baseline correction using 25-tick segments.

    For each channel, divides the waveform into 25-tick segments, computes the
    range and mean of each segment, then takes the average of the 2nd and 3rd
    lowest-range segments as the baseline estimate.

    Parameters
    ----------
    array : ndarray, shape (..., n_samples)
        Raw waveform data. Last axis is the time axis (typically 500 samples).

    Returns
    -------
    ndarray : same shape as input, baseline-subtracted.
    """
    n_samples = array.shape[-1]
    num_bins = int((n_samples // 25) + 1)
    indices = np.arange(0, num_bins) * 25
    start_indices = indices[:-1]
    segment_range = np.arange(25)
    index_array = start_indices[:, None] + segment_range

    sliced_data = array[..., index_array]
    ranges = np.abs(np.ptp(sliced_data, axis=-1))
    means = np.mean(sliced_data, axis=-1)

    mask_zero = (ranges != 0)
    ranges = np.where(mask_zero, ranges, np.nan)
    means = np.where(mask_zero, means, np.nan)

    smallest_ordering = np.argsort(ranges, axis=-1)
    sorted_means = np.take_along_axis(means, smallest_ordering, axis=-1)
    average_mean = np.nanmean(sorted_means[..., 1:3], axis=-1)

    fallback_mean = np.mean(array, axis=-1)
    average_mean = np.where(np.isnan(average_mean), fallback_mean, average_mean)

    return array - average_mean[..., None]


# ---------------------------------------------------------------------------
# Trap aggregation
# ---------------------------------------------------------------------------

def sum_to_traps(samples, trap_map=None):
    """Sum ADC channels within each light trap.

    Parameters
    ----------
    samples : ndarray, shape (n_events, 8, 64, n_ticks)
    trap_map : list of dicts, optional (default: TRAP_NAME_MAP)

    Returns
    -------
    ndarray, shape (n_events, n_traps, n_ticks)
    """
    if trap_map is None:
        trap_map = TRAP_NAME_MAP
    n_ev, _, _, n_t = samples.shape
    out = np.zeros((n_ev, len(trap_map), n_t), dtype=np.float64)
    for i, entry in enumerate(trap_map):
        out[:, i, :] = samples[:, entry["adc"], :, :][:, entry["channels"], :].sum(axis=1)
    return out


def sum_to_tpcs(trap_wvfms, trap_map=None):
    """Sum trap waveforms within each TPC.

    Parameters
    ----------
    trap_wvfms : ndarray, shape (n_events, n_traps, n_ticks)
    trap_map : list of dicts, optional (default: TRAP_NAME_MAP)

    Returns
    -------
    ndarray, shape (n_events, 8, n_ticks)
    """
    if trap_map is None:
        trap_map = TRAP_NAME_MAP
    n_ev, _, n_t = trap_wvfms.shape
    out = np.zeros((n_ev, N_TPCS, n_t), dtype=np.float64)
    for i, entry in enumerate(trap_map):
        out[:, entry["tpc"], :] += trap_wvfms[:, i, :]
    return out


# ---------------------------------------------------------------------------
# Fprompt computation
# ---------------------------------------------------------------------------

def compute_fprompt_fixed(trap_wvfms, peak_tick=PEAK_TICK_FIXED):
    """Fixed-window fprompt (for decay data where peak is always at a known tick).

    Parameters
    ----------
    trap_wvfms : ndarray, shape (n_events, n_traps, n_ticks)
    peak_tick : int

    Returns
    -------
    fprompt : ndarray, shape (n_events, n_traps)
    integrals : ndarray, shape (n_events, n_traps) — full waveform integral
    """
    prompt_slice = slice(peak_tick - 5, peak_tick + 10)    # 15 ticks
    total_slice = slice(peak_tick - 5, peak_tick + 195)    # 200 ticks

    fprompt_num = trap_wvfms[:, :, prompt_slice].sum(axis=-1)
    fprompt_den = trap_wvfms[:, :, total_slice].sum(axis=-1)
    fprompt = fprompt_num / fprompt_den
    integrals = trap_wvfms.sum(axis=-1)
    return fprompt, integrals


def compute_fprompt_dynamic(trap_wvfms):
    """Dynamic fprompt — peak found per trap via argmax (for DTG-on data).

    Parameters
    ----------
    trap_wvfms : ndarray, shape (n_events, n_traps, n_ticks)

    Returns
    -------
    fprompt : ndarray, shape (n_events, n_traps)
    integrals : ndarray, shape (n_events, n_traps) — full waveform integral
    peak_idx : ndarray, shape (n_events, n_traps) — tick of peak per trap
    """
    n_t = trap_wvfms.shape[-1]
    peak_idx = trap_wvfms.argmax(axis=-1)  # (n_events, n_traps)

    prompt_idx = np.clip(peak_idx[..., None] + np.arange(-5, 10), 0, n_t - 1)
    total_idx = np.clip(peak_idx[..., None] + np.arange(-5, 195), 0, n_t - 1)

    fprompt_num = np.take_along_axis(trap_wvfms, prompt_idx, axis=-1).sum(axis=-1)
    fprompt_den = np.take_along_axis(trap_wvfms, total_idx, axis=-1).sum(axis=-1)
    fprompt = fprompt_num / fprompt_den
    integrals = trap_wvfms.sum(axis=-1)
    return fprompt, integrals, peak_idx


# ---------------------------------------------------------------------------
# Quality cuts
# ---------------------------------------------------------------------------

def reject_saturation(samples, threshold=SAT_THRESHOLD):
    """Boolean mask: True for events that have any saturated sample.

    Parameters
    ----------
    samples : ndarray, shape (n_events, 8, 64, n_ticks) or (n_events, n_traps, n_ticks)
        Baseline-corrected waveforms.

    Returns
    -------
    ndarray of bool, shape (n_events,)
    """
    return (samples >= threshold).any(axis=tuple(range(1, samples.ndim)))


def reject_late_peaks(trap_wvfms, threshold=PEAK_MAX_TICK):
    """Boolean mask: True for events whose total-sum peak is at or after threshold.

    Parameters
    ----------
    trap_wvfms : ndarray, shape (n_events, n_traps, n_ticks)

    Returns
    -------
    ndarray of bool, shape (n_events,)
    """
    total_wvfm = trap_wvfms.sum(axis=1)
    event_peak_tick = total_wvfm.argmax(axis=-1)
    return event_peak_tick >= threshold


# ---------------------------------------------------------------------------
# Pileup detection
# ---------------------------------------------------------------------------

def detect_pileup_find_peaks(trap_wvfms, min_distance=PILEUP_MIN_DISTANCE,
                             min_rel_height=PILEUP_MIN_REL_HEIGHT):
    """Pileup detection via scipy.signal.find_peaks (DTG-on method).

    Parameters
    ----------
    trap_wvfms : ndarray, shape (n_events, n_traps, n_ticks)

    Returns
    -------
    n_peaks : ndarray of int, shape (n_events, n_traps)
        Number of significant peaks found per trap per event.
    """
    from scipy.signal import find_peaks

    n_ev, n_traps, _ = trap_wvfms.shape
    trap_peak_heights = trap_wvfms.max(axis=-1)
    n_peaks = np.ones((n_ev, n_traps), dtype=np.int8)

    for ev in range(n_ev):
        for trap in range(n_traps):
            threshold = min_rel_height * trap_peak_heights[ev, trap]
            peaks, _ = find_peaks(
                trap_wvfms[ev, trap],
                height=threshold,
                distance=min_distance,
            )
            n_peaks[ev, trap] = len(peaks)

    return n_peaks


def detect_pileup_rising_tail(trap_wvfms, peak_tick=PEAK_TICK_FIXED,
                              lookback=PILEUP_LOOKBACK,
                              rel_height=PILEUP_TAIL_REL_HEIGHT):
    """Pileup detection via rising-after-peak method (decay data method).

    The scintillation tail always decreases after the peak. If the waveform
    is higher at any tick than it was `lookback` ticks earlier (and above the
    amplitude threshold), a second event is present.

    Parameters
    ----------
    trap_wvfms : ndarray, shape (n_events, n_traps, n_ticks)

    Returns
    -------
    n_peaks : ndarray of int8, shape (n_events, n_traps)
        1 = clean, 2 = pileup detected.
    """
    total_end = peak_tick + 195  # end of total window
    past = trap_wvfms[:, :, peak_tick:total_end - lookback]
    later = trap_wvfms[:, :, peak_tick + lookback:total_end]
    rising = later > past
    above_thresh = later > (rel_height * trap_wvfms[:, :, peak_tick:peak_tick + 1])
    pileup = (rising & above_thresh).any(axis=-1)
    return np.where(pileup, np.int8(2), np.int8(1))


# ---------------------------------------------------------------------------
# Energy calibration
# ---------------------------------------------------------------------------

def calibrate_energy_mev(trap_integrals, detector="lcm"):
    """Convert trap integrals (ADC*tick) to MeV.

    Parameters
    ----------
    trap_integrals : ndarray
        Full waveform integral per trap.
    detector : str
        "lcm" uses LCM_ENERGY_NORM=147. "acl" — not yet calibrated.

    Returns
    -------
    ndarray : energy in MeV, same shape as input.
    """
    if detector == "lcm":
        return trap_integrals / LCM_ENERGY_NORM * ENERGY_SCALE / N_MODULES
    else:
        raise ValueError(
            f"Energy calibration for '{detector}' not yet defined. "
            "Use raw integrals or provide the ACL normalization factor."
        )


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def _part_number(fname):
    """Extract the numeric part index from a filename like '..._p42_...'."""
    m = re.search(r'_p(\d+)[_.]', fname)
    return int(m.group(1)) if m else 0


def discover_files(base_dir, run=None, extension=".hdf5"):
    """Find and sort HDF5 (or other) files by part number.

    Parameters
    ----------
    base_dir : str
        Directory to search.
    run : int or None
        If given, only return files whose name contains this run number
        (e.g. run=979 matches files containing '_979_' or '_rctl_979_').
    extension : str
        File extension to match.

    Returns
    -------
    list of str : sorted file paths.
    """
    all_files = [
        os.path.join(base_dir, f)
        for f in os.listdir(base_dir)
        if f.endswith(extension)
    ]
    if run is not None:
        run_str = str(run)
        all_files = [f for f in all_files if f"_{run_str}_" in os.path.basename(f)]
    return sorted(all_files, key=lambda f: _part_number(os.path.basename(f)))


# ---------------------------------------------------------------------------
# Charge data from flow files (h5flow references)
# ---------------------------------------------------------------------------

def get_charge_hits_for_light_events(h5_path, light_event_indices=None):
    """Read charge hits associated with light events from a reflow HDF5 file.

    Uses h5flow reference chains:
        charge/events -> light/events (to find which charge events match)
        charge/events -> charge/calib_final_hits (to get the hits)

    Parameters
    ----------
    h5_path : str
        Path to a reflow FLOW.hdf5 file.
    light_event_indices : array-like of int or None
        If given, only return hits for these light event indices.
        If None, return hits for all light events.

    Returns
    -------
    dict with keys:
        "hits" : structured ndarray with fields x, y, z, Q, E, t_drift, ...
        "light_event_idx" : int array, the light event index each hit belongs to
        "n_hits_per_event" : int array, number of hits per light event
    """
    with h5py.File(h5_path, "r") as h:
        # Load reference arrays
        charge_to_light_ref = h["/charge/events/ref/light/events/ref"][:]
        charge_to_light_region = h["/charge/events/ref/light/events/ref_region"][:]
        charge_to_hits_ref = h["/charge/events/ref/charge/calib_final_hits/ref"][:]
        charge_to_hits_region = h["/charge/events/ref/charge/calib_final_hits/ref_region"][:]

        n_charge_events = len(charge_to_light_region)
        all_hits = h["/charge/calib_final_hits/data"][:]

        # Build mapping: for each charge event, find which light event(s) it maps to
        # charge_to_light_ref[:, 1] gives the light event index
        charge_to_light_idx = {}  # charge_event_idx -> light_event_idx
        for ce in range(n_charge_events):
            start = charge_to_light_region[ce]["start"]
            stop = charge_to_light_region[ce]["stop"]
            if start < stop:
                light_indices = charge_to_light_ref[start:stop, 1]
                for li in light_indices:
                    charge_to_light_idx[ce] = int(li)

        # Invert: light_event_idx -> list of charge_event_idx
        light_to_charge = {}
        for ce, le in charge_to_light_idx.items():
            light_to_charge.setdefault(le, []).append(ce)

        if light_event_indices is not None:
            target_light = set(int(i) for i in light_event_indices)
        else:
            target_light = set(light_to_charge.keys())

        # Collect hits
        hit_arrays = []
        light_idx_arrays = []
        n_hits_list = []

        for le in sorted(target_light):
            charge_events = light_to_charge.get(le, [])
            event_hits = []
            for ce in charge_events:
                start = charge_to_hits_region[ce]["start"]
                stop = charge_to_hits_region[ce]["stop"]
                if start < stop:
                    hit_indices = charge_to_hits_ref[start:stop, 1]
                    event_hits.append(all_hits[hit_indices])

            if event_hits:
                combined = np.concatenate(event_hits)
                hit_arrays.append(combined)
                light_idx_arrays.append(np.full(len(combined), le, dtype=np.int64))
                n_hits_list.append(len(combined))
            else:
                n_hits_list.append(0)

    if hit_arrays:
        hits = np.concatenate(hit_arrays)
        light_event_idx = np.concatenate(light_idx_arrays)
    else:
        hits = np.array([], dtype=all_hits.dtype)
        light_event_idx = np.array([], dtype=np.int64)

    return {
        "hits": hits,
        "light_event_idx": light_event_idx,
        "n_hits_per_event": np.array(n_hits_list, dtype=int),
    }
