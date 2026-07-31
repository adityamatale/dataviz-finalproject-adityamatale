import streamlit as st

from utils import inject_css


# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Global Superstore Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# Global Styling
# --------------------------------------------------
inject_css()


# --------------------------------------------------
# Application Branding
# --------------------------------------------------
st.logo(
    "assets/logo.png",
    size="large"
)


# --------------------------------------------------
# Sidebar Information
# --------------------------------------------------
with st.sidebar:
    st.caption("Global Superstore Analytics")
    st.caption("2011–2014 · 51,290 orders · 147 countries")
    st.divider()


# --------------------------------------------------
# Application Navigation
# --------------------------------------------------
# All dashboard pages are grouped under a single
# navigation section displayed at the top.
pg = st.navigation(
    {
        "Dashboard": [
            st.Page(
                "pages/00_home.py",
                title="Home",
                icon="🏠"
            ),
            st.Page(
                "pages/01_overview.py",
                title="Global Performance",
                icon="🌍"
            ),
            st.Page(
                "pages/02_discount_impact.py",
                title="Discount Impact",
                icon="💸"
            ),
            st.Page(
                "pages/03_segments_trends.py",
                title="Segments & Trends",
                icon="📈"
            ),
            st.Page(
                "pages/04_operations.py",
                title="Operations",
                icon="🚚"
            ),
        ]
    },
    position="top"
)


# --------------------------------------------------
# Run Application
# --------------------------------------------------
pg.run()