import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# ---------------- CONFIG ---------------- #
st.set_page_config(page_title="Co-working Dashboard", layout="wide")

# ---------------- LOAD DATA ---------------- #
try:
    df = pd.read_csv("usage_stats.csv")
except FileNotFoundError:
    st.error("❌ usage_stats.csv not found")
    st.stop()

# parse timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df = df.dropna(subset=["timestamp"])

if len(df) == 0:
    st.warning("⚠️ No data available in usage_stats.csv")
    st.stop()

# ---------------- CURRENT STATUS ---------------- #
latest = df.iloc[-1]
latest_time = latest["timestamp"]

st.title("📊 Co-working Space Dashboard")

col1, col2, col3, col4 = st.columns(4)
col1.metric("👥 People", int(latest["people_count"]))
col2.metric("🪑 Tables Used", f"{latest['table_used']} / {latest['table_total']}")
col3.metric("🛋️ Bean Bag Used", f"{latest['beanbag_used']} / {latest['beanbag_total']}")
col4.metric("⏰ Last Update", latest_time.strftime("%Y-%m-%d %H:%M:%S"))

st.markdown("---")

# ---------------- CHARTS ---------------- #
st.subheader("📊 Charts")
df["hour"] = df["timestamp"].dt.hour
hourly = df.groupby("hour")[["people_count", "table_used"]].mean().reset_index()

col1, col2 = st.columns(2)
with col1:
    st.markdown("**📈 People and Tables Usage Over Time**")
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(df["timestamp"], df["people_count"], marker="o", label="People")
    ax.plot(df["timestamp"], df["table_used"], marker="s", label="Tables Used")
    ax.set_xlabel("Time")
    ax.set_ylabel("Count")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()
    st.pyplot(fig)

with col2:
    st.markdown("**⏳ Hourly Average**")
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.plot(hourly["hour"], hourly["people_count"], marker="o", label="People (avg)")
    ax2.plot(hourly["hour"], hourly["table_used"], marker="s", label="Tables Used (avg)")
    ax2.set_xlabel("Hour of Day")
    ax2.set_ylabel("Average Count")
    ax2.legend()
    st.pyplot(fig2)

# ---------------- DAILY SUMMARY ---------------- #
st.subheader("📅 Daily Summary")
df["date"] = df["timestamp"].dt.date
daily_avg = df.groupby("date")[["people_count", "table_used"]].mean().reset_index()

col1, col2 = st.columns(2)
with col1:
    st.markdown("**👥 Average People per Day**")
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    ax3.bar(daily_avg["date"], daily_avg["people_count"], color="royalblue")
    ax3.set_ylabel("People (avg)")
    ax3.set_xlabel("Date")
    ax3.tick_params(axis="x", rotation=45)
    st.pyplot(fig3)

with col2:
    st.markdown("**🪑 Average Tables Used per Day**")
    fig4, ax4 = plt.subplots(figsize=(6, 4))
    ax4.bar(daily_avg["date"], daily_avg["table_used"], color="orange")
    ax4.set_ylabel("Tables Used (avg)")
    ax4.set_xlabel("Date")
    ax4.tick_params(axis="x", rotation=45)
    st.pyplot(fig4)

# ---------------- TOP BUSY DAYS ---------------- #
st.subheader("🏆 Top Busy Days (by People)")
peak_info = df.groupby(["date", "hour"])["people_count"].max().reset_index()
top_days = daily_avg.sort_values(by="people_count", ascending=False).head(5)

# หา peak hour ของแต่ละวัน
peak_hours = []
max_people = []
for d in top_days["date"]:
    day_data = df[df["date"] == d]
    peak_row = day_data.loc[day_data["people_count"].idxmax()]
    peak_hours.append(peak_row["timestamp"].strftime("%H:%M"))
    max_people.append(peak_row["people_count"])

top_days = top_days.assign(
    Peak_Hour=peak_hours,
    Max_People=max_people
)

st.table(top_days.rename(columns={
    "date": "Date",
    "people_count": "Avg People",
    "Peak_Hour": "Peak Hour",
    "Max_People": "Max People"
}))

# ---------------- RAW DATA ---------------- #
st.subheader("📋 Raw Data (CSV)")
st.dataframe(df[["timestamp", "people_count", "table_used", "table_total"]])
