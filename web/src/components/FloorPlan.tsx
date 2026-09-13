'use client';

import React, { useState } from 'react';
import { Layers, CheckCircle2, XCircle, Info, Zap, Users, Armchair, Coffee } from 'lucide-react';
import { LiveStats } from '@/lib/data-service';

interface FloorPlanProps {
  stats: LiveStats;
}

interface TableSpot {
  id: string;
  name: string;
  type: 'table' | 'beanbag';
  zone: string;
  seats: number;
  hasPower: boolean;
  x: number;
  y: number;
  width: number;
  height: number;
}

const ROOM_SPOTS: TableSpot[] = [
  { id: 'T1', name: 'โต๊ะเดี่ยว Focus #01', type: 'table', zone: 'Focus Pods', seats: 1, hasPower: true, x: 12, y: 18, width: 14, height: 12 },
  { id: 'T2', name: 'โต๊ะเดี่ยว Focus #02', type: 'table', zone: 'Focus Pods', seats: 1, hasPower: true, x: 12, y: 35, width: 14, height: 12 },
  { id: 'T3', name: 'โต๊ะคู่ Focus Duo #03', type: 'table', zone: 'Focus Pods', seats: 2, hasPower: true, x: 12, y: 55, width: 14, height: 14 },
  { id: 'T4', name: 'โต๊ะคู่ Focus Duo #04', type: 'table', zone: 'Focus Pods', seats: 2, hasPower: true, x: 12, y: 75, width: 14, height: 14 },

  { id: 'T5', name: 'โต๊ะกลาง Team #05', type: 'table', zone: 'Collaborative Hub', seats: 4, hasPower: true, x: 38, y: 22, width: 22, height: 16 },
  { id: 'T6', name: 'โต๊ะกลาง Team #06', type: 'table', zone: 'Collaborative Hub', seats: 4, hasPower: true, x: 38, y: 48, width: 22, height: 16 },
  { id: 'T7', name: 'โต๊ะคุยงาน Discussion #07', type: 'table', zone: 'Collaborative Hub', seats: 3, hasPower: true, x: 38, y: 74, width: 22, height: 14 },

  { id: 'T8', name: 'โต๊ะวิวหน้าต่าง Window #08', type: 'table', zone: 'Window View', seats: 2, hasPower: true, x: 70, y: 15, width: 18, height: 11 },
  { id: 'T9', name: 'โต๊ะวิวหน้าต่าง Window #09', type: 'table', zone: 'Window View', seats: 2, hasPower: true, x: 70, y: 30, width: 18, height: 11 },
  { id: 'T10', name: 'โต๊ะวิวหน้าต่าง Window #10', type: 'table', zone: 'Window View', seats: 2, hasPower: true, x: 70, y: 45, width: 18, height: 11 },

  { id: 'B1', name: 'บีนแบ็ก Lounge A1', type: 'beanbag', zone: 'Chill Lounge', seats: 1, hasPower: false, x: 68, y: 68, width: 11, height: 11 },
  { id: 'B2', name: 'บีนแบ็ก Lounge A2', type: 'beanbag', zone: 'Chill Lounge', seats: 1, hasPower: false, x: 82, y: 68, width: 11, height: 11 },
  { id: 'B3', name: 'บีนแบ็ก Lounge B1', type: 'beanbag', zone: 'Chill Lounge', seats: 1, hasPower: false, x: 68, y: 82, width: 11, height: 11 },
  { id: 'B4', name: 'บีนแบ็ก Lounge B2', type: 'beanbag', zone: 'Chill Lounge', seats: 1, hasPower: false, x: 82, y: 82, width: 11, height: 11 },
  { id: 'B5', name: 'บีนแบ็ก Center B3', type: 'beanbag', zone: 'Chill Lounge', seats: 1, hasPower: false, x: 75, y: 75, width: 10, height: 10 },
];

export default function FloorPlan({ stats }: FloorPlanProps) {
  const [selectedSpot, setSelectedSpot] = useState<TableSpot | null>(null);
  const [filterType, setFilterType] = useState<'all' | 'table' | 'beanbag'>('all');

  const tableOccupiedCount = stats.table_used;
  const beanbagOccupiedCount = stats.beanbag_used;

  const tables = ROOM_SPOTS.filter(s => s.type === 'table');
  const beanbags = ROOM_SPOTS.filter(s => s.type === 'beanbag');

  const isSpotOccupied = (spot: TableSpot): boolean => {
    if (spot.type === 'table') {
      const idx = tables.findIndex(t => t.id === spot.id);
      return idx < tableOccupiedCount;
    } else {
      const idx = beanbags.findIndex(b => b.id === spot.id);
      return idx < beanbagOccupiedCount;
    }
  };

  const filteredSpots = ROOM_SPOTS.filter(s => filterType === 'all' || s.type === filterType);

  const availableTables = Math.max(0, stats.table_total - stats.table_used);
  const availableBeanbags = Math.max(0, stats.beanbag_total - stats.beanbag_used);

  return (
    <div className="glass-panel p-6 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 pb-4 border-b border-white/5">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            แผนผังจำลอง Co-working Space (Interactive Floor Plan)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            แสดงสถานะความพร้อมใช้งานของโต๊ะทำงานและบีนแบ็กแบบ Real-time ตามผลวิเคราะห์จากกล้อง AI
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2">
          <div className="flex items-center gap-3 bg-black/40 px-3 py-1.5 rounded-lg border border-white/5 text-xs mr-2">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
              ว่าง (Available)
            </span>
            <span className="flex items-center gap-1.5 text-rose-400">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50" />
              มีคนนั่ง (Occupied)
            </span>
          </div>

          <div className="flex items-center bg-[#101726] p-1 rounded-lg border border-white/5 text-xs">
            <button
              onClick={() => setFilterType('all')}
              className={`px-2.5 py-1 rounded-md transition ${filterType === 'all' ? 'bg-cyan-500 text-white font-medium' : 'text-slate-400 hover:text-white'}`}
            >
              ทั้งหมด
            </button>
            <button
              onClick={() => setFilterType('table')}
              className={`px-2.5 py-1 rounded-md transition ${filterType === 'table' ? 'bg-cyan-500 text-white font-medium' : 'text-slate-400 hover:text-white'}`}
            >
              โต๊ะทำงาน ({stats.table_total})
            </button>
            <button
              onClick={() => setFilterType('beanbag')}
              className={`px-2.5 py-1 rounded-md transition ${filterType === 'beanbag' ? 'bg-cyan-500 text-white font-medium' : 'text-slate-400 hover:text-white'}`}
            >
              บีนแบ็ก ({stats.beanbag_total})
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8">
          <div className="relative w-full aspect-[16/10] bg-[#070b12] rounded-2xl border border-white/10 overflow-hidden shadow-2xl p-4 select-none">
            <div
              className="absolute inset-0 opacity-15"
              style={{
                backgroundImage: 'radial-gradient(#38bdf8 1px, transparent 1px), radial-gradient(#38bdf8 1px, #070b12 1px)',
                backgroundSize: '24px 24px',
                backgroundPosition: '0 0, 12px 12px',
              }}
            />

            <div className="absolute top-3 left-4 text-[10px] font-mono tracking-widest text-slate-500 uppercase flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              CO-WORKING MAIN FLOOR • AI SENSING AREA
            </div>
            <div className="absolute bottom-3 right-4 text-[10px] font-mono text-slate-500">
              ENTRANCE / DOORWAY →
            </div>

            <div className="absolute top-10 left-3 w-[26%] h-[82%] border border-dashed border-cyan-500/10 rounded-xl pointer-events-none flex flex-col justify-end p-2">
              <span className="text-[10px] font-semibold text-cyan-400/40 uppercase tracking-wider">Quiet Focus Zone</span>
            </div>
            <div className="absolute top-10 left-[32%] w-[32%] h-[82%] border border-dashed border-amber-500/10 rounded-xl pointer-events-none flex flex-col justify-end p-2">
              <span className="text-[10px] font-semibold text-amber-400/40 uppercase tracking-wider">Collaborative Hub</span>
            </div>
            <div className="absolute top-10 right-3 w-[32%] h-[82%] border border-dashed border-purple-500/10 rounded-xl pointer-events-none flex flex-col justify-end p-2">
              <span className="text-[10px] font-semibold text-purple-400/40 uppercase tracking-wider">Lounge & Window Bar</span>
            </div>

            {filteredSpots.map((spot) => {
              const occupied = isSpotOccupied(spot);
              const isSelected = selectedSpot?.id === spot.id;

              return (
                <div
                  key={spot.id}
                  onClick={() => setSelectedSpot(spot)}
                  style={{
                    left: `${spot.x}%`,
                    top: `${spot.y}%`,
                    width: `${spot.width}%`,
                    height: `${spot.height}%`,
                  }}
                  className={`absolute rounded-xl transition-all duration-300 cursor-pointer flex flex-col items-center justify-center p-1 border shadow-lg ${
                    occupied
                      ? isSelected
                        ? 'bg-rose-500/30 border-rose-400 text-rose-200 glow-rose scale-105 z-20'
                        : 'bg-rose-950/40 hover:bg-rose-900/50 border-rose-500/50 text-rose-300 hover:scale-102 z-10'
                      : isSelected
                      ? 'bg-emerald-500/30 border-emerald-400 text-emerald-200 glow-emerald scale-105 z-20'
                      : 'bg-emerald-950/40 hover:bg-emerald-900/50 border-emerald-500/50 text-emerald-300 hover:scale-102 z-10'
                  }`}
                  title={`${spot.name} - ${occupied ? 'มีคนนั่ง' : 'ว่าง'}`}
                >
                  <div className="flex items-center gap-1 font-bold text-xs">
                    {spot.type === 'table' ? (
                      <Coffee className="w-3 h-3 opacity-80" />
                    ) : (
                      <Armchair className="w-3 h-3 opacity-80" />
                    )}
                    <span>{spot.id}</span>
                  </div>

                  <span className={`text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.2 rounded mt-0.5 ${
                    occupied ? 'bg-rose-500/20 text-rose-300' : 'bg-emerald-500/20 text-emerald-300'
                  }`}>
                    {occupied ? 'BUSY' : 'FREE'}
                  </span>

                  {spot.hasPower && (
                    <div className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-slate-900 border border-amber-400/60 flex items-center justify-center text-amber-300 shadow-sm" title="มีปลั๊กไฟ">
                      <Zap className="w-2.5 h-2.5" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="lg:col-span-4 flex flex-col justify-between space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-[#101726] border border-white/5 rounded-xl p-3.5">
              <span className="text-xs text-slate-400 block mb-1">โต๊ะว่างพร้อมใช้</span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-bold text-emerald-400">{availableTables}</span>
                <span className="text-xs text-slate-400">/ {stats.table_total}</span>
              </div>
            </div>
            <div className="bg-[#101726] border border-white/5 rounded-xl p-3.5">
              <span className="text-xs text-slate-400 block mb-1">บีนแบ็กว่าง</span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-bold text-emerald-400">{availableBeanbags}</span>
                <span className="text-xs text-slate-400">/ {stats.beanbag_total}</span>
              </div>
            </div>
          </div>

          <div className="bg-[#0f172a]/90 rounded-xl border border-white/10 p-5 flex-1 flex flex-col justify-between">
            {selectedSpot ? (
              <div>
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-white/10">
                  <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold ${
                      isSpotOccupied(selectedSpot) ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
                    }`}>
                      {selectedSpot.id}
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">{selectedSpot.name}</h4>
                      <p className="text-xs text-slate-400">{selectedSpot.zone}</p>
                    </div>
                  </div>
                  <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${
                    isSpotOccupied(selectedSpot)
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  }`}>
                    {isSpotOccupied(selectedSpot) ? <XCircle className="w-3 h-3" /> : <CheckCircle2 className="w-3 h-3" />}
                    {isSpotOccupied(selectedSpot) ? 'มีคนใช้งาน' : 'ว่างพร้อมนั่ง'}
                  </span>
                </div>

                <div className="space-y-2.5 text-xs">
                  <div className="flex justify-between py-1.5 border-b border-white/5">
                    <span className="text-slate-400 flex items-center gap-1.5">
                      <Users className="w-3.5 h-3.5 text-cyan-400" />
                      ความจุที่นั่ง (Seats)
                    </span>
                    <span className="font-semibold text-white">{selectedSpot.seats} ที่นั่ง</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-white/5">
                    <span className="text-slate-400 flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5 text-amber-400" />
                      ปลั๊กไฟ (Power Outlets)
                    </span>
                    <span className="font-semibold text-white">{selectedSpot.hasPower ? 'มีพร้อมใช้งาน' : 'ไม่มี'}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-white/5">
                    <span className="text-slate-400 flex items-center gap-1.5">
                      <Coffee className="w-3.5 h-3.5 text-purple-400" />
                      ประเภทจุดบริการ
                    </span>
                    <span className="font-semibold text-white capitalize">{selectedSpot.type}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center text-center p-6 my-auto">
                <Info className="w-8 h-8 text-cyan-400/50 mb-2" />
                <h5 className="text-sm font-medium text-slate-300">คลิกเลือกโต๊ะบนแผนผัง</h5>
                <p className="text-xs text-slate-500 mt-1 max-w-xs">
                  เพื่อดูรายละเอียดจำนวนที่นั่ง ปลั๊กไฟ และสถานะความพร้อมใช้งานอย่างละเอียด
                </p>
              </div>
            )}

            <div className="mt-4 pt-3 border-t border-white/5 text-[11px] text-slate-400 flex items-center justify-between">
              <span>สถานะอัปเดตจากโมเดล:</span>
              <span className="font-mono text-cyan-400 font-semibold">ResNet-18 & YOLOv8</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
