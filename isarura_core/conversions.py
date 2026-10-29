"""Prices, value and meals (Method steps D to F). Owner: Croix."""
import numpy as np
import pandas as pd

from .config import KCAL_PER_ADULT_DAY, KCAL_PER_KG


NATIONAL = "National"


def national_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """One row per crop with low/central/high national prices: the explicit 'National' rows if the
    table has them, otherwise the median across districts."""
    pcols = ["price_low", "price_central", "price_high"]
    if "district" in prices and (prices["district"] == NATIONAL).any():
        return prices[prices["district"] == NATIONAL][["crop"] + pcols]
    return prices.groupby("crop", as_index=False)[pcols].median()


def trimmed_price_table(unit_values: pd.DataFrame, trim: float = 0.05, min_obs: int = 10) -> pd.DataFrame:
    """Median and IQR of EICV7 unit values per crop x district, after trimming extremes.

    District cells with fewer than `min_obs` observations fall back to the crop's
    national figures (source column says which).
    """
    uv = unit_values.dropna(subset=["unit_value_rwf_per_kg"])
    uv = uv[uv["unit_value_rwf_per_kg"] > 0]
    q = uv.groupby("crop")["unit_value_rwf_per_kg"].quantile([trim, 1 - trim]).unstack()
    uv = uv.join(q, on="crop")
    uv = uv[uv["unit_value_rwf_per_kg"].between(uv[trim], uv[1 - trim])]

    def summ(g):
        v = g["unit_value_rwf_per_kg"]
        return pd.Series({"price_low": v.quantile(0.25), "price_central": v.median(),
                          "price_high": v.quantile(0.75), "n_obs": len(v)})

    nat = uv.groupby("crop").apply(summ, include_groups=False).reset_index()
    dist = uv.groupby(["crop", "district"]).apply(summ, include_groups=False).reset_index()
    dist["source"] = "EICV7 unit values, district median"
    nat = nat.assign(district=NATIONAL, source="EICV7 unit values, national")
    thin = dist["n_obs"] < min_obs
    dist.loc[thin, ["price_low", "price_central", "price_high"]] = (
        dist.loc[thin, ["crop"]].merge(nat, on="crop", how="left")[["price_low", "price_central", "price_high"]].to_numpy())
    dist.loc[thin, "source"] = "EICV7 unit values, national median (thin district)"
    return pd.concat([dist, nat], ignore_index=True)


def cpi_factor(cpi: pd.DataFrame, base_month: str, latest_month: str, area: str = "Rural") -> float:
    s = cpi[cpi["area"] == area].set_index("month")["food_index"]
    return float(s[latest_month] / s[base_month])


def roll_forward(prices: pd.DataFrame, factor: float, month: str) -> pd.DataFrame:
    p = prices.copy()
    for c in ["price_low", "price_central", "price_high"]:
        p[c] = p[c] * factor
    p["month"] = month
    p["source"] = p["source"] + f", rolled to {month} with CPI food index (x{factor:.3f})"
    return p


def value_and_meals(tonnes: pd.DataFrame, prices: pd.DataFrame,
                    kcal_per_adult_day: float = KCAL_PER_ADULT_DAY,
                    kcal_per_kg: dict = KCAL_PER_KG) -> pd.DataFrame:
    """tonnes needs crop, district, tonnes_lost. Adds price, value range, kcal, adult_years."""
    pcols = ["crop", "district", "price_low", "price_central", "price_high"]
    v = tonnes.merge(prices[pcols], on=["crop", "district"], how="left")
    kg = v["tonnes_lost"] * 1000.0
    v["value_low_rwf"] = kg * v["price_low"]
    v["value_rwf"] = kg * v["price_central"]
    v["value_high_rwf"] = kg * v["price_high"]
    v["kcal"] = kg * v["crop"].map(kcal_per_kg).astype(float)
    v["adult_years"] = v["kcal"] / (kcal_per_adult_day * 365.0)
    return v


OFFICIAL_VALUE_COLS = ["value_low_rwf", "value_rwf", "value_high_rwf"]


def official_loss(national: pd.DataFrame, share: pd.DataFrame, prices: pd.DataFrame | None = None,
                  kcal_per_adult_day: float = KCAL_PER_ADULT_DAY,
                  kcal_per_kg: dict = KCAL_PER_KG) -> pd.DataFrame:
    """NISR published production x NISR published post-harvest loss share (% of production).

    One row per crop x season present in BOTH tables. Value columns use the national (median of
    district) price per crop and are NaN when `prices` is None or empty.
    """
    m = (national.rename(columns={"source": "src_production"})[["crop", "season", "production_t", "src_production"]]
         .merge(share.rename(columns={"source": "src_loss"})[["crop", "season", "loss_share_pct", "src_loss"]],
                on=["crop", "season"], how="inner"))
    m["tonnes_lost"] = m["production_t"] * m["loss_share_pct"] / 100.0
    kg = m["tonnes_lost"] * 1000.0
    m["kcal"] = kg * m["crop"].map(kcal_per_kg).astype(float)
    m["adult_years"] = m["kcal"] / (kcal_per_adult_day * 365.0)
    pcols = ["price_low", "price_central", "price_high"]
    if prices is not None and len(prices):
        m = m.merge(national_prices(prices), on="crop", how="left")
    else:
        for c in pcols:
            m[c] = np.nan
    m["value_low_rwf"], m["value_rwf"], m["value_high_rwf"] = (kg * m[c] for c in pcols)
    m["source"] = "Production: " + m["src_production"].astype(str) + "; loss share: " + m["src_loss"].astype(str)
    cols = ["crop", "season", "production_t", "loss_share_pct", "tonnes_lost", "kcal", "adult_years", "source"]
    return m[cols + OFFICIAL_VALUE_COLS].sort_values(["season", "crop"]).reset_index(drop=True)


def adult_years(kcal: float, kcal_per_adult_day: float = KCAL_PER_ADULT_DAY) -> float:
    return kcal / (kcal_per_adult_day * 365.0) if kcal_per_adult_day else np.nan
