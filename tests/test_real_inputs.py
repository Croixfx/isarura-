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


# ---- cross-check against the NISR workbooks kept in data/inputs/nisr_tables (needs openpyxl) -------------
LOSS_TABLES = [("SAS_2025_Annual_Tables", "Table 27", "2025A"), ("SAS_2025_Annual_Tables", "Table 28", "2025B"),
               ("SAS_2025_Annual_Tables", "Table 29", "2025C"), ("Tables_2026_Season_A", "Table 16", "2026A"),
               ("Tables_2026_Season_B", "Table 14", "2026B")]
CROP_OF = {"Maize": "maize", "Sorghum": "sorghum", "Paddy rice": "rice", "Wheat": "wheat",
           "Sweet potato": "sweet_potato", "Irish potato": "irish_potato", "Cassava": "cassava",
           "Cooking banana": "cooking_banana"}


@pytest.mark.parametrize("book,sheet,season", LOSS_TABLES)
def test_loss_share_matches_nisr_workbook(book, sheet, season):
    openpyxl = pytest.importorskip("openpyxl")
    path = INPUTS / "nisr_tables" / f"{book}.xlsx"
    if not path.exists():
        pytest.skip("NISR workbook not present")
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[sheet]
    rows = [r for r in ws.iter_rows(values_only=True) if any(c is not None for c in r)]
    header = next(r for r in rows if "Crops" in r)
    label, col = header.index("Crops"), header.index("Post harvesting losses")
    sh = pd.read_csv(INPUTS / "published_loss_share.csv")
    sh = sh[sh["season"] == season].set_index("crop")["loss_share_pct"]
    checked = 0
    for r in rows:
        crop = CROP_OF.get(str(r[label]).strip())
        if crop in sh.index and isinstance(r[col], (int, float)):
            assert sh[crop] == pytest.approx(r[col], rel=1e-6), (sheet, crop)
            checked += 1
    assert checked >= 2   # season C covers only sweet potato, Irish potato and beans (beans are weighted, not checked)
