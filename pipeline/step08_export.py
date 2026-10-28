"""Step 08 - Export aggregates only, plus a privacy scan (FR-11).  OWNER: Chadia

Writes data/public/*.csv (what the app and judges see) and data/public/meta.json.
Fails if any table could expose farm-level rows.
"""
import json
from datetime import date

import pandas as pd

from isarura_core.config import MIN_N, PUBLIC, ROOT
from isarura_core.contracts import CONTRACTS, PUBLIC_TABLES, check

from .common import Paths, log, read_out

FORBIDDEN_COLS = {"farm_id", "cluster_id", "hh_id", "household_id", "weight", "gps", "latitude", "longitude"}


def privacy_scan():
    """No microdata files anywhere in the repo outside data/raw and data/interim."""
    bad = [str(f.relative_to(ROOT)) for ext in ("*.dta", "*.sav", "*.sas7bdat")
           for f in ROOT.rglob(ext) if "raw" not in f.parts and "interim" not in f.parts]
    if bad:
        raise SystemExit(f"PRIVACY: microdata files outside data/raw: {bad}")


def run(p: Paths):
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for name in PUBLIC_TABLES:
        df = read_out(p, name)
        leak = FORBIDDEN_COLS & set(df.columns)
        if leak:
            raise SystemExit(f"PRIVACY: {name} has farm-level columns {leak}")
        keep = list(CONTRACTS[name]) + [c for c in df.columns if c not in CONTRACTS[name]]
        check(df, name)[keep].to_csv(PUBLIC / f"{name}.csv", index=False, float_format="%.6g")
    sc = read_out(p, "stage_consistency")
    sc.to_csv(PUBLIC / "stage_consistency.csv", index=False, float_format="%.6g")
    prices = pd.read_csv(PUBLIC / "prices.csv")
    meta = {
        "demo": p.synthetic,
        "generated": date.today().isoformat(),
        "price_month": str(prices["month"].iloc[0]),
        "min_n": MIN_N,
        "seasons": sorted(pd.read_csv(PUBLIC / "loss_value.csv")["season"].unique().tolist()),
    }
    (PUBLIC / "meta.json").write_text(json.dumps(meta, indent=2))
    privacy_scan()
    log("08", f"exported {len(PUBLIC_TABLES) + 1} tables to data/public (demo={p.synthetic})")
