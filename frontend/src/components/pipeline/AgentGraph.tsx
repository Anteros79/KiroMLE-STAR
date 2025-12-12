'use client';

import React from 'react';
import { AgentNode } from '@/types';

interface AgentGraphProps {
  agents: AgentNode[];
  currentAgent?: string;
}

// Agent connections for visualization
const AGENT_CONNECTIONS: { [key: string]: string[] } = {
  // Phase 1
  'retriever': ['evaluator'],
  'evaluator': ['merger'],
  'merger': ['leakage_checker'],
  'leakage_checker': ['usage_checker'],
  'usage_checker': [],
  
  // Phase 2
  'ablation': ['summarizer'],
  'summarizer': ['extractor'],
  'extractor': ['coder'],
  'coder': ['planner'],
  'planner': ['coder', 'ablation'], // Inner loop back to coder, outer loop to ablation
  
  // Phase 3
  'ensemble_planner': ['ensembler'],
  'ensembler': ['ensemble_planner', 'submission'], // Loop back or to submission
  'submission': [],
};

// Agent positions for layout
const AGENT_POSITIONS: { [key: string]: { x: number; y: number } } = {
  // Phase 1 - horizontal layout
  'retriever': { x: 50, y: 80 },
  'evaluator': { x: 150, y: 80 },
  'merger': { x: 250, y: 80 },
  'leakage_checker': { x: 350, y: 80 },
  'usage_checker': { x: 450, y: 80 },
  
  // Phase 2 - grid layout
  'ablation': { x: 50, y: 200 },
  'summarizer': { x: 150, y: 200 },
  'extractor': { x: 250, y: 200 },
  'coder': { x: 350, y: 200 },
  'planner': { x: 350, y: 280 },
  
  // Phase 3 - horizontal layout
  'ensemble_planner': { x: 50, y: 380 },
  'ensembler': { x: 150, y: 380 },
  'submission': { x: 250, y: 380 },
};

export default function AgentGraph({ agents, currentAgent }: AgentGraphProps) {
  const getAgentStatus = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    return agent?.status || 'idle';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return '#3B82F6'; // blue
      case 'completed':
        return '#22C55E'; // green
      case 'error':
        return '#EF4444'; // red
      default:
        return '#9CA3AF'; // gray
    }
  };

  const renderConnections = () => {
    const lines: JSX.Element[] = [];
    
    Object.entries(AGENT_CONNECTIONS).forEach(([from, targets]) => {
      const fromPos = AGENT_POSITIONS[from];
      if (!fromPos) return;
      
      targets.forEach((to, index) => {
        const toPos = AGENT_POSITIONS[to];
        if (!toPos) return;
        
        const fromStatus = getAgentStatus(from);
        const isActive = fromStatus === 'completed' || fromStatus === 'running';
        
        lines.push(
          <line
            key={`${from}-${to}-${index}`}
            x1={fromPos.x + 40}
            y1={fromPos.y + 20}
            x2={toPos.x}
            y2={toPos.y + 20}
            stroke={isActive ? '#3B82F6' : '#E5E7EB'}
            strokeWidth={2}
            strokeDasharray={fromStatus === 'running' ? '5,5' : 'none'}
            markerEnd="url(#arrowhead)"
          />
        );
      });
    });
    
    return lines;
  };

  const renderAgentNodes = () => {
    return Object.entries(AGENT_POSITIONS).map(([agentId, pos]) => {
      const status = getAgentStatus(agentId);
      const isCurrentAgent = currentAgent === agentId;
      const color = getStatusColor(status);
      
      return (
        <g key={agentId} transform={`translate(${pos.x}, ${pos.y})`}>
          <rect
            width={80}
            height={40}
            rx={8}
            fill={isCurrentAgent ? color : 'white'}
            stroke={color}
            strokeWidth={isCurrentAgent ? 3 : 2}
            className={status === 'running' ? 'animate-pulse' : ''}
          />
          <text
            x={40}
            y={25}
            textAnchor="middle"
            fontSize={10}
            fill={isCurrentAgent ? 'white' : '#374151'}
            fontWeight={isCurrentAgent ? 'bold' : 'normal'}
          >
            {agentId.replace('_', ' ')}
          </text>
        </g>
      );
    });
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Graph</h3>
      <svg width="100%" height="450" viewBox="0 0 550 450">
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#9CA3AF" />
          </marker>
        </defs>
        
        {/* Phase labels */}
        <text x="250" y="30" textAnchor="middle" fontSize={14} fontWeight="bold" fill="#374151">
          Phase 1: Initial Solution
        </text>
        <text x="200" y="170" textAnchor="middle" fontSize={14} fontWeight="bold" fill="#374151">
          Phase 2: Iterative Refinement
        </text>
        <text x="150" y="350" textAnchor="middle" fontSize={14} fontWeight="bold" fill="#374151">
          Phase 3: Ensemble
        </text>
        
        {/* Connections */}
        {renderConnections()}
        
        {/* Agent nodes */}
        {renderAgentNodes()}
      </svg>
    </div>
  );
}
