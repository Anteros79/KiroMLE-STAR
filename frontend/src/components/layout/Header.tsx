'use client';

import React from 'react';
import { Sparkles, Github, Settings, ExternalLink } from 'lucide-react';

interface HeaderProps {
  onSettingsClick?: () => void;
}

export default function Header({ onSettingsClick }: HeaderProps) {
  return (
    <header className="bg-white/80 backdrop-blur-md border-b border-slate-200/60 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-4">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl blur-lg opacity-40" />
          <div className="relative bg-gradient-to-br from-indigo-500 to-purple-600 p-2.5 rounded-xl shadow-lg">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
              MLE-STAR
            </h1>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-full uppercase tracking-wide">
              Beta
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Automated ML Engineering Pipeline
          </p>
        </div>
      </div>
      
      <div className="flex items-center gap-1">
        <a
          href="https://arxiv.org/abs/2503.04613"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all"
        >
          Paper
          <ExternalLink className="w-3 h-3" />
        </a>
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-all"
        >
          <Github className="w-4.5 h-4.5" />
        </a>
        <button
          onClick={onSettingsClick}
          className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-all"
        >
          <Settings className="w-4.5 h-4.5" />
        </button>
      </div>
    </header>
  );
}
