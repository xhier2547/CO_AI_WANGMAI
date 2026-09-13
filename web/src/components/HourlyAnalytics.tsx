'use client';

import React, { useState } from 'react';
import { Clock, Flame } from 'lucide-react';
import { HourlyData, TopDay } from '@/lib/data-service';

interface HourlyAnalyticsProps {
  hourlyByDay: Record<string, HourlyData[]>;
  topDays: TopDay[];
}

const DAYS_OF_WEEK = [
  { key: 'Monday', label: 'วันจันทร์' },
  { key: 'Tuesday', label: 'วันอังคาร' },
  { key: 'Wednesday', label: 'วันพุธ' },
  { key: 'Thursday', label: 'วันพฤหัสบดี' },
  { key: 'Friday', label: 'วันศุกร์' },
  { key: 'Saturday', label: 'วันเสาร์' },
  { key: 'Sunday', label: 'วันอาทิตย์' },
];

export default function HourlyAnalytics({ hourlyByDay, topDays }: HourlyAnalyticsProps) {
  const [selectedDay, setSelectedDay] = useState<string>('Monday');

  const dayData = hourlyByDay[selectedDay] || [];
  const maxVal = Math.max(5, ...dayData.map(d => Math.max(d.people_count, d.table_used, d.beanbag_used)));

  return (
    <div className="space-y-6 mb-6">
      <div className="glass-panel p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 pb-4 border-b border-white/5">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-cyan-400" />
              ช่วงเวลายอดนิยมรายชั่วโมง (08:00 – 23:00)
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              ค่าเฉลี่ยจำนวนผู้ใช้งาน โต๊ะ และบีนแบ็กที่ถูกใช้งานในแต่ละชั่วโมงของวัน
            </p>
          </div>

          <div className="flex items-center flex-wrap gap-1.5 bg-[#101726] p-1 rounded-xl border border-white/5 text-xs">
            {DAYS_OF_WEEK.map(d => (
              <button
                key={d.key}
                onClick={() => setSelectedDay(d.key)}
                className={`px-3 py-1.5 rounded-lg transition font-medium ${
                  selectedDay === d.key
                    ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/25'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4 mb-4 text-xs">
          <span className="flex items-center gap-1.5 text-cyan-300">
            <span className="w-3 h-3 rounded bg-cyan-500" />
            👥 จำนวนคนเฉลี่ย (People)
          </span>
          <span className="flex items-center gap-1.5 text-amber-300">
            <span className="w-3 h-3 rounded bg-amber-500" />
            🪑 โต๊ะที่ใช้งาน (Tables)
          </span>
          <span className="flex items-center gap-1.5 text-emerald-300">
            <span className="w-3 h-3 rounded bg-emerald-500" />
            🛋️ บีนแบ็กที่ใช้งาน (Beanbags)
          </span>
        </div>

        <div className="w-full overflow-x-auto pb-2">
          <div className="min-w-[650px] h-64 flex items-end gap-2.5 pt-8 px-2 border-b border-white/10">
            {dayData.map((d) => {
              const peopleHeight = (d.people_count / maxVal) * 100;
              const tableHeight = (d.table_used / maxVal) * 100;
              const beanbagHeight = (d.beanbag_used / maxVal) * 100;

              return (
                <div key={d.hour} className="flex-1 flex flex-col items-center h-full justify-end group relative">
                  <div className="absolute -top-14 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none bg-slate-900/95 border border-white/15 px-2.5 py-1.5 rounded-lg text-[10px] text-white whitespace-nowrap shadow-xl z-20 flex flex-col gap-0.5">
                    <span className="font-bold text-cyan-300">{d.hour}:00 น.</span>
                    <span>คน: {d.people_count} คน</span>
                    <span>โต๊ะ: {d.table_used} ตัว</span>
                    <span>บีนแบ็ก: {d.beanbag_used} ตัว</span>
                  </div>

                  <div className="w-full flex items-end justify-center gap-0.5 h-full">
                    <div
                      style={{ height: `${Math.max(4, peopleHeight)}%` }}
                      className="w-1/3 bg-cyan-500/80 hover:bg-cyan-400 rounded-t transition-all"
                      title={`People: ${d.people_count}`}
                    />
                    <div
                      style={{ height: `${Math.max(4, tableHeight)}%` }}
                      className="w-1/3 bg-amber-500/80 hover:bg-amber-400 rounded-t transition-all"
                      title={`Tables: ${d.table_used}`}
                    />
                    <div
                      style={{ height: `${Math.max(4, beanbagHeight)}%` }}
                      className="w-1/3 bg-emerald-500/80 hover:bg-emerald-400 rounded-t transition-all"
                      title={`Beanbags: ${d.beanbag_used}`}
                    />
                  </div>

                  <span className="text-[10px] text-slate-400 font-mono mt-2">{d.hour}:00</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/5">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Flame className="w-4 h-4 text-rose-400" />
            วันที่ผู้ใช้งานหนาแน่นที่สุด (Top Busy Days)
          </h3>
          <span className="text-xs text-slate-400">เรียงตามค่าเฉลี่ยจำนวนคนต่อวัน</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-white/10 text-slate-400">
                <th className="py-2.5 px-3 font-semibold">วันที่ (Date)</th>
                <th className="py-2.5 px-3 font-semibold">วันในสัปดาห์</th>
                <th className="py-2.5 px-3 font-semibold text-cyan-300">👥 เฉลี่ยคน (Avg People)</th>
                <th className="py-2.5 px-3 font-semibold text-amber-300">🪑 เฉลี่ยโต๊ะ (Avg Tables)</th>
                <th className="py-2.5 px-3 font-semibold text-emerald-300">🛋️ เฉลี่ยบีนแบ็ก</th>
                <th className="py-2.5 px-3 font-semibold">ชั่วโมงหนาแน่นสุด (Peak Hour)</th>
                <th className="py-2.5 px-3 font-semibold text-rose-300">คนสูงสุดตอน Peak</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {topDays.map((td, idx) => (
                <tr key={td.date} className="hover:bg-white/5 transition-colors">
                  <td className="py-3 px-3 font-mono font-medium text-white flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-slate-800 text-[10px] flex items-center justify-center text-slate-300">
                      #{idx + 1}
                    </span>
                    {td.date}
                  </td>
                  <td className="py-3 px-3 text-slate-300">{td.dayName}</td>
                  <td className="py-3 px-3 font-bold text-cyan-400">{td.avgPeople} คน</td>
                  <td className="py-3 px-3 text-amber-300">{td.avgTables} ตัว</td>
                  <td className="py-3 px-3 text-emerald-300">{td.avgBeanbags} ตัว</td>
                  <td className="py-3 px-3 font-mono text-slate-300">{td.peakHour} น.</td>
                  <td className="py-3 px-3 font-bold text-rose-400">{td.maxPeople} คน</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
