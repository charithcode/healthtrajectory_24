import React from 'react';
import { TrajectorySummary as TrajectorySummaryType } from '../types';

interface TrajectorySummaryProps {
  summary: TrajectorySummaryType;
}

export const TrajectorySummary: React.FC<TrajectorySummaryProps> = ({ summary }) => {
  return (
    <div className="card trajectory-summary-card">
      <div className="card-header">
        <div className="card-header-icon icon-trajectory">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
            <polyline points="17 6 23 6 23 12" />
          </svg>
        </div>
        <div>
          <h3 className="card-title">Trajectory Shift Summary</h3>
          <p className="card-subtitle">Aggregated longitudinal changes across tracked laboratory biomarkers</p>
        </div>
      </div>

      <div className="shift-chips-grid">
        <div className="shift-chip chip-increased">
          <div className="chip-indicator">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="19" x2="12" y2="5" />
              <polyline points="5 12 12 5 19 12" />
            </svg>
          </div>
          <div className="chip-content">
            <span className="chip-count">{summary.increased_count}</span>
            <span className="chip-label">Increased</span>
          </div>
        </div>

        <div className="shift-chip chip-decreased">
          <div className="chip-indicator">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" />
              <polyline points="19 12 12 19 5 12" />
            </svg>
          </div>
          <div className="chip-content">
            <span className="chip-count">{summary.decreased_count}</span>
            <span className="chip-label">Decreased</span>
          </div>
        </div>

        <div className="shift-chip chip-unchanged">
          <div className="chip-indicator">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </div>
          <div className="chip-content">
            <span className="chip-count">{summary.unchanged_count}</span>
            <span className="chip-label">Unchanged</span>
          </div>
        </div>

        <div className="shift-chip chip-unavailable">
          <div className="chip-indicator">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <div className="chip-content">
            <span className="chip-count">{summary.unavailable_count}</span>
            <span className="chip-label">Unavailable</span>
          </div>
        </div>
      </div>

      <div className="trajectory-narrative">
        <p className="narrative-text">{summary.summary_text}</p>
      </div>
    </div>
  );
};
