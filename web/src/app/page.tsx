'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Header from '@/components/Header';
import MetricCards from '@/components/MetricCards';
import FloorPlan from '@/components/FloorPlan';
import SnapshotViewer from '@/components/SnapshotViewer';
import HourlyAnalytics from '@/components/HourlyAnalytics';
import ForecastViewer from '@/components/ForecastViewer';
import { LiveStats, HourlyData, TopDay } from '@/lib/data-service';
import { ShieldCheck, Cpu, Terminal } from 'lucide-react';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'overview' | 'floorplan' | 'camera' | 'forecast'>('overview');
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(30);
  const [countdown, setCountdown] = useState<number>(30);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const [stats, setStats] = useState<LiveStats>({
    timestamp: new Date().toISOString(),
    people_count: 0,
    table_used: 0,
    table_total: 10,
    beanbag_used: 0,
    beanbag_total: 5,
    occupancy_rate: 0,
    status: 'low',
    last_updated_human: 'กำลังเชื่อมต่อ...',
  });

  const [hourlyByDay, setHourlyByDay] = useState<Record<string, HourlyData[]>>({});
  const [topDays, setTopDays] = useState<TopDay[]>([]);

  const fetchStats = useCallback(async () => {
    try {
      setIsRefreshing(true);
      const res = await fetch('/api/stats');
      const json = await res.json();
      if (json.success && json.data) {
        setStats(json.data.latest);
        setHourlyByDay(json.data.hourlyByDay || {});
        setTopDays(json.data.topDays || []);
      }
    } catch (error) {
      console.error('Failed to fetch occupancy stats:', error);
    } finally {
      setIsRefreshing(false);
      setCountdown(autoRefreshInterval);
    }
  }, [autoRefreshInterval]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  useEffect(() => {
    if (autoRefreshInterval <= 0) return;

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          fetchStats();
          return autoRefreshInterval;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [autoRefreshInterval, fetchStats]);

  return (
    <div className="min-h-screen bg-[#070b12] text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-white">
      <div className="fixed top-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none -z-10" />
      <div className="fixed top-1/3 right-10 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none -z-10" />
      <div className="fixed bottom-10 left-1/3 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none -z-10" />

      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        autoRefreshInterval={autoRefreshInterval}
        setAutoRefreshInterval={(interval) => {
          setAutoRefreshInterval(interval);
          setCountdown(interval);
        }}
        countdown={countdown}
        onManualRefresh={fetchStats}
        isRefreshing={isRefreshing}
        lastUpdated={stats.last_updated_human}
      />

      <main className="max-w-7xl mx-auto w-full px-4 lg:px-8 pb-16 flex-1">
        <MetricCards stats={stats} />

        {activeTab === 'overview' && (
          <div className="space-y-6">
            <FloorPlan stats={stats} />
            <HourlyAnalytics hourlyByDay={hourlyByDay} topDays={topDays} />
          </div>
        )}

        {activeTab === 'floorplan' && (
          <div className="space-y-6">
            <FloorPlan stats={stats} />
          </div>
        )}

        {activeTab === 'camera' && (
          <div className="space-y-6">
            <SnapshotViewer />
          </div>
        )}

        {activeTab === 'forecast' && (
          <div className="space-y-6">
            <ForecastViewer />
          </div>
        )}

        <div className="mt-10 p-5 rounded-2xl bg-[#0b101c]/80 border border-white/5 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-cyan-400">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <span className="text-white font-medium block">AI Computer Vision & Forecasting Core</span>
              <span>YOLOv8x • ResNet-18 Classifier • SARIMAX • Next.js 15 App Router</span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
              Edge AI Pipeline Connected
            </span>
            <span className="text-slate-600">|</span>
            <span className="font-mono text-cyan-300 flex items-center gap-1">
              <Terminal className="w-3.5 h-3.5" />
              CO-AI Wangmai v2.0
            </span>
          </div>
        </div>
      </main>
    </div>
  );
}
