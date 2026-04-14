#!/usr/bin/env python3
import os
import sys
from pathlib import Path

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from web import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
