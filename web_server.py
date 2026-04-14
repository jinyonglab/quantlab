import os
import sys
from pathlib import Path

os.chdir('/mnt/d/open_agent/InvestLab')
sys.path.insert(0, '/mnt/d/open_agent/InvestLab')

from web import app

if __name__ == "__main__":
    print("Starting InvestLab Web Server on port 8081...")
    app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)
