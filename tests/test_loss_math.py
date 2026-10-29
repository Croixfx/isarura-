"""Hand-checkable math tests (QA section 10). Run: pytest -q"""
import numpy as np
import pandas as pd
import pytest

from isarura_core.config import STAGES
from isarura_core.conversions import adult_years, value_and_meals
from isarura_core.estimators import loss_rates, stage_consistency, validate_totals
from isarura_core.priority import priority


def tiny():
    # two farms, two clusters, one cell. Hand result for storage:
    # (2*10 + 1*30) / (2*100 + 1*200) = 50 / 400 = 0.125
    base = {"stratum": "s", "district": "Huye", "season": "2025A", "crop": "maize", "storage_type": "bags"}
    rows = [
        {**base, "farm_id": "f1", "cluster_id": "c1", "weight": 2.0, "harvest_kg": 100.0, "loss_total_kg": 15.0,
         "loss_transport_kg": 5.0, "loss_storage_kg": 10.0, "loss_processing_kg": 0.0, "loss_packaging_kg": 0.0, "loss_sales_kg": 0.0},
        {**base, "farm_id": "f2", "cluster_id": "c2", "weight": 1.0, "harvest_kg": 200.0, "loss_total_kg": 40.0,
         "loss_transport_kg": 0.0, "loss_storage_kg": 30.0, "loss_processing_kg": 0.0, "loss_packaging_kg": 0.0, "loss_sales_kg": 10.0},
    ]
    return pd.DataFrame(rows)


def rate(r, stage):
    return float(r.loc[r["stage"] == stage, "loss_rate"].iloc[0])


def test_weighted_ratio_by_hand():
    r = loss_rates(tiny(), n_boot=0)
    assert rate(r, "storage") == pytest.approx(0.125)
    assert rate(r, "transport") == pytest.approx(10 / 400)
    assert rate(r, "total") == pytest.approx((30 + 40) / 400)
    assert set(r["stage"]) == set(STAGES) | {"total"}


def test_small_n_flag():
    r = loss_rates(tiny(), n_boot=0, min_n=10)
    assert r["flag_small_n"].all() and (r["n_farmers"] == 2).all()


def test_stage_sum_matches_total_here():
    sc = stage_consistency(loss_rates(tiny(), n_boot=0))
    assert sc["gap_pp"].iloc[0] == pytest.approx(0.0)


def test_bootstrap_interval_contains_point():
    rng = np.random.default_rng(0)
    df = pd.concat([tiny().assign(farm_id=f"f{i}", cluster_id=f"c{i}",
                                  harvest_kg=rng.uniform(50, 300)) for i in range(40)])
    r = loss_rates(df, n_boot=300)
    s = r[r["stage"] == "storage"].iloc[0]
    assert s["ci_low"] <= s["loss_rate"] <= s["ci_high"]


def test_validation_tolerance():
    pub = pd.DataFrame({"crop": ["maize"], "season": ["2025A"], "production_t": [0.4], "source": ["x"]})
    v = validate_totals(tiny(), pub, tol_pct=5)
    assert v["our_estimate_t"].iloc[0] == pytest.approx(0.4)   # (2*100 + 1*200)/1000
    assert bool(v["within_tolerance"].iloc[0])


def test_value_and_meals():
    t = pd.DataFrame({"crop": ["maize"], "district": ["Huye"], "tonnes_lost": [2.0]})
    pr = pd.DataFrame({"crop": ["maize"], "district": ["Huye"], "price_low": [300.0],
                       "price_central": [400.0], "price_high": [500.0]})
    v = value_and_meals(t, pr, kcal_per_adult_day=2500, kcal_per_kg={"maize": 3650})
    assert v["value_rwf"].iloc[0] == 800_000
    assert v["kcal"].iloc[0] == 2000 * 3650
    assert v["adult_years"].iloc[0] == pytest.approx(2000 * 3650 / (2500 * 365))
    assert adult_years(2500 * 365, kcal_per_adult_day=2500) == pytest.approx(1.0)
    from isarura_core.config import KCAL_PER_ADULT_DAY
    assert KCAL_PER_ADULT_DAY == 2400   # NISR EICV7 Methodological Note, p.30


def test_priority_default_and_scenario():
    lv = pd.DataFrame([
        {"district": "Huye", "crop": "maize", "season": "2025A", "stage": "total", "value_rwf": 100.0, "tonnes_lost": 1.0, "flag_small_n": False},
        {"district": "Huye", "crop": "maize", "season": "2025A", "stage": "storage", "value_rwf": 80.0, "tonnes_lost": 0.8, "flag_small_n": False},
        {"district": "Musanze", "crop": "beans", "season": "2025A", "stage": "total", "value_rwf": 150.0, "tonnes_lost": 1.0, "flag_small_n": False},
        {"district": "Musanze", "crop": "beans", "season": "2025A", "stage": "storage", "value_rwf": 10.0, "tonnes_lost": 0.1, "flag_small_n": False},
    ])
    d = priority(lv)
    assert d.iloc[0]["district"] == "Musanze"            # biggest total loss first
    s = priority(lv, a_k={"storage": 0.5})
    assert s.iloc[0]["district"] == "Huye"               # storage fix pays more in Huye
    assert s.iloc[0]["avoidable_value_rwf"] == pytest.approx(40.0)


def test_negative_losses_become_missing_and_are_logged(capsys):
    from pipeline.step01_load_sas import negatives_to_missing
    df = pd.DataFrame({"season": ["2024A", "2024A", "2025A"],
                       "loss_total_kg": [5.0, -1.0, 2.0], "loss_storage_kg": [-340.0, 0.0, 3.0],
                       "loss_transport_kg": [0.0, 1.0, 2.0], "loss_processing_kg": [0.0, 0.0, 0.0],
                       "loss_packaging_kg": [0.0, 0.0, 0.0], "loss_sales_kg": [0.0, 0.0, -2.0]})
    out = negatives_to_missing(df)
    assert out["loss_storage_kg"].isna().tolist() == [True, False, False]
    assert out["loss_total_kg"].isna().tolist() == [False, True, False]
    assert out["loss_sales_kg"].isna().tolist() == [False, False, True]
    assert out["loss_transport_kg"].notna().all()               # untouched columns keep their values
    assert out["loss_storage_kg"].iloc[2] == 3.0 and out["loss_total_kg"].iloc[0] == 5.0
    assert (df["loss_storage_kg"].iloc[0] == -340.0)           # input frame is not modified
    log = capsys.readouterr().out
    assert "2024A" in log and "loss_storage_kg" in log and "1 negative" in log.replace("     1", "1")
    assert "2025A" in log and "loss_sales_kg" in log


def test_kcal_factors_are_sourced_and_consistent():
    import csv
    from isarura_core.config import CROPS, INPUTS, KCAL_PER_KG
    assert list(KCAL_PER_KG) == CROPS
    assert all(v > 0 for v in KCAL_PER_KG.values())
    assert KCAL_PER_KG["rice"] < KCAL_PER_KG["maize"]            # paddy adjustment applied
    with open(INPUTS / "kcal_per_kg.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            expect = (float(row["kcal_per_100g_edible"]) * 10 * (1 - float(row["waste_pct"]) / 100)
                      * float(row["extra_factor"]))
            assert KCAL_PER_KG[row["crop"]] == pytest.approx(expect, abs=1.0), row["crop"]
            assert row["source"].strip() and row["table_entry"].strip()
