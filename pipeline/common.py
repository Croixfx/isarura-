"""Where each step reads and writes. Real runs read published tables from data/inputs;
--synthetic runs read the fake ones from data/interim."""
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from isarura_core.config import INPUTS, INTERIM


@dataclass
class Paths:
    synthetic: bool

    @property
    def inputs(self) -> Path:          # published tables, CPI
        return INTERIM if self.synthetic else INPUTS

    crop_records = INTERIM / "crop_records.parquet"
    unit_values = INTERIM / "unit_values.parquet"

    def out(self, name: str) -> Path:  # private step outputs
        return INTERIM / f"{name}.parquet"


def log(step: str, msg: str):
    print(f"[{step}] {msg}")


def read_out(p: Paths, name: str) -> pd.DataFrame:
    return pd.read_parquet(p.out(name))
