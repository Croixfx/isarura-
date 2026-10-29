"""Step 01 - Load SAS microdata into one tidy crop-record table (FR-01).  OWNER: Chadia

Input : data/raw/sas_<year>/Season <A|B|C>/Rwa_raw_Season<S><year>_Production.dta   (NISR microdata, never committed)
Output: data/interim/crop_records.parquet   (contract: contracts.CONTRACTS["crop_records"])

One output row = one plot x crop. Findings from the raw files that shape this loader (checked against
NISR published production, see docs/variable_map.md):
  * Farm identity is Segment_ID + s1q6 (s1q6 alone is only a number inside the segment). The sampling
    cluster is the segment (Segment_ID).
  * s2q21 is the harvest of THIS PLOT; s2q22 and ALL loss questions (s2q39, s2q46-s2q50, s2q37) are
    reported once per FARM x CROP and repeated on every plot row. Summing them over plot rows overcounts.
    harvest_kg = s2q21 (with plot_weight reproduces NISR production); farm-crop losses are shared
    across the farm's plots of that crop in proportion to plot harvest, so they add up exactly once.
  * SAS 2025 A and B have no total-loss question (s2q39): the total is the sum of the five stage losses
    (in 2024 s2q39 equals that sum).
"""
import pandas as pd

from isarura_core.config import RAW, STAGES
from isarura_core.contracts import check

from .common import Paths, log

YEARS = ("2024", "2025")
SEASON_LETTERS = ("A", "B", "C")

# Same questionnaire codes in every file; only the weight column's capitalisation differs (2025 C).
VARIABLE_MAP = {
    "segment": "Segment_ID",
    "farm_no": "s1q6",          # farmer ID, unique only inside its segment
    "stratum": "s1q3",
    "district": "s1q2",
    "plot": "s2q1",
    "crop": "s2q4",
    "harvest_kg": "s2q21",      # plot-level harvest (kg). NOT s2q22: that is the farm-crop total repeated per plot
    "loss_total_kg": "s2q39",   # absent in 2025 A and B
    "loss_transport_kg": "s2q46",
    "loss_storage_kg": "s2q47",
    "loss_processing_kg": "s2q48",
    "loss_packaging_kg": "s2q49",
    "loss_sales_kg": "s2q50",
    "storage_type": "s2q37",
}
WEIGHT_COLUMNS = ("plot_weight", "Plot_weight")

CROP_CODES = {
    "Maize": "maize",
    "Bush bean": "beans",
    "Climbing bean": "beans",
    "Cassava": "cassava",
    "Cooking banana": "cooking_banana",   # not "Banana for beer" (a different NISR category)
    "Irish potato": "irish_potato",
    "Sweet potato": "sweet_potato",
    "Paddy rice": "rice",                 # the SAS label; reports paddy
    "Rice": "rice",
    "Sorghum": "sorghum",
    "Wheat": "wheat",
}

DISTRICT_CODES = {
    "Nyarugenege": "Nyarugenge"
}

LOSS_COLS = [f"loss_{s}_kg" for s in STAGES] + ["loss_total_kg"]


def season_files():
    for year in YEARS:
        for letter in SEASON_LETTERS:
            yield year + letter, RAW / f"sas_{year}" / f"Season {letter}" / f"Rwa_raw_Season{letter}{year}_Production.dta"


def _labelled(series: pd.Series, labels: dict | None) -> pd.Series:
    """Value labels applied by hand (pandas refuses files with duplicate labels in columns we do not use)."""
    if not labels:
        return series
    lab = {float(k): v for k, v in labels.items()}
    return series.map(lambda v: lab.get(float(v), str(v)) if pd.notna(v) else v)


def load_season(season: str, path) -> pd.DataFrame:
    import pyreadstat
    _, meta0 = pyreadstat.read_dta(str(path), metadataonly=True)
    vm = dict(VARIABLE_MAP)
    vm["weight"] = next(c for c in WEIGHT_COLUMNS if c in meta0.column_names)
    cols = {v: k for k, v in vm.items() if v in meta0.column_names}
    df, meta = pyreadstat.read_dta(str(path), usecols=list(cols), apply_value_formats=False)
    out = df.rename(columns=cols)
    for name in ("crop", "district", "stratum", "storage_type"):
        if name in cols.values():
            src = next(k for k, v in cols.items() if v == name)
            out[name] = _labelled(out[name], meta.variable_value_labels.get(src))
    for k in ["loss_total_kg", "storage_type"] + [f"loss_{s}_kg" for s in STAGES]:
        if k not in out:
            out[k] = pd.NA

    for c in ["weight", "harvest_kg", "plot"] + LOSS_COLS:
        out[c] = pd.to_numeric(out[c], errors="coerce").astype(float)
    out["raw_crop"] = out["crop"].astype(str)
    out["crop"] = out["raw_crop"].map(CROP_CODES)
    out["district"] = out["district"].astype(str).map(lambda x: DISTRICT_CODES.get(x, x.title()))
    out["season"] = season
    out["farm_id"] = out["segment"].astype(str) + "|" + out["farm_no"].astype(str)
    out["cluster_id"] = out["segment"].astype(str)
    for c in ["stratum", "storage_type"]:
        out[c] = out[c].astype(str)
    return out.drop(columns=["segment", "farm_no", "plot"])


def negatives_to_missing(df: pd.DataFrame) -> pd.DataFrame:
    """A quantity lost cannot be negative: set negative loss values to missing and log how many
    per season and stage (SAS 2024A has 126 negative loss_storage_kg values, down to -340 kg)."""
    df = df.copy()
    for season, g in df.groupby("season"):
        for c in LOSS_COLS:
            neg = g[c] < 0
            if neg.any():
                log("01", f"{season}: {int(neg.sum()):>6} negative {c} values ({neg.mean():.2%} of records) "
                          f"set to missing (min {g[c].min():,.0f} kg)")
    for c in LOSS_COLS:
        df[c] = df[c].mask(df[c] < 0)
    return df


def complete_total_loss(df: pd.DataFrame) -> pd.DataFrame:
    """Where the file has no total-loss question, the total is the sum of the five stage losses."""
    stages = df[[f"loss_{s}_kg" for s in STAGES]].sum(axis=1, min_count=1)
    return df.assign(loss_total_kg=df["loss_total_kg"].fillna(stages))


def share_farm_crop_losses(df: pd.DataFrame) -> pd.DataFrame:
    """Losses are reported once per farm x crop and repeated on each plot row. Share each farm-crop
    value across its plots in proportion to plot harvest, so summing plot rows counts it exactly once."""
    key = df["farm_id"] + "|" + df["raw_crop"]
    g = df.groupby(key)
    harvest = df["harvest_kg"].fillna(0)
    total_h = harvest.groupby(key).transform("sum")
    share = (harvest / total_h).where(total_h > 0, 1.0 / g["harvest_kg"].transform("size"))
    out = df.copy()
    for c in LOSS_COLS:
        out[c] = g[c].transform("max") * share      # identical on every plot row of the farm-crop
    return out


def implausible_losses_to_missing(df: pd.DataFrame) -> pd.DataFrame:
    """A farm cannot lose more of a crop than it harvested. Where the total loss exceeds the harvest the
    loss report is unreliable (a handful of such rows carried about 70% of the weighted Irish potato loss in
    2025A): set all loss values on those rows to missing, but keep the row, so production totals are unchanged."""
    bad = df["loss_total_kg"] > df["harvest_kg"]
    for season, n in bad.groupby(df["season"]).sum().items():
        if n:
            log("01", f"{season}: {int(n):>6} rows with loss > harvest: losses set to missing (harvest kept)")
    out = df.copy()
    out.loc[bad, LOSS_COLS] = float("nan")
    return out


def run(p: Paths):
    if p.synthetic:
        log("01", "synthetic mode: crop_records already written by pipeline/synthetic.py")
        return
    frames = []
    for season, path in season_files():
        if not path.exists():
            log("01", f"{season}: file not found, skipped ({path.name})")
            continue
        df = complete_total_loss(negatives_to_missing(load_season(season, path)))
        n0 = len(df)
        df = implausible_losses_to_missing(share_farm_crop_losses(df))
        dq = {
            "unmapped crop": df["crop"].isna(),
            "missing weight": df["weight"].isna() | (df["weight"] <= 0),
            "missing/zero harvest": df["harvest_kg"].isna() | (df["harvest_kg"] <= 0),
        }
        for reason, mask in dq.items():
            log("01", f"{season}: {int(mask.sum()):>6} rows flagged: {reason}")
        drop = dq["unmapped crop"] | dq["missing weight"] | dq["missing/zero harvest"]
        df = df[~drop].drop(columns="raw_crop")
        log("01", f"{season}: rows in {n0:,} -> kept {len(df):,} (dropped {int(drop.sum()):,}; reasons above)")
        frames.append(df)
    if not frames:
        raise SystemExit("No SAS season loaded. Put the raw files in data/raw/sas_<year>/Season <A|B|C>/ or run with --synthetic.")
    rec = check(pd.concat(frames, ignore_index=True), "crop_records")
    rec.to_parquet(p.crop_records, index=False)
    log("01", f"wrote {len(rec):,} crop records ({rec['season'].nunique()} seasons, {rec['farm_id'].nunique():,} farms, "
              f"{rec['cluster_id'].nunique():,} clusters)")
