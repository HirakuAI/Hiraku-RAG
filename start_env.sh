#!/bin/bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: This script must be sourced. Run:"
    echo "source ${0}"
    exit 1
fi

VENV_PATH="venv/bin/activate"
MIN_PYTHON_VERSION="3.8"

check_python_version() {
    local python_cmd=$1
    local version=$($python_cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    local major_version=$(echo $version | cut -d. -f1)
    local minor_version=$(echo $version | cut -d. -f2)
    local min_major=$(echo $MIN_PYTHON_VERSION | cut -d. -f1)
    local min_minor=$(echo $MIN_PYTHON_VERSION | cut -d. -f2)

    if [ "$major_version" -lt "$min_major" ] || ([ "$major_version" -eq "$min_major" ] && [ "$minor_version" -lt "$min_minor" ]); then
        echo "Error: Python version $version found. Minimum required version is $MIN_PYTHON_VERSION"
        return 1
    fi
    echo "Python version check passed: $version >= $MIN_PYTHON_VERSION"
    return 0
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

setup_environment() {
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        echo "Error: Python 3 is not installed"
        return 1
    fi

    if ! check_python_version $PYTHON_CMD; then
        return 1
    fi

    if [ ! -w "$(pwd)" ]; then
        echo "Error: Cannot write to current directory"
        return 1
    fi

    if [ ! -f "$VENV_PATH" ]; then
        echo "Virtual environment not found at $VENV_PATH"
        echo "Would you like to create a new virtual environment? (y/n)"
        read -r answer
        if [ "$answer" = "y" ]; then
            echo "Creating new virtual environment..."
            $PYTHON_CMD -m venv venv || {
                echo "Error: Failed to create virtual environment"
                return 1
            }
            echo "Virtual environment created successfully"
        else
            echo "Operation cancelled by user"
            return 1
        fi
    fi

    source "$VENV_PATH" || {
        echo "Error: Failed to activate virtual environment"
        return 1
    }

    echo "Virtual environment activated successfully"
    echo "Python path: $(which python)"
    echo "Python version: $(python --version)"
    return 0
}

setup_environment
