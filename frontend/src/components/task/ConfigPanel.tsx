'use client';

import React, { useState } from 'react';
import { Settings, Cpu, Zap, RefreshCw, ChevronDown, Server, Cloud, Sparkles } from 'lucide-react';
import { MLEStarConfig, DEFAULT_CONFIG, ModelProvider } from '@/types';

interface ConfigPanelProps {
  config: MLEStarConfig;
  onChange: (config: MLEStarConfig) => void;
  disabled?: boolean;
}

const MODEL_PRESETS = {
  ollama: [
    { id: 'gemma3:27b', name: 'Gemma 3 27B', desc: 'Local • High Quality' },
    { id: 'llama3.3:70b', name: 'Llama 3.3 70B', desc: 'Local • Best Quality' },
    { id: 'qwen2.5:32b', name: 'Qwen 2.5 32B', desc: 'Local • Fast' },
    { id: 'deepseek-r1:32b', name: 'DeepSeek R1 32B', desc: 'Local • Reasoning' },
  ],
  bedrock: [
    { id: 'anthropic.claude-sonnet-4-20250514-v1:0', name: 'Claude Sonnet 4', desc: 'AWS • Balanced' },
    { id: 'anthropic.claude-3-5-sonnet-20241022-v2:0', name: 'Claude 3.5 Sonnet', desc: 'AWS • Fast' },
  ],
  openai: [
    { id: 'gpt-4o', name: 'GPT-4o', desc: 'OpenAI • Multimodal' },
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', desc: 'OpenAI • Fast' },
  ],
};

export default function ConfigPanel({ config, onChange, disabled }: ConfigPanelProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const updateConfig = <K extends keyof MLEStarConfig>(key: K, value: MLEStarConfig[K]) => {
    onChange({ ...config, [key]: value });
  };

  const resetToDefaults = () => {
    onChange(DEFAULT_CONFIG);
  };

  const providerIcons: Record<ModelProvider, React.ReactNode> = {
    ollama: <Server className="w-4 h-4" />,
    bedrock: <Cloud className="w-4 h-4" />,
    openai: <Sparkles className="w-4 h-4" />,
  };

  return (
    <div className="bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200/60 bg-white/50 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20">
              <Settings className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">Configuration</h3>
              <p className="text-xs text-slate-500">Pipeline & Model Settings</p>
            </div>
          </div>
          <button
            onClick={resetToDefaults}
            disabled={disabled}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all disabled:opacity-40"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reset
          </button>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Model Provider Selection */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-slate-700">Model Provider</label>
          <div className="grid grid-cols-3 gap-2">
            {(['ollama', 'bedrock', 'openai'] as ModelProvider[]).map((provider) => (
              <button
                key={provider}
                onClick={() => {
                  updateConfig('model_provider', provider);
                  const presets = MODEL_PRESETS[provider];
                  if (presets.length > 0) {
                    updateConfig('model_id', presets[0].id);
                  }
                }}
                disabled={disabled}
                className={`flex items-center justify-center gap-2 px-4 py-3 rounded-xl border-2 transition-all ${
                  config.model_provider === provider
                    ? 'border-indigo-500 bg-indigo-50 text-indigo-700 shadow-sm'
                    : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                } disabled:opacity-40`}
              >
                {providerIcons[provider]}
                <span className="text-sm font-medium capitalize">{provider}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Model Selection */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-slate-700">Model</label>
          <div className="grid grid-cols-1 gap-2">
            {MODEL_PRESETS[config.model_provider].map((preset) => (
              <button
                key={preset.id}
                onClick={() => updateConfig('model_id', preset.id)}
                disabled={disabled}
                className={`flex items-center justify-between px-4 py-3 rounded-xl border transition-all text-left ${
                  config.model_id === preset.id
                    ? 'border-indigo-500 bg-gradient-to-r from-indigo-50 to-purple-50 shadow-sm'
                    : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
                } disabled:opacity-40`}
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    config.model_id === preset.id 
                      ? 'bg-indigo-100 text-indigo-600' 
                      : 'bg-slate-100 text-slate-500'
                  }`}>
                    <Cpu className="w-4 h-4" />
                  </div>
                  <div>
                    <p className={`text-sm font-medium ${
                      config.model_id === preset.id ? 'text-indigo-900' : 'text-slate-700'
                    }`}>
                      {preset.name}
                    </p>
                    <p className="text-xs text-slate-500">{preset.desc}</p>
                  </div>
                </div>
                {config.model_id === preset.id && (
                  <div className="w-2 h-2 rounded-full bg-indigo-500" />
                )}
              </button>
            ))}
          </div>
          
          {/* Custom Model ID */}
          <input
            type="text"
            value={config.model_id}
            onChange={(e) => updateConfig('model_id', e.target.value)}
            disabled={disabled}
            placeholder="Or enter custom model ID..."
            className="w-full px-4 py-2.5 text-sm border border-slate-200 rounded-xl bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all disabled:opacity-40 placeholder:text-slate-400"
          />
        </div>

        {/* Ollama URL (only show for Ollama) */}
        {config.model_provider === 'ollama' && (
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Ollama Server URL</label>
            <input
              type="text"
              value={config.ollama_base_url}
              onChange={(e) => updateConfig('ollama_base_url', e.target.value)}
              disabled={disabled}
              className="w-full px-4 py-2.5 text-sm border border-slate-200 rounded-xl bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all disabled:opacity-40"
            />
          </div>
        )}

        {/* Quick Settings - Bento Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-4 bg-white rounded-xl border border-slate-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Temperature</span>
              <span className="text-sm font-semibold text-slate-900">{config.temperature}</span>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.1}
              value={config.temperature}
              onChange={(e) => updateConfig('temperature', parseFloat(e.target.value))}
              disabled={disabled}
              className="w-full h-1.5 bg-slate-200 rounded-full appearance-none cursor-pointer accent-indigo-500 disabled:opacity-40"
            />
          </div>
          
          <div className="p-4 bg-white rounded-xl border border-slate-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Max Tokens</span>
              <span className="text-sm font-semibold text-slate-900">{(config.max_tokens / 1000).toFixed(0)}K</span>
            </div>
            <input
              type="range"
              min={1024}
              max={16384}
              step={1024}
              value={config.max_tokens}
              onChange={(e) => updateConfig('max_tokens', parseInt(e.target.value))}
              disabled={disabled}
              className="w-full h-1.5 bg-slate-200 rounded-full appearance-none cursor-pointer accent-indigo-500 disabled:opacity-40"
            />
          </div>
        </div>

        {/* Advanced Settings Toggle */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 text-sm text-slate-600 hover:text-indigo-600 transition-colors"
        >
          <ChevronDown className={`w-4 h-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
          Advanced Settings
        </button>

        {/* Advanced Settings */}
        {showAdvanced && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
            {[
              { key: 'num_retrieved_models', label: 'Models', icon: Cpu, min: 1, max: 10 },
              { key: 'inner_loop_iterations', label: 'Inner Loop', icon: RefreshCw, min: 1, max: 10 },
              { key: 'outer_loop_iterations', label: 'Outer Loop', icon: RefreshCw, min: 1, max: 10 },
              { key: 'ensemble_iterations', label: 'Ensemble', icon: Zap, min: 1, max: 10 },
            ].map(({ key, label, icon: Icon, min, max }) => (
              <div key={key} className="p-3 bg-white rounded-xl border border-slate-200">
                <div className="flex items-center gap-2 mb-2">
                  <Icon className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-xs font-medium text-slate-600">{label}</span>
                </div>
                <input
                  type="number"
                  min={min}
                  max={max}
                  value={config[key as keyof MLEStarConfig] as number}
                  onChange={(e) => updateConfig(key as keyof MLEStarConfig, parseInt(e.target.value) || min)}
                  disabled={disabled}
                  className="w-full px-3 py-2 text-sm font-medium text-center border border-slate-200 rounded-lg bg-slate-50 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all disabled:opacity-40"
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
