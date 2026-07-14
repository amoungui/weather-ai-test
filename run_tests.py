#!/usr/bin/env python
"""
Script to run pytest with proper path configuration
"""

import sys
import os
import subprocess

# Add current directory to path
sys.path.insert(0, os.getcwd())

if __name__ == "__main__":
    # Run pytest with coverage
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "-v",
        "--cov=app",
        "--cov-report=term"
    ])
    
    sys.exit(result.returncode)