#!/usr/bin/env python3
"""
HIV Risk Predictor Plugin for Dify
Main entry point
"""

import os
from pathlib import Path
from dify_plugin import DifyPluginEnv, Plugin

# Load .env file
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

if __name__ == "__main__":
    plugin = Plugin(DifyPluginEnv())
    plugin.run()
