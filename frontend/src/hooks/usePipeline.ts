/**
 * usePipeline Hook
 * 
 * Manages pipeline state with real API integration and WebSocket updates.
 */

'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import {
  pipelineAPI,
  submissionAPI,
  PipelineWebSocket,
  PipelineStatusResponse,
  AgentStatusUpdate,
  PhaseStatusUpdate,
  checkHealth,
} from '@/services/api';
import {
  MLEStarConfig,
  TaskDescription,
  PipelineState,
  AgentNode,
  LogEntry,
  RefinementAttempt,
  EnsembleResult,
  DEFAULT_CONFIG,
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

export interface UsePipelineReturn {
  // State
  config: MLEStarConfig;
  task: TaskDescription | null;
  pipelineState: PipelineState;
  agents: AgentNode[];
  logs: LogEntry[];
  runId: string | null;
  currentCode: string;
  validationScore: number;
  refinementAttempts: RefinementAttempt[];
  ensembleResults: EnsembleResult[];
  ablationSummaries: string[];
  submissionData: string[][] | null;
  isConnected: boolean;
  isBackendAvailable: boolean;
  
  // Actions
  setConfig: (config: MLEStarConfig) => void;
  setTask: (task: TaskDescription) => void;
  handleStart: () => Promise<void>;
  handlePause: () => Promise<void>;
  handleResume: () => Promise<void>;
  handleStop: () => Promise<void>;
  handleReset: () => void;
  handleDownloadSubmission: () => Promise<void>;
  addLog: (level: LogEntry['level'], agent: string, message: string) => void;
  clearLogs: () => void;
}

export function usePipeline(): UsePipelineReturn {
  // Configuration state
  const [config, setConfig] = useState<MLEStarConfig>(DEFAULT_CONFIG);
  const [task, setTask] = useState<TaskDescription | null>(null);
  
  // Pipeline state
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
  
  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [isBackendAvailable, setIsBackendAvailable] = useState(false);
  
  // WebSocket ref
  const wsRef = useRef<PipelineWebSocket | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Add log entry
  const addLog = useCallback((level: LogEntry['level'], agent: string, message: string) => {
    setLogs(prev => [...prev, {
      timestamp: new Date(),
      level,
      agent,
      message,
    }]);
  }, []);

  // Clear logs
  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Check backend health on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        await checkHealth();
        setIsBackendAvailable(true);
      } catch {
        setIsBackendAvailable(false);
        addLog('warning', 'System', 'Backend not available. Running in demo mode.');
      }
    };
    checkBackend();
  }, [addLog]);

  // Update pipeline state from API response
  const updateFromStatus = useCallback((status: PipelineStatusResponse) => {
    setPipelineState((prev: PipelineState) => ({
      ...prev,
      isRunning: status.is_running,
      isPaused: status.is_paused,
      currentPhase: status.current_phase as 1 | 2 | 3 | null,
      phase1: {
        ...prev.phase1,
        status: status.phases[0]?.status || 'pending',
        progress: status.phases[0]?.progress || 0,
        message: status.phases[0]?.message,
      },
      phase2: {
        ...prev.phase2,
        status: status.phases[1]?.status || 'pending',
        progress: status.phases[1]?.progress || 0,
        message: status.phases[1]?.message,
      },
      phase3: {
        ...prev.phase3,
        status: status.phases[2]?.status || 'pending',
        progress: status.phases[2]?.progress || 0,
        message: status.phases[2]?.message,
      },
    }));

    if (status.current_score !== null) {
      setValidationScore(status.current_score);
    }
    if (status.current_code) {
      setCurrentCode(status.current_code);
    }

    // Update agents from phase data
    if (status.phases) {
      status.phases.forEach(phase => {
        if (phase.agents) {
          phase.agents.forEach(agentUpdate => {
            setAgents((prev: AgentNode[]) => prev.map((a: AgentNode) => 
              a.id === agentUpdate.agent_id 
                ? { ...a, status: agentUpdate.status }
                : a
            ));
          });
        }
      });
    }
  }, []);

  // Handle agent update from WebSocket
  const handleAgentUpdate = useCallback((update: AgentStatusUpdate) => {
    setAgents((prev: AgentNode[]) => prev.map((a: AgentNode) => 
      a.id === update.agent_id 
        ? { ...a, status: update.status }
        : a
    ));
    if (update.message) {
      const level = update.status === 'error' ? 'error' : 
                    update.status === 'completed' ? 'success' : 'info';
      addLog(level, update.agent_name, update.message);
    }
  }, [addLog]);

  // Handle phase update from WebSocket
  const handlePhaseUpdate = useCallback((update: PhaseStatusUpdate) => {
    const phaseKey = `phase${update.phase}` as 'phase1' | 'phase2' | 'phase3';
    setPipelineState((prev: PipelineState) => ({
      ...prev,
      currentPhase: update.status === 'running' ? update.phase as 1 | 2 | 3 : prev.currentPhase,
      [phaseKey]: {
        ...prev[phaseKey],
        status: update.status,
        progress: update.progress,
        message: update.message,
      },
    }));
  }, []);

  // Connect WebSocket
  const connectWebSocket = useCallback((newRunId: string) => {
    if (wsRef.current) {
      wsRef.current.disconnect();
    }

    const ws = new PipelineWebSocket(newRunId);
    
    ws.onOpen = () => {
      setIsConnected(true);
      addLog('info', 'System', 'Connected to pipeline updates');
    };
    
    ws.onClose = () => {
      setIsConnected(false);
    };
    
    ws.onAgentUpdate = handleAgentUpdate;
    ws.onPhaseUpdate = handlePhaseUpdate;
    
    ws.onLogEntry = (entry) => {
      setLogs(prev => [...prev, entry]);
    };
    
    ws.onScoreUpdate = (score) => {
      setValidationScore(score);
      addLog('success', 'System', `Validation score updated: ${score.toFixed(4)}`);
    };
    
    ws.onError = (error) => {
      addLog('error', 'System', `WebSocket error: ${error.message}`);
    };

    ws.connect();
    wsRef.current = ws;
  }, [addLog, handleAgentUpdate, handlePhaseUpdate]);

  // Start polling as fallback
  const startPolling = useCallback((newRunId: string) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    pollIntervalRef.current = setInterval(async () => {
      try {
        const status = await pipelineAPI.getStatus(newRunId);
        updateFromStatus(status);
        
        if (!status.is_running && status.status !== 'paused') {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 2000);
  }, [updateFromStatus]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  // Simulate pipeline for demo mode (defined before handleStart to avoid hoisting issues)
  const simulatePipeline = useCallback(() => {
    setPipelineState((prev: PipelineState) => ({
      ...prev,
      isRunning: true,
      currentPhase: 1,
      phase1: { ...prev.phase1, status: 'running', startTime: new Date() },
    }));

    addLog('info', 'System', 'Pipeline started (demo mode)');
    addLog('info', 'Retriever', 'Searching for relevant models...');

    let progress = 0;
    const interval = setInterval(() => {
      progress += 5;
      
      if (progress <= 100) {
        setPipelineState((prev: PipelineState) => ({
          ...prev,
          phase1: { ...prev.phase1, progress, message: 'Processing...' },
        }));
      }
      
      if (progress === 30) {
        setAgents((prev: AgentNode[]) => prev.map((a: AgentNode) => 
          a.id === 'retriever' ? { ...a, status: 'completed' as const } :
          a.id === 'evaluator' ? { ...a, status: 'running' as const } : a
        ));
        addLog('success', 'Retriever', 'Found 4 model candidates');
        addLog('info', 'Evaluator', 'Evaluating candidates...');
      }
      
      if (progress === 60) {
        setAgents((prev: AgentNode[]) => prev.map((a: AgentNode) => 
          a.id === 'evaluator' ? { ...a, status: 'completed' as const } :
          a.id === 'merger' ? { ...a, status: 'running' as const } : a
        ));
        addLog('success', 'Evaluator', 'Evaluation complete. Best score: 0.8234');
        addLog('info', 'Merger', 'Merging solutions...');
      }
      
      if (progress >= 100) {
        clearInterval(interval);
        setPipelineState((prev: PipelineState) => ({
          ...prev,
          phase1: { ...prev.phase1, status: 'completed', progress: 100, endTime: new Date() },
          phase2: { ...prev.phase2, status: 'running', startTime: new Date() },
          currentPhase: 2,
        }));
        setAgents((prev: AgentNode[]) => prev.map((a: AgentNode) => 
          a.phase === 1 ? { ...a, status: 'completed' as const } :
          a.id === 'ablation' ? { ...a, status: 'running' as const } : a
        ));
        addLog('success', 'System', 'Phase 1 complete');
        addLog('info', 'Ablation Study', 'Starting ablation analysis...');
        
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
  }, [addLog]);

  // Start pipeline
  const handleStart = useCallback(async () => {
    if (!task) {
      addLog('error', 'System', 'Please configure a task before starting');
      return;
    }

    if (!isBackendAvailable) {
      // Demo mode - simulate pipeline
      addLog('warning', 'System', 'Running in demo mode (backend not available)');
      simulatePipeline();
      return;
    }

    try {
      addLog('info', 'System', 'Starting pipeline...');
      
      const response = await pipelineAPI.start(task, config);
      setRunId(response.run_id);
      
      setPipelineState((prev: PipelineState) => ({
        ...prev,
        isRunning: true,
        currentPhase: 1,
        phase1: { ...prev.phase1, status: 'running', startTime: new Date() },
      }));

      addLog('success', 'System', `Pipeline started with run ID: ${response.run_id}`);
      
      // Connect WebSocket for real-time updates
      connectWebSocket(response.run_id);
      
      // Start polling as fallback
      startPolling(response.run_id);
      
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      addLog('error', 'System', `Failed to start pipeline: ${message}`);
    }
  }, [task, config, isBackendAvailable, addLog, connectWebSocket, startPolling, simulatePipeline]);

  // Pause pipeline
  const handlePause = useCallback(async () => {
    if (!runId || !isBackendAvailable) {
      setPipelineState((prev: PipelineState) => ({ ...prev, isPaused: true }));
      addLog('warning', 'System', 'Pipeline paused');
      return;
    }

    try {
      await pipelineAPI.pause(runId);
      setPipelineState((prev: PipelineState) => ({ ...prev, isPaused: true }));
      addLog('warning', 'System', 'Pipeline paused');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      addLog('error', 'System', `Failed to pause: ${message}`);
    }
  }, [runId, isBackendAvailable, addLog]);

  // Resume pipeline
  const handleResume = useCallback(async () => {
    if (!runId || !isBackendAvailable) {
      setPipelineState((prev: PipelineState) => ({ ...prev, isPaused: false }));
      addLog('info', 'System', 'Pipeline resumed');
      return;
    }

    try {
      await pipelineAPI.resume(runId);
      setPipelineState((prev: PipelineState) => ({ ...prev, isPaused: false }));
      addLog('info', 'System', 'Pipeline resumed');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      addLog('error', 'System', `Failed to resume: ${message}`);
    }
  }, [runId, isBackendAvailable, addLog]);

  // Stop pipeline
  const handleStop = useCallback(async () => {
    if (!runId || !isBackendAvailable) {
      setPipelineState((prev: PipelineState) => ({
        ...prev,
        isRunning: false,
        isPaused: false,
      }));
      addLog('warning', 'System', 'Pipeline stopped');
      return;
    }

    try {
      await pipelineAPI.stop(runId);
      setPipelineState((prev: PipelineState) => ({
        ...prev,
        isRunning: false,
        isPaused: false,
      }));
      addLog('warning', 'System', 'Pipeline stopped');
      
      // Cleanup WebSocket and polling
      if (wsRef.current) {
        wsRef.current.disconnect();
        wsRef.current = null;
      }
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      addLog('error', 'System', `Failed to stop: ${message}`);
    }
  }, [runId, isBackendAvailable, addLog]);

  // Reset pipeline
  const handleReset = useCallback(() => {
    // Cleanup connections
    if (wsRef.current) {
      wsRef.current.disconnect();
      wsRef.current = null;
    }
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    // Reset all state
    setPipelineState(initialPipelineState);
    setAgents(initialAgents);
    setLogs([]);
    setRunId(null);
    setCurrentCode('');
    setValidationScore(0);
    setRefinementAttempts([]);
    setEnsembleResults([]);
    setAblationSummaries([]);
    setSubmissionData(null);
    setIsConnected(false);
  }, []);

  // Download submission
  const handleDownloadSubmission = useCallback(async () => {
    if (!runId) {
      addLog('error', 'System', 'No run ID available for download');
      return;
    }

    if (!isBackendAvailable) {
      addLog('info', 'System', 'Download not available in demo mode');
      return;
    }

    try {
      addLog('info', 'System', 'Downloading submission file...');
      await submissionAPI.triggerDownload(runId);
      addLog('success', 'System', 'Submission downloaded successfully');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      addLog('error', 'System', `Failed to download: ${message}`);
    }
  }, [runId, isBackendAvailable, addLog]);

  return {
    // State
    config,
    task,
    pipelineState,
    agents,
    logs,
    runId,
    currentCode,
    validationScore,
    refinementAttempts,
    ensembleResults,
    ablationSummaries,
    submissionData,
    isConnected,
    isBackendAvailable,
    
    // Actions
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
  };
}

export default usePipeline;
