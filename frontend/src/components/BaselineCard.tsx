import React from 'react';
import { LongitudinalAnalysisResponse } from '../types';

interface BaselineCardProps {
  data: LongitudinalAnalysisResponse;
}

export const BaselineCard: React.FC<BaselineCardProps> = ({ data }) => {
  return (
    <div className="card baseline-callout-card">
      <div className="baseline-icon-wrap">
        <span className="baseline-emoji">🌱</span>
      </div>
      <div className="baseline-body">
        <div className="baseline-tag">First Report in Series</div>
        <h3 className="baseline-title">Baseline established for "{data.report_series_name}"</h3>
        <p className="baseline-text">
          This report serves as the personal reference anchor for Patient <strong>{data.user_id}</strong>. All extracted
          laboratory biomarkers ({data.extracted_features.length} parameters) have been securely cataloged.
        </p>
        <div className="baseline-hint-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
          <span>
            When you upload your next follow-up report under the <strong>"{data.report_series_name}"</strong> series, HealthTrajectory will automatically perform mathematical delta and shift calculations against this baseline.
          </span>
        </div>
      </div>
    </div>
  );
};
