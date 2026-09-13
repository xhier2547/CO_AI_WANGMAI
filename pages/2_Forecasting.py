import streamlit as st
import pandas as pd
import altair as alt
import os

# =========================================================
# ⚙️ CONFIG
# =========================================================
st.set_page_config(page_title="Forecast Comparison Dashboard", layout="wide")
st.title("การพยากรณ์จำนวนคนใช้งานพื้นที่ Co-working Space")

# =========================================================
# 📦 LOAD DATA
# =========================================================
@st.cache_data
def load_csv(path):
    df = pd.read_csv(path)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    elif "index" in df.columns:
        df["timestamp"] = pd.to_datetime(df["index"], errors="coerce")
    else:
        st.error(f"❌ ไม่พบคอลัมน์เวลาในไฟล์ {path}")
        st.stop()
    return df.dropna(subset=["timestamp"])

# ---------------- Path ---------------- #
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "forecast", "outputs_forecast")

usage_path = os.path.join(DATA_DIR, "usage_stats_filled_days.csv")
forecast_1d_path = os.path.join(DATA_DIR, "forecast_results_1day_filtered.csv")
forecast_7d_path = os.path.join(DATA_DIR, "forecast_results_7day_filtered.csv")
metrics_path = os.path.join(DATA_DIR, "holdout_validation_metrics_filtered.csv")

# ---------------- Load Data ---------------- #
df_real = load_csv(usage_path)
df_1d = load_csv(forecast_1d_path)
df_7d = load_csv(forecast_7d_path)

# =========================================================
# 📆 DATE RANGE SLIDER (ข้อมูลจริง)
# =========================================================
df_real["timestamp"] = pd.to_datetime(df_real["index"])
min_date = df_real["timestamp"].min().to_pydatetime()
max_date = df_real["timestamp"].max().to_pydatetime()

st.subheader("📆 เลือกช่วงเวลาเพื่อแสดงข้อมูลจริง (Actual Data)")
start_date, end_date = st.slider(
    "ช่วงเวลา:",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD HH:mm"
)
df_real_filtered = df_real[(df_real["timestamp"] >= start_date) & (df_real["timestamp"] <= end_date)]

# =========================================================
# 🔮 PREDICTION DATE PICKER (เลือกวันพยากรณ์)
# =========================================================
st.subheader("วันที่ที่ต้องการดูผลการพยากรณ์")
min_forecast_date = min(df_1d["timestamp"].min(), df_7d["timestamp"].min()).date()
max_forecast_date = max(df_1d["timestamp"].max(), df_7d["timestamp"].max()).date()

selected_forecast_date = st.date_input(
    "วันที่ต้องการดูการพยากรณ์",
    value=min_forecast_date,
    min_value=min_forecast_date,
    max_value=max_forecast_date
)


# =========================================================
# 🎛️ MODEL TOGGLE (กราฟ)
# =========================================================
model_options = ["ARIMA", "SARIMA", "SARIMAX"]
selected_models = st.multiselect(
    "เลือกโมเดลที่ต้องการแสดงในกราฟ",
    model_options,
    default=model_options
)

# =========================================================
# 🧩 PLOT FUNCTION
# =========================================================
def plot_forecast_chart(title, forecast_df, real_df, models):
    forecast_df = forecast_df.melt("timestamp", var_name="model", value_name="forecast")
    forecast_df = forecast_df[forecast_df["model"].isin(models)]

    actual_chart = (
        alt.Chart(real_df)
        .mark_line(color="#AAAAAA", point=True)
        .encode(
            x=alt.X("timestamp:T", title="เวลา"),
            y=alt.Y("people_count:Q", title="จำนวนคน (Actual)"),
            tooltip=["timestamp", "people_count"]
        )
    )

    forecast_chart = (
        alt.Chart(forecast_df)
        .mark_line(point=True)
        .encode(
            x="timestamp:T",
            y="forecast:Q",
            color=alt.Color("model:N", title="Model"),
            tooltip=["timestamp", "model", "forecast"]
        )
    )

    return alt.layer(actual_chart, forecast_chart).properties(
        title=title, width="container", height=400
    ).interactive()

# =========================================================
# 📈 DISPLAY FORECASTS
# =========================================================
st.subheader(f"พยากรณ์ระยะสั้น (1 วันข้างหน้า) – วันที่ {selected_forecast_date}")
df_1d_selected = df_1d[df_1d["timestamp"].dt.date == selected_forecast_date]
st.altair_chart(plot_forecast_chart("Forecast 1 Day Ahead", df_1d_selected, df_real_filtered, selected_models), use_container_width=True)

st.subheader(f"พยากรณ์ระยะกลาง (7 วันข้างหน้า) – วันที่ {selected_forecast_date}")
df_7d_selected = df_7d[df_7d["timestamp"].dt.date == selected_forecast_date]
st.altair_chart(plot_forecast_chart("Forecast 7 Days Ahead", df_7d_selected, df_real_filtered, selected_models), use_container_width=True)

# =========================================================
# 🧾 สรุปผลพยากรณ์รายโมเดล (ตาราง)
# =========================================================
st.markdown("### สรุปผลพยากรณ์ของแต่ละโมเดลสำหรับวันที่ที่เลือก")

# รวมผลพยากรณ์ทั้งหมด
df_forecast_all = df_7d.copy()
df_forecast_all["mean_forecast"] = df_forecast_all[["ARIMA", "SARIMA", "SARIMAX"]].mean(axis=1)

# กรองเฉพาะวันพยากรณ์ที่เลือก
mask_forecast_day = df_forecast_all["timestamp"].dt.date == selected_forecast_date
df_day = df_forecast_all.loc[mask_forecast_day].copy()

if df_day.empty:
    st.warning("⚠️ ไม่มีข้อมูลพยากรณ์สำหรับวันที่ที่เลือก")
else:
    # สร้างตารางสรุปค่าเฉลี่ยต่อโมเดล
    summary_data = {
        "Model": ["ARIMA", "SARIMA", "SARIMAX"],
        "Average People": [
            round(df_day["ARIMA"].mean()),
            round(df_day["SARIMA"].mean()),
            round(df_day["SARIMAX"].mean())
        ],
        "Peak Time": [
            df_day.loc[df_day["ARIMA"].idxmax(), "timestamp"].strftime("%H:%M"),
            df_day.loc[df_day["SARIMA"].idxmax(), "timestamp"].strftime("%H:%M"),
            df_day.loc[df_day["SARIMAX"].idxmax(), "timestamp"].strftime("%H:%M")
        ],
        "Peak Value": [
            round(df_day["ARIMA"].max()),
            round(df_day["SARIMA"].max()),
            round(df_day["SARIMAX"].max())
        ],
        "Lowest Time": [
            df_day.loc[df_day["ARIMA"].idxmin(), "timestamp"].strftime("%H:%M"),
            df_day.loc[df_day["SARIMA"].idxmin(), "timestamp"].strftime("%H:%M"),
            df_day.loc[df_day["SARIMAX"].idxmin(), "timestamp"].strftime("%H:%M")
        ],
        "Lowest Value": [
            round(df_day["ARIMA"].min()),
            round(df_day["SARIMA"].min()),
            round(df_day["SARIMAX"].min())
        ],
    }

    df_summary = pd.DataFrame(summary_data)

    # ส่วนควบคุมการเปิด/ปิดโมเดล
    selected_models_summary = st.multiselect(
        "เลือกโมเดลที่ต้องการแสดงในตาราง",
        options=df_summary["Model"].tolist(),
        default=df_summary["Model"].tolist()
    )

    # แสดงตารางเฉพาะโมเดลที่เลือก
    df_display = df_summary[df_summary["Model"].isin(selected_models_summary)]
    st.dataframe(df_display, use_container_width=True)

# =========================================================
# 📊 METRICS + HIGHLIGHT
# =========================================================
if os.path.exists(metrics_path):
    st.markdown("---")
    st.subheader("Holdout Validation Metrics")

    df_metrics = pd.read_csv(metrics_path)
    best_row = df_metrics.loc[df_metrics["RMSE"].idxmin()]
    best_model = best_row["Unnamed: 0"]
    best_rmse, best_mae, best_mape = best_row["RMSE"], best_row["MAE"], best_row["MAPE"]

    def highlight_best(s):
        return [
            "background-color: #4CAF50; color: white; font-weight: bold; text-align: center"
            if v == s.min() else "" for v in s
        ]

    st.dataframe(
        df_metrics.style.apply(highlight_best, subset=["RMSE"]).format({
            "RMSE": "{:.4f}",
            "MAE": "{:.4f}",
            "MAPE": "{:.2f}"
        }),
        use_container_width=True
    )

    st.markdown(f"""
    ### 🏆 **โมเดลที่ดีที่สุด:** `{best_model}`
    - 🔹 RMSE = {best_rmse:.4f}
    - 🔹 MAE = {best_mae:.4f}
    - 🔹 MAPE = {best_mape:.2f} %

    💬 **สรุปผล:** โมเดล `{best_model}` มีค่า RMSE ต่ำสุด
    ซึ่งแปลว่าค่าคลาดเคลื่อนโดยเฉลี่ยของการพยากรณ์น้อยที่สุด
    ทำให้เหมาะสำหรับใช้งานจริงในการพยากรณ์จำนวนผู้ใช้งานพื้นที่ Co-working Space
    """)

else:
    st.info("ℹ️ ไม่มีไฟล์ holdout_validation_metrics_filtered.csv สำหรับแสดงผล")
