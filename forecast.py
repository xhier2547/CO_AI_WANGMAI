# forecast.py
import pandas as pd
import numpy as np
import json
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from datetime import timedelta
import warnings
warnings.filterwarnings("ignore")

INPUT_CSV = "usage_stats.csv"
MODEL_JSON = "best_model.json"
OUTPUT_CSV = "best_forecast.csv"

def main():
    print("🚀 Starting Forecast Pipeline...")

    # 1) Load data
    df = pd.read_csv(INPUT_CSV, parse_dates=["timestamp"])
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.set_index("timestamp").asfreq("10min")
    df["people_count"] = df["people_count"].ffill().fillna(0)

    # 2) Load best model config
    with open(MODEL_JSON, "r") as f:
        best = json.load(f)

    model_name = best["Model"]
    params = best["Params"]
    print(f"📌 Using best model: {model_name} {params}")

    train = df
    exog_train = train[["table_used"]] if "table_used" in df.columns else None

    # 3) Fit best model
    if model_name == "ARIMA":
        order = eval(params)
        model = ARIMA(train["people_count"], order=order)
        fit = model.fit()

    elif model_name == "SARIMA":
        # params เก็บมาเป็น string → แปลงกลับเป็น tuple
        order, seasonal_order = eval(params[:params.find(")")]+")"), eval(params[params.find("("):])
        model = SARIMAX(train["people_count"], order=order, seasonal_order=seasonal_order)
        fit = model.fit(disp=False)

    elif model_name == "SARIMAX":
        order, seasonal_order = eval(params.split("+")[0][:params.find(")")+1]), eval(params.split("+")[0][params.find(")")+1:])
        model = SARIMAX(train["people_count"], order=order, seasonal_order=seasonal_order, exog=exog_train)
        fit = model.fit(disp=False)

    else:
        raise ValueError(f"Unknown model: {model_name}")

    # 4) Forecast 12 steps ahead (2 ชั่วโมงถ้าเก็บทุก 10 นาที)
    steps = 12
    if model_name == "SARIMAX":
        forecast = fit.forecast(steps=steps, exog=exog_train.tail(steps))
    else:
        forecast = fit.forecast(steps=steps)

    # 5) Save results
    result = pd.DataFrame({
        "timestamp": pd.date_range(start=df.index[-1] + timedelta(minutes=10), periods=steps, freq="10min"),
        "forecast": forecast.values
    })
    result.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Forecast saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
