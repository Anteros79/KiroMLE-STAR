'use client';

import React, { useState } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import { PhaseStatus } from '@/types';

interface MainLayoutProps {
  children: React.ReactNode;
  activeSection: string;
  onSectionChange: (section: string) => void;
  phaseStatuses?: { [key: number]: PhaseStatus };
}

export default function MainLayout({
  children,
  activeSection,
  onSectionChange,
  phaseStatuses = {},
}: MainLayoutProps) {
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 via-slate-50 to-slate-100">
      <Header onSettingsClick={() => setShowSettings(!showSettings)} />
      
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeSection={activeSection}
          onSectionChange={onSectionChange}
          phaseStatuses={phaseStatuses}
        />
        
        <main className="flex-1 overflow-auto">
          <div className="max-w-7xl mx-auto p-6 lg:p-8">
            <div className="animate-fade-in">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
