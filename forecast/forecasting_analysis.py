# =========================================================
# 🔮 forecasting_analysis_multi_model.py (✨ FIX: TypeError, Forecast Fail, NameError ✨)
# ---------------------------------------------------------
# 1. Filters data 08:00-17:30, Resamples 30T, m=48(auto)/20(steps).
# 2. Uses auto_arima (P/Q up to 1). Handles NaNs before auto_arima.
# 3. Fits final model on train_fit.
# 4. Hold-out = last 7 days.
# 5. Generates 1/7-day forecasts (Simplified forecast logic).
# 6. Generates interactive/static plots (Fixed NameError).
# =========================================================

import os
import sys
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt # For static plots
import plotly.graph_objects as go # For interactive plots
import joblib
import pmdarima as pm # Import pmdarima
from sklearn.metrics import mean_squared_error, mean_absolute_error
from statsmodels.tsa.statespace.sarimax import SARIMAX
from datetime import timedelta, date, time # Import time

warnings.filterwarnings("ignore")

# =========================================================
# 📂 SETUP & CONFIGURATION
# =========================================================
print("🎯 Running Multi-Model Forecasting Script (FIX: TypeError, Forecast Fail, NameError)")
np.random.seed(42)

INPUT_CSV_PATH = "usage_stats_filled_days.csv"
OUTPUT_DIR = "outputs_forecast"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEASONAL_PERIOD_M_AUTOARIMA = 48
SEASONAL_PERIOD_M_FILTERED = 20
print(f"🔄 Resampling Freq: 30T. Filtering Time: 08:00-17:30.")
print(f"   Using m={SEASONAL_PERIOD_M_AUTOARIMA} for auto_arima, m_filtered={SEASONAL_PERIOD_M_FILTERED} for checks/steps.")

# =========================================================
# 📂 LOAD DATA, RESAMPLE, & FILTER TIME
# =========================================================
try:
    df = pd.read_csv(INPUT_CSV_PATH, parse_dates=["index"])
    df = df.rename(columns={"index": "timestamp"})
    print(f"📂 Loaded {len(df)} rows (original) from {INPUT_CSV_PATH}")
except FileNotFoundError: sys.exit(f"❌ Error: Input file not found at '{INPUT_CSV_PATH}'")
except Exception as e: sys.exit(f"❌ Error while reading file: {e}")

df = df.sort_values("timestamp").set_index("timestamp")

numeric_cols = df.select_dtypes(include=np.number).columns
if not numeric_cols.empty:
    df_resampled = df[numeric_cols].resample('30T').mean().ffill().bfill()
    print(f"📊 Resampled to 30T. Temp size: {len(df_resampled)} rows.")
else: sys.exit("❌ Error: No numeric columns found to resample.")

df_filtered = df_resampled[(df_resampled.index.hour >= 8) & (df_resampled.index.hour < 18)].copy()
if df_filtered.empty: sys.exit("❌ Error: No data found between 08:00 and 18:00.")
df = df_filtered
print(f"🕰️ Filtered time to 08:00-17:30. Final data size: {len(df)} rows.")

exog_cols = ["table_used", "beanbag_used"]
available_exog_cols = [col for col in exog_cols if col in df.columns]
HAS_EXOG = len(available_exog_cols) == len(exog_cols)

cols_to_process = ["people_count"] + (available_exog_cols if HAS_EXOG else [])
print(f"✅ Using columns: {cols_to_process}")
if "people_count" not in df.columns: sys.exit("❌ Error: 'people_count' missing.")

df = df[cols_to_process].clip(lower=0).astype(float) # Ensure float after selection
# ✨ FIX: Double check for NaNs/Infs AFTER all processing before split ✨
df = df.replace([np.inf, -np.inf], np.nan).fillna(0) # Replace Inf with NaN then fill NaN with 0
print(f"✅ Cleaned data ready: {len(df)} records, columns = {cols_to_process}")


# =========================================================
# ✂️ TRAIN/TEST SPLIT (Hold-out Last 7 Days - Filtered Data)
# =========================================================
if df.empty: sys.exit("❌ Error: Filtered DataFrame is empty.")

last_date_in_data = df.index.max().date()
unique_timestamps = df.index.normalize().unique()
unique_dates_list = sorted([ts.date() for ts in unique_timestamps])

if len(unique_dates_list) < 8:
    print(f"⚠️ Warning: Less than 8 unique days ({len(unique_dates_list)}). Hold-out might be shorter.")
    holdout_days_count = min(7, len(unique_dates_list))
    holdout_start_date_actual = unique_dates_list[-holdout_days_count] if holdout_days_count > 0 else last_date_in_data
else: holdout_start_date_actual = unique_dates_list[-7]

holdout_start_timestamp = pd.Timestamp(holdout_start_date_actual)
print(f"🗓️ Last date: {last_date_in_data}, Hold-out starts: {holdout_start_timestamp.date()}")

test = df[df.index >= holdout_start_timestamp]
train_full = df[df.index < holdout_start_timestamp]

if train_full.empty or test.empty: sys.exit("❌ Error: Could not split filtered data.")

fit_period_days = 30
fit_start_date_calc = train_full.index.max().date() - timedelta(days=fit_period_days - 1)
fit_start_timestamp = pd.Timestamp(fit_start_date_calc)
train_fit = train_full[train_full.index >= fit_start_timestamp]

MIN_SAMPLES_FOR_FIT = 3 * SEASONAL_PERIOD_M_FILTERED # Use filtered m for this check (e.g., 3*20=60)
if len(train_fit) < MIN_SAMPLES_FOR_FIT:
    print(f"⚠️ Warning: Recent {fit_period_days} days data ({len(train_fit)}) < {MIN_SAMPLES_FOR_FIT}. Using fallback.")
    if len(train_full) >= MIN_SAMPLES_FOR_FIT: train_fit = train_full.iloc[-MIN_SAMPLES_FOR_FIT:]
    else: train_fit = train_full

print(f"📘 Using {len(train_fit)} samples (from {train_fit.index.min()} to {train_fit.index.max()}) for fitting.")
print(f"   Train size (before hold-out): {len(train_full)}, Test size (hold-out): {len(test)}")

ALLOW_SEASONAL = len(train_fit) >= (2 * SEASONAL_PERIOD_M_FILTERED) # Check using filtered m
if not ALLOW_SEASONAL: print(f"   Disabling SARIMA/SARIMAX (need {2*SEASONAL_PERIOD_M_FILTERED} samples in train_fit, got {len(train_fit)}).")

# =========================================================
# 🔎 AUTO-ARIMA FUNCTION (Reduced Complexity, Robust Inputs)
# =========================================================
def find_best_arima(train_data, seasonal=False, exog=False):
    print(f"Running Stepwise Auto-ARIMA (seasonal={seasonal}, exog={exog})...")
    if seasonal: print(f"   (Allowing p/q/P/Q up to 1, using m={SEASONAL_PERIOD_M_AUTOARIMA})")

    train_exog_df = None
    y_train = train_data["people_count"].astype(float).fillna(0) # Ensure float, fill NaNs

    if exog and HAS_EXOG:
        # ✨ FIX: Ensure exog is float and handle NaNs/Infs rigorously BEFORE passing ✨
        train_exog_df = train_data[available_exog_cols].astype(float)
        train_exog_df = train_exog_df.replace([np.inf, -np.inf], np.nan).fillna(0)
        # Ensure index alignment (should be aligned already but safe check)
        train_exog_df = train_exog_df.reindex(y_train.index).fillna(0)

    MAX_ORDER_P = 1; MAX_ORDER_Q = 1
    MAX_SEASONAL_P = 1; MAX_SEASONAL_Q = 1

    stepwise_model_result = None
    try:
        stepwise_model_result = pm.auto_arima(
            y_train, X=train_exog_df, # Pass cleaned data
            start_p=0, start_q=0, max_p=MAX_ORDER_P, max_q=MAX_ORDER_Q,
            m=SEASONAL_PERIOD_M_AUTOARIMA if seasonal else 1, seasonal=seasonal,
            start_P=0, max_P=MAX_SEASONAL_P,
            start_Q=0, max_Q=MAX_SEASONAL_Q,
            D=1 if seasonal else None, d=None, # Suggest D=1
            trace=False, error_action='ignore', suppress_warnings=True, stepwise=True,
            # n_jobs=-1
        )
    except MemoryError: print("❌ MemoryError during auto_arima."); return None, None
    except Exception as e: print(f"❌ auto_arima error: {e}"); return None, None

    if stepwise_model_result is None: print("❌ Auto ARIMA failed."); return None, None

    print(f"✅ Best Config Found: {stepwise_model_result.order} {stepwise_model_result.seasonal_order}")
    order = stepwise_model_result.order
    seasonal_order = stepwise_model_result.seasonal_order

    # Fit final model with statsmodels
    try:
        # Use the same cleaned exog data
        stats_train_exog = train_exog_df
        final_model = SARIMAX(
            y_train, exog=stats_train_exog, # Use cleaned y_train
            order=order, seasonal_order=seasonal_order,
            enforce_stationarity=False, enforce_invertibility=False,
        )
        fit = final_model.fit(disp=False, maxiter=200)
        return (order, seasonal_order), fit
    except Exception as e:
        print(f"❌ Error fitting final statsmodels model ({order}{seasonal_order}): {e}")
        return (order, seasonal_order), None

# =========================================================
# 🧮 TRAIN MODELS (Fit Final Model on train_fit)
# =========================================================
models, metrics_summary = {}, {}
best_configs = {}

def calc_metrics(y_true, y_pred):
    # (Function remains the same)
    y_true_np = y_true.values if isinstance(y_true, pd.Series) else np.array(y_true)
    y_pred_np = y_pred.values if isinstance(y_pred, pd.Series) else np.array(y_pred)
    y_true_np = np.maximum(y_true_np, 0); y_pred_np = np.maximum(y_pred_np, 0)
    mask = y_true_np > 1e-6
    valid_true = y_true_np[mask]; valid_pred = y_pred_np[mask]
    if len(valid_true) == 0: mape = np.inf
    else: mape = np.mean(np.abs((valid_true - valid_pred) / valid_true)) * 100
    return {"RMSE": np.sqrt(mean_squared_error(y_true_np, y_pred_np)), "MAE": mean_absolute_error(y_true_np, y_pred_np), "MAPE": mape}

model_definitions = [("ARIMA", False, False)]
if ALLOW_SEASONAL: model_definitions.append(("SARIMA", True, False))
if ALLOW_SEASONAL and HAS_EXOG: model_definitions.append(("SARIMAX", True, True))

# --- Step 1: Find best config using auto_arima on train_fit ---
for name, seasonal, exog in model_definitions:
    print(f"\n🚀 Finding best config for {name}...")
    best_cfg_found, _ = find_best_arima(train_fit, seasonal=seasonal, exog=exog)
    if best_cfg_found: best_configs[name] = best_cfg_found
    else: print(f"❌ Failed to find config for {name}.")

# --- Step 2: Fit final model using best config on train_fit and evaluate ---
print("\n🚀 Fitting final models on recent data (train_fit) & evaluating...")
for name, best_cfg in best_configs.items():
    print(f"   Fitting {name} config {best_cfg} on {len(train_fit)} samples...")
    order, seasonal_order = best_cfg
    exog_model = name == "SARIMAX"
    final_model = None
    try:
        train_fit_exog = None
        if exog_model and HAS_EXOG:
             train_fit_exog = train_fit[available_exog_cols].astype(float).replace([np.inf, -np.inf], np.nan).fillna(0)
             train_fit_exog = train_fit_exog.reindex(train_fit.index).fillna(0)

        final_model_obj = SARIMAX(
            train_fit["people_count"].astype(float).fillna(0), # Use train_fit, ensure clean
            exog=train_fit_exog,
            order=order, seasonal_order=seasonal_order,
            enforce_stationarity=False, enforce_invertibility=False,
        )
        final_model = final_model_obj.fit(disp=False, maxiter=200)
        print(f"   ✅ {name} fitted successfully.")

        # --- Step 3: Predict the hold-out period (test) ---
        test_exog_df = None
        if exog_model and HAS_EXOG:
             test_exog_df = test[available_exog_cols].astype(float).replace([np.inf, -np.inf], np.nan)
             # Fill NaNs using train_fit mean
             for col in available_exog_cols:
                  col_mean = train_fit[col].mean() if not train_fit[col].isnull().all() else 0
                  test_exog_df[col] = test_exog_df[col].fillna(col_mean)
             test_exog_df = test_exog_df.reindex(test.index).fillna(0) # Ensure alignment and fill remaining

        pred = final_model.forecast(steps=len(test), exog=test_exog_df)
        pred.index = test.index
        pred = pred.fillna(0); pred = np.maximum(pred, 0)
        target = test["people_count"]

        if not pred.isnull().all() and not target.isnull().all() and pred.shape == target.shape:
             metrics = calc_metrics(target, pred)
             metrics_summary[name] = metrics
             models[name] = final_model # Store the successfully fitted model
             print(f"   ✅ {name} Hold-out Test -> RMSE: {metrics['RMSE']:.3f}, MAE: {metrics['MAE']:.3f}, MAPE: {metrics['MAPE']:.1f}%")
        else: print(f"   ⚠️ Skipping metrics for {name}.")

    except MemoryError: print(f"   ❌ MemoryError fitting {name}. Skipping.")
    except Exception as e: print(f"   ❌ Error fitting/predicting {name}: {e}")
    if name not in metrics_summary and name in models: del models[name]


if not models: sys.exit("\n❌❌ CRITICAL: No models fitted successfully.")

metrics_df = pd.DataFrame(metrics_summary).T
print("\n📊 Hold-out Validation Metrics Summary (Filtered Time):")
print(metrics_df)

# =========================================================
# 🔮 GENERATE FORECASTS (1-Day and 7-Day - ✨ Simplified Logic ✨)
# =========================================================
print("\n🔮 Generating forecasts (Filtered Time 08:00-17:30)...")
last_timestamp = df.index[-1] # Use end of filtered df

exog_future_base_dict = {}
if HAS_EXOG:
    for col in available_exog_cols:
         col_mean = train_fit[col].mean() if not train_fit[col].isnull().all() else 0
         exog_future_base_dict[col] = col_mean
    print(f"   Using mean exog values for future: {exog_future_base_dict}")

# --- Function to Generate Forecast (Simplified) ---
def generate_forecast(n_days, suffix):
    n_steps = n_days * SEASONAL_PERIOD_M_FILTERED # Steps within filtered window
    print(f"   Generating {suffix} forecast ({n_steps} steps)...")
    local_forecast_results = {}

    # Create the target index for the filtered time slots
    target_future_index = pd.date_range(
        start=last_timestamp + timedelta(minutes=30),
        periods=n_days * 48, # Create full index first
        freq="30T"
    )
    target_future_index = target_future_index[(target_future_index.hour >= 8) & (target_future_index.hour < 18)]
    n_steps = len(target_future_index) # Actual number of steps needed
    if n_steps == 0:
        print(f"      ⚠️ No valid future timestamps for {suffix}.")
        return {}, None


    local_exog_future = None
    if HAS_EXOG and exog_future_base_dict:
         exog_dict = {col: np.full(n_steps, mean_val) for col, mean_val in exog_future_base_dict.items()}
         local_exog_future = pd.DataFrame(exog_dict, index=target_future_index).astype(float)

    for name, model in models.items():
        fc = None
        try:
            needs_exog = (name == "SARIMAX") and (local_exog_future is not None)

            # ✨ FIX: Predict exactly n_steps needed ✨
            if hasattr(model, 'forecast'):
                 if needs_exog:
                      fc = model.forecast(steps=n_steps, exog=local_exog_future)
                 elif name != "SARIMAX":
                      fc = model.forecast(steps=n_steps)
                 elif name == "SARIMAX" and local_exog_future is None and HAS_EXOG: continue

                 if fc is not None:
                      # Assign the correct index
                      fc.index = target_future_index
                      forecast_values = fc.values
                      forecast_values = np.maximum(forecast_values, 0); forecast_values = np.nan_to_num(forecast_values)
                      local_forecast_results[name] = pd.DataFrame({"timestamp": target_future_index, name: forecast_values})
                 else: print(f"      ⚠️ Forecast failed for {name} ({suffix}).")

            else: continue # Skip if no forecast method
        except Exception as e: print(f"      ❌ Error forecasting {name} ({suffix}): {e}")

    return local_forecast_results, target_future_index

# --- Generate Both Forecasts ---
forecast_1day, index_1day = generate_forecast(n_days=1, suffix="1-day")
forecast_7day, index_7day = generate_forecast(n_days=7, suffix="7-day")

# =========================================================
# 📁 SAVE RESULTS (Filtered Time Forecasts)
# =========================================================
# (Saving logic remains the same, filenames indicate filtered time)
print(f"\n💾 Saving results to '{OUTPUT_DIR}'...")
if forecast_1day and index_1day is not None:
    merged_1day = pd.DataFrame({"timestamp": index_1day})
    for name, data in forecast_1day.items(): merged_1day = pd.merge(merged_1day, data, on="timestamp", how="left")
    merged_1day = merged_1day.fillna(0)
    merged_1day.to_csv(os.path.join(OUTPUT_DIR, "forecast_results_1day_filtered.csv"), index=False)
    print("✅ Saved forecast_results_1day_filtered.csv")
else: print("⚠️ No 1-day forecasts.")

if forecast_7day and index_7day is not None:
    merged_7day = pd.DataFrame({"timestamp": index_7day})
    for name, data in forecast_7day.items(): merged_7day = pd.merge(merged_7day, data, on="timestamp", how="left")
    merged_7day = merged_7day.fillna(0)
    merged_7day.to_csv(os.path.join(OUTPUT_DIR, "forecast_results_7day_filtered.csv"), index=False)
    print("✅ Saved forecast_results_7day_filtered.csv")
else: print("⚠️ No 7-day forecasts.")

if not metrics_df.empty:
    metrics_df.to_csv(os.path.join(OUTPUT_DIR, "holdout_validation_metrics_filtered.csv"))
    print("✅ Saved holdout_validation_metrics_filtered.csv")

if models:
    for name, model in models.items(): joblib.dump(model, os.path.join(OUTPUT_DIR, f"{name}_model_filtered_time.pkl"))
    print(f"✅ {len(models)} Models saved.")
else: print("⚠️ No models trained.")

# =========================================================
# 📊 PLOTS (✨ Fixed NameError ✨ + Filtered Time Data)
# =========================================================
print("\n📊 Generating Plots...")
# ✨ FIX: Use last_date_in_data which is defined earlier ✨
last_date_in_data_str = last_date_in_data.strftime('%Y-%m-%d') if isinstance(last_date_in_data, date) else str(last_date_in_data)

try:
    # --- Plot 1: Hold-out Validation Comparison (Interactive HTML) ---
    if models and not test.empty: # test is already filtered
        fig_val_html = go.Figure()
        fig_val_html.add_trace(go.Scatter(x=test.index, y=test["people_count"], mode='lines', name=f'Actual ({last_date_in_data_str} 08-18)', line=dict(color='black', width=2)))
        plotted_preds_html = False
        for name, model in models.items():
             try:
                 test_exog_df_plot = None
                 if name == "SARIMAX" and HAS_EXOG:
                      test_exog_df_plot = test[available_exog_cols].astype(float)
                      # Fill NaNs using train_fit mean
                      for col in available_exog_cols:
                           col_mean = train_fit[col].mean() if not train_fit[col].isnull().all() else 0
                           test_exog_df_plot[col] = test_exog_df_plot[col].fillna(col_mean)
                 pred_plot_vals = model.forecast(steps=len(test), exog=test_exog_df_plot)
                 pred_plot = pd.Series(pred_plot_vals, index=test.index).fillna(0).clip(lower=0)
                 fig_val_html.add_trace(go.Scatter(x=pred_plot.index, y=pred_plot.values, mode='lines', name=f'{name} Forecast', line=dict(dash='dot')))
                 plotted_preds_html = True
             except Exception as plot_pred_err: print(f"   ⚠️ Error plotting {name} holdout: {plot_pred_err}")
        if plotted_preds_html:
            fig_val_html.update_layout(title=f'Hold-out Validation ({last_date_in_data_str} 08:00-17:30)', xaxis_title='Time', yaxis_title='People Count', template='plotly_white', hovermode='x unified', legend_title_text='Models')
            html_save_path = os.path.join(OUTPUT_DIR, "holdout_validation_plot_filtered.html")
            fig_val_html.write_html(html_save_path)
            print(f"✅ Saved Interactive Plot: {os.path.basename(html_save_path)}")
        else: print("⚠️ No valid hold-out predictions plotted.")
    else: print("⚠️ Skipping hold-out HTML plot.")

    # --- Plot 2: 7-Day Forecast (Interactive HTML - Filtered Time) ---
    if forecast_7day:
        fig_fc7_html = go.Figure()
        recent_actual_start_dt = df.index.max() - timedelta(days=3)
        recent_actual = df[df.index >= recent_actual_start_dt] # df is already filtered
        if not recent_actual.empty: fig_fc7_html.add_trace(go.Scatter(x=recent_actual.index, y=recent_actual["people_count"], mode="lines", name="Recent Actual (08-18)", line=dict(color="black")))
        plot_fc7 = False
        for name, data in forecast_7day.items():
             if isinstance(data, pd.DataFrame) and not data.empty:
                fig_fc7_html.add_trace(go.Scatter(x=data["timestamp"], y=data[name], mode="lines", name=f"{name} Forecast (7d, 08-18)", line=dict(dash="dot")))
                plot_fc7 = True
        if plot_fc7:
            fig_fc7_html.update_layout(title="7-Day Future Forecast (08:00-17:30 Daily)", xaxis_title="Time", yaxis_title="People Count", template='plotly_white', hovermode='x unified', legend_title_text='Models')
            html_fc7_save_path = os.path.join(OUTPUT_DIR, "forecast_plot_7day_filtered.html")
            fig_fc7_html.write_html(html_fc7_save_path)
            print(f"✅ Saved Interactive Plot: {os.path.basename(html_fc7_save_path)}")
        else: print("⚠️ No valid 7-day forecasts plotted.")
    else: print("⚠️ No 7-day forecast results.")

    # --- Plot 3: Metrics Comparison (Static PNG) ---
    if not metrics_df.empty:
        try:
            fig_metrics, ax_metrics = plt.subplots(figsize=(8, 5))
            metrics_df.plot(kind="bar", ax=ax_metrics, rot=0)
            ax_metrics.set_title("Hold-out Validation Performance (Filtered Time)"); ax_metrics.set_ylabel("Error Value"); ax_metrics.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            png_metrics_save_path = os.path.join(OUTPUT_DIR, "holdout_metrics_comparison_filtered.png")
            plt.savefig(png_metrics_save_path); plt.close(fig_metrics)
            print(f"✅ Saved Static Plot: {os.path.basename(png_metrics_save_path)}")
        except Exception as e: print(f"⚠️ Error plotting metrics: {e}"); plt.close(fig_metrics) if 'fig_metrics' in locals() else None
    else: print("⚠️ No metrics available.")

    # --- Plot 4: Residuals Comparison (Static PNG) ---
    if models:
        try:
            fig_resid, ax_resid = plt.subplots(figsize=(12, 6))
            plot_resid = False
            for name, model in models.items():
                 if hasattr(model, 'resid') and model.resid is not None:
                     ax_resid.plot(model.resid.values, label=f"{name} Residuals (Train Fit)", alpha=0.7)
                     plot_resid = True
            if plot_resid:
                ax_resid.set_title("Residuals Comparison (Recent Data - Filtered Time)"); ax_resid.set_ylabel("Residual Value")
                ax_resid.legend(); ax_resid.grid(True, linestyle='--', alpha=0.6)
                plt.tight_layout()
                png_resid_save_path = os.path.join(OUTPUT_DIR, "residuals_comparison_filtered.png")
                plt.savefig(png_resid_save_path)
                print(f"✅ Saved Static Plot: {os.path.basename(png_resid_save_path)}")
            else: print("⚠️ No valid residuals found.")
            plt.close(fig_resid)
        except Exception as e: print(f"⚠️ Error plotting residuals: {e}"); plt.close(fig_resid) if 'fig_resid' in locals() else None
    else: print("⚠️ No models available.")
    # --- Plot 5: SARIMAX Diagnostic Plots (Static PNG - 4-in-1) ---
    SARIMAX_model_results = models.get("SARIMAX")
    if SARIMAX_model_results:
        print("\n   Generating SARIMAX Diagnostic Plots...")
        try:
            # ใช้ .plot_diagnostics() เพื่อสร้างพล็อต 4 แผ่นตามมาตรฐาน:
            # 1. Standardized Residuals (Residuals vs. Time)
            # 2. Histogram plus KDE
            # 3. Normal Q-Q
            # 4. Correlogram (ACF)
            fig_sarimax_diag = SARIMAX_model_results.plot_diagnostics(figsize=(15, 10))
            png_diag_save_path = os.path.join(OUTPUT_DIR, "sarimax_residuals_diagnostics.png")
            fig_sarimax_diag.savefig(png_diag_save_path)
            plt.close(fig_sarimax_diag)
            print(f"   ✅ Saved Static Plot: {os.path.basename(png_diag_save_path)}")
        except Exception as e:
            print(f"   ❌ Error plotting SARIMAX diagnostics: {e}")
            plt.close()

    else:
        print("   ⚠️ SARIMAX model not available or failed to fit. Cannot generate diagnostics.")
except Exception as e:
    print(f"❌ An error occurred during plotting: {e}")

print("\n✅ Plot generation complete.")
print("\n✅ Process complete.")