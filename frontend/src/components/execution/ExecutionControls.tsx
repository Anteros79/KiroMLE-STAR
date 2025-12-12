'use client';

import React from 'react';
import { Play, Pause, Square, RotateCcw, Loader2 } from 'lucide-react';

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
    <div className="flex items-center gap-3">
      {!isRunning && !isPaused && (
        <button
          onClick={onStart}
          disabled={!canStart}
          className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          <Play className="w-5 h-5" />
          Start Pipeline
        </button>
      )}

      {isRunning && !isPaused && (
        <>
          <button
            onClick={onPause}
            className="flex items-center gap-2 px-4 py-3 bg-yellow-500 text-white rounded-lg font-medium hover:bg-yellow-600 transition-colors"
          >
            <Pause className="w-5 h-5" />
            Pause
          </button>
          <button
            onClick={onStop}
            className="flex items-center gap-2 px-4 py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
          >
            <Square className="w-5 h-5" />
            Stop
          </button>
          <div className="flex items-center gap-2 px-4 py-3 bg-blue-100 text-blue-700 rounded-lg">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span className="font-medium">Running...</span>
          </div>
        </>
      )}

      {isPaused && (
        <>
          <button
            onClick={onResume}
            className="flex items-center gap-2 px-4 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors"
          >
            <Play className="w-5 h-5" />
            Resume
          </button>
          <button
            onClick={onStop}
            className="flex items-center gap-2 px-4 py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
          >
            <Square className="w-5 h-5" />
            Stop
          </button>
          <div className="flex items-center gap-2 px-4 py-3 bg-yellow-100 text-yellow-700 rounded-lg">
            <Pause className="w-5 h-5" />
            <span className="font-medium">Paused</span>
          </div>
        </>
      )}

      {!isRunning && !isPaused && (
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-4 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition-colors"
        >
          <RotateCcw className="w-5 h-5" />
          Reset
        </button>
      )}
    </div>
  );
}
