# Data sources (owner: Croix)

All inputs are NISR unless marked. Accessed 28 Oct 2026.

| Dataset | Used for | Detail | Licence |
|---|---|---|---|
| NISR SAS 2025 microdata (catalog 124, RWA-NISR-SAS-2025-v01) | Loss, harvest, weights | Files per season: `Rwa_raw_Season{A,B,C}2025_Production`, `_Agricultural_practice`, `_Screening`, `Rwa_raw_fertilizer_pesticide{A,B,C}2025`. Latest SAS microdata available. | NISR terms (no redistribution) |
| NISR SAS 2024 microdata (catalog 113) | Loss, harvest, weights | Loss questions s2q39, s2q46-s2q50 confirmed in the 2024 data dictionary | NISR terms |
| NISR SAS 2026 Season A Final Report (updated 28 Apr 2026) | Published production 2026A and 2025A (`data/inputs/published_national.csv`) | Table 6, p.30. District table: Table 15 (also in `Tables_2026 Season A.xlsx`) | Public |
| NISR SAS 2026 Season B Main Report (updated 22 Sep 2026) | Published production 2026B and 2025B | Table 6, p.31. District table: Table 13, p.41 (also in `Tables_2026 Season B.xlsx`) | Public |
| NISR SAS 2025 Annual Tables (`data/inputs/nisr_tables/SAS_2025_Annual_Tables.xlsx`) | District production 2025A/B/C (Tables 24-26) and NISR post-harvest loss share (Tables 27-29, "Use of production by farmers"); 2025C national total (Table 26) | `published_district.csv`, `published_loss_share.csv`, `published_national.csv` | Public |
| NISR Tables_2026 Season A (`Tables_2026 Season A.xlsx`) | District production 2026A (Table 15); loss share 2026A (Table 16); 2024 production from the previous-year rows | same | Public |
| NISR Tables_2026 Season B (`Tables_2026 Season B.xlsx`) | District production 2026B (Table 13); loss share 2026B (Table 14); 2024 production from the previous-year rows | same | Public |
| NISR SAS 2025 Annual Report (Final report, summary, INCAMAKE PDFs) | Narrative and cross-checks for the 2025 tables | statistics.gov.rw, SAS Annual Report 2025 page | Public |
| NISR CPI January 2025 report | Food index Jan-24, Dec-24, Jan-25 (`data/inputs/cpi.csv`) | Annexes 1-3, pp.7-9, Feb 2014=100 | CC BY 4.0 |
| NISR CPI September 2026 report | Food index Sep-25, Aug-26, Sep-26 | Annexes 1-3, pp.10-12, Feb 2014=100 | CC BY 4.0 |
| NISR CPI_time_series_September_2026.xls | Full monthly series (optional upgrade of cpi.csv) | 13.8 MB on the CPI September 2026 page | CC BY 4.0 |
| NISR EICV7 2023/24 microdata (catalog 119), `Cross_Section/CS_S8B_Food_Expenditure_Consumption.dta` | Unit values (prices): value / quantity of purchases reported in kg, visits 2-5, items 19 maize, 1 beans, 45 sorghum, 16 rice (milled), 47 wheat, 7 cassava, 5 Irish potato, 6 sweet potato, 9 cooking banana | Fieldwork Oct 2023 - Oct 2024. Household purchase prices, not farm-gate. The file has no purchase dates. | NISR terms (not committed) |
| NISR EICV7 Methodological Note (2025-04) | 2,400 kcal/adult equivalent/day (p.30); consumption valued in Jan 2024 national prices (pp.29-30) → price base month | statistics.gov.rw/sites/default/files/documents/2025-04/Methodological Note.pdf | Public |
| kcal per kg by crop (`data/inputs/kcal_per_kg.csv`) | Calorie conversion | West, Pepping & Temalilwa (1988), *The composition of foods commonly eaten in East Africa*, as reproduced in FAO (2001) *Improving Nutrition through Home Gardening*, Appendix 2 (fao.org/4/x3996e/x3996e44.htm), per 100 g edible portion, adjusted for waste. Flags below. | Public |
| District boundaries | Map | TODO: NISR geodata first, geoBoundaries fallback | TODO |

## Notes

- **Prices:** national EICV7 purchase-price medians (Rwf/kg, nominal, at purchase time): beans 800, cassava 333, cooking banana 300, Irish potato 500, maize 400, rice 1,200 (milled), sorghum 700, sweet potato 250, wheat 1,000. Rice is multiplied by 0.65 (paddy-to-milled, assumption). Coverage: 6 crops have at least 10 observations in all 30 districts; maize 28 districts, sorghum 20, wheat 3 (others use the national median). Rolled forward x1.350: Sep-26 rural food index 332.5 divided by the average of Jan-24 (236.2) and Dec-24 (256.4) = 246.3, a mid-2024 proxy because the file has no purchase dates (assumption).
- **Price caveat:** household purchase prices are an upper-side estimate of farmers' loss. The base month is uncertain: using Jan-2024 alone would give a factor of 1.408 (about 4% higher prices), Dec-2024 alone 1.297 (about 4% lower).

- **Calorie factor flags:** rice: SAS reports paddy, so the milled value is multiplied by 0.65 (paddy to milled), an assumption not yet sourced. Cooking banana uses "Plantain, ripe, raw" (proxy). Wheat uses "Wheat, whole, parboiled" (proxy, no raw-grain entry). Cassava assumes the SAS reports fresh roots; confirm against the SAS report definitions.

- **Food inflation:** in September 2026, food prices rose 20.9% in the year in **urban** areas, 27.0% in **rural** areas and 25.2% for all Rwanda (CPI Sept 2026, Annexes 1-3). We use the rural index because the losses are on farms.
- **Price roll-forward:** rural food index, average of Jan-24 (236.2) and Dec-24 (256.4) = 246.3 → Sep-26 332.5, factor 1.350.
- **2026 seasons:** NISR has published 2026A and 2026B production, but microdata ends at 2025. The `loss_latest` table applies the 2025 loss rate of the same season to 2026 production, and is labelled as an extrapolation.
- Crop mapping: rice = paddy rice; beans = all beans (bush + climbing, loss share weighted by production); cooking_banana = cooking banana only. Season C covers only sweet potato, Irish potato and beans.
- 2025A and 2025B figures come from the comparison columns of the 2026 reports. If they differ from the SAS 2025 annual report, use the annual report figures for validation and note the revision.
