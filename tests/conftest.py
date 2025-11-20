"""
Pytest configuration file for EmailReader tests.

This file adds the project root to sys.path to allow imports from src/.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
