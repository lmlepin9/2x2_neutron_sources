#!/usr/bin/env python3
"""
Compare source-present and no-source cluster-energy CSV files.

For each requested minimum charge-cluster size, the script:
  1. loads all source-present CSVs,
  2. loads all no-source CSVs,
  3. keeps events with n_charge_hits >= the requested cut,
  4. overlays the two distributions,
  5. plots source - no-source in a lower panel.

Plotted quantity:
  - charge_E_calib (cluster energy calibrated from charge_Q)

Every CSV that is read is also written back out with an added
"charge_E_calib" column, containing the cluster energy obtained by
running charge_Q through charge_to_energy(). The calibrated column is
added to the full CSV, before any window selection or cluster-size cut,
so the saved files remain complete and reusable.

Example:
    python compare_light_csvs.py \
        --source events_109us_min0.csv events_128us_min0.csv \
        --background bkg_matched_no_source_min0.csv \
        --min-cluster-size 0 3 6 \
        --source-runtime 1200 \
        --background-runtime 1500

The histogram values are rates (events / second) and the difference panel
is source rate - no-source rate.

Plots are written to ./comparison_plots/
Calibrated CSVs are written next to their inputs as <name>_calib.csv,
unless --calibrated-csv-dir is given.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ------------------------------------------------------------------
# Plot configuration
# ------------------------------------------------------------------
# The reference plotting code uses the same `bins` array for source and
# no-source data. Its definition was outside the supplied code block.
# Use the fixed 0-10 MeV / 50-bin definition used for these cluster-energy
# plots, and derive centers from the exact same bin edges.
BINS = np.arange(0, 10.5, 0.5)
CENTERS = 0.5 * (BINS[:-1] + BINS[1:])

# Column holding the raw collected charge, and the calibrated energy
# column derived from it.
CHARGE_COLUMN = "charge_Q"
CALIB_ENERGY_COLUMN = "charge_E_calib"


def charge_to_energy(charge):
    """
    Convert collected charge (ke-) into deposited energy.

    Calibration copied directly from the notebook.
    """

    return (np.asarray(charge)*1000*23.6/0.57523585/1e6)


def add_calibrated_energy(df):
    """
    Add the calibrated cluster-energy column, derived from charge_Q.

    Operates on the full frame (before any window selection or
    cluster-size cut) so the saved CSV keeps every original row.
    """
    if CHARGE_COLUMN not in df.columns:
        raise KeyError(
            f"CSV is missing required column: {CHARGE_COLUMN}. "
            "This column contains the cluster's total collected charge "
            "and is needed for the energy calibration."
        )

    charge = pd.to_numeric(df[CHARGE_COLUMN], errors="coerce").to_numpy()
    df[CALIB_ENERGY_COLUMN] = charge_to_energy(charge)

    return df


def read_csvs(paths, calibrated_csv_dir=None, save_calibrated=True):
    """
    Read and concatenate CSVs, adding the calibrated energy column.

    Each input CSV gets a "charge_E_calib" column and is written back out
    as <name>_calib.csv, either beside the input or into
    `calibrated_csv_dir` if one is supplied.

    If a Window/window column exists, keep only prompt-trigger clusters.
    If no Window/window column exists, assume all rows are prompt-trigger
    clusters and keep the entire CSV.
    """
    frames = []

    for path in paths:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        print(f"Reading {path}")
        df = pd.read_csv(path)

        # Calibrate charge -> energy for every row in the file, before any
        # selection, then save the augmented CSV.
        df = add_calibrated_energy(df)

        n_bad = int(np.count_nonzero(~np.isfinite(df[CALIB_ENERGY_COLUMN])))
        if n_bad:
            print(
                f"  Warning: {n_bad} row(s) have non-finite "
                f"{CALIB_ENERGY_COLUMN} (missing/unparsable {CHARGE_COLUMN})."
            )

        if save_calibrated:
            out_dir = (
                Path(calibrated_csv_dir)
                if calibrated_csv_dir is not None
                else path.parent
            )
            out_dir.mkdir(parents=True, exist_ok=True)
            calibrated_path = out_dir / f"{path.stem}_calib{path.suffix}"
            df.to_csv(calibrated_path, index=False)
            print(f"  Wrote calibrated CSV: {calibrated_path}")

        # Accept either "Window" or "window" (or any capitalization).
        window_column = next(
            (column for column in df.columns if column.lower() == "window"),
            None,
        )

        if window_column is not None:
            # Only use clusters from the prompt trigger window.
            df = df.copy()
            df[window_column] = (
                df[window_column].astype(str).str.strip().str.lower()
            )
            df = df[df[window_column] == "prompt"].copy()
            print(f"  Prompt-window clusters selected: {len(df)}")
        else:
            # Older CSVs may not contain window information. In that case,
            # treat every row as belonging to the prompt trigger window.
            print(
                "  No Window column found; assuming all rows are "
                "prompt-trigger clusters."
            )

        frames.append(df)

    if not frames:
        raise ValueError("No CSV files were supplied.")

    return pd.concat(frames, ignore_index=True)


def apply_cluster_cut(df, min_cluster_size, require_valid_sumhits=True):
    """Apply the minimum cluster-size cut and optionally n_valid_sumhits > 0."""
    if "n_charge_hits" not in df.columns:
        raise KeyError("CSV is missing required column: n_charge_hits.")

    mask = df["n_charge_hits"] >= min_cluster_size

    if require_valid_sumhits:
        if "n_valid_sumhits" not in df.columns:
            raise KeyError("CSV is missing required column: n_valid_sumhits.")
        n_valid_sumhits = pd.to_numeric(df["n_valid_sumhits"], errors="coerce")
        mask &= n_valid_sumhits > 0

    return df[mask].copy()


def get_cluster_energy(df):
    """Return finite calibrated cluster energies from charge_E_calib."""
    if CALIB_ENERGY_COLUMN not in df.columns:
        raise KeyError(
            f"Frame is missing '{CALIB_ENERGY_COLUMN}'. It should have been "
            "added by add_calibrated_energy() when the CSV was read."
        )

    energy = pd.to_numeric(df[CALIB_ENERGY_COLUMN], errors="coerce").to_numpy()
    return energy[np.isfinite(energy)]


def plot_comparison(
    source_df,
    nosource_df,
    min_cluster_size,
    output_dir,
    source_runtime,
    background_runtime,
):
    """Make the source/no-source + difference plot in the supplied format."""
    if source_runtime <= 0 or background_runtime <= 0:
        raise ValueError("Source and no-source runtimes must be positive.")

    source_energy = get_cluster_energy(source_df)
    nosource_energy = get_cluster_energy(nosource_df)

    bins = BINS
    centers = CENTERS

    source_counts, _ = np.histogram(source_energy, bins=bins)
    nosource_counts, _ = np.histogram(nosource_energy, bins=bins)

    source_rate = source_counts / source_runtime
    nosource_rate = nosource_counts / background_runtime

    source_error = np.sqrt(source_counts) / source_runtime
    nosource_error = np.sqrt(nosource_counts) / background_runtime

    difference = source_rate - nosource_rate
    difference_error = np.sqrt(source_error**2 + nosource_error**2)

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------

    f, (a0, a1) = plt.subplots(
        2,
        1,
        gridspec_kw={'height_ratios': [8, 5]},
        sharex=True,
        figsize=(11, 7),
    )

    f.tight_layout()

    # Top panel: source data + no-source data
    a0.errorbar(
        centers,
        source_rate,
        yerr=source_error,
        linestyle='none',
        color='black',
        marker='.',
        label=f'Source Data (Stat Errors Only) - All Prompt Sandbox ({source_runtime / 3600:.2f} hrs)',
    )

    # Note: the original code passed linestyle='none' here. Newer matplotlib
    # rejects that value, and it has no visible effect on a bar histogram
    # (no edge color is set), so it has been dropped.
    a0.hist(
        nosource_energy,
        weights=np.ones(len(nosource_energy)) / background_runtime,
        color='red',
        histtype='bar',
        bins=bins,
        label='No Source Data',
        alpha=0.6,
    )

    a0.errorbar(
        centers,
        nosource_rate,
        yerr=nosource_error,
        linestyle='none',
        color='red',
        marker='none',
    )

    # Bottom panel: source - no source
    a1.errorbar(
        centers,
        difference,
        yerr=difference_error,
        linestyle='none',
        color='black',
        marker='.',
        label='Source - No Source Difference',
    )

    a0.set_title(
        f'Minimum Cluster Size: {min_cluster_size}',
        fontsize=18,
    )
    a0.set_ylabel('Cluster Count/s', fontsize=20)
    a1.set_xlabel('Calibrated Energy of Clusters (MeV)', fontsize=20)
    a1.set_ylabel('Subtracted Count/s', fontsize=20)

    a0.grid(True)
    a1.grid(True)

    a0.legend(fontsize=10)
    a1.legend(fontsize=10)

    plt.tight_layout()

    output_file = output_dir / f'cluster_energy_calib_comparison_mincluster{min_cluster_size}_valid_sumhits.png'
    plt.savefig(
        output_file,
        dpi=300,
        # bbox_inches='tight'
    )
    plt.close(f)

    print(f"Saved {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compare source-present and no-source calibrated cluster-energy "
            "distributions for several minimum cluster-size cuts."
        )
    )

    parser.add_argument(
        "--source",
        nargs="+",
        required=True,
        help="Source-present CSV files.",
    )
    parser.add_argument(
        "--background",
        nargs="+",
        required=True,
        help="No-source CSV files.",
    )
    parser.add_argument(
        "--min-cluster-size",
        nargs="+",
        type=int,
        default=[0, 3, 6],
        help="Minimum n_charge_hits cuts. Example: 0 3 6.",
    )
    parser.add_argument(
        "--source-runtime",
        type=float,
        required=True,
        help="Total source runtime in seconds.",
    )
    parser.add_argument(
        "--background-runtime",
        type=float,
        required=True,
        help="Total no-source runtime in seconds.",
    )
    parser.add_argument(
        "--no-valid-sumhits-cut",
        action="store_true",
        help="Do not apply the n_valid_sumhits > 0 cut.",
    )
    parser.add_argument(
        "--output-dir",
        default="comparison_plots",
        help="Directory for output plots.",
    )
    parser.add_argument(
        "--calibrated-csv-dir",
        default=None,
        help=(
            "Directory for the CSVs with the added charge_E_calib column. "
            "Default: alongside each input file."
        ),
    )
    parser.add_argument(
        "--no-save-calibrated-csv",
        action="store_true",
        help="Compute charge_E_calib but do not write the updated CSVs.",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    save_calibrated = not args.no_save_calibrated_csv

    source_df = read_csvs(
        args.source,
        calibrated_csv_dir=args.calibrated_csv_dir,
        save_calibrated=save_calibrated,
    )
    background_df = read_csvs(
        args.background,
        calibrated_csv_dir=args.calibrated_csv_dir,
        save_calibrated=save_calibrated,
    )

    print(f"\nTotal source-present rows: {len(source_df)}")
    print(f"Total no-source rows:      {len(background_df)}")

    for min_cluster_size in args.min_cluster_size:
        source_cut = apply_cluster_cut(
            source_df, min_cluster_size,
            require_valid_sumhits=not args.no_valid_sumhits_cut,
        )
        background_cut = apply_cluster_cut(
            background_df, min_cluster_size,
            require_valid_sumhits=not args.no_valid_sumhits_cut,
        )

        print(
            f"\nMinimum cluster size >= {min_cluster_size}:"
            f"\n  Source present: {len(source_cut)}"
            f"\n  No source:      {len(background_cut)}"
        )

        plot_comparison(
            source_cut,
            background_cut,
            min_cluster_size,
            output_dir,
            source_runtime=args.source_runtime,
            background_runtime=args.background_runtime,
        )


if __name__ == "__main__":
    main()