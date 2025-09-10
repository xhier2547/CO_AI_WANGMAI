import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error
import numpy as np

# โหลดข้อมูล
df = pd.read_csv("usage_stats.csv", parse_dates=["timestamp"])
df = df.set_index("timestamp")

# ใช้แค่จำนวนคน (people_count) เป็น series
series = df["people_count"].asfreq("10min").fillna(0)

# train/test split (เช่น 80/20)
train_size = int(len(series) * 0.8)
train, test = series[:train_size], series[train_size:]

# SARIMA (p,d,q)(P,D,Q,s)
model = SARIMAX(train, order=(1,1,1), seasonal_order=(1,1,1,6))
fit = model.fit(disp=False)

# พยากรณ์ช่วง test
forecast = fit.forecast(steps=len(test))

# ประเมินค่า
rmse = np.sqrt(mean_squared_error(test, forecast))
print(f"RMSE = {rmse:.2f}")

# พล็อตผลลัพธ์
plt.figure(figsize=(10,5))
plt.plot(train.index, train, label="Train")
plt.plot(test.index, test, label="Test", color="orange")
plt.plot(test.index, forecast, label="Forecast", color="red")
plt.legend()
plt.show()
