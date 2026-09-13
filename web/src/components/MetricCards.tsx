'use client';

import React from 'react';
import { Users, Armchair, Coffee, Gauge, TrendingUp, CheckCircle2, AlertTriangle, Flame } from 'lucide-react';
import { LiveStats } from '@/lib/data-service';

interface MetricCardsProps {
  stats: LiveStats;
}

export default function MetricCards({ stats }: MetricCardsProps) {
  const tablePercentage = stats.table_total > 0 ? Math.round((stats.table_used / stats.table_total) * 100) : 0;
  const beanbagPercentage = stats.beanbag_total > 0 ? Math.round((stats.beanbag_used / stats.beanbag_total) * 100) : 0;

  const statusConfig = {
    low: {
      label: 'บรรยากาศเงียบสงบ (Low)',
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/30',
      icon: CheckCircle2,
    },
    moderate: {
      label: 'คนใช้งานปานกลาง (Medium)',
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/30',
      icon: AlertTriangle,
    },
    crowded: {
      label: 'คนใช้งานหนาแน่น (Crowded)',
      color: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/30',
      icon: Flame,
    },
  }[stats.status];

  const StatusIcon = statusConfig.icon;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* 1. People Count */}
      <div className="glass-panel glass-panel-hover p-5 relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-28 h-28 bg-cyan-500/10 rounded-full blur-2xl -mr-10 -mt-10 group-hover:bg-cyan-500/20 transition-all" />
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">จำนวนผู้ใช้งาน (People)</span>
          <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Users className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-white tracking-tight">{stats.people_count}</span>
          <span className="text-xs text-slate-400 font-medium">คนในห้อง</span>
        </div>
        <div className="mt-3 flex items-center gap-1.5 text-xs text-emerald-400">
          <TrendingUp className="w-3.5 h-3.5" />
          <span>ตรวจจับโดยโมเดล YOLOv8 Real-time</span>
        </div>
      </div>

      {/* 2. Tables Occupied */}
      <div className="glass-panel glass-panel-hover p-5 relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-28 h-28 bg-amber-500/10 rounded-full blur-2xl -mr-10 -mt-10 group-hover:bg-amber-500/20 transition-all" />
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">การใช้โต๊ะ (Tables Used)</span>
          <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <Coffee className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-white tracking-tight">{stats.table_used}</span>
          <span className="text-slate-400 text-sm font-medium">/ {stats.table_total} โต๊ะ</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 font-semibold ml-auto">
            {tablePercentage}%
          </span>
        </div>
        <div className="mt-3 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div
            className="bg-gradient-to-r from-amber-500 to-orange-400 h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, tablePercentage)}%` }}
          />
        </div>
      </div>

      {/* 3. Beanbags Occupied */}
      <div className="glass-panel glass-panel-hover p-5 relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-28 h-28 bg-emerald-500/10 rounded-full blur-2xl -mr-10 -mt-10 group-hover:bg-emerald-500/20 transition-all" />
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">บีนแบ็ก (Beanbags Used)</span>
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Armchair className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-white tracking-tight">{stats.beanbag_used}</span>
          <span className="text-slate-400 text-sm font-medium">/ {stats.beanbag_total} ตัว</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 font-semibold ml-auto">
            {beanbagPercentage}%
          </span>
        </div>
        <div className="mt-3 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div
            className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, beanbagPercentage)}%` }}
          />
        </div>
      </div>

      {/* 4. Total Capacity & Status */}
      <div className="glass-panel glass-panel-hover p-5 relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-28 h-28 bg-purple-500/10 rounded-full blur-2xl -mr-10 -mt-10 group-hover:bg-purple-500/20 transition-all" />
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">สถานะความหนาแน่น</span>
          <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
            <Gauge className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-white tracking-tight">{stats.occupancy_rate}%</span>
          <span className="text-xs text-slate-400 font-medium">อัตราการครองพื้นที่</span>
        </div>
        <div className="mt-3">
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border ${statusConfig.bg} ${statusConfig.color}`}>
            <StatusIcon className="w-3.5 h-3.5" />
            {statusConfig.label}
          </span>
        </div>
      </div>
    </div>
  );
}
