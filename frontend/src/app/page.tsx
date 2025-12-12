'use client';

import React, { useState, useCallback } from 'react';
import { MainLayout } from '@/components/layout';
import { TaskInputForm, DatasetUpload, ConfigPanel } from '@/components/task';
import { PipelineVisualization, StatusIndicator } from '@/components/pipeline';
import { ExecutionControls, ProgressIndicator, LogViewer } from '@/components/execution';
import { CodeViewer, ScoreDisplay, RefinementHistory, AblationResults } from '@/components/results';
import { SubmissionPreview, EnsembleResults } from '@/components/submission';
import {
  MLEStarConfig,
  TaskDescription,
  PipelineState,
  AgentNode,
  LogEntry,
  RefinementAttempt,
  EnsembleResult,
  DEFAULT_CONFIG,
  PhaseStatus,
} from '@/types';

// Initial state
const initialPipelineState: PipelineState = {
  phase1: { status: 'pending', progress: 0 },
  phase2: { status: 'pending', progress: 0 },
  phase3: { status: 'pending', progress: 0 },
  currentPhase: null,
  isRunning: false,
  isPaused: false,
};

const initialAgents: AgentNode[] = [
  { id: 'retriever', name: 'Retriever', status: 'idle', phase: 1 },
  { id: 'evaluator', name: 'Evaluator', status: 'idle', phase: 1 },
  { id: 'merger', name: 'Merger', status: 'idle', phase: 1 },
  { id: 'leakage_checker', name: 'Leakage Checker', status: 'idle', phase: 1 },
  { id: 'usage_checker', name: 'Usage Checker', status: 'idle', phase: 1 },
  { id: 'ablation', name: 'Ablation Study', status: 'idle', phase: 2 },
  { id: 'summarizer', name: 'Summarizer', status: 'idle', phase: 2 },
  { id: 'extractor', name: 'Extractor', status: 'idle', phase: 2 },
  { id: 'coder', name: 'Coder', status: 'idle', phase: 2 },
  { id: 'planner', name: 'Planner', status: 'idle', phase: 2 },
  { id: 'ensemble_planner', name: 'Ensemble Planner', status: 'idle', phase: 3 },
  { id: 'ensembler', name: 'Ensembler', status: 'idle', phase: 3 },
  { id: 'submission', name: 'Submission', status: 'idle', phase: 3 },
];

export default function Home() {
  // State
  const [activeSection, setActiveSection] = useState('task');
  const [config, setConfig] = useState<MLEStarConfig>(DEFAULT_CONFIG);
  const [task, setTask] = useState<TaskDescription | null>(null);
  const [pipelineState, setPipelineState] = useState<PipelineState>(initialPipelineState);
  const [agents, setAgents] = useState<AgentNode[]>(initialAgents);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [runId, setRunId] = useState<string | null>(null);
  
  // Results state
  const [currentCode, setCurrentCode] = useState<string>('');
  const [validationScore, setValidationScore] = useState<number>(0);
  const [refinementAttempts, setRefinementAttempts] = useState<RefinementAttempt[]>([]);
  const [ensembleResults, setEnsembleResults] = useState<EnsembleResult[]>([]);
  const [ablationSummaries, setAblationSummaries] = useState<string[]>([]);
  const [submissionData, setSubmissionData] = useState<string[][] | null>(null);

  // Handlers
  const handleTaskSubmit = useCallback((newTask: TaskDescription) => {
    setTask(newTask);
    addLog('info', 'System', `Task configured: ${newTask.task_type} on ${newTask.data_modality} data`);
  }, []);

  const handleFileUpload = useCallback((files: File[]) => {
    files.forEach(file => {
      addLog('info', 'System', `File uploaded: ${file.name}`);
    });
  }, []);

  const addLog = useCallback((level: LogEntry['level'], agent: string, message: string) => {
    setLogs(prev => [...prev, {
      timestamp: new Date(),
      level,
      agent,
      message,
    }]);
  }, []);

  const handleStart = useCallback(async () => {
    if (!task) {
      addLog('error', 'System', 'Please configure a task before starting');
      return;
    }

    setPipelineState(prev => ({
      ...prev,
      isRunning: true,
      currentPhase: 1,
      phase1: { ...prev.phase1, status: 'running', startTime: new Date() },
    }));

    addLog('info', 'System', 'Pipeline started');
    addLog('info', 'Retriever', 'Searching for relevant models...');

    // Simulate pipeline execution for demo
    simulatePipeline();
  }, [task]);

  const simulatePipeline = useCallback(() => {
    // This is a simulation for the frontend demo
    // In production, this would poll the backend API
    let progress = 0;
    const interval = setInterval(() => {
      progress += 5;
      
      if (progress <= 100) {
        setPipelineState(prev => ({
          ...prev,
          phase1: { ...prev.phase1, progress, message: 'Processing...' },
        }));
      }
      
      if (progress === 30) {
        setAgents(prev => prev.map(a => 
          a.id === 'retriever' ? { ...a, status: 'completed' } :
          a.id === 'evaluator' ? { ...a, status: 'running' } : a
        ));
        addLog('success', 'Retriever', 'Found 4 model candidates');
        addLog('info', 'Evaluator', 'Evaluating candidates...');
      }
      
      if (progress === 60) {
        setAgents(prev => prev.map(a => 
          a.id === 'evaluator' ? { ...a, status: 'completed' } :
          a.id === 'merger' ? { ...a, status: 'running' } : a
        ));
        addLog('success', 'Evaluator', 'Evaluation complete. Best score: 0.8234');
        addLog('info', 'Merger', 'Merging solutions...');
      }
      
      if (progress >= 100) {
        clearInterval(interval);
        setPipelineState(prev => ({
          ...prev,
          phase1: { ...prev.phase1, status: 'completed', progress: 100, endTime: new Date() },
          phase2: { ...prev.phase2, status: 'running', startTime: new Date() },
          currentPhase: 2,
        }));
        setAgents(prev => prev.map(a => 
          a.phase === 1 ? { ...a, status: 'completed' } :
          a.id === 'ablation' ? { ...a, status: 'running' } : a
        ));
        addLog('success', 'System', 'Phase 1 complete');
        addLog('info', 'Ablation Study', 'Starting ablation analysis...');
        
        // Set some demo results
        setCurrentCode(`# MLE-STAR Generated Solution
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split

# Load data
train = pd.read_csv('train.csv')
test = pd.read_csv('test.csv')

# Feature engineering
X = train.drop('target', axis=1)
y = train['target']

# Train models
rf = RandomForestClassifier(n_estimators=100)
gb = GradientBoostingClassifier(n_estimators=100)

rf.fit(X, y)
gb.fit(X, y)

# Ensemble predictions
predictions = (rf.predict_proba(test)[:, 1] + gb.predict_proba(test)[:, 1]) / 2
`);
        setValidationScore(0.8456);
      }
    }, 500);
  }, []);

  const handlePause = useCallback(() => {
    setPipelineState(prev => ({ ...prev, isPaused: true }));
    addLog('warning', 'System', 'Pipeline paused');
  }, []);

  const handleResume = useCallback(() => {
    setPipelineState(prev => ({ ...prev, isPaused: false }));
    addLog('info', 'System', 'Pipeline resumed');
  }, []);

  const handleStop = useCallback(() => {
    setPipelineState(prev => ({
      ...prev,
      isRunning: false,
      isPaused: false,
    }));
    addLog('warning', 'System', 'Pipeline stopped');
  }, []);

  const handleReset = useCallback(() => {
    setPipelineState(initialPipelineState);
    setAgents(initialAgents);
    setLogs([]);
    setCurrentCode('');
    setValidationScore(0);
    setRefinementAttempts([]);
    setEnsembleResults([]);
    setAblationSummaries([]);
    setSubmissionData(null);
  }, []);

  const handleDownloadSubmission = useCallback(() => {
    // In production, this would call the API
    addLog('info', 'System', 'Downloading submission file...');
  }, []);

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
            <h2 className="text-2xl font-bold text-gray-900">Task Configuration</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-6">
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Task Description</h3>
                  <TaskInputForm
                    onSubmit={handleTaskSubmit}
                    disabled={pipelineState.isRunning}
                  />
                </div>
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Dataset Upload</h3>
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
            <PipelineVisualization
              phase1Status={pipelineState.phase1.status}
              phase2Status={pipelineState.phase2.status}
              phase3Status={pipelineState.phase3.status}
              currentPhase={pipelineState.currentPhase}
              agents={agents}
            />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ProgressIndicator
                phase1={pipelineState.phase1}
                phase2={pipelineState.phase2}
                phase3={pipelineState.phase3}
              />
              <StatusIndicator pipelineState={pipelineState} />
            </div>
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
            <LogViewer logs={logs} onClear={() => setLogs([])} />
          </div>
        );

      case 'results':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Results</h2>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <ScoreDisplay
                currentScore={validationScore}
                metric={task?.evaluation_metric || 'accuracy'}
              />
              <div className="lg:col-span-2">
                <AblationResults summaries={ablationSummaries} />
              </div>
            </div>
            {currentCode && (
              <CodeViewer
                code={currentCode}
                title="Current Solution"
                language="python"
              />
            )}
            <RefinementHistory attempts={refinementAttempts} />
          </div>
        );

      case 'submission':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Submission</h2>
            <EnsembleResults results={ensembleResults} />
            {submissionData ? (
              <SubmissionPreview
                data={submissionData}
                headers={['id', 'prediction']}
                totalRows={submissionData.length}
                onDownload={handleDownloadSubmission}
              />
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
                <p className="text-gray-500">
                  No submission generated yet. Complete the pipeline to generate a submission file.
                </p>
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
