"""Step 03 - Loss rates with intervals, then tonnes (FR-03, FR-04, FR-05; Method B-D).  OWNER: Croix

Output: loss_rates (district rows + 'National' rows), tonnes (rate x published production),
        stage_consistency (stage sum vs reported total, for the Methods page).
"""
import pandas as pd

from isarura_core.contracts import CONTRACTS, check
from isarura_core.estimators import (loss_rates, scale_to_national, stage_consistency, validate_loss_share,
                                     weighted_production)

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

    # Second validation: our national loss rate against NISR's own published post-harvest loss share.
    share_path = p.inputs / "published_loss_share.csv"
    share = pd.read_csv(share_path) if share_path.exists() else pd.DataFrame()
    if share.empty:
        share = pd.DataFrame(columns=list(CONTRACTS["published_loss_share"]))
    vl = check(validate_loss_share(rates, check(share, "published_loss_share")), "validation_loss")
    vl.to_parquet(p.out("validation_loss"), index=False)
    if len(vl):
        log("03", f"loss share vs NISR: median |diff| {vl['difference_pp'].abs().median():.2f} pp "
                  f"over {len(vl)} crop x season pairs")
    else:
        log("03", "no published loss shares to compare with")
    log("03", f"{len(dist):,} district cells, {dist['flag_small_n'].mean():.0%} flagged small-n")

    # Tonnes: apply the rate to PUBLISHED district production so totals reconcile to NISR.
    # Where NISR publishes no district figure for a crop x season (e.g. 2024A), scale each district's
    # survey share to NISR's published NATIONAL production; only if that is missing too, use the raw
    # survey total. production_base records which one was used.
    pub_path = p.inputs / "published_district.csv"
    ours = weighted_production(rec, by=("crop", "district", "season")).rename(columns={"our_estimate_t": "survey_t"})
    
    if pub_path.exists():
        # ADDED dtype={'production_t': float} to prevent TypeError on typos in the CSV
        pub = check(pd.read_csv(pub_path, dtype={'production_t': float}), "published_district")[["crop", "district", "season", "production_t"]]
    pub = pd.read_csv(pub_path) if pub_path.exists() else pd.DataFrame()
    if not pub.empty:
        pub = check(pub, "published_district")[["crop", "district", "season", "production_t"]]
        base = ours.merge(pub, on=["crop", "district", "season"], how="left")
    else:
        base = ours.assign(production_t=float("nan"))
    national = check(pd.read_csv(p.inputs / "published_national.csv"), "published_national")
    base = scale_to_national(base, national)

    t = dist.merge(base[["crop", "district", "season", "production_t", "production_base"]],
                   on=["crop", "district", "season"], how="left")
    t["tonnes_lost"] = t["loss_rate"] * t["production_t"]
    t.to_parquet(p.out("tonnes"), index=False)
    tot = t[t["stage"] == "total"]
    for col, what in (("production_t", "production"), ("tonnes_lost", "tonnes lost")):
        sh = tot.groupby("production_base")[col].sum() / tot[col].sum()
        log("03", f"share of {what} by production base: " + ", ".join(f"{k} {v:.1%}" for k, v in sh.items()))
    log("03", "share of cells: " + ", ".join(
        f"{k} {v:.0%}" for k, v in base["production_base"].value_counts(normalize=True).items()))
