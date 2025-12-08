"""
FastAPI Application for Stock Price Prediction
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import numpy as np
import pandas as pd
import yfinance as yf
from tensorflow.keras.models import load_model
import joblib
from datetime import datetime, timedelta
import os
from typing import Optional

app = FastAPI(title="Stock Price Predictor", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Load model and scaler
MODEL_PATH = "models/stock_model.h5"
SCALER_PATH = "models/scaler.pkl"
METADATA_PATH = "models/metadata.pkl"

model = None
scaler = None
metadata = None

def load_model_and_scaler():
    """Load the trained model and scaler"""
    global model, scaler, metadata
    try:
        model = load_model(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        metadata = joblib.load(METADATA_PATH)
        print("Model and scaler loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Please run train_model.py first to train the model.")

# Load on startup
load_model_and_scaler()

class PredictionRequest(BaseModel):
    ticker: str
    days: int = 30

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render home page"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "metadata": metadata
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/predict")
async def predict(prediction_request: PredictionRequest):
    """Predict stock prices"""
    if model is None or scaler is None:
        raise HTTPException(status_code=500, detail="Model not loaded. Please train the model first.")

    try:
        ticker = prediction_request.ticker.upper()
        days = min(prediction_request.days, 90)  # Limit to 90 days

        # Fetch historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # Get 1 year of data

        df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"Stock ticker '{ticker}' not found")

        # Flatten column names if multi-index
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        # Get close prices
        close_prices_df = df[['Close']].copy()
        close_prices = close_prices_df.values

        if len(close_prices) < metadata['sequence_length']:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data. Need at least {metadata['sequence_length']} days of historical data."
            )

        # Scale the data (using DataFrame to match training)
        scaled_data = scaler.transform(close_prices_df)

        # Get the last sequence
        last_sequence = scaled_data[-metadata['sequence_length']:].flatten()

        # Predict future prices
        predictions = []
        current_sequence = last_sequence.copy()

        for _ in range(days):
            # Reshape for prediction
            current_input = current_sequence.reshape((1, metadata['sequence_length'], 1))

            # Predict next value
            next_pred = model.predict(current_input, verbose=0)[0, 0]
            predictions.append(next_pred)

            # Update sequence
            current_sequence = np.append(current_sequence[1:], next_pred)

        # Inverse transform predictions
        predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1))

        # Create future dates
        last_date = df.index[-1]
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days, freq='D')

        # Prepare response
        current_price = float(close_prices[-1][0])
        predicted_price = float(predictions[-1][0])
        price_change = predicted_price - current_price
        percent_change = (price_change / current_price) * 100

        # Historical data for chart (last 90 days)
        historical_days = min(90, len(df))
        historical_dates = df.index[-historical_days:].strftime('%Y-%m-%d').tolist()
        historical_prices = close_prices[-historical_days:].flatten().tolist()

        # Future predictions for chart
        future_dates_str = future_dates.strftime('%Y-%m-%d').tolist()
        future_prices = predictions.flatten().tolist()

        return {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "predicted_price": round(predicted_price, 2),
            "price_change": round(price_change, 2),
            "percent_change": round(percent_change, 2),
            "prediction_days": days,
            "historical_data": {
                "dates": historical_dates,
                "prices": [round(p, 2) for p in historical_prices]
            },
            "future_data": {
                "dates": future_dates_str,
                "prices": [round(p, 2) for p in future_prices]
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.get("/api/stock-info/{ticker}")
async def get_stock_info(ticker: str):
    """Get basic stock information"""
    try:
        ticker = ticker.upper()
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "ticker": ticker,
            "name": info.get('longName', ticker),
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A'),
            "currency": info.get('currency', 'USD'),
            "market_cap": info.get('marketCap', 'N/A'),
            "description": info.get('longBusinessSummary', 'No description available.')[:200] + "..."
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Stock information not found: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
