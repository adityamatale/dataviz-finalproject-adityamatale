import streamlit as st
import pandas as pd
import plotly.express as px

from utils import (
    generate_discount_band_insight,
    generate_discount_margin_insight,
    load_data,
    year_filter,
    keep_alive,
    themed_layout,
    DIVERGING_SCALE,
    CATEGORY_COLORS
)


# --------------------------------------------------
# Load Dataset
# --------------------------------------------------
df_full = load_data()


# --------------------------------------------------
# Page Header
# --------------------------------------------------
st.title("💸 Are Discounts destroying our Margins?")


# --------------------------------------------------
# Sidebar Filters
# --------------------------------------------------
with st.sidebar:
    st.header("Filters")

    df = year_filter(df_full)

    keep_alive("flt_category_p2", "All")
    st.pills("Category", ["All"] + sorted(df_full["Category"].unique()), key="flt_category_p2", selection_mode="single")

    keep_alive("flt_discount_p2", (0.0, 1.0))
    st.slider("🏷️ Discount range", 0.0, 1.0, key="flt_discount_p2", format="%.0f%%")


# Apply category filter
if st.session_state.flt_category_p2 and st.session_state.flt_category_p2 != "All":
    df = df[df["Category"] == st.session_state.flt_category_p2]


# Apply discount filter
lo, hi = st.session_state.flt_discount_p2
df_discount = df[df["Discount"].between(lo, hi)]


if df.empty:
    st.warning("No data matches current filters.")
    st.stop()


# --------------------------------------------------
# Filter Summary
# --------------------------------------------------
st.caption(f"{len(df):,} orders | {st.session_state.flt_year[0]}–{st.session_state.flt_year[1]} | Category: {st.session_state.flt_category_p2} | Discount: {lo:.0%}–{hi:.0%}")

st.space("small")


# --------------------------------------------------
# Main Dashboard Layout
# --------------------------------------------------
col_left, col_right = st.columns([1, 1], border=False, gap="medium")


# --------------------------------------------------
# Discount vs Margin Analysis
# --------------------------------------------------
with col_left:
    st.markdown("###### 🎫 Discount Impact on Profit Margin by Sub-category")

    agg = df.groupby(["Sub-Category", "Category"]).agg(
        Avg_Discount=("Discount", "mean"),
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Profit", "sum")
    ).reset_index()

    agg["Margin"] = agg["Total_Profit"] / agg["Total_Sales"] * 100

    st.caption(generate_discount_margin_insight(agg))

    fig1 = px.scatter(
        agg,
        x="Avg_Discount",
        y="Margin",
        size="Total_Sales",
        color="Category",
        color_discrete_map=CATEGORY_COLORS,
        hover_name="Sub-Category",
        size_max=45
    )

    fig1.add_hline(y=0, line_dash="dash", line_color="#888888", line_width=1.5)

    worst = agg.loc[agg["Margin"].idxmin()]

    fig1.add_annotation(
        x=worst["Avg_Discount"],
        y=worst["Margin"],
        text=f"<b>{worst['Sub-Category']}</b><br>{worst['Avg_Discount']:.0%} discount<br>{worst['Margin']:.1f}% margin",
        showarrow=True,
        arrowhead=1,
        ax=-40,
        ay=-40
    )

    fig1.update_traces(marker=dict(opacity=0.8, line=dict(width=0.5, color="white")))

    themed_layout(
        fig1,
        height=400,
        xaxis=dict(tickformat=".0%", gridcolor="rgba(128,128,128,0.15)", title="Avg Discount"),
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)", title="Profit Margin %"),
        legend=dict(orientation="h", y=1.15, x=0.5, xanchor="center", title=""),
        margin=dict(l=60, r=30, t=60, b=40)
    )

    with st.container(border=False, horizontal_alignment="center"):
        st.plotly_chart(fig1, width="content", theme=None)


# --------------------------------------------------
# Discount Band Analysis
# --------------------------------------------------
with col_right:
    st.markdown("###### 📝 Profit Margin across Discount Bands and Order Sizes")

    d2 = df_discount.copy()
    d2["Qty_Bin"] = pd.cut(d2["Quantity"], bins=[0, 3, 6, 9, 14], labels=["1-3", "4-6", "7-9", "10-14"])
    d2["Disc_Bin"] = pd.cut(d2["Discount"], bins=[-0.01, 0.1, 0.2, 0.3, 0.5, 1.0], labels=["0-10%", "10-20%", "20-30%", "30-50%", "50%+"])

    agg2 = d2.groupby(["Qty_Bin", "Disc_Bin"], observed=True).agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Profit", "sum")
    ).reset_index()

    if agg2.empty:
        st.info("Not enough data in this filter combination.")

    else:
        agg2["Margin"] = agg2["Total_Profit"] / agg2["Total_Sales"] * 100

        st.caption(generate_discount_band_insight(agg2))

        fig2 = px.scatter(
            agg2,
            x="Disc_Bin",
            y="Qty_Bin",
            size="Total_Sales",
            color="Margin",
            color_continuous_scale=DIVERGING_SCALE,
            color_continuous_midpoint=0,
            range_color=[-40, 40],
            size_max=55
        )

        worst = agg2.loc[agg2["Margin"].idxmin()]

        fig2.add_annotation(
            x=worst["Disc_Bin"],
            y=worst["Qty_Bin"],
            text="Lowest margin",
            showarrow=True,
            arrowhead=1,
            ax=35,
            ay=-30
        )

        fig2.update_traces(marker=dict(line=dict(width=0.5, color="white"), opacity=0.9))

        themed_layout(
            fig2,
            height=400,
            xaxis=dict(title="Discount Band"),
            yaxis=dict(title="Quantity"),
            coloraxis_colorbar=dict(title="Margin %", thickness=15, len=0.6),
            margin=dict(l=60, r=30, t=20, b=40)
        )

        with st.container(border=False, horizontal_alignment="center"):
            st.plotly_chart(fig2, width="content", theme=None)


# --------------------------------------------------
# Best / Worst Segment Summary
# --------------------------------------------------
st.space("small")

if agg2.empty:
    pass
else:
    best = agg2.loc[agg2["Margin"].idxmax()]
    worst = agg2.loc[agg2["Margin"].idxmin()]

    c1, c2 = st.columns(2)

    c1.metric(
        "Best Segment",
        f"{best['Disc_Bin']} · {best['Qty_Bin']}",
        f"{best['Margin']:.1f}% margin",
        help="The most profitable combination of discount band and order quantity within the current filters. The value shows the discount range and quantity bin, while the margin below is the average profit margin for that segment."
    )

    c2.metric(
        "Worst Segment",
        f"{worst['Disc_Bin']} · {worst['Qty_Bin']}",
        f"{worst['Margin']:.1f}% margin",
        help="The least profitable combination of discount band and order quantity within the current filters. Use this to identify where heavy discounts or specific order sizes are associated with the weakest margins."
    )


# --------------------------------------------------
# Raw Data Preview
# --------------------------------------------------
st.space("small")

with st.expander("View underlying data", icon="📄"):
    st.dataframe(df.head(200), width="content", height=200)

st.space("small")