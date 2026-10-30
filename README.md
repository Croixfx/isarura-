# Isarura

**From harvest to table: where Rwanda's food is lost after harvest, what it is worth today, and where to act first.**

NISR 2026 Big Data Hackathon · Track 1: Agricultural Productivity
Team: Jean De La Croix Niyonkuru and Chadia Ingabire, University of Rwanda

- **Live app:** https://isarura.streamlit.app/
- **Demo Video:** https://drive.google.com/file/d/1ULItxu1M48cKSPklcR2LaRvEaIeUCA2b/view?usp=sharing


---

## The headline

> By NISR's own count, at least **12,300 tonnes** of food were lost after harvest in 2025: about **9.8 billion Rwf** at September 2026 prices (range 8.3 to 11.4 billion), enough to feed **about 32,000 adults for a year**. Rice and beans account for more than half of that value.

The figures are calculated from NISR's own published tables: national production × post-harvest loss share by crop and season (SAS 2025 Annual Tables; SAS 2026 Season A and B tables). Values use EICV7 household food prices, rolled forward with NISR's rural food CPI.

## Why it matters now

- **Food prices are rising fast.** In September 2026, food prices were up **27.0%** on a year earlier in rural areas, and up 10.6% in that month alone (NISR CPI, September 2026). Every tonne lost now costs households more.
- **Reducing post-harvest loss is a national target.** Under NST2, the Fifth Strategic Plan for Agriculture Transformation (PSTA 5, 2024/25 to 2028/29) includes the indicator *"Reduction of post-harvest losses in priority staple crops"*. It has a baseline of **13.8%** and a target of **8% by 2028/29**, under Outcome 2.2, *"Strengthened market linkages and post-harvest infrastructures"*. It plans more silos, drying shelters, mobile dryers and collection centres (PSTA 5 abridged version, pp. 26–27).
- **The measurement gap is large.** Farmers in the Seasonal Agricultural Survey report losing about **0.2%** of production. The PSTA 5 baseline is **13.8%**. The two measure different things: farmer recall at harvest versus losses along the wider chain. Isarura shows both, so planners can see what the survey captures and what it misses.

| If the loss rate is… | Tonnes lost (2025, 9 crops) | Value at Sep 2026 prices | Adult-years of food |
|---|---|---|---|
| **Farmer-reported (SAS, NISR)** | **12,300** | **9.8 bn Rwf** | **32,000** |
| PSTA 5 target 2028/29 (8%) | 493,000 | 265 bn Rwf | 793,000 |
| PSTA 5 baseline (13.8%) | 850,000 | 457 bn Rwf | 1.37 million |

*Rows 2 and 3 are scenarios (labelled **Scenario** on the app's Home page) that apply a single national rate to all nine crops, for scale only.*

## Who it is for

| User | Question | Decision |
|---|---|---|
| MINAGRI and RAB planners | Which crops and districts lose most, and at which stage? | Where to place storage, drying and handling support (PSTA 5 Output 2.2.2) |
| District agriculture officers | How does my district compare? | Local extension and cooperative priorities |
| Cooperatives and agri-SMEs | At which stage does my crop lose most? | Drying, bags, sorting or transport |
| Development partners | Where does an investment save the most food per franc? | Funding allocation |
| NISR | Are the estimates consistent with official totals? | Possible post-harvest indicators by district and stage |

## What the app shows

1. **National picture:** tonnes, value and adult-years of food lost, by season, from NISR's published figures.
2. **Map:** loss by district (SAS microdata detail).
3. **Crop and stage explorer:** where in the chain each crop loses most (transport, storage, processing, packaging, sales).
4. **District profile:** top crops, comparison of stages with the national average, a priority list, and scenario sliders.
5. **Methods:** validation against NISR, sources, assumptions and limits.

Every number is labelled **Official (NISR published)**, **Calculated by Isarura** or **Scenario (user assumption)**. Every table can be downloaded as CSV.

## Data

| Dataset | Producer | Used for |
|---|---|---|
| Seasonal Agricultural Survey 2024 and 2025, microdata (catalogs 113, 124) | NISR | Loss by district, crop and stage; survey weights |
| SAS 2025 Annual Tables; SAS 2026 Season A and B Tables | NISR | Published production (national and district), post-harvest loss share |
| EICV7 2023/24, food purchases module S8B (catalog 119) | NISR | Food prices (value ÷ quantity, purchases in kg) |
| EICV7 Methodological Note | NISR | 2,400 kcal per adult equivalent per day; January 2024 price basis |
| CPI, January 2025 and September 2026 reports | NISR | Rural food index, used to roll prices forward |
| *The composition of foods commonly eaten in East Africa* (West, Pepping & Temalilwa, 1988), via FAO (2001) | FAO / WUR | kcal per kg, net of inedible waste |
| PSTA 5 (MINAGRI, 2024) | MINAGRI | Policy targets and the 13.8% baseline |
| District boundaries | geoBoundaries (ADM2) | Map |

Full details: `docs/data_sources.md`.

## Method in brief

- **Validation first.** Survey-weighted production from the microdata is compared with NISR's published totals, and microdata loss rates with NISR's published loss share. Both comparisons are shown on the Methods page.
- **Loss rates:** weighted ratio Σ(weight × kg lost) ÷ Σ(weight × kg harvested), by crop, district, season and stage, with cluster-bootstrap 95% intervals. Cells with fewer than 10 farmers are flagged.
- **Tonnes** are anchored to NISR's published production.
- **Prices:** median EICV7 purchase price per crop (trimmed to the 5th–95th percentile), rolled forward to September 2026 with the rural food CPI (×1.35, using the 2024 fieldwork-year midpoint as the base).
- **Meals:** tonnes × kcal per kg ÷ (2,400 kcal × 365).
- **No machine learning** is used to produce any estimate.

### Known limits

- Losses are **farmer-reported** and are much lower than the PSTA 5 baseline (see above).
- Prices are **household purchase prices**, not farm-gate prices, so they overstate farmers' loss.
- **Rice:** SAS reports paddy, so the milled price and calorie values are multiplied by 0.65. This is an assumption.
- **Calorie proxies:** cooking banana uses the plantain entry, and wheat uses parboiled wheat.
- **Small samples:** 20% of district cells have fewer than 10 farmers and are greyed out.
- **Validation gaps:** wheat in Season B and sweet potato in Season A fall outside the 5% production tolerance.

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

## Run it

```bash
python -m venv .venv && .venv\Scripts\activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py --synthetic   # optional: demo data, works anywhere (overwrites data/interim)
streamlit run app/Home.py      # the app reads data/public only
pytest -q
```

To rebuild from microdata, request access to NISR catalogs 113, 124 and 119 and place the files in `data/raw/` (never committed). Then run `python run_pipeline.py`. Details: `docs/methods.md`.

## Data protection

No farm-level or household-level data is in this repository or the app; only aggregates are. Microdata is used under NISR's terms on the team's own computers.

## Declarations

- **Original work:** This project is the original work of the team, built for the NISR 2026 Big Data Hackathon (Track 1).
- **Intellectual property:** In line with the competition rules, the team agrees to the transfer of intellectual property rights in this submission to NISR.
- **Team:** Jean De La Croix Niyonkuru and Chadia Ingabire, University of Rwanda.

## Sources

- NISR, Seasonal Agricultural Survey 2025 Annual Report and Tables; SAS 2026 Season A and B: https://statistics.gov.rw
- NISR, CPI September 2026: https://statistics.gov.rw/node/1836
- NISR, EICV7 Methodological Note: https://statistics.gov.rw/sites/default/files/documents/2025-04/Methodological%20Note.pdf
- NISR microdata catalog (SAS 2024, SAS 2025, EICV7): https://microdata.statistics.gov.rw/index.php/catalog/113, /124, /119
- MINAGRI, PSTA 5 abridged version: https://www.minagri.gov.rw/fileadmin/user_upload/Minagri/Publications/Policies_and_strategies/PSTA_5_Abridged_version_Final.pdf
- FAO (2001), *Improving Nutrition through Home Gardening*, Appendix 2: https://www.fao.org/4/x3996e/x3996e44.htm
- geoBoundaries, Rwanda ADM2 district boundaries: https://www.geoboundaries.org/
