#!/usr/bin/env python
"""Run ctp-python tests with auto-discovered reachable fronts."""
import subprocess
import sys
import os

# Change to project directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run pytest with verbose output
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests', '-v', '--tb=short'],
    timeout=120,
)

sys.exit(result.returncode)
