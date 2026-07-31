import streamlit as st
import plotly.express as px

from utils import (
    generate_segment_growth_insight,
    generate_segment_region_insight,
    generate_subcategory_volatility_insight,
    load_data,
    year_filter,
    keep_alive,
    themed_layout,
    HIGHLIGHT_COLOR,
    CONTEXT_GREY
)


# --------------------------------------------------
# Load Dataset
# --------------------------------------------------
df_full = load_data()


# --------------------------------------------------
# Page Header
# --------------------------------------------------
st.title("📈 How are Segments evolving over Time?")


# --------------------------------------------------
# Sidebar Filters
# --------------------------------------------------
with st.sidebar:
    st.header("Filters")

    df = year_filter(df_full)

    keep_alive("flt_segments_p3", sorted(df_full["Segment"].unique()))
    st.multiselect("👤 Segments", sorted(df_full["Segment"].unique()), key="flt_segments_p3")


# Validate segment selection
if not st.session_state.flt_segments_p3:
    st.warning("Select at least one segment.")
    st.stop()

df = df[df["Segment"].isin(st.session_state.flt_segments_p3)]

if df.empty:
    st.warning("No data matches current filters.")
    st.stop()


# --------------------------------------------------
# Filter Summary
# --------------------------------------------------
st.caption(f"{len(df):,} orders | {st.session_state.flt_year[0]}–{st.session_state.flt_year[1]} | Segments: {', '.join(st.session_state.flt_segments_p3)}")

st.space("small")


# --------------------------------------------------
# Main Dashboard Layout
# --------------------------------------------------
col_left, col_right = st.columns([1, 1], border=False, gap="medium")


# --------------------------------------------------
# Segment Growth Analysis
# --------------------------------------------------
with col_left:
    st.markdown("###### 📑 Sales Growth by Customer Segment")

    trend = df.groupby(["Year", "Segment"])["Sales"].sum().reset_index()
    years = sorted(trend["Year"].unique())

    st.caption(generate_segment_growth_insight(trend))

    if len(years) < 2:
        st.info("📅 Select at least two years to visualize growth trends.")

    else:
        growth = trend.pivot(index="Segment", columns="Year", values="Sales")

        if growth.shape[1] >= 2 and not growth.isnull().values.any():
            yrs = sorted(growth.columns)
            growth["pct"] = (growth[yrs[-1]] - growth[yrs[0]]) / growth[yrs[0]] * 100
            highlight = growth["pct"].idxmax()

        else:
            highlight = trend["Segment"].iloc[0]

        color_map = {s: HIGHLIGHT_COLOR if s == highlight else CONTEXT_GREY for s in trend["Segment"].unique()}

        fig1 = px.line(trend, x="Year", y="Sales", color="Segment", color_discrete_map=color_map, markers=True)

        fig1.update_traces(line=dict(width=1.5), marker=dict(size=5), showlegend=False)
        fig1.update_traces(line=dict(width=4), marker=dict(size=9), selector=dict(name=highlight))

        latest_year = trend["Year"].max()

        for seg in trend["Segment"].unique():
            point = trend[(trend["Segment"] == seg) & (trend["Year"] == latest_year)]
            pct = growth.loc[seg, "pct"]

            fig1.add_annotation(
                x=latest_year,
                y=point["Sales"].values[0],
                text=f"<b>{seg}</b> (+{pct:.0f}%)" if seg == highlight else f"{seg} (+{pct:.0f}%)",
                showarrow=False,
                xshift=10,
                xanchor="left",
                font=dict(size=12 if seg == highlight else 10, color=HIGHLIGHT_COLOR if seg == highlight else CONTEXT_GREY)
            )

        themed_layout(fig1, height=400, xaxis=dict(title="Year", tickmode="linear", dtick=1), yaxis=dict(gridcolor="rgba(128,128,128,0.15)", title="Total Sales ($)"), legend=dict(orientation="h", y=1.15, x=0.5, xanchor="center", title=""))

        with st.container(border=False, horizontal_alignment="center"):
            st.plotly_chart(fig1, width="content", theme=None)


    # --------------------------------------------------
    # Sub-category Stability Analysis
    # --------------------------------------------------
    with st.expander("Sales stability by sub-category", icon="📉", type="compact", on_change="rerun"):
        sub_year = df.groupby(["Sub-Category", "Year"])["Sales"].sum().reset_index()

        if len(sub_year["Year"].unique()) < 2:
            st.info("📅 Select at least two years to analyze sales stability.")

        else:
            st.caption(generate_subcategory_volatility_insight(sub_year))

            pivot = sub_year.pivot(index="Sub-Category", columns="Year", values="Sales")
            cv = (pivot.std(axis=1) / pivot.mean(axis=1)).sort_values(ascending=False)

            most_volatile, most_stable = cv.index[0], cv.index[-1]

            color_map = {sc: CONTEXT_GREY for sc in sub_year["Sub-Category"].unique()}
            color_map[most_volatile] = "#E07B39"
            color_map[most_stable] = HIGHLIGHT_COLOR

            fig2 = px.line(sub_year, x="Year", y="Sales", color="Sub-Category", color_discrete_map=color_map, markers=True)

            fig2.update_traces(line=dict(width=1), marker=dict(size=4), opacity=0.4, showlegend=False)
            fig2.update_traces(line=dict(width=3), marker=dict(size=8), opacity=1, selector=dict(name=most_volatile))
            fig2.update_traces(line=dict(width=3), marker=dict(size=8), opacity=1, selector=dict(name=most_stable))

            for sc, color in [(most_volatile, "#E07B39"), (most_stable, HIGHLIGHT_COLOR)]:
                pt = sub_year[(sub_year["Sub-Category"] == sc) & (sub_year["Year"] == sub_year["Year"].max())]

                fig2.add_annotation(
                    x=pt["Year"].values[0],
                    y=pt["Sales"].values[0],
                    text=f"<b>{sc}</b><br>CV: {cv[sc]:.2f}",
                    showarrow=False,
                    xshift=10,
                    xanchor="left",
                    font=dict(size=11, color=color)
                )

            themed_layout(fig2, height=450, xaxis=dict(title="Year", tickmode="linear", dtick=1), yaxis=dict(title="Sales ($)", gridcolor="rgba(128,128,128,0.15)"))

            with st.container(border=False, horizontal_alignment="center"):
                st.plotly_chart(fig2, width="content", theme=None)


# --------------------------------------------------
# Segment Region Distribution
# --------------------------------------------------
with col_right:
    st.markdown("###### 🌎 Sales distribution across Segments and Regions")

    sr = df.groupby(["Segment", "Region"]).agg(Total_Sales=("Sales", "sum"), Total_Profit=("Profit", "sum")).reset_index()
    sr["Margin"] = sr["Total_Profit"] / sr["Total_Sales"] * 100

    st.caption(generate_segment_region_insight(sr))

    fig3 = px.sunburst(sr, path=["Segment", "Region"], values="Total_Sales", color="Margin", color_continuous_scale="Blues", labels={"Total_Sales": "Sales", "Total_Profit": "Profit", "Margin": "Profit Margin %"})

    fig3.update_traces(textinfo="label", insidetextorientation="radial", marker=dict(line=dict(color="white", width=1)))

    themed_layout(fig3, height=400, margin=dict(l=10, r=10, t=20, b=30), coloraxis_colorbar=dict(title="Margin %", thickness=15, len=0.6))

    with st.container(border=False, horizontal_alignment="center"):
        st.plotly_chart(fig3, width="content", theme=None)


    # Segment-region KPI comparison
    best, worst = sr.loc[sr["Margin"].idxmax()], sr.loc[sr["Margin"].idxmin()]
    avg_margin = sr["Margin"].mean()

    c1, c2 = st.columns(2)

    c1.metric("Highest Margin", f"{best['Segment']} · {best['Region']}", f"{best['Margin']:.1f}% ({best['Margin'] - avg_margin:+.1f}pp)", help="The segment-region combination with the highest profit margin. The value in brackets shows how much this margin differs from the average margin across all segment-region combinations.")

    c2.metric("Lowest Margin", f"{worst['Segment']} · {worst['Region']}", f"{worst['Margin']:.1f}% ({worst['Margin'] - avg_margin:+.1f}pp)", help="The segment-region combination with the lowest profit margin. The value in brackets shows how far this margin is from the average segment-region margin.")


# --------------------------------------------------
# Raw Data Preview
# --------------------------------------------------
st.space("small")

with st.expander("View underlying data", icon="📄"):
    st.dataframe(df.head(200), width="content", height=200)

st.space("small")