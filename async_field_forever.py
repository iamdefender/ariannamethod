#!/usr/bin/env python3
"""
ASYNC FIELD FOREVER - Quick Launcher
Launches Field Visualiser from anywhere in the repo.
"""

import sys
import os
from pathlib import Path

# Get the field directory
SCRIPT_DIR = Path(__file__).parent
FIELD_DIR = SCRIPT_DIR / "async_field_forever" / "field"
VISUALISER = FIELD_DIR / "field_visualiser_hybrid.py"

# Add to path
sys.path.insert(0, str(FIELD_DIR))

def main():
    print("🧬⚡ Launching Async Field Forever...\n")
    
    if not VISUALISER.exists():
        print(f"❌ Visualiser not found at: {VISUALISER}")
        print("Make sure you're in the arianna_clean root directory!")
        sys.exit(1)
    
    # Change to field directory
    os.chdir(FIELD_DIR)
    
    # Execute visualiser
    with open(VISUALISER) as f:
        code = compile(f.read(), VISUALISER, 'exec')
        exec(code, {'__name__': '__main__', '__file__': str(VISUALISER)})

if __name__ == "__main__":
    main()

