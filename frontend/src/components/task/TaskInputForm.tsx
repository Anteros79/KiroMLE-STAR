'use client';

import React, { useState } from 'react';
import { FileText, Upload, AlertCircle } from 'lucide-react';
import { TaskDescription } from '@/types';

interface TaskInputFormProps {
  onSubmit: (task: TaskDescription) => void;
  disabled?: boolean;
}

const TASK_TYPES = [
  'classification',
  'regression',
  'seq2seq',
  'time_series',
  'clustering',
  'ranking',
];

const DATA_MODALITIES = [
  'tabular',
  'image',
  'text',
  'audio',
  'multimodal',
];

const EVALUATION_METRICS = [
  'accuracy',
  'f1_score',
  'auc_roc',
  'rmse',
  'mae',
  'log_loss',
  'map',
  'ndcg',
];

export default function TaskInputForm({ onSubmit, disabled }: TaskInputFormProps) {
  const [description, setDescription] = useState('');
  const [taskType, setTaskType] = useState('classification');
  const [dataModality, setDataModality] = useState('tabular');
  const [evaluationMetric, setEvaluationMetric] = useState('accuracy');
  const [datasetPath, setDatasetPath] = useState('');
  const [submissionFormat, setSubmissionFormat] = useState('');
  const [errors, setErrors] = useState<string[]>([]);

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
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-700 mb-2">
            <AlertCircle className="w-5 h-5" />
            <span className="font-medium">Please fix the following errors:</span>
          </div>
          <ul className="list-disc list-inside text-red-600 text-sm">
            {errors.map((error, i) => (
              <li key={i}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Task Description *
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={disabled}
          rows={6}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          placeholder="Describe your ML task in detail. Include information about the problem, data characteristics, and any specific requirements..."
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Task Type
          </label>
          <select
            value={taskType}
            onChange={(e) => setTaskType(e.target.value)}
            disabled={disabled}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
          >
            {TASK_TYPES.map((type) => (
              <option key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Data Modality
          </label>
          <select
            value={dataModality}
            onChange={(e) => setDataModality(e.target.value)}
            disabled={disabled}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
          >
            {DATA_MODALITIES.map((modality) => (
              <option key={modality} value={modality}>
                {modality.charAt(0).toUpperCase() + modality.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Evaluation Metric
          </label>
          <select
            value={evaluationMetric}
            onChange={(e) => setEvaluationMetric(e.target.value)}
            disabled={disabled}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
          >
            {EVALUATION_METRICS.map((metric) => (
              <option key={metric} value={metric}>
                {metric.toUpperCase().replace('_', ' ')}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Dataset Path *
        </label>
        <input
          type="text"
          value={datasetPath}
          onChange={(e) => setDatasetPath(e.target.value)}
          disabled={disabled}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
          placeholder="/path/to/dataset or URL"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Submission Format (optional)
        </label>
        <input
          type="text"
          value={submissionFormat}
          onChange={(e) => setSubmissionFormat(e.target.value)}
          disabled={disabled}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
          placeholder="e.g., id,prediction"
        />
      </div>

      <button
        type="submit"
        disabled={disabled}
        className="w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <FileText className="w-5 h-5" />
        Save Task Configuration
      </button>
    </form>
  );
}
