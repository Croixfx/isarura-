"""Priority index (Method step H). Owner: Croix. Also called live by the app for sliders.

Default (no assumptions): rank district x crop pairs by total loss value.
Scenario: user sets a_k (share of stage-k loss an intervention could avoid) and, optionally,
a cost per tonne avoided; then rank by avoidable value, or avoidable value per franc spent.
"""
import pandas as pd

from .config import STAGES


def priority(loss_value: pd.DataFrame, a_k: dict | None = None, price_change: float = 0.0,
             cost_per_tonne: float | None = None, seasons: list | None = None,
             include_small_n: bool = True) -> pd.DataFrame:
    lv = loss_value
    if seasons:
        lv = lv[lv["season"].isin(seasons)]
    if not include_small_n:
        lv = lv[~lv["flag_small_n"]]
    mult = 1.0 + price_change

    if not a_k:
        t = lv[lv["stage"] == "total"]
        g = t.groupby(["district", "crop"], as_index=False).agg(
            loss_value_rwf=("value_rwf", "sum"), tonnes_lost=("tonnes_lost", "sum"))
        g["loss_value_rwf"] *= mult
        g["avoidable_value_rwf"] = g["loss_value_rwf"]
        g["tonnes_avoided"] = g["tonnes_lost"]
        g["assumption_set"] = "default: total loss value, no effectiveness assumed"
    else:
        s = lv[lv["stage"].isin(STAGES)].copy()
        s["a"] = s["stage"].map(a_k).fillna(0.0)
        s["avoid_v"] = s["value_rwf"] * s["a"] * mult
        s["avoid_t"] = s["tonnes_lost"] * s["a"]
        g = s.groupby(["district", "crop"], as_index=False).agg(
            avoidable_value_rwf=("avoid_v", "sum"), tonnes_avoided=("avoid_t", "sum"))
        tot = lv[lv["stage"] == "total"].groupby(["district", "crop"], as_index=False).agg(
            loss_value_rwf=("value_rwf", "sum"), tonnes_lost=("tonnes_lost", "sum"))
        tot["loss_value_rwf"] *= mult
        g = g.merge(tot, on=["district", "crop"], how="left")
        g["assumption_set"] = "scenario: " + ", ".join(f"{k}={v:.0%}" for k, v in a_k.items() if v)

    sort_col = "avoidable_value_rwf"
    if cost_per_tonne:
        g["cost_rwf"] = g["tonnes_avoided"] * cost_per_tonne
        g["value_per_rwf"] = g["avoidable_value_rwf"] / g["cost_rwf"].where(g["cost_rwf"] > 0)
        g["assumption_set"] += f", cost {cost_per_tonne:,.0f} Rwf/t"
        sort_col = "value_per_rwf"
    if price_change:
        g["assumption_set"] += f", price change {price_change:+.0%}"
    g = g.sort_values(sort_col, ascending=False, na_position="last").reset_index(drop=True)
    g["rank"] = (g.index + 1).astype("int64")
    return g
