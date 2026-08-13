import React from 'react';

export const ModelPlaceholder: React.FC = () => {
  return (
    <div className="card model-placeholder-card">
      <div className="card-header">
        <div className="card-header-icon icon-ai">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
            <line x1="12" y1="22.08" x2="12" y2="12" />
          </svg>
        </div>
        <div>
          <h3 className="card-title">AI Predictive Modeling & SHAP Attribution</h3>
          <p className="card-subtitle">Validated ML risk estimation pipeline interface</p>
        </div>
      </div>

      <div className="model-placeholder-body">
        <div className="honest-notice-box">
          <div className="notice-icon">🔒</div>
          <div className="notice-content">
            <strong>Model Analysis Pending Clinical Training</strong>
            <p>
              Model analysis and SHAP TreeExplainer feature importance will appear here once a verified, clinically labeled
              training dataset is connected to the XGBoost pipeline.
            </p>
            <div className="notice-badges">
              <span className="notice-badge">XGBoost &bull; Planned</span>
              <span className="notice-badge">SHAP TreeExplainer &bull; Planned</span>
              <span className="notice-badge">Zero Fabricated Predictions</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
