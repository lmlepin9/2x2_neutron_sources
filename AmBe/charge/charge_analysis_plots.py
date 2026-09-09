#!/usr/bin/env python3

import h5py as h5 

import matplotlib.pyplot as plt
from matplotlib import cm, colors
import matplotlib.patches as mpatches
from matplotlib.colors import BoundaryNorm
from matplotlib import colors, ticker

import argparse
import numpy as np
import os, sys
import traceback
import glob
import pandas as pd

#import h5flow
plt.style.use('../../utils/dune.mplstyle')
from sklearn.cluster import DBSCAN

# Path to repo root (two directories above notebook)
light_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(light_root)

#from light.PMT_analysis_utils import * 

# Path to repo root (two directories above notebook)
repo_root = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))
sys.path.append(repo_root)

#from utils.backtracking import get_charge_event_hits, hit_backtracker, get_ancestry # Now this works
#from utils.my_ev_display import event_display


'''
Charge analysis plot production script
'''

# ------------ Utility Functions ------------

def parse_arguments():

    parser = argparse.ArgumentParser(
        description="AmBe Charge Analysis"
    )

    parser.add_argument(
        "--source",
        required=True,
        help="CSV containing source data"
    )

    parser.add_argument(
        "--background",
        required=True,
        help="CSV containing no-source data"
    )

    parser.add_argument(
        "--source-directory",
        default=None,
        help="Directory containing source HDF5 files "
             "(used to calculate runtime)"
    )

    parser.add_argument(
        "--background-directory",
        default=None,
        help="Directory containing background HDF5 files"
             "(used to calculate runtime)"
    )

    parser.add_argument(
        "--cluster_quality_cut",
        nargs=3,
        default=(0,0.0,None),
        help="Cuts for selecting clusters of different quality: (min_hits, min_energy [MeV], max_energy [MeV])"
    )

    parser.add_argument(
        "--output",
        default="plots",
        help="Output directory"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Only process 10%% of files"
    )

    return parser.parse_args()


def load_dataframe(filename):

    '''
    Read clustered hit csv files and load them into dataframes

    Create a unique trigger identifier
    '''

    print(f"Loading {filename}")
    df = pd.read_csv(filename)
    df["trigger_id"] = (df["file_id"].astype(str) + "::" + df["light_id"].astype(str))
    print(f"Loaded {len(df):,} hits")
    return df

def load_all_data(args):
    source = load_dataframe(args.source)
    background = load_dataframe(args.background)
    return source, background

# TODO: change this function once timestamps are incorporated into analysis objects

def get_runtime(input_dataset, debug=False):

    """
    Calculate total detector livetime.

    Requires information from unprocessed files

    Parameters
    ----------
    input_dataset : str
        Directory containing HDF5 files.

    debug : bool
        If True only reads roughly 10% of files.
    """

    runtime = 0.0
    files = sorted(os.listdir(input_dataset))

    if debug:
        files = files[:max(1, int(0.1 * len(files)))]
    print(f"Reading runtime from {len(files)} files...")

    for i, filename in enumerate(files):
        fullpath = os.path.join(input_dataset, filename)
        try:
            with h5.File(fullpath, "r") as f:
                # Skip malformed files
                if "charge/events" not in f:
                    continue
                events = f["charge/events"]
                if len(events) < 2:
                    continue
                timestamps = events["data"]["unix_ts"]
                runtime += (
                    max(timestamps)
                    - min(timestamps)
                )

        except Exception:
            print(f"Failed reading {filename}")
            traceback.print_exc()
    #runtime /= 1e6
    print(f"Runtime = {runtime:.2f} s")

    return runtime

# ------------ Energy Calibration ------------

def charge_to_energy(charge):

    """
    Convert collected charge into deposited energy.

    Calibration copied directly from the notebook.
    """

    return (np.asarray(charge)*1000*23.6/0.57523585/1e6)


def calibrate_dataframe(df):

    """
    Add calibrated quantities to dataframe.
    """

    df = df.copy()

    df["E"] = charge_to_energy(df["Q"])

    return df

# ------------ Trigger Bookkeeping ------------

def get_unique_triggers(df):

    """
    Return all trigger IDs.
    """

    return np.unique(df["trigger_id"])


def count_unique_triggers(df):
    return len(get_unique_triggers(df))


def print_dataset_summary(df, name):
    print()
    print("=" * 60)
    print(name)
    print("=" * 60)
    print(f"Hits:      {len(df):,}")
    print(f"Triggers:  {count_unique_triggers(df):,}")

    if "cluster_label" in df.columns:
        labels = df["cluster_label"]
        print(
            f"Clusters:  {(labels >= 0).sum():,} hit assignments"
        )
    print()

def print_cluster_statistics(
    cluster_df,
):
    """
    Print a concise summary of the cluster sample.
    """

    print()
    print("=" * 70)
    print("Cluster Statistics")
    print("=" * 70)
    print(
        f"Clusters          : {len(cluster_df):,}"
    )

    print(
        f"Mean Energy       : "
        f"{cluster_df.total_energy.mean():.3f} MeV"
    )

    print(
        f"Median Energy     : "
        f"{cluster_df.total_energy.median():.3f} MeV"
    )

    print(
        f"Largest Cluster   : "
        f"{cluster_df.total_energy.max():.3f} MeV"
    )

    print(
        f"Mean Hits         : "
        f"{cluster_df.nhits.mean():.1f}"
    )

    print(
        f"Median Hits       : "
        f"{cluster_df.nhits.median():.1f}"
    )

    print()

# ------------ Simple Selections ------------

def remove_noise_hits(df):

    """
    Remove hits with cluster_label == -1.
    """

    return df[df.cluster_label >= 0].copy()


def select_trigger(df, trigger_id):
    return df[df.trigger_id == trigger_id].copy()


def select_cluster(df, cluster_label):
    return df[df.cluster_label == cluster_label].copy()

# ------------ Cluster-level Summary ------------

def build_cluster_summary(df):
    """
    Collapse the hit table into one row per cluster.

    Returns
    -------
    DataFrame

    Columns
    -------
    trigger_id
    file_id
    light_id
    cluster_label
    nhits
    total_charge
    total_energy
    mean_x
    mean_y
    mean_z
    min_x
    max_x
    min_y
    max_y
    min_z
    max_z
    rms_x
    rms_y
    rms_z
    """

    clustered = df[df.cluster_label >= 0].copy()

    if len(clustered) == 0:
        return pd.DataFrame()

    summary = (
        clustered
        .groupby(
            [
                "trigger_id",
                "file_id",
                "light_id",
                "cluster_label"
            ]
        )
        .agg(
            nhits=("Q", "size"),

            total_charge=("Q", "sum"),

            total_energy=("E", "sum"),

            mean_x=("x", "mean"),
            mean_y=("y", "mean"),
            mean_z=("z", "mean"),

            min_x=("x", "min"),
            max_x=("x", "max"),

            min_y=("y", "min"),
            max_y=("y", "max"),

            min_z=("z", "min"),
            max_z=("z", "max"),

            rms_x=("x", "std"),
            rms_y=("y", "std"),
            rms_z=("z", "std")
        )
        .reset_index()
    )

    summary.fillna(0.0, inplace=True)

    summary["extent_x"] = summary.max_x - summary.min_x
    summary["extent_y"] = summary.max_y - summary.min_y
    summary["extent_z"] = summary.max_z - summary.min_z

    return summary

# ------------ Event-level Summary ------------

def build_event_summary(cluster_df):
    """
    Build one row per trigger.
    Useful for all trigger-level plots.
    """

    if len(cluster_df) == 0:
        return pd.DataFrame()

    event_summary = (
        cluster_df
        .groupby("trigger_id")
        .agg(
            nclusters=("cluster_label", "count"),
            event_charge=("total_charge", "sum"),
            event_energy=("total_energy", "sum"),
            largest_cluster=("total_energy", "max"),
            total_hits=("nhits", "sum")

        )

        .reset_index()

    )

    return event_summary

# ------------ Fiducial Volume Cuts ------------

def apply_fiducial_cut(
    cluster_df,
    xmin=-62,
    xmax=62,
    ymin=-20,
    ymax=104,
    zmin=3,
    zmax=61
):
    """
    Keep only clusters whose centroid lies
    inside the fiducial volume.
    """

    keep = (
        (cluster_df.mean_x >= xmin) &
        (cluster_df.mean_x <= xmax) &

        (cluster_df.mean_y >= ymin) &
        (cluster_df.mean_y <= ymax) &

        (cluster_df.mean_z >= zmin) &
        (cluster_df.mean_z <= zmax)
    )

    return cluster_df.loc[keep].copy()

# ------------ Cluster-quality Cuts ------------

def apply_cluster_quality_cut(
    cluster_df,
    min_hits=0,
    min_energy=0.0,
    max_energy=None
):
    """
    Generic quality cuts.
    """

    keep = cluster_df.nhits >= min_hits
    keep &= cluster_df.total_energy >= min_energy

    if max_energy is not None:
        keep &= cluster_df.total_energy <= max_energy

    return cluster_df.loc[keep].copy()

# ------------ Event Selection ------------

def select_single_cluster_events(cluster_df):
    """
    Keep events containing exactly one cluster.
    """

    counts = (
        cluster_df
        .groupby("trigger_id")
        .size()
    )

    single_ids = counts[counts == 1].index

    return cluster_df[
        cluster_df.trigger_id.isin(single_ids)
    ].copy()

def select_multiple_cluster_events(cluster_df):
    """
    Keep events containing multiple clusters.
    """

    counts = (
        cluster_df
        .groupby("trigger_id")
        .size()
    )

    ids = counts[counts > 1].index

    return cluster_df[
        cluster_df.trigger_id.isin(ids)
    ].copy()

# ------------ Background Subtraction ------------

def normalize_by_runtime(hist, runtime):
    """
    Convert histogram counts into rates.
    """

    hist = np.asarray(hist, dtype=float)

    return hist / runtime


def subtract_background(
    source_hist,
    source_runtime,
    background_hist,
    background_runtime
):
    """
    Runtime-normalized subtraction.
    """

    source_rate = normalize_by_runtime(
        source_hist,
        source_runtime
    )

    background_rate = normalize_by_runtime(
        background_hist,
        background_runtime
    )

    subtracted = source_rate - background_rate
    error = np.sqrt(
        source_hist / source_runtime**2 +
        background_hist / background_runtime**2
    )

    return subtracted, error


###############################################################################
# Plotting
###############################################################################


# ------------ Plotting Helpers ------------

def make_histogram(
    values,
    bins,
    density=False
):
    """
    Wrapper around numpy.histogram.
    """

    hist, edges = np.histogram(
        values,
        bins=bins,
        density=density
    )

    centers = 0.5 * (edges[:-1] + edges[1:])

    return hist, centers, edges


def histogram_cluster_energy(
    cluster_df,
    bins=np.linspace(0,10,101)
):

    return make_histogram(
        cluster_df.total_energy,
        bins=bins
    )


def histogram_cluster_charge(
    cluster_df,
    bins=np.linspace(0,4e5,100)
):

    return make_histogram(
        cluster_df.total_charge,
        bins=bins
    )


def histogram_cluster_size(
    cluster_df,
    bins=np.arange(0,100)
):

    return make_histogram(
        cluster_df.nhits,
        bins=bins
    )

# ------------ Plot Formatting ------------

def setup_figure(figsize=(8, 6)):
    """
    Create a standard figure.

    All notebook plots should call this first.
    """

    fig, ax = plt.subplots(figsize=figsize)

    ax.tick_params(
        axis="both",
        direction="in",
        top=True,
        right=True,
        length=6,
    )

    ax.minorticks_on()

    return fig, ax


def finalize_plot(
    ax,
    xlabel,
    ylabel,
    title=None,
    legend=True,
    grid=False,
    logx=False,
    logy=False,
    output_file=None,
):
    """
    Apply consistent formatting to every figure.
    """

    ax.set_xlabel(xlabel, fontsize=14)
    ax.set_ylabel(ylabel, fontsize=14)

    if title is not None:
        ax.set_title(title)
    if legend:
        ax.legend(frameon=False)
    if grid:
        ax.grid(alpha=0.3)
    if logx:
        ax.set_xscale("log")
    if logy:
        ax.set_yscale("log")

    plt.tight_layout()

    if output_file is not None:
        plt.savefig(output_file, dpi=300)

    return ax

def source_nosource_comparison(
    source_clusters,
    nosource_clusters,
    source_runtime,
    nosource_runtime,
    bins=np.arange(0, 10.5, 0.5),
    output_file=None,
):
    """
    Plot source and no-source cluster-energy spectra and
    their difference.

    Parameters
    ----------
    source_clusters : pandas.DataFrame
        Cluster-level source data.

    nosource_clusters : pandas.DataFrame
        Cluster-level no-source data.

    source_runtime : float
        Source runtime in seconds.

    nosource_runtime : float
        No-source runtime in seconds.

    bins : array-like
        Energy histogram bin edges in MeV.

    output_file : str, optional
        Output filename for the figure.

    Returns
    -------
    results : dict
        Histogram information and source-minus-no-source spectrum.
    """

    # ------------------------------------------------------------------
    # Histograms
    # ------------------------------------------------------------------

    h_source, centers, _ = histogram_cluster_energy(
        source_clusters,
        bins=bins,
    )

    h_nosource, _, _ = histogram_cluster_energy(
        nosource_clusters,
        bins=bins,
    )

    # ------------------------------------------------------------------
    # Runtime normalization
    # ------------------------------------------------------------------

    source_rate = normalize_by_runtime(
        h_source,
        source_runtime,
    )

    nosource_rate = normalize_by_runtime(
        h_nosource,
        nosource_runtime,
    )

    # ------------------------------------------------------------------
    # Source - no source
    # ------------------------------------------------------------------

    difference = source_rate - nosource_rate

    # Poisson uncertainties after runtime normalization
    source_error = (
        np.sqrt(h_source)
        / source_runtime
    )

    nosource_error = (
        np.sqrt(h_nosource)
        / nosource_runtime
    )

    difference_error = np.sqrt(
        source_error**2
        + nosource_error**2
    )

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(10, 8),
        sharex=True,
    )

    ax_source = axes[0]
    ax_difference = axes[1]

    # Source
    ax_source.errorbar(
        centers,
        source_rate,
        yerr=source_error,
        fmt=".",
        markersize=7,
        label="Source",
    )

    # No source
    ax_source.step(
        centers,
        nosource_rate,
        where="mid",
        linewidth=2,
        label="No Source",
    )

    finalize_plot(
        ax_source,
        xlabel="",
        ylabel="Rate [Hz]",
        legend=True,
    )

    # Difference
    ax_difference.errorbar(
        centers,
        difference,
        yerr=difference_error,
        fmt=".",
        markersize=7,
        label="Source - No Source",
    )

    ax_difference.axhline(
        0,
        linestyle="--",
        linewidth=1,
    )

    finalize_plot(
        ax_difference,
        xlabel="Energy of Clusters [MeV]",
        ylabel="Rate Difference [Hz]",
        legend=True,
    )

    plt.tight_layout()

    if output_file is not None:
        plt.savefig(
            output_file,
            dpi=300,
            bbox_inches="tight",
        )

    return {
        "centers": centers,
        "source_counts": h_source,
        "nosource_counts": h_nosource,
        "source_rate": source_rate,
        "nosource_rate": nosource_rate,
        "source_error": source_error,
        "nosource_error": nosource_error,
        "difference": difference,
        "difference_error": difference_error,
    }

class AnalysisDataset:
    '''
    Container for one clustered dataset.
    '''

    def __init__(self, hits, runtime, name):
        self.name = name
        self.hits = hits
        self.clusters = build_cluster_summary(hits)
        self.events = build_event_summary(self.clusters)
        self.runtime = runtime

def main():

    args = parse_arguments()

    os.makedirs(
        args.output,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Load data
    # ---------------------------------------------------------------

    source_hits = load_dataframe(
        args.source
    )

    nosource_hits = load_dataframe(
        args.background
    )

    # ---------------------------------------------------------------
    # Get runtimes
    # ---------------------------------------------------------------

    #source_runtime = get_runtime(
    #    args.source_directory,
    #    debug=args.debug,
    #)

    #nosource_runtime = get_runtime(
    #    args.background_directory,
    #    debug=args.debug,
    #)

    source_runtime = get_runtime(
        args.source_directory,
        debug=True
    )

    nosource_runtime = get_runtime(
        args.background_directory,
        debug=False
    )

    # ---------------------------------------------------------------
    # Create datasets
    # ---------------------------------------------------------------

    source = AnalysisDataset(
        source_hits,
        source_runtime,
        "Source",
    )

    nosource = AnalysisDataset(
        nosource_hits,
        nosource_runtime,
        "No Source",
    )

    # ---------------------------------------------------------------
    # Calibrate
    # ---------------------------------------------------------------

    source.hits = calibrate_dataframe(
        source.hits
    )

    nosource.hits = calibrate_dataframe(
        nosource.hits
    )

    # ---------------------------------------------------------------
    # Build clusters
    # ---------------------------------------------------------------

    source_clusters = build_cluster_summary(
        source.hits
    )

    nosource_clusters = build_cluster_summary(
        nosource.hits
    )

    print()
    print(
        f"Source clusters before quality cut: "
        f"{len(source_clusters):,}"
    )

    print(
        f"No-source clusters before quality cut: "
        f"{len(nosource_clusters):,}"
    )

    # ---------------------------------------------------------------
    # Apply cluster quality cuts
    # ---------------------------------------------------------------

    source_clusters = apply_cluster_quality_cut(
        source_clusters,
        min_hits=int(args.cluster_quality_cut[0]),
        min_energy=float(args.cluster_quality_cut[1]),
        max_energy=None if args.cluster_quality_cut[2].lower() == "none" else float(args.cluster_quality_cut[2])
    )

    nosource_clusters = apply_cluster_quality_cut(
        nosource_clusters,
        min_hits=int(args.cluster_quality_cut[0]),
        min_energy=float(args.cluster_quality_cut[1]),
        max_energy=None if args.cluster_quality_cut[2].lower() == "none" else float(args.cluster_quality_cut[2])
    )

    print()
    print(
        f"Source clusters after quality cut: "
        f"{len(source_clusters):,}"
    )

    print(
        f"No-source clusters after quality cut: "
        f"{len(nosource_clusters):,}"
    )

    # ---------------------------------------------------------------
    # Source vs no-source comparison
    # ---------------------------------------------------------------

    comparison_file = os.path.join(
        args.output,
        "source_vs_no_source.png",
    )

    comparison = source_nosource_comparison(
        source_clusters,
        nosource_clusters,
        source.runtime,
        nosource.runtime,
        bins=np.arange(
            0,
            10.5,
            0.5,
        ),
        output_file=comparison_file,
    )

    # ---------------------------------------------------------------
    # Save numerical result
    # ---------------------------------------------------------------

    pd.DataFrame({
        "energy": comparison["centers"],
        "source_rate": comparison["source_rate"],
        "nosource_rate": comparison["nosource_rate"],
        "difference": comparison["difference"],
        "difference_error": comparison["difference_error"],
    }).to_csv(
        os.path.join(
            args.output,
            "source_vs_no_source.csv",
        ),
        index=False,
    )

    plt.close("all")

if __name__ == "__main__":
    main()