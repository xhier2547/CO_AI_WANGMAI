# =========================================================
# 🧩 Co-AI WANGMAI Dashboard (✨ No Daily Summary Version ✨)
# =========================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
from datetime import datetime, timedelta, date # Import date
import os
import numpy as np # Import numpy
# import plotly.graph_objects as go # ไม่ได้ใช้แล้ว ลบออกได้

# ---------------- CONFIG ---------------- #
st.set_page_config(page_title="Co-working Dashboard", layout="wide") # Corrected layout

# =========================================================
# 📂 LOAD DATA FUNCTIONS (Handles 'index' or 'timestamp')
# =========================================================
@st.cache_data
def load_data(path):
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        st.error(f"❌ Error: Input file not found at '{path}'")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error reading file '{path}': {e}")
        return pd.DataFrame()

    time_col_original = None
    if "timestamp" in df.columns:
        time_col_original = "timestamp"
        time_col_standard = "timestamp"
    elif "index" in df.columns:
        time_col_original = "index"
        time_col_standard = "timestamp"
        df = df.rename(columns={"index": "timestamp"})
        print("   Renamed 'index' column to 'timestamp'.")
    else:
        st.error(f"❌ Error: Could not find 'timestamp' or 'index' column in '{path}'")
        return pd.DataFrame()

    if time_col_standard in df.columns:
        df["timestamp"] = pd.to_datetime(df[time_col_standard], errors="coerce")
        df = df.dropna(subset=["timestamp"])
    else:
        st.error(f"❌ Error: Standard time column '{time_col_standard}' not found.")
        return pd.DataFrame()

    for col in ["people_count", "table_used", "beanbag_used", "table_total", "beanbag_total"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    if "timestamp" in df.columns:
        df = df.sort_values("timestamp").set_index("timestamp")
    else:
        st.error("❌ Critical Error: 'timestamp' column lost.")
        return pd.DataFrame()

    return df

# โหลด usage data
USAGE_FILE = "usage_stats_filled_days.csv"
df = load_data(USAGE_FILE)

if df.empty:
    st.error(f"Failed to load or process data from '{USAGE_FILE}'. Dashboard cannot be displayed.")
    st.stop()

# =========================================================
# 🧭 CURRENT STATUS
# =========================================================
latest = df.iloc[-1]
latest_time = latest.name

st.title("Co-AI WANGMAI Dashboard")
st.caption(f"Last Updated: {latest_time.strftime('%Y-%m-%d %H:%M:%S')}")

col1, col2, col3 = st.columns(3)
people_count = latest.get("people_count", 0)
table_used = latest.get("table_used", 0)
table_total = latest.get("table_total", "N/A")
beanbag_used = latest.get("beanbag_used", 0)
beanbag_total = latest.get("beanbag_total", "N/A")

col1.metric("👥 People", int(people_count))
if isinstance(table_total, (int, float)) and table_total > 0:
    col2.metric("🪑 Tables Used", f"{int(table_used)} / {int(table_total)}")
else:
    col2.metric("🪑 Tables Used", f"{int(table_used)}")
if isinstance(beanbag_total, (int, float)) and beanbag_total > 0:
    col3.metric("🛋️ Bean Bags Used", f"{int(beanbag_used)} / {int(beanbag_total)}")
else:
    col3.metric("🛋️ Bean Bags Used", f"{int(beanbag_used)}")

st.markdown("---")

# =========================================================
# ⏰ POPULAR HOURS BY DAY (✨ FIX: Round Displayed Averages to Integer ✨)
# =========================================================
st.subheader("⏳ Popular Hours by Day (08:00–23:00)")

# Ensure 'day_of_week' and 'hour' columns exist or create them
if 'day_of_week' not in df.columns:
    df["day_of_week"] = df.index.strftime("%A")
if 'hour' not in df.columns:
    df["hour"] = df.index.hour

day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
day_choice = st.selectbox("เลือกวัน:", day_order)

day_data = df[df["day_of_week"] == day_choice]

if not day_data.empty:
    grouping_cols = ["people_count", "table_used", "beanbag_used"]
    available_grouping_cols = [col for col in grouping_cols if col in day_data.columns]

    if available_grouping_cols:
        # Calculate hourly averages (keep decimals for accuracy)
        hourly_avg = day_data.groupby("hour")[available_grouping_cols].mean()
        hours_range = list(range(8, 24))
        hourly_avg = hourly_avg.reindex(hours_range, fill_value=0.0).reset_index()

        # Melt ALL available columns
        hourly_melt = hourly_avg.melt(
            id_vars=['hour'],
            value_vars=available_grouping_cols,
            var_name='Usage Type Raw',
            value_name='Average Count' # This value still has decimals
        )

        # Define color scale and legend mapping
        label_map = {
            'people_count': '👥 People',
            'table_used': '🪑 Tables Used',
            'beanbag_used': '🛋️ Beanbags Used'
        }
        color_range_map = {
             '👥 People': '#1f77b4',       # Blue
             '🪑 Tables Used': '#ff7f0e',   # Orange
             '🛋️ Beanbags Used': '#2ca02c'  # Green
        }
        hourly_melt['Usage Type'] = hourly_melt['Usage Type Raw'].map(label_map)
        available_labels = hourly_melt['Usage Type'].unique()
        color_domain = [label_map[col] for col in grouping_cols if label_map[col] in available_labels]
        color_range = [color_range_map[label] for label in color_domain]

        # --- Plotting Code using Melted Data ---
        base = alt.Chart(hourly_melt).encode(
            x=alt.X('hour:O', title='Hour of Day (08–23)', axis=alt.Axis(labelAngle=0)),
            # Color encode based on the 'Usage Type' column
            color=alt.Color('Usage Type:N',
                            scale=alt.Scale(domain=color_domain, range=color_range),
                            legend=alt.Legend(title="Usage Type")),
            tooltip=[
                alt.Tooltip('hour', title='Hour'),
                alt.Tooltip('Usage Type', title='Type'),
                # ✨ FIX: Format tooltip average as integer ✨
                alt.Tooltip('Average Count', title='Average', format=".0f") # Use ".0f" for zero decimals
            ]
        ).properties(
             title=f'Average Usage per Hour on {day_choice} (08:00–23:00)'
        )

        chart_layers = []

        # Layer 1: Bars for People Count
        people_label = label_map.get('people_count')
        if people_label in available_labels:
            bars = base.mark_bar(opacity=0.7).encode(
                # Y-axis can still show decimals for precision if needed
                y=alt.Y('Average Count:Q', title='Average Usage Count', axis=alt.Axis(format=".1f")),
            ).transform_filter(
                alt.datum['Usage Type'] == people_label
            )
            chart_layers.append(bars)
        else:
            st.warning("Column 'people_count' not found for plotting.")

        # Layer 2: Lines + Points for Table and Beanbag
        line_labels = [label_map.get('table_used'), label_map.get('beanbag_used')]
        line_labels_available = [label for label in line_labels if label in available_labels]

        if line_labels_available:
            lines = base.mark_line(point=True).encode(
                y=alt.Y('Average Count:Q'),
            ).transform_filter(
                alt.FieldOneOfPredicate(field='Usage Type', oneOf=line_labels_available)
            )
            chart_layers.append(lines)

            # Layer 3: Text labels for the lines
            texts = lines.mark_text(
                 align='center',
                 baseline='bottom',
                 dy=-10
             ).encode(
                 # ✨ FIX: Format text label as integer ✨
                 text=alt.Text('Average Count:Q', format='.0f'), # Use ".0f" for zero decimals
                 color=alt.Color('Usage Type:N', legend=None) # Color text by type
             )
            chart_layers.append(texts)

        # Combine layers and plot
        if chart_layers:
             final_chart = alt.layer(*chart_layers).resolve_scale(y='shared')
             st.altair_chart(final_chart, use_container_width=True)
        elif not available_grouping_cols:
             st.warning("No usage data columns available to plot for Popular Hours.")

    else:
        st.warning(f"No usage data columns found for {day_choice}.")
else:
    st.warning(f"No data available for {day_choice}.")

st.markdown("---")

# =========================================================
# 🔥 TOP BUSY DAYS (Check columns exist)
# =========================================================
st.subheader("🔥 Top Busy Days (by People)")

# Recalculate daily_avg_by_date specifically for this section
daily_avg_for_top = pd.DataFrame()
top_days_cols = ["people_count", "table_used", "beanbag_used"] # Define needed columns
available_top_days_cols = [col for col in top_days_cols if col in df.columns]

if 'date' not in df.columns: # Ensure date column exists
     if isinstance(df.index, pd.DatetimeIndex):
         df["date"] = df.index.date
     else:
         st.warning("Cannot calculate Top Busy Days without date information.")
         available_top_days_cols = [] # Prevent further processing

if available_top_days_cols:
     try:
          daily_avg_for_top = df.groupby("date")[available_top_days_cols].mean().reset_index()
          daily_avg_for_top['date'] = pd.to_datetime(daily_avg_for_top['date']).dt.date
     except Exception as e:
          st.error(f"Error calculating daily averages for Top Busy Days: {e}")
          daily_avg_for_top = pd.DataFrame()


if not daily_avg_for_top.empty and "people_count" in daily_avg_for_top.columns:
    top_days = daily_avg_for_top.sort_values(by="people_count", ascending=False).head(5).copy()
    peak_hours, max_people = [], []

    if "people_count" in df.columns:
        for d in top_days["date"]:
            day_data_peak = df[df.index.date == d]
            if not day_data_peak.empty:
                try:
                    peak_row = day_data_peak.loc[day_data_peak["people_count"].idxmax()]
                    peak_hours.append(peak_row.name.strftime("%H:%M"))
                    max_people.append(int(peak_row["people_count"]))
                except KeyError:
                     peak_hours.append("Error"); max_people.append(0)
            else:
                peak_hours.append("N/A"); max_people.append(0)
        top_days['Peak_Hour'] = peak_hours
        top_days['Max_People'] = max_people
    else:
         st.warning("Cannot determine peak hours.")
         if 'Peak_Hour' not in top_days.columns: top_days['Peak_Hour'] = "N/A"
         if 'Max_People' not in top_days.columns: top_days['Max_People'] = "N/A"

    display_cols_mapping = {
        "date": "Date", "people_count": "Avg People", "table_used": "Avg Tables Used",
        "beanbag_used": "Avg Bean Bags Used", "Peak_Hour": "Peak Hour", "Max_People": "Max People at Peak"
    }
    existing_cols_in_top_days = [col for col in display_cols_mapping.keys() if col in top_days.columns]
    final_rename_mapping = {k: display_cols_mapping[k] for k in existing_cols_in_top_days}
    final_display_names = [final_rename_mapping[k] for k in existing_cols_in_top_days]

    if final_rename_mapping:
         top_days_display = top_days.rename(columns=final_rename_mapping)[final_display_names]
         format_dict = {}
         if "Avg People" in top_days_display.columns: format_dict["Avg People"] = "{:.1f}"
         if "Avg Tables Used" in top_days_display.columns: format_dict["Avg Tables Used"] = "{:.1f}"
         if "Avg Bean Bags Used" in top_days_display.columns: format_dict["Avg Bean Bags Used"] = "{:.1f}"
         if "Max People at Peak" in top_days_display.columns: format_dict["Max People at Peak"] = "{:d}"
         st.dataframe(top_days_display.style.format(format_dict))
    else: st.warning("No columns available for Top Busy Days display.")

else:
    st.warning("Cannot determine top busy days (missing 'people_count' or data).")

st.markdown("---")

# =========================================================
# 📂 RAW DATA
# =========================================================
st.subheader("📂 Raw Data (Resampled to 30min - if applicable)")
st.dataframe(df.reset_index())

@st.cache_data
def convert_df_to_csv(df_to_convert):
    return df_to_convert.reset_index().to_csv(index=False).encode('utf-8')

csv = convert_df_to_csv(df)
st.download_button(
    label="💾 Download Displayed Data as CSV",
    data=csv,
    file_name="usage_stats_display.csv",
    mime="text/csv",
)