import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from streamlit_autorefresh import st_autorefresh   # ✅ ใช้ auto-refresh

# ---------------- CONFIG ---------------- #
st.set_page_config(page_title="Co-working Dashboard", layout="wide")

# ---------------- REFRESH CONTROL ---------------- #
# Auto-refresh ทุก 600 วินาที (10 นาที)
count = st_autorefresh(interval=600 * 1000, key="auto_refresh")

# ถ้าเป็นรอบ auto-refresh (count > 0) แสดง toast
if count > 0:
    if hasattr(st, "toast"):
        st.toast("🔄 Refreshing (auto)...")
    else:
        st.info("🔄 Refreshing (auto)...")

# ฟังก์ชัน rerun ให้รองรับทั้งเวอร์ชันใหม่/เก่า
def do_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# ปุ่ม refresh manual
if st.button("🔄 Refresh Now"):
    if hasattr(st, "toast"):
        st.toast("🔄 Refreshing (manual)...")
    else:
        st.info("🔄 Refreshing (manual)...")
    do_rerun()

# ---------------- LOAD DATA ---------------- #
df = pd.read_csv("usage_stats.csv", usecols=[0,1,2,3,4,5])
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df = df.dropna(subset=["timestamp"])

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

# ---------------- LINE CHARTS + HOURLY GROUP ---------------- #
st.subheader("📊 Charts")

df["hour"] = df["timestamp"].dt.hour
hourly = df.groupby("hour")[["people_count", "table_used"]].mean().reset_index()

col1, col2 = st.columns(2)

with col1:
    st.markdown("**📈 People and Tables Usage Over Time**")
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(df["timestamp"], df["people_count"], marker="o", label="People")
    ax.plot(df["timestamp"], df["table_used"], marker="s", label="Tables Used")
    ax.set_xlabel("Time")
    ax.set_ylabel("Count")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()
    st.pyplot(fig)

with col2:
    st.markdown("**⏳ Hourly Average**")
    fig2, ax2 = plt.subplots(figsize=(5, 3))
    ax2.plot(hourly["hour"], hourly["people_count"], marker="o", label="People (avg)")
    ax2.plot(hourly["hour"], hourly["table_used"], marker="s", label="Tables Used (avg)")
    ax2.set_xlabel("Hour of Day")
    ax2.set_ylabel("Average Count")
    ax2.legend()
    st.pyplot(fig2)

# ---------------- SHOW DATA ---------------- #
st.subheader("📋 Raw Data (CSV)")
st.dataframe(df[["timestamp", "people_count", "table_used", "table_total"]])
