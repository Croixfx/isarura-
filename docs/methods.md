# Methods (owner: Croix)

The app's Methods page is the main write-up; keep this file in step with it.

1. **Validate.** Weighted production (sum of weight x harvest) by crop and season vs NISR published
   totals. Tolerance: TODO %. Results: `data/public/validation.csv`.
2. **Loss rates.** For crop c, district d, season s, stage k:
   `L = sum(w * loss_k) / sum(w * harvest)` over farms with harvest > 0. Also national rates.
   Code: `isarura_core/estimators.py::loss_rates`.
3. **Uncertainty.** Within each cell, clusters resampled with replacement 200 times; 95% interval from
   the 2.5th/97.5th percentiles. Cells with fewer than `MIN_N` farmers are flagged.
   Limitation: resampling is per cell rather than within design strata.
4. **Stage consistency.** Sum of stage rates vs reported total; the gap is published, not forced to zero.
5. **Tonnes.** Loss rate x NISR published district production (fallback: survey-weighted production,
   flagged in `production_base`).
6. **Prices.** Trimmed EICV7 unit values; district median (national median where a district has
   fewer than 10 observations); 25th/75th percentiles as low/high; rolled forward with the rural CPI
   food index.
7. **Meals.** kcal = tonnes x 1000 x kcal/kg; adult-years = kcal / (daily requirement x 365).
8. **Priority.** Default rank by value lost; scenario: avoidable value = sum over stages of
   value_k x a_k, optionally per franc at a user-entered cost per tonne avoided.
