"""Page 3 - Crop and stage explorer: which crop loses most, and where in the chain?  OWNER: Chadia"""
import numpy as np
import plotly.express as px
import streamlit as st

from common import BADGE, DETAIL_CAPTION, crop_name, download, load, season_filter, setup
from isarura_core.config import DISTRICT_LIST, STAGES

meta = setup("Crop and stage")
seasons = season_filter(meta)
st.title("Which crop loses most, and where in the chain?")
st.caption(DETAIL_CAPTION)

area = st.selectbox("Area", ["National"] + DISTRICT_LIST)
r = load("loss_rates")
r = r[r["season"].isin(seasons) & (r["district"] == area) & r["stage"].isin(STAGES)]

# mean across the selected seasons; a cell is greyed if every season is small-n
h = r.groupby(["crop", "stage"], as_index=False).agg(loss_rate=("loss_rate", "mean"),
                                                     n=("n_farmers", "sum"), small=("flag_small_n", "all"))
grid = h.pivot(index="crop", columns="stage", values="loss_rate").reindex(columns=STAGES)
small = h.pivot(index="crop", columns="stage", values="small").reindex(columns=STAGES).fillna(True).astype(bool)
shown = grid.mask(small)
shown.index = [crop_name(c) for c in shown.index]

fig = px.imshow(shown * 100, color_continuous_scale="cividis", aspect="auto", text_auto=".1f",
                labels={"color": "% of harvest lost", "x": "Stage", "y": ""})
fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="#d9d9d9")
st.plotly_chart(fig, width="stretch")
st.markdown(BADGE["calculated"] + f" Grey cells: fewer than {meta['min_n']} sampled farmers, not shown.")

if grid.notna().any().any():
    c, s = np.unravel_index(np.nanargmax(shown.to_numpy(dtype=float)), shown.shape) if shown.notna().any().any() else (0, 0)
    st.caption(f"Takeaway: the highest reliable rate in {area} is **{shown.index[c]}** at the **{STAGES[s]}** stage.")

st.subheader("Crops ranked by total loss rate")
t = load("loss_rates")
t = t[t["season"].isin(seasons) & (t["district"] == area) & (t["stage"] == "total")]
t = t.groupby("crop", as_index=False).agg(loss_rate=("loss_rate", "mean"), ci_low=("ci_low", "mean"),
                                          ci_high=("ci_high", "mean"), farmers=("n_farmers", "sum"))
t = t.sort_values("loss_rate", ascending=False)
t.insert(0, "Crop", t.pop("crop").map(crop_name))
st.dataframe(t, hide_index=True, width="stretch", column_config={
    "loss_rate": st.column_config.NumberColumn("Loss rate", format="percent"),
    "ci_low": st.column_config.NumberColumn("95% low", format="percent"),
    "ci_high": st.column_config.NumberColumn("95% high", format="percent")})
download(r, f"stage_rates_{area}")
