'use client';

import React, { useRef, useEffect, useState } from 'react';
import { Terminal, Download, Trash2, Filter, ChevronDown } from 'lucide-react';
import { LogEntry } from '@/types';

interface LogViewerProps {
  logs: LogEntry[];
  onClear?: () => void;
  maxHeight?: string;
}

type LogLevel = 'all' | 'info' | 'warning' | 'error' | 'success';

export default function LogViewer({ logs, onClear, maxHeight = '400px' }: LogViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState<LogLevel>('all');
  const [showFilterMenu, setShowFilterMenu] = useState(false);

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      setAutoScroll(isAtBottom);
    }
  };

  const filteredLogs = filter === 'all' 
    ? logs 
    : logs.filter(log => log.level === filter);

  const getLevelColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'error':
        return 'text-red-400';
      case 'warning':
        return 'text-yellow-400';
      case 'success':
        return 'text-green-400';
      default:
        return 'text-blue-400';
    }
  };

  const getLevelBadge = (level: LogEntry['level']) => {
    const colors = {
      error: 'bg-red-900/50 text-red-400',
      warning: 'bg-yellow-900/50 text-yellow-400',
      success: 'bg-green-900/50 text-green-400',
      info: 'bg-blue-900/50 text-blue-400',
    };
    return colors[level];
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const handleDownload = () => {
    const content = logs
      .map(log => `[${formatTimestamp(log.timestamp)}] [${log.level.toUpperCase()}] [${log.agent}] ${log.message}`)
      .join('\n');
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mle-star-logs-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-gray-400" />
          <span className="text-sm font-medium text-gray-300">Execution Logs</span>
          <span className="text-xs text-gray-500">({filteredLogs.length} entries)</span>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="relative">
            <button
              onClick={() => setShowFilterMenu(!showFilterMenu)}
              className="flex items-center gap-1 px-2 py-1 text-gray-400 hover:text-white transition-colors text-sm"
            >
              <Filter className="w-4 h-4" />
              <span className="capitalize">{filter}</span>
              <ChevronDown className="w-3 h-3" />
            </button>
            
            {showFilterMenu && (
              <div className="absolute right-0 top-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-10">
                {(['all', 'info', 'warning', 'error', 'success'] as LogLevel[]).map(level => (
                  <button
                    key={level}
                    onClick={() => {
                      setFilter(level);
                      setShowFilterMenu(false);
                    }}
                    className={`block w-full px-4 py-2 text-left text-sm hover:bg-gray-700 capitalize ${
                      filter === level ? 'text-primary-400' : 'text-gray-300'
                    }`}
                  >
                    {level}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <button
            onClick={handleDownload}
            className="p-1.5 text-gray-400 hover:text-white transition-colors"
            title="Download logs"
          >
            <Download className="w-4 h-4" />
          </button>
          
          {onClear && (
            <button
              onClick={onClear}
              className="p-1.5 text-gray-400 hover:text-white transition-colors"
              title="Clear logs"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
      
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="overflow-auto font-mono text-sm"
        style={{ maxHeight }}
      >
        {filteredLogs.length === 0 ? (
          <div className="p-4 text-gray-500 text-center">
            No logs to display
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {filteredLogs.map((log, index) => (
              <div key={index} className="flex items-start gap-2 py-1 px-2 hover:bg-gray-800/50 rounded">
                <span className="text-gray-500 flex-shrink-0">
                  {formatTimestamp(log.timestamp)}
                </span>
                <span className={`px-1.5 py-0.5 rounded text-xs font-medium flex-shrink-0 ${getLevelBadge(log.level)}`}>
                  {log.level.toUpperCase()}
                </span>
                <span className="text-purple-400 flex-shrink-0">
                  [{log.agent}]
                </span>
                <span className={`${getLevelColor(log.level)} break-all`}>
                  {log.message}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {!autoScroll && (
        <button
          onClick={() => {
            setAutoScroll(true);
            if (containerRef.current) {
              containerRef.current.scrollTop = containerRef.current.scrollHeight;
            }
          }}
          className="w-full py-2 bg-gray-800 text-gray-400 text-sm hover:text-white transition-colors border-t border-gray-700"
        >
          ↓ Scroll to bottom
        </button>
      )}
    </div>
  );
}
