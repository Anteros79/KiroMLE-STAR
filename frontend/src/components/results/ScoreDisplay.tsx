'use client';

import React from 'react';
import { TrendingUp, TrendingDown, Minus, Target, Award } from 'lucide-react';

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

  const getTrendIcon = () => {
    if (improvement > 0.001) return <TrendingUp className="w-5 h-5 text-green-500" />;
    if (improvement < -0.001) return <TrendingDown className="w-5 h-5 text-red-500" />;
    return <Minus className="w-5 h-5 text-gray-400" />;
  };

  const getTrendColor = () => {
    if (improvement > 0.001) return 'text-green-600';
    if (improvement < -0.001) return 'text-red-600';
    return 'text-gray-500';
  };

  const isBestScore = bestScore !== undefined && Math.abs(currentScore - bestScore) < 0.0001;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-primary-600" />
          <h3 className="font-semibold text-gray-900">Validation Score</h3>
        </div>
        {isBestScore && (
          <div className="flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">
            <Award className="w-3 h-3" />
            Best
          </div>
        )}
      </div>

      <div className="flex items-end gap-4">
        <div>
          <p className="text-4xl font-bold text-gray-900">
            {currentScore.toFixed(4)}
          </p>
          <p className="text-sm text-gray-500 mt-1">{metric.toUpperCase()}</p>
        </div>

        {showTrend && previousScore !== undefined && (
          <div className={`flex items-center gap-1 ${getTrendColor()}`}>
            {getTrendIcon()}
            <span className="text-sm font-medium">
              {improvement >= 0 ? '+' : ''}{improvement.toFixed(4)}
              {' '}({improvementPercent >= 0 ? '+' : ''}{improvementPercent.toFixed(2)}%)
            </span>
          </div>
        )}
      </div>

      {bestScore !== undefined && !isBestScore && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Best Score</span>
            <span className="font-medium text-gray-900">{bestScore.toFixed(4)}</span>
          </div>
          <div className="flex items-center justify-between text-sm mt-1">
            <span className="text-gray-500">Gap to Best</span>
            <span className={`font-medium ${bestScore > currentScore ? 'text-red-600' : 'text-green-600'}`}>
              {(currentScore - bestScore).toFixed(4)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
