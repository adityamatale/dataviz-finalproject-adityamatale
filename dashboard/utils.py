import pandas as pd
import streamlit as st
from pathlib import Path


@st.cache_data
def load_data():
    """Cached loader — shared across every page so the CSV is read from disk once."""
    path = Path(__file__).parent / 'data' / 'global_superstore_cleaned.csv'
    df = pd.read_csv(path)
    return df


# CVD-safe shared palette — used consistently across every page/chart
DIVERGING_SCALE = [[0, '#E07B39'], [0.5, '#F5F5F5'], [1, '#2E75B6']]   # orange -> white -> blue
HIGHLIGHT_COLOR = '#2E75B6'
CONTEXT_GREY = '#DDDDDD'
CATEGORY_COLORS = {
    'Furniture': '#2E75B6',
    'Office Supplies': '#E07B39',
    'Technology': '#4DAF4A'
}


def year_filter(df, key='flt_year'):
    """Shared year-range slider — used identically on every page."""
    years = sorted(df['Year'].unique())
    if key not in st.session_state:
        st.session_state[key] = (years[0], years[-1])
    else:
        st.session_state[key] = st.session_state[key]   # keep alive across page switches

    st.slider('Year range', years[0], years[-1], key=key)
    lo, hi = st.session_state[key]
    return df[df['Year'].between(lo, hi)]