import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. VIEWPORT SETTINGS
st.set_page_config(page_title="Simple Investor Hub", layout="wide")
st.title("🎯 Simple Investor Hub & Strategy Lab")
st.write("Track favorite stocks, check if it's a good time to buy, and project long-term wealth growth.")

# Initialize a clean user tracking registry inside memory cache
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["NVDA", "VOO", "AAPL"]

# 2. SIDEBAR CONTROLS & CURRENCY MIXER
st.sidebar.header("🌍 Currency Settings")
currency = st.sidebar.selectbox(
    "Display Currency:",
    options=["USD ($)", "EUR (€)", "GBP (£)", "CAD ($)"]
)

# Precise currency multipliers mapped for June 20, 2026
currency_symbols = {"USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£", "CAD ($)": "$"}
exchange_rates = {"USD ($)": 1.0, "EUR (€)": 0.872, "GBP (£)": 0.756, "CAD ($)": 1.415}

fx_rate = exchange_rates[currency]
symbol = currency_symbols[currency]

st.sidebar.markdown("---")
st.sidebar.header("Add Assets to Hub")
new_ticker = st.sidebar.text_input("Enter Ticker Symbol (e.g. MSFT, TSLA, BTC-USD):").upper().strip()

if st.sidebar.button("➕ Add to Dashboard") and new_ticker:
    if new_ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_ticker)
        st.toast(f"Added {new_ticker} to tracking dashboard!", icon="✅")

if st.sidebar.button("🗑️ Reset Watchlist"):
    st.session_state.watchlist = ["NVDA", "VOO", "AAPL"]
    st.rerun()

# 3. GLOBAL LIVE DATA PROCESSING ENGINE
@st.cache_data(ttl=1800)
def fetch_hub_data(tickers):
    # Set historical window fixed down from June 20, 2026
    end = datetime(2026, 6, 20)
    start = end - timedelta(days=730)
    try:
        data = yf.download(tickers, start=start, end=end)['Close']
        if len(tickers) == 1:
            data = pd.DataFrame({tickers: data})
        return data
    except Exception:
        return pd.DataFrame()

price_matrix = fetch_hub_data(st.session_state.watchlist)

# ==========================================
# MODULE 1: INTERACTIVE ASSET MATRIX RADAR
# ==========================================
st.header("📋 1. Simple Risk-Reward Dashboard")

if price_matrix.empty:
    st.warning("Please enter valid ticker symbols in the left sidebar configuration panel.")
else:
    # Inform users exactly where data scales
    latest_market_date = price_matrix.index[-1].strftime('%B %d, %Y')
    st.info(f"显示最新市场价格数据: **{latest_market_date}** (Traditional stock markets are closed on weekends).")

    for ticker in st.session_state.watchlist:
        if ticker in price_matrix.columns:
            series = price_matrix[ticker].dropna()
            if len(series) > 2:
                returns = series.pct_change().dropna()
                volatility = returns.std() * np.sqrt(252) * 100
                
                # Convert raw prices by our live FX rate multiplier
                current_val = float(series.iloc[-1]) * fx_rate
                prev_val = float(series.iloc[-2]) * fx_rate
                day_change = ((current_val - prev_val) / prev_val) * 100
                
                # Simple Risk Classification
                if volatility < 20:
                    badge = "🟢 Low Risk (Steady / Slow)"
                elif volatility < 40:
                    badge = "🟡 Medium Risk (Moderate Swings)"
                else:
                    badge = "🔴 High Risk (Fast / Bumpy)"
                
                with st.container():
                    c_tick, c_price, c_risk = st.columns([2, 3, 3])
                    c_tick.write(f"### **{ticker}**\n{badge}")
                    c_price.metric("Current Price", f"{symbol}{current_val:,.2f}", delta=f"{day_change:.2f}% Today")
                    c_risk.metric("Historical Price Jumpiness", f"{volatility:.1f}%", help="Higher % means a bumpy ride with sudden price movements.")
                    st.markdown("---")

# ==========================================
# MODULE 2: BALANCED ENTRY STRATEGY SCANNER
# ==========================================
st.header("⚡ 2. Strategy Check: Is it a good time to buy?")
st.write("This scans the asset's overall momentum over the past **50 days** versus the long-term trend line of **200 days**.")

selected_strat_stock = st.selectbox("Select a stock to evaluate:", st.session_state.watchlist)

if selected_strat_stock and not price_matrix.empty and selected_strat_stock in price_matrix.columns:
    strat_df = pd.DataFrame({"Close": price_matrix[selected_strat_stock].dropna()})
    
    # Generate smoothed rolling baseline indicators
    strat_df['SMA_50'] = strat_df['Close'].rolling(window=50).mean()
    strat_df['SMA_200'] = strat_df['Close'].rolling(window=200).mean()
    
    latest_row = strat_df.iloc[-1]
    
    # Multiply charts by selected currency variables
    price_plot = strat_df['Close'] * fx_rate
    sma50_plot = strat_df['SMA_50'] * fx_rate
    sma200_plot = strat_df['SMA_200'] * fx_rate

    if latest_row['SMA_50'] > latest_row['SMA_200']:
        st.success(f"🟢 **Bullish Momentum:** {selected_strat_stock} is historically in an **Upward Trend**. Long-term demand remains healthy.")
    else:
        st.error(f"🔴 **Bearish Caution:** {selected_strat_stock} is historically in a **Downward Trend**. Prices might continue to slide short-term.")

    # Render interactive plot mapping trends
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strat_df.index, y=price_plot, name='Converted Market Price', line=dict(color='#00CC96', width=1.5)))
    fig.add_trace(go.Scatter(x=strat_df.index, y=sma50_plot, name='50-Day Line (Recent Trend)', line=dict(color='#FECB52', width=2)))
    fig.add_trace(go.Scatter(x=strat_df.index, y=sma200_plot, name='200-Day Line (Long-Term Base)', line=dict(color='#EF553B', width=2)))
    
    fig.update_layout(template="plotly_dark", xaxis_title="Date", yaxis_title=f"Price ({currency})", margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# MODULE 3: THE COMPOUNDING INTEREST LAB
# ==========================================
st.header("⏳ 3. Long-Term Wealth Compound Planner")
st.write("See how regular monthly investments can grow your savings account over time.")

col_input1, col_input2, col_input3 = st.columns(3)
init_cash = col_input1.number_input(f"Starting Cash ({symbol}):", value=1000)
monthly_add = col_input2.number_input(f"Monthly Addition ({symbol}):", value=200)
horizon_years = col_input3.slider("How many years do you want to hold?", min_value=1, max_value=30, value=10)

# Extract standard baseline growth values
annual_return_pct = 10.0
if not price_matrix.empty and selected_strat_stock in price_matrix.columns:
    series = price_matrix[selected_strat_stock].dropna()
    if len(series) > 252:
        annual_return_pct = float(((series.iloc[-1] / series.iloc[0]) ** (252 / len(series)) - 1) * 100)
        annual_return_pct = max(min(annual_return_pct, 35.0), -5.0)

st.info(f"Using **{selected_strat_stock}'s** historical trend return of **{annual_return_pct:.1f}%** per year to run projection modeling.")

# Run calculation engine
months = horizon_years * 12
monthly_rate = (1 + (annual_return_pct / 100)) ** (1/12) - 1

balance = init_cash
total_invested = init_cash
timeline_data = []

for m in range(1, months + 1):
    balance = (balance + monthly_add) * (1 + monthly_rate)
    total_invested += monthly_add
    if m % 12 == 0:
        timeline_data.append({
            "Year": m // 12,
            "Your Invested Cash": total_invested,
            "Total Accumulated Value": balance
        })

df_projection = pd.DataFrame(timeline_data)

if not df_projection.empty:
    fig_proj = go.Figure()
    fig_proj.add_trace(go.Bar(x=df_projection["Year"], y=df_projection["Your Invested Cash"], name="Your Saved Cash", marker_color="#636EFA"))
    fig_proj.add_trace(go.Scatter(x=df_projection["Year"], y=df_projection["Total Accumulated Value"], name="Compounded Growth", line=dict(color="#00CC96", width=3)))
    fig_proj.update_layout(template="plotly_dark", xaxis_title="Years", yaxis_title=f"Total Value ({symbol})", barmode='group')
    st.plotly_chart(fig_proj, use_container_width=True)
    
    col_res1, col_res2 = st.columns(2)
    col_res1.metric("Your Net Cash Injected", f"{symbol}{total_invested:,.2f}")
    col_res2.metric("Projected Total Account Ending Balance", f"{symbol}{balance:,.2f}", delta=f"{symbol}{balance - total_invested:,.2f} Earned from Compounding Interest")
