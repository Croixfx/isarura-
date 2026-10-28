"""Step 03 - Loss rates with intervals, then tonnes (FR-03, FR-04, FR-05; Method B-D).  OWNER: Croix

Output: loss_rates (district rows + 'National' rows), tonnes (rate x published production),
        stage_consistency (stage sum vs reported total, for the Methods page).
"""
import pandas as pd

from isarura_core.contracts import check
from isarura_core.estimators import loss_rates, stage_consistency, weighted_production

from .common import Paths, log


def run(p: Paths, n_boot: int = 200):
    rec = pd.read_parquet(p.crop_records)
    
    # --- FIX FOR 2025 DATA GAP ---
    # SAS 2025 does not have a single "total loss" question (s2q39).
    # We calculate it by summing the individual stages.
    stages = ["loss_transport_kg", "loss_storage_kg", "loss_processing_kg", "loss_packaging_kg", "loss_sales_kg"]
    calculated_total = rec[stages].sum(axis=1)
    rec["loss_total_kg"] = rec["loss_total_kg"].fillna(calculated_total)
    # ------------------------------

    dist = loss_rates(rec, n_boot=n_boot)
    nat = loss_rates(rec.assign(district="National"), n_boot=n_boot)
    rates = check(pd.concat([dist, nat], ignore_index=True), "loss_rates")
    rates.to_parquet(p.out("loss_rates"), index=False)
    stage_consistency(dist).to_parquet(p.out("stage_consistency"), index=False)
    log("03", f"{len(dist):,} district cells, {dist['flag_small_n'].mean():.0%} flagged small-n")

    # Tonnes: apply the rate to PUBLISHED district production so totals reconcile to NISR.
    # Where NISR publishes no district figure, fall back to our weighted estimate and say so.
    pub_path = p.inputs / "published_district.csv"
    ours = weighted_production(rec, by=("crop", "district", "season")).rename(columns={"our_estimate_t": "survey_t"})
    
    if pub_path.exists():
        # ADDED dtype={'production_t': float} to prevent TypeError on typos in the CSV
        pub = check(pd.read_csv(pub_path, dtype={'production_t': float}), "published_district")[["crop", "district", "season", "production_t"]]
        base = ours.merge(pub, on=["crop", "district", "season"], how="left")
    else:
        base = ours.assign(production_t=float("nan"))
        
    base["production_base"] = base["production_t"].notna().map({True: "NISR published", False: "survey estimate"})
    base["production_t"] = base["production_t"].fillna(base["survey_t"])

    t = dist.merge(base[["crop", "district", "season", "production_t", "production_base"]],
                   on=["crop", "district", "season"], how="left")
    t["tonnes_lost"] = t["loss_rate"] * t["production_t"]
    t.to_parquet(p.out("tonnes"), index=False)
    share = (base["production_base"] == "NISR published").mean()
    log("03", f"tonnes computed; {share:.0%} of cells use NISR published production as base")