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

st.subheader("We also reproduce NISR's published post-harvest loss share")
vl = load("validation_loss")
if len(vl):
    st.markdown(f"NISR publishes post-harvest losses as a percentage of production. Our national loss rate from the "
                f"microdata differs from it by a median of **{vl['difference_pp'].abs().median():.2f} percentage points** "
                f"across {len(vl)} crop-season pairs. " + BADGE["official"] + " vs " + BADGE["calculated"])
    vl2 = vl.assign(Crop=vl["crop"].map(crop_name))
    fig2 = px.scatter(vl2, x="nisr_published_pct", y="our_estimate_pct", hover_data=["Crop", "season"],
                      labels={"nisr_published_pct": "NISR published loss (% of production)",
                              "our_estimate_pct": "Isarura estimate (%)"})
    m2 = float(vl[["nisr_published_pct", "our_estimate_pct"]].max().max())
    fig2.add_shape(type="line", x0=0, y0=0, x1=m2, y1=m2, line=dict(dash="dot", color="#999"))
    fig2.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig2, width="stretch")
    st.dataframe(vl2.drop(columns="crop"), hide_index=True, width="stretch")
    download(vl, "validation_loss")
else:
    st.info("No published loss shares overlap the seasons with microdata yet.")

st.caption("Losses in our own microdata run higher than NISR's published shares for beans, Irish potato and sorghum, "
           "so the national headline uses NISR's figures and both are shown here.")

st.header("2. How each number is made")
st.markdown(f"""
| Step | What we do |
|---|---|
| National headline | NISR published production x NISR published post-harvest loss share, for every season and crop NISR publishes both (2025A to 2026B). No microdata involved. |
| Loss rate | Weighted ratio: sum(weight x kg lost) / sum(weight x kg harvested), per crop, district, season and stage, using NISR survey weights. |
| Uncertainty | 95% interval from resampling survey clusters (200 replicates). Cells with fewer than {meta['min_n']} farmers are flagged and greyed. |
| Tonnes | Loss rate x NISR published district production, so tonnes reconcile with official totals. |
| Price | Median EICV7 household purchase unit value per crop and district (trimmed 5 to 95%; districts with fewer than 10 observations use the national median), rolled forward to {meta['price_month']} with the rural CPI food index. Low/high = 25th/75th percentile. |
| Meals | Tonnes x kcal per kg (East African food composition table, see sources), divided by the daily adult requirement x 365. |
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
- NISR EICV7 2023/24 (catalog 119), food purchases module (S8B): unit values = value / quantity for purchases reported in kg, visits 2 to 5. **Caveat:** these are household *purchase* prices, not farm-gate prices. Farm-gate values are typically lower, so the Rwf figures are an upper-side estimate of farmers' loss. The file has no purchase dates (fieldwork ran October 2023 to October 2024), so prices are rolled to the latest month with the rural food CPI from the average of the January 2024 and December 2024 index, a mid-2024 proxy (an assumption). **Rice:** EICV7 prices milled rice but the SAS loss is paddy, so rice prices are multiplied by 0.65, an assumed paddy-to-milled rate that is not yet sourced.
- NISR CPI time series, September 2026 (CC BY 4.0)
- Calorie factors: West, Pepping & Temalilwa (1988), *The composition of foods commonly eaten in East Africa*, as reproduced in FAO (2001), *Improving Nutrition through Home Gardening*, Appendix 2. Per 100 g edible portion, adjusted for waste. **Assumptions:** rice is paddy, so the milled value is multiplied by 0.65 (an assumed paddy-to-milled rate, not yet sourced); cooking banana uses plantain and wheat uses parboiled wheat as proxies; cassava is assumed to be reported as fresh roots.
- District boundaries: source to be confirmed

**Data use.** No farm- or household-level data is in this app or its repository; only aggregates.
**Originality.** This project is the original work of the team, built for the NISR 2026 Big Data Hackathon (Track 1). **AI use.** We used Claude (Anthropic) and Claude Code as assistants for code, data checks and drafting text; the team reviewed and takes responsibility for all code, figures and conclusions. No machine-learning model produces any estimate. **IP.** In line with the competition rules, the team agrees to the transfer of intellectual property rights in this submission to NISR.
""")
