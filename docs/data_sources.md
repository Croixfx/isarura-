# Data sources (owner: Croix)

All inputs are NISR unless marked. Accessed 28 Oct 2026.

| Dataset | Used for | Detail | Licence |
|---|---|---|---|
| NISR SAS 2025 microdata (catalog 124, RWA-NISR-SAS-2025-v01) | Loss, harvest, weights | Files per season: `Rwa_raw_Season{A,B,C}2025_Production`, `_Agricultural_practice`, `_Screening`, `Rwa_raw_fertilizer_pesticide{A,B,C}2025`. Latest SAS microdata available. | NISR terms (no redistribution) |
| NISR SAS 2024 microdata (catalog 113) | Loss, harvest, weights | Loss questions s2q39, s2q46-s2q50 confirmed in the 2024 data dictionary | NISR terms |
| NISR SAS 2026 Season A Final Report (updated 28 Apr 2026) | Published production 2026A and 2025A (`data/inputs/published_national.csv`) | Table 6, p.30. District table: Table 15 (also in `Tables_2026 Season A.xlsx`) | Public |
| NISR SAS 2026 Season B Main Report (updated 22 Sep 2026) | Published production 2026B and 2025B | Table 6, p.31. District table: Table 13, p.41 (also in `Tables_2026 Season B.xlsx`) | Public |
| NISR SAS 2025 Annual Tables (`SAS_2025_Annual_Tables.xlsx`) | District production 2025A/B/C (Tables 24-26) and NISR post-harvest loss share (Tables 27-29, "Use of production by farmers"); 2025C national total (Table 26) | `published_district.csv`, `published_loss_share.csv`, `published_national.csv` | Public |
| NISR Tables_2026 Season A (`Tables_2026 Season A.xlsx`) | District production 2026A (Table 15); loss share 2026A (Table 16); 2024 production from the previous-year rows | same | Public |
| NISR Tables_2026 Season B (`Tables_2026 Season B.xlsx`) | District production 2026B (Table 13); loss share 2026B (Table 14); 2024 production from the previous-year rows | same | Public |
| NISR SAS 2025 Annual Report (Final report, summary, INCAMAKE PDFs) | Narrative and cross-checks for the 2025 tables | statistics.gov.rw, SAS Annual Report 2025 page | Public |
| NISR CPI January 2025 report | Food index Jan-24, Dec-24, Jan-25 (`data/inputs/cpi.csv`) | Annexes 1-3, pp.7-9, Feb 2014=100 | CC BY 4.0 |
| NISR CPI September 2026 report | Food index Sep-25, Aug-26, Sep-26 | Annexes 1-3, pp.10-12, Feb 2014=100 | CC BY 4.0 |
| NISR CPI_time_series_September_2026.xls | Full monthly series (optional upgrade of cpi.csv) | 13.8 MB on the CPI September 2026 page | CC BY 4.0 |
| NISR EICV7 2023/24 microdata (catalog 119) | Unit values (prices) | Fieldwork Oct 2023 - Oct 2024 | NISR terms |
| NISR EICV7 Methodological Note (2025-04) | 2,400 kcal/adult equivalent/day (p.30); consumption valued in Jan 2024 national prices (pp.29-30) → price base month | statistics.gov.rw/sites/default/files/documents/2025-04/Methodological Note.pdf | Public |
| kcal per kg by crop | Calorie conversion | **Still FAO placeholders.** Prefer an NISR table if found; else FAO/INFOODS with table and version. Rice: SAS reports paddy. | |
| District boundaries | Map | TODO: NISR geodata first, geoBoundaries fallback | TODO |

## Notes

- **Food inflation:** in September 2026, food prices rose 20.9% in the year in **urban** areas, 27.0% in **rural** areas and 25.2% for all Rwanda (CPI Sept 2026, Annexes 1-3). We use the rural index because the losses are on farms.
- **Price roll-forward:** rural food index Jan-24 236.2 → Sep-26 332.5, factor 1.408.
- **2026 seasons:** NISR has published 2026A and 2026B production, but microdata ends at 2025. The `loss_latest` table applies the 2025 loss rate of the same season to 2026 production, and is labelled as an extrapolation.
- Crop mapping: rice = paddy rice; beans = all beans (bush + climbing, loss share weighted by production); cooking_banana = cooking banana only. Season C covers only sweet potato, Irish potato and beans.
- 2025A and 2025B figures come from the comparison columns of the 2026 reports. If they differ from the SAS 2025 annual report, use the annual report figures for validation and note the revision.
