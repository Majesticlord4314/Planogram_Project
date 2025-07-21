#!/usr/bin/env python3
"""
Simple startup script for the planogram web UI
Uses the simplified backend that directly runs main.py
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def start_backend():
    """Start the Flask backend"""
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    print("Starting simplified Planogram Web UI backend...")
    print("   - Directly executes your main.py and cohort_planogram.py")
    print("   - No complex integration layer")
    print("   - Same frontend features")
    
    try:
        # Start the backend
        subprocess.run([sys.executable, "simple_app.py"], check=True)
    except KeyboardInterrupt:
        print("\nBackend stopped")
    except Exception as e:
        print(f"Error starting backend: {e}")

if __name__ == "__main__":
    start_backend()
