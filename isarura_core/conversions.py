"""Prices, value and meals (Method steps D to F). Owner: Croix."""
import numpy as np
import pandas as pd

from .config import KCAL_PER_ADULT_DAY, KCAL_PER_KG


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
    thin = dist["n_obs"] < min_obs
    dist.loc[thin, ["price_low", "price_central", "price_high"]] = (
        dist.loc[thin, ["crop"]].merge(nat, on="crop", how="left")[["price_low", "price_central", "price_high"]].to_numpy())
    dist.loc[thin, "source"] = "EICV7 unit values, national median (thin district)"
    return dist


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


def adult_years(kcal: float, kcal_per_adult_day: float = KCAL_PER_ADULT_DAY) -> float:
    return kcal / (kcal_per_adult_day * 365.0) if kcal_per_adult_day else np.nan
