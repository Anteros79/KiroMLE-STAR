'use client';

import React, { useState, useRef, useCallback } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { datasetAPI, UploadResponse } from '@/services/api';

interface DatasetUploadProps {
  onUpload: (files: File[]) => void;
  disabled?: boolean;
  runId?: string;
}

interface UploadedFile {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  path?: string;
}

const ALLOWED_EXTENSIONS = ['csv', 'json', 'parquet', 'xlsx', 'xls', 'zip', 'png', 'jpg', 'jpeg', 'wav', 'mp3'];
const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB

export default function DatasetUpload({ onUpload, disabled, runId }: DatasetUploadProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): string | null => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !ALLOWED_EXTENSIONS.includes(ext)) {
      return `File type .${ext} not allowed. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`;
    }
    if (file.size > MAX_FILE_SIZE) {
      return `File too large. Maximum size is 500MB.`;
    }
    return null;
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (disabled) return;
    
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      handleFiles(files);
    }
  };

  const handleFiles = async (files: File[]) => {
    // Validate files first
    const validatedFiles: UploadedFile[] = files.map(file => {
      const error = validateFile(file);
      return {
        file,
        status: error ? 'error' as const : 'pending' as const,
        progress: 0,
        error: error || undefined,
      };
    });

    setUploadedFiles(prev => [...prev, ...validatedFiles]);

    // Get files that passed validation
    const validFiles = validatedFiles.filter(f => f.status === 'pending').map(f => f.file);
    
    if (validFiles.length === 0) return;

    // Upload valid files
    setIsUploading(true);
    
    // Update status to uploading
    setUploadedFiles(prev => prev.map(f => 
      validFiles.includes(f.file) ? { ...f, status: 'uploading' as const } : f
    ));

    try {
      const response: UploadResponse = await datasetAPI.upload(
        validFiles,
        runId,
        (progress) => {
          setUploadedFiles(prev => prev.map(f => 
            validFiles.includes(f.file) && f.status === 'uploading'
              ? { ...f, progress }
              : f
          ));
        }
      );

      // Update file statuses based on response
      setUploadedFiles(prev => prev.map(f => {
        const uploaded = response.uploaded.find(u => u.filename === f.file.name);
        const error = response.errors.find(e => e.filename === f.file.name);
        
        if (uploaded) {
          return { ...f, status: 'success' as const, progress: 100, path: uploaded.path };
        } else if (error) {
          return { ...f, status: 'error' as const, error: error.error };
        }
        return f;
      }));

      // Notify parent of successful uploads
      const successfulFiles = validFiles.filter(f => 
        response.uploaded.some(u => u.filename === f.name)
      );
      if (successfulFiles.length > 0) {
        onUpload(successfulFiles);
      }

    } catch (error) {
      // Mark all uploading files as error
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setUploadedFiles(prev => prev.map(f => 
        validFiles.includes(f.file) && f.status === 'uploading'
          ? { ...f, status: 'error' as const, error: errorMessage }
          : f
      ));
    } finally {
      setIsUploading(false);
    }
  };

  const retryUpload = async (index: number) => {
    const fileToRetry = uploadedFiles[index];
    if (!fileToRetry || fileToRetry.status !== 'error') return;

    // Reset status
    setUploadedFiles(prev => prev.map((f, i) => 
      i === index ? { ...f, status: 'pending' as const, error: undefined, progress: 0 } : f
    ));

    // Re-upload
    await handleFiles([fileToRetry.file]);
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="space-y-4">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && !isUploading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? 'border-primary-500 bg-primary-50'
            : disabled || isUploading
            ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50 cursor-pointer'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ALLOWED_EXTENSIONS.map(ext => `.${ext}`).join(',')}
          onChange={handleFileSelect}
          disabled={disabled || isUploading}
          className="hidden"
        />
        
        <Upload className={`w-12 h-12 mx-auto mb-4 ${
          isDragging ? 'text-primary-500' : 'text-gray-400'
        }`} />
        
        <p className="text-gray-600 mb-2">
          {isUploading
            ? 'Uploading files...'
            : isDragging
            ? 'Drop files here...'
            : 'Drag and drop dataset files here, or click to browse'}
        </p>
        <p className="text-sm text-gray-400">
          Supported: CSV, JSON, Parquet, Excel, ZIP, Images, Audio (max 500MB)
        </p>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Uploaded Files</h4>
          {uploadedFiles.map((uploadedFile, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              <File className="w-5 h-5 text-gray-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700 truncate">
                  {uploadedFile.file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(uploadedFile.file.size)}
                </p>
                {uploadedFile.status === 'uploading' && (
                  <div className="mt-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 transition-all duration-200"
                      style={{ width: `${uploadedFile.progress}%` }}
                    />
                  </div>
                )}
                {uploadedFile.error && (
                  <p className="text-xs text-red-500 mt-1">{uploadedFile.error}</p>
                )}
              </div>
              {uploadedFile.status === 'success' && (
                <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
              )}
              {uploadedFile.status === 'error' && (
                <div className="flex items-center gap-1">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      retryUpload(index);
                    }}
                    className="text-gray-400 hover:text-primary-500"
                    title="Retry upload"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>
              )}
              {uploadedFile.status === 'uploading' && (
                <div className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin flex-shrink-0" />
              )}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(index);
                }}
                className="text-gray-400 hover:text-gray-600 flex-shrink-0"
                disabled={uploadedFile.status === 'uploading'}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
