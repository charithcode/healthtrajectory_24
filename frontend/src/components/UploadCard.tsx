import React, { ChangeEvent, DragEvent, useRef, useState } from 'react';

interface UploadCardProps {
  userId: string;
  setUserId: (val: string) => void;
  reportSeriesName: string;
  setReportSeriesName: (val: string) => void;
  file: File | null;
  setFile: (file: File | null) => void;
  onAnalyze: () => void;
  loading: boolean;
  onReset: () => void;
}

export const UploadCard: React.FC<UploadCardProps> = ({
  userId,
  setUserId,
  reportSeriesName,
  setReportSeriesName,
  file,
  setFile,
  onAnalyze,
  loading,
  onReset,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!loading) setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (loading) return;
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && (droppedFile.type === 'application/pdf' || droppedFile.name.endsWith('.pdf'))) {
      setFile(droppedFile);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null;
    setFile(selected);
  };

  return (
    <div className="card upload-card" id="upload-card">
      <div className="card-header">
        <div className="card-header-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="12" y1="18" x2="12" y2="12" />
            <line x1="9" y1="15" x2="15" y2="15" />
          </svg>
        </div>
        <div>
          <h2 className="card-title">Upload Laboratory Report</h2>
          <p className="card-subtitle">Convert multi-page PDF lab results into structured biomarker data</p>
        </div>
      </div>

      <div className="form-grid">
        <div className="input-group">
          <label htmlFor="user-id-input" className="input-label">
            Patient / User ID
          </label>
          <input
            id="user-id-input"
            type="text"
            className="input-field"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            disabled={loading}
            placeholder="e.g. dev-user-1"
          />
          <span className="input-hint">Used to keep this patient's report history separate.</span>
        </div>

        <div className="input-group">
          <label htmlFor="series-input" className="input-label">
            Report Series Name
          </label>
          <input
            id="series-input"
            type="text"
            className="input-field"
            value={reportSeriesName}
            onChange={(e) => setReportSeriesName(e.target.value)}
            disabled={loading}
            placeholder="e.g. Annual Health Checkup"
          />
          <span className="input-hint">Groups related tests (e.g. Annual Checkup, Lipid Panel).</span>
        </div>
      </div>

      <div
        className={`dropzone ${isDragOver ? 'dropzone-active' : ''} ${file ? 'dropzone-has-file' : ''} ${loading ? 'dropzone-disabled' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !loading && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf,.pdf"
          onChange={handleFileChange}
          disabled={loading}
          className="file-input-hidden"
        />

        <div className="dropzone-body">
          {file ? (
            <div className="file-preview">
              <div className="pdf-icon-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="9" y1="13" x2="15" y2="13" />
                  <line x1="9" y1="17" x2="13" y2="17" />
                </svg>
              </div>
              <div className="file-details">
                <strong className="file-name">{file.name}</strong>
                <span className="file-size">{(file.size / 1024).toFixed(1)} KB &bull; Ready for OCR Analysis</span>
              </div>
              <button
                type="button"
                className="btn-remove-file"
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                  if (fileInputRef.current) fileInputRef.current.value = '';
                }}
                title="Remove file"
                disabled={loading}
              >
                &times;
              </button>
            </div>
          ) : (
            <div className="dropzone-empty">
              <div className="upload-icon-circle">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>
              <p className="dropzone-title">
                <strong>Click to browse</strong> or drag & drop laboratory PDF
              </p>
              <p className="dropzone-subtitle">Supported format: Multi-page PDF reports with printed or scanned text</p>
            </div>
          )}
        </div>
      </div>

      <div className="upload-actions">
        <button
          type="button"
          className="btn btn-primary btn-block btn-lg"
          onClick={onAnalyze}
          disabled={loading || !file}
        >
          {loading ? (
            <>
              <span className="spinner-border"></span>
              Processing OCR & Clinical Analysis...
            </>
          ) : (
            <>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              Process & Analyze Report
            </>
          )}
        </button>

        {file && !loading && (
          <button type="button" className="btn btn-secondary" onClick={onReset}>
            Reset
          </button>
        )}
      </div>
    </div>
  );
};
