'use client';

import React from 'react';
import {
  FileText,
  Search,
  RefreshCw,
  Layers,
  Download,
  Activity,
  Settings,
} from 'lucide-react';

type NavItem = {
  id: string;
  label: string;
  icon: React.ReactNode;
  phase?: number;
};

const navItems: NavItem[] = [
  { id: 'task', label: 'Task Input', icon: <FileText className="w-5 h-5" /> },
  { id: 'phase1', label: 'Phase 1: Retrieval', icon: <Search className="w-5 h-5" />, phase: 1 },
  { id: 'phase2', label: 'Phase 2: Refinement', icon: <RefreshCw className="w-5 h-5" />, phase: 2 },
  { id: 'phase3', label: 'Phase 3: Ensemble', icon: <Layers className="w-5 h-5" />, phase: 3 },
  { id: 'results', label: 'Results', icon: <Activity className="w-5 h-5" /> },
  { id: 'submission', label: 'Submission', icon: <Download className="w-5 h-5" /> },
];

interface SidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
  phaseStatuses?: { [key: number]: 'pending' | 'running' | 'completed' | 'error' };
}

export default function Sidebar({
  activeSection,
  onSectionChange,
  phaseStatuses = {},
}: SidebarProps) {
  const getStatusColor = (phase?: number) => {
    if (!phase) return '';
    const status = phaseStatuses[phase];
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-600';
      case 'completed':
        return 'bg-green-100 text-green-600';
      case 'error':
        return 'bg-red-100 text-red-600';
      default:
        return 'bg-gray-100 text-gray-400';
    }
  };

  const getStatusDot = (phase?: number) => {
    if (!phase) return null;
    const status = phaseStatuses[phase];
    let dotColor = 'bg-gray-300';
    if (status === 'running') dotColor = 'bg-blue-500 animate-pulse';
    if (status === 'completed') dotColor = 'bg-green-500';
    if (status === 'error') dotColor = 'bg-red-500';
    
    return <span className={`w-2 h-2 rounded-full ${dotColor}`} />;
  };

  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 h-full">
      <nav className="p-4 space-y-2">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onSectionChange(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
              activeSection === item.id
                ? 'bg-primary-100 text-primary-700 font-medium'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <span className={item.phase ? getStatusColor(item.phase) : ''}>
              {item.icon}
            </span>
            <span className="flex-1">{item.label}</span>
            {getStatusDot(item.phase)}
          </button>
        ))}
      </nav>
      
      <div className="absolute bottom-4 left-4 right-4">
        <button
          onClick={() => onSectionChange('settings')}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
            activeSection === 'settings'
              ? 'bg-primary-100 text-primary-700 font-medium'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <Settings className="w-5 h-5" />
          <span>Settings</span>
        </button>
      </div>
    </aside>
  );
}
