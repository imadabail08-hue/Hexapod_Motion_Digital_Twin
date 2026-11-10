"""
run.py — Root Launcher for HEXAPOD MOTION DIGITAL TWIN (HEX-01)
"""

import sys
import os
from pathlib import Path

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import main

if __name__ == "__main__":
    main()
