# DTG Job Submission

This directory contains the scripts used to submit DTG cluster-processing jobs on NERSC Perlmutter.

## Files

- `submit_all_dtg_files.sh`
  Submits one Slurm job per input file listed in a text file.
- `submit_dtg_single_file.slurm`
  Slurm job script for processing a single `.FLOW.hdf5` file.
- `run_DTG_cluster_analysis.sh`
  Direct/manual runner for local or interactive testing.
- `charge/process_DTG_data.py`
  Python entry point that reads file lists and writes one CSV per processed chunk.

## Important working-directory assumption

The Slurm script assumes you submit from inside `DTG/`.

Why:
- `submit_all_dtg_files.sh` calls `submit_dtg_single_file.slurm` with a relative path.
- `submit_dtg_single_file.slurm` does:
  - `cd "${SLURM_SUBMIT_DIR}"`
  - `cd ../`
  - `source setup_env.sh`
  - `cd ./DTG`

So the expected workflow is:

```bash
cd /global/homes/l/lmlepin/neutron_source_work/2x2_neutron_sources/DTG
```

## Environment setup

The Slurm script uses:

```bash
source setup_env.sh
```

`setup_env.sh` exports `REPO_DIR`, creates `~/neutron_env_py` if needed using the pinned dependencies in `requirements/neutron_env_py_requirements.txt`, and activates that environment. `REPO_DIR` is required by `charge/process_DTG_data.py`.

## Standard submission: one job per file in a list

From `DTG/`, run:

```bash
bash submit_all_dtg_files.sh DTG_ON_1212_files.txt
```

Optional arguments:

```bash
bash submit_all_dtg_files.sh FILE_LIST.txt [cl:0|1] [debug:0|1]
```

Examples:

```bash
bash submit_all_dtg_files.sh DTG_ON_1212_files.txt 0 0
bash submit_all_dtg_files.sh DTG_ON_CL_1212_files.txt 1 0
bash submit_all_dtg_files.sh DTG_BKG_CL_files.txt 1 1
```

Argument meanings:

- `cl`
  - `0`: process charge-event input
  - `1`: process CL/light-linked input
- `debug`
  - `0`: normal processing
  - `1`: debug mode

What happens:

- The script creates a job name from the file-list stem plus timestamp.
- It submits one `sbatch` job per non-empty line in the file list.
- Each submitted job runs `submit_dtg_single_file.slurm` on exactly one input file.

## Single-file submission

If you want to submit one file manually:

```bash
sbatch --job-name=MY_DTG_JOB submit_dtg_single_file.slurm /full/path/to/file.FLOW.hdf5 [cl:0|1] [debug:0|1]
```

Examples:

```bash
sbatch --job-name=dtg_on_test submit_dtg_single_file.slurm /path/to/my_file.FLOW.hdf5 0 0
sbatch --job-name=dtg_cl_test submit_dtg_single_file.slurm /path/to/my_cl_file.FLOW.hdf5 1 1
```

## Output and log locations

The Slurm script writes logs to:

```text
/pscratch/sd/l/${USER}/cluster_logs/
```

The per-job output directory is:

```text
/pscratch/sd/l/${USER}/cluster_outputs/${JOB_NAME}_${SLURM_JOB_ID}
```

Inside that output directory, the script also creates a one-line temporary input file:

```text
input_${SLURM_JOB_ID}.txt
```

The Python processing writes one CSV per chunk, with names like:

```text
<input_filename>.chunk_0000.csv
<input_filename>.chunk_0001.csv
...
```

## Chunk size

Current default chunk size is hard-coded in the submission scripts as:

```bash
CHUNK_SIZE=2000
```

This is passed to:

```bash
python ./charge/process_DTG_data.py --cs 2000
```

If you want a different chunk size for batch jobs, edit:

- `submit_dtg_single_file.slurm`
- optionally `run_DTG_cluster_analysis.sh`

## Direct/manual execution

For interactive testing without `sbatch`, you can use:

```bash
bash run_DTG_cluster_analysis.sh [cl:0|1] [debug:0|1]
```

Notes:

- This script currently has its own hard-coded settings:
  - `JOB_NAME`
  - `INPUT_DSET`
  - `CHUNK_SIZE`
  - `NOHUP_OPT`
- It is best treated as a convenience test script, not the main production submission path.

## Input file lists

This directory already includes several file lists, for example:

- `DTG_ON_1212_files.txt`
- `DTG_OFF_1212_files.txt`
- `DTG_OFF_1209_files.txt`
- `DTG_ON_CL_1212_files.txt`
- `DTG_BKG_CL_files.txt`

Each file list should contain one full input path per line.

## Debug mode behavior

`charge/process_DTG_data.py` prints:

```text
Running in debug mode, only 5 files will be processed.
```

But for the current DTG batch flow, each Slurm job is already passed a one-line temporary file list containing exactly one input file, so in practice debug mode mainly affects verbosity and per-file processing behavior rather than list length.

## Common issues

### `setup_env.sh` not found

Make sure you submitted from `DTG/`, not from the repository root or another directory.

### `REPO_DIR` problems

`process_DTG_data.py` expects `REPO_DIR` to be set by `setup_env.sh`.

### First-time environment creation takes a while

On the first run, `setup_env.sh` creates `~/neutron_env_py` and installs the packages listed in `requirements/neutron_env_py_requirements.txt`. Later runs just activate the existing environment.

### Relative-path failures

If `submit_all_dtg_files.sh` cannot find `submit_dtg_single_file.slurm`, you are probably not running it from inside `DTG/`.

### Missing input file

Both submission scripts check that the input list or input file exists and will exit with an error if not.

## Recommended workflow

For production runs:

1. `cd` into `DTG/`
2. Choose the correct file list
3. Decide whether the input is CL or non-CL
4. Submit with `submit_all_dtg_files.sh`
5. Monitor logs in `/pscratch/sd/l/${USER}/cluster_logs/`
6. Collect chunk CSVs from `/pscratch/sd/l/${USER}/cluster_outputs/`
