# Start here, Chadia

Your job: **get NISR data in, get the app online, make it work on real data.**
Croix handles the statistics (validation, loss rates, prices, Methods page) and the submission.
The full schedule is in `TASKS.md`. This page is the *how*.

Deadline: submit Fri 30 Oct by 15:00. Feature freeze Thu 20:00.
Sync calls: Wed 21:00, Thu 12:00, Thu 20:00, Fri 12:00.

---

## 0. Set up (30 min)

```bash
git clone <repo-url> isarura && cd isarura
python -m venv .venv
.venv\Scripts\activate            # Windows   (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python run_pipeline.py --synthetic
streamlit run app/Home.py
pytest -q
```

You should see the app with a yellow **Demo data** banner, and `19 passed`.
The demo data is fake and only lets us build before the NISR files arrive. Nothing fake is submitted.

**Git rules**
- Work on a branch: `git checkout -b chadia/load-sas`. Push it and open a pull request. Croix merges.
- Only edit your files (table in `TASKS.md`). To change `isarura_core/contracts.py` or `config.py`, ask Croix first.
- **Never commit anything from `data/raw/` or `data/interim/`.** NISR's licence forbids it. `.gitignore` blocks it, but check `git status` before every commit.

---

## 1. Get the SAS microdata (today, first thing)

1. Go to microdata.statistics.gov.rw. Register or log in.
2. Request **Seasonal Agricultural Survey 2025** (catalog 124) and **2024** (catalog 113). Choose the Stata (.dta) format if offered.
3. Unzip into `data/raw/sas_2025/` and `data/raw/sas_2024/`.
4. **If approval is not instant, message Croix right away with how long it says.** That decides whether we switch to the fallback plan.

## 2. Find the variables (1-2 hours)

Open the files and find the crop-level file (one row per farm × crop × season):

```python
import pandas as pd, pyreadstat, glob
for f in glob.glob("data/raw/sas_2024/*.dta"):
    df, meta = pyreadstat.read_dta(f, metadataonly=True)
    print(f, len(meta.column_names))
    for name, label in zip(meta.column_names, meta.column_labels):
        print("   ", name, "|", label)
```

Look for: `s2q21`/`s2q22` (harvest), `s2q37` (storage type), `s2q39` (total loss),
`s2q46`-`s2q50` (loss by stage), plus the farm ID, cluster/enumeration area, stratum,
weight, district, season and crop columns.

Then:
1. Fill the table in `docs/variable_map.md`.
2. Fill `VARIABLE_MAP` in `pipeline/step01_load_sas.py` (2024 block, then copy for 2025).
   If a variable does not exist in a year, write `None`. Never guess.
3. See the crop and district labels:
   ```python
   df = pd.read_stata("data/raw/sas_2024/<file>.dta")
   print(df["<crop column>"].value_counts())
   print(df["<district column>"].value_counts())
   ```
   Fill `CROP_CODES` so the names match `config.CROPS` (e.g. `"Irish potato": "irish_potato"`).
   Fill `DISTRICT_CODES` only if names don't already match `config.DISTRICT_LIST` after `.title()`.
4. Check the units are kg. If not, tell Croix.

## 3. Run the loader

```bash
python run_pipeline.py --only 1
```

Read the log: rows in, rows dropped and why. If more than ~10% are dropped, find out why before moving on.
When it passes, **send `data/interim/crop_records.parquet` to Croix privately** (Google Drive,
shared only with Croix). Not GitHub, not WhatsApp groups.

## 4. Deploy the demo app (today)

1. Push `main` to GitHub (the demo `data/public/` files are committed, so the app has data).
2. Go to share.streamlit.io, sign in with GitHub, create an app from our repo.
   Main file path: `app/Home.py`. Python 3.12.
3. Open the URL in a private window and on your phone. Send the link to Croix.

Do this today so any hosting problem shows up now, not on Friday.

---

## 5. Thursday: real map, real data, phone check

**District boundaries.** Prefer NISR's geodata portal. Fallback: geoBoundaries, Rwanda ADM2.
```python
import geopandas as gpd
g = gpd.read_file("path/to/districts.shp")      # or .geojson
g["district"] = g["<name column>"].str.title()  # must match config.DISTRICT_LIST exactly
g = g[["district", "geometry"]].to_crs(4326)
g["geometry"] = g.simplify(0.002)
g.to_file("data/public/districts.geojson", driver="GeoJSON")
```
(`pip install geopandas` just for this; it is not needed by the app.)
Keep it under 300 KB. Run `pytest -q` (it checks all 30 districts are there).
If districts fill the whole map instead of their shape, the polygon direction is reversed:
`from shapely.geometry.polygon import orient; g["geometry"] = g.geometry.apply(lambda p: orient(p, -1))`
(for MultiPolygons, orient each part).

**Real data.** When Croix pushes real `data/public/*.csv`, the demo banner disappears.
Go through every page and check:
- Home: three headline numbers show, stage bar and crop table fill.
- Map: every metric works; clicking a district opens its profile.
- Crop and stage: heatmap greys small-sample cells; CSV downloads open.
- District profile: sliders change the priority list.

**Phone and speed.** Chrome DevTools → device toolbar → 360 px wide. Fix anything cut off.
DevTools → Network → "Fast 4G": first page should load in under 3 seconds.

**One user test.** Ask a classmate to find their home district. Time it (target under 30 s).
Write down what confused them and fix the easy things.

## 6. Friday (until 15:00)

1. **Backup host:** create a Hugging Face Space (Streamlit SDK) from the same repo. Put both URLs in the README.
2. **Fresh-clone test:** clone into a new folder, then `pip install -r requirements.txt`, `pytest -q`, `streamlit run app/Home.py`.
3. **Privacy sweep:** `git ls-files | findstr /i ".dta .sav"` (Windows) must return nothing.
4. Fix anything Croix reports. Open both URLs on two devices in private windows.

---

## Where things are

| Path | What |
|---|---|
| `pipeline/step01_load_sas.py` | **Yours.** Reads NISR files → `crop_records` |
| `pipeline/step08_export.py` | **Yours.** Writes `data/public/` + privacy checks |
| `app/` | **Yours** (except the Methods page). One file per page |
| `isarura_core/contracts.py` | The agreed columns of every table. Ask before changing |
| `isarura_core/config.py` | District names, crop names, constants |

**If stuck for more than 30 minutes, message Croix.** Two days is too short to be stuck alone.
