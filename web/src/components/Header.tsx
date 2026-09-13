'use client';

import React from 'react';
import { Activity, RefreshCw, Layers, Eye, TrendingUp, Sparkles } from 'lucide-react';

interface HeaderProps {
  activeTab: 'overview' | 'floorplan' | 'camera' | 'forecast';
  setActiveTab: (tab: 'overview' | 'floorplan' | 'camera' | 'forecast') => void;
  autoRefreshInterval: number;
  setAutoRefreshInterval: (interval: number) => void;
  countdown: number;
  onManualRefresh: () => void;
  isRefreshing: boolean;
  lastUpdated: string;
}

export default function Header({
  activeTab,
  setActiveTab,
  autoRefreshInterval,
  setAutoRefreshInterval,
  countdown,
  onManualRefresh,
  isRefreshing,
  lastUpdated,
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 glass-panel border-x-0 border-t-0 rounded-none px-4 lg:px-8 py-3.5 mb-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Brand & Live status */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-emerald-400 p-0.5 shadow-lg shadow-cyan-500/20 flex items-center justify-center">
            <div className="w-full h-full bg-[#0b0f19] rounded-[10px] flex items-center justify-center">
              <Activity className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                CO-AI WANGMAI
              </h1>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-radar" />
                LIVE
              </span>
            </div>
            <p className="text-xs text-slate-400 flex items-center gap-1.5">
              <span>Co-working Occupancy & AI Analytics</span>
              <span>•</span>
              <span>อัปเดต: {lastUpdated}</span>
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center bg-[#101726] p-1 rounded-xl border border-white/5 overflow-x-auto text-xs sm:text-sm">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'overview'
                ? 'bg-gradient-to-r from-cyan-600 to-cyan-500 text-white shadow-md shadow-cyan-500/25'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Activity className="w-4 h-4" />
            ภาพรวม
          </button>
          <button
            onClick={() => setActiveTab('floorplan')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'floorplan'
                ? 'bg-gradient-to-r from-cyan-600 to-cyan-500 text-white shadow-md shadow-cyan-500/25'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Layers className="w-4 h-4" />
            แผนผังห้อง
          </button>
          <button
            onClick={() => setActiveTab('camera')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'camera'
                ? 'bg-gradient-to-r from-cyan-600 to-cyan-500 text-white shadow-md shadow-cyan-500/25'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Eye className="w-4 h-4" />
            AI Snapshot
          </button>
          <button
            onClick={() => setActiveTab('forecast')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'forecast'
                ? 'bg-gradient-to-r from-cyan-600 to-cyan-500 text-white shadow-md shadow-cyan-500/25'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            การพยากรณ์
          </button>
        </div>

        {/* Auto Refresh & Controls */}
        <div className="flex items-center gap-2 self-end md:self-auto">
          <div className="flex items-center bg-[#101726] border border-white/5 rounded-xl px-2.5 py-1.5 gap-2">
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              Auto:
            </span>
            <select
              value={autoRefreshInterval}
              onChange={(e) => setAutoRefreshInterval(Number(e.target.value))}
              className="bg-transparent text-xs text-white border-0 focus:ring-0 cursor-pointer font-medium outline-none"
            >
              <option value={10} className="bg-slate-900 text-white">10 วินาที</option>
              <option value={30} className="bg-slate-900 text-white">30 วินาที</option>
              <option value={60} className="bg-slate-900 text-white">60 วินาที</option>
              <option value={0} className="bg-slate-900 text-white">ปิด (Off)</option>
            </select>
            {autoRefreshInterval > 0 && (
              <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300">
                {countdown}s
              </span>
            )}
          </div>

          <button
            onClick={onManualRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white/5 hover:bg-white/10 text-white border border-white/10 transition active:scale-95 disabled:opacity-50"
            title="รีเฟรชข้อมูลเดี๋ยวนี้"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
            <span>รีเฟรช</span>
          </button>
        </div>
      </div>
    </header>
  );
}
