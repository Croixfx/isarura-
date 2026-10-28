"""Page 4 - District profile: what should my district do first?  OWNER: Chadia (layout), Croix (scenario logic)"""
import pandas as pd
import plotly.express as px
import streamlit as st

from common import BADGE, crop_name, download, load, rwf, season_filter, setup, tonnes
from isarura_core.config import DISTRICT_LIST, STAGES
from isarura_core.priority import priority

meta = setup("District profile")
seasons = season_filter(meta)
default = st.session_state.get("district", DISTRICT_LIST[0])
district = st.selectbox("District", DISTRICT_LIST, index=DISTRICT_LIST.index(default))
st.session_state["district"] = district
st.title(f"{district}: what to fix first")

lv = load("loss_value")
lv = lv[lv["season"].isin(seasons)]
mine = lv[lv["district"] == district]
tot = mine[mine["stage"] == "total"]

c1, c2, c3 = st.columns(3)
c1.metric("Food lost", tonnes(tot["tonnes_lost"].sum()))
c2.metric("Value lost", rwf(tot["value_rwf"].sum()))
c3.metric("Adult-years of food", f"{tot['adult_years'].sum():,.0f}")
st.markdown(BADGE["calculated"])

left, right = st.columns(2)
with left:
    st.subheader("Top crops by value lost")
    top = tot.groupby("crop", as_index=False)["value_rwf"].sum().sort_values("value_rwf", ascending=False).head(5)
    top["Crop"] = top["crop"].map(crop_name)
    fig = px.bar(top, x="value_rwf", y="Crop", orientation="h", labels={"value_rwf": "Value lost (Rwf)", "Crop": ""},
                 color_discrete_sequence=["#0072B2"])
    fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")
with right:
    st.subheader("Loss rate by stage vs national")
    r = load("loss_rates")
    r = r[r["season"].isin(seasons) & r["stage"].isin(STAGES)]
    cmp = (r[r["district"].isin([district, "National"])].groupby(["district", "stage"], as_index=False)["loss_rate"].mean())
    fig = px.bar(cmp, x="stage", y="loss_rate", color="district", barmode="group",
                 color_discrete_map={district: "#D55E00", "National": "#999999"},
                 labels={"loss_rate": "Share of harvest lost", "stage": "", "district": ""})
    fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), yaxis_tickformat=".0%")
    st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("Priority list")
with st.expander("Test a scenario: what if an intervention avoided part of the loss?", expanded=False):
    st.caption("These are your assumptions, not NISR statistics. Leave all at 0 to rank by total loss value.")
    cols = st.columns(len(STAGES))
    a_k = {k: cols[i].slider(k.capitalize(), 0, 100, 0, 5, format="%d%%", key=f"a_{k}") / 100 for i, k in enumerate(STAGES)}
    p1, p2 = st.columns(2)
    price_change = p1.slider("Price change", -30, 50, 0, 5, format="%d%%") / 100
    cost = p2.number_input("Cost per tonne avoided (Rwf, optional)", min_value=0, value=0, step=10_000)

scenario = any(a_k.values())
pr = priority(lv, a_k=a_k if scenario else None, price_change=price_change, cost_per_tonne=cost or None)
pr["national_rank"] = pr["rank"]
local = pr[pr["district"] == district].copy()
local["Crop"] = local["crop"].map(crop_name)
show = ["Crop", "loss_value_rwf", "avoidable_value_rwf", "national_rank"] + (["value_per_rwf"] if cost else [])
st.dataframe(local[show], hide_index=True, width="stretch", column_config={
    "loss_value_rwf": st.column_config.NumberColumn("Value lost (Rwf)", format="localized"),
    "avoidable_value_rwf": st.column_config.NumberColumn("Avoidable value (Rwf)", format="localized"),
    "national_rank": st.column_config.NumberColumn("Rank among all district-crop pairs"),
    "value_per_rwf": st.column_config.NumberColumn("Rwf saved per Rwf spent", format="%.2f")})
st.markdown(BADGE["scenario" if (scenario or price_change or cost) else "calculated"]
            + f" {pr['assumption_set'].iloc[0] if len(pr) else ''}")
download(local.drop(columns=["Crop"]), f"priority_{district}")
