# Isarura: who builds what (remote split)

Deadline: **Fri 30 Oct, submit by 15:00** (portal closes 23:59).
Feature freeze: **Thu 29 Oct, 20:00**.

## How the split works

The repo already runs end to end on **synthetic data** (`python run_pipeline.py --synthetic`, then
`streamlit run app/Home.py`). So nobody waits for anybody: you each replace one side of a
working system.

```
 data/raw (NISR files, private)
        │  step01  ← Chadia
        ▼
 data/interim/crop_records.parquet  ── contract: isarura_core/contracts.py
        │  step02-06 + isarura_core/*  ← Croix (statistics)
        ▼
 data/public/*.csv  ── contract: isarura_core/contracts.py
        │  step08 export + app pages + deploy  ← Chadia
        ▼
 Public Streamlit app
```

The two hand-off points are the **contracts** in `isarura_core/contracts.py`. If you need a new
column, add it there in a PR the other person approves. Everything else you own, you change freely.

## File ownership (avoid merge conflicts)

| Owner | Files |
|---|---|
| **Chadia** | `pipeline/step01_load_sas.py`, `pipeline/step08_export.py`, `docs/variable_map.md`, `data/public/districts.geojson`, `app/Home.py` (layout), `app/pages/1_Map.py`, `app/pages/2_Crop_and_stage.py`, `app/pages/3_District_profile.py` (layout), `app/common.py`, `.streamlit/`, `.github/` |
| **Croix** | `isarura_core/*`, `pipeline/step02`-`step06`, `data/inputs/*`, `app/pages/4_Methods.py`, scenario block in `3_District_profile.py`, `README.md`, `docs/methods.md`, `docs/data_sources.md`, `demo/` |
| Shared (PR + review) | `isarura_core/contracts.py`, `isarura_core/config.py`, `requirements.txt` |

Git: work on `chadia/<thing>` or `croix/<thing>` branches, open a PR, the other person merges
within an hour. Small PRs. Never commit anything from `data/raw` or `data/interim`.

**Microdata sharing:** the raw files and `crop_records.parquet` cannot go on GitHub. Chadia shares
`crop_records.parquet` with Croix privately (Google Drive, restricted to the two of you), or both
download from the NISR catalog with your own accounts.

---

## Chadia: data in, app out, deployment

### Wed 28 Oct (today)
- [ ] **H1. Gate 1 and 2.** Log in to microdata.statistics.gov.rw, request SAS 2025 (catalog 124) and
      SAS 2024 (113). Note approval time and tell Croix immediately if access is blocked (then we
      switch to the fallback in the plan, section 9).
- [ ] **H2. Fill the variable map.** Open the crop-level `.dta` file, fill `VARIABLE_MAP`,
      `CROP_CODES`, `DISTRICT_CODES` in `step01_load_sas.py` and the worksheet in
      `docs/variable_map.md`. Key question: which of `s2q21`/`s2q22` is the crop-level harvest,
      and are `s2q46`-`s2q50` present in 2025.
- [ ] **H3. Run step 01 on real data** (`python run_pipeline.py --only 1`). Read the data-quality
      log. Send `crop_records.parquet` to Croix privately. **Exit check: file passes the contract.**
- [ ] **H4. Deploy the demo app now** on Streamlit Community Cloud (main file `app/Home.py`).
      Share the URL. Deploying early means hosting surprises happen today, not Friday.

### Thu 29 Oct
- [ ] **H5. Real district map.** Replace `data/public/districts.geojson` with simplified real
      boundaries (NISR geodata, backup geoBoundaries RWA ADM2). Property `district` must match
      `config.DISTRICT_LIST` spelling. If districts fill the whole map instead of their shape, the
      polygon winding is reversed: rewind them (e.g. `geojson-rewind`, or `shapely.geometry.polygon.orient(p, -1)`).
      Keep the file under 300 KB. Run `pytest -q`.
- [ ] **H6. App pages 1-4 on real data.** When Croix pushes real `data/public/*.csv`, check every
      page: headline numbers, map click opens the district, heatmap greys small cells, CSV buttons work.
- [ ] **H7. Mobile and speed.** Open every page at 360 px width (Chrome dev tools) and on a phone;
      fix anything that overflows. First page under 3 s on throttled 4G.
- [ ] **H8. Usability test.** One classmate finds their district in under 30 s. Note what confused them.

### Fri 30 Oct (until 15:00)
- [ ] **H9. Backup host** on Hugging Face Spaces (Streamlit SDK). Put both URLs in the README.
- [ ] **H10. Fresh-clone test** on a clean folder: `pip install -r requirements.txt`, `pytest -q`,
      `streamlit run app/Home.py`. Search the repo for `.dta`, `.sav`, farm IDs.
- [ ] **H11. Fix defects** Croix reports. Open both URLs in a private window on two devices.

Stretch (only if all above is done): Kinyarwanda headline labels (FR-15).

---

## Croix: statistics, validation, story, submission

### Wed 28 Oct (today)
- [x] **C1. Gate 3 inputs.** (done for 2025A/B and 2026A/B; still to add: 2025C, and 2024 seasons if using SAS 2024; district table from Tables 15 and 13) From the SAS 2025 annual report, type national production by crop and
      season into `data/inputs/published_national.csv` (header already there; put the table number
      in `source`). Do the district table too if the report has it (`published_district.csv`).
- [x] **C2. CPI.** (typed from NISR CPI reports into `data/inputs/cpi.csv`; xls upgrade optional) Download `CPI_time_series_September_2026.xls`, write `cpi_from_xls()` in
      `step04_prices_cpi.py` (needs `xlrd`), output `data/inputs/cpi.csv` (month `YYYY-MM`, area,
      food_index).
- [ ] **C3. Validate** as soon as Chadia sends `crop_records.parquet`:
      `python run_pipeline.py --only 2`. If most totals miss, stop and fix weights / crop codes /
      season codes with Chadia before anything else. Then set `VALIDATION_TOLERANCE_PCT` in `config.py`.
      **Exit check: validation table exists (FR-01, FR-02).**

### Thu 29 Oct
- [ ] **C4. Loss rates on real data** (`--only 3`). Look at `stage_consistency`; decide `MIN_N`.
- [ ] **C5. Prices.** Download EICV7, write `load_eicv7_unit_values()` (crop, district,
      value/quantity per item), confirm `EICV7_BASE_MONTH`. Run `--only 4 5 6`.
- [ ] **C6. Replace placeholders** in `config.py`: `KCAL_PER_KG` from FAO/INFOODS (cite table and
      version), `KCAL_PER_ADULT_DAY` from the EICV7 poverty methodology note.
- [ ] **C7. Publish real aggregates:** `python run_pipeline.py --only 8` then commit `data/public/`.
      The demo banner disappears automatically (`meta.json` → `demo: false`). Tell Chadia.
- [ ] **C8. Methods page and README:** sources with links, NST2 / Vision 2050 exact quote,
      originality, AI-use and IP-transfer declarations (fill every TODO in `4_Methods.py` and README).

### Fri 30 Oct (until 15:00)
- [ ] **C9. Numbers check:** every headline number on the app matches `data/public`; every number has
      its official / calculated / scenario label.
- [ ] **C10. Demo video** under 3 minutes (OBS): National → Map → one district → priority slider →
      Methods validation table.
- [ ] **C11. Submit** the form: repo link, app link, backup link, video. Tag `v1.0-submission`.

---

## Sync points (15-minute calls)

| When | Check |
|---|---|
| Wed 21:00 | Microdata access? Variable map filled? Demo URL live? |
| Thu 12:00 | Validation table result. Real `data/public` ready? |
| Thu 20:00 | **Feature freeze.** Only fixes after this. |
| Fri 12:00 | Fresh-clone test passed, video recorded, final read-through. |

## If you fall behind, cut in this order
1. Driver model and rainfall layer (not built; mention as planned work)
2. Scenario sliders (keep the default priority table)
3. Bootstrap intervals (`--boot 0`; keep sample sizes and small-n flags)
4. Kinyarwanda labels

Never cut: validation table, stage split, value and meals, Methods page, declarations, public URL.
