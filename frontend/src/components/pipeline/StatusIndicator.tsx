'use client';

import React from 'react';
import { CheckCircle, Loader2, AlertCircle, Clock, Pause } from 'lucide-react';
import { PipelineState } from '@/types';

interface StatusIndicatorProps {
  pipelineState: PipelineState;
}

export default function StatusIndicator({ pipelineState }: StatusIndicatorProps) {
  const { phase1, phase2, phase3, currentPhase, isRunning, isPaused } = pipelineState;

  const getOverallStatus = () => {
    if (phase3.status === 'completed') return 'completed';
    if (phase1.status === 'error' || phase2.status === 'error' || phase3.status === 'error') return 'error';
    if (isPaused) return 'paused';
    if (isRunning) return 'running';
    return 'idle';
  };

  const status = getOverallStatus();

  const getStatusDisplay = () => {
    switch (status) {
      case 'completed':
        return {
          icon: <CheckCircle className="w-6 h-6 text-green-500" />,
          text: 'Pipeline Completed',
          color: 'bg-green-50 border-green-200 text-green-700',
        };
      case 'running':
        return {
          icon: <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />,
          text: `Running Phase ${currentPhase}`,
          color: 'bg-blue-50 border-blue-200 text-blue-700',
        };
      case 'paused':
        return {
          icon: <Pause className="w-6 h-6 text-yellow-500" />,
          text: 'Pipeline Paused',
          color: 'bg-yellow-50 border-yellow-200 text-yellow-700',
        };
      case 'error':
        return {
          icon: <AlertCircle className="w-6 h-6 text-red-500" />,
          text: 'Pipeline Error',
          color: 'bg-red-50 border-red-200 text-red-700',
        };
      default:
        return {
          icon: <Clock className="w-6 h-6 text-gray-400" />,
          text: 'Ready to Start',
          color: 'bg-gray-50 border-gray-200 text-gray-600',
        };
    }
  };

  const statusDisplay = getStatusDisplay();

  const calculateProgress = () => {
    let progress = 0;
    if (phase1.status === 'completed') progress += 33;
    else if (phase1.status === 'running') progress += phase1.progress * 0.33;
    
    if (phase2.status === 'completed') progress += 33;
    else if (phase2.status === 'running') progress += phase2.progress * 0.33;
    
    if (phase3.status === 'completed') progress += 34;
    else if (phase3.status === 'running') progress += phase3.progress * 0.34;
    
    return Math.round(progress);
  };

  const progress = calculateProgress();

  return (
    <div className={`rounded-lg border p-4 ${statusDisplay.color}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          {statusDisplay.icon}
          <span className="font-semibold">{statusDisplay.text}</span>
        </div>
        <span className="text-sm font-medium">{progress}%</span>
      </div>
      
      <div className="h-2 bg-white/50 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ${
            status === 'error' ? 'bg-red-500' :
            status === 'completed' ? 'bg-green-500' :
            'bg-blue-500'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>
      
      <div className="flex justify-between mt-3 text-xs">
        <PhaseProgress label="Phase 1" status={phase1.status} progress={phase1.progress} />
        <PhaseProgress label="Phase 2" status={phase2.status} progress={phase2.progress} />
        <PhaseProgress label="Phase 3" status={phase3.status} progress={phase3.progress} />
      </div>
    </div>
  );
}

interface PhaseProgressProps {
  label: string;
  status: string;
  progress: number;
}

function PhaseProgress({ label, status, progress }: PhaseProgressProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-3 h-3 text-green-500" />;
      case 'running':
        return <Loader2 className="w-3 h-3 text-blue-500 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-3 h-3 text-red-500" />;
      default:
        return <Clock className="w-3 h-3 text-gray-400" />;
    }
  };

  return (
    <div className="flex items-center gap-1">
      {getStatusIcon()}
      <span>{label}</span>
      {status === 'running' && <span>({Math.round(progress)}%)</span>}
    </div>
  );
}
