'use client';

import React, { useState } from 'react';
import { Copy, Check, Download, Maximize2, Minimize2 } from 'lucide-react';

interface CodeViewerProps {
  code: string;
  language?: string;
  title?: string;
  showLineNumbers?: boolean;
  maxHeight?: string;
}

export default function CodeViewer({
  code,
  language = 'python',
  title,
  showLineNumbers = true,
  maxHeight = '500px',
}: CodeViewerProps) {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `solution.${language === 'python' ? 'py' : language}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const lines = code.split('\n');

  return (
    <div className={`bg-gray-900 rounded-lg overflow-hidden ${isExpanded ? 'fixed inset-4 z-50' : ''}`}>
      {title && (
        <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
          <span className="text-sm font-medium text-gray-300">{title}</span>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="p-1.5 text-gray-400 hover:text-white transition-colors"
              title="Copy code"
            >
              {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
            </button>
            <button
              onClick={handleDownload}
              className="p-1.5 text-gray-400 hover:text-white transition-colors"
              title="Download code"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1.5 text-gray-400 hover:text-white transition-colors"
              title={isExpanded ? 'Minimize' : 'Maximize'}
            >
              {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          </div>
        </div>
      )}
      
      <div
        className="overflow-auto"
        style={{ maxHeight: isExpanded ? 'calc(100vh - 120px)' : maxHeight }}
      >
        <pre className="p-4 text-sm">
          <code className="text-gray-100">
            {lines.map((line, index) => (
              <div key={index} className="flex">
                {showLineNumbers && (
                  <span className="select-none text-gray-500 w-12 text-right pr-4 flex-shrink-0">
                    {index + 1}
                  </span>
                )}
                <span className="flex-1 whitespace-pre-wrap break-all">{line || ' '}</span>
              </div>
            ))}
          </code>
        </pre>
      </div>
      
      {isExpanded && (
        <div
          className="fixed inset-0 bg-black/50 -z-10"
          onClick={() => setIsExpanded(false)}
        />
      )}
    </div>
  );
}
