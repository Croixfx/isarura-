"""Page 2 - Map: where is the loss concentrated?  OWNER: Chadia"""
import plotly.express as px
import streamlit as st

from common import BADGE, crop_name, download, geojson, load, rwf, season_filter, setup
from isarura_core.priority import priority

meta = setup("Map")
seasons = season_filter(meta)
st.title("Where is the loss concentrated?")

crops = sorted(load("loss_value")["crop"].unique())
c1, c2 = st.columns(2)
crop = c1.selectbox("Crop", ["All crops"] + crops, format_func=lambda c: c if c == "All crops" else crop_name(c))
metric = c2.radio("Show", ["Value lost (Rwf)", "Tonnes lost", "Loss rate", "Priority rank"], horizontal=True)

lv = load("loss_value")
lv = lv[lv["season"].isin(seasons) & (lv["stage"] == "total")]
if crop != "All crops":
    lv = lv[lv["crop"] == crop]
d = lv.groupby("district", as_index=False).agg(value_rwf=("value_rwf", "sum"), tonnes_lost=("tonnes_lost", "sum"),
                                                production_t=("production_t", "sum"))
d["loss_rate"] = d["tonnes_lost"] / d["production_t"]
pr = priority(load("loss_value"), seasons=seasons)
if crop != "All crops":
    pr = pr[pr["crop"] == crop]
d = d.merge(pr.groupby("district", as_index=False)["rank"].min().rename(columns={"rank": "best_rank"}),
            on="district", how="left")

col = {"Value lost (Rwf)": "value_rwf", "Tonnes lost": "tonnes_lost", "Loss rate": "loss_rate",
       "Priority rank": "best_rank"}[metric]
fig = px.choropleth(d, geojson=geojson(), locations="district", featureidkey="properties.district", color=col,
                    color_continuous_scale="cividis_r" if col == "best_rank" else "cividis",
                    hover_name="district",
                    hover_data={"district": False, "value_rwf": ":,.0f", "tonnes_lost": ":,.0f", "loss_rate": ":.1%"},
                    labels={"value_rwf": "Value lost (Rwf)", "tonnes_lost": "Tonnes lost", "loss_rate": "Loss rate",
                            "best_rank": "Best priority rank"})
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(height=520, margin=dict(l=0, r=0, t=0, b=0))
event = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points", key="map")
st.markdown(BADGE["calculated"] + (" Rank 1 = highest loss value." if col == "best_rank" else ""))

picked = None
try:
    pts = event.selection.points if event else []
    picked = pts[0].get("location") if pts else None
except AttributeError:
    pass
top = d.sort_values("value_rwf", ascending=False).iloc[0]
st.caption(f"Highest value lost: **{top['district']}** ({rwf(top['value_rwf'])}). Click a district to open it.")

district = st.selectbox("Open a district profile", sorted(d["district"]),
                        index=sorted(d["district"]).index(picked) if picked in set(d["district"]) else 0)
if picked or st.button("Open profile"):
    st.session_state["district"] = picked or district
    st.switch_page("pages/3_District_profile.py")

download(d, "map_districts")
