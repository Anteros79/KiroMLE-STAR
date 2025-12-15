'use client';

import React, { useState, useMemo } from 'react';
import { 
  ChevronDown, 
  ChevronRight, 
  TrendingUp, 
  TrendingDown, 
  Code, 
  Clock,
  Trophy,
  GitBranch
} from 'lucide-react';
import { RefinementAttempt } from '@/types';
import CodeViewer from './CodeViewer';

interface RefinementHistoryProps {
  attempts: RefinementAttempt[];
  bestAttemptIndex?: number;
}

// Simple line chart for score progression
function ScoreProgressChart({ attempts }: { attempts: RefinementAttempt[] }) {
  if (attempts.length < 2) return null;

  const scores = attempts.map(a => a.validation_score);
  const minScore = Math.min(...scores) - 0.01;
  const maxScore = Math.max(...scores) + 0.01;
  const range = maxScore - minScore;

  const width = 300;
  const height = 80;
  const padding = { top: 10, right: 10, bottom: 20, left: 40 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const points = attempts.map((a, i) => ({
    x: padding.left + (i / (attempts.length - 1)) * chartWidth,
    y: padding.top + chartHeight - ((a.validation_score - minScore) / range) * chartHeight,
    score: a.validation_score,
    iteration: a.iteration,
  }));

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

  return (
    <div className="mb-6">
      <h4 className="text-sm font-medium text-gray-700 mb-2">Score Progression</h4>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
          <g key={i}>
            <line
              x1={padding.left}
              y1={padding.top + chartHeight * (1 - ratio)}
              x2={width - padding.right}
              y2={padding.top + chartHeight * (1 - ratio)}
              stroke="#e5e7eb"
              strokeWidth={1}
            />
            <text
              x={padding.left - 5}
              y={padding.top + chartHeight * (1 - ratio) + 3}
              textAnchor="end"
              className="text-[8px] fill-gray-400"
            >
              {(minScore + range * ratio).toFixed(3)}
            </text>
          </g>
        ))}

        {/* Line path */}
        <path
          d={pathD}
          fill="none"
          stroke="#6366f1"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points */}
        {points.map((p, i) => (
          <g key={i}>
            <circle
              cx={p.x}
              cy={p.y}
              r={4}
              fill={i === attempts.length - 1 ? '#22c55e' : '#6366f1'}
              stroke="white"
              strokeWidth={2}
            />
            <text
              x={p.x}
              y={height - 5}
              textAnchor="middle"
              className="text-[8px] fill-gray-500"
            >
              {p.iteration}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

export default function RefinementHistory({ attempts, bestAttemptIndex }: RefinementHistoryProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<'timeline' | 'list'>('timeline');

  const bestIndex = useMemo(() => {
    if (bestAttemptIndex !== undefined) return bestAttemptIndex;
    if (attempts.length === 0) return -1;
    return attempts.reduce((best, curr, i) => 
      curr.validation_score > attempts[best].validation_score ? i : best, 0
    );
  }, [attempts, bestAttemptIndex]);

  const totalImprovement = useMemo(() => {
    if (attempts.length < 2) return 0;
    return attempts[attempts.length - 1].validation_score - attempts[0].validation_score;
  }, [attempts]);

  if (attempts.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <GitBranch className="w-5 h-5 text-primary-600" />
          <h3 className="font-semibold text-gray-900">Refinement History</h3>
        </div>
        <div className="text-center py-8">
          <Clock className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No refinement attempts yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Refinements will appear here as the pipeline iterates
          </p>
        </div>
      </div>
    );
  }

  const getScoreChange = (index: number) => {
    if (index === 0) return 0;
    return attempts[index].validation_score - attempts[index - 1].validation_score;
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-primary-600" />
          <h3 className="font-semibold text-gray-900">Refinement History</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('timeline')}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              viewMode === 'timeline' 
                ? 'bg-primary-100 text-primary-700' 
                : 'text-gray-500 hover:bg-gray-100'
            }`}
          >
            Timeline
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              viewMode === 'list' 
                ? 'bg-primary-100 text-primary-700' 
                : 'text-gray-500 hover:bg-gray-100'
            }`}
          >
            List
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-gray-900">{attempts.length}</p>
          <p className="text-xs text-gray-500">Iterations</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-green-600">
            {attempts[bestIndex]?.validation_score.toFixed(4) || '-'}
          </p>
          <p className="text-xs text-gray-500">Best Score</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className={`text-2xl font-bold ${totalImprovement >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {totalImprovement >= 0 ? '+' : ''}{totalImprovement.toFixed(4)}
          </p>
          <p className="text-xs text-gray-500">Total Change</p>
        </div>
      </div>

      {/* Score Chart */}
      <ScoreProgressChart attempts={attempts} />

      {/* Timeline/List View */}
      {viewMode === 'timeline' ? (
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
          
          <div className="space-y-4">
            {attempts.map((attempt, index) => {
              const scoreChange = getScoreChange(index);
              const isExpanded = expandedIndex === index;
              const isBest = bestIndex === index;

              return (
                <div key={index} className="relative pl-10">
                  {/* Timeline dot */}
                  <div className={`absolute left-2 w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                    isBest 
                      ? 'bg-yellow-400 border-yellow-500' 
                      : scoreChange > 0 
                        ? 'bg-green-400 border-green-500'
                        : scoreChange < 0
                          ? 'bg-red-400 border-red-500'
                          : 'bg-gray-300 border-gray-400'
                  }`}>
                    {isBest && <Trophy className="w-3 h-3 text-yellow-800" />}
                  </div>

                  <div className={`border rounded-lg overflow-hidden ${
                    isBest ? 'border-yellow-300 bg-yellow-50' : 'border-gray-200 bg-white'
                  }`}>
                    <button
                      onClick={() => setExpandedIndex(isExpanded ? null : index)}
                      className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-gray-400" />
                        )}
                        <span className="font-medium text-gray-900 text-sm">
                          Iteration {attempt.iteration}
                        </span>
                        {isBest && (
                          <span className="px-2 py-0.5 bg-yellow-200 text-yellow-800 text-xs rounded-full">
                            Best
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-3">
                        <span className="font-medium text-gray-900 text-sm">
                          {attempt.validation_score.toFixed(4)}
                        </span>
                        {index > 0 && (
                          <span className={`flex items-center gap-0.5 text-xs ${
                            scoreChange > 0 ? 'text-green-600' : scoreChange < 0 ? 'text-red-600' : 'text-gray-500'
                          }`}>
                            {scoreChange > 0 ? <TrendingUp className="w-3 h-3" /> : 
                             scoreChange < 0 ? <TrendingDown className="w-3 h-3" /> : null}
                            {scoreChange >= 0 ? '+' : ''}{scoreChange.toFixed(4)}
                          </span>
                        )}
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="border-t border-gray-200 p-4 space-y-4">
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-2">Refinement Plan</h4>
                          <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                            {attempt.plan}
                          </p>
                        </div>
                        
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                            <Code className="w-4 h-4" />
                            Refined Code Block
                          </h4>
                          <CodeViewer
                            code={attempt.refined_code_block}
                            title="Refined Code"
                            maxHeight="300px"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {attempts.map((attempt, index) => {
            const scoreChange = getScoreChange(index);
            const isExpanded = expandedIndex === index;
            const isBest = bestIndex === index;

            return (
              <div
                key={index}
                className={`border rounded-lg overflow-hidden ${
                  isBest ? 'border-yellow-300 bg-yellow-50' : 'border-gray-200'
                }`}
              >
                <button
                  onClick={() => setExpandedIndex(isExpanded ? null : index)}
                  className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                    <div className="text-left">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">
                          Iteration {attempt.iteration}
                        </span>
                        {isBest && (
                          <span className="px-2 py-0.5 bg-yellow-200 text-yellow-800 text-xs rounded-full">
                            Best
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 truncate max-w-md">
                        {attempt.plan.substring(0, 100)}...
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-medium text-gray-900">
                        {attempt.validation_score.toFixed(4)}
                      </p>
                      {index > 0 && (
                        <div className={`flex items-center gap-1 text-sm ${
                          scoreChange > 0 ? 'text-green-600' : scoreChange < 0 ? 'text-red-600' : 'text-gray-500'
                        }`}>
                          {scoreChange > 0 ? (
                            <TrendingUp className="w-3 h-3" />
                          ) : scoreChange < 0 ? (
                            <TrendingDown className="w-3 h-3" />
                          ) : null}
                          <span>{scoreChange >= 0 ? '+' : ''}{scoreChange.toFixed(4)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </button>

                {isExpanded && (
                  <div className="border-t border-gray-200 p-4 space-y-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Refinement Plan</h4>
                      <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                        {attempt.plan}
                      </p>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                        <Code className="w-4 h-4" />
                        Refined Code Block
                      </h4>
                      <CodeViewer
                        code={attempt.refined_code_block}
                        title="Refined Code"
                        maxHeight="300px"
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
