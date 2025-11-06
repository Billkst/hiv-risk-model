#!/usr/bin/env python3
"""
File Reorganization Tool - Main Entry Point

This script provides a command-line interface for reorganizing project files.
"""

import sys
import os

# Add the parent directory to the Python path to allow package imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from reorg_tool.cli import main

if __name__ == '__main__':
    sys.exit(main())
