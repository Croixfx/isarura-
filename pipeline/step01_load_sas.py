"""Step 01 - Load SAS microdata into one tidy crop-record table (FR-01).  OWNER: Chadia

Input : data/raw/sas_<year>/*.dta   (NISR microdata, never committed)
Output: data/interim/crop_records.parquet   (contract: contracts.CONTRACTS["crop_records"])
"""
import pandas as pd

from isarura_core.config import RAW, STAGES
from isarura_core.contracts import check

from .common import Paths, log

VARIABLE_MAP = {
    "2024": {
        "file": "sas_2024/Rwa_raw_SeasonA2024_Production.dta", 
        "farm_id": "s1q6",      
        "cluster_id": "s1q4",   
        "stratum": "s1q3",      
        "weight": "plot_weight",
        "district": "s1q2",     
        "crop": "s2q4",         
        "harvest_kg": "s2q22",  
        "loss_total_kg": "s2q39",
        "loss_transport_kg": "s2q46", 
        "loss_storage_kg": "s2q47", 
        "loss_processing_kg": "s2q48",
        "loss_packaging_kg": "s2q49", 
        "loss_sales_kg": "s2q50",
        "storage_type": "s2q37",
    },
    "2025": {
        "file": "sas_2025/Rwa_raw_SeasonA2025_Production.dta", 
        "farm_id": "s1q6",      
        "cluster_id": "s1q4",   
        "stratum": "s1q3",      
        "weight": "plot_weight",
        "district": "s1q2",     
        "crop": "s2q4",         
        "harvest_kg": "s2q22",  
        "loss_total_kg": None,     # 2025 doesn't have a single total loss question
        "loss_transport_kg": "s2q46", 
        "loss_storage_kg": "s2q47", 
        "loss_processing_kg": "s2q48",
        "loss_packaging_kg": "s2q49", 
        "loss_sales_kg": "s2q50",
        "storage_type": "s2q37",
    }
}

CROP_CODES = {
    "Maize": "maize",
    "Bush bean": "beans",
    "Climbing bean": "beans",
    "Cassava": "cassava",
    "Banana for beer": "cooking_banana",
    "Irish potato": "irish_potato",
    "Sweet potato": "sweet_potato",
    "Rice": "rice",
    "Sorghum": "sorghum",
    "Wheat": "wheat",
}

DISTRICT_CODES = {
    "Nyarugenege": "Nyarugenge"
}


def load_year(year: str, vm: dict) -> pd.DataFrame:
    path = RAW / vm["file"]
    df = pd.read_stata(path, convert_categoricals=True)
    
    # Only get columns that actually exist in the map
    cols = {v: k for k, v in vm.items() if k != "file" and v}
    out = df[list(cols)].rename(columns=cols)
    
    for k in [f"loss_{s}_kg" for s in STAGES] + ["loss_total_kg", "storage_type"]:
        if k not in out:
            out[k] = pd.NA
            
    out["crop"] = out["crop"].astype(str).map(CROP_CODES)
    out["district"] = out["district"].astype(str).map(lambda x: DISTRICT_CODES.get(x, x.title()))
    
    # Hardcode the season based on the year we are loading
    out["season"] = year + "A"  # -> "2024A"
    
    for c in ["farm_id", "cluster_id", "stratum", "storage_type"]:
        if c in out:
            out[c] = out[c].astype(str)
            
    for c in ["weight", "harvest_kg", "loss_total_kg"] + [f"loss_{s}_kg" for s in STAGES]:
        if c in out:
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
        }
        # Only check loss > harvest if loss_total_kg exists
        if "loss_total_kg" in df and not df["loss_total_kg"].isna().all():
            dq["loss > harvest"] = df["loss_total_kg"].astype(float) > df["harvest_kg"]
            
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