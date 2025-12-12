'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronRight, TrendingUp, TrendingDown, Code } from 'lucide-react';
import { RefinementAttempt } from '@/types';
import CodeViewer from './CodeViewer';

interface RefinementHistoryProps {
  attempts: RefinementAttempt[];
  bestAttemptIndex?: number;
}

export default function RefinementHistory({ attempts, bestAttemptIndex }: RefinementHistoryProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (attempts.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Refinement History</h3>
        <p className="text-gray-500 text-center py-8">No refinement attempts yet</p>
      </div>
    );
  }

  const getScoreChange = (index: number) => {
    if (index === 0) return 0;
    return attempts[index].validation_score - attempts[index - 1].validation_score;
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="font-semibold text-gray-900 mb-4">Refinement History</h3>
      
      <div className="space-y-3">
        {attempts.map((attempt, index) => {
          const scoreChange = getScoreChange(index);
          const isExpanded = expandedIndex === index;
          const isBest = bestAttemptIndex === index;

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
    </div>
  );
}
