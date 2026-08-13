import React from 'react';
import { LongitudinalAnalysisResponse } from '../types';

interface ReportSummaryProps {
  data: LongitudinalAnalysisResponse;
}

export const ReportSummary: React.FC<ReportSummaryProps> = ({ data }) => {
  const formattedDate = data.uploaded_at
    ? new Date(data.uploaded_at).toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : 'Recently';

  return (
    <div className="card report-summary-card">
      <div className="summary-top">
        <div className="summary-heading-wrap">
          <div className="status-indicator-badge status-success">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            Report Analyzed
          </div>
          <h2 className="summary-title">Clinical Extraction Summary</h2>
        </div>

        <div className="summary-badges">
          {data.is_baseline ? (
            <span className="badge badge-baseline">
              <span className="badge-icon">🌱</span> Baseline Established
            </span>
          ) : (
            <span className="badge badge-compared">
              <span className="badge-icon">📊</span> Compared with Previous Report (#{data.previous_report_id})
            </span>
          )}

          {data.validation.eligible_for_basic_model ? (
            <span className="badge badge-eligible">
              <span className="badge-icon">✓</span> 9/9 Basic Features Verified
            </span>
          ) : (
            <span className="badge badge-warning">
              <span className="badge-icon">⚠️</span> Basic Labs Incomplete
            </span>
          )}
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">Report ID</span>
          <span className="stat-value">#{data.report_id}</span>
          <span className="stat-sub">{data.report_series_name}</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Patient ID</span>
          <span className="stat-value">{data.user_id}</span>
          <span className="stat-sub">{formattedDate}</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Pages Processed</span>
          <span className="stat-value">{data.page_count}</span>
          <span className="stat-sub">{data.extraction_method.toUpperCase()} Engine</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Biomarkers Detected</span>
          <span className="stat-value">{data.extracted_features.length}</span>
          <span className="stat-sub">{data.validation.available_features.length} Canonical Mapped</span>
        </div>
      </div>
    </div>
  );
};
