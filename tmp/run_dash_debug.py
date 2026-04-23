# tmp/run_dash_debug.py
import traceback
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

try:
    from src.visualizer.dashboard import run_dashboard
    from src.database import init_db
    init_db()
    run_dashboard()
except Exception:
    with open("tmp/dash_error.log", "w") as f:
        f.write(traceback.format_exc())
    print("Dashboard crashed. Traceback saved to tmp/dash_error.log")
    sys.exit(1)
