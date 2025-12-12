'use client';

import React from 'react';
import { CheckCircle, Loader2, Circle, AlertCircle } from 'lucide-react';
import { PhaseState } from '@/types';

interface ProgressIndicatorProps {
  phase1: PhaseState;
  phase2: PhaseState;
  phase3: PhaseState;
}

interface PhaseProgressProps {
  phase: PhaseState;
  phaseNumber: number;
  title: string;
}

function PhaseProgress({ phase, phaseNumber, title }: PhaseProgressProps) {
  const getStatusIcon = () => {
    switch (phase.status) {
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'running':
        return <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-6 h-6 text-red-500" />;
      default:
        return <Circle className="w-6 h-6 text-gray-300" />;
    }
  };

  const getProgressBarColor = () => {
    switch (phase.status) {
      case 'completed':
        return 'bg-green-500';
      case 'running':
        return 'bg-blue-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-200';
    }
  };

  const formatDuration = () => {
    if (!phase.startTime) return null;
    const endTime = phase.endTime || new Date();
    const duration = Math.floor((endTime.getTime() - phase.startTime.getTime()) / 1000);
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex-1">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className="font-medium text-gray-900">Phase {phaseNumber}</span>
        </div>
        <div className="text-sm text-gray-500">
          {phase.status === 'running' && `${Math.round(phase.progress)}%`}
          {phase.status === 'completed' && formatDuration()}
        </div>
      </div>
      
      <p className="text-sm text-gray-600 mb-2">{title}</p>
      
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${getProgressBarColor()}`}
          style={{ width: `${phase.status === 'completed' ? 100 : phase.progress}%` }}
        />
      </div>
      
      {phase.message && (
        <p className="text-xs text-gray-500 mt-1 truncate">{phase.message}</p>
      )}
    </div>
  );
}

export default function ProgressIndicator({ phase1, phase2, phase3 }: ProgressIndicatorProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="font-semibold text-gray-900 mb-6">Pipeline Progress</h3>
      
      <div className="flex items-start gap-4">
        <PhaseProgress
          phase={phase1}
          phaseNumber={1}
          title="Initial Solution Generation"
        />
        
        <div className="flex-shrink-0 pt-3">
          <div className={`w-8 h-0.5 ${phase1.status === 'completed' ? 'bg-green-500' : 'bg-gray-200'}`} />
        </div>
        
        <PhaseProgress
          phase={phase2}
          phaseNumber={2}
          title="Iterative Refinement"
        />
        
        <div className="flex-shrink-0 pt-3">
          <div className={`w-8 h-0.5 ${phase2.status === 'completed' ? 'bg-green-500' : 'bg-gray-200'}`} />
        </div>
        
        <PhaseProgress
          phase={phase3}
          phaseNumber={3}
          title="Ensemble"
        />
      </div>
    </div>
  );
}
