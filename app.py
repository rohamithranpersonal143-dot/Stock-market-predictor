import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# 1. APP VIEWPORT CONFIGURATION
st.set_page_config(page_title="Investment Tier Matrix", layout="wide")
st.title("🎯 Strategic Investment Matrix Dashboard")
st.write("Filter and explore prime asset options structured by historical risk-to-reward metrics rather than speculative projections.")

# 2. SECTOR PROFILE DATAFRAME
@st.cache_data
def get_investment_catalog():
    # Catalog tracking asset, tier, risk description, and baseline benchmark profiles
    catalog = {
        "Ticker": ["AAPL", "NVDA", "O", "JNJ", "TSLA", "BTC-USD", "VOO", "SCHD"],
        "Name": ["Apple Inc.", "NVIDIA Corporation", "Realty Income", "Johnson & Johnson", "Tesla Inc.", "Bitcoin Crypto", "S&P 500 ETF", "Schwab Dividend ETF"],
        "Risk Tier": ["Medium Risk", "High Risk", "Low Risk", "Low Risk", "High Risk", "High Risk", "Low Risk", "Low Risk"],
        "Color Badge": ["🟡 Amber", "🔴 Red", "🟢 Green", "🟢 Green", "🔴 Red", "🔴 Red", "🟢 Green", "🟢 Green"],
        "Investment Thesis": ["Stable tech ecosystem with strong free cash flows.", "Exponential AI demand catalyst paired with extreme price volatility.", "Consistent real estate monthly dividend payouts.", "Defensive healthcare blue-chip with rock-solid balance sheet.", "High beta innovation stock driven by retail momentum.", "Speculative decentralized digital asset with massive price swings.", "Diversified broad-market exposure mimicking global economic growth.", "Focused high-yield dividend growth for defensive safety."]
    }
    return pd.DataFrame(catalog)

df_catalog = get_investment_catalog()

# 3. INTERACTIVE SIDEBAR WIDGETS
st.sidebar.header("Matrix Filters")
selected_tier = st.sidebar.multiselect(
    "Filter by Risk Profiles:",
    options=["Low Risk", "Medium Risk", "High Risk"],
    default=["Low Risk", "Medium Risk", "High Risk"]
)
years_back = st.sidebar.slider("Historical Calculation Window (Years)", min_value=1, max_value=5, value=2)

# Filter catalog array dynamically based on selection
df_filtered = df_catalog[df_catalog["Risk Tier"].isin(selected_tier)].reset_index(drop=True)

# 4. PARSE LIVE PERFORMANCE METRICS
@st.cache_data(ttl=3600)
def fetch_live_metrics(tickers, years):
    end = datetime.now()
    start = end - timedelta(days=years * 365)
    
    # Download batch array data safely via yfinance
    try:
        data = yf.download(tickers, start=start, end=end, auto_adjust=True, actions=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(-1)
        data.columns = [str(col).strip().lower() for col in data.columns]
        
        # In batch requests with different column lengths, extract the closing dataframe cleanly
        close_data = yf.download(tickers, start=start, end=end)['Close']
        return close_data
    except Exception:
        # Fallback empty structure if network errors trigger
        return pd.DataFrame()

tickers_list = df_filtered["Ticker"].tolist()

if tickers_list:
    with st.spinner("Calculating live risk-reward variances..."):
        price_df = fetch_live_metrics(tickers_list, years_back)
    
    # Calculate annualized statistics
    if not price_df.empty:
        stats = []
        for ticker in tickers_list:
            if ticker in price_df.columns:
                series = price_df[ticker].dropna()
                if len(series) > 1:
                    # Calculate percentage shifts to locate compound returns and standard deviation risks
                    returns = series.pct_change().dropna()
                    annualized_return = (series.iloc[-1] / series.iloc[0]) ** (1 / years_back) - 1
                    annualized_volatility = returns.std() * np.sqrt(252)
                    
                    stats.append({
                        "Ticker": ticker,
                        "Annual Return": annualized_return * 100,
                        "Historical Risk (Volatility)": annualized_volatility * 100
                    })
        
        df_stats = pd.DataFrame(stats)
        if not df_stats.empty:
            df_filtered = pd.merge(df_filtered, df_stats, on="Ticker", how="left")

# 5. RENDER SYSTEM INTERACTIVE ROWS
st.subheader("📋 Screened Allocation Matrix")
if df_filtered.empty:
    st.warning("No assets match your sidebar filter selections.")
else:
    for idx, row in df_filtered.iterrows():
        # Clean expandable cards themed by tier indicators
        with st.container():
            col_badge, col_name, col_return, col_risk = st.columns([1.5, 3, 2, 2])
            
            # Extract statistics labels
            ret_val = f"{row['Annual Return']:.1f}%" if "Annual Return" in row else "Data Pending"
            risk_val = f"{row['Historical Risk (Volatility)']:.1f}%" if "Historical Risk (Volatility)" in row else "Data Pending"
            
            col_badge.write(f"### {row['Color Badge']}")
            col_name.write(f"**{row['Name']} ({row['Ticker']})**\n\n_{row['Investment Thesis']}_")
            col_return.metric("Est. Annual Reward", ret_val)
            col_risk.metric("Calculated Risk Metric", risk_val)
            st.markdown("---")

    # 6. RISK VS REWARD SCATTER PLOT
    if "Annual Return" in df_filtered.columns:
        st.subheader("📊 Visualizing Your Options: Risk vs. Reward")
        st.write("Look for options in the **top-left corner** (High Reward, Low Risk) or find balanced options that suit your personal style.")
        
        fig = px.scatter(
            df_filtered,
            x="Historical Risk (Volatility)",
            y="Annual Return",
            text="Ticker",
            color="Risk Tier",
            color_discrete_map={"Low Risk": "#00CC96", "Medium Risk": "#FECB52", "High Risk": "#EF553B"},
            labels={"Historical Risk (Volatility)": "Risk Axis (Annualized Volatility %)", "Annual Return": "Reward Axis (Annual Returns %)"},
            template="plotly_dark"
        )
        fig.update_traces(textposition='top center', marker=dict(size=14, line=dict(width=1, color='white')))
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
