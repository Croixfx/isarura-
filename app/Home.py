"""Page 1 - National picture: how much food is lost, and what is it worth now?  OWNER: Chadia (layout), Croix (wording)"""
import plotly.express as px
import streamlit as st

from common import BADGE, STAGE_COLORS, crop_name, download, load, rwf, season_filter, setup, tonnes

meta = setup("National picture")
seasons = season_filter(meta)

st.title("Isarura: where Rwanda's harvest is lost")
st.markdown("From harvest to table: how much food is lost after harvest, what it is worth at today's prices, "
            "and where to act first.")

lv = load("loss_value")
lv = lv[lv["season"].isin(seasons)]
tot = lv[lv["stage"] == "total"]

c1, c2, c3 = st.columns(3)
c1.metric("Food lost after harvest", tonnes(tot["tonnes_lost"].sum()))
c2.metric(f"Value at {meta['price_month']} prices", rwf(tot["value_rwf"].sum()))
c3.metric("Equal to a year of food for", f"{tot['adult_years'].sum():,.0f} adults")
c2.caption(f"Range {rwf(tot['value_low_rwf'].sum())} to {rwf(tot['value_high_rwf'].sum())} (low/high price)")
c3.caption("Calorie equivalence only. It does not mean recovered food would reach any household.")
st.markdown(BADGE["calculated"] + f" Seasons: {', '.join(seasons)}")

st.divider()
left, right = st.columns([3, 2])
with left:
    stage = (lv[lv["stage"] != "total"].groupby("stage", as_index=False)
             .agg(tonnes_lost=("tonnes_lost", "sum"), value_rwf=("value_rwf", "sum"))
             .sort_values("tonnes_lost"))
    top_stage = stage.iloc[-1]
    st.subheader(f"Most food is lost in {top_stage['stage']}")
    fig = px.bar(stage, x="tonnes_lost", y="stage", orientation="h", color="stage",
                 color_discrete_map=STAGE_COLORS, labels={"tonnes_lost": "Tonnes lost", "stage": ""})
    fig.update_layout(showlegend=False, height=300, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width="stretch")
    st.caption(f"{top_stage['stage'].capitalize()} accounts for "
               f"{top_stage['tonnes_lost'] / stage['tonnes_lost'].sum():.0%} of stage-reported loss.")
with right:
    crops = (tot.groupby("crop", as_index=False)["value_rwf"].sum().sort_values("value_rwf", ascending=False))
    st.subheader(f"{crop_name(crops.iloc[0]['crop'])} loses the most value")
    crops["Crop"] = crops["crop"].map(crop_name)
    crops["Value lost"] = crops["value_rwf"].map(rwf)
    st.dataframe(crops[["Crop", "Value lost"]], hide_index=True, width="stretch")
    download(tot.drop(columns=["stage"]), "national_loss_value")

st.info("Loss quantities are reported by farmers in the Seasonal Agricultural Survey. Prices are EICV7 household "
        "unit values rolled forward with the CPI food index, not farm-gate quotes. See **Methods**.")
