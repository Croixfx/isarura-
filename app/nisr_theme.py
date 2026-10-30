"""Isarura look and feel, aligned with the NISR website (statistics.gov.rw).

Presentation only: this file never reads data, computes numbers or changes text.
Turn it on with one line in common.setup(), right after st.set_page_config:

    import nisr_theme; nisr_theme.apply()

Delete that line to switch it off again.
"""
import sys
from pathlib import Path

import streamlit as st

_ASSETS = Path(__file__).resolve().parent / "assets"

# NISR palette (from the statistics.gov.rw theme)
NAVY = "#0D2343"      # headings
BODY = "#37404D"      # body text
BLUE = "#2258A9"      # buttons, links, active items
BLUE_DARK = "#143465" # hover
BRAND = "#005CAB"     # brand panels
PANEL = "#E6E9EB"     # grey panels
PAGE = "#EEF1F4"      # page background behind the white cards
LINE = "#DCE1E6"

# Chart colours (colour-blind validated). Same order as config.toml.
CATEGORICAL = ["#2258A9", "#C95100", "#008C7E", "#855CD7", "#CE3936"]

_CSS = f"""
<style>
/* ---------- page: grey canvas, white content blocks (like NISR panels) ---------- */
.stApp, [data-testid="stMain"] {{ background: {PAGE}; }}
.block-container {{ max-width: 1200px; padding-top: 0 !important; padding-bottom: 4rem; }}

/* top bar: plain white strip with a hairline, like the NISR header */
header[data-testid="stHeader"] {{
  background: #FFFFFF;
  border-bottom: 1px solid {LINE};
}}

/* ---------- page title sits in a NISR-style grey banner ---------- */
[data-testid="stHeading"]:has(h1) {{
  position: relative;
  z-index: 0;
  padding: 4.2rem 0 1.4rem;
  margin-bottom: .6rem;
}}
[data-testid="stHeading"]:has(h1)::before {{
  content: "";
  position: absolute;
  z-index: -1;
  top: 0; bottom: 0;
  left: -100vw; right: -100vw;
  background:
    linear-gradient(118deg, transparent 0 58%, rgba(255,255,255,.55) 58% 58.4%, transparent 58.4% 100%),
    linear-gradient(118deg, transparent 0 66%, rgba(255,255,255,.45) 66% 67.2%, transparent 67.2% 100%),
    linear-gradient(118deg, transparent 0 78%, rgba(255,255,255,.35) 78% 78.3%, transparent 78.3% 100%),
    linear-gradient(90deg, #E2E6EA 0%, #EEF1F4 55%, #F7F8FA 100%);
  border-bottom: 1px solid {LINE};
}}
h1 {{
  color: {NAVY} !important;
  font-weight: 700 !important;
  letter-spacing: -0.015em;
  line-height: 1.12 !important;
  font-size: clamp(1.9rem, 3.6vw, 2.75rem) !important;
}}
/* small breadcrumb-style line above every page title */
h1::before {{
  content: "Isarura  \\203A  Post-harvest loss in Rwanda";
  display: block;
  white-space: pre;
  font-size: .82rem;
  font-weight: 500;
  letter-spacing: 0;
  color: {BLUE};
  margin-bottom: .7rem;
}}
h2, h3 {{ color: {NAVY} !important; font-weight: 600 !important; letter-spacing: -0.005em; }}
p, li {{ color: {BODY}; }}

/* ---------- headline numbers: white cards with a blue top rule ---------- */
div[data-testid="stColumn"]:has(> div [data-testid="stMetric"]) {{
  background: #FFFFFF;
  border: 1px solid {LINE};
  border-top: 3px solid {BLUE};
  border-radius: 8px;
  padding: 16px 18px 12px;
  box-shadow: 0 1px 2px rgba(13, 35, 67, .05);
}}
[data-testid="stMetricLabel"] p {{
  color: {BODY} !important;
  font-weight: 500 !important;
  font-size: .86rem !important;
}}
[data-testid="stMetricValue"] {{
  color: {NAVY} !important;
  font-weight: 600 !important;
  letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums;
}}
div[data-testid="stColumn"]:has(> div [data-testid="stMetric"]) [data-testid="stCaptionContainer"] {{
  font-size: .8rem;
  line-height: 1.45;
}}

/* ---------- charts and tables as white panels ---------- */
[data-testid="stPlotlyChart"] {{
  background: #FFFFFF;
  border: 1px solid {LINE};
  border-radius: 8px;
}}
[data-testid="stDataFrame"], [data-testid="stTable"] {{
  border: 1px solid {LINE};
  border-radius: 8px;
  overflow: hidden;
}}

/* ---------- buttons: solid NISR blue, squared like the NISR site ---------- */
.stDownloadButton button, .stButton button {{
  background: {BLUE} !important;
  color: #FFFFFF !important;
  border: 1px solid {BLUE} !important;
  border-radius: 4px !important;
  font-weight: 500 !important;
}}
.stDownloadButton button:hover, .stButton button:hover {{
  background: {BLUE_DARK} !important;
  border-color: {BLUE_DARK} !important;
}}
.stDownloadButton button p, .stButton button p {{ color: #FFFFFF !important; }}

[data-testid="stAlert"] {{ border-radius: 6px; }}
hr {{ border-color: {LINE} !important; }}

/* ---------- sidebar: white, logo + name, blue active item ---------- */
section[data-testid="stSidebar"] {{ border-right: 1px solid {LINE}; }}
[data-testid="stSidebarHeader"] {{ align-items: center; }}
[data-testid="stSidebarHeader"] > div:has(> img.stLogo),
[data-testid="stSidebarHeader"] > a:has(> img.stLogo),
[data-testid="stSidebarHeader"] > div:has(> a > img.stLogo) {{
  display: flex; align-items: center; gap: .65rem;
}}
img.stLogo {{ height: 2.4rem !important; width: auto; }}
[data-testid="stSidebarHeader"] > div:has(> img.stLogo)::after,
[data-testid="stSidebarHeader"] > a:has(> img.stLogo)::after,
[data-testid="stSidebarHeader"] > div:has(> a > img.stLogo)::after {{
  content: "Isarura";
  font-family: "Lexend", sans-serif;
  font-weight: 700;
  font-size: 1.35rem;
  color: {NAVY};
  letter-spacing: -0.01em;
}}
[data-testid="stSidebarNav"] a {{ border-radius: 6px; }}
[data-testid="stSidebarNav"] a span {{ color: {BODY}; font-weight: 500; }}
[data-testid="stSidebarNav"] a:hover {{ background: #EAF1FA; }}
[data-testid="stSidebarNav"] a[aria-current="page"] {{ background: {BLUE} !important; }}
[data-testid="stSidebarNav"] a span p {{ color: {BODY}; font-weight: 500; }}
[data-testid="stSidebarNav"] a[aria-current="page"] span,
[data-testid="stSidebarNav"] a[aria-current="page"] p {{ color: #FFFFFF !important; font-weight: 600 !important; }}

/* ---------- phones ---------- */
@media (max-width: 640px) {{
  .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
  [data-testid="stHeading"]:has(h1) {{ padding-top: 3.4rem; }}
  h1::before {{ font-size: .75rem; }}
}}
</style>
"""


def apply():
    """Apply the NISR-aligned look. Safe: any failure leaves the page unstyled, never broken."""
    try:
        st.logo(str(_ASSETS / "isarura_mark.svg"), size="large",
                icon_image=str(_ASSETS / "isarura_mark.svg"))
    except Exception:
        pass
    st.markdown(_CSS, unsafe_allow_html=True)
    # Recolour the stage chart without editing common.py: update its colour dict in place.
    try:
        common = sys.modules.get("common")
        if common is not None and hasattr(common, "STAGE_COLORS"):
            stages = list(common.STAGE_COLORS)
            common.STAGE_COLORS.update(dict(zip(stages, CATEGORICAL)))
    except Exception:
        pass
