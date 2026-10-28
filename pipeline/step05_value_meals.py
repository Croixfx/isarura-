"""Step 05 - Tonnes -> Rwf (low/central/high), kcal, adult-years (FR-07, Method F).  OWNER: Croix

Also builds `loss_latest`: for seasons NISR has published but whose microdata is not out yet
(e.g. 2026 A and B), apply the national loss rate of the same season letter in the latest
microdata year to the published national production. Labelled as an extrapolation.
"""
import pandas as pd

from isarura_core.config import KCAL_PER_ADULT_DAY, KCAL_PER_KG
from isarura_core.contracts import CONTRACTS, check
from isarura_core.conversions import value_and_meals

from .common import Paths, log, read_out


def latest_seasons(p: Paths, rates: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    cols = list(CONTRACTS["loss_latest"])
    pub = pd.read_csv(p.inputs / "published_national.csv")
    have = set(rates["season"])
    last_year = max(s[:4] for s in have)
    new = pub[~pub["season"].isin(have) & (pub["season"].str[:4] > last_year)].copy()
    if new.empty:
        return pd.DataFrame({c: pd.Series(dtype="float64" if k == "num" else "object")
                             for c, k in CONTRACTS["loss_latest"].items()})
    nat = rates[(rates["district"] == "National") & (rates["stage"] == "total")]
    new["rate_from_season"] = last_year + new["season"].str[-1]
    new = new.merge(nat[["crop", "season", "loss_rate"]].rename(columns={"season": "rate_from_season"}),
                    on=["crop", "rate_from_season"], how="inner")
    new["tonnes_lost"] = new["loss_rate"] * new["production_t"]
    nat_price = prices.groupby("crop", as_index=False)[["price_low", "price_central", "price_high"]].median()
    kg = new["tonnes_lost"] * 1000
    new = new.merge(nat_price, on="crop", how="left")
    new["value_low_rwf"] = kg * new["price_low"]
    new["value_rwf"] = kg * new["price_central"]
    new["value_high_rwf"] = kg * new["price_high"]
    new["kcal"] = kg * new["crop"].map(KCAL_PER_KG).astype(float)
    new["adult_years"] = new["kcal"] / (KCAL_PER_ADULT_DAY * 365.0)
    new["source"] = new["source"] + "; loss rate from SAS microdata season " + new["rate_from_season"]
    return new[cols]


def run(p: Paths):
    t = read_out(p, "tonnes")
    prices = read_out(p, "prices")
    v = check(value_and_meals(t, prices), "loss_value")
    v.to_parquet(p.out("loss_value"), index=False)
    tot = v[v["stage"] == "total"]
    log("05", f"total: {tot['tonnes_lost'].sum():,.0f} t, {tot['value_rwf'].sum()/1e9:,.1f} bn Rwf, "
              f"{tot['adult_years'].sum():,.0f} adult-years")

    latest = check(latest_seasons(p, read_out(p, "loss_rates"), prices), "loss_latest")
    latest.to_parquet(p.out("loss_latest"), index=False)
    if len(latest):
        for s, g in latest.groupby("season"):
            log("05", f"latest {s} (rates from {g['rate_from_season'].iloc[0]}): "
                      f"{g['tonnes_lost'].sum():,.0f} t, {g['value_rwf'].sum()/1e9:,.1f} bn Rwf")
    else:
        log("05", "no published seasons newer than the microdata")
