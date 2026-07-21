# 2x2_neutron_sources

## Setup repository environment

Before running any tool or notebook, source the repository setup from the top level:

```bash
cd /path/to/2x2_neutron_sources
source setup_env.sh
```

This script:

- exports `REPO_DIR`
- creates `~/neutron_env_py` if it does not already exist
- prefers `python3.11` when available to avoid old-package resolution failures from Python 3.6
- installs the pinned dependencies from `requirements/neutron_env_py_requirements.txt` on first creation
- activates `~/neutron_env_py` on every run

This setup is needed by the processing data scripts.

## To Analyze AmBe data check the respective repository.

## To Analyze DTG data check the respective repository.
