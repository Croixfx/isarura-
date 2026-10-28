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
