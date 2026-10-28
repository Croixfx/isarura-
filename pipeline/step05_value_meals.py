"""Step 05 - Tonnes -> Rwf (low/central/high), kcal, adult-years (FR-07, Method F).  OWNER: Croix"""
from isarura_core.contracts import check
from isarura_core.conversions import value_and_meals

from .common import Paths, log, read_out


def run(p: Paths):
    t = read_out(p, "tonnes")
    v = value_and_meals(t, read_out(p, "prices"))
    v = check(v, "loss_value")
    v.to_parquet(p.out("loss_value"), index=False)
    tot = v[v["stage"] == "total"]
    log("05", f"total: {tot['tonnes_lost'].sum():,.0f} t, {tot['value_rwf'].sum()/1e9:,.1f} bn Rwf, "
              f"{tot['adult_years'].sum():,.0f} adult-years")
