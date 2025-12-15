'use client';

import React from 'react';
import { TrendingUp, TrendingDown, Minus, Target, Award, Sparkles } from 'lucide-react';

interface ScoreDisplayProps {
  currentScore: number;
  previousScore?: number;
  bestScore?: number;
  metric: string;
  showTrend?: boolean;
}

export default function ScoreDisplay({
  currentScore,
  previousScore,
  bestScore,
  metric,
  showTrend = true,
}: ScoreDisplayProps) {
  const improvement = previousScore !== undefined ? currentScore - previousScore : 0;
  const improvementPercent = previousScore !== undefined && previousScore !== 0
    ? ((currentScore - previousScore) / previousScore) * 100
    : 0;

  const getTrendConfig = () => {
    if (improvement > 0.001) return {
      icon: TrendingUp,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
      border: 'border-emerald-200/60',
    };
    if (improvement < -0.001) return {
      icon: TrendingDown,
      color: 'text-rose-600',
      bg: 'bg-rose-50',
      border: 'border-rose-200/60',
    };
    return {
      icon: Minus,
      color: 'text-slate-500',
      bg: 'bg-slate-50',
      border: 'border-slate-200/60',
    };
  };

  const trend = getTrendConfig();
  const TrendIcon = trend.icon;
  const isBestScore = bestScore !== undefined && Math.abs(currentScore - bestScore) < 0.0001;

  // Calculate score percentage for visual indicator (assuming 0-1 range)
  const scorePercent = Math.min(Math.max(currentScore * 100, 0), 100);

  return (
    <div className="bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-2xl border border-slate-200/60 p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20">
            <Target className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">Validation Score</h3>
            <p className="text-xs text-slate-500">{metric.toUpperCase()} metric</p>
          </div>
        </div>
        {isBestScore && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-amber-100 to-yellow-100 text-amber-700 rounded-full text-xs font-semibold border border-amber-200/60">
            <Award className="w-3.5 h-3.5" />
            Best Score
          </div>
        )}
      </div>

      {/* Main Score */}
      <div className="relative mb-5">
        <div className="flex items-baseline gap-2">
          <span className="text-5xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
            {currentScore.toFixed(4)}
          </span>
          {showTrend && previousScore !== undefined && (
            <div className={`flex items-center gap-1 px-2.5 py-1 rounded-lg ${trend.bg} ${trend.border} border`}>
              <TrendIcon className={`w-4 h-4 ${trend.color}`} />
              <span className={`text-sm font-semibold ${trend.color}`}>
                {improvement >= 0 ? '+' : ''}{improvement.toFixed(4)}
              </span>
            </div>
          )}
        </div>
        
        {/* Score Progress Bar */}
        <div className="mt-4 h-2 bg-slate-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all duration-500"
            style={{ width: `${scorePercent}%` }}
          />
        </div>
        <div className="flex justify-between mt-1.5 text-xs text-slate-400">
          <span>0.0</span>
          <span>1.0</span>
        </div>
      </div>

      {/* Trend Details */}
      {showTrend && previousScore !== undefined && (
        <div className={`flex items-center justify-between p-3 rounded-xl ${trend.bg} ${trend.border} border mb-4`}>
          <div className="flex items-center gap-2">
            <Sparkles className={`w-4 h-4 ${trend.color}`} />
            <span className="text-sm text-slate-600">Change from previous</span>
          </div>
          <span className={`text-sm font-semibold ${trend.color}`}>
            {improvementPercent >= 0 ? '+' : ''}{improvementPercent.toFixed(2)}%
          </span>
        </div>
      )}

      {/* Best Score Comparison */}
      {bestScore !== undefined && !isBestScore && (
        <div className="pt-4 border-t border-slate-200/60 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-500">Best Score</span>
            <span className="text-sm font-semibold text-slate-900">{bestScore.toFixed(4)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-500">Gap to Best</span>
            <span className={`text-sm font-semibold ${bestScore > currentScore ? 'text-rose-600' : 'text-emerald-600'}`}>
              {(currentScore - bestScore).toFixed(4)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
