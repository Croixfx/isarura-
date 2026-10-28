"""FAKE data with the exact shapes of the real inputs, so both of us can build before
the NISR microdata arrives. Every output is marked DEMO. Delete nothing here; just stop
using --synthetic once real files are in data/raw and data/inputs.
"""
import json

import numpy as np
import pandas as pd

from isarura_core.config import CROPS, DISTRICT_LIST, INPUTS, INTERIM, PUBLIC, STAGES

SEASONS = ["2024A", "2024B", "2025A", "2025B"]
DEMO = "DEMO synthetic data - not NISR"

# rough, invented loss profiles per crop (share of harvest lost at each stage)
PROFILE = {
    "maize": [0.02, 0.06, 0.02, 0.005, 0.01], "beans": [0.015, 0.04, 0.02, 0.005, 0.01],
    "sorghum": [0.01, 0.05, 0.015, 0.005, 0.005], "rice": [0.02, 0.03, 0.04, 0.01, 0.01],
    "wheat": [0.015, 0.035, 0.02, 0.005, 0.005], "cassava": [0.03, 0.02, 0.05, 0.005, 0.03],
    "irish_potato": [0.04, 0.07, 0.01, 0.01, 0.04], "sweet_potato": [0.03, 0.05, 0.01, 0.005, 0.03],
    "cooking_banana": [0.04, 0.03, 0.01, 0.01, 0.06],
}
YIELD_KG = {"maize": 900, "beans": 400, "sorghum": 600, "rice": 1500, "wheat": 500, "cassava": 3000,
            "irish_potato": 2500, "sweet_potato": 2000, "cooking_banana": 2500}
PRICE = {"maize": 450, "beans": 1100, "sorghum": 550, "rice": 1300, "wheat": 700, "cassava": 300,
         "irish_potato": 400, "sweet_potato": 250, "cooking_banana": 350}


def make_crop_records(seed=7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for di, d in enumerate(DISTRICT_LIST):
        risk = 0.6 + 0.8 * rng.random()  # district loss multiplier
        crops = rng.choice(CROPS, size=6, replace=False)
        for s in SEASONS:
            for c in range(int(rng.integers(3, 12))):  # some thin district-seasons on purpose
                cid = f"{d[:3].upper()}-{s}-{c:02d}"
                for f in range(rng.integers(4, 9)):
                    fid = f"{cid}-{f}"
                    w = float(rng.uniform(80, 220))
                    for crop in rng.choice(crops, size=rng.integers(1, 4), replace=False):
                        if rng.random() < 0.05:   # make a few thin cells on purpose
                            continue
                        h = float(rng.gamma(2.0, YIELD_KG[crop] / 2.0))
                        prof = np.array(PROFILE[crop]) * risk * rng.lognormal(0, 0.5, 5)
                        stage_loss = np.minimum(h * prof, h * 0.3)
                        reported_total = stage_loss.sum() * rng.uniform(0.9, 1.1)
                        rows.append({"farm_id": fid, "cluster_id": cid, "stratum": d, "weight": w,
                                     "district": d, "season": s, "crop": str(crop), "harvest_kg": h,
                                     "loss_total_kg": reported_total,
                                     **{f"loss_{k}_kg": v for k, v in zip(STAGES, stage_loss)},
                                     "storage_type": str(rng.choice(["house", "granary", "bags", "none", "public_store"]))})
    return pd.DataFrame(rows)


def make_inputs(records: pd.DataFrame, seed=8):
    rng = np.random.default_rng(seed)
    r = records.assign(wh=records["weight"] * records["harvest_kg"] / 1000)
    nat = r.groupby(["crop", "season"], as_index=False)["wh"].sum()
    nat["production_t"] = nat.pop("wh") * rng.uniform(0.96, 1.04, len(nat))
    nat["source"] = DEMO
    dist = r.groupby(["crop", "district", "season"], as_index=False)["wh"].sum()
    dist["production_t"] = dist.pop("wh") * rng.uniform(0.9, 1.1, len(dist))
    dist["source"] = DEMO

    uv = []
    for crop, p in PRICE.items():
        for d in DISTRICT_LIST:
            n = int(rng.integers(3, 40))
            uv += [{"crop": crop, "district": d, "unit_value_rwf_per_kg": float(v)}
                   for v in p * rng.lognormal(0, 0.25, n)]
    uv = pd.DataFrame(uv)

    months = pd.period_range("2023-10", "2026-09", freq="M").astype(str)
    cpi = []
    for area, g in [("Urban", 0.010), ("Rural", 0.012), ("All Rwanda", 0.011)]:
        idx = 100 * np.cumprod(1 + g + rng.normal(0, 0.006, len(months)))
        cpi += [{"month": m, "area": area, "food_index": float(v)} for m, v in zip(months, idx)]
    return nat, dist, uv, pd.DataFrame(cpi)


def make_demo_geojson():
    """A 6x5 grid of squares, one per district. NOT real boundaries.
    Chadia replaces data/public/districts.geojson with simplified real boundaries."""
    feats = []
    for i, d in enumerate(DISTRICT_LIST):
        x, y = 29.0 + (i % 6) * 0.3, -1.2 - (i // 6) * 0.3
        poly = [[x, y], [x + 0.28, y], [x + 0.28, y - 0.28], [x, y - 0.28], [x, y]]
        feats.append({"type": "Feature", "properties": {"district": d, "demo": True},
                      "geometry": {"type": "Polygon", "coordinates": [poly]}})
    return {"type": "FeatureCollection", "features": feats}


def write_all():
    for p in (INPUTS, INTERIM, PUBLIC):
        p.mkdir(parents=True, exist_ok=True)
    rec = make_crop_records()
    rec.to_parquet(INTERIM / "crop_records.parquet", index=False)
    nat, dist, uv, cpi = make_inputs(rec)
    nat.to_csv(INTERIM / "published_national.csv", index=False)
    dist.to_csv(INTERIM / "published_district.csv", index=False)
    uv.to_parquet(INTERIM / "unit_values.parquet", index=False)
    cpi.to_csv(INTERIM / "cpi.csv", index=False)
    gj = PUBLIC / "districts.geojson"
    if not gj.exists() or json.loads(gj.read_text())["features"][0]["properties"].get("demo"):
        gj.write_text(json.dumps(make_demo_geojson()))
    print(f"[synthetic] {len(rec):,} fake crop records written (DEMO).")
