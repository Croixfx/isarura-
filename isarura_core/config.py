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

# Daily energy requirement per adult equivalent (kcal). NISR EICV7 Methodological Note
# (statistics.gov.rw, 2025-04), p.30: poverty line uses 2,400 kcal/adult equivalent/day.
KCAL_PER_ADULT_DAY = 2400

# kcal per kg of the product as the SAS reports it, from data/inputs/kcal_per_kg.csv:
# kcal per 100 g edible x 10 x (1 - waste%) x extra_factor. Source: West, Pepping & Temalilwa (1988),
# as reproduced in FAO (2001) Improving Nutrition through Home Gardening, Appendix 2. Proxies and
# assumptions (rice paddy-to-milled 0.65, cooking banana, wheat, cassava) are in the CSV's note column.
CROPS = ["maize", "beans", "sorghum", "rice", "wheat", "cassava", "irish_potato", "sweet_potato", "cooking_banana"]


def _load_kcal_per_kg() -> dict:
    import csv
    with open(INPUTS / "kcal_per_kg.csv", newline="", encoding="utf-8") as f:
        table = {row["crop"]: float(row["kcal_per_kg_as_produced"]) for row in csv.DictReader(f)}
    missing = [c for c in CROPS if c not in table]
    if missing:
        raise ValueError(f"kcal_per_kg.csv: missing crops {missing}")
    return {c: table[c] for c in CROPS}


KCAL_PER_KG = _load_kcal_per_kg()

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
