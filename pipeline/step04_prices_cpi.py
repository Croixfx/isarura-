"""Step 04 - Prices from EICV7 unit values, rolled forward with CPI (FR-06, Method E).  OWNER: Croix

Inputs:
  data/raw/eicv7/Cross_Section/CS_S8B_Food_Expenditure_Consumption.dta   (NISR EICV7, catalog 119; never committed)
      -> unit values (value / quantity of purchases reported in kg), cached in data/interim/unit_values.parquet
  data/inputs/cpi.csv  (month 'YYYY-MM', area, food_index, source) typed from the NISR CPI reports
      (Annexes 1-3). Optional upgrade: full monthly series from CPI_time_series_September_2026.xls.
Output: prices.parquet (district rows, plus a 'National' row per crop used for the national headline)
Skipped (value columns stay empty downstream) when the EICV7 file is not on this machine.
"""
import pandas as pd

from isarura_core.config import RAW, RICE_PADDY_FACTOR
from isarura_core.contracts import check
from isarura_core.conversions import cpi_factor, roll_forward, trimmed_price_table

from .common import Paths, log

EICV7_BASE_MONTH = "2024-01"   # NISR EICV7 Methodological Note p.29-30: consumption valued in Jan 2024 national prices.
CPI_AREA = "Rural"             # farm losses -> rural food index

EICV7_FOOD_FILE = RAW / "eicv7" / "Cross_Section" / "CS_S8B_Food_Expenditure_Consumption.dta"
# s8bq0 item codes -> our crops (from the file's value labels)
EICV7_ITEMS = {19: "maize",        # Dry maize (grain)
               1: "beans",         # Dry bean
               45: "sorghum",      # Sorghum
               16: "rice",         # Local rice (MILLED; paddy adjustment applied in run())
               47: "wheat",        # Wheat (grain)
               7: "cassava",       # Cassava (root)
               5: "irish_potato",  # Irish potato
               6: "sweet_potato",  # Sweet potato
               9: "cooking_banana"}  # Banana-cooking (Inyamunyo)
KG_UNIT = 1                    # s8bq3b unit code for kilograms
VISITS = (2, 3, 4, 5)


def load_eicv7_unit_values() -> pd.DataFrame:
    """One row per purchase reported in kg with quantity > 0 and value > 0, visits 2-5 (Jan 2024 prices)."""
    if not EICV7_FOOD_FILE.exists():
        raise NotImplementedError(f"EICV7 food file not found: {EICV7_FOOD_FILE}")
    import pyreadstat
    cols = ["district", "s8bq0"] + [f"s8bq{q}_v{v}" for v in VISITS for q in ("3a", "3b", "4")]
    d, meta = pyreadstat.read_dta(str(EICV7_FOOD_FILE), usecols=cols, apply_value_formats=False)
    d = d[d["s8bq0"].isin(EICV7_ITEMS)]
    district_names = meta.variable_value_labels["district"]
    frames = []
    for v in VISITS:
        x = d[["district", "s8bq0", f"s8bq3a_v{v}", f"s8bq3b_v{v}", f"s8bq4_v{v}"]]
        x.columns = ["district", "item", "qty", "unit", "value"]
        frames.append(x)
    q = pd.concat(frames, ignore_index=True)
    q = q[(q["unit"] == KG_UNIT) & (q["qty"] > 0) & (q["value"] > 0)]
    return pd.DataFrame({
        "crop": q["item"].map(EICV7_ITEMS),
        "district": q["district"].map(district_names).astype(str),
        "unit_value_rwf_per_kg": (q["value"] / q["qty"]).astype(float),
    }).reset_index(drop=True)


def run(p: Paths):
    if p.unit_values.exists():
        uv = pd.read_parquet(p.unit_values)
        log("04", f"unit values from cache {p.unit_values.name} ({len(uv):,} purchases)")
    else:
        try:
            uv = load_eicv7_unit_values()
        except NotImplementedError:
            log("04", "SKIPPED: EICV7 unit values not available; no prices.parquet written. "
                      "Later steps leave value columns empty.")
            return
        uv.to_parquet(p.unit_values, index=False)
        log("04", f"read {len(uv):,} EICV7 purchases in kg, cached to {p.unit_values.name}")
    uv = check(uv, "unit_values")
    cpi = check(pd.read_csv(p.inputs / "cpi.csv", dtype={"month": str}), "cpi")
    latest = cpi["month"].max()
    f = cpi_factor(cpi, EICV7_BASE_MONTH, latest, CPI_AREA)
    table = trimmed_price_table(uv)
    # EICV7 prices MILLED rice; SAS loss is PADDY. ASSUMED paddy-to-milled rate (see config.RICE_PADDY_FACTOR).
    rice = table["crop"] == "rice"
    table.loc[rice, ["price_low", "price_central", "price_high"]] *= RICE_PADDY_FACTOR
    table.loc[rice, "source"] += f", x{RICE_PADDY_FACTOR} paddy-to-milled (assumption)"
    prices = roll_forward(table, f, latest)
    prices = check(prices, "prices")
    prices.to_parquet(p.out("prices"), index=False)
    nat = prices[prices["district"] == "National"].set_index("crop")["price_central"]
    log("04", f"prices for {prices['crop'].nunique()} crops, rolled {EICV7_BASE_MONTH} -> {latest} (x{f:.3f})")
    log("04", "national central price (Rwf/kg, " + latest + "): " + ", ".join(f"{c} {v:,.0f}" for c, v in nat.items()))
