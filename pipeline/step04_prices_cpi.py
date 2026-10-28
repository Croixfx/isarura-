"""Step 04 - Prices from EICV7 unit values, rolled forward with CPI (FR-06, Method E).  OWNER: Croix

Inputs:
  data/interim/unit_values.parquet  (from EICV7 food module: crop, district, value/quantity)
      TODO(Croix): write load_eicv7_unit_values() once the EICV7 files are downloaded.
  data/inputs/cpi.csv  (month 'YYYY-MM', area, food_index, source) typed from the NISR CPI reports
      (Annexes 1-3). Optional upgrade: full monthly series from CPI_time_series_September_2026.xls.
Output: prices.parquet
"""
import pandas as pd

from isarura_core.contracts import check
from isarura_core.conversions import cpi_factor, roll_forward, trimmed_price_table

from .common import Paths, log

EICV7_BASE_MONTH = "2024-01"   # NISR EICV7 Methodological Note p.29-30: consumption valued in Jan 2024 national prices.
CPI_AREA = "Rural"             # farm losses -> rural food index


def load_eicv7_unit_values():
    raise NotImplementedError("TODO(Croix): read EICV7 food consumption file -> crop, district, unit_value_rwf_per_kg")


def run(p: Paths):
    uv = pd.read_parquet(p.unit_values) if p.unit_values.exists() else load_eicv7_unit_values()
    uv = check(uv, "unit_values")
    cpi = check(pd.read_csv(p.inputs / "cpi.csv", dtype={"month": str}), "cpi")
    latest = cpi["month"].max()
    f = cpi_factor(cpi, EICV7_BASE_MONTH, latest, CPI_AREA)
    prices = roll_forward(trimmed_price_table(uv), f, latest)
    prices = check(prices, "prices")
    prices.to_parquet(p.out("prices"), index=False)
    log("04", f"prices for {prices['crop'].nunique()} crops, rolled {EICV7_BASE_MONTH} -> {latest} (x{f:.3f})")
