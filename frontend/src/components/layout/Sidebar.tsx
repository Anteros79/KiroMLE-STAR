'use client';

import React from 'react';
import {
  FileText,
  Search,
  RefreshCw,
  Layers,
  Download,
  BarChart3,
  CheckCircle2,
  Circle,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { PhaseStatus } from '@/types';

type NavItem = {
  id: string;
  label: string;
  description?: string;
  icon: React.ReactNode;
  phase?: number;
};

const navItems: NavItem[] = [
  { id: 'task', label: 'Configure', description: 'Task & Settings', icon: <FileText className="w-4 h-4" /> },
  { id: 'phase1', label: 'Retrieval', description: 'Search & Evaluate', icon: <Search className="w-4 h-4" />, phase: 1 },
  { id: 'phase2', label: 'Refinement', description: 'Iterate & Improve', icon: <RefreshCw className="w-4 h-4" />, phase: 2 },
  { id: 'phase3', label: 'Ensemble', description: 'Combine & Optimize', icon: <Layers className="w-4 h-4" />, phase: 3 },
  { id: 'results', label: 'Results', description: 'Analysis & Metrics', icon: <BarChart3 className="w-4 h-4" /> },
  { id: 'submission', label: 'Export', description: 'Download Output', icon: <Download className="w-4 h-4" /> },
];

interface SidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
  phaseStatuses?: { [key: number]: PhaseStatus };
}

export default function Sidebar({
  activeSection,
  onSectionChange,
  phaseStatuses = {},
}: SidebarProps) {
  const getStatusIcon = (phase?: number) => {
    if (!phase) return null;
    const status = phaseStatuses[phase];
    
    switch (status) {
      case 'running':
        return <Loader2 className="w-3.5 h-3.5 text-indigo-500 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />;
      case 'error':
        return <AlertCircle className="w-3.5 h-3.5 text-red-500" />;
      default:
        return <Circle className="w-3.5 h-3.5 text-slate-300" />;
    }
  };

  const getPhaseNumber = (phase?: number) => {
    if (!phase) return null;
    const status = phaseStatuses[phase];
    
    const baseClasses = "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold";
    
    switch (status) {
      case 'running':
        return <span className={`${baseClasses} bg-indigo-100 text-indigo-600 ring-2 ring-indigo-500/20`}>{phase}</span>;
      case 'completed':
        return <span className={`${baseClasses} bg-emerald-100 text-emerald-600`}>{phase}</span>;
      case 'error':
        return <span className={`${baseClasses} bg-red-100 text-red-600`}>{phase}</span>;
      default:
        return <span className={`${baseClasses} bg-slate-100 text-slate-400`}>{phase}</span>;
    }
  };

  return (
    <aside className="w-64 bg-white/50 backdrop-blur-sm border-r border-slate-200/60 h-full flex flex-col">
      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        <div className="px-3 py-2">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Pipeline</p>
        </div>
        
        {navItems.map((item, index) => {
          const isActive = activeSection === item.id;
          const isPhase = item.phase !== undefined;
          
          return (
            <button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all group ${
                isActive
                  ? 'bg-gradient-to-r from-indigo-50 to-purple-50 shadow-sm'
                  : 'hover:bg-slate-50'
              }`}
            >
              {/* Icon or Phase Number */}
              <div className={`flex-shrink-0 ${
                isActive 
                  ? 'text-indigo-600' 
                  : 'text-slate-400 group-hover:text-slate-600'
              }`}>
                {isPhase ? getPhaseNumber(item.phase) : (
                  <div className={`p-1.5 rounded-lg ${
                    isActive ? 'bg-indigo-100' : 'bg-slate-100 group-hover:bg-slate-200'
                  }`}>
                    {item.icon}
                  </div>
                )}
              </div>
              
              {/* Label & Description */}
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium truncate ${
                  isActive ? 'text-indigo-900' : 'text-slate-700'
                }`}>
                  {item.label}
                </p>
                {item.description && (
                  <p className="text-[11px] text-slate-400 truncate">
                    {item.description}
                  </p>
                )}
              </div>
              
              {/* Status Icon */}
              {isPhase && (
                <div className="flex-shrink-0">
                  {getStatusIcon(item.phase)}
                </div>
              )}
              
              {/* Active Indicator */}
              {isActive && (
                <div className="w-1 h-8 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full absolute right-0" />
              )}
            </button>
          );
        })}
      </nav>
      
      {/* Footer */}
      <div className="p-3 border-t border-slate-200/60">
        <div className="px-3 py-2 bg-gradient-to-r from-slate-50 to-slate-100 rounded-xl">
          <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wide mb-1">Model</p>
          <p className="text-xs font-semibold text-slate-700 truncate">Gemma 3 27B</p>
          <p className="text-[10px] text-slate-400">Local • Ollama</p>
        </div>
      </div>
    </aside>
  );
}
