"""The hand-typed NISR inputs in data/inputs obey their contracts, and the latest-seasons
extrapolation (loss_latest) works on them."""
import pandas as pd
import pytest

from isarura_core.config import CROPS, INPUTS
from isarura_core.contracts import check
from isarura_core.conversions import cpi_factor
from isarura_core.estimators import validate_totals
from pipeline.common import Paths
from pipeline.step05_value_meals import latest_seasons


def test_published_national_contract():
    pub = check(pd.read_csv(INPUTS / "published_national.csv"), "published_national")
    assert set(pub["crop"]) == set(CROPS)
    assert set(pub["season"]) == {"2025A", "2025B", "2026A", "2026B"}
    assert not pub.duplicated(["crop", "season"]).any()


def test_cpi_contract_and_factor():
    cpi = check(pd.read_csv(INPUTS / "cpi.csv", dtype={"month": str}), "cpi")
    assert cpi_factor(cpi, "2024-01", "2026-09", "Rural") == pytest.approx(332.5 / 236.2)


def test_empty_published_district_passes_contract():
    check(pd.DataFrame(columns=["crop", "district", "season", "production_t", "source"]), "published_district")


def test_validation_ignores_seasons_without_microdata():
    pub = pd.read_csv(INPUTS / "published_national.csv")
    rec = pd.DataFrame({"crop": ["maize"], "season": ["2025A"], "weight": [1.0], "harvest_kg": [1000.0]})
    v = validate_totals(rec, pub)
    assert set(v["season"]) == {"2025A"}


def test_latest_seasons_uses_same_letter_rate():
    pub = pd.read_csv(INPUTS / "published_national.csv")
    rates = pd.DataFrame({"crop": ["maize", "maize", "maize"], "district": "National", "stage": "total",
                          "season": ["2025A", "2025B", "2025A"], "loss_rate": [0.10, 0.20, 0.10]}
                         ).drop_duplicates(["crop", "season"])
    prices = pd.DataFrame({"crop": ["maize"] * 2, "price_low": [100.0, 100.0],
                           "price_central": [200.0, 200.0], "price_high": [300.0, 300.0]})

    class P(Paths):
        inputs = INPUTS

    out = latest_seasons(P(synthetic=False), rates, prices)
    a = out[out["season"] == "2026A"].iloc[0]
    b = out[out["season"] == "2026B"].iloc[0]
    assert a["rate_from_season"] == "2025A" and b["rate_from_season"] == "2025B"
    assert a["tonnes_lost"] == pytest.approx(0.10 * 488622)
    assert b["tonnes_lost"] == pytest.approx(0.20 * 122370)
    assert a["value_rwf"] == pytest.approx(a["tonnes_lost"] * 1000 * 200)
    assert "SAS microdata season 2025A" in a["source"]
    check(out, "loss_latest")
