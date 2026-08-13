import React from 'react';

interface HeaderProps {
  userId: string;
  reportSeriesName: string;
}

export const Header: React.FC<HeaderProps> = ({ userId, reportSeriesName }) => {
  return (
    <header className="app-header">
      <div className="header-container">
        <div className="brand-group">
          <div className="logo-badge">
            <svg
              className="logo-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <div>
            <div className="brand-title-wrap">
              <span className="brand-title">HealthTrajectory</span>
              <span className="brand-tag">Clinical Research MVP</span>
            </div>
            <p className="brand-tagline">Understand your health trajectory</p>
          </div>
        </div>

        <div className="header-context">
          <div className="context-pill">
            <span className="pill-dot"></span>
            <span className="context-label">Patient:</span>
            <strong className="context-value">{userId || 'Not set'}</strong>
          </div>
          <div className="context-pill">
            <span className="context-label">Series:</span>
            <strong className="context-value">{reportSeriesName || 'Default'}</strong>
          </div>
        </div>
      </div>
    </header>
  );
};
