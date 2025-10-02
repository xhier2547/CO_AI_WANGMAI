import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
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

# ensure numeric for usage columns
for col in ["people_count", "table_used", "beanbag_used", "table_total", "beanbag_total"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

if len(df) == 0:
    st.warning("⚠️ No data available in usage_stats.csv")
    st.stop()

# ---------------- CURRENT STATUS ---------------- #
latest = df.iloc[-1]
latest_time = latest["timestamp"]

st.title("Co-AI WANGMAI Dashboard")
st.caption(f"Last Updated: {latest_time.strftime('%Y-%m-%d %H:%M:%S')}")

col1, col2, col3 = st.columns(3)
col1.metric("👥 People", int(latest["people_count"]))
col2.metric("🪑 Tables Used", f"{int(latest['table_used'])} / {int(latest['table_total'])}")
col3.metric("🛋️ Bean Bags Used", f"{int(latest['beanbag_used'])} / {int(latest['beanbag_total'])}")

st.markdown("---")

# ---------------- POPULAR HOURS BY DAY ---------------- #
st.subheader("⏳ Popular Hours by Day (08:00–23:00, Stacked)")

df["day_of_week"] = df["timestamp"].dt.strftime("%A")
df["hour"] = df["timestamp"].dt.hour

# เลือกวัน
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
day_choice = st.selectbox("เลือกวัน:", day_order)

# กรองข้อมูลเฉพาะวัน
day_data = df[df["day_of_week"] == day_choice]

# ค่าเฉลี่ยต่อชั่วโมง
hourly_avg = day_data.groupby("hour")[["people_count", "beanbag_used", "table_used"]].mean()

# กำหนด index ชั่วโมง 8–23 แล้ว reindex
hours_range = list(range(8, 24))
hourly_avg = hourly_avg.reindex(hours_range, fill_value=0).reset_index().rename(columns={"index": "hour"})

# แปลงเป็น long format
hourly_melt = hourly_avg.melt(
    id_vars="hour",
    value_vars=["people_count", "beanbag_used", "table_used"],
    var_name="Category", value_name="Count"
)

# กราฟ stacked bar
chart = alt.Chart(hourly_melt).mark_bar().encode(
    x=alt.X("hour:O", title="Hour of Day (08–23)"),
    y=alt.Y("Count:Q", stack="zero", title="Usage Count"),
    color=alt.Color(
        "Category:N",
        scale=alt.Scale(
            domain=["people_count", "beanbag_used", "table_used"],
            range=["#1f77b4", "#2ca02c", "#ff7f0e"]
        ),
        legend=alt.Legend(title="Category")
    ),
    tooltip=["hour", "Category", "Count"]
).properties(
    width=700,
    height=400,
    title=f"Average Usage per Hour on {day_choice} (08:00–23:00)"
)

st.altair_chart(chart, use_container_width=True)

# ---------------- DAILY SUMMARY ---------------- #
st.subheader("📊 Daily Summary")

summary_option = st.radio("View Mode:", ["By Date", "By Weekday"], horizontal=True)

if summary_option == "By Date":
    df["date"] = df["timestamp"].dt.date
    daily_avg = df.groupby("date")[["people_count", "table_used", "beanbag_used"]].mean().reset_index()

    col1, col2, col3 = st.columns(3)

    with col1:
        fig1 = px.bar(daily_avg, x="date", y="people_count",
                      labels={"date": "Date", "people_count": "People (avg)"},
                      title="👥 Average People per Day",
                      color_discrete_sequence=["royalblue"])
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.bar(daily_avg, x="date", y="table_used",
                      labels={"date": "Date", "table_used": "Tables Used (avg)"},
                      title="🪑 Average Tables Used per Day",
                      color_discrete_sequence=["orange"])
        fig2.update_yaxes(range=[0, int(df["table_total"].max())])  # fix scale
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        fig3 = px.bar(daily_avg, x="date", y="beanbag_used",
                      labels={"date": "Date", "beanbag_used": "Bean Bags Used (avg)"},
                      title="🛋️ Average Bean Bags Used per Day",
                      color_discrete_sequence=["green"])
        fig3.update_yaxes(range=[0, int(df["beanbag_total"].max())])  # fix scale
        st.plotly_chart(fig3, use_container_width=True)

else:  # By Weekday
    df["day_of_week"] = df["timestamp"].dt.strftime("%A")
    df["date"] = df["timestamp"].dt.date

    # เฉลี่ยรายวันก่อน แล้วรวมเป็นราย weekday
    daily_avg = df.groupby(["date", "day_of_week"])[["people_count", "table_used", "beanbag_used"]].mean().reset_index()
    weekday_avg = daily_avg.groupby("day_of_week")[["people_count", "table_used", "beanbag_used"]].mean()

    # reindex ให้ครบ 7 วัน
    weekday_avg = weekday_avg.reindex(day_order, fill_value=0).reset_index()
    weekday_avg.rename(columns={"index": "day_of_week"}, inplace=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        fig1 = px.bar(weekday_avg, x="day_of_week", y="people_count",
                      labels={"day_of_week": "Day of Week", "people_count": "People (avg)"},
                      title="👥 Average People (Mon–Sun)",
                      color_discrete_sequence=["royalblue"])
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.bar(weekday_avg, x="day_of_week", y="table_used",
                      labels={"day_of_week": "Day of Week", "table_used": "Tables Used (avg)"},
                      title="🪑 Average Tables Used (Mon–Sun)",
                      color_discrete_sequence=["orange"])
        fig2.update_yaxes(range=[0, int(df["table_total"].max())])  # fix scale
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        fig3 = px.bar(weekday_avg, x="day_of_week", y="beanbag_used",
                      labels={"day_of_week": "Day of Week", "beanbag_used": "Bean Bags Used (avg)"},
                      title="🛋️ Average Bean Bags Used (Mon–Sun)",
                      color_discrete_sequence=["green"])
        fig3.update_yaxes(range=[0, int(df["beanbag_total"].max())])  # fix scale
        st.plotly_chart(fig3, use_container_width=True)

# ---------------- TOP BUSY DAYS ---------------- #
st.subheader("🔥 Top Busy Days (by People)")

daily_avg = df.groupby(df["timestamp"].dt.date)[["people_count", "table_used", "beanbag_used"]].mean().reset_index()
top_days = daily_avg.sort_values(by="people_count", ascending=False).head(5)

peak_hours = []
max_people = []
for d in top_days["timestamp"]:
    day_data = df[df["timestamp"].dt.date == d]
    peak_row = day_data.loc[day_data["people_count"].idxmax()]
    peak_hours.append(peak_row["timestamp"].strftime("%H:%M"))
    max_people.append(peak_row["people_count"])

top_days = top_days.assign(Peak_Hour=peak_hours, Max_People=max_people)

st.table(top_days.rename(columns={
    "timestamp": "Date",
    "people_count": "Avg People",
    "table_used": "Avg Tables Used",
    "beanbag_used": "Avg Bean Bags Used",
    "Peak_Hour": "Peak Hour",
    "Max_People": "Max People"
}))

# ---------------- RAW DATA ---------------- #
st.subheader("📂 Raw Data")
st.dataframe(df[["timestamp", "people_count", "table_used", "table_total", "beanbag_used", "beanbag_total"]])

# download CSV button
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="💾 CSV",
    data=csv,
    file_name="usage_stats_clean.csv",
    mime="text/csv",
)
