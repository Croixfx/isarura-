# Variable discovery worksheet (owner: Chadia)

# Variable Map

Fill one column per year from the actual files. If a variable is missing in a year, write
"missing" and set it to `None` in `pipeline/step01_load_sas.py`. Do not guess.

| Concept                         | SAS 2024 (dictionary)  | SAS 2024 (confirmed in file)                      | SAS 2025                                |
| ------------------------------- | ---------------------- | ------------------------------------------------- | --------------------------------------- |
| Crop-level file name            | ?                      | `Rwa_raw_SeasonA2024_Production.dta`              | `Rwa_raw_SeasonA2025_Production.dta`    |
| Farm / household id             | ?                      | `s1q6`                                            | `s1q6`                                  |
| Cluster (enumeration area)      | ?                      | `s1q4`                                            | `s1q4`                                  |
| Stratum                         | ?                      | `s1q3`                                            | `s1q3`                                  |
| Weight                          | ?                      | `plot_weight`                                     | `plot_weight`                           |
| District                        | ?                      | `s1q2`                                            | `s1q2`                                  |
| Season (A/B/C)                  | ?                      | Hardcoded (from file name)                        | Hardcoded (from file name)              |
| Crop                            | ?                      | `s2q4`                                            | `s2q4`                                  |
| Harvest quantity (crop total)   | s2q21 / s2q22 (which?) | `s2q22` (Total quantity of harvest for this crop) | `s2q22`                                 |
| Storage facility type           | s2q37                  | `s2q37`                                           | `s2q37`                                 |
| Quantity in public storage (kg) | s2q38                  | `s2q38` (not loaded)                              | `s2q37_public`                          |
| Total loss (kg)                 | s2q39                  | `s2q39`                                           | **missing** (NISR removed this in 2025) |
| Loss in transport (kg)          | s2q46                  | `s2q46`                                           | `s2q46`                                 |
| Loss in storage (kg)            | s2q47                  | `s2q47`                                           | `s2q47`                                 |
| Loss in processing (kg)         | s2q48                  | `s2q48`                                           | `s2q48`                                 |
| Loss in packaging (kg)          | s2q49                  | `s2q49`                                           | `s2q49`                                 |
| Loss at sales (kg)              | s2q50                  | `s2q50`                                           | `s2q50`                                 |

## Corrections after checking against NISR published production (29 Oct 2026)

The first mapping gave weighted production 2 to 4 times NISR's. Reading the raw files (all six Production
files: seasons A, B, C of 2024 and 2025) showed:

| Concept | Earlier mapping | Correct | Why |
|---|---|---|---|
| Farm id | `s1q6` | `Segment_ID` + `s1q6` | `s1q6` is only a number inside the segment (61 values); with the segment there are about 42,000 farms |
| Cluster | `s1q4` (78 values) | `Segment_ID` (the sampling segment) | `s1q4` is a segment number within a district-level code, not unique |
| Harvest | `s2q22` | **`s2q21`** (plot harvest) | `s2q22` is the farm's total for the crop, repeated on every plot row; `plot_weight` expands one plot |
| Losses (`s2q39`, `s2q46`-`s2q50`) | summed over plot rows | shared across the farm's plots in proportion to plot harvest | also reported once per farm and crop and repeated on every plot row |
| Rice | `Rice` | `Paddy rice` | the SAS label; rice was never matched |
| Cooking banana | `Banana for beer` | `Cooking banana` | "Banana for beer" is a different category |
| Seasons | A only | A, B and C of 2024 and 2025 | |
| Weight in 2025 C | `plot_weight` | `Plot_weight` | capitalised in that file |

Result: weighted production is within 5% of NISR for 27 of 42 crop-season pairs (median difference 4.0%).
Rice matches within 0.5%. Largest gaps: wheat season B (-36%, -39%), sweet potato season A (-23%, -29%).

Data cleaning in step 01: negative loss values and loss totals larger than the harvest are set to missing
(harvest kept), and counted per season in the log. SAS 2025 A and B have no total-loss question, so the
total is the sum of the five stage losses (in 2024 `s2q39` equals that sum).

Units: confirm all quantities are kg. If some are in other units, note the conversion here.
**Confirmed:** Harvest (`s2q22`) and all loss stages (`s2q39`, `s2q46`-`s2q50`) are explicitly labeled as "(in Kg)" or "(kg)" in the NISR variable descriptions.
