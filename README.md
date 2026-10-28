# Isarura

**From harvest to table: where Rwanda's food is lost, what it is worth today, and where to act first.**

NISR 2026 Big Data Hackathon, Track 1: Agricultural Productivity.
Team: NIYONKURU Jean De La Croix, Chadia.

> **Status:** the app currently shows **synthetic demo data** while the NISR microdata pipeline is
> being connected. A banner in the app says so. See [TASKS.md](TASKS.md).

- Live app: TODO
- Backup: TODO
- Demo video: TODO

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
cluster-bootstrap 95% intervals; small-sample flags (fewer than 10 farmers). Machine learning is not
used to produce any estimate. Details on the app's Methods page and in `docs/methods.md`.

## National alignment

TODO: exact NST2 (2024-2029) and Vision 2050 wording, with page references.

## Data use

No farm- or household-level data is in this repository or the app. Microdata is used under NISR's
terms on the team's machines only.

## Declarations

- **Original work:** TODO
- **AI use:** TODO (which tools, for what)
- **Intellectual property:** TODO (transfer to NISR per competition rules)
- **Sources:** see `docs/data_sources.md`
