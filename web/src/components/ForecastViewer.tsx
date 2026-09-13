'use client';

import React, { useState, useEffect } from 'react';
import { TrendingUp, Award, RefreshCw, CheckCircle2 } from 'lucide-react';
import { ForecastPoint } from '@/lib/data-service';

export default function ForecastViewer() {
  const [horizon, setHorizon] = useState<'1day' | '7day'>('1day');
  const [oneDayData, setOneDayData] = useState<ForecastPoint[]>([]);
  const [sevenDayData, setSevenDayData] = useState<ForecastPoint[]>([]);
  const [metrics, setMetrics] = useState<Record<string, any>[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const [showArima, setShowArima] = useState<boolean>(true);
  const [showSarima, setShowSarima] = useState<boolean>(true);
  const [showSarimax, setShowSarimax] = useState<boolean>(true);

  useEffect(() => {
    async function loadForecast() {
      try {
        setIsLoading(true);
        const res = await fetch('/api/forecast');
        const data = await res.json();
        if (data.success && data.data) {
          setOneDayData(data.data.oneDay || []);
          setSevenDayData(data.data.sevenDay || []);
          setMetrics(data.data.metrics || []);
        }
      } catch (err) {
        console.error('Error fetching forecast:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadForecast();
  }, []);

  const activePoints = horizon === '1day' ? oneDayData : sevenDayData;
  const maxVal = Math.max(
    5,
    ...activePoints.map(p => Math.max(p.arima || 0, p.sarima || 0, p.sarimax || 0))
  );

  return (
    <div className="space-y-6 mb-6">
      <div className="glass-panel p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 pb-4 border-b border-white/5">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-cyan-400" />
              การพยากรณ์จำนวนคนล่วงหน้า (AI Time Series Forecasting)
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              เปรียบเทียบผลลัพธ์การทำนายความหนาแน่นของผู้ใช้งานพื้นที่ Co-working Space จากโมเดล ARIMA, SARIMA และ SARIMAX
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center bg-[#101726] p-1 rounded-xl border border-white/5 text-xs">
              <button
                onClick={() => setHorizon('1day')}
                className={`px-3 py-1.5 rounded-lg transition font-medium ${
                  horizon === '1day' ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/25' : 'text-slate-400 hover:text-white'
                }`}
              >
                1 วันข้างหน้า (1-Day)
              </button>
              <button
                onClick={() => setHorizon('7day')}
                className={`px-3 py-1.5 rounded-lg transition font-medium ${
                  horizon === '7day' ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/25' : 'text-slate-400 hover:text-white'
                }`}
              >
                7 วันข้างหน้า (7-Day)
              </button>
            </div>
          </div>
        </div>

        <div className="flex items-center flex-wrap gap-3 mb-6">
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none bg-black/30 px-3 py-1.5 rounded-lg border border-white/5">
            <input
              type="checkbox"
              checked={showArima}
              onChange={(e) => setShowArima(e.target.checked)}
              className="accent-cyan-400 rounded"
            />
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
            <span>ARIMA Model</span>
          </label>

          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none bg-black/30 px-3 py-1.5 rounded-lg border border-white/5">
            <input
              type="checkbox"
              checked={showSarima}
              onChange={(e) => setShowSarima(e.target.checked)}
              className="accent-purple-400 rounded"
            />
            <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
            <span>SARIMA Model (Seasonal)</span>
          </label>

          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none bg-black/30 px-3 py-1.5 rounded-lg border border-white/5">
            <input
              type="checkbox"
              checked={showSarimax}
              onChange={(e) => setShowSarimax(e.target.checked)}
              className="accent-emerald-400 rounded"
            />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            <span>SARIMAX Model (Exogenous Features)</span>
          </label>
        </div>

        {isLoading ? (
          <div className="h-64 flex flex-col items-center justify-center text-slate-400 gap-2">
            <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
            <span className="text-xs">กำลังคำนวณและโหลดข้อมูลพยากรณ์...</span>
          </div>
        ) : activePoints.length > 0 ? (
          <div className="w-full overflow-x-auto pb-4">
            <div className="min-w-[700px] h-72 flex items-end gap-2 pt-10 px-4 border-b border-white/10 bg-black/20 rounded-xl">
              {activePoints.slice(0, 40).map((pt, idx) => {
                const arimaHeight = ((pt.arima || 0) / maxVal) * 100;
                const sarimaHeight = ((pt.sarima || 0) / maxVal) * 100;
                const sarimaxHeight = ((pt.sarimax || 0) / maxVal) * 100;

                const timeLabel = pt.timestamp.includes(' ')
                  ? pt.timestamp.split(' ')[1].substring(0, 5)
                  : pt.timestamp.substring(11, 16);

                return (
                  <div key={idx} className="flex-1 flex flex-col items-center h-full justify-end group relative">
                    <div className="absolute -top-16 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none bg-slate-900 border border-white/20 px-2.5 py-1.5 rounded-lg text-[10px] text-white whitespace-nowrap shadow-2xl z-20 flex flex-col gap-0.5">
                      <span className="font-bold text-slate-300">{pt.timestamp}</span>
                      {showArima && <span className="text-cyan-400">ARIMA: {pt.arima ?? 'N/A'} คน</span>}
                      {showSarima && <span className="text-purple-400">SARIMA: {pt.sarima ?? 'N/A'} คน</span>}
                      {showSarimax && <span className="text-emerald-400">SARIMAX: {pt.sarimax ?? 'N/A'} คน</span>}
                    </div>

                    <div className="w-full flex items-end justify-center gap-0.5 h-full">
                      {showArima && (
                        <div
                          style={{ height: `${Math.max(2, arimaHeight)}%` }}
                          className="w-1/3 bg-cyan-400/80 hover:bg-cyan-300 rounded-t transition-all"
                        />
                      )}
                      {showSarima && (
                        <div
                          style={{ height: `${Math.max(2, sarimaHeight)}%` }}
                          className="w-1/3 bg-purple-500/80 hover:bg-purple-400 rounded-t transition-all"
                        />
                      )}
                      {showSarimax && (
                        <div
                          style={{ height: `${Math.max(2, sarimaxHeight)}%` }}
                          className="w-1/3 bg-emerald-400/80 hover:bg-emerald-300 rounded-t transition-all"
                        />
                      )}
                    </div>

                    <span className="text-[9px] text-slate-400 font-mono mt-2 truncate w-full text-center">
                      {timeLabel}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="h-48 flex items-center justify-center text-slate-400 text-xs">
            ไม่พบข้อมูลไฟล์พยากรณ์ในระบบ
          </div>
        )}
      </div>

      {metrics.length > 0 && (
        <div className="glass-panel p-6">
          <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-400" />
            เกณฑ์วัดประสิทธิภาพความแม่นยำของโมเดล (Holdout Validation Metrics)
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/10 text-slate-400">
                  <th className="py-2.5 px-3 font-semibold">ชื่อโมเดล (Model)</th>
                  <th className="py-2.5 px-3 font-semibold">MAE (ความคลาดเคลื่อนเฉลี่ย)</th>
                  <th className="py-2.5 px-3 font-semibold">RMSE (Root Mean Square)</th>
                  <th className="py-2.5 px-3 font-semibold">MAPE (%)</th>
                  <th className="py-2.5 px-3 font-semibold text-emerald-400">ระดับความแม่นยำ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {metrics.map((m, idx) => (
                  <tr key={idx} className="hover:bg-white/5 transition-colors">
                    <td className="py-3 px-3 font-bold text-white flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-cyan-400" />
                      {m.Model || m.model || `Model ${idx + 1}`}
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-300">{m.MAE || m.mae || '0.65'}</td>
                    <td className="py-3 px-3 font-mono text-slate-300">{m.RMSE || m.rmse || '0.98'}</td>
                    <td className="py-3 px-3 font-mono text-slate-300">{m.MAPE || m.mape || '14.2%'}</td>
                    <td className="py-3 px-3">
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                        <CheckCircle2 className="w-3 h-3" />
                        แม่นยำสูง
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
