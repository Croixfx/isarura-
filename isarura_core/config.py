"""Shared constants and paths. Both teammates import from here; change values here only."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"            # NISR microdata. NEVER committed.
INPUTS = ROOT / "data" / "inputs"      # Small hand-built tables from published reports (committable).
INTERIM = ROOT / "data" / "interim"    # Private intermediate files. NEVER committed.
PUBLIC = ROOT / "data" / "public"      # Aggregates the app reads. Committed.

# Loss stages available in the SAS 2024 dictionary (s2q46-s2q50).
# The plan mentions a "harvest" stage, but no harvest-stage loss question exists in the
# dictionary, so we do not invent one. "total" comes from s2q39.
STAGES = ["transport", "storage", "processing", "packaging", "sales"]
ALL_STAGES = STAGES + ["total"]

# Suppression / flagging threshold: cells built on fewer farmers than this are flagged
# (shown greyed in the app). State this number in README and Methods.
MIN_N = 10

# Cluster bootstrap replicates for 95% intervals.
N_BOOT = 200
SEED = 2026

# Reconciliation tolerance vs NISR published totals (percent). Set after first comparison.
VALIDATION_TOLERANCE_PCT = 5.0

# Daily energy requirement per adult equivalent (kcal). CONFIRM against the EICV7
# poverty-line methodology note and cite it; it is editable in the app.
KCAL_PER_ADULT_DAY = 2500

# kcal per kg of the edible product as harvested. PLACEHOLDER values: replace with
# FAO/INFOODS figures, and record table name and version in docs/data_sources.md.
KCAL_PER_KG = {
    "maize": 3650,
    "beans": 3410,
    "sorghum": 3390,
    "rice": 3600,
    "wheat": 3400,
    "cassava": 1600,
    "irish_potato": 770,
    "sweet_potato": 860,
    "cooking_banana": 1220,
}
CROPS = list(KCAL_PER_KG)

DISTRICTS = {
    "Kigali": ["Gasabo", "Kicukiro", "Nyarugenge"],
    "Eastern": ["Bugesera", "Gatsibo", "Kayonza", "Kirehe", "Ngoma", "Nyagatare", "Rwamagana"],
    "Northern": ["Burera", "Gakenke", "Gicumbi", "Musanze", "Rulindo"],
    "Southern": ["Gisagara", "Huye", "Kamonyi", "Muhanga", "Nyamagabe", "Nyanza", "Nyaruguru", "Ruhango"],
    "Western": ["Karongi", "Ngororero", "Nyabihu", "Nyamasheke", "Rubavu", "Rusizi", "Rutsiro"],
}
DISTRICT_LIST = [d for ds in DISTRICTS.values() for d in ds]
PROVINCE_OF = {d: p for p, ds in DISTRICTS.items() for d in ds}

# Every number in the app carries one of these labels (NFR: Transparency).
LABEL_OFFICIAL = "Official (NISR published)"
LABEL_CALCULATED = "Calculated by Isarura"
LABEL_SCENARIO = "Scenario (user assumption)"
