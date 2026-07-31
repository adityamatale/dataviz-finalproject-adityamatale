import datetime
from pathlib import Path

import pandas as pd
import pycountry
import streamlit as st


# --------------------------------------------------
# Cache Timestamp Tracking
# --------------------------------------------------
_last_cache_load = None


def get_cache_time():
    return _last_cache_load


# --------------------------------------------------
# Data Loading
# --------------------------------------------------
@st.cache_data
def load_data():
    global _last_cache_load

    _last_cache_load = datetime.datetime.now()

    path = Path(__file__).parent / "data" / "global_superstore_cleaned.csv"
    return pd.read_csv(path)


# --------------------------------------------------
# Chart Styling Constants
# --------------------------------------------------
# Shared CVD-safe color palettes for charts
DIVERGING_SCALE = [[0, "#E07B39"], [0.5, "#F5F5F5"], [1, "#2E75B6"]]

HIGHLIGHT_COLOR = "#2E75B6"
CONTEXT_GREY = "#AAAAAA"
CATEGORY_COLORS = {"Furniture": "#2E75B6", "Office Supplies": "#E07B39", "Technology": "#4DAF4A"}

# Neutral font color compatible with light and dark themes
CHART_FONT_COLOR = "#8A8A8A"


# --------------------------------------------------
# Plotly Theme Helper
# --------------------------------------------------
def themed_layout(fig, **kwargs):
    """Apply transparent backgrounds and adaptive chart styling."""

    defaults = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=11, color=CHART_FONT_COLOR)
    )

    defaults.update(kwargs)
    fig.update_layout(**defaults)

    return fig


# --------------------------------------------------
# Streamlit State Helpers
# --------------------------------------------------
def keep_alive(key, default):
    """Initialize session state values and preserve them across page changes."""

    if key not in st.session_state:
        st.session_state[key] = default
    else:
        st.session_state[key] = st.session_state[key]


def year_filter(df, key="flt_year"):
    """Apply year range filtering using Streamlit session state."""

    years = sorted(df["Year"].unique())

    keep_alive(key, (years[0], years[-1]))

    st.slider("📅 Year range", years[0], years[-1], key=key)

    lo, hi = st.session_state[key]

    return df[df["Year"].between(lo, hi)]


# --------------------------------------------------
# Application Styling
# --------------------------------------------------
def inject_css():
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1rem; padding-bottom: 0.5rem; }
        footer { visibility: hidden; }

        [data-testid='stMetric'] {
            background: var(--secondary-background-color);
            border: 1px solid rgba(128,128,128,0.25);
            padding: 0.7rem 0.9rem;
            border-radius: 10px;
        }

        [data-testid='stMetricLabel'] { font-size: 0.8rem; }

        h1 {
            font-size: 2rem !important;
            margin-top: 0.8rem !important;
            margin-bottom: 0.1rem !important;
        }

        h3 {
            margin-top: 0.3rem !important;
            margin-bottom: 0.3rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# --------------------------------------------------
# Geographic Utilities
# --------------------------------------------------
def add_country_iso3(df, country_col="Country"):
    """Add ISO3 country codes required for Plotly maps."""

    def get_iso3(country):
        try:
            return pycountry.countries.lookup(country).alpha_3

        except LookupError:
            manual_map = {
                "cote d'ivoire": "CIV",
                "ivory coast": "CIV",
                "south korea": "KOR",
                "north korea": "PRK",
                "russia": "RUS",
                "taiwan": "TWN",
                "venezuela": "VEN"
            }

            return manual_map.get(country.lower())

    df["ISO3"] = df[country_col].apply(get_iso3)

    return df


# --------------------------------------------------
# Insight Generators
# --------------------------------------------------
def generate_margin_insight(agg):
    """Generate insight for region-category margin analysis."""

    worst = agg.loc[agg["Margin"].idxmin()]
    best = agg.loc[agg["Margin"].idxmax()]

    loss_count = (agg["Margin"] < 0).sum()
    total_pairs = len(agg)

    if loss_count == 0:
        return f"All {total_pairs} region-category combinations are profitable."

    if loss_count == 1:
        return f"{worst.Region} is the only region-category combination losing money on {worst.Category} ({worst.Margin:.1f}% margin)."

    return f"{loss_count} out of {total_pairs} region-category combinations are loss-making. Worst: {worst.Region} ({worst.Category}) at {worst.Margin:.1f}% margin."


def generate_country_insight(country_agg):
    """Generate insight for country profitability map."""

    worst = country_agg.loc[country_agg["Margin"].idxmin()]
    best = country_agg.loc[country_agg["Margin"].idxmax()]

    top_sales = country_agg.nlargest(8, "Total_Sales")

    if worst["Margin"] < 0 and worst["Total_Sales"] > 0:
        return ( 
            f"{worst.Country} loses money with " 
            f"\${worst.Total_Sales:,.0f} in sales " 
            f"({worst.Margin:.1f}% margin, " 
            f"\${worst.Total_Profit:,.0f} profit). \n" 
            f"{best.Country} posts the strongest margin " 
            f"at {best.Margin:.1f}%." 
            )

    return f"{best.Country} is the most profitable market with a {best.Margin:.1f}% margin"


def generate_discount_margin_insight(agg):
    """Generate insight for discount versus margin analysis."""

    worst = agg.loc[agg["Margin"].idxmin()]
    negative = agg[agg["Margin"] < 0]

    if not negative.empty:
        return f"{worst['Sub-Category']} has the weakest profitability, with an average discount of {worst['Avg_Discount']:.0%} and a profit margin of {worst['Margin']:.1f}%."

    if not agg[agg["Avg_Discount"] > 0.2].empty:
        return f"Discount pressure is visible beyond 20%. {worst['Sub-Category']} has the lowest margin at {worst['Margin']:.1f}%."

    return f"All sub-categories remain profitable. {worst['Sub-Category']} has the lowest margin at {worst['Margin']:.1f}%."


def generate_discount_band_insight(agg):
    """Generate insight for quantity and discount matrix."""

    if agg.empty:
        return "No data available for the selected filters."

    best = agg.loc[agg["Margin"].idxmax()]
    worst = agg.loc[agg["Margin"].idxmin()]

    low_discount = agg[agg["Disc_Bin"].isin(["0-10%", "10-20%"])]["Margin"].mean()
    high_discount = agg[agg["Disc_Bin"].isin(["30-50%", "50%+"])]["Margin"].mean()

    if high_discount < low_discount:
        return f"Margins fall sharply once discounts exceed 30%. The weakest segment is {worst['Disc_Bin']} discounts with {worst['Qty_Bin']} orders ({worst['Margin']:.1f}% margin)."

    return f"The strongest segment is {best['Disc_Bin']} discounts with {best['Qty_Bin']} orders ({best['Margin']:.1f}% margin)."


def generate_segment_growth_insight(trend):
    """Generate insight for segment sales growth."""

    growth = trend.pivot(index="Segment", columns="Year", values="Sales")
    years = sorted(growth.columns)

    if len(years) < 2:
        return "At least two years of data are required to compare segment growth."

    growth["Growth"] = (growth[years[-1]] - growth[years[0]]) / growth[years[0]] * 100

    fastest = growth["Growth"].idxmax()
    fastest_pct = growth.loc[fastest, "Growth"]

    largest = trend[trend["Year"] == years[-1]].sort_values("Sales", ascending=False).iloc[0]["Segment"]

    if fastest == largest:
        return f"{fastest} remains the largest segment and also recorded the strongest growth (+{fastest_pct:.0f}%) since {years[0]}."

    return f"{fastest} grew fastest (+{fastest_pct:.0f}% since {years[0]}), while {largest} remains the largest segment by total sales."


def generate_segment_region_insight(sr):
    """Generate insight for segment-region profitability."""

    if sr.empty:
        return "No data available for the selected filters."

    best = sr.loc[sr["Margin"].idxmax()]
    worst = sr.loc[sr["Margin"].idxmin()]
    largest = sr.loc[sr["Total_Sales"].idxmax()]

    return f"{largest['Segment']} generates the highest sales volume, while {best['Region']} in {best['Segment']} delivers the strongest margin ({best['Margin']:.1f}%). The weakest combination is {worst['Region']} in {worst['Segment']} ({worst['Margin']:.1f}% margin)."


def generate_subcategory_volatility_insight(sub_year):
    """Generate insight for sub-category sales volatility."""

    pivot = sub_year.pivot(index="Sub-Category", columns="Year", values="Sales")

    cv = pivot.std(axis=1) / pivot.mean(axis=1)

    volatile, stable = cv.idxmax(), cv.idxmin()

    return f"{volatile} shows the largest year-to-year sales swings (CV {cv[volatile]:.2f}), while {stable} remains the most predictable sub-category (CV {cv[stable]:.2f})."


def generate_shipmode_insight(df):
    """Generate insight for shipping mode order values."""

    avg = df.groupby("Ship Mode")["Sales"].median().sort_values(ascending=False)

    return f"{avg.index[0]} has the highest typical order value with a median order size of ${avg.iloc[0]:,.0f}."


def generate_profit_contribution_insight(sub_profit):
    """Generate insight for sub-category profit contribution."""

    best = sub_profit.loc[sub_profit["Profit"].idxmax()]
    worst = sub_profit.loc[sub_profit["Profit"].idxmin()]

    total_profit = sub_profit["Profit"].sum()
    best_share = best["Profit"] / total_profit * 100 if total_profit != 0 else 0

    return f"{best['Sub-Category']} contributes the most profit (${best['Profit']:,.0f}), accounting for {best_share:.1f}% of total profit. {worst['Sub-Category']} is the weakest contributor."