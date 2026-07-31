import streamlit as st
import pandas as pd
import plotly.express as px

from utils import (
    add_country_iso3,
    generate_country_insight,
    load_data,
    year_filter,
    keep_alive,
    themed_layout,
    DIVERGING_SCALE,
    generate_margin_insight
)


# --------------------------------------------------
# Load Dataset
# --------------------------------------------------
df_full = load_data()


# --------------------------------------------------
# Page Header
# --------------------------------------------------
st.title("🌍 How is global performance right now?")


# --------------------------------------------------
# Sidebar Filters
# --------------------------------------------------
with st.sidebar:
    st.header("Filters")

    df = year_filter(df_full)

    keep_alive("flt_market", "All")
    st.pills("Market", ["All"] + sorted(df_full["Market"].unique()), key="flt_market", selection_mode="single")

    keep_alive("flt_show_loss_only", False)
    st.toggle("Show only loss-making combinations", key="flt_show_loss_only")


# Apply market filter
if st.session_state.flt_market and st.session_state.flt_market != "All":
    df = df[df["Market"] == st.session_state.flt_market]


# Stop rendering if no data matches filters
if df.empty:
    st.warning("No data matches current filters.")
    st.stop()


# --------------------------------------------------
# Filter Summary
# --------------------------------------------------
st.caption(
    f"{len(df):,} orders shown | {st.session_state.flt_year[0]}–{st.session_state.flt_year[1]} | Market: {st.session_state.flt_market}"
)


# --------------------------------------------------
# KPI Metrics
# --------------------------------------------------
k1, k2, k3, k4 = st.columns(4)

total_sales, total_profit = df["Sales"].sum(), df["Profit"].sum()
margin = total_profit / total_sales * 100
full_margin = df_full["Profit"].sum() / df_full["Sales"].sum() * 100

k1.metric("Sales", f"${total_sales:,.0f}", f"{len(df) / len(df_full) * 100:.1f}% data coverage", height="stretch", delta_arrow="off", delta_color="blue")
k2.metric("Profit", f"${total_profit:,.0f}", f"{total_profit / df_full['Profit'].sum() * 100:.1f}% of total", height="stretch", delta_arrow="off", delta_color="blue")
k3.metric("Margin", f"{margin:.1f}%", f"{margin - full_margin:+.1f}pp vs overall")
k4.metric("Orders", f"{len(df):,}", f"{len(df) / len(df_full) * 100:.1f}% of total", height="stretch", delta_arrow="off", delta_color="blue")

st.space("small")


# --------------------------------------------------
# Main Dashboard Layout
# --------------------------------------------------
col_left, col_right = st.columns([1, 1], border=False, gap="medium")


# --------------------------------------------------
# Regional Margin Analysis
# --------------------------------------------------
with col_left:
    st.markdown("###### 📶 Profit Margin by Region × Category")

    agg = df.groupby(["Region", "Category"]).agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Profit", "sum")
    ).reset_index()

    agg["Margin"] = agg["Total_Profit"] / agg["Total_Sales"] * 100

    st.caption(generate_margin_insight(agg))

    if st.session_state.flt_show_loss_only:
        loss_regions = agg[agg["Margin"] < 0]["Region"].unique()
        agg = agg[agg["Region"].isin(loss_regions)]

    if agg.empty:
        st.success("No loss-making combinations in this selection! 🎉")

    else:
        pivot = agg.pivot(index="Region", columns="Category", values="Margin")
        pivot = pivot.loc[pivot.min(axis=1).sort_values().index]

        fig1 = px.imshow(
            pivot,
            color_continuous_scale=DIVERGING_SCALE,
            color_continuous_midpoint=0,
            aspect="auto",
            text_auto=".1f",
            labels={"color": "Margin %"}
        )

        fig1.update_traces(texttemplate="%{z:.1f}%", textfont=dict(size=10), xgap=2, ygap=2)

        themed_layout(
            fig1,
            coloraxis_showscale=False,
            height=360,
            xaxis=dict(title=""),
            yaxis=dict(title=""),
            margin=dict(l=100, r=20, t=20, b=30)
        )

        with st.container(border=False, horizontal_alignment="center"):
            st.plotly_chart(fig1, width="content", theme=None)

        worst, best = agg.loc[agg["Margin"].idxmin()], agg.loc[agg["Margin"].idxmax()]

        st.info(
            f"""
            Lowest:
            **{worst.Region} - {worst.Category}**
            ({worst.Margin:.1f}%)                 
            Highest:
            **{best.Region} - {best.Category}**
            ({best.Margin:.1f}%)
            """
        )


# --------------------------------------------------
# Country Margin Analysis
# --------------------------------------------------
with col_right:
    st.markdown("###### 🧭 Profit Margin by Country")

    country_agg = df.groupby("Country").agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Profit", "sum")
    ).reset_index()

    country_agg = add_country_iso3(country_agg)
    country_agg["Margin"] = country_agg["Total_Profit"] / country_agg["Total_Sales"] * 100

    st.caption(generate_country_insight(country_agg))

    fig2 = px.choropleth(
        country_agg,
        locations="ISO3",
        locationmode="ISO-3",
        color="Margin",
        color_continuous_scale=DIVERGING_SCALE,
        color_continuous_midpoint=0,
        range_color=[-50, 50],
        hover_name="Country",
        hover_data={"Total_Sales": ":,.0f", "Total_Profit": ":,.0f", "Margin": ":.1f", "Country": False},
        projection="natural earth",
        labels={"Margin": "Profit Margin (%)"}
    )

    themed_layout(
        fig2,
        height=390,
        geo=dict(showframe=False, showcoastlines=False, bgcolor="rgba(0,0,0,0)"),
        coloraxis_colorbar=dict(title="Margin %", thickness=15, len=0.6),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    with st.container(border=False, horizontal_alignment="center"):
        st.plotly_chart(fig2, width="content", theme=None)


    # Country Ranking Controls
    with st.expander("Country Rankings", icon="🏆", type="compact", on_change="rerun"):
        rank_mode = st.radio("Show", ["Top Countries", "Bottom Countries"], horizontal=True, key="country_rank_mode")

        n_countries = st.slider("Number of countries", min_value=3, max_value=10, value=5, key="country_rank_n")

        ranking = country_agg.nlargest(n_countries, "Margin") if rank_mode == "Top Countries" else country_agg.nsmallest(n_countries, "Margin")

        st.dataframe(
            ranking[["Country", "Margin", "Total_Sales", "Total_Profit"]].style.format(
                {"Margin": "{:.1f}%", "Total_Sales": "${:,.0f}", "Total_Profit": "${:,.0f}"}
            ),
            hide_index=True,
            width="stretch"
        )


# --------------------------------------------------
# Raw Data Preview
# --------------------------------------------------
st.space("small")

with st.expander("View underlying data", icon="📄"):
    st.dataframe(df.head(200), width="content", height=200)

st.space("small")