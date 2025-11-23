#!/bin/bash

# EmailReader Startup Script
# Simplified version - assumes Python, venv, and pip are already set up

set -e  # Exit on error

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Start the application
python index.py
