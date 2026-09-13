'use client';

import React, { useState, useEffect } from 'react';
import { Camera, Calendar, ChevronLeft, ChevronRight, Play, Pause, RefreshCw, ZoomIn, Info, CheckCircle2 } from 'lucide-react';
import { SnapshotMeta } from '@/lib/data-service';

export default function SnapshotViewer() {
  const [snapshots, setSnapshots] = useState<SnapshotMeta[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isZoomed, setIsZoomed] = useState<boolean>(false);

  const fetchSnapshots = async () => {
    try {
      setIsLoading(true);
      const res = await fetch('/api/snapshots');
      const data = await res.json();
      if (data.success && data.snapshots) {
        setSnapshots(data.snapshots);
        if (data.snapshots.length > 0) {
          setCurrentIndex(0);
        }
      }
    } catch (err) {
      console.error('Error loading snapshots:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSnapshots();
  }, []);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isPlaying && snapshots.length > 1) {
      timer = setInterval(() => {
        setCurrentIndex((prev) => (prev + 1) % snapshots.length);
      }, 2500);
    }
    return () => clearInterval(timer);
  }, [isPlaying, snapshots.length]);

  const currentSnapshot = snapshots[currentIndex];

  const handlePrev = () => {
    if (snapshots.length === 0) return;
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : snapshots.length - 1));
  };

  const handleNext = () => {
    if (snapshots.length === 0) return;
    setCurrentIndex((prev) => (prev < snapshots.length - 1 ? prev + 1 : 0));
  };

  return (
    <div className="glass-panel p-6 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 pb-4 border-b border-white/5">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Camera className="w-5 h-5 text-cyan-400" />
            AI Detection Snapshot Inspector (Live & History)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            ตรวจเช็คภาพ Snapshot จากกล้อง พร้อม Bounding Box ที่โมเดล YOLOv8 + ResNet-18 วาดและวิเคราะห์
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
              isPlaying
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                : 'bg-white/5 text-slate-300 border-white/10 hover:bg-white/10'
            }`}
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{isPlaying ? 'พัก Timeline' : 'เล่นภาพสไลด์'}</span>
          </button>

          <button
            onClick={fetchSnapshots}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white/5 hover:bg-white/10 text-white border border-white/10 transition active:scale-95"
          >
            <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
            <span>อัปเดตภาพ</span>
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="h-96 flex flex-col items-center justify-center text-slate-400 gap-3">
          <RefreshCw className="w-8 h-8 animate-spin text-cyan-400" />
          <span className="text-sm">กำลังโหลดภาพตรวจจับ AI จากคลังข้อมูล...</span>
        </div>
      ) : currentSnapshot ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          <div className="lg:col-span-9 flex flex-col items-center">
            <div className="relative w-full rounded-2xl overflow-hidden border border-white/10 bg-black/60 shadow-2xl group">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={currentSnapshot.url}
                alt={currentSnapshot.filename}
                className={`w-full max-h-[540px] object-contain transition-transform duration-300 ${
                  isZoomed ? 'scale-125 cursor-zoom-out' : 'cursor-zoom-in'
                }`}
                onClick={() => setIsZoomed(!isZoomed)}
              />

              <div className="absolute top-3 left-3 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/10 text-xs text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <Calendar className="w-3.5 h-3.5 text-cyan-400" />
                <span className="font-mono">{currentSnapshot.formattedTime}</span>
              </div>

              <div className="absolute top-3 right-3 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/10 text-xs text-slate-300 font-mono">
                {currentSnapshot.filename}
              </div>

              <button
                onClick={handlePrev}
                className="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/60 hover:bg-black/80 text-white flex items-center justify-center border border-white/10 transition opacity-80 hover:opacity-100 active:scale-95"
                title="ภาพก่อนหน้า"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={handleNext}
                className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/60 hover:bg-black/80 text-white flex items-center justify-center border border-white/10 transition opacity-80 hover:opacity-100 active:scale-95"
                title="ภาพถัดไป"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>

            <div className="w-full mt-4 bg-[#101726] border border-white/10 rounded-xl p-3 flex items-center gap-4">
              <span className="text-xs text-slate-400 font-mono whitespace-nowrap">
                ภาพ {currentIndex + 1} จาก {snapshots.length}
              </span>
              <input
                type="range"
                min="0"
                max={snapshots.length - 1}
                value={currentIndex}
                onChange={(e) => setCurrentIndex(Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
              />
              <button
                onClick={() => setCurrentIndex(0)}
                className="text-xs px-2 py-1 rounded bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 whitespace-nowrap font-medium transition"
              >
                ภาพล่าสุด
              </button>
            </div>
          </div>

          <div className="lg:col-span-3 space-y-4">
            <div className="bg-[#101726] border border-white/10 rounded-xl p-4">
              <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                <Info className="w-4 h-4 text-cyan-400" />
                ข้อมูล Bounding Box
              </h3>

              <div className="space-y-2.5 text-xs">
                <div className="flex items-center justify-between p-2 rounded-lg bg-black/30 border border-white/5">
                  <span className="flex items-center gap-2 text-slate-300">
                    <span className="w-2.5 h-2.5 rounded bg-green-500" />
                    บุคคล (People)
                  </span>
                  <span className="font-mono font-bold text-emerald-400">Green Box</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-lg bg-black/30 border border-white/5">
                  <span className="flex items-center gap-2 text-slate-300">
                    <span className="w-2.5 h-2.5 rounded bg-orange-500" />
                    โต๊ะมีคนใช้ (USED)
                  </span>
                  <span className="font-mono font-bold text-orange-400">Orange Box</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-lg bg-black/30 border border-white/5">
                  <span className="flex items-center gap-2 text-slate-300">
                    <span className="w-2.5 h-2.5 rounded bg-slate-400" />
                    โต๊ะว่าง (FREE)
                  </span>
                  <span className="font-mono font-bold text-slate-400">Grey Box</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-lg bg-black/30 border border-white/5">
                  <span className="flex items-center gap-2 text-slate-300">
                    <span className="w-2.5 h-2.5 rounded bg-red-500" />
                    บีนแบ็กมีคนใช้
                  </span>
                  <span className="font-mono font-bold text-red-400">Red Box</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-lg bg-black/30 border border-white/5">
                  <span className="flex items-center gap-2 text-slate-300">
                    <span className="w-2.5 h-2.5 rounded bg-indigo-400" />
                    บีนแบ็กว่าง
                  </span>
                  <span className="font-mono font-bold text-indigo-400">Blue Box</span>
                </div>
              </div>
            </div>

            <div className="bg-[#101726]/60 border border-white/5 rounded-xl p-4 text-xs text-slate-400">
              <span className="font-semibold text-slate-200 block mb-1">AI Pipeline:</span>
              <p className="leading-relaxed text-[11px]">
                ภาพนี้ถูกประมวลผลผ่าน YOLOv8x Object Detection เพื่อหาพิกัดคนและเฟอร์นิเจอร์ จากนั้นส่งภาพ Crop ของโต๊ะไปยัง ResNet-18 Classifier เพื่อยืนยันสถานะการใช้งาน
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="h-64 flex flex-col items-center justify-center text-slate-400">
          <Camera className="w-8 h-8 mb-2 opacity-50" />
          <span className="text-sm">ยังไม่มีภาพ Snapshot ในโฟลเดอร์ outputs/</span>
        </div>
      )}
    </div>
  );
}
