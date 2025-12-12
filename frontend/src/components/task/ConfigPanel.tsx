'use client';

import React from 'react';
import { Settings, Info } from 'lucide-react';
import { MLEStarConfig, DEFAULT_CONFIG } from '@/types';

interface ConfigPanelProps {
  config: MLEStarConfig;
  onChange: (config: MLEStarConfig) => void;
  disabled?: boolean;
}

interface ConfigFieldProps {
  label: string;
  tooltip: string;
  children: React.ReactNode;
}

function ConfigField({ label, tooltip, children }: ConfigFieldProps) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <div className="group relative">
          <Info className="w-4 h-4 text-gray-400 cursor-help" />
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
            {tooltip}
          </div>
        </div>
      </div>
      {children}
    </div>
  );
}

export default function ConfigPanel({ config, onChange, disabled }: ConfigPanelProps) {
  const updateConfig = (key: keyof MLEStarConfig, value: number | string) => {
    onChange({ ...config, [key]: value });
  };

  const resetToDefaults = () => {
    onChange(DEFAULT_CONFIG);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Configuration</h3>
        </div>
        <button
          onClick={resetToDefaults}
          disabled={disabled}
          className="text-sm text-primary-600 hover:text-primary-700 disabled:text-gray-400"
        >
          Reset to defaults
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ConfigField
          label="Retrieved Models"
          tooltip="Number of model candidates to retrieve from web search"
        >
          <input
            type="number"
            min={1}
            max={10}
            value={config.num_retrieved_models}
            onChange={(e) => updateConfig('num_retrieved_models', parseInt(e.target.value) || 4)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
          />
        </ConfigField>

        <ConfigField
          label="Inner Loop Iterations"
          tooltip="Number of refinement attempts per code block"
        >
          <input
            type="number"
            min={1}
            max={10}
            value={config.inner_loop_iterations}
            onChange={(e) => updateConfig('inner_loop_iterations', parseInt(e.target.value) || 4)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
          />
        </ConfigField>

        <ConfigField
          label="Outer Loop Iterations"
          tooltip="Number of code blocks to refine"
        >
          <input
            type="number"
            min={1}
            max={10}
            value={config.outer_loop_iterations}
            onChange={(e) => updateConfig('outer_loop_iterations', parseInt(e.target.value) || 4)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
          />
        </ConfigField>

        <ConfigField
          label="Ensemble Iterations"
          tooltip="Number of ensemble strategies to explore"
        >
          <input
            type="number"
            min={1}
            max={10}
            value={config.ensemble_iterations}
            onChange={(e) => updateConfig('ensemble_iterations', parseInt(e.target.value) || 5)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
          />
        </ConfigField>

        <ConfigField
          label="Max Debug Retries"
          tooltip="Maximum attempts to fix code errors"
        >
          <input
            type="number"
            min={1}
            max={10}
            value={config.max_debug_retries}
            onChange={(e) => updateConfig('max_debug_retries', parseInt(e.target.value) || 3)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
          />
        </ConfigField>

        <ConfigField
          label="Temperature"
          tooltip="LLM temperature for response randomness (0-1)"
        >
          <input
            type="number"
            min={0}
            max={1}
            step={0.1}
            value={config.temperature}
            onChange={(e) => updateConfig('temperature', parseFloat(e.target.value) || 0.7)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
          />
        </ConfigField>

        <ConfigField
          label="Max Tokens"
          tooltip="Maximum tokens for LLM responses"
        >
          <input
            type="number"
            min={1024}
            max={16384}
            step={1024}
            value={config.max_tokens}
            onChange={(e) => updateConfig('max_tokens', parseInt(e.target.value) || 4096)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
          />
        </ConfigField>

        <ConfigField
          label="Model ID"
          tooltip="Bedrock model identifier"
        >
          <input
            type="text"
            value={config.model_id}
            onChange={(e) => updateConfig('model_id', e.target.value)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
          />
        </ConfigField>
      </div>
    </div>
  );
}
