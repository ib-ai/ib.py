#!/bin/bash
# Run formatters to enforce code style

set -euo pipefail

message() {
    echo -e "\033[47;34m$1\033[0m"
}

success() {
    echo -e "\033[47;32m$1\033[0m"
}

warning() {
    echo -e "\033[47;31m$1\033[0m"
}

# Ensure uv is available
if ! command -v uv &> /dev/null; then
    warning "uv command not found. Please install uv (e.g., via pip install uv)."
    exit 1
fi

DIRECTORY=${1:-.}

# Run isort
message "Running isort..."
if uv pip show isort > /dev/null 2>&1; then
    uv run isort $DIRECTORY
else
    warning "isort is not installed in the virtual environment. Using uvx to run isort."
    uvx isort $DIRECTORY
fi
success "isort formatting completed."

# Run black
message "Running black..."
if uv pip show black > /dev/null 2>&1; then
    uv run black $DIRECTORY
else
    warning "black is not installed in the virtual environment. Using uvx to run black."
    uvx black $DIRECTORY
fi
success "black formatting completed."

# Run ruff to check code style
message "Running ruff..."
if uv pip show ruff > /dev/null 2>&1; then
    uv run ruff check $DIRECTORY --fix --unsafe-fixes
else
    warning "ruff is not installed in the virtual environment. Using uvx to run ruff."
    uvx ruff check $DIRECTORY --fix --unsafe-fixes
fi
success "ruff code style check completed."

# # Run mypy for type checking
# message "Running mypy..."
# if uv pip show mypy > /dev/null 2>&1; then
#     uv run mypy $DIRECTORY
# else
#     warning "mypy is not installed in the virtual environment. Using uvx to run mypy."
#     uvx mypy $DIRECTORY
# fi
# success "mypy type checking completed."

echo -e "\033[47;42mCode style enforcement completed successfully!\033[0m"