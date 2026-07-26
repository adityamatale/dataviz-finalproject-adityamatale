import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_data, year_filter

df_full = load_data()

st.title("Does fulfillment affect profitability?")

with st.sidebar:
    st.header("Filters")
    df = year_filter(df_full)

    categories = ['All'] + sorted(df_full['Category'].unique())
    if 'flt_category_p4' not in st.session_state:
        st.session_state.flt_category_p4 = 'All'
    else:
        st.session_state.flt_category_p4 = st.session_state.flt_category_p4
    st.selectbox('Category', categories, key='flt_category_p4')

    ship_modes = sorted(df_full['Ship Mode'].unique())
    if 'flt_shipmode_p4' not in st.session_state:
        st.session_state.flt_shipmode_p4 = ship_modes
    else:
        st.session_state.flt_shipmode_p4 = st.session_state.flt_shipmode_p4
    st.multiselect('Ship Mode', ship_modes, key='flt_shipmode_p4')

if st.session_state.flt_category_p4 != 'All':
    df = df[df['Category'] == st.session_state.flt_category_p4]
if not st.session_state.flt_shipmode_p4:
    st.warning("Select at least one ship mode.")
    st.stop()
df = df[df['Ship Mode'].isin(st.session_state.flt_shipmode_p4)]

if df.empty:
    st.warning("No data matches current filters.")
    st.stop()

st.caption(f"{len(df):,} orders | {st.session_state.flt_year[0]}–{st.session_state.flt_year[1]} "
           f"| Category: {st.session_state.flt_category_p4}")

col_left, col_right = st.columns([1, 1.2])

# ── Chart 1: Ship Mode vs order value ───────────────────────────────────────
with col_left:
    st.subheader("Order value by ship mode")
    p95 = df['Sales'].quantile(0.95)
    df_cap = df[df['Sales'] <= p95]

    color_map = {sm: ('#2E75B6' if sm == 'Standard Class' else '#AAAAAA')
                 for sm in df_cap['Ship Mode'].unique()}

    fig1 = px.box(df_cap, x='Sales', y='Ship Mode', color='Ship Mode',
                  color_discrete_map=color_map, points=False,
                  labels={'Sales': 'Order Value ($, capped 95th pct)', 'Ship Mode': ''})
    fig1.update_layout(
        font=dict(family='Arial', size=11), plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(gridcolor='#EEEEEE'), yaxis=dict(showgrid=False),
        showlegend=False, margin=dict(l=10, r=10, t=10, b=10), height=420
    )
    st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Sub-category profit waterfall ──────────────────────────────────
with col_right:
    st.subheader("Sub-category profit contribution")
    sub_profit = df.groupby('Sub-Category')['Profit'].sum().reset_index().sort_values('Profit')

    if len(sub_profit) > 0:
        labels = sub_profit['Sub-Category'].tolist() + ['Total']
        values = sub_profit['Profit'].tolist() + [sub_profit['Profit'].sum()]
        measures = ['relative'] * len(sub_profit) + ['total']

        trace = go.Waterfall(
            x=labels, y=values, measure=measures,
            connector=dict(line=dict(color='#CCCCCC', width=1, dash='dot')),
            increasing=dict(marker_color='#2E75B6'),
            decreasing=dict(marker_color='#E07B39'),
            totals=dict(marker_color='#4D4D4D'),
            texttemplate='%{y:$,.0f}', textposition='outside', textfont=dict(size=9)
        )
        fig2 = go.Figure(data=[trace])
        fig2.update_layout(
            font=dict(family='Arial', size=10), plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(tickangle=-45, showgrid=False), yaxis=dict(gridcolor='#EEEEEE', title='Profit ($)'),
            showlegend=False, margin=dict(l=10, r=10, t=10, b=90), height=420
        )
        st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.caption("Colour type: highlight (Standard Class) + categorical (profit direction: blue=gain, orange=loss)")