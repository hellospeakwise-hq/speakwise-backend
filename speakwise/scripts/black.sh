#!/bin/bash

# Get the project root directory (two levels up from this script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Run black from the project root
cd "$PROJECT_ROOT"
black --line-length 117 --exclude '^.*\b(migrations)\b.*$' speakwise
