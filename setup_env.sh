#!/bin/bash

_setup_env_fail() {
    return 1 2>/dev/null || exit 1
}

_setup_env_choose_python() {
    if command -v python3.11 >/dev/null 2>&1; then
        command -v python3.11
        return 0
    fi

    if command -v python3 >/dev/null 2>&1; then
        command -v python3
        return 0
    fi

    echo "ERROR: Could not find python3.11 or python3 on PATH" >&2
    _setup_env_fail
}

_setup_env_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export REPO_DIR="${_setup_env_script_dir}"

ENV_NAME="neutron_env_py"
ENV_DIR="${REPO_DIR}/${ENV_NAME}"
REQ_FILE="${REPO_DIR}/requirements/neutron_env_py_requirements.txt"
PYTHON_BIN="$(_setup_env_choose_python)"

echo "Repository root: ${REPO_DIR}"
echo "Using Python interpreter: ${PYTHON_BIN}"

if [ ! -d "${ENV_DIR}" ]; then
    echo "Creating virtual environment: ${ENV_DIR}"
    "${PYTHON_BIN}" -m venv "${ENV_DIR}" || _setup_env_fail

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
    if [ -x "${ENV_DIR}/bin/python" ]; then
        ENV_PY_MAJOR_MINOR="$("${ENV_DIR}/bin/python" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')" || _setup_env_fail
        if [ "${ENV_PY_MAJOR_MINOR}" != "3.11" ]; then
            echo "ERROR: Existing environment uses Python ${ENV_PY_MAJOR_MINOR}, but this repo now expects Python 3.11." >&2
            echo "Remove ${ENV_DIR} and re-run 'source setup_env.sh' to recreate it with ${PYTHON_BIN}." >&2
            _setup_env_fail
        fi
    fi

    if [ -n "${VIRTUAL_ENV:-}" ] && [ "${VIRTUAL_ENV}" != "${ENV_DIR}" ] && command -v deactivate >/dev/null 2>&1; then
        deactivate
    fi

    # shellcheck disable=SC1090
    source "${ENV_DIR}/bin/activate" || _setup_env_fail
fi

export NEUTRON_ENV_NAME="${ENV_NAME}"
echo "Activated virtual environment: ${VIRTUAL_ENV}"
