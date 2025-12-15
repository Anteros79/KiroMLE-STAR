/**
 * MLE-STAR API Client Service
 * 
 * Provides methods for communicating with the backend REST API
 * and WebSocket for real-time updates.
 */

import { MLEStarConfig, TaskDescription, LogEntry } from '@/types';

// API Configuration
const API_BASE_URL = typeof window !== 'undefined' 
  ? (window as unknown as { ENV?: { NEXT_PUBLIC_API_URL?: string } }).ENV?.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  : 'http://localhost:8000';
const WS_BASE_URL = typeof window !== 'undefined'
  ? (window as unknown as { ENV?: { NEXT_PUBLIC_WS_URL?: string } }).ENV?.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
  : 'ws://localhost:8000';

// Types for API responses
export interface PipelineStartResponse {
  run_id: string;
  status: string;
  message: string;
  created_at: string;
}

export interface AgentStatusUpdate {
  agent_id: string;
  agent_name: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  phase: number;
  message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface PhaseStatusUpdate {
  phase: number;
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number;
  message?: string;
  started_at?: string;
  completed_at?: string;
  agents: AgentStatusUpdate[];
}

export interface PipelineStatusResponse {
  run_id: string;
  status: string;
  current_phase: number | null;
  is_running: boolean;
  is_paused: boolean;
  phases: PhaseStatusUpdate[];
  current_score: number | null;
  best_score: number | null;
  current_code: string | null;
  error: string | null;
  created_at: string | null;
  updated_at: string | null;
  completed_at: string | null;
}

export interface WebSocketMessage {
  type: string;
  run_id: string;
  data: Record<string, unknown>;
  timestamp: string;
}

// API Error class
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Helper function for API requests
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorDetails;
    try {
      errorDetails = JSON.parse(errorText);
    } catch {
      errorDetails = errorText;
    }
    throw new APIError(
      `API request failed: ${response.statusText}`,
      response.status,
      errorDetails
    );
  }

  return response.json();
}

// Pipeline API methods
export const pipelineAPI = {
  /**
   * Start a new pipeline run
   */
  async start(
    task: TaskDescription,
    config: MLEStarConfig
  ): Promise<PipelineStartResponse> {
    return apiRequest<PipelineStartResponse>('/api/pipeline/start', {
      method: 'POST',
      body: JSON.stringify({
        task_description: {
          description: task.description,
          task_type: task.task_type,
          data_modality: task.data_modality,
          evaluation_metric: task.evaluation_metric,
          dataset_path: task.dataset_path,
          submission_format: task.submission_format,
        },
        config: {
          num_retrieved_models: config.num_retrieved_models,
          inner_loop_iterations: config.inner_loop_iterations,
          outer_loop_iterations: config.outer_loop_iterations,
          ensemble_iterations: config.ensemble_iterations,
          max_debug_retries: config.max_debug_retries,
          model_id: config.model_id,
          temperature: config.temperature,
          max_tokens: config.max_tokens,
        },
      }),
    });
  },

  /**
   * Get pipeline status
   */
  async getStatus(runId: string): Promise<PipelineStatusResponse> {
    return apiRequest<PipelineStatusResponse>(
      `/api/pipeline/status?run_id=${encodeURIComponent(runId)}`
    );
  },

  /**
   * Pause a running pipeline
   */
  async pause(runId: string): Promise<{ status: string; run_id: string }> {
    return apiRequest(`/api/pipeline/pause/${encodeURIComponent(runId)}`, {
      method: 'POST',
    });
  },

  /**
   * Resume a paused pipeline
   */
  async resume(runId: string): Promise<{ status: string; run_id: string }> {
    return apiRequest(`/api/pipeline/resume/${encodeURIComponent(runId)}`, {
      method: 'POST',
    });
  },

  /**
   * Stop a running pipeline
   */
  async stop(runId: string): Promise<{ status: string; run_id: string }> {
    return apiRequest(`/api/pipeline/stop/${encodeURIComponent(runId)}`, {
      method: 'POST',
    });
  },

  /**
   * List recent pipeline runs
   */
  async listRuns(
    limit: number = 10,
    offset: number = 0
  ): Promise<{ runs: Array<{ run_id: string; status: string; best_score: number | null }>; total: number }> {
    return apiRequest(`/api/runs?limit=${limit}&offset=${offset}`);
  },
};

// Dataset upload types
export interface UploadedFileInfo {
  filename: string;
  path: string;
  size: number;
  status: 'success';
}

export interface UploadError {
  filename: string;
  error: string;
}

export interface UploadResponse {
  uploaded: UploadedFileInfo[];
  errors: UploadError[];
  total_uploaded: number;
  total_errors: number;
}

export interface DatasetFile {
  filename: string;
  path: string;
  size: number;
  modified: string;
}

// Dataset API methods
export const datasetAPI = {
  /**
   * Upload dataset files with progress tracking
   */
  async upload(
    files: File[],
    runId?: string,
    onProgress?: (progress: number) => void
  ): Promise<UploadResponse> {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    if (runId) formData.append('run_id', runId);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = (event.loaded / event.total) * 100;
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new APIError('Upload failed', xhr.status, xhr.responseText));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new APIError('Upload failed', 0, 'Network error'));
      });

      xhr.open('POST', `${API_BASE_URL}/api/datasets/upload`);
      xhr.send(formData);
    });
  },

  /**
   * List uploaded dataset files
   */
  async list(runId?: string): Promise<{ files: DatasetFile[]; total: number }> {
    const params = runId ? `?run_id=${encodeURIComponent(runId)}` : '';
    return apiRequest(`/api/datasets/list${params}`);
  },

  /**
   * Delete a dataset file
   */
  async delete(filename: string, runId?: string): Promise<{ status: string; filename: string }> {
    const params = runId ? `?run_id=${encodeURIComponent(runId)}` : '';
    return apiRequest(`/api/datasets/${encodeURIComponent(filename)}${params}`, {
      method: 'DELETE',
    });
  },
};

// Submission API methods
export const submissionAPI = {
  /**
   * Download submission file
   */
  async download(runId: string): Promise<Blob> {
    const url = `${API_BASE_URL}/api/submission/download/${encodeURIComponent(runId)}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new APIError(
        'Failed to download submission',
        response.status
      );
    }
    
    return response.blob();
  },

  /**
   * Trigger download in browser
   */
  async triggerDownload(runId: string, filename?: string): Promise<void> {
    const blob = await this.download(runId);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || `submission_${runId}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },
};

// WebSocket connection manager
export class PipelineWebSocket {
  private ws: WebSocket | null = null;
  private runId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null;

  // Event handlers
  public onMessage: ((message: WebSocketMessage) => void) | null = null;
  public onAgentUpdate: ((update: AgentStatusUpdate) => void) | null = null;
  public onPhaseUpdate: ((update: PhaseStatusUpdate) => void) | null = null;
  public onLogEntry: ((entry: LogEntry) => void) | null = null;
  public onScoreUpdate: ((score: number) => void) | null = null;
  public onError: ((error: Error) => void) | null = null;
  public onClose: (() => void) | null = null;
  public onOpen: (() => void) | null = null;

  constructor(runId: string) {
    this.runId = runId;
  }

  /**
   * Connect to WebSocket
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    const url = `${WS_BASE_URL}/ws/pipeline/${this.runId}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log(`WebSocket connected for run ${this.runId}`);
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.onOpen?.();
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      this.onError?.(new Error('WebSocket connection error'));
    };

    this.ws.onclose = () => {
      console.log(`WebSocket closed for run ${this.runId}`);
      this.stopHeartbeat();
      this.onClose?.();
      this.attemptReconnect();
    };
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(message: WebSocketMessage): void {
    this.onMessage?.(message);

    switch (message.type) {
      case 'agent_update':
        if (this.onAgentUpdate && message.data) {
          this.onAgentUpdate(message.data as unknown as AgentStatusUpdate);
        }
        break;

      case 'phase_update':
        if (this.onPhaseUpdate && message.data) {
          this.onPhaseUpdate(message.data as unknown as PhaseStatusUpdate);
        }
        break;

      case 'log':
        if (this.onLogEntry && message.data) {
          const data = message.data as { level: string; agent: string; message: string };
          this.onLogEntry({
            timestamp: new Date(message.timestamp),
            level: data.level as LogEntry['level'],
            agent: data.agent,
            message: data.message,
          });
        }
        break;

      case 'score_update':
        if (this.onScoreUpdate && message.data.score !== undefined) {
          this.onScoreUpdate(message.data.score as number);
        }
        break;

      case 'heartbeat':
        // Heartbeat received, connection is alive
        break;

      case 'initial_status':
        // Initial status received on connection
        console.log('Received initial status:', message.data);
        break;

      case 'pipeline_completed':
      case 'pipeline_error':
        console.log(`Pipeline ${message.type}:`, message.data);
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 25000);
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Health check
export async function checkHealth(): Promise<{ status: string; timestamp: string }> {
  return apiRequest('/health');
}

// Export default API object
export default {
  pipeline: pipelineAPI,
  submission: submissionAPI,
  dataset: datasetAPI,
  checkHealth,
  PipelineWebSocket,
};
