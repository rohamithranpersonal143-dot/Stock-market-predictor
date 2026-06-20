import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Investor Hub",
    page_icon="📈",
    layout="wide"
)

# =========================
# SESSION STATE INIT
# =========================
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["NVDA", "AAPL", "VOO"]

if "currency" not in st.session_state:
    st.session_state.currency = "USD"

if "language" not in st.session_state:
    st.session_state.language = "EN"

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
    st.sidebar.title("⚙️ Settings")

# Language selector (restored feature)
st.session_state.language = st.sidebar.selectbox(
    "Language",
    ["EN", "MY", "CN"]
)

# Currency selector (restored feature)
st.session_state.currency = st.sidebar.selectbox(
    "Currency Display",
    ["USD", "MYR", "EUR"]
)

st.sidebar.markdown("---")

# Watchlist input
new_stock = st.sidebar.text_input("Add Stock (e.g. TSLA)")

if st.sidebar.button("Add to Watchlist"):
    if new_stock and new_stock.upper() not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_stock.upper())
        st.rerun()

st.sidebar.markdown("### 📌 Watchlist")
for stock in st.session_state.watchlist:
    col1, col2 = st.sidebar.columns([3, 1])
    col1.write(stock)

    if col2.button("❌", key=f"del_{stock}"):
        st.session_state.watchlist.remove(stock)
        st.rerun()
        @st.cache_data(ttl=300)
        
def get_stock_data(ticker):
    try:
        data = yf.download(ticker, period="1mo", interval="1d")
        if data.empty:
            return None
        return data
    except Exception:
        return None


def get_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"].iloc[-1]
        return round(price, 2)
    except Exception:
        return None
        st.title("📊 Investor Hub Dashboard")

st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

cols = st.columns(len(st.session_state.watchlist))

for i, stock in enumerate(st.session_state.watchlist):
    price = get_price(stock)

    with cols[i]:
        st.metric(
            label=stock,
            value=f"{price} {st.session_state.currency}" if price else "N/A"
        )
        st.markdown("---")
st.subheader("📉 Stock Charts")

selected = st.selectbox("Select stock", st.session_state.watchlist)

data = get_stock_data(selected)

if data is not None:
    st.line_chart(data["Close"])
else:
    st.warning("No data available for this stock.")

st.markdown("---")
st.caption("Investor Hub v2.0 — Stable Build")
