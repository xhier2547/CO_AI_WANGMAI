# ===========================================================
# 🧠 Smart Day Clone Fill v2
# เติมวันหายโดยใช้วันเดียวกันของสัปดาห์อื่น + Random ±10%
# พร้อมกรองช่วงเวลา 07:00–22:59
# ===========================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
import os

# ---------- CONFIG ----------
INPUT_FILE = "usage_stats.csv"
OUTPUT_FILE = "usage_stats_filled_days.csv"
START_HOUR = 7
END_HOUR = 23  # exclusive

# ---------- LOAD DATA ----------
print("📥 กำลังโหลดข้อมูล...")
df = pd.read_csv(INPUT_FILE)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp').sort_index()

# ---------- FILTER WORKING HOURS ----------
df = df[(df.index.hour >= START_HOUR) & (df.index.hour < END_HOUR)]
print(f"🕐 ช่วงเวลาที่ใช้: {START_HOUR}:00 - {END_HOUR-1}:59")
print(f"มีข้อมูลทั้งหมด {len(df)} records")

# ---------- FIND MISSING DAYS ----------
all_days = pd.date_range(df.index.min().normalize(), df.index.max().normalize(), freq='D')
existing_days = df.index.normalize().unique()
missing_days = sorted(list(set(all_days) - set(existing_days)))

print(f"📅 มีข้อมูลจริง {len(existing_days)} วัน | ขาด {len(missing_days)} วัน")

# ---------- SMART CLONE FILL ----------
filled_days = []

for missing_day in missing_days:
    weekday = missing_day.day_name()

    # หา "วันอ้างอิง" ของวันเดียวกันในสัปดาห์อื่น
    same_weekdays = [d for d in existing_days if d.day_name() == weekday]
    if not same_weekdays:
        continue

    # เลือกวันอ้างอิงใกล้ที่สุดก่อนหน้า (หรือวันแรกถ้าไม่มี)
    ref_day = max([d for d in same_weekdays if d < missing_day], default=min(same_weekdays))
    ref_data = df.loc[ref_day.strftime("%Y-%m-%d")].copy()

    # ปรับ timestamp ให้เป็นวันที่ใหม่
    ref_data.index = [missing_day + (t - ref_day) for t in ref_data.index]

    # เพิ่ม noise ±10% สำหรับคอลัมน์หลัก
    for col in ['people_count', 'table_used', 'beanbag_used']:
        if col in ref_data.columns:
            ref_data[col] = ref_data[col] * (1 + (random.uniform(-0.1, 0.1)))
            ref_data[col] = ref_data[col].round().clip(lower=0)

    filled_days.append(ref_data)

# ---------- MERGE ----------
if filled_days:
    df_filled = pd.concat([df] + filled_days).sort_index()
else:
    df_filled = df.copy()

# ---------- SAVE ----------
df_filled.reset_index().to_csv(OUTPUT_FILE, index=False)
print(f"✅ บันทึกข้อมูลใหม่เรียบร้อย: {OUTPUT_FILE}")
print(f"รวมวันหลังเติม: {len(df_filled.index.normalize().unique())} วัน")
# ---------- PLOT ----------
plt.figure(figsize=(13, 5))
plt.plot(df.index, df['people_count'], label="raw data", color='gray', alpha=0.6)
plt.plot(df_filled.index, df_filled['people_count'], label="after fill ", color='dodgerblue', linewidth=2)
plt.title(" people count  after fill ")
plt.xlabel("time")
plt.ylabel("people_count")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
