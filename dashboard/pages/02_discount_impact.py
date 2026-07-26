import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_data, year_filter, DIVERGING_SCALE, CATEGORY_COLORS

df_full = load_data()

st.title("Are discounts destroying our margins?")

with st.sidebar:
    st.header("Filters")
    df = year_filter(df_full)

    categories = ['All'] + sorted(df_full['Category'].unique())
    if 'flt_category_p2' not in st.session_state:
        st.session_state.flt_category_p2 = 'All'
    else:
        st.session_state.flt_category_p2 = st.session_state.flt_category_p2
    st.selectbox('Category', categories, key='flt_category_p2')

    if 'flt_discount_p2' not in st.session_state:
        st.session_state.flt_discount_p2 = (0.0, 1.0)
    else:
        st.session_state.flt_discount_p2 = st.session_state.flt_discount_p2
    st.slider('Discount range', 0.0, 1.0, key='flt_discount_p2')

if st.session_state.flt_category_p2 != 'All':
    df = df[df['Category'] == st.session_state.flt_category_p2]
lo, hi = st.session_state.flt_discount_p2
df = df[df['Discount'].between(lo, hi)]

if df.empty:
    st.warning("No data matches current filters.")
    st.stop()

st.caption(f"{len(df):,} orders | {st.session_state.flt_year[0]}–{st.session_state.flt_year[1]} "
           f"| Category: {st.session_state.flt_category_p2} | Discount: {lo:.0%}–{hi:.0%}")

col_left, col_right = st.columns([1.2, 1])

# ── Chart 1: Discount vs Margin bubble (by sub-category) ───────────────────
with col_left:
    st.subheader("Discount vs profit margin by sub-category")
    agg = (df.groupby(['Sub-Category', 'Category'])
           .agg(Avg_Discount=('Discount', 'mean'), Total_Sales=('Sales', 'sum'),
                Total_Profit=('Profit', 'sum')).reset_index())
    agg['Margin'] = agg['Total_Profit'] / agg['Total_Sales'] * 100

    fig1 = px.scatter(
        agg, x='Avg_Discount', y='Margin', size='Total_Sales', color='Category',
        color_discrete_map=CATEGORY_COLORS, hover_name='Sub-Category',
        labels={'Avg_Discount': 'Avg Discount', 'Margin': 'Profit Margin (%)'}, size_max=50
    )
    fig1.add_hline(y=0, line_dash='dash', line_color='#888888', line_width=1.5)
    fig1.update_traces(marker=dict(opacity=0.8, line=dict(width=0.5, color='white')))
    fig1.update_layout(
        font=dict(family='Arial', size=11), plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(tickformat='.0%', gridcolor='#EEEEEE', title='Avg Discount'),
        yaxis=dict(gridcolor='#EEEEEE', title='Profit Margin (%)'),
        legend=dict(orientation='h', y=1.1, x=0.5, xanchor='center', title=''),
        margin=dict(l=10, r=10, t=40, b=10), height=430
    )
    st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Quantity x Discount margin matrix ──────────────────────────────
with col_right:
    st.subheader("Quantity × discount margin matrix")
    d2 = df.copy()
    d2['Qty_Bin'] = pd.cut(d2['Quantity'], bins=[0, 3, 6, 9, 14],
                           labels=['1-3', '4-6', '7-9', '10-14'])
    d2['Disc_Bin'] = pd.cut(d2['Discount'], bins=[-0.01, 0.1, 0.2, 0.3, 0.5, 1.0],
                            labels=['0-10%', '10-20%', '20-30%', '30-50%', '50%+'])
    agg2 = (d2.groupby(['Qty_Bin', 'Disc_Bin'], observed=True)
            .agg(Total_Sales=('Sales', 'sum'), Total_Profit=('Profit', 'sum')).reset_index())
    if not agg2.empty:
        agg2['Margin'] = agg2['Total_Profit'] / agg2['Total_Sales'] * 100

        fig2 = px.scatter(
            agg2, x='Disc_Bin', y='Qty_Bin', size='Total_Sales', color='Margin',
            color_continuous_scale=DIVERGING_SCALE, color_continuous_midpoint=0,
            range_color=[-40, 40], labels={'Disc_Bin': 'Discount Band', 'Qty_Bin': 'Quantity'},
            size_max=45
        )
        fig2.update_traces(marker=dict(line=dict(width=0.5, color='white'), opacity=0.9))
        fig2.update_layout(
            font=dict(family='Arial', size=11), plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(showgrid=False, title='Discount Band'),
            yaxis=dict(gridcolor='#EEEEEE', title='Quantity'),
            coloraxis_colorbar=dict(title='Margin %', thickness=12, len=0.6),
            margin=dict(l=10, r=10, t=40, b=10), height=430
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Not enough data in this filter combination for the matrix view.")

st.divider()
st.caption("Colour type: diverging (margin above/below breakeven) | Size: total sales volume")