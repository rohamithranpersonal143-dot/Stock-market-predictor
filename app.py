import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. SET UP PAGE CONFIGURATION
st.set_page_config(page_title="Stock Predictor", layout="wide")
st.title("📈 Stock Price Predictor App")
st.write("Train a Random Forest model on historical data to predict the next day's closing price.")

# 2. CREATE SIDEBAR CONTROLS
st.sidebar.header("Configuration")
ticker = st.sidebar.text_input("Stock Ticker", value="AAPL").upper()
years_back = st.sidebar.slider("Years of Historical Data", min_value=1, max_value=10, value=5)
prediction_days = st.sidebar.slider("Prediction Lookback Window (Days)", min_value=1, max_value=30, value=5)

# Calculate dynamic dates based on today (June 20, 2026)
end_date = datetime.now()
start_date = end_date - timedelta(days=years_back * 365)

# 3. FETCH DATA VIA YFINANCE
@st.cache_data(ttl=3600)  # Cache data for 1 hour to prevent redundant API calls
def load_data(stock_ticker, start, end):
    data = yf.download(stock_ticker, start=start, end=end)
    return data

with st.spinner(f"Fetching data for {ticker}..."):
    df = load_data(ticker, start_date, end_date)

if df.empty:
    st.error(f"No data found for ticker '{ticker}'. Please check the symbol and try again.")
    st.stop()

# 4. PREPROCESS DATA & ENGINEER FEATURES
st.subheader(f"Data Overview for {ticker}")
st.dataframe(df.tail(10), use_container_width=True)

# Flatten columns if multi-indexed by yfinance
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# Target: Next day's Close price
df['Target'] = df['Close'].shift(-1)

# Features: Creation of a rolling lookback window
feature_cols = []
for i in range(prediction_days):
    col_name = f'Close_Lag_{i+1}'
    df[col_name] = df['Close'].shift(i)
    feature_cols.append(col_name)

# Drop missing rows caused by shifts
df_model = df.dropna().copy()

X = df_model[feature_cols]
y = df_model['Target']

# Chronological split to prevent data leakage
train_size = int(len(X) * 0.8)
X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]

# 5. TRAIN MACHINE LEARNING MODEL
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 6. EVALUATE MODEL
predictions = model.predict(X_test)
mse = mean_squared_error(y_test, predictions)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, predictions)

# Display Metrics in Columns
col1, col2, col3 = st.columns(3)
col1.metric("Root Mean Squared Error (RMSE)", f"${rmse:.2f}")
col2.metric("R² Accuracy Score", f"{r2:.2f}")

# 7. GENERATE NEXT DAY'S PREDICTION
latest_features = df['Close'].iloc[-prediction_days:].values[::-1].reshape(1, -1)
next_day_pred = model.predict(latest_features)[0]

col3.metric("Next Trading Day Prediction", f"${next_day_pred:.2f}", 
            delta=f"${next_day_pred - df['Close'].iloc[-1]:.2f} vs Last Close")

# 8. VISUALIZE RESULTS
st.subheader("Model Performance: Actual vs. Predicted Prices")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_model.index[train_size:], y=y_test, mode='lines', name='Actual Price', line=dict(color='blue')))
fig.add_trace(go.Scatter(x=df_model.index[train_size:], y=predictions, mode='lines', name='Predicted Price', line=dict(color='orange', dash='dash')))

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Stock Price ($)",
    hovermode="x unified",
    margin=dict(l=20, r=20, t=20, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)
