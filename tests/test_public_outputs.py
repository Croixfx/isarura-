"""Checks on whatever is in data/public (synthetic or real). Runs in CI."""
import json

import pandas as pd
import pytest

from isarura_core.config import PUBLIC
from isarura_core.contracts import PUBLIC_TABLES, check

pytestmark = pytest.mark.skipif(not (PUBLIC / "meta.json").exists(), reason="run the pipeline first")


@pytest.mark.parametrize("name", PUBLIC_TABLES)
def test_contract(name):
    check(pd.read_csv(PUBLIC / f"{name}.csv"), name)


@pytest.mark.parametrize("name", PUBLIC_TABLES)
def test_no_farm_level_columns(name):
    cols = set(pd.read_csv(PUBLIC / f"{name}.csv", nrows=1).columns)
    assert not cols & {"farm_id", "cluster_id", "weight", "hh_id"}


def test_rates_are_proportions():
    r = pd.read_csv(PUBLIC / "loss_rates.csv")
    assert r["loss_rate"].dropna().between(0, 1).all()


def test_geojson_covers_all_districts():
    from isarura_core.config import DISTRICT_LIST
    gj = json.loads((PUBLIC / "districts.geojson").read_text())
    names = {f["properties"]["district"] for f in gj["features"]}
    assert set(DISTRICT_LIST) <= names


def test_loss_official_public_table_is_consistent():
    o = pd.read_csv(PUBLIC / "loss_official.csv")
    assert not o.duplicated(["crop", "season"]).any()
    assert o["tonnes_lost"].sub(o["production_t"] * o["loss_share_pct"] / 100).abs().max() < 1e-6 * max(1, o["production_t"].max())
    assert (o["tonnes_lost"] <= o["production_t"]).all()
    assert (o["adult_years"] >= 0).all()


def test_value_columns_empty_when_no_prices():
    meta = json.loads((PUBLIC / "meta.json").read_text())
    if meta.get("prices_available", True):
        pytest.skip("prices are available")
    assert pd.read_csv(PUBLIC / "prices.csv").empty
    assert pd.read_csv(PUBLIC / "loss_value.csv")["value_rwf"].isna().all()
    assert pd.read_csv(PUBLIC / "loss_official.csv")["value_rwf"].isna().all()
    assert meta["official_seasons"]


def test_values_ordered_and_present_when_prices_available():
    meta = json.loads((PUBLIC / "meta.json").read_text())
    if not meta.get("prices_available", True):
        pytest.skip("no prices")
    o = pd.read_csv(PUBLIC / "loss_official.csv")
    ok = o["tonnes_lost"] > 0
    assert o.loc[ok, ["value_low_rwf", "value_rwf", "value_high_rwf"]].notna().all().all()
    assert (o["value_low_rwf"] <= o["value_rwf"]).all() and (o["value_rwf"] <= o["value_high_rwf"]).all()
    p = pd.read_csv(PUBLIC / "prices.csv")
    assert (p["district"] == "National").sum() == p["crop"].nunique()
    assert not p[["price_low", "price_central", "price_high"]].isna().any().any()
