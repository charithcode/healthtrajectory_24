import React from 'react';

interface EmptyStateProps {
  onSelectSample?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = () => {
  return (
    <div className="card empty-state-card">
      <div className="empty-state-illustration">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5.586a1 1 0 0 1 .707.293l5.414 5.414a1 1 0 0 1 .293.707V19a2 2 0 0 1-2 2z" />
        </svg>
      </div>
      <h3 className="empty-title">No Laboratory Report Analyzed Yet</h3>
      <p className="empty-desc">
        Select or drag a multi-page PDF laboratory report above to perform full-document OCR extraction and track longitudinal trajectory shifts.
      </p>
      <div className="empty-steps-guide">
        <div className="guide-step">
          <span className="guide-num">1</span>
          <span>Enter Patient ID & Series Name</span>
        </div>
        <div className="guide-step">
          <span className="guide-num">2</span>
          <span>Upload PDF Diagnostic Report</span>
        </div>
        <div className="guide-step">
          <span className="guide-num">3</span>
          <span>Review Baseline or Trajectory Shifts</span>
        </div>
      </div>
    </div>
  );
};
