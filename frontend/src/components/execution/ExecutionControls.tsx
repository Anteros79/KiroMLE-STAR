'use client';

import React from 'react';
import { Play, Pause, Square, RotateCcw, Loader2, Rocket } from 'lucide-react';

interface ExecutionControlsProps {
  isRunning: boolean;
  isPaused: boolean;
  canStart: boolean;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onReset: () => void;
}

export default function ExecutionControls({
  isRunning,
  isPaused,
  canStart,
  onStart,
  onPause,
  onResume,
  onStop,
  onReset,
}: ExecutionControlsProps) {
  return (
    <div className="bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-2xl border border-slate-200/60 p-4 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        {/* Main Action Button */}
        <div className="flex items-center gap-3">
          {!isRunning && !isPaused && (
            <button
              onClick={onStart}
              disabled={!canStart}
              className="group relative flex items-center gap-2.5 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl font-semibold shadow-lg shadow-emerald-500/25 hover:shadow-xl hover:shadow-emerald-500/30 hover:scale-[1.02] transition-all disabled:from-slate-300 disabled:to-slate-400 disabled:shadow-none disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              <Rocket className="w-5 h-5 group-hover:rotate-12 transition-transform" />
              Start Pipeline
              {canStart && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full animate-pulse" />
              )}
            </button>
          )}

          {isRunning && !isPaused && (
            <>
              <button
                onClick={onPause}
                className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-amber-400 to-orange-500 text-white rounded-xl font-semibold shadow-lg shadow-amber-500/25 hover:shadow-xl hover:shadow-amber-500/30 hover:scale-[1.02] transition-all"
              >
                <Pause className="w-5 h-5" />
                Pause
              </button>
              <button
                onClick={onStop}
                className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-rose-500 to-red-600 text-white rounded-xl font-semibold shadow-lg shadow-rose-500/25 hover:shadow-xl hover:shadow-rose-500/30 hover:scale-[1.02] transition-all"
              >
                <Square className="w-5 h-5" />
                Stop
              </button>
            </>
          )}

          {isPaused && (
            <>
              <button
                onClick={onResume}
                className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl font-semibold shadow-lg shadow-emerald-500/25 hover:shadow-xl hover:shadow-emerald-500/30 hover:scale-[1.02] transition-all"
              >
                <Play className="w-5 h-5" />
                Resume
              </button>
              <button
                onClick={onStop}
                className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-rose-500 to-red-600 text-white rounded-xl font-semibold shadow-lg shadow-rose-500/25 hover:shadow-xl hover:shadow-rose-500/30 hover:scale-[1.02] transition-all"
              >
                <Square className="w-5 h-5" />
                Stop
              </button>
            </>
          )}

          {!isRunning && !isPaused && (
            <button
              onClick={onReset}
              className="flex items-center gap-2 px-4 py-3 bg-white text-slate-600 rounded-xl font-medium border border-slate-200 hover:bg-slate-50 hover:border-slate-300 transition-all"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>
          )}
        </div>

        {/* Status Indicator */}
        <div className="flex items-center">
          {isRunning && !isPaused && (
            <div className="flex items-center gap-3 px-4 py-2.5 bg-indigo-50 border border-indigo-200/60 rounded-xl">
              <div className="relative">
                <Loader2 className="w-5 h-5 text-indigo-600 animate-spin" />
              </div>
              <div>
                <span className="text-sm font-semibold text-indigo-700">Pipeline Running</span>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse" />
                  <span className="text-xs text-indigo-500">Processing agents...</span>
                </div>
              </div>
            </div>
          )}

          {isPaused && (
            <div className="flex items-center gap-3 px-4 py-2.5 bg-amber-50 border border-amber-200/60 rounded-xl">
              <Pause className="w-5 h-5 text-amber-600" />
              <div>
                <span className="text-sm font-semibold text-amber-700">Pipeline Paused</span>
                <p className="text-xs text-amber-500 mt-0.5">Click Resume to continue</p>
              </div>
            </div>
          )}

          {!isRunning && !isPaused && canStart && (
            <div className="flex items-center gap-3 px-4 py-2.5 bg-emerald-50 border border-emerald-200/60 rounded-xl">
              <div className="w-2 h-2 bg-emerald-500 rounded-full" />
              <div>
                <span className="text-sm font-semibold text-emerald-700">Ready to Start</span>
                <p className="text-xs text-emerald-500 mt-0.5">Task configured</p>
              </div>
            </div>
          )}

          {!isRunning && !isPaused && !canStart && (
            <div className="flex items-center gap-3 px-4 py-2.5 bg-slate-50 border border-slate-200/60 rounded-xl">
              <div className="w-2 h-2 bg-slate-300 rounded-full" />
              <div>
                <span className="text-sm font-semibold text-slate-600">Waiting</span>
                <p className="text-xs text-slate-400 mt-0.5">Configure task to start</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
