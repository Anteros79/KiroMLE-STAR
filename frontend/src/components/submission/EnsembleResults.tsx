'use client';

import React, { useState } from 'react';
import { Layers, Trophy, ChevronDown, ChevronRight, TrendingUp } from 'lucide-react';
import { EnsembleResult } from '@/types';
import { CodeViewer } from '../results';

interface EnsembleResultsProps {
  results: EnsembleResult[];
  bestResultIndex?: number;
}

export default function EnsembleResults({ results, bestResultIndex }: EnsembleResultsProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (results.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Layers className="w-5 h-5 text-primary-600" />
          <h3 className="font-semibold text-gray-900">Ensemble Results</h3>
        </div>
        <p className="text-gray-500 text-center py-8">No ensemble results yet</p>
      </div>
    );
  }

  // Sort by score descending
  const sortedResults = [...results].sort((a, b) => b.validation_score - a.validation_score);
  const bestScore = sortedResults[0]?.validation_score || 0;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-primary-600" />
          <h3 className="font-semibold text-gray-900">Ensemble Results</h3>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Trophy className="w-4 h-4 text-yellow-500" />
          <span className="text-gray-600">Best Score:</span>
          <span className="font-bold text-gray-900">{bestScore.toFixed(4)}</span>
        </div>
      </div>

      <div className="space-y-3">
        {sortedResults.map((result, index) => {
          const isExpanded = expandedIndex === index;
          const isBest = index === 0;
          const originalIndex = results.findIndex(r => r === result);

          return (
            <div
              key={originalIndex}
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
                        Strategy {result.iteration}
                      </span>
                      {isBest && (
                        <span className="flex items-center gap-1 px-2 py-0.5 bg-yellow-200 text-yellow-800 text-xs rounded-full">
                          <Trophy className="w-3 h-3" />
                          Best
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 truncate max-w-md">
                      {result.strategy}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="font-medium text-gray-900">
                      {result.validation_score.toFixed(4)}
                    </p>
                    {!isBest && (
                      <div className="flex items-center gap-1 text-sm text-red-600">
                        <TrendingUp className="w-3 h-3 rotate-180" />
                        <span>{(result.validation_score - bestScore).toFixed(4)}</span>
                      </div>
                    )}
                  </div>
                </div>
              </button>

              {isExpanded && (
                <div className="border-t border-gray-200 p-4 space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Ensemble Strategy</h4>
                    <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                      {result.strategy}
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Merged Code</h4>
                    <CodeViewer
                      code={result.merged_code}
                      title="Ensemble Code"
                      maxHeight="300px"
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
