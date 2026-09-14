#!/usr/bin/env python3

import argparse
import os
import traceback
from pathlib import Path

import h5py as h5
import pandas as pd

"""
Combine cluster result CSVs into the same CSV

Usage
-----
Without runtime calculation

python combine_delay_trigger_csvs.py ./csvs combined.csv \
    --file delay_0.csv 0 \
    --file delay_100.csv 100 \
    --file delay_200.csv 200

With runtime calculation

python combine_delay_trigger_csvs.py ./csvs combined.csv \
    --file delay_0.csv 0 \
    --file delay_100.csv 100 \
    --file delay_200.csv 200 \
    --h5-dir /path/to/h5/delay_0 \
    --h5-dir /path/to/h5/delay_100 \
    --h5-dir /path/to/h5/delay_200 \
    --calculate-runtime
"""

def get_runtime(input_dataset, debug=False):
    """
    Calculate total detector livetime from a directory of HDF5 files.

    Parameters
    ----------
    input_dataset : str or Path
        Directory containing HDF5 files.
    debug : bool
        If True, only reads roughly 10% of files.

    Returns
    -------
    float
        Runtime in seconds.
    """
    runtime = 0.0
    input_dataset = Path(input_dataset)

    files = sorted(
        filename for filename in os.listdir(input_dataset)
        if (input_dataset / filename).is_file()
    )

    if debug:
        files = files[:max(1, int(0.1 * len(files)))]

    print(f"Reading runtime from {len(files)} files in {input_dataset}...")

    for filename in files:
        fullpath = input_dataset / filename
        try:
            with h5.File(fullpath, "r") as f:
                if "charge/events" not in f:
                    print(f"No charge/events in {fullpath}")
                    continue

                events = f["charge/events"]
                if len(events) < 2:
                    continue

                timestamps = events["data"]["unix_ts"]
                runtime += max(timestamps) - min(timestamps)

        except Exception:
            print(f"Failed reading {fullpath}")
            traceback.print_exc()

    print(f"Runtime = {runtime:.2f} s")
    return runtime


def calculate_combined_runtime(h5_dirs, debug=False):
    """Calculate and sum runtime across multiple HDF5 directories."""
    total_runtime = 0.0

    print("\nCalculating runtime for HDF5 datasets...")
    for h5_dir in h5_dirs:
        total_runtime += get_runtime(h5_dir, debug=debug)

    print(f"\nCombined runtime = {total_runtime:.2f} s")
    print(f"Combined runtime = {total_runtime / 3600.0:.2f} hours")
    return total_runtime


def combine_csv_files(
    input_dir,
    output_file,
    settings,
    calculate_runtime=False,
    h5_dirs=None,
    debug=False,
):
    """Combine CSV files and optionally calculate corresponding HDF5 runtime."""
    input_dir = Path(input_dir)
    dfs = []

    for filename, setting in settings.items():
        csv_path = input_dir / filename

        if not csv_path.exists():
            print(f"WARNING: file not found, skipping: {csv_path}")
            continue

        df = pd.read_csv(csv_path)
        df["delay_trigger_setting"] = setting
        dfs.append(df)

        print(
            f"Read {len(df)} rows from {filename} "
            f"(delay trigger setting = {setting})"
        )

    if not dfs:
        raise RuntimeError("No CSV files were found/read.")

    combined = pd.concat(dfs, ignore_index=True)
    combined.to_csv(output_file, index=False)
    print(f"\nWrote {len(combined)} total rows to {output_file}")

    total_runtime = None
    if calculate_runtime:
        if h5_dirs is None:
            raise ValueError(
                "Runtime calculation requested, but no HDF5 directories were supplied."
            )
        if len(h5_dirs) != len(settings):
            raise ValueError(
                "The number of HDF5 directories must match the number of CSV files."
            )

        total_runtime = calculate_combined_runtime(h5_dirs, debug=debug)

    return total_runtime


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Combine CSV files, add their delay trigger setting, "
            "and optionally calculate combined HDF5 runtime."
        )
    )

    parser.add_argument("input_dir", help="Directory containing the CSV files")
    parser.add_argument("output_file", help="Path for the combined CSV")

    parser.add_argument(
        "--file",
        action="append",
        nargs=2,
        metavar=("FILENAME", "SETTING"),
        required=True,
        help=(
            "CSV filename and its delay trigger setting. "
            "Can be specified multiple times."
        ),
    )

    parser.add_argument(
        "--h5-dir",
        action="append",
        required=False,
        help=(
            "HDF5 directory corresponding to each --file argument. "
            "Specify in the same order as --file."
        ),
    )

    parser.add_argument(
        "--calculate-runtime",
        action="store_true",
        help="Calculate and print the combined HDF5 runtime.",
    )

    parser.add_argument(
        "--debug-runtime",
        action="store_true",
        help="For runtime calculation, only read roughly 10%% of files.",
    )

    args = parser.parse_args()

    settings = {filename: setting for filename, setting in args.file}

    if args.calculate_runtime and not args.h5_dir:
        parser.error("--calculate-runtime requires at least one --h5-dir argument.")

    if args.calculate_runtime and len(args.h5_dir) != len(args.file):
        parser.error("You must provide exactly one --h5-dir for each --file.")

    combine_csv_files(
        input_dir=args.input_dir,
        output_file=args.output_file,
        settings=settings,
        calculate_runtime=args.calculate_runtime,
        h5_dirs=args.h5_dir,
        debug=args.debug_runtime,
    )


if __name__ == "__main__":
    main()