"""Page 2 - Map: where is the loss concentrated?  OWNER: Chadia"""
import copy

import plotly.express as px
import streamlit as st

from common import BADGE, crop_name, download, geojson, load, rwf, season_filter, setup
from isarura_core.priority import priority


# --- GeoJSON fix -------------------------------------------------------------
# Plotly's geo maps expect outer rings clockwise and holes counter-clockwise.
# Standard GeoJSON (RFC 7946) is the opposite, so districts were drawn
# "inside out" (whole globe filled, Rwanda as a hole). Reverse the rings.
def _signed_area(ring):
    return sum(x1 * y2 - x2 * y1 for (x1, y1, *_), (x2, y2, *_) in zip(ring, ring[1:])) / 2


def _rewind_polygon(rings):
    out = []
    for i, ring in enumerate(rings):
        a = _signed_area(ring)
        if (i == 0 and a > 0) or (i > 0 and a < 0):
            ring = ring[::-1]
        out.append(ring)
    return out


@st.cache_data
def plotly_geojson():
    gj = copy.deepcopy(geojson())
    for f in gj["features"]:
        g = f["geometry"]
        if g["type"] == "Polygon":
            g["coordinates"] = _rewind_polygon(g["coordinates"])
        elif g["type"] == "MultiPolygon":
            g["coordinates"] = [_rewind_polygon(p) for p in g["coordinates"]]
    return gj
# -----------------------------------------------------------------------------


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

if d.empty:
    st.info("No data for this crop in the selected seasons.")
    st.stop()

col = {"Value lost (Rwf)": "value_rwf", "Tonnes lost": "tonnes_lost", "Loss rate": "loss_rate",
       "Priority rank": "best_rank"}[metric]
fig = px.choropleth(d, geojson=plotly_geojson(), locations="district", featureidkey="properties.district", color=col,
                    color_continuous_scale="cividis_r" if col == "best_rank" else "cividis",
                    hover_name="district",
                    hover_data={"district": False, "value_rwf": ":,.0f", "tonnes_lost": ":,.0f",
                                "loss_rate": ":.2%", "best_rank": True},
                    labels={"value_rwf": "Value lost (Rwf)", "tonnes_lost": "Tonnes lost", "loss_rate": "Loss rate",
                            "best_rank": "Best priority rank"})

fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(height=520, margin=dict(l=0, r=0, t=0, b=0), autosize=True)
if col == "loss_rate":
    fig.update_coloraxes(colorbar_tickformat=".2%")

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

districts = sorted(d["district"])
district = st.selectbox("Open a district profile", districts,
                        index=districts.index(picked) if picked in districts else 0)

# Only navigate on a NEW map click; the old selection persists when the user
# comes back to this page, which used to bounce them straight to the profile.
if picked and picked != st.session_state.get("_map_last_pick"):
    st.session_state["_map_last_pick"] = picked
    st.session_state["district"] = picked
    st.switch_page("pages/3_District_profile.py")
elif st.button("Open profile"):
    st.session_state["district"] = district
    st.switch_page("pages/3_District_profile.py")

download(d, "map_districts")