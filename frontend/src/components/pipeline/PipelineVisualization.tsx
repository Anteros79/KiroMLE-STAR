'use client';

import React from 'react';
import { Search, RefreshCw, Layers, ArrowRight, CheckCircle, Loader2, Circle, AlertCircle } from 'lucide-react';
import { PhaseStatus, AgentNode } from '@/types';

interface PhaseCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  status: PhaseStatus;
  agents: AgentNode[];
  isActive: boolean;
}

function PhaseCard({ title, description, icon, status, agents, isActive }: PhaseCardProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Circle className="w-5 h-5 text-gray-300" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'border-green-200 bg-green-50';
      case 'running':
        return 'border-blue-200 bg-blue-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-gray-200 bg-white';
    }
  };

  return (
    <div className={`rounded-xl border-2 p-6 transition-all ${getStatusColor()} ${isActive ? 'ring-2 ring-primary-500 ring-offset-2' : ''}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${status === 'running' ? 'bg-blue-100' : status === 'completed' ? 'bg-green-100' : 'bg-gray-100'}`}>
            {icon}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{title}</h3>
            <p className="text-sm text-gray-500">{description}</p>
          </div>
        </div>
        {getStatusIcon()}
      </div>

      <div className="space-y-2">
        {agents.map((agent) => (
          <AgentNodeItem key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  );
}

function AgentNodeItem({ agent }: { agent: AgentNode }) {
  const getStatusStyle = () => {
    switch (agent.status) {
      case 'running':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'completed':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'error':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-gray-50 text-gray-600 border-gray-200';
    }
  };

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${getStatusStyle()}`}>
      {agent.status === 'running' && (
        <Loader2 className="w-4 h-4 animate-spin" />
      )}
      {agent.status === 'completed' && (
        <CheckCircle className="w-4 h-4" />
      )}
      {agent.status === 'error' && (
        <AlertCircle className="w-4 h-4" />
      )}
      {agent.status === 'idle' && (
        <Circle className="w-4 h-4" />
      )}
      <span className="text-sm font-medium">{agent.name}</span>
    </div>
  );
}

interface PipelineVisualizationProps {
  phase1Status: PhaseStatus;
  phase2Status: PhaseStatus;
  phase3Status: PhaseStatus;
  currentPhase: 1 | 2 | 3 | null;
  agents: AgentNode[];
}

export default function PipelineVisualization({
  phase1Status,
  phase2Status,
  phase3Status,
  currentPhase,
  agents,
}: PipelineVisualizationProps) {
  const phase1Agents = agents.filter(a => a.phase === 1);
  const phase2Agents = agents.filter(a => a.phase === 2);
  const phase3Agents = agents.filter(a => a.phase === 3);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Pipeline Overview</h2>
      
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <PhaseCard
            title="Phase 1: Initial Solution"
            description="Model retrieval, evaluation, and merging"
            icon={<Search className="w-5 h-5 text-primary-600" />}
            status={phase1Status}
            agents={phase1Agents}
            isActive={currentPhase === 1}
          />
        </div>
        
        <ArrowRight className={`w-8 h-8 flex-shrink-0 ${phase1Status === 'completed' ? 'text-green-500' : 'text-gray-300'}`} />
        
        <div className="flex-1">
          <PhaseCard
            title="Phase 2: Iterative Refinement"
            description="Ablation studies and targeted improvements"
            icon={<RefreshCw className="w-5 h-5 text-primary-600" />}
            status={phase2Status}
            agents={phase2Agents}
            isActive={currentPhase === 2}
          />
        </div>
        
        <ArrowRight className={`w-8 h-8 flex-shrink-0 ${phase2Status === 'completed' ? 'text-green-500' : 'text-gray-300'}`} />
        
        <div className="flex-1">
          <PhaseCard
            title="Phase 3: Ensemble"
            description="Combining solutions for best performance"
            icon={<Layers className="w-5 h-5 text-primary-600" />}
            status={phase3Status}
            agents={phase3Agents}
            isActive={currentPhase === 3}
          />
        </div>
      </div>
    </div>
  );
}
