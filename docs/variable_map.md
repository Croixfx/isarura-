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

Units: confirm all quantities are kg. If some are in other units, note the conversion here.
**Confirmed:** Harvest (`s2q22`) and all loss stages (`s2q39`, `s2q46`-`s2q50`) are explicitly labeled as "(in Kg)" or "(kg)" in the NISR variable descriptions.
