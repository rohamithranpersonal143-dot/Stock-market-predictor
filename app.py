import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Global Investor Hub", layout="wide")

# =========================
# TRANSLATION PACK (FULL)
# =========================
LANG_PACK = {
    "English": {
        "title": "🎯 Universal Investor Hub & Strategy Lab",
        "sub": "Track stocks, review entry timing metrics, and simulate compounding portfolio growth.",
        "header_1": "📋 1. Simple Risk-Reward Dashboard",
        "header_2": "⚡ 2. Strategy Check: Is it a good time to buy?",
        "header_3": "⏳ 3. Long-Term Wealth Compound Planner",
        "lbl_currency": "Display Currency:",
        "lbl_lang": "Interface Language:",
        "lbl_add": "Add Assets to Hub",
        "lbl_add_btn": "➕ Add to Dashboard",
        "lbl_reset": "🗑️ Reset Watchlist",
        "msg_weekend": "Showing latest closing market price data for",
        "price_lbl": "Current Price",
        "swing_lbl": "Historical Price Jumpiness",
        "help_swing": "Higher % means more volatility.",
        "strat_desc": "50-day vs 200-day trend comparison.",
        "strat_select": "Select stock:",
        "strat_bull": "🟢 Bullish Momentum",
        "strat_bear": "🔴 Bearish Caution",
        "line_market": "Market Price",
        "line_sma50": "50-Day SMA",
        "line_sma200": "200-Day SMA",
        "dca_desc": "Monthly investing growth simulation.",
        "dca_start": "Starting Cash",
        "dca_add": "Monthly Add",
        "dca_years": "Years",
        "dca_info": "Using {val}% annual return estimate.",
        "dca_res1": "Total Invested",
        "dca_res2": "Final Balance",
        "dca_delta": "Profit",
        "chart_cash": "Cash",
        "chart_growth": "Growth",
        "risk_low": "🟢 Low Risk",
        "risk_med": "🟡 Medium Risk",
        "risk_high": "🔴 High Risk"
    }
}

# =========================
# STATE
# =========================
DEFAULT_WATCHLIST = ["NVDA", "VOO", "AAPL"]

if "watchlist" not in st.session_state:
    st.session_state.watchlist = DEFAULT_WATCHLIST.copy()

# =========================
# SIDEBAR
# =========================
txt = LANG_PACK["English"]

st.sidebar.header("Settings")

new_ticker = st.sidebar.text_input("Ticker").upper().strip()

if st.sidebar.button("Add") and new_ticker:
    if new_ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_ticker)
        st.toast("Added!")

if st.sidebar.button("Reset"):
    st.session_state.watchlist = DEFAULT_WATCHLIST.copy()
    st.rerun()

# =========================
# TITLE
# =========================
st.title(txt["title"])
st.write(txt["sub"])

# =========================
# DATA ENGINE
# =========================
@st.cache_data(ttl=1800)
def fetch_data(tickers):
    end = datetime(2026, 6, 20)
    start = end - timedelta(days=730)
    try:
        data = yf.download(tickers, start=start, end=end)["Close"]
        if len(tickers) == 1:
            data = pd.DataFrame({tickers: data})
        return data
    except Exception:
        return pd.DataFrame()

price_matrix = fetch_data(st.session_state.watchlist)

# =========================
# DASHBOARD
# =========================
st.header(txt["header_1"])

if not price_matrix.empty:
    for t in st.session_state.watchlist:
        if t in price_matrix.columns:
            s = price_matrix[t].dropna()
            if len(s) > 2:
                vol = s.pct_change().std() * np.sqrt(252) * 100
                cur = float(s.iloc[-1])

                if vol < 20:
                    risk = txt["risk_low"]
                elif vol < 40:
                    risk = txt["risk_med"]
                else:
                    risk = txt["risk_high"]

                st.write(f"### {t} — {risk}")
                st.metric("Price", f"${cur:,.2f}")

# =========================
# STRATEGY
# =========================
st.header(txt["header_2"])

if not price_matrix.empty:
    stock = st.selectbox("Stock", st.session_state.watchlist)

    df = pd.DataFrame({"Close": price_matrix[stock].dropna()})
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()

    if df["SMA50"].iloc[-1] > df["SMA200"].iloc[-1]:
        st.success(txt["strat_bull"])
    else:
        st.error(txt["strat_bear"])

# =========================
# DCA SIM
# =========================
st.header(txt["header_3"])

cash = st.number_input("Cash", value=1000)
monthly = st.number_input("Monthly", value=200)
years = st.slider("Years", 1, 30, 10)

months = years * 12
rate = (1 + 0.10) ** (1/12) - 1

bal = cash
invested = cash
history = []

for i in range(months):
    bal = (bal + monthly) * (1 + rate)
    invested += monthly
    if i % 12 == 0:
        history.append((i//12, bal, invested))

st.success("Simulation complete")
