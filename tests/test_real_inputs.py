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


# ---- scaling survey district shares to the NISR national total (step 03 fallback) ----------------------
def _base(rows):
    return pd.DataFrame(rows, columns=["crop", "district", "season", "survey_t", "production_t"])


def test_scale_to_national_districts_sum_to_nisr_national():
    from isarura_core.estimators import BASE_DISTRICT, BASE_NATIONAL_SHARE, scale_to_national
    nat = pd.read_csv(INPUTS / "published_national.csv")
    nan = float("nan")
    base = _base([("maize", "Huye", "2024A", 100.0, nan), ("maize", "Gasabo", "2024A", 300.0, nan),
                  ("beans", "Huye", "2024A", 50.0, nan), ("beans", "Gasabo", "2024A", 50.0, nan),
                  ("maize", "Huye", "2025A", 10.0, 111.0), ("maize", "Gasabo", "2025A", 20.0, 222.0)])
    out = scale_to_national(base, nat).set_index(["crop", "district", "season"])
    national = nat.set_index(["crop", "season"])["production_t"]
    for crop in ("maize", "beans"):
        g = out.loc[crop].xs("2024A", level="season")
        assert g["production_t"].sum() == pytest.approx(national[(crop, "2024A")])
        assert (g["production_base"] == BASE_NATIONAL_SHARE).all()
    # shares follow the survey: Gasabo has 3x Huye's maize
    assert out.loc[("maize", "Gasabo", "2024A"), "production_t"] == pytest.approx(
        0.75 * national[("maize", "2024A")])
    # a crop x season with published district figures is untouched
    assert out.loc[("maize", "Huye", "2025A"), "production_t"] == 111.0
    assert out.loc[("maize", "Huye", "2025A"), "production_base"] == BASE_DISTRICT


def test_scale_to_national_falls_back_to_survey_when_no_national_figure():
    from isarura_core.estimators import BASE_SURVEY, scale_to_national
    nat = pd.read_csv(INPUTS / "published_national.csv")
    nan = float("nan")
    out = scale_to_national(_base([("maize", "Huye", "1999A", 40.0, nan), ("maize", "Gasabo", "1999A", 60.0, nan)]), nat)
    assert out["production_t"].tolist() == [40.0, 60.0]
    assert (out["production_base"] == BASE_SURVEY).all()


# ---- national headline: NISR production x NISR loss share (loss_official) ----------------------------------
def _official(prices=None):
    from isarura_core.conversions import official_loss
    nat = pd.read_csv(INPUTS / "published_national.csv")
    share = pd.read_csv(INPUTS / "published_loss_share.csv")
    return official_loss(nat, share, prices), nat, share


def test_loss_official_covers_every_published_crop_season_incl_rice():
    out, nat, share = _official()
    check(out, "loss_official")
    assert set(out["season"]) == {"2025A", "2025B", "2025C", "2026A", "2026B"}   # 2024 has no NISR loss share
    assert len(out) == len(share)                                                  # every published loss share is used
    assert not out.duplicated(["crop", "season"]).any()
    assert {"rice"} <= set(out[out["season"] == "2025A"]["crop"])
    assert set(out[out["season"] == "2025C"]["crop"]) == {"beans", "irish_potato", "sweet_potato"}


def test_loss_official_math():
    out, nat, share = _official()
    r = out.set_index(["crop", "season"])
    n = nat.set_index(["crop", "season"])["production_t"]
    s = share.set_index(["crop", "season"])["loss_share_pct"]
    for key in [("maize", "2025A"), ("rice", "2025B"), ("beans", "2026A")]:
        assert r.loc[key, "production_t"] == pytest.approx(n[key])
        assert r.loc[key, "tonnes_lost"] == pytest.approx(n[key] * s[key] / 100)
    from isarura_core.config import KCAL_PER_ADULT_DAY, KCAL_PER_KG
    k = ("maize", "2025A")
    assert r.loc[k, "kcal"] == pytest.approx(r.loc[k, "tonnes_lost"] * 1000 * KCAL_PER_KG["maize"])
    assert r.loc[k, "adult_years"] == pytest.approx(r.loc[k, "kcal"] / (KCAL_PER_ADULT_DAY * 365))
    assert "NISR" in r.loc[k, "source"] and "loss share" in r.loc[k, "source"]


def test_loss_official_value_columns_empty_without_prices_and_filled_with():
    out, _, _ = _official()
    assert out[["value_low_rwf", "value_rwf", "value_high_rwf"]].isna().all().all()
    assert out["tonnes_lost"].notna().all() and out["adult_years"].notna().all()
    prices = pd.DataFrame({"crop": ["maize", "maize"], "price_low": [100.0, 100.0],
                           "price_central": [200.0, 200.0], "price_high": [300.0, 300.0]})
    out2, _, _ = _official(prices)
    m = out2[out2["crop"] == "maize"].iloc[0]
    assert m["value_rwf"] == pytest.approx(m["tonnes_lost"] * 1000 * 200)
    assert out2[out2["crop"] == "beans"]["value_rwf"].isna().all()   # no price for beans -> empty, not zero


def test_loss_official_empty_inputs_give_empty_valid_table():
    from isarura_core.conversions import official_loss
    nat = pd.read_csv(INPUTS / "published_national.csv")
    out = official_loss(nat, pd.DataFrame(columns=["crop", "season", "loss_share_pct", "source"]))
    assert out.empty
    check(out, "loss_official")
