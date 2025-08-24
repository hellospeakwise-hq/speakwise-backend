#!/bin/bash

# Get the project root directory (two levels up from this script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Run flake8 with the config file in the project root
cd "$PROJECT_ROOT"
flake8 --config "$PROJECT_ROOT/flake8-config" speakwise
