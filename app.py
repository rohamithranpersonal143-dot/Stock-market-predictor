import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. PAGE LAYOUT CONFIGURATION
st.set_page_config(page_title="Stock Predictor", layout="wide")
st.title("📈 Stock Price Predictor App")
st.write("Train a Random Forest model on clean historical data to predict the next day's closing price.")

# 2. SIDEBAR CONTROLS
st.sidebar.header("Configuration")
ticker = st.sidebar.text_input("Stock Ticker", value="AAPL").upper()
years_back = st.sidebar.slider("Years of Historical Data", min_value=1, max_value=10, value=5)
prediction_days = st.sidebar.slider("Prediction Lookback Window (Days)", min_value=1, max_value=30, value=5)

# Calculate dynamic tracking dates
end_date = datetime.now()
start_date = end_date - timedelta(days=years_back * 365)

# 3. ROBUST DATA FETCHING AND CLEANING
@st.cache_data(ttl=3600)
def load_and_clean_data(stock_ticker, start, end):
    # Fetch data explicitly grouping by ticker to control layout
    data = yf.download(stock_ticker, start=start, end=end, group_by="ticker")
    
    if data.empty:
        return pd.DataFrame()
        
    # FIX: Flatten Multi-Index columns if yfinance returns layered headers
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(-1)
        
    # Standardize column naming rules by stripping white spaces
    data.columns = [str(col).strip() for col in data.columns]
    
    # Ensure standard structural arrays are cast explicitly to 1D numeric vectors
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col].values.flatten())
            
    return data

with st.spinner(f"Fetching and processing data for {ticker}..."):
    df = load_and_clean_data(ticker, start_date, end_date)

if df.empty:
    st.error(f"❌ No data found for ticker '{ticker}'. Please check the symbol and try again.")
    st.stop()

# Inform user about weekend data schedules
latest_date = df.index[-1].strftime('%A, %B %d, %Y')
st.info(f"🗓️ Latest available market data: **{latest_date}**. (Note: Traditional stock markets are closed on weekends and holidays).")

# 4. DATA OVERVIEW
st.subheader(f"Data Window Preview for {ticker}")
st.dataframe(df.tail(10), use_container_width=True)

# 5. FEATURE ENGINEERING (LOOKBACK MATRIX)
# Target variable: The actual closing price of the next trading day
df['Target'] = df['Close'].shift(-1)

feature_cols = []
for i in range(prediction_days):
    col_name = f'Close_Lag_{i+1}'
    df[col_name] = df['Close'].shift(i)
    feature_cols.append(col_name)

# Clear structural missing entries caused by shifts
df_model = df.dropna().copy()

if df_model.empty:
    st.error("❌ Not enough data rows to train the model. Try expanding the 'Years of Historical Data' or decreasing the 'Lookback Window'.")
    st.stop()

X = df_model[feature_cols]
y = df_model['Target']

# Chronological test split to preserve chronological validation structure
train_size = int(len(X) * 0.8)
X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]

# 6. MODEL TRAINING
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 7. MODEL EVALUATION METRICS
predictions = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, predictions))
r2 = r2_score(y_test, predictions)

# Formulate single-row feature array for next upcoming cycle forecast
latest_features = df['Close'].iloc[-prediction_days:].values[::-1].reshape(1, -1)
next_day_pred = model.predict(latest_features)[0]
last_close_val = df['Close'].iloc[-1]
price_delta = next_day_pred - last_close_val

# Render Metrics Row
col1, col2, col3 = st.columns(3)
col1.metric("Model Error Margin (RMSE)", f"${rmse:.2f}", help="Average dollar distance from true price.")
col2.metric("R² Directional Fit Score", f"{r2:.2f}", help="How well model fits trend. Closer to 1.0 is best.")
col3.metric("Next Trading Day Prediction", f"${next_day_pred:.2f}", 
            delta=f"${price_delta:.2f} vs Last Close", help="Calculated forecast target value.")

# 8. PLOTLY VISUALIZATION RENDERING
st.subheader("Interactive Evaluation: Actual vs. Predicted Movements")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_model.index[train_size:], y=y_test, mode='lines', name='True Actual Price', line=dict(color='#00CC96', width=2)))
fig.add_trace(go.Scatter(x=df_model.index[train_size:], y=predictions, mode='lines', name='Model Prediction', line=dict(color='#EF553B', width=2, dash='dash')))

fig.update_layout(
    xaxis_title="Timeline Date Range",
    yaxis_title="Stock Value ($)",
    hovermode="x unified",
    template="plotly_dark",
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)
