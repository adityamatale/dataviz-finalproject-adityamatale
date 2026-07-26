import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_data, year_filter, DIVERGING_SCALE

df_full = load_data()

st.title("How is global performance right now?")

# ── Sidebar filters ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    df = year_filter(df_full)   # shared year-range slider

    markets = ['All'] + sorted(df_full['Market'].unique())
    if 'flt_market' not in st.session_state:
        st.session_state.flt_market = 'All'
    else:
        st.session_state.flt_market = st.session_state.flt_market
    st.selectbox('Market', markets, key='flt_market')

if st.session_state.flt_market != 'All':
    df = df[df['Market'] == st.session_state.flt_market]

if df.empty:
    st.warning("No data matches current filters.")
    st.stop()

st.caption(f"{len(df):,} orders shown | {st.session_state.flt_year[0]}–{st.session_state.flt_year[1]} "
           f"| Market: {st.session_state.flt_market}")

# ── KPI row — 5-second test ─────────────────────────────────────────────────
total_sales = df['Sales'].sum()
total_profit = df['Profit'].sum()
margin = total_profit / total_sales * 100
full_margin = df_full['Profit'].sum() / df_full['Sales'].sum() * 100

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Sales", f"${total_sales:,.0f}")
k2.metric("Total Profit", f"${total_profit:,.0f}")
k3.metric("Profit Margin", f"{margin:.1f}%", f"{margin - full_margin:+.1f}pp vs overall")
k4.metric("Orders", f"{len(df):,}")

st.divider()

col_left, col_right = st.columns([1, 1.2])

# ── Chart 1: Region x Category margin heatmap ───────────────────────────────
with col_left:
    st.subheader("Region × Category profit margin")
    agg = (df.groupby(['Region', 'Category'])
           .agg(Total_Sales=('Sales', 'sum'), Total_Profit=('Profit', 'sum'))
           .reset_index())
    agg['Margin'] = agg['Total_Profit'] / agg['Total_Sales'] * 100
    pivot = agg.pivot(index='Region', columns='Category', values='Margin')
    pivot = pivot.loc[pivot.min(axis=1).sort_values().index]

    fig1 = px.imshow(
        pivot, color_continuous_scale=DIVERGING_SCALE, color_continuous_midpoint=0,
        aspect='auto', text_auto='.1f', labels={'color': 'Margin %'}
    )
    fig1.update_traces(texttemplate='%{z:.1f}%', textfont=dict(size=10), xgap=2, ygap=2)
    fig1.update_layout(
        font=dict(family='Arial', size=11), plot_bgcolor='white', paper_bgcolor='white',
        coloraxis_showscale=False, margin=dict(l=10, r=10, t=10, b=10), height=420,
        xaxis=dict(title=''), yaxis=dict(title='')
    )
    st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Country margin choropleth ───────────────────────────────────────
with col_right:
    st.subheader("Profit margin by country")
    country_agg = (df.groupby('Country')
                   .agg(Total_Sales=('Sales', 'sum'), Total_Profit=('Profit', 'sum'))
                   .reset_index())
    country_agg['Margin'] = country_agg['Total_Profit'] / country_agg['Total_Sales'] * 100

    fig2 = px.choropleth(
        country_agg, locations='Country', locationmode='country names',
        color='Margin', color_continuous_scale=DIVERGING_SCALE, color_continuous_midpoint=0,
        range_color=[-50, 50], hover_name='Country',
        hover_data={'Total_Sales': ':,.0f', 'Margin': ':.1f', 'Country': False},
        labels={'Margin': 'Profit Margin (%)'}, projection='natural earth'
    )
    fig2.update_layout(
        font=dict(family='Arial', size=11),
        geo=dict(showframe=False, showcoastlines=False, bgcolor='white'),
        coloraxis_colorbar=dict(title='Margin %', thickness=12, len=0.6),
        margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor='white', height=420
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.caption("Source: Global Superstore Dataset | Colour type: diverging (margin above/below breakeven)")