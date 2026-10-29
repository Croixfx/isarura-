# Isarura

**From harvest to table: where Rwanda's food is lost, what it is worth today, and where to act first.**

NISR 2026 Big Data Hackathon, Track 1: Agricultural Productivity.
Team: NIYONKURU Jean De La Croix, Chadia.

> **Status:** the app runs on real data. The national headline is NISR's published production x NISR's
> published post-harvest loss share (2025A to 2026B). District and stage detail comes from the SAS 2024-2025
> microdata, which reproduces NISR production within 5% for 27 of 42 crop-season pairs (see the Methods page).
> Prices are EICV7 household purchase prices rolled forward with the NISR rural food CPI.

- Live app: not deployed yet (to be added before submission)
- Backup: not deployed yet
- Demo video: not recorded yet

## Why now

NISR's September 2026 CPI shows food prices up **27.0%** in the year in rural areas (20.9% urban, 25.2%
nationally), and rural food prices rose **10.6%** in September alone. Every tonne of food lost after
harvest is worth more than it was a year ago.

## What it does

Isarura estimates post-harvest loss by crop, district, season and stage (transport, storage,
processing, packaging, sales) from the Seasonal Agricultural Survey, converts it to Rwf at current
prices and to adult-years of food, and ranks district-and-crop pairs for storage, drying and
handling investment.

Users: MINAGRI and RAB planners, district agriculture officers, cooperatives, development partners.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_pipeline.py --synthetic     # demo data, works anywhere
streamlit run app/Home.py
pytest -q
```

With NISR access: put SAS files in `data/raw/`, fill `data/inputs/`, then `python run_pipeline.py`.

## Repository

| Folder | Contents |
|---|---|
| `isarura_core/` | Config, data contracts, estimators, conversions, priority index |
| `pipeline/` | Numbered steps; `run_pipeline.py` runs them all |
| `app/` | Streamlit app (reads only `data/public`) |
| `data/public/` | Aggregates published with the app |
| `data/inputs/` | Small tables typed from NISR publications |
| `data/raw/`, `data/interim/` | Microdata and private intermediates. **Never committed.** |
| `tests/` | Math and contract tests |
| `docs/` | Variable map, data sources, methods |

## Method in brief

Design-based estimation with NISR survey weights; reconciliation with NISR published production;
extrapolation of the latest 2025 loss rates to NISR's published 2026 seasons (labelled as such);
prices from EICV7 unit values rolled forward with the NISR rural food CPI; 2,400 kcal per adult per day
(EICV7 Methodological Note);
cluster-bootstrap 95% intervals; small-sample flags (fewer than 10 farmers). Machine learning is not
used to produce any estimate. Details on the app's Methods page and in `docs/methods.md`.

## National alignment

TODO: exact NST2 (2024-2029) and Vision 2050 wording, with page references.

## Data use

No farm- or household-level data is in this repository or the app. Microdata is used under NISR's
terms on the team's machines only.

## Declarations

- **Original work:** TODO (Croix to confirm: the team's own design and code, built for this hackathon)
- **AI use:** Claude Code (Anthropic) was used as a coding assistant for scaffolding, refactoring, tests and
  documentation. The team chose the methods and sources and checked the numbers. No machine-learning
  model produces any estimate.
- **Intellectual property:** TODO (transfer to NISR per competition rules; check the rules text)
- **Sources:** see `docs/data_sources.md`
