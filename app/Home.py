"""Page 1 - National picture: how much food is lost, and what is it worth now?  OWNER: Chadia (layout), Croix (wording)

Headline = NISR published production x NISR published post-harvest loss share (data/public/loss_official.csv).
Stage and crop detail below comes from the SAS microdata (2024A, 2025A) and says so.
"""
import plotly.express as px
import streamlit as st

from common import (BADGE, DETAIL_CAPTION, STAGE_COLORS, crop_name, download, load, prices_ready, rwf, season_filter,
                    setup, tonnes)

meta = setup("National picture")

st.title("Isarura: where Rwanda's harvest is lost")
st.markdown("From harvest to table: how much food is lost after harvest, what it is worth at today's prices, "
            "and where to act first.")

# ---- headline: official national figures, every season NISR publishes both production and loss for ----
off = load("loss_official")
all_seasons = sorted(off["season"].unique())
years = {y: {s[-1] for s in all_seasons if s.startswith(y)} for y in {s[:4] for s in all_seasons}}
complete = sorted(y for y, letters in years.items() if {"A", "B", "C"} <= letters)
default_year = complete[-1] if complete else max(years)
picked = st.multiselect("Seasons", all_seasons, default=[s for s in all_seasons if s.startswith(default_year)],
                        key="official_seasons") or all_seasons
o = off[off["season"].isin(picked)]

c1, c2, c3 = st.columns(3)
c1.metric("Food lost after harvest", tonnes(o["tonnes_lost"].sum()))
if prices_ready(meta) and o["value_rwf"].notna().any():
    c2.metric(f"Value at {meta['price_month']} prices", rwf(o["value_rwf"].sum()))
    c2.caption(f"Range {rwf(o['value_low_rwf'].sum())} to {rwf(o['value_high_rwf'].sum())} (low/high price)")
else:
    c2.metric("Value in Rwf", "Coming soon")
    c2.caption("Needs EICV7 unit prices, which are not loaded yet.")
c3.metric("Equal to a year of food for", f"{o['adult_years'].sum():,.0f} adults")
c3.caption("Calorie equivalence only. It does not mean recovered food would reach any household.")
st.markdown(BADGE["official"] + " NISR published production x NISR published post-harvest loss share. "
            + BADGE["calculated"] + " calories and adult-years.")

by_season = (o.groupby("season", as_index=False)
             .agg(production_t=("production_t", "sum"), tonnes_lost=("tonnes_lost", "sum"),
                  adult_years=("adult_years", "sum")))
by_season["loss_pct"] = 100 * by_season["tonnes_lost"] / by_season["production_t"]
show = by_season.rename(columns={"season": "Season", "production_t": "Production (t)", "tonnes_lost": "Lost (t)",
                                 "loss_pct": "Loss (% of production)", "adult_years": "Adult-years of food"})
st.dataframe(show, hide_index=True, width="stretch", column_config={
    "Production (t)": st.column_config.NumberColumn(format="localized"),
    "Lost (t)": st.column_config.NumberColumn(format="localized"),
    "Loss (% of production)": st.column_config.NumberColumn(format="%.2f"),
    "Adult-years of food": st.column_config.NumberColumn(format="localized")})

crop_tot = o.groupby("crop", as_index=False).agg(tonnes_lost=("tonnes_lost", "sum")).sort_values(
    "tonnes_lost", ascending=False)
crop_tot["Crop"] = crop_tot["crop"].map(crop_name)
fig = px.bar(crop_tot, x="tonnes_lost", y="Crop", orientation="h", labels={"tonnes_lost": "Tonnes lost", "Crop": ""},
             color_discrete_sequence=["#0072B2"])
fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), yaxis={"categoryorder": "total ascending"})
st.subheader(f"{crop_name(crop_tot.iloc[0]['crop'])} loses the most food")
st.plotly_chart(fig, width="stretch")
download(o, "national_loss_official")

# ---- detail: microdata ----
st.divider()
st.subheader("Where in the chain? Stage detail")
st.caption(DETAIL_CAPTION)
seasons = season_filter(meta)
lv = load("loss_value")
lv = lv[lv["season"].isin(seasons)]
stage = (lv[lv["stage"] != "total"].groupby("stage", as_index=False).agg(tonnes_lost=("tonnes_lost", "sum"))
         .sort_values("tonnes_lost"))
if stage["tonnes_lost"].sum() > 0:
    top_stage = stage.iloc[-1]
    st.markdown(f"**Most stage-reported loss is at the {top_stage['stage']} stage** "
                f"({top_stage['tonnes_lost'] / stage['tonnes_lost'].sum():.0%}).")
    fig = px.bar(stage, x="tonnes_lost", y="stage", orientation="h", color="stage",
                 color_discrete_map=STAGE_COLORS, labels={"tonnes_lost": "Tonnes lost", "stage": ""})
    fig.update_layout(showlegend=False, height=300, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width="stretch")
    st.markdown(BADGE["calculated"] + f" Microdata seasons: {', '.join(seasons)}")
else:
    st.info("No stage-level loss recorded for the selected microdata seasons.")

st.info("Loss quantities are reported by farmers in the Seasonal Agricultural Survey. Prices, when shown, are EICV7 "
        "household unit values rolled forward with the CPI food index, not farm-gate quotes. See **Methods**.")
