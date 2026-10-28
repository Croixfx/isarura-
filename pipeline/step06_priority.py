"""Step 06 - Default priority index (FR-08, Method H).  OWNER: Croix
The app recomputes scenarios live with isarura_core.priority.priority()."""
from isarura_core.contracts import check
from isarura_core.priority import priority

from .common import Paths, log, read_out


def run(p: Paths):
    lv = read_out(p, "loss_value")
    latest_year = sorted(lv["season"].str[:4].unique())[-1]
    pr = priority(lv, seasons=[s for s in lv["season"].unique() if s.startswith(latest_year)])
    pr = check(pr, "priority_index")
    pr.to_parquet(p.out("priority_index"), index=False)
    top = pr.iloc[0]
    log("06", f"top pair {latest_year}: {top['district']} / {top['crop']} ({top['loss_value_rwf']/1e6:,.0f} m Rwf)")
