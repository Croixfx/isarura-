"""Design-based estimators (Method steps A to C). Owner: Croix.

Loss rate for a cell (crop c, district d, season s, stage k):
    L = sum(w * loss_k) / sum(w * harvest)
Intervals: resample clusters with replacement inside the cell, B times, and take the
2.5th and 97.5th percentiles of the ratio. Cells with fewer than MIN_N farmers are flagged.
"""
import numpy as np
import pandas as pd

from .config import MIN_N, N_BOOT, SEED, STAGES, VALIDATION_TOLERANCE_PCT

KEYS = ["crop", "district", "season"]


def weighted_production(records: pd.DataFrame, by=("crop", "season")) -> pd.DataFrame:
    """Weighted production in tonnes. Used for validation against NISR (step A)."""
    r = records.assign(wh=records["weight"] * records["harvest_kg"])
    out = r.groupby(list(by), as_index=False)["wh"].sum()
    out["our_estimate_t"] = out.pop("wh") / 1000.0
    return out


def validate_totals(records: pd.DataFrame, published: pd.DataFrame,
                    tol_pct: float = VALIDATION_TOLERANCE_PCT) -> pd.DataFrame:
    ours = weighted_production(records, by=("crop", "season"))
    # only seasons we have microdata for (published 2026 rows are used later, not validated)
    published = published[published["season"].isin(ours["season"].unique())]
    v = published.rename(columns={"production_t": "nisr_published_t"})[["crop", "season", "nisr_published_t"]]
    v = v.merge(ours, on=["crop", "season"], how="left")
    v["difference_pct"] = 100 * (v["our_estimate_t"] - v["nisr_published_t"]) / v["nisr_published_t"]
    v["within_tolerance"] = v["difference_pct"].abs().le(tol_pct).fillna(False).astype(bool)
    return v


BASE_DISTRICT = "NISR published"
BASE_NATIONAL_SHARE = "NISR national x survey district share"
BASE_SURVEY = "survey estimate"


def scale_to_national(base: pd.DataFrame, national: pd.DataFrame) -> pd.DataFrame:
    """Fill production_t / production_base where NISR published no district figure.

    `base` has crop, district, season, survey_t (survey-weighted tonnes) and production_t
    (NISR district figure, NaN where missing). For a crop x season with NO published district
    figure at all, each district gets its share of the survey total times NISR's published
    NATIONAL production, so the districts add up to the national figure. Only where no national
    figure exists either do we keep the raw survey total.
    """
    b = base.copy()
    b["production_base"] = BASE_DISTRICT
    has_pub = b.groupby(["crop", "season"])["production_t"].transform(lambda s: s.notna().any())
    todo = ~has_pub
    nat = national[["crop", "season", "production_t"]].rename(columns={"production_t": "national_t"})
    nat = nat.drop_duplicates(["crop", "season"])
    b = b.merge(nat, on=["crop", "season"], how="left")
    total = b.groupby(["crop", "season"])["survey_t"].transform("sum")
    scaled = b["survey_t"] / total * b["national_t"]
    use_nat = todo & scaled.notna() & (total > 0)
    b.loc[use_nat, "production_t"] = scaled[use_nat]
    b.loc[use_nat, "production_base"] = BASE_NATIONAL_SHARE
    # cells without a published district figure that could not be scaled: raw survey estimate
    # (includes the odd missing district inside a crop x season that NISR does cover)
    raw = b["production_t"].isna()
    b.loc[raw, "production_t"] = b.loc[raw, "survey_t"]
    b.loc[raw, "production_base"] = BASE_SURVEY
    return b.drop(columns="national_t")


def validate_loss_share(rates: pd.DataFrame, share: pd.DataFrame) -> pd.DataFrame:
    """Compare our national total loss rate (x100) with NISR's published post-harvest loss share (%)."""
    nat = rates[(rates["district"] == "National") & (rates["stage"] == "total")]
    ours = nat[["crop", "season", "loss_rate"]].assign(our_estimate_pct=nat["loss_rate"] * 100)
    v = share.rename(columns={"loss_share_pct": "nisr_published_pct"})[["crop", "season", "nisr_published_pct"]]
    v = v.merge(ours[["crop", "season", "our_estimate_pct"]], on=["crop", "season"], how="inner")
    v["difference_pp"] = v["our_estimate_pct"] - v["nisr_published_pct"]
    return v


def _boot_ratio(num: np.ndarray, den: np.ndarray, rng, n_boot: int):
    """num/den are per-cluster weighted sums. Returns (low, high) of the bootstrap ratio."""
    m = len(num)
    if m < 2 or den.sum() <= 0:
        return np.nan, np.nan
    idx = rng.integers(0, m, size=(n_boot, m))
    n_s, d_s = num[idx].sum(axis=1), den[idx].sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratios = np.where(d_s > 0, n_s / d_s, np.nan)
    return np.nanpercentile(ratios, 2.5), np.nanpercentile(ratios, 97.5)


def loss_rates(records: pd.DataFrame, n_boot: int = N_BOOT, min_n: int = MIN_N,
               seed: int = SEED, extra_keys=()) -> pd.DataFrame:
    """Long table: one row per crop x district x season x stage (+ 'total').

    extra_keys lets you compute national or provincial rates by passing a pre-set
    'district' value (e.g. records.assign(district='National')).
    """
    keys = KEYS + list(extra_keys)
    r = records[records["harvest_kg"] > 0].copy()
    stage_cols = {k: f"loss_{k}_kg" for k in STAGES} | {"total": "loss_total_kg"}
    for k, col in stage_cols.items():
        r[f"wl_{k}"] = r["weight"] * r[col].fillna(0)
    r["wh"] = r["weight"] * r["harvest_kg"]

    # cluster-level sums inside each cell: makes the bootstrap cheap
    agg = {f"wl_{k}": "sum" for k in stage_cols} | {"wh": "sum", "farm_id": "nunique"}
    cl = r.groupby(keys + ["cluster_id"], as_index=False).agg(agg)

    rng = np.random.default_rng(seed)
    rows = []
    for cell, g in cl.groupby(keys, sort=True):
        cell = dict(zip(keys, cell if isinstance(cell, tuple) else (cell,)))
        n = int(g["farm_id"].sum())
        den = g["wh"].to_numpy()
        for k in stage_cols:
            num = g[f"wl_{k}"].to_numpy()
            rate = num.sum() / den.sum() if den.sum() > 0 else np.nan
            lo, hi = _boot_ratio(num, den, rng, n_boot) if n_boot else (np.nan, np.nan)
            rows.append({**cell, "stage": k, "loss_rate": rate, "ci_low": lo, "ci_high": hi,
                         "n_farmers": n, "flag_small_n": n < min_n})
    out = pd.DataFrame(rows)
    out["n_farmers"] = out["n_farmers"].astype("int64")
    out["flag_small_n"] = out["flag_small_n"].astype(bool)
    return out


def stage_consistency(rates: pd.DataFrame) -> pd.DataFrame:
    """Compare sum of stage rates with reported total rate. The gap is reported, not hidden."""
    w = rates.pivot_table(index=KEYS, columns="stage", values="loss_rate").reset_index()
    w["stage_sum"] = w[STAGES].sum(axis=1)
    w["gap_pp"] = 100 * (w["total"] - w["stage_sum"])
    return w[KEYS + ["total", "stage_sum", "gap_pp"]]
