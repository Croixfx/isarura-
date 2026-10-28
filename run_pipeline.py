"""One command reruns everything (NFR: Reproducibility).

    python run_pipeline.py --synthetic      # fake data, works on any machine (for building the app)
    python run_pipeline.py                  # real NISR data in data/raw + data/inputs
    python run_pipeline.py --only 3 4 5     # rerun some steps
"""
import argparse

from pipeline import (step01_load_sas, step02_validate, step03_loss_rates, step04_prices_cpi,
                      step05_value_meals, step06_priority, step08_export, synthetic)
from pipeline.common import Paths

STEPS = {1: step01_load_sas, 2: step02_validate, 3: step03_loss_rates, 4: step04_prices_cpi,
         5: step05_value_meals, 6: step06_priority, 8: step08_export}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true", help="use fake data (marked DEMO in the app)")
    ap.add_argument("--only", type=int, nargs="*", help="step numbers to run")
    ap.add_argument("--boot", type=int, default=200, help="bootstrap replicates (0 = no intervals)")
    a = ap.parse_args()
    p = Paths(synthetic=a.synthetic)
    if a.synthetic:
        synthetic.write_all()
    for n, mod in STEPS.items():
        if a.only and n not in a.only:
            continue
        mod.run(p, n_boot=a.boot) if n == 3 else mod.run(p)
