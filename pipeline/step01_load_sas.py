"""Step 01 - Load SAS microdata into one tidy crop-record table (FR-01).  OWNER: Chadia

Input : data/raw/sas_<year>/*.dta   (NISR microdata, never committed)
Output: data/interim/crop_records.parquet   (contract: contracts.CONTRACTS["crop_records"])

What to do:
 1. Download SAS 2025 (catalog 124) and 2024 (catalog 113) into data/raw/sas_2025, sas_2024.
 2. Open the crop-level file in each year and fill VARIABLE_MAP below (also docs/variable_map.md).
 3. Fill CROP_CODES and DISTRICT_CODES from the value labels in the .dta files.
 4. Run:  python run_pipeline.py --only 1   and read the data-quality log it prints.
Rule: if a loss variable is missing in a year, set it to None here. Do not guess.
"""
import pandas as pd

from isarura_core.config import RAW, STAGES
from isarura_core.contracts import check

from .common import Paths, log

# TODO(Chadia): confirm every name against the actual files. SAS 2024 names from the
# data dictionary are pre-filled; the file name and id/weight names are guesses.
VARIABLE_MAP = {
    "2024": {
        "file": "sas_2024/TODO_crop_level_file.dta",
        "farm_id": "TODO", "cluster_id": "TODO", "stratum": "TODO", "weight": "TODO",
        "district": "TODO", "season": "TODO", "crop": "TODO",
        "harvest_kg": "s2q22",          # check: s2q21 vs s2q22 - which is the crop-level total?
        "loss_total_kg": "s2q39",
        "loss_transport_kg": "s2q46", "loss_storage_kg": "s2q47", "loss_processing_kg": "s2q48",
        "loss_packaging_kg": "s2q49", "loss_sales_kg": "s2q50",
        "storage_type": "s2q37",
    },
    "2025": None,  # TODO(Chadia): copy the 2024 block once you confirm the names in 2025
}

# TODO(Chadia): map raw value labels to our names (see config.CROPS / config.DISTRICT_LIST)
CROP_CODES: dict = {}       # e.g. {"Maize": "maize", "Beans": "beans", "Irish potato": "irish_potato"}
DISTRICT_CODES: dict = {}   # e.g. {"NYAGATARE": "Nyagatare"} if labels are upper case


def load_year(year: str, vm: dict) -> pd.DataFrame:
    path = RAW / vm["file"]
    df = pd.read_stata(path, convert_categoricals=True)
    cols = {v: k for k, v in vm.items() if k != "file" and v}
    out = df[list(cols)].rename(columns=cols)
    for k in [f"loss_{s}_kg" for s in STAGES] + ["loss_total_kg", "storage_type"]:
        if k not in out:
            out[k] = pd.NA
    out["crop"] = out["crop"].astype(str).map(CROP_CODES)
    out["district"] = out["district"].astype(str).map(lambda x: DISTRICT_CODES.get(x, x.title()))
    out["season"] = year + out["season"].astype(str).str.strip().str[-1].str.upper()  # -> "2024A"
    for c in ["farm_id", "cluster_id", "stratum", "storage_type"]:
        out[c] = out[c].astype(str)
    for c in ["weight", "harvest_kg", "loss_total_kg"] + [f"loss_{s}_kg" for s in STAGES]:
        out[c] = pd.to_numeric(out[c], errors="coerce").astype(float)
    return out


def run(p: Paths):
    if p.synthetic:
        log("01", "synthetic mode: crop_records already written by pipeline/synthetic.py")
        return
    frames = []
    for year, vm in VARIABLE_MAP.items():
        if not vm:
            log("01", f"{year}: no variable map yet, skipped")
            continue
        df = load_year(year, vm)
        n0 = len(df)
        dq = {
            "unmapped crop": df["crop"].isna(),
            "missing weight": df["weight"].isna() | (df["weight"] <= 0),
            "missing/zero harvest": df["harvest_kg"].isna() | (df["harvest_kg"] <= 0),
            "loss > harvest": df["loss_total_kg"].astype(float) > df["harvest_kg"],
        }
        for reason, mask in dq.items():
            log("01", f"{year}: {int(mask.sum()):>6} rows flagged: {reason}")
        drop = dq["unmapped crop"] | dq["missing weight"] | dq["missing/zero harvest"]
        df = df[~drop]
        log("01", f"{year}: rows in {n0:,} -> kept {len(df):,} (dropped {int(drop.sum()):,}; reasons above)")
        frames.append(df)
    if not frames:
        raise SystemExit("No SAS year loaded. Fill VARIABLE_MAP or run with --synthetic.")
    rec = check(pd.concat(frames, ignore_index=True), "crop_records")
    rec.to_parquet(p.crop_records, index=False)
    log("01", f"wrote {len(rec):,} crop records")
