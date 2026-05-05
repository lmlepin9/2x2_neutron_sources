# AmBe Charge Cluster Job Submission

This directory contains the scripts used to submit AmBe charge-clustering jobs on NERSC Perlmutter.

## Files

- `submit_ambe_list.sh`
  Helper script that submits one Slurm job for one AmBe input file list.
- `submit_ambe_file_list.slurm`
  Slurm job script that processes every HDF5 file listed in one text file.
- `run_AmBe_cluster_analysis.sh`
  Direct/manual runner for interactive testing or one-off jobs.
- `charge/process_CL_AmBe_data.py`
  Python entry point that reads an input file list and writes per-file plus combined cluster CSVs.

## Important working-directory assumption

The batch submission scripts assume you submit from inside `AmBe/`.

Why:

- `submit_ambe_list.sh` calls `submit_ambe_file_list.slurm` with a relative path.
- `submit_ambe_file_list.slurm` does:
  - `cd ../`
  - `source setup_env.sh`
  - `cd ./AmBe`

Expected workflow:

```bash
cd "${REPO_DIR}/AmBe"
```

## Environment setup

The Slurm job uses:

```bash
cd "${REPO_DIR}"
source setup_env.sh
```

`setup_env.sh` exports `REPO_DIR`, creates `~/neutron_env_py` if needed using the pinned dependencies in `requirements/neutron_env_py_requirements.txt`, and activates that environment. `REPO_DIR` is required by `charge/process_CL_AmBe_data.py` and the AmBe light-analysis utilities it imports.

## Standard submission: one job per file list

From `AmBe/`, run:

```bash
cd "${REPO_DIR}/AmBe"
bash submit_ambe_list.sh AmBe_mod2_pmt_trigger_109us_period.txt
```

Optional arguments:

```bash
bash submit_ambe_list.sh INPUT_LIST.txt [DEBUG]
```

Examples:

```bash
cd "${REPO_DIR}/AmBe"
bash submit_ambe_list.sh AmBe_mod2_pmt_trigger_32us_period.txt 0
bash submit_ambe_list.sh AmBe_mod2_pmt_trigger_prompt.txt 1
bash submit_ambe_list.sh "${REPO_DIR}/AmBe/my_ambe_list.txt" 0
```

Argument meanings:

- `DEBUG`
  - `0`: normal processing
  - `1`: debug mode

What happens:

- The helper script builds a Slurm job name from the input list stem plus a timestamp.
- It submits one `sbatch` job for the entire input list.
- The Slurm job reads every non-empty, non-comment line in that list and processes each HDF5 file in sequence.

## Filename-based configuration

`submit_ambe_file_list.slurm` infers processing mode from the input list filename.

Default values:

- `SINGLE_TRIGGER=1`
- `USE_TRIGGER=0`
- `PERIOD=320`

Inference rules:

- If the list name contains `period`, the job switches to multi-trigger mode:
  - `SINGLE_TRIGGER=0`
- If the list name contains `pmt_trigger` or `trigger`, the job enables PMT-trigger selection:
  - `USE_TRIGGER=1`
- If the list name contains a token like `32us`, `109us`, or `320us`, that value is used for:
  - `PERIOD=<number>`

Examples:

- `AmBe_mod2_pmt_trigger_109us_period.txt`
  - `SINGLE_TRIGGER=0`
  - `USE_TRIGGER=1`
  - `PERIOD=109`
- `AmBe_mod2_pmt_trigger_prompt.txt`
  - `SINGLE_TRIGGER=1`
  - `USE_TRIGGER=1`
  - `PERIOD=320` default remains
- A custom list with none of those keywords
  - `SINGLE_TRIGGER=1`
  - `USE_TRIGGER=0`
  - `PERIOD=320`

This naming convention is the main way the batch job decides whether to run prompt-only, prompt/delayed pairing, or all-event processing.

## Processing behavior

`charge/process_CL_AmBe_data.py` expects:

- `--input`: a text file containing one HDF5 path per line
- `--out`: a combined output CSV path ending in `.csv`

The script ignores blank lines and lines starting with `#`.

Depending on the inferred mode:

- Single-trigger with trigger selection:
  - clusters only the selected prompt events
- Multi-trigger with trigger selection:
  - treats event `N` as prompt and event `N+1` as delayed
  - writes prompt, delayed, and combined cluster outputs
- No trigger selection:
  - clusters all events in the listed files

In debug mode, the Python script samples about 10% of events or prompt-delayed pairs, using a fixed random seed.

## Output and log locations

The Slurm script writes stdout/stderr logs to:

```text
/pscratch/sd/l/${USER}/cluster_logs/
```

The per-job output directory is:

```text
/pscratch/sd/l/${USER}/cluster_outputs/${LIST_STEM}_${TIMESTAMP}/
```

Inside that directory, the main combined output is:

```text
${LIST_STEM}_clusters.csv
```

The Python script also writes additional CSVs when data are present:

- Per-input-file combined CSVs:
  - `${LIST_STEM}_clusters_<input_file_stem>.csv`
- Per-input-file prompt CSVs:
  - `${LIST_STEM}_clusters_<input_file_stem>_prompt.csv`
- Per-input-file delayed CSVs:
  - `${LIST_STEM}_clusters_<input_file_stem>_delayed.csv`
- Combined prompt CSV:
  - `${LIST_STEM}_clusters_prompt.csv`
- Combined delayed CSV:
  - `${LIST_STEM}_clusters_delayed.csv`

If a file or category produces no clusters, that specific CSV is not written.

## Direct/manual execution

For interactive testing without `sbatch`, you can use:

```bash
cd "${REPO_DIR}/AmBe"
bash run_AmBe_cluster_analysis.sh
```

Notes:

- This script has hard-coded settings such as:
  - `JOB_NAME`
  - `INPUT_DSET`
  - `SINGLE_TRIGGER`
  - `USE_TRIGGER`
  - `PERIOD`
  - `DEBUG`
- It is best treated as a convenience script for one-off runs rather than the main production submission path.
- The Python entry point still expects `--input` to be a text file list, so make sure the configured `INPUT_DSET` matches that expectation before using it.

## Input file lists

This directory already includes several AmBe file lists, for example:

- `AmBe_mod2_pmt_trigger_prompt.txt`
- `AmBe_mod2_pmt_trigger_prompt_no_source.txt`
- `AmBe_mod2_pmt_trigger_32us_period.txt`
- `AmBe_mod2_pmt_trigger_80us_period.txt`
- `AmBe_mod2_pmt_trigger_109us_period.txt`
- `AmBe_mod2_pmt_trigger_320us_period.txt`

Each list should contain one input HDF5 path per line.

## Common issues

### `setup_env.sh` not found

Make sure you submit from inside `AmBe/`, not from the repository root or another directory.

### `REPO_DIR` problems

`process_CL_AmBe_data.py` expects `REPO_DIR` to be set by `setup_env.sh`.

### First-time environment creation takes a while

On the first run, `setup_env.sh` creates `~/neutron_env_py` and installs the packages listed in `requirements/neutron_env_py_requirements.txt`. Later runs just activate the existing environment.

### Missing input file list

Both submission scripts check that the provided list exists and exit with an error if it does not.

### No output CSV written

The Python script only writes CSVs for categories that produced clusters. A job can finish successfully and still skip writing one or more files if no clusters were found.

## Recommended workflow

1. `cd "${REPO_DIR}/AmBe"`
2. Choose the correct input file list
3. Verify the list filename matches the intended trigger/period mode
4. Submit with `submit_ambe_list.sh`
5. Monitor logs in `/pscratch/sd/l/${USER}/cluster_logs/`
6. Collect CSV outputs from `/pscratch/sd/l/${USER}/cluster_outputs/`
