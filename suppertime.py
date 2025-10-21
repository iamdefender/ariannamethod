#!/usr/bin/env python3
"""
SUPPERTIME GOSPEL THEATRE - LAUNCHER
Simple launcher for Termux version
"""

import os
import sys
from pathlib import Path

# Determine repo root
REPO_ROOT = Path(__file__).resolve().parent

# Path to Termux script
TERMUX_SCRIPT = REPO_ROOT / "SUPPERTIME" / "suppertime_termux.py"

def main():
    if not TERMUX_SCRIPT.exists():
        print(f"Error: Script not found at {TERMUX_SCRIPT}", file=sys.stderr)
        sys.exit(1)
    
    # Change to SUPPERTIME directory for relative imports
    os.chdir(TERMUX_SCRIPT.parent)
    
    # Execute the Termux version
    print(f"Launching SUPPERTIME from {TERMUX_SCRIPT.parent}...")
    os.execv(sys.executable, [sys.executable, str(TERMUX_SCRIPT)])

if __name__ == "__main__":
    main()

