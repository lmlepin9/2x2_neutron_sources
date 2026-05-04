#!/bin/bash

_setup_env_fail() {
    return 1 2>/dev/null || exit 1
}

_setup_env_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export REPO_DIR="${_setup_env_script_dir}"

ENV_NAME="neutron_env_py"
ENV_DIR="${HOME}/${ENV_NAME}"
REQ_FILE="${REPO_DIR}/requirements/neutron_env_py_requirements.txt"

echo "Repository root: ${REPO_DIR}"

if [ ! -d "${ENV_DIR}" ]; then
    echo "Creating virtual environment: ${ENV_DIR}"
    python3 -m venv "${ENV_DIR}" || _setup_env_fail

    # shellcheck disable=SC1090
    source "${ENV_DIR}/bin/activate" || _setup_env_fail

    python -m pip install --upgrade pip setuptools wheel || _setup_env_fail

    if [ -f "${REQ_FILE}" ]; then
        echo "Installing dependencies from ${REQ_FILE}"
        python -m pip install -r "${REQ_FILE}" || _setup_env_fail
    else
        echo "WARNING: requirements file not found: ${REQ_FILE}"
    fi
else
    if [ -n "${VIRTUAL_ENV:-}" ] && [ "${VIRTUAL_ENV}" != "${ENV_DIR}" ] && command -v deactivate >/dev/null 2>&1; then
        deactivate
    fi

    # shellcheck disable=SC1090
    source "${ENV_DIR}/bin/activate" || _setup_env_fail
fi

export NEUTRON_ENV_NAME="${ENV_NAME}"
echo "Activated virtual environment: ${VIRTUAL_ENV}"
