"""Run the whole project: py run_all.py"""
import runpy, sys
from pathlib import Path
here = Path(__file__).resolve().parent
try:
    runpy.run_path(str(here / "churn_analysis.py"), run_name="__main__")
    runpy.run_path(str(here / "build_dashboard.py"), run_name="__main__")
except ModuleNotFoundError as e:
    print("\nMissing package:", e.name, "-> run:  py -m pip install pandas numpy scikit-learn")
input("\nDone. Press Enter to close.")
