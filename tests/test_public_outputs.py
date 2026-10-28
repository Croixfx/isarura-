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
    # tolerance: SAS 2024A has 126 records with negative loss_storage_kg (known step01 data issue,
    # reported to Chadia), which pushes a few storage rates just below zero (worst: about -0.2%)
    assert r["loss_rate"].dropna().between(-5e-3, 1).all()


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
