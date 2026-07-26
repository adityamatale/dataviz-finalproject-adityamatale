import streamlit as st

st.set_page_config(
    page_title="Global Superstore Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Light global polish — carried onto every page automatically
st.markdown("""
<style>
.block-container { padding-top: 1.5rem; padding-bottom: 0; }
[data-testid='metric-container'] {
    background: #F8F9FA; border: 1px solid #E9ECEF;
    padding: 1rem; border-radius: 8px;
}
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

pg = st.navigation([
    st.Page("pages/01_overview.py",
            title="How is global performance right now?",       icon="🌍"),
    st.Page("pages/02_discount_impact.py",
            title="Are discounts destroying our margins?",      icon="💸"),
    st.Page("pages/03_segments_trends.py",
            title="How are segments evolving over time?",       icon="📈"),
    st.Page("pages/04_operations.py",
            title="Does fulfillment affect profitability?",     icon="🚚"),
])
pg.run()