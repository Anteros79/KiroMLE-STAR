'use client';

import React from 'react';
import { Search, RefreshCw, Layers, CheckCircle, Loader2, Circle, AlertCircle, Sparkles } from 'lucide-react';
import { PhaseStatus, AgentNode } from '@/types';

interface PhaseCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  status: PhaseStatus;
  agents: AgentNode[];
  isActive: boolean;
  phaseNumber: number;
}

function PhaseCard({ title, description, icon, status, agents, isActive, phaseNumber }: PhaseCardProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'completed':
        return {
          border: 'border-emerald-200/60',
          bg: 'bg-gradient-to-br from-emerald-50 to-teal-50/50',
          iconBg: 'bg-gradient-to-br from-emerald-500 to-teal-600',
          badge: 'bg-emerald-100 text-emerald-700',
          glow: 'shadow-emerald-500/10',
        };
      case 'running':
        return {
          border: 'border-indigo-300/60',
          bg: 'bg-gradient-to-br from-indigo-50 to-purple-50/50',
          iconBg: 'bg-gradient-to-br from-indigo-500 to-purple-600',
          badge: 'bg-indigo-100 text-indigo-700',
          glow: 'shadow-indigo-500/20',
        };
      case 'error':
        return {
          border: 'border-rose-200/60',
          bg: 'bg-gradient-to-br from-rose-50 to-red-50/50',
          iconBg: 'bg-gradient-to-br from-rose-500 to-red-600',
          badge: 'bg-rose-100 text-rose-700',
          glow: 'shadow-rose-500/10',
        };
      default:
        return {
          border: 'border-slate-200/60',
          bg: 'bg-gradient-to-br from-slate-50 to-slate-100/50',
          iconBg: 'bg-gradient-to-br from-slate-400 to-slate-500',
          badge: 'bg-slate-100 text-slate-600',
          glow: '',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div 
      className={`relative rounded-2xl border ${config.border} ${config.bg} p-5 transition-all duration-300 ${
        isActive ? `ring-2 ring-indigo-500/50 ring-offset-2 shadow-xl ${config.glow}` : 'shadow-sm hover:shadow-md'
      }`}
    >
      {/* Phase Number Badge */}
      <div className="absolute -top-3 -left-3">
        <div className={`w-8 h-8 rounded-xl ${config.iconBg} shadow-lg flex items-center justify-center`}>
          <span className="text-sm font-bold text-white">{phaseNumber}</span>
        </div>
      </div>

      {/* Status Indicator */}
      <div className="absolute top-4 right-4">
        {status === 'completed' && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700">
            <CheckCircle className="w-3.5 h-3.5" />
            <span className="text-xs font-medium">Done</span>
          </div>
        )}
        {status === 'running' && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-100 text-indigo-700">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span className="text-xs font-medium">Running</span>
          </div>
        )}
        {status === 'error' && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-100 text-rose-700">
            <AlertCircle className="w-3.5 h-3.5" />
            <span className="text-xs font-medium">Error</span>
          </div>
        )}
        {status === 'pending' && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 text-slate-500">
            <Circle className="w-3.5 h-3.5" />
            <span className="text-xs font-medium">Pending</span>
          </div>
        )}
      </div>

      {/* Header */}
      <div className="flex items-start gap-3 mb-4 mt-2">
        <div className={`p-2.5 rounded-xl ${config.iconBg} shadow-lg`}>
          {React.cloneElement(icon as React.ReactElement, { className: 'w-5 h-5 text-white' })}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-slate-900 text-sm">{title}</h3>
          <p className="text-xs text-slate-500 mt-0.5">{description}</p>
        </div>
      </div>

      {/* Agents List */}
      <div className="space-y-1.5">
        {agents.length > 0 ? (
          agents.map((agent) => (
            <AgentNodeItem key={agent.id} agent={agent} />
          ))
        ) : (
          <div className="text-xs text-slate-400 italic py-2">No agents in this phase</div>
        )}
      </div>
    </div>
  );
}

function AgentNodeItem({ agent }: { agent: AgentNode }) {
  const getStatusStyle = () => {
    switch (agent.status) {
      case 'running':
        return {
          bg: 'bg-indigo-50',
          border: 'border-indigo-200/60',
          text: 'text-indigo-700',
          dot: 'bg-indigo-500',
        };
      case 'completed':
        return {
          bg: 'bg-emerald-50',
          border: 'border-emerald-200/60',
          text: 'text-emerald-700',
          dot: 'bg-emerald-500',
        };
      case 'error':
        return {
          bg: 'bg-rose-50',
          border: 'border-rose-200/60',
          text: 'text-rose-700',
          dot: 'bg-rose-500',
        };
      default:
        return {
          bg: 'bg-slate-50/50',
          border: 'border-slate-200/40',
          text: 'text-slate-500',
          dot: 'bg-slate-300',
        };
    }
  };

  const style = getStatusStyle();

  return (
    <div className={`flex items-center gap-2.5 px-3 py-2 rounded-lg border ${style.bg} ${style.border} transition-all`}>
      <div className="relative">
        <div className={`w-2 h-2 rounded-full ${style.dot}`} />
        {agent.status === 'running' && (
          <div className={`absolute inset-0 w-2 h-2 rounded-full ${style.dot} animate-ping`} />
        )}
      </div>
      <span className={`text-xs font-medium ${style.text} truncate`}>{agent.name}</span>
      {agent.status === 'running' && (
        <Loader2 className="w-3 h-3 text-indigo-500 animate-spin ml-auto" />
      )}
      {agent.status === 'completed' && (
        <CheckCircle className="w-3 h-3 text-emerald-500 ml-auto" />
      )}
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

  const getConnectorStyle = (fromStatus: PhaseStatus) => {
    if (fromStatus === 'completed') {
      return 'from-emerald-400 to-emerald-500';
    }
    if (fromStatus === 'running') {
      return 'from-indigo-400 to-indigo-500';
    }
    return 'from-slate-200 to-slate-300';
  };

  return (
    <div className="bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-2xl border border-slate-200/60 p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Pipeline Overview</h2>
          <p className="text-xs text-slate-500">MLE-STAR automated ML engineering workflow</p>
        </div>
      </div>
      
      {/* Pipeline Flow */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
        {/* Phase 1 */}
        <div className="relative">
          <PhaseCard
            title="Initial Solution"
            description="Model retrieval & evaluation"
            icon={<Search />}
            status={phase1Status}
            agents={phase1Agents}
            isActive={currentPhase === 1}
            phaseNumber={1}
          />
          {/* Connector (hidden on mobile) */}
          <div className="hidden lg:block absolute top-1/2 -right-3 transform -translate-y-1/2 z-10">
            <div className={`w-6 h-1 rounded-full bg-gradient-to-r ${getConnectorStyle(phase1Status)}`} />
          </div>
        </div>
        
        {/* Phase 2 */}
        <div className="relative">
          <PhaseCard
            title="Iterative Refinement"
            description="Ablation & improvements"
            icon={<RefreshCw />}
            status={phase2Status}
            agents={phase2Agents}
            isActive={currentPhase === 2}
            phaseNumber={2}
          />
          {/* Connector (hidden on mobile) */}
          <div className="hidden lg:block absolute top-1/2 -right-3 transform -translate-y-1/2 z-10">
            <div className={`w-6 h-1 rounded-full bg-gradient-to-r ${getConnectorStyle(phase2Status)}`} />
          </div>
        </div>
        
        {/* Phase 3 */}
        <PhaseCard
          title="Ensemble"
          description="Combining solutions"
          icon={<Layers />}
          status={phase3Status}
          agents={phase3Agents}
          isActive={currentPhase === 3}
          phaseNumber={3}
        />
      </div>
    </div>
  );
}
