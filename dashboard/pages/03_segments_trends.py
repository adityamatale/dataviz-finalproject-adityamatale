import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_data, year_filter, DIVERGING_SCALE, HIGHLIGHT_COLOR, CONTEXT_GREY

df_full = load_data()

st.title("How are segments evolving over time?")

with st.sidebar:
    st.header("Filters")
    df = year_filter(df_full)

    segments = sorted(df_full['Segment'].unique())
    if 'flt_segments_p3' not in st.session_state:
        st.session_state.flt_segments_p3 = segments
    else:
        st.session_state.flt_segments_p3 = st.session_state.flt_segments_p3
    st.multiselect('Segments', segments, key='flt_segments_p3')

if not st.session_state.flt_segments_p3:
    st.warning("Select at least one segment.")
    st.stop()

df = df[df['Segment'].isin(st.session_state.flt_segments_p3)]

if df.empty:
    st.warning("No data matches current filters.")
    st.stop()

st.caption(f"{len(df):,} orders | {st.session_state.flt_year[0]}–{st.session_state.flt_year[1]} "
           f"| Segments: {', '.join(st.session_state.flt_segments_p3)}")

col_left, col_right = st.columns([1.3, 1])

# ── Chart 1: Sales trend by segment, highlight fastest grower ──────────────
with col_left:
    st.subheader("Sales trend by segment")
    trend = df.groupby(['Year', 'Segment'])['Sales'].sum().reset_index()
    growth = trend.pivot(index='Segment', columns='Year', values='Sales')

    if growth.shape[1] >= 2 and not growth.isnull().values.any():
        yrs = sorted(growth.columns)
        growth['pct_change'] = (growth[yrs[-1]] - growth[yrs[0]]) / growth[yrs[0]] * 100
        highlight = growth['pct_change'].idxmax()
    else:
        highlight = trend['Segment'].iloc[0]

    color_map = {s: (HIGHLIGHT_COLOR if s == highlight else CONTEXT_GREY)
                 for s in trend['Segment'].unique()}

    fig1 = px.line(trend, x='Year', y='Sales', color='Segment', color_discrete_map=color_map,
                   markers=True, labels={'Sales': 'Total Sales ($)', 'Year': 'Year'})
    fig1.update_traces(line=dict(width=1.5), marker=dict(size=5), showlegend=False)
    fig1.update_traces(line=dict(width=3), marker=dict(size=8), selector=dict(name=highlight))
    fig1.update_layout(
        font=dict(family='Arial', size=11), plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(showgrid=False, title='Year'), yaxis=dict(gridcolor='#EEEEEE', title='Total Sales ($)'),
        legend=dict(orientation='h', y=1.1, x=0.5, xanchor='center', title=''),
        margin=dict(l=10, r=10, t=40, b=10), height=430
    )
    st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Segment x Region sunburst ──────────────────────────────────────
with col_right:
    st.subheader("Segment × region breakdown")
    sr = (df.groupby(['Segment', 'Region'])
          .agg(Total_Sales=('Sales', 'sum'), Total_Profit=('Profit', 'sum')).reset_index())
    sr['Margin'] = sr['Total_Profit'] / sr['Total_Sales'] * 100

    fig2 = px.sunburst(
        sr, path=['Segment', 'Region'], values='Total_Sales', color='Margin',
        color_continuous_scale='Blues', labels={'Margin': 'Profit Margin (%)'}
    )
    fig2.update_traces(textinfo='label', insidetextorientation='radial',
                       marker=dict(line=dict(color='white', width=1)))
    fig2.update_layout(
        font=dict(family='Arial', size=10),
        coloraxis_colorbar=dict(title='Margin %', thickness=12, len=0.6),
        margin=dict(l=10, r=10, t=10, b=10), height=430, paper_bgcolor='white'
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.caption("Colour type: highlight (fastest-growing segment) + sequential (margin depth)")