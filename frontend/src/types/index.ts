// MLE-STAR Configuration Types
export type ModelProvider = 'ollama' | 'bedrock' | 'openai';

export interface MLEStarConfig {
  num_retrieved_models: number;
  inner_loop_iterations: number;
  outer_loop_iterations: number;
  ensemble_iterations: number;
  max_debug_retries: number;
  model_id: string;
  model_provider: ModelProvider;
  ollama_base_url: string;
  temperature: number;
  max_tokens: number;
}

// Task Description Types
export interface TaskDescription {
  description: string;
  task_type: string;
  data_modality: string;
  evaluation_metric: string;
  dataset_path: string;
  submission_format?: string;
}

// Pipeline Status Types
export type PhaseStatus = 'pending' | 'running' | 'completed' | 'error';

export interface PhaseState {
  status: PhaseStatus;
  progress: number;
  message?: string;
  startTime?: Date;
  endTime?: Date;
}

export interface PipelineState {
  phase1: PhaseState;
  phase2: PhaseState;
  phase3: PhaseState;
  currentPhase: 1 | 2 | 3 | null;
  isRunning: boolean;
  isPaused: boolean;
}

// Agent Node Types
export interface AgentNode {
  id: string;
  name: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  phase: 1 | 2 | 3;
}

// Model Candidate Types
export interface ModelCandidate {
  name: string;
  description: string;
  example_code: string;
  validation_score?: number;
  generated_code?: string;
}

// Solution State Types
export interface SolutionState {
  current_code: string;
  validation_score: number;
  ablation_summaries: string[];
  refined_blocks: string[];
  outer_iteration: number;
  inner_iteration: number;
}

// Refinement Attempt Types
export interface RefinementAttempt {
  plan: string;
  refined_code_block: string;
  full_solution: string;
  validation_score: number;
  iteration: number;
}

// Ensemble Result Types
export interface EnsembleResult {
  strategy: string;
  merged_code: string;
  validation_score: number;
  iteration: number;
}

// Log Entry Types
export interface LogEntry {
  timestamp: Date;
  level: 'info' | 'warning' | 'error' | 'success';
  agent: string;
  message: string;
}

// Results Types
export interface PipelineResults {
  finalCode: string;
  validationScore: number;
  submissionPath?: string;
  refinementHistory: RefinementAttempt[];
  ensembleResults: EnsembleResult[];
  ablationSummaries: string[];
}

// Default Configuration - Using local Ollama with Gemma 3 27B
export const DEFAULT_CONFIG: MLEStarConfig = {
  num_retrieved_models: 4,
  inner_loop_iterations: 4,
  outer_loop_iterations: 4,
  ensemble_iterations: 5,
  max_debug_retries: 3,
  model_id: 'gemma3:27b',
  model_provider: 'ollama',
  ollama_base_url: 'http://localhost:11434',
  temperature: 0.7,
  max_tokens: 4096,
};
