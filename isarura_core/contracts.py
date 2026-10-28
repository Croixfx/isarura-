"""Data contracts: the agreed columns of every table that passes between teammates.

If you need to change a contract, change it here in a PR the other person reviews.
`check(df, "name")` raises if a table breaks its contract, so mistakes fail loudly.
"""
import pandas as pd

from .config import ALL_STAGES, CROPS, DISTRICT_LIST

# kind: "str", "num", "int", "bool"
CONTRACTS = {
    # ---- private (data/interim) -------------------------------------------------
    # One row per farm x crop x season. Produced by step01 (Chadia). Never published.
    "crop_records": {
        "farm_id": "str", "cluster_id": "str", "stratum": "str", "weight": "num",
        "district": "str", "season": "str", "crop": "str",
        "harvest_kg": "num", "loss_total_kg": "num",
        "loss_transport_kg": "num", "loss_storage_kg": "num", "loss_processing_kg": "num",
        "loss_packaging_kg": "num", "loss_sales_kg": "num",
        "storage_type": "str",
    },
    # ---- hand-built inputs (data/inputs), copied from NISR publications ----------
    # National production by crop x season from the SAS report (Croix).
    "published_national": {"crop": "str", "season": "str", "production_t": "num", "source": "str"},
    # NISR official post-harvest loss as % of production, by crop x season ("Use of production by
    # farmers" tables). Used to validate our loss rates (Croix).
    "published_loss_share": {"crop": "str", "season": "str", "loss_share_pct": "num", "source": "str"},
    # District production by crop x season from the SAS report (Croix). May be partial.
    "published_district": {"crop": "str", "district": "str", "season": "str", "production_t": "num", "source": "str"},
    # Unit values from EICV7 food records, one row per household item (private, Croix).
    "unit_values": {"crop": "str", "district": "str", "unit_value_rwf_per_kg": "num"},
    # CPI food index by month and area, from CPI_time_series_*.xls (Croix).
    "cpi": {"month": "str", "area": "str", "food_index": "num"},
    # ---- public (data/public) -----------------------------------------------------
    "validation": {"crop": "str", "season": "str", "nisr_published_t": "num", "our_estimate_t": "num",
                   "difference_pct": "num", "within_tolerance": "bool"},
    "validation_loss": {"crop": "str", "season": "str", "nisr_published_pct": "num",
                        "our_estimate_pct": "num", "difference_pp": "num"},
    "loss_rates": {"crop": "str", "district": "str", "season": "str", "stage": "str",
                   "loss_rate": "num", "ci_low": "num", "ci_high": "num",
                   "n_farmers": "int", "flag_small_n": "bool"},
    "prices": {"crop": "str", "district": "str", "month": "str", "price_low": "num",
               "price_central": "num", "price_high": "num", "source": "str"},
    "loss_value": {"crop": "str", "district": "str", "season": "str", "stage": "str",
                   "production_t": "num", "production_base": "str", "tonnes_lost": "num",
                   "price_low": "num", "price_central": "num", "price_high": "num",
                   "value_low_rwf": "num", "value_rwf": "num", "value_high_rwf": "num",
                   "kcal": "num", "adult_years": "num", "flag_small_n": "bool"},
    # Latest official seasons (published production newer than the microdata), national level:
    # loss rate from the same season letter in the latest microdata year x published production.
    "loss_latest": {"crop": "str", "season": "str", "rate_from_season": "str", "production_t": "num",
                    "loss_rate": "num", "tonnes_lost": "num", "value_low_rwf": "num", "value_rwf": "num",
                    "value_high_rwf": "num", "kcal": "num", "adult_years": "num", "source": "str"},
    "priority_index": {"district": "str", "crop": "str", "loss_value_rwf": "num",
                       "avoidable_value_rwf": "num", "rank": "int", "assumption_set": "str"},
}

PUBLIC_TABLES = ["validation", "validation_loss", "loss_rates", "prices", "loss_value", "loss_latest", "priority_index"]

_KIND_CHECK = {
    "str": lambda s: pd.api.types.is_string_dtype(s) or pd.api.types.is_object_dtype(s),
    "num": pd.api.types.is_numeric_dtype,
    "int": pd.api.types.is_integer_dtype,
    "bool": pd.api.types.is_bool_dtype,
}


def check(df: pd.DataFrame, name: str) -> pd.DataFrame:
    spec = CONTRACTS[name]
    missing = [c for c in spec if c not in df.columns]
    if missing:
        raise ValueError(f"{name}: missing columns {missing}")
    # an empty table (e.g. header-only CSV not filled yet) has no meaningful dtypes
    bad = [] if df.empty else [c for c, k in spec.items() if not _KIND_CHECK[k](df[c])]
    if bad:
        raise TypeError(f"{name}: wrong dtype for {[(c, str(df[c].dtype), spec[c]) for c in bad]}")
    if "district" in spec and name not in ("unit_values",):
        unknown = sorted(set(df["district"]) - set(DISTRICT_LIST) - {"National"})
        if unknown:
            raise ValueError(f"{name}: unknown districts {unknown[:5]} (spell as in config.DISTRICT_LIST)")
    if "crop" in spec:
        unknown = sorted(set(df["crop"]) - set(CROPS))
        if unknown:
            raise ValueError(f"{name}: unknown crops {unknown[:5]} (add to config.KCAL_PER_KG or recode)")
    if "stage" in spec:
        unknown = sorted(set(df["stage"]) - set(ALL_STAGES))
        if unknown:
            raise ValueError(f"{name}: unknown stages {unknown}")
    return df[list(spec) + [c for c in df.columns if c not in spec]]
