'use client';

import React, { useState } from 'react';
import { FileText, AlertCircle, CheckCircle, Sparkles, Database, BarChart3, Layers } from 'lucide-react';
import { TaskDescription } from '@/types';

interface TaskInputFormProps {
  onSubmit: (task: TaskDescription) => void;
  disabled?: boolean;
}

const TASK_TYPES = [
  { value: 'classification', label: 'Classification', icon: Layers },
  { value: 'regression', label: 'Regression', icon: BarChart3 },
  { value: 'seq2seq', label: 'Seq2Seq', icon: Sparkles },
  { value: 'time_series', label: 'Time Series', icon: BarChart3 },
  { value: 'clustering', label: 'Clustering', icon: Layers },
  { value: 'ranking', label: 'Ranking', icon: BarChart3 },
];

const DATA_MODALITIES = [
  { value: 'tabular', label: 'Tabular' },
  { value: 'image', label: 'Image' },
  { value: 'text', label: 'Text' },
  { value: 'audio', label: 'Audio' },
  { value: 'multimodal', label: 'Multimodal' },
];

const EVALUATION_METRICS = [
  { value: 'accuracy', label: 'Accuracy' },
  { value: 'f1_score', label: 'F1 Score' },
  { value: 'auc_roc', label: 'AUC-ROC' },
  { value: 'rmse', label: 'RMSE' },
  { value: 'mae', label: 'MAE' },
  { value: 'log_loss', label: 'Log Loss' },
  { value: 'map', label: 'MAP' },
  { value: 'ndcg', label: 'NDCG' },
];

export default function TaskInputForm({ onSubmit, disabled }: TaskInputFormProps) {
  const [description, setDescription] = useState('');
  const [taskType, setTaskType] = useState('classification');
  const [dataModality, setDataModality] = useState('tabular');
  const [evaluationMetric, setEvaluationMetric] = useState('accuracy');
  const [datasetPath, setDatasetPath] = useState('');
  const [submissionFormat, setSubmissionFormat] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const validate = (): boolean => {
    const newErrors: string[] = [];
    
    if (!description.trim()) {
      newErrors.push('Task description is required');
    }
    if (!datasetPath.trim()) {
      newErrors.push('Dataset path is required');
    }
    
    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) return;
    
    onSubmit({
      description,
      task_type: taskType,
      data_modality: dataModality,
      evaluation_metric: evaluationMetric,
      dataset_path: datasetPath,
      submission_format: submissionFormat || undefined,
    });
    setIsSubmitted(true);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {errors.length > 0 && (
        <div className="bg-rose-50 border border-rose-200/60 rounded-xl p-4">
          <div className="flex items-center gap-2 text-rose-700 mb-2">
            <AlertCircle className="w-5 h-5" />
            <span className="font-medium">Please fix the following:</span>
          </div>
          <ul className="list-disc list-inside text-rose-600 text-sm space-y-1">
            {errors.map((error, i) => (
              <li key={i}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {isSubmitted && errors.length === 0 && (
        <div className="bg-emerald-50 border border-emerald-200/60 rounded-xl p-4 flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-emerald-600" />
          <span className="text-emerald-700 font-medium">Task configuration saved!</span>
        </div>
      )}

      {/* Task Description */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <FileText className="w-4 h-4 text-slate-400" />
          Task Description
          <span className="text-rose-500">*</span>
        </label>
        <textarea
          value={description}
          onChange={(e) => { setDescription(e.target.value); setIsSubmitted(false); }}
          disabled={disabled}
          rows={5}
          className="w-full px-4 py-3 border border-slate-200 rounded-xl bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 disabled:bg-slate-50 disabled:cursor-not-allowed transition-all placeholder:text-slate-400 text-sm"
          placeholder="Describe your ML task in detail. Include information about the problem, data characteristics, and any specific requirements..."
        />
      </div>

      {/* Task Type Selection */}
      <div className="space-y-3">
        <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <Layers className="w-4 h-4 text-slate-400" />
          Task Type
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {TASK_TYPES.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              type="button"
              onClick={() => { setTaskType(value); setIsSubmitted(false); }}
              disabled={disabled}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-all text-sm ${
                taskType === value
                  ? 'border-indigo-500 bg-indigo-50 text-indigo-700 shadow-sm'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50'
              } disabled:opacity-40`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Data Modality & Metric */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <Database className="w-4 h-4 text-slate-400" />
            Data Modality
          </label>
          <div className="flex flex-wrap gap-2">
            {DATA_MODALITIES.map(({ value, label }) => (
              <button
                key={value}
                type="button"
                onClick={() => { setDataModality(value); setIsSubmitted(false); }}
                disabled={disabled}
                className={`px-3 py-1.5 rounded-lg border text-sm transition-all ${
                  dataModality === value
                    ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                    : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                } disabled:opacity-40`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <BarChart3 className="w-4 h-4 text-slate-400" />
            Evaluation Metric
          </label>
          <select
            value={evaluationMetric}
            onChange={(e) => { setEvaluationMetric(e.target.value); setIsSubmitted(false); }}
            disabled={disabled}
            className="w-full px-4 py-2.5 border border-slate-200 rounded-xl bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 disabled:bg-slate-50 text-sm"
          >
            {EVALUATION_METRICS.map(({ value, label }) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Dataset Path */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <Database className="w-4 h-4 text-slate-400" />
          Dataset Path
          <span className="text-rose-500">*</span>
        </label>
        <input
          type="text"
          value={datasetPath}
          onChange={(e) => { setDatasetPath(e.target.value); setIsSubmitted(false); }}
          disabled={disabled}
          className="w-full px-4 py-2.5 border border-slate-200 rounded-xl bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 disabled:bg-slate-50 text-sm placeholder:text-slate-400"
          placeholder="/path/to/dataset or URL"
        />
      </div>

      {/* Submission Format */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <FileText className="w-4 h-4 text-slate-400" />
          Submission Format
          <span className="text-slate-400 text-xs font-normal">(optional)</span>
        </label>
        <input
          type="text"
          value={submissionFormat}
          onChange={(e) => { setSubmissionFormat(e.target.value); setIsSubmitted(false); }}
          disabled={disabled}
          className="w-full px-4 py-2.5 border border-slate-200 rounded-xl bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 disabled:bg-slate-50 text-sm placeholder:text-slate-400"
          placeholder="e.g., id,prediction"
        />
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={disabled}
        className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white py-3 px-6 rounded-xl font-semibold shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30 hover:scale-[1.01] transition-all disabled:from-slate-300 disabled:to-slate-400 disabled:shadow-none disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2"
      >
        <Sparkles className="w-5 h-5" />
        Save Task Configuration
      </button>
    </form>
  );
}
