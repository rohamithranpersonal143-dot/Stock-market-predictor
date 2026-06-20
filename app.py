import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. VIEWPORT SETTINGS
st.set_page_config(page_title="Ultimate Investor Hub", layout="wide")
st.title("🛡️ Universal Investor Hub & Strategy Lab")
st.write("Track custom tickers, backtest moving average entry strategies, and simulate compounding positions in one portal.")

# Initialize a clean user tracking registry inside Streamlit memory cache
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["NVDA", "VOO", "AAPL"]

# 2. UNIVERSAL SIDEBAR CONTROL PANEL
st.sidebar.header("Add Assets to Hub")
new_ticker = st.sidebar.text_input("Enter Ticker Symbol (e.g. MSFT, TSLA, BTC-USD):").upper().strip()

if st.sidebar.button("➕ Add to Dashboard") and new_ticker:
    if new_ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_ticker)
        st.toast(f"Added {new_ticker} to tracking dashboard!", icon="✅")

if st.sidebar.button("🗑️ Clear Watchlist"):
    st.session_state.watchlist = ["VOO"]
    st.rerun()

# 3. GLOBAL LIVE DATA PROCESSING ENGINE
@st.cache_data(ttl=1800)
def fetch_hub_data(tickers, days_back=730):
    end = datetime.now()
    start = end - timedelta(days=days_back)
    try:
        # Use clean closing price arrays to avoid parsing bugs
        data = yf.download(tickers, start=start, end=end)['Close']
        if len(tickers) == 1:
            data = pd.DataFrame({tickers[0]: data})
        return data
    except Exception:
        return pd.DataFrame()

price_matrix = fetch_hub_data(st.session_state.watchlist)

# ==========================================
# MODULE 1: UNIVERSAL PORTFOLIO MATRIX RADAR
# ==========================================
st.header("📋 1. Live Asset Risk-Reward Radar")

if price_matrix.empty:
    st.warning("Please enter valid ticker symbols in the left sidebar configuration panel.")
else:
    for ticker in st.session_state.watchlist:
        if ticker in price_matrix.columns:
            series = price_matrix[ticker].dropna()
            if len(series) > 2:
                returns = series.pct_change().dropna()
                volatility = returns.std() * np.sqrt(252) * 100
                current_val = series.iloc[-1]
                prev_val = series.iloc[-2]
                day_change = ((current_val - prev_val) / prev_val) * 100
                
                # Determine categorical risk tier coloring badges dynamically
                if volatility < 20:
                    badge, color = "🟢 Low Risk", "normal"
                elif volatility < 40:
                    badge, color = "🟡 Med Risk", "off"
                else:
                    badge, color = "🔴 High Risk", "inverse"
                
                with st.container():
                    c_badge, c_tick, c_price, c_risk = st.columns(4)
                    c_badge.write(f"### {badge}")
                    c_tick.write(f"### **{ticker}**")
                    c_price.metric("Live Close Value", f"${current_val:.2f}", delta=f"{day_change:.2f}%")
                    c_risk.metric("Annual Volatility Swing", f"{volatility:.1f}%")
                    st.markdown("---")

# ==========================================
# MODULE 2: ALGORITHMIC STRATEGY LAB
# ==========================================
st.header("⚡ 2. Strategic Moving Average Entry Scanner")
st.write("This tool helps you buy stocks at strong entry points by tracking momentum changes via the **Golden Cross / Death Cross** strategy.")

selected_strat_stock = st.selectbox("Choose stock to run strategy on:", st.session_state.watchlist)

if selected_strat_stock and not price_matrix.empty and selected_strat_stock in price_matrix.columns:
    strat_df = pd.DataFrame({"Close": price_matrix[selected_strat_stock].dropna()})
    
    # Calculate rolling indicators
    strat_df['SMA_50'] = strat_df['Close'].rolling(window=50).mean()
    strat_df['SMA_200'] = strat_df['Close'].rolling(window=200).mean()
    
    # Locate exact technical indicators to display status tags
    latest_row = strat_df.iloc[-1]
    
    col_strat_info, col_strat_status = st.columns([2, 1])
    
    with col_strat_info:
        st.write("""
        * **Golden Cross (🟢 BUY Indicator):** The fast 50-day line crosses *above* the slow 200-day line. This signals massive upward momentum.
        * **Death Cross (🔴 SELL Indicator):** The fast 50-day line crosses *below* the slow 200-day line. This signals a defensive exit.
        """)
        
    with col_strat_status:
        if latest_row['SMA_50'] > latest_row['SMA_200']:
            st.success(f"**Strategy Status for {selected_strat_stock}:** BULLISH TREND (50 SMA is above 200 SMA)")
        else:
            st.error(f"**Strategy Status for {selected_strat_stock}:** BEARISH TREND (50 SMA is below 200 SMA)")

    # Render interactive plot mapping trends
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strat_df.index, y=strat_df['Close'], name='Market Price', line=dict(color='#00CC96', width=1.5)))
    fig.add_trace(go.Scatter(x=strat_df.index, y=strat_df['SMA_50'], name='50-Day Trendline', line=dict(color='#FECB52', width=2)))
    fig.add_trace(go.Scatter(x=strat_df.index, y=strat_df['SMA_200'], name='200-Day Trendline', line=dict(color='#EF553B', width=2)))
    
    fig.update_layout(template="plotly_dark", xaxis_title="Timeline", yaxis_title="Price ($)", margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# MODULE 3: THE STRATEGIC DCA ACCUMULATOR
# ==========================================
st.header("⏳ 3. Position Wealth Accumulator Simulation")
st.write("Simulate long-term Dollar-Cost Averaging (DCA) to see how compounding changes your position value over time.")

col_input1, col_input2, col_input3 = st.columns(3)
init_cash = col_input1.number_input("Starting Capital ($):", value=1000)
monthly_add = col_input2.number_input("Monthly Contribution ($):", value=200)
horizon_years = col_input3.slider("Accumulation Timeline (Years)", min_value=1, max_value=30, value=10)

# Extract returns from target selection asset profile
annual_return_pct = 10.0
if not price_matrix.empty and selected_strat_stock in price_matrix.columns:
    series = price_matrix[selected_strat_stock].dropna()
    if len(series) > 252:
        # Pull geometric compounded growth returns baseline value
        annual_return_pct = float(((series.iloc[-1] / series.iloc[0]) ** (252 / len(series)) - 1) * 100)
        # Cap excessive outliers to keep financial projections realistic
        annual_return_pct = max(min(annual_return_pct, 40.0), -10.0)

st.info(f"Using **{selected_strat_stock}'s** adjusted annualized return baseline of **{annual_return_pct:.1f}%** for projections.")

# Compute continuous monthly compound math sequences
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
            "Total Contributions": total_invested,
            "Compounded Wealth": balance
        })

df_projection = pd.DataFrame(timeline_data)

if not df_projection.empty:
    fig_proj = go.Figure()
    fig_proj.add_trace(go.Bar(x=df_projection["Year"], y=df_projection["Total Contributions"], name="Your Cash Injected", marker_color="#636EFA"))
    fig_proj.add_trace(go.Scatter(x=df_projection["Year"], y=df_projection["Compounded Wealth"], name="Total Portfolio Balance", line=dict(color="#00CC96", width=3)))
    fig_proj.update_layout(template="plotly_dark", xaxis_title="Years Accumulated", yaxis_title="Capital Value ($)", barmode='group')
    st.plotly_chart(fig_proj, use_container_width=True)
    
    col_res1, col_res2 = st.columns(2)
    col_res1.metric("Your Total Cash Contributions", f"${total_invested:,.2f}")
    col_res2.metric("Final Projected Portfolio Balance", f"${balance:,.2f}", delta=f"${balance - total_invested:,.2f} Earned in Compound Interest")
