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
    assert set(pub["season"]) == {f"{y}{l}" for y in (2024, 2025) for l in "ABC"} | {"2026A", "2026B"}
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


def test_published_district_sums_to_national():
    nat = pd.read_csv(INPUTS / "published_national.csv")
    dist = check(pd.read_csv(INPUTS / "published_district.csv"), "published_district")
    assert dist["district"].nunique() == 30
    assert not dist.duplicated(["crop", "district", "season"]).any()
    s = dist.groupby(["crop", "season"], as_index=False)["production_t"].sum().merge(
        nat, on=["crop", "season"], suffixes=("_d", "_n"))
    assert len(s) > 0
    assert ((s["production_t_d"] - s["production_t_n"]).abs() / s["production_t_n"].clip(lower=1) < 1e-3).all()


def test_published_loss_share_contract():
    sh = check(pd.read_csv(INPUTS / "published_loss_share.csv"), "published_loss_share")
    assert sh["loss_share_pct"].between(0, 10).all()
    assert not sh.duplicated(["crop", "season"]).any()


def test_validate_loss_share_compares_pct_to_rate():
    from isarura_core.estimators import validate_loss_share
    rates = pd.DataFrame({"crop": ["maize", "maize"], "district": ["National", "Huye"], "stage": "total",
                          "season": "2025A", "loss_rate": [0.004, 0.5]})
    share = pd.DataFrame({"crop": ["maize", "maize"], "season": ["2025A", "2026A"],
                          "loss_share_pct": [0.35, 0.3], "source": "x"})
    v = check(validate_loss_share(rates, share), "validation_loss")
    assert len(v) == 1                                  # 2026A has no microdata; district rows ignored
    assert v["our_estimate_pct"].iloc[0] == pytest.approx(0.4)
    assert v["difference_pp"].iloc[0] == pytest.approx(0.05)
