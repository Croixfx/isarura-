"""Page 5 - Methods: can I trust this?  OWNER: Croix"""
import plotly.express as px
import streamlit as st

from common import BADGE, crop_name, download, load, setup

meta = setup("Methods")
st.title("Can I trust this?")

st.header("1. We reproduce NISR's published production first")
v = load("validation")
ok = v["within_tolerance"].mean()
st.markdown(f"Weighted production from the survey microdata matches NISR's published totals for "
            f"**{ok:.0%}** of crop-season pairs (median difference {v['difference_pct'].abs().median():.1f}%). "
            + BADGE["official"] + " vs " + BADGE["calculated"])
v2 = v.assign(Crop=v["crop"].map(crop_name))
fig = px.scatter(v2, x="nisr_published_t", y="our_estimate_t", color="within_tolerance", hover_data=["Crop", "season"],
                 color_discrete_map={True: "#0072B2", False: "#D55E00"},
                 labels={"nisr_published_t": "NISR published (t)", "our_estimate_t": "Isarura estimate (t)",
                         "within_tolerance": "Within tolerance"})
m = float(v[["nisr_published_t", "our_estimate_t"]].max().max())
fig.add_shape(type="line", x0=0, y0=0, x1=m, y1=m, line=dict(dash="dot", color="#999"))
fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, width="stretch")
st.dataframe(v2.drop(columns="crop"), hide_index=True, width="stretch")
download(v, "validation")

st.header("2. How each number is made")
st.markdown(f"""
| Step | What we do |
|---|---|
| Loss rate | Weighted ratio: sum(weight x kg lost) / sum(weight x kg harvested), per crop, district, season and stage, using NISR survey weights. |
| Uncertainty | 95% interval from resampling survey clusters (200 replicates). Cells with fewer than {meta['min_n']} farmers are flagged and greyed. |
| Tonnes | Loss rate x NISR published district production, so tonnes reconcile with official totals. |
| Price | Median EICV7 household unit value per crop and district (trimmed), rolled forward to {meta['price_month']} with the rural CPI food index. Low/high = 25th/75th percentile. |
| Meals | Tonnes x kcal per kg (FAO/INFOODS), divided by the daily adult requirement x 365. |
| Priority | Default: rank district-crop pairs by value lost. Scenario: user-chosen share avoidable per stage and cost per tonne. |
""")

st.header("3. Do the stages add up?")
sc = load("stage_consistency")
st.markdown(f"Farmers report a total loss and a loss at each stage. The median gap between them is "
            f"**{sc['gap_pp'].abs().median():.1f} percentage points**. We show both rather than forcing them to agree.")
download(sc, "stage_consistency")

st.header("4. Limits")
st.warning("""Loss quantities are reported by farmers and may be affected by recall and by how respondents define "lost".
Prices are estimates built from household unit values rolled forward with CPI; they are not farm-gate market quotes.
Calories-to-people figures are equivalences. They do not mean recovered food would reach any specific household.
Effectiveness and cost inputs are scenarios chosen by the user, not NISR statistics.
Nothing here replaces official NISR figures.""")

st.header("5. Sources, data use and declarations")
st.markdown("""
- NISR Seasonal Agricultural Survey microdata 2024, 2025 (microdata.statistics.gov.rw, catalog 113, 124)
- NISR SAS 2025 annual report (published production tables)
- NISR EICV7 2023/24 (unit values, extreme poverty)
- NISR CPI time series, September 2026 (CC BY 4.0)
- FAO/INFOODS food composition tables (TODO: exact table and version)
- District boundaries: TODO (NISR geodata or geoBoundaries, with licence)

**Data use.** No farm- or household-level data is in this app or its repository; only aggregates.
**Originality.** TODO: declaration text. **AI use.** TODO: disclosure text. **IP.** TODO: note on transfer to NISR per rules.
""")
