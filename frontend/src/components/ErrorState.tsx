import React from 'react';
import { FEATURE_LABELS } from '../constants/featureLabels';

interface ErrorStateProps {
  error: string;
  missingFeatures?: string[];
  warnings?: string[];
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  error,
  missingFeatures = [],
  warnings = [],
  onRetry,
}) => {
  return (
    <div className="card error-state-card">
      <div className="error-icon-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>

      <div className="error-body">
        <h3 className="error-title">Processing Notice</h3>
        <p className="error-message">{error}</p>

        {missingFeatures.length > 0 && (
          <div className="missing-features-section">
            <strong className="missing-subtitle">More information is required</strong>
            <p className="missing-desc">
              The following required Basic model features were not detected in the uploaded report:
            </p>
            <ul className="missing-feature-list">
              {missingFeatures.map((key) => (
                <li key={key}>
                  <strong>{FEATURE_LABELS[key] ?? key}</strong> ({key})
                </li>
              ))}
            </ul>
          </div>
        )}

        {warnings.length > 0 && (
          <div className="warnings-section">
            <strong className="warnings-subtitle">System Warnings:</strong>
            <ul className="warning-list">
              {warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}

        {onRetry && (
          <button type="button" className="btn btn-secondary btn-sm" onClick={onRetry}>
            Dismiss & Try Again
          </button>
        )}
      </div>
    </div>
  );
};
