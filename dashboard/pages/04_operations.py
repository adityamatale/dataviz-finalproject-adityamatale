import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from utils import (
    generate_profit_contribution_insight,
    generate_shipmode_insight,
    load_data,
    year_filter,
    keep_alive,
    themed_layout
)


# --------------------------------------------------
# Load Dataset
# --------------------------------------------------
df_full = load_data()


# --------------------------------------------------
# Page Header
# --------------------------------------------------
st.title("🚚 Does fulfillment affect Profitability?")


# --------------------------------------------------
# Sidebar Filters
# --------------------------------------------------
with st.sidebar:
    st.header("Filters")

    df = year_filter(df_full)

    keep_alive("flt_category_p4", "All")
    st.pills("Category", ["All"] + sorted(df_full["Category"].unique()), key="flt_category_p4", selection_mode="single")

    keep_alive("flt_shipmode_p4", sorted(df_full["Ship Mode"].unique()))
    st.multiselect("🚛 Ship Mode", sorted(df_full["Ship Mode"].unique()), key="flt_shipmode_p4")


# Apply filters
if st.session_state.flt_category_p4 and st.session_state.flt_category_p4 != "All":
    df = df[df["Category"] == st.session_state.flt_category_p4]

if not st.session_state.flt_shipmode_p4:
    st.warning("Select at least one ship mode.")
    st.stop()

df = df[df["Ship Mode"].isin(st.session_state.flt_shipmode_p4)]


# Validate filtered data
if df.empty:
    st.warning("No data matches current filters.")
    st.stop()


# --------------------------------------------------
# Filter Summary
# --------------------------------------------------
st.caption(f"{len(df):,} orders | {st.session_state.flt_year[0]}–{st.session_state.flt_year[1]} | Category: {st.session_state.flt_category_p4}")

st.space("small")


# --------------------------------------------------
# Main Dashboard Layout
# --------------------------------------------------
col_left, col_right = st.columns([1, 1.2], border=False, gap="medium")


# --------------------------------------------------
# Shipping Mode Order Value Analysis
# --------------------------------------------------
with col_left:
    st.markdown("###### 📦 Order Value Distribution by Shipping Mode")

    p95 = df["Sales"].quantile(0.95)
    df_cap = df[df["Sales"] <= p95]

    st.caption(generate_shipmode_insight(df_cap))


    # Identify ship mode with highest median order value
    median_sales = df_cap.groupby("Ship Mode")["Sales"].median().sort_values(ascending=False)
    top_ship_mode = median_sales.index[0]

    ship_summary = (df.groupby('Ship Mode')
                .agg(Avg_Sales=('Sales', 'mean'), Avg_Shipping_Cost=('Shipping Cost', 'mean'))
                .reset_index())

    # Highlight top performing ship mode
    color_map = {
        sm: "#2E75B6" if sm == top_ship_mode else "#AAAAAA"
        for sm in df_cap["Ship Mode"].unique()
    }


    fig1 = px.box(
        df_cap,
        x="Sales",
        y="Ship Mode",
        color="Ship Mode",
        color_discrete_map=color_map,
        points=False
    )

    for _, row in ship_summary.iterrows():
        fig1.add_annotation(
            x=p95 * 0.92, y=row['Ship Mode'],
            text=f"avg ship cost: ${row['Avg_Shipping_Cost']:.0f}",
            showarrow=False, font=dict(size=10, color='#666666', family='Arial'),
            xanchor='right', yshift=12,                    # added — lifts text above the whisker line
            bgcolor='white', borderpad=2                    # added — clean background so line doesn't cross text
        )

    themed_layout(
        fig1,
        height=360,
        xaxis=dict(gridcolor="rgba(128,128,128,0.15)", title="Order Value ($, capped 95th pct)"),
        yaxis=dict(title=""),
        showlegend=False,
        margin={"l": 80, "r": 30, "t": 40, "b": 60}
    )

    with st.container(border=False, horizontal_alignment="center"):
        st.plotly_chart(fig1, width="content", theme=None)


# --------------------------------------------------
# Product Profit Contribution Analysis
# --------------------------------------------------
with col_right:
    st.markdown("###### 💰 Profit Contribution by Product Sub-category")

    sub_profit = df.groupby("Sub-Category")["Profit"].sum().reset_index().sort_values("Profit")

    st.caption(generate_profit_contribution_insight(sub_profit))


    if len(sub_profit) > 0:
        labels = sub_profit["Sub-Category"].tolist() + ["Total"]
        values = sub_profit["Profit"].tolist() + [sub_profit["Profit"].sum()]
        measures = ["relative"] * len(sub_profit) + ["total"]

        trace = go.Waterfall(
            x=labels,
            y=values,
            measure=measures,
            connector=dict(line=dict(color="#CCCCCC", width=1, dash="dot")),
            increasing=dict(marker_color="#2E75B6"),
            decreasing=dict(marker_color="#E07B39"),
            totals=dict(marker_color="#4D4D4D"),
            texttemplate="%{y:$,.0f}",
            textposition="outside",
            textfont=dict(size=9)
        )

        fig2 = go.Figure(data=[trace])


        # Highlight lowest profit contributor
        worst = sub_profit.iloc[0]

        fig2.add_annotation(
            x=worst["Sub-Category"],
            y=worst["Profit"],
            text=f"<b>{worst['Sub-Category']}</b><br>Lowest contributor<br>${worst['Profit']:,.0f}",
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-100,
            font=dict(size=10)
        )


        themed_layout(
            fig2,
            height=400,
            xaxis=dict(tickangle=-45),
            yaxis=dict(gridcolor="rgba(128,128,128,0.15)", title="Profit ($)"),
            showlegend=False,
            margin={"l": 50, "r": 10, "t": 20, "b": 70}
        )

        with st.container(border=False, horizontal_alignment="center"):
            st.plotly_chart(fig2, width="content", theme=None)


# --------------------------------------------------
# Raw Data Preview
# --------------------------------------------------
st.space("xxlarge")
st.space("small")

with st.expander("View underlying data", icon="📄"):
    st.dataframe(df.head(200), width="content", height=200)

st.space("small")