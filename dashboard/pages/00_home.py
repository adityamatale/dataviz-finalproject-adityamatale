import streamlit as st

from utils import load_data, get_cache_time


# --------------------------------------------------
# Load Dataset
# --------------------------------------------------
df = load_data()
cache_time = get_cache_time()


# --------------------------------------------------
# Page Header
# --------------------------------------------------
st.title("📦 Global Superstore Analytics")
st.caption(
    "A profitability story across 4 years, 147 countries, and 51K orders"
)


# --------------------------------------------------
# Key Performance Indicators
# --------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Orders",
    f"{len(df):,}"
)

c2.metric(
    "Countries",
    df["Country"].nunique()
)

c3.metric(
    "Total Sales",
    f"${df['Sales'].sum():,.0f}"
)

margin = (
    df["Profit"].sum()
    / df["Sales"].sum()
    * 100
)

c4.metric(
    "Overall Margin",
    f"{margin:.1f}%"
)


# --------------------------------------------------
# Dashboard Overview Sections
# --------------------------------------------------
st.divider()

col_left, col_right = st.columns(
    [1, 1],
    gap="medium"
)


# --------------------------------------------------
# Dashboard Navigation Guide
# --------------------------------------------------
with col_left:
    st.markdown("#### What this dashboard answers")

    st.markdown("""
    - **Global Performance** — where is the business winning and losing, geographically?
    - **Discount Impact** — are our discounts quietly destroying margin?
    - **Segments & Trends** — which customer segments are growing, and where?
    - **Operations** — does shipping speed or product mix affect profitability?
    """)

    st.info(
        "Use the navigation dropdown at the top-left of the page to explore each story. "
        "Every page has its own filters in the sidebar.",
        icon="🧭"
    )

    # Display dataset cache timestamp when available
    if cache_time:
        st.caption(
            f"➜] Dataset loaded into cache: "
            f"{cache_time.strftime('%d %b %Y, %H:%M:%S')}"
        )


# --------------------------------------------------
# Dataset Information
# --------------------------------------------------
with col_right:
    st.markdown("#### About the dataset")

    st.markdown("""
    **Source:** Global Superstore Dataset (Kaggle)\n
    **Period:** 2011 – 2014\n
    **Scope:** Consumer, Corporate & Home Office orders across 7 global markets
    """)

    with st.expander(
        "View raw data sample",
        icon="📄"
    ):
        st.dataframe(
            df.head(50),
            width="content",
            height=270
        )