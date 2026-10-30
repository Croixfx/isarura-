"""Shared app helpers: data loading (aggregates only), labels, formatting, filters."""
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from isarura_core.config import (LABEL_CALCULATED, LABEL_OFFICIAL, LABEL_SCENARIO,  # noqa: E402
                                 PUBLIC, STAGES)

# Okabe-Ito: colour-blind safe, one colour per stage
STAGE_COLORS = dict(zip(STAGES, ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00"]))
CROP_LABEL = {"maize": "Maize", "beans": "Beans", "sorghum": "Sorghum", "rice": "Rice", "wheat": "Wheat",
              "cassava": "Cassava", "irish_potato": "Irish potato", "sweet_potato": "Sweet potato",
              "cooking_banana": "Cooking banana"}
BADGE = {"official": f":blue-badge[{LABEL_OFFICIAL}]",
         "calculated": f":green-badge[{LABEL_CALCULATED}]",
         "scenario": f":orange-badge[{LABEL_SCENARIO}]"}


# Phones (360px): side-by-side columns stack at full width instead of shrinking; charts never overflow.
NARROW_CSS = """<style>
@media (max-width: 640px) {
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 100% !important; flex: 1 1 100% !important; }
  [data-testid="stMainBlockContainer"] { padding-left: 1rem; padding-right: 1rem; }
  .js-plotly-plot, .plotly, .stPlotlyChart { max-width: 100% !important; }
}
</style>"""


def setup(title: str):
    st.set_page_config(page_title=f"{title} | Isarura", layout="wide")
    import nisr_theme; nisr_theme.apply()  # NISR look: logo, ISARURA wordmark, banner, cards. Keep this line.
    st.markdown(NARROW_CSS, unsafe_allow_html=True)
    meta = load_meta()
    if meta.get("demo"):
        st.warning("**Demo data.** These numbers are synthetic, generated to build the app. "
                   "They are not NISR statistics.", icon="⚠️")
    return meta


@st.cache_data
def load_meta() -> dict:
    return json.loads((PUBLIC / "meta.json").read_text())


@st.cache_data
def load(name: str) -> pd.DataFrame:
    return pd.read_csv(PUBLIC / f"{name}.csv")


@st.cache_data
def geojson() -> dict:
    return json.loads((PUBLIC / "districts.geojson").read_text())


def season_filter(meta: dict, key: str = "seasons") -> list:
    seasons = meta["seasons"]
    latest_year = seasons[-1][:4]
    default = [s for s in seasons if s.startswith(latest_year)]
    picked = st.sidebar.multiselect("Seasons", seasons, default=st.session_state.get(key, default), key=key)
    st.sidebar.caption("Season A: Sep-Feb, B: Mar-Jun, C: Jul-Sep. Totals add up across the seasons you pick.")
    return picked or default


DETAIL_CAPTION = "District and stage detail from SAS microdata; NISR publishes national figures only."


def prices_ready(meta: dict) -> bool:
    """Rwf values need EICV7 prices; until then value columns are empty and the app shows tonnes."""
    return bool(meta.get("prices_available", True))


def rwf(x: float) -> str:
    if pd.isna(x):
        return "n/a"
    if abs(x) >= 1e9:
        return f"{x/1e9:,.1f} bn Rwf"
    if abs(x) >= 1e6:
        return f"{x/1e6:,.0f} m Rwf"
    return f"{x:,.0f} Rwf"


def tonnes(x: float) -> str:
    if pd.isna(x):
        return "n/a"
    return f"{x:,.0f} t"


def crop_name(c: str) -> str:
    return CROP_LABEL.get(c, c)


def download(df: pd.DataFrame, name: str, label: str = "Download CSV"):
    st.download_button(label, df.to_csv(index=False).encode(), file_name=f"isarura_{name}.csv",
                       mime="text/csv", key=f"dl_{name}")
