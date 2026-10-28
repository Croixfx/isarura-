"""Step 02 - Reproduce NISR published production (FR-02, Method A).  OWNER: Croix

Input : crop_records + data/inputs/published_national.csv
        (type this table from the SAS 2025 annual report: crop, season, production_t, source)
Output: data/interim/validation.parquet  -> becomes the headline of the Methods page.
If many rows fall outside tolerance, STOP and fix weights / crop codes / season codes first.
"""
import pandas as pd

from isarura_core.contracts import check
from isarura_core.estimators import validate_totals

from .common import Paths, log


def run(p: Paths):
    rec = pd.read_parquet(p.crop_records)
    
    # ADDED dtype={'production_t': float} to prevent TypeError on typos in the CSV
    pub = check(pd.read_csv(p.inputs / "published_national.csv", dtype={'production_t': float}), "published_national")
    
    v = check(validate_totals(rec, pub), "validation")
    v.to_parquet(p.out("validation"), index=False)
    ok = v["within_tolerance"].mean()
    log("02", f"{ok:.0%} of crop x season totals within tolerance "
              f"(median |diff| {v['difference_pct'].abs().median():.1f}%)")
    if ok < 0.5:
        log("02", "WARNING: most totals do not reconcile. Fix data handling before trusting anything else.")