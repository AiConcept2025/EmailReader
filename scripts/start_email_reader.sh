#!/bin/bash

# EmailReader Startup Script
# Simplified version - assumes Python, venv, and pip are already set up

set -e  # Exit on error

# Get the project root directory (parent of scripts directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

# Activate virtual environment
source venv/bin/activate

# Start the application
python index.py
