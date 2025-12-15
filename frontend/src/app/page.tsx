'use client';

import React, { useState, useCallback } from 'react';
import { MainLayout } from '@/components/layout';
import { TaskInputForm, DatasetUpload, ConfigPanel } from '@/components/task';
import { PipelineVisualization, StatusIndicator } from '@/components/pipeline';
import { ExecutionControls, ProgressIndicator, LogViewer } from '@/components/execution';
import { CodeViewer, ScoreDisplay, RefinementHistory, AblationResults } from '@/components/results';
import { SubmissionPreview, EnsembleResults } from '@/components/submission';
import { usePipeline } from '@/hooks';
import { TaskDescription, PhaseStatus } from '@/types';
import { Sparkles, Zap, FileText, Trophy, Cpu, Wifi, WifiOff } from 'lucide-react';

export default function Home() {
  const [activeSection, setActiveSection] = useState('task');
  
  // Use the pipeline hook for all state management
  const {
    config,
    task,
    pipelineState,
    agents,
    logs,
    currentCode,
    validationScore,
    refinementAttempts,
    ensembleResults,
    ablationSummaries,
    submissionData,
    isConnected,
    isBackendAvailable,
    setConfig,
    setTask,
    handleStart,
    handlePause,
    handleResume,
    handleStop,
    handleReset,
    handleDownloadSubmission,
    addLog,
    clearLogs,
  } = usePipeline();

  // Handlers
  const handleTaskSubmit = useCallback((newTask: TaskDescription) => {
    setTask(newTask);
    addLog('info', 'System', `Task configured: ${newTask.task_type} on ${newTask.data_modality} data`);
  }, [setTask, addLog]);

  const handleFileUpload = useCallback((files: File[]) => {
    files.forEach(file => {
      addLog('info', 'System', `File uploaded: ${file.name}`);
    });
  }, [addLog]);

  const phaseStatuses: { [key: number]: PhaseStatus } = {
    1: pipelineState.phase1.status,
    2: pipelineState.phase2.status,
    3: pipelineState.phase3.status,
  };

  // Render section content
  const renderContent = () => {
    switch (activeSection) {
      case 'task':
        return (
          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">Task Configuration</h2>
                  <p className="text-sm text-slate-500">Define your ML task and upload data</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
                  isBackendAvailable 
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/60' 
                    : 'bg-amber-50 text-amber-700 border border-amber-200/60'
                }`}>
                  <Cpu className="w-3.5 h-3.5" />
                  {isBackendAvailable ? 'Backend Connected' : 'Demo Mode'}
                </div>
                {isConnected && (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                    <Wifi className="w-3.5 h-3.5" />
                    Live Updates
                  </div>
                )}
              </div>
            </div>

            {/* Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-6">
                <div className="bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-2xl border border-slate-200/60 p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20">
                      <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900">Task Description</h3>
                      <p className="text-xs text-slate-500">Define your ML problem</p>
                    </div>
                  </div>
                  <TaskInputForm
                    onSubmit={handleTaskSubmit}
                    disabled={pipelineState.isRunning}
                  />
                </div>
                <div className="bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-2xl border border-slate-200/60 p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="p-2 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl shadow-lg shadow-emerald-500/20">
                      <Zap className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900">Dataset Upload</h3>
                      <p className="text-xs text-slate-500">Upload your training data</p>
                    </div>
                  </div>
                  <DatasetUpload
                    onUpload={handleFileUpload}
                    disabled={pipelineState.isRunning}
                  />
                </div>
              </div>
              <div>
                <ConfigPanel
                  config={config}
                  onChange={setConfig}
                  disabled={pipelineState.isRunning}
                />
              </div>
            </div>
          </div>
        );

      case 'phase1':
      case 'phase2':
      case 'phase3':
        return (
          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20">
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">Pipeline Execution</h2>
                  <p className="text-sm text-slate-500">Monitor agent progress in real-time</p>
                </div>
              </div>
              {isConnected ? (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                  <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" />
                  Live Updates Active
                </div>
              ) : (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-slate-50 text-slate-600 border border-slate-200/60">
                  <WifiOff className="w-3.5 h-3.5" />
                  Offline
                </div>
              )}
            </div>

            {/* Pipeline Visualization */}
            <PipelineVisualization
              phase1Status={pipelineState.phase1.status}
              phase2Status={pipelineState.phase2.status}
              phase3Status={pipelineState.phase3.status}
              currentPhase={pipelineState.currentPhase}
              agents={agents}
            />

            {/* Progress & Status */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ProgressIndicator
                phase1={pipelineState.phase1}
                phase2={pipelineState.phase2}
                phase3={pipelineState.phase3}
              />
              <StatusIndicator pipelineState={pipelineState} />
            </div>

            {/* Controls */}
            <ExecutionControls
              isRunning={pipelineState.isRunning}
              isPaused={pipelineState.isPaused}
              canStart={!!task}
              onStart={handleStart}
              onPause={handlePause}
              onResume={handleResume}
              onStop={handleStop}
              onReset={handleReset}
            />

            {/* Logs */}
            <LogViewer logs={logs} onClear={clearLogs} />
          </div>
        );

      case 'results':
        return (
          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl shadow-lg shadow-emerald-500/20">
                <Trophy className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Results</h2>
                <p className="text-sm text-slate-500">View scores, ablation studies, and refinements</p>
              </div>
            </div>

            {/* Score & Ablation */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <ScoreDisplay
                currentScore={validationScore}
                metric={task?.evaluation_metric || 'accuracy'}
              />
              <div className="lg:col-span-2">
                <AblationResults summaries={ablationSummaries} />
              </div>
            </div>

            {/* Code Viewer */}
            {currentCode && (
              <CodeViewer
                code={currentCode}
                title="Current Solution"
                language="python"
              />
            )}

            {/* Refinement History */}
            <RefinementHistory attempts={refinementAttempts} />
          </div>
        );

      case 'submission':
        return (
          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl shadow-lg shadow-amber-500/20">
                <Trophy className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Submission</h2>
                <p className="text-sm text-slate-500">Review ensemble results and download submission</p>
              </div>
            </div>

            {/* Ensemble Results */}
            <EnsembleResults results={ensembleResults} />

            {/* Submission Preview */}
            {submissionData ? (
              <SubmissionPreview
                data={submissionData}
                headers={['id', 'prediction']}
                totalRows={submissionData.length}
                onDownload={handleDownloadSubmission}
              />
            ) : (
              <div className="bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-2xl border border-slate-200/60 p-12 text-center shadow-sm">
                <div className="w-16 h-16 mx-auto mb-4 bg-slate-100 rounded-2xl flex items-center justify-center">
                  <Trophy className="w-8 h-8 text-slate-400" />
                </div>
                <p className="text-slate-600 font-medium">No submission generated yet</p>
                <p className="text-sm text-slate-400 mt-1">Complete the pipeline to generate a submission file</p>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <MainLayout
      activeSection={activeSection}
      onSectionChange={setActiveSection}
      phaseStatuses={phaseStatuses}
    >
      {renderContent()}
    </MainLayout>
  );
}
